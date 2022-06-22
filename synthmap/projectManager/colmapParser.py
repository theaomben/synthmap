# pylint: disable=C0301

from collections import defaultdict
from datetime import datetime
from glob import glob
import os
from pathlib import Path
import re
import shutil
import sqlite3
from typing import List, Optional


import numpy as np
from pydantic import BaseModel, conint


from synthmap.db.manager import mk_conn, insert_project, insert_image


MAX_IMAGE_ID = 2**31 - 1


###
#
# Colmap specific conversions.
# https://github.com/colmap/colmap/blob/dev/scripts/python/database.py
#
###


def image_ids_to_pair_id(image_id1, image_id2):
    """Converts a pair of image_ids to a single pair_id. Used in match related data.
    See `pair_id_to_images()`."""
    if image_id1 > image_id2:
        image_id1, image_id2 = image_id2, image_id1
    return image_id1 * MAX_IMAGE_ID + image_id2


def pair_id_to_image_ids(pair_id):
    """Converts a pair_id to a pair of image_ids. Used in match related data.
    See `image_ids_to_pair_id()`."""
    image_id2 = pair_id % MAX_IMAGE_ID
    image_id1 = (pair_id - image_id2) / MAX_IMAGE_ID
    return int(image_id1), int(image_id2)


def array_to_blob(array: np.ndarray) -> bytes:
    """Serialise any ndarray to bytes."""
    return array.tobytes()


def blob_to_array(blob: bytes, dtype: type, shape=(-1,)) -> np.ndarray:
    """Deserialise bytes to the ndarray of the specified type & shape."""
    return np.frombuffer(blob, dtype=dtype).reshape(*shape)


###
#
# Project Enumeration and storage population
#
###


def get_proj_dirs(proj_path):
    """Reads the first N lines of a colmap configuration file ('project.ini')"""
    cnt = 0
    data = {"project_file": proj_path, "project_type": "colmap"}
    with open(proj_path, "r") as fd:
        for line in fd.readlines():
            if line.startswith("database_path"):
                k, v = line.split("=")
                data["db_path"] = v.strip()
            elif line.startswith("image_path"):
                k, v = line.split("=")
                data[k] = v.strip()
            cnt += 1
            if cnt > 10:
                break
    return data


def update_project_paths(project_path, database_path=None, image_path=None):
    """Amends a Colmap project.ini to include the given paths.
    Copies the original file with an additional ".bak" suffix before affecting changes."""
    print(project_path, database_path, image_path)
    if not database_path and not image_path:
        return None
    project_bak = project_path.with_suffix(project_path.suffix + ".bak")
    # Don't overwrite the backup if it already exists, use it instead.
    if not os.path.exists(project_bak):
        shutil.move(project_path, project_bak)
    else:
        os.remove(project_path)
    with open(project_bak, "r") as fd_in:
        with open(project_path, "w") as fd_out:
            for line in fd_in.readlines():
                if database_path and line.startswith("database_path"):
                    line = f"database_path={database_path}\n"
                if database_path and line.startswith("image_path"):
                    line = f"image_path={image_path}\n"
                fd_out.write(line)


def find_projects(db, paths: List[Path] = list()):
    """Searchs for colmap 'project.ini' files under each of the directories specified in <paths>.
    Creates a Project in <db> for each new one found."""
    projects = []
    for p in paths:
        q_string = os.path.join(p, "**\\project.ini")
        log.debug(f"Searching for projects under {q_string}")
        projects += [get_proj_dirs(i) for i in glob(q_string, recursive=True)]
    log.debug(f"...found {len(projects)} projects")
    for i in projects:
        if not "label" in i:
            i["label"] = i["project_file"]
        insert_project(db, i)
    db.commit()


def list_project_images(db: sqlite3.Connection, project_id: int) -> bool:
    """Attempts to register all images listed in the Project."""
    stmt_get_proj_data = """SELECT db_path, image_path FROM ColmapProjects
        WHERE project_id=?"""
    proj_data = db.execute(stmt_get_proj_data, [project_id]).fetchone()
    stmt_add_image_to_project = """INSERT OR IGNORE INTO projectImages
        (image_id, project_id, project_image_id)
        VALUES (?, ?, ?)"""
    print("Working on", proj_data)
    with mk_conn(proj_data["db_path"], read_only=True) as proj_db:
        try:
            num_images = proj_db.execute(
                "SELECT count(*) AS cnt FROM Images"
            ).fetchone()["cnt"]
        except sqlite3.OperationalError:
            return None
        num_in_db = db.execute(
            "SELECT count(*) AS cnt FROM projectImages WHERE project_id=?", [project_id]
        ).fetchone()["cnt"]
        if num_in_db >= num_images:
            return None
        for row in proj_db.execute("""SELECT image_id, name FROM Images"""):
            file_path = os.path.join(proj_data["image_path"], row["name"])
            syn_image_id = insert_image(db, file_path)
            db.execute(
                stmt_add_image_to_project, [syn_image_id, project_id, row["image_id"]]
            )
            print(f"Done #{row['image_id']}/{num_images}, global #{syn_image_id}")
    return True


def list_image_matches(
    db: sqlite3.Connection, image_id: int, kp_pos_only: bool = False
):
    """Returns this Image's keypoints and all its matches.
    <kp_pos_only> toggles whether to include each keypoint's orientation/scale
    parameters.

    Return format -> (matches, keypoints)
        matches = {project_id: {image2_global_id: {data: np.ndarray}}}
        keypoints = {project_id: {data: np.ndarray}}
    """
    stmt = """SELECT * FROM projectImages
    INNER JOIN Projects 
    ON Projects.id = projectImages.project_id
    WHERE image_id=?"""
    stmt_get_g_img_id = """SELECT image_id FROM projectImages
    WHERE project_image_id=? AND project_id=?"""
    matches = defaultdict(dict)
    keypoints = dict()
    for project_data in db.execute(stmt, [image_id]):
        project_id = project_data["project_id"]
        project_image_id = project_data["project_image_id"]
        with mk_conn(project_data["db_path"], read_only=True) as proj_db:
            kps = proj_db.execute(
                """SELECT rows, cols, data FROM Keypoints WHERE image_id=?""",
                [project_image_id],
            ).fetchone()
            data = blob_to_array(
                kps["data"], dtype=np.float32, shape=(kps["rows"], kps["cols"])
            )
            if kp_pos_only:
                kps["cols"] = 2
                kps["data"] = data[:, :2].tolist()
            else:
                kps["data"] = data.tolist()
            keypoints[project_id] = kps
            for row in proj_db.execute("""SELECT pair_id, rows, data FROM matches"""):
                i1, i2 = pair_id_to_image_ids(row["pair_id"])
                if not project_image_id in [i1, i2] or row["rows"] < 25:
                    continue
                data = {
                    "rows": row["rows"],
                    "data": blob_to_array(
                        row["data"], dtype=int, shape=(-1, 2)
                    ).tolist(),
                }
                if project_image_id == i1:
                    i2_id = db.execute(stmt_get_g_img_id, [i2, project_id]).fetchone()[
                        "image_id"
                    ]
                    matches[project_id][i2_id] = data
                elif project_image_id == i2:
                    i1_id = db.execute(stmt_get_g_img_id, [i1, project_id]).fetchone()[
                        "image_id"
                    ]
                    matches[project_id][i1_id] = data
    return dict(matches), keypoints


def list_image_keypoints(db, image_id):
    # TODO: break out kp extraction from list_image_matches()
    pass


def list_project_matches(db, project_id):
    # TODO: for project_data in db.execute("SELECT * FROM Projects"):
    matches = defaultdict(dict)
    keypoints = dict()
    pass


def list_project_matches_old(db, project_id, image_id):
    stmt_get_g_img_id = """SELECT image_id FROM projectImages
    WHERE project_image_id=? AND project_id=?"""
    proj_data = db.execute(
        """SELECT db_path, image_path FROM ColmapProjects
        WHERE project_id=?""",
        [project_id],
    ).fetchone()
    proj_image_id = db.execute(
        """SELECT project_image_id FROM projectImages
    WHERE image_id=? AND project_id=?""",
        [image_id, project_id],
    ).fetchone()["project_image_id"]
    ret = []
    with mk_conn(proj_data["db_path"], read_only=True) as proj_db:
        for row in proj_db.execute("""SELECT pair_id FROM matches"""):
            i1, i2 = pair_id_to_image_ids(row["pair_id"])
            if proj_image_id == i1:
                i2_id = db.execute(stmt_get_g_img_id, [i2, project_id]).fetchone()[
                    "image_id"
                ]
                ret.append(i2_id)
            elif proj_image_id == i2:
                i1_id = db.execute(stmt_get_g_img_id, [i1, project_id]).fetchone()[
                    "image_id"
                ]
                ret.append(i1_id)
    return ret


def get_image_descriptors(db, image_id):
    """Returns single set of Descriptors for this Image, as stored in the
    first (in terms of project_id) Project."""
    proj_data = db.execute(
        """SELECT min(project_id) AS project_id,
            projectImages.project_image_id, Projects.file_path,
            Projects.db_path, Projects.image_path
        FROM projectImages
        INNER JOIN Projects ON projectImages.project_id=Projects.id
        WHERE image_id=?""",
        [image_id],
    ).fetchone()
    with mk_conn(proj_data["db_path"], read_only=True) as proj_db:
        descriptor = proj_db.execute(
            """SELECT * FROM Descriptors WHERE image_id=?""",
            [proj_data["project_image_id"]],
        ).fetchone()
        descriptor["data"] = blob_to_array(
            descriptor["data"],
            dtype=np.uint8,
            shape=(descriptor["rows"], descriptor["cols"]),
        )
    return descriptor


class RelatedImagesItem(BaseModel):
    image_id: int
    project_id: int
    project_image_id: int
    file_path: str


def get_entity_related_images(db, entity_id: int) -> List[RelatedImagesItem]:
    """Returns basic information for all Images matching this Image."""
    registered_images = [
        i["image_id"]
        for i in db.execute(
            "SELECT image_id FROM imageEntities WHERE entity_id=?", [entity_id]
        )
    ]
    related_images = set(registered_images)
    print("Collecting related images...\nproj#\timg#\tcnt\ttotal")
    for image_id in registered_images:
        project_ids = [
            i["project_id"]
            for i in db.execute(
                "SELECT project_id FROM projectImages WHERE image_id = ?", [image_id]
            )
        ]
        for project_id in project_ids:
            matches = list_project_matches_old(db, project_id, image_id)
            related_images = related_images.union(matches)
            print(
                "{}\t{}\t{}\t{}".format(
                    project_id, image_id, len(matches), len(related_images)
                )
            )
    related_data = []
    for image_id in related_images:
        related_data.extend(
            db.execute(
                """SELECT projectImages.image_id as image_id,
        project_id, project_image_id, file_path
        FROM projectImages
        INNER JOIN imageFiles ON projectImages.image_id=imageFiles.image_id
        WHERE projectImages.image_id=?""",
                [image_id],
            ).fetchall()
        )
    return sorted(related_data, key=lambda x: x["project_id"])


def get_imageset_data(db, project_id: int, image_ids: list):
    """Returns each row of the Project's Match data linking Images listed in
    <image_ids>."""
    gid2pid = (
        lambda image_id: db.execute(
            """SELECT project_image_id FROM projectImages
    WHERE image_id=? AND project_id=?""",
            [image_id, project_id],
        )
        .fetchone()
        .get("project_image_id")
    )
    proj_data = db.execute(
        """SELECT file_path, db_path, image_path FROM Projects WHERE id=?""",
        [project_id],
    ).fetchone()
    proj_image_id_set = set([gid2pid(i) for i in image_ids])
    print("\t", proj_data["db_path"])
    with mk_conn(proj_data["db_path"], read_only=True) as proj_db:
        img_ids_str = ", ".join(map(str, proj_image_id_set))
        stmt = """SELECT images.image_id AS project_image_id, images.name, images.camera_id, images.prior_qw, images.prior_qx, images.prior_qy, images.prior_qz, images.prior_tx, images.prior_ty, images.prior_tz,
    cameras.model, cameras.width, cameras.height, cameras.params, cameras.prior_focal_length,
    keypoints.rows AS keypoints_rows, keypoints.cols AS keypoints_cols, keypoints.data AS keypoints_data,
    descriptors.rows AS descriptors_rows, descriptors.cols AS descriptors_cols, descriptors.data AS descriptors_data
    FROM images
    INNER JOIN cameras on images.camera_id = cameras.camera_id
    INNER JOIN keypoints on keypoints.image_id = images.image_id
    INNER JOIN descriptors on descriptors.image_id = images.image_id
    WHERE images.image_id in ({})""".format(
            img_ids_str
        )
        images = proj_db.execute(stmt).fetchall()
        matches = []
        for row in proj_db.execute(
            """SELECT matches.pair_id, matches.rows AS matches_rows, matches.cols AS matches_cols, matches.data AS matches_data,
    two_view_geometries.rows AS two_view_geometries_rows, two_view_geometries.cols AS two_view_geometries_cols, two_view_geometries.data AS two_view_geometries_data, two_view_geometries.config, two_view_geometries.F, two_view_geometries.E, two_view_geometries.H
    FROM matches
    INNER JOIN two_view_geometries ON matches.pair_id = two_view_geometries.pair_id"""
        ):
            id1, id2 = pair_id_to_image_ids(row["pair_id"])
            if id1 in proj_image_id_set and id2 in proj_image_id_set:
                matches.append([id1, id2, row])
    return {
        "images": {row["project_image_id"]: row for row in images},
        "matches": matches,
    }


def init_db(temp_db):
    """Inserts all tables you'd expect in a vanilla Colmap project database."""
    return [
        temp_db.execute(stmt)
        for stmt in [
            """CREATE TABLE cameras (camera_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, model INTEGER NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, params BLOB, prior_focal_length INTEGER NOT NULL);""",
            """CREATE TABLE images (image_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL UNIQUE, camera_id INTEGER NOT NULL, prior_qw REAL, prior_qx REAL, prior_qy REAL, prior_qz REAL, prior_tx REAL, prior_ty REAL, prior_tz REAL,CONSTRAINT image_id_check CHECK(image_id >= 0 and image_id < 2147483647),FOREIGN KEY(camera_id) REFERENCES cameras(camera_id));""",
            """CREATE UNIQUE INDEX index_name ON images(name);""",
            """CREATE TABLE keypoints (image_id INTEGER PRIMARY KEY NOT NULL, rows INTEGER NOT NULL, cols INTEGER NOT NULL, data BLOB,FOREIGN KEY(image_id) REFERENCES images(image_id) ON DELETE CASCADE);""",
            """CREATE TABLE descriptors (image_id INTEGER PRIMARY KEY NOT NULL, rows INTEGER NOT NULL, cols INTEGER NOT NULL, data BLOB,FOREIGN KEY(image_id) REFERENCES images(image_id) ON DELETE CASCADE);""",
            """CREATE TABLE matches (pair_id INTEGER PRIMARY KEY NOT NULL, rows INTEGER NOT NULL, cols INTEGER NOT NULL, data BLOB);""",
            """CREATE TABLE two_view_geometries (pair_id INTEGER PRIMARY KEY NOT NULL, rows INTEGER NOT NULL, cols INTEGER NOT NULL, data BLOB, config INTEGER NOT NULL, F BLOB, E BLOB, H BLOB);""",
        ]
    ]


# TODO: select existing images from project, don't reinsert
# existing_ids = []
# related = get_entity_related_images(db, query_entity_id, exclude=existing_ids)
def create_entity_project(db, query_entity_id: int, output_path="C:\\data\\"):
    """Synthesize a Colmap Project from available data"""
    output_dir = os.path.join(output_path, str(query_entity_id))
    if os.path.exists(output_dir):
        print(
            "Entity #{} already has a directory, try colmapParser.extend_entity_project()".format(
                query_entity_id
            )
        )

    related = get_entity_related_images(db, query_entity_id)

    image_graph = defaultdict(lambda: defaultdict(int))
    project_count = defaultdict(list)
    for row in related:
        image_id, project_id, project_image_id, file_path = row.values()
        image_graph[project_id][image_id] = project_image_id
        project_count[image_id] += [project_id]
    image_graph = {k: dict(v) for k, v in image_graph.items() if len(v)}
    stmt_proj_data = """SELECT db_path, image_path
    FROM ColmapProjects WHERE project_id=?"""
    project_data = {
        project_id: db.execute(
            stmt_proj_data,
            [project_id],
        ).fetchone()
        for project_id in image_graph.keys()
    }

    new_image_dir = os.path.commonprefix(
        [i["image_path"] for i in project_data.values()]
    )
    image_dir_offsets = {
        k: os.path.relpath(v["image_path"], start=new_image_dir)
        for k, v in project_data.items()
    }
    print("New image root directory is {}".format(new_image_dir))

    image_data = {}
    for project_id, images in sorted(
        image_graph.items(), key=lambda x: len(x[1]), reverse=True
    ):
        image_data[project_id] = get_imageset_data(
            db,
            project_id,
            [i["image_id"] for i in related if i["project_id"] == project_id],
        )
    print("Starting project database...")
    with sqlite3.connect(":memory:") as temp_db:
        init_db(temp_db)

        new_idxs = defaultdict(dict)
        excluded = defaultdict(dict)
        skip = defaultdict(list)
        new_idx = 0
        for row in related:
            image_id, project_id, project_image_id, file_path = row.values()
            if project_image_id in excluded[project_id]:
                print("Found previously excluded image #{}".format(image_id))
                continue
            elif len(project_count[image_id]) > 1:
                # Find out if each project's descriptors are the same
                descriptors = set()
                _p_i_ids = dict()
                for _project_id in project_count[image_id]:
                    p_img_id = image_graph[_project_id][image_id]
                    _p_i_ids[_project_id] = p_img_id
                    descriptors.add(
                        image_data[_project_id]["images"][p_img_id]["descriptors_data"]
                    )
                    excluded[_project_id][p_img_id] = [project_id, project_image_id]
                if len(descriptors) > 1:
                    print(
                        "Problem: Found {} different descriptors for image #{}. Projects #{}".format(
                            len(descriptors),
                            image_id,
                            ", ".join(project_count[image_id]),
                        )
                    )
                    for k, v in _p_i_ids:
                        skip[k].append(v)
                    continue
            new_idx += 1
            new_idxs[project_id][project_image_id] = new_idx
            data = image_data[project_id]["images"][project_image_id]
            data["image_id"] = new_idx
            data["camera_id"] = new_idx
            data["name"] = os.path.join(image_dir_offsets[project_id], data["name"])
            try:
                for stmt in [
                    """INSERT INTO images
    (image_id, name, camera_id, prior_qw, prior_qx, prior_qy, prior_qz, prior_tx, prior_ty, prior_tz)
    VALUES (:image_id, :name, :camera_id, :prior_qw, :prior_qx, :prior_qy, :prior_qz, :prior_tx, :prior_ty, :prior_tz)""",
                    """INSERT INTO cameras
    (camera_id, model, width, height, params, prior_focal_length)
    VALUES (:camera_id, :model, :width, :height, :params, :prior_focal_length)""",
                    """INSERT INTO keypoints
    (image_id, rows, cols, data)
    VALUES (:image_id, :keypoints_rows, :keypoints_cols, :keypoints_data)""",
                    """INSERT INTO descriptors
    (image_id, rows, cols, data)
    VALUES (:image_id, :descriptors_rows, :descriptors_cols, :descriptors_data)""",
                ]:
                    temp_db.execute(stmt, data)
            except sqlite3.IntegrityError:
                continue
        print("Extracted Image data, starting matches...")
        # Insert matches with new_idxs
        for project_id, items in image_data.items():
            for match in items["matches"]:
                id1, id2, match_data = match
                if id1 in skip[project_id] or id2 in skip[project_id]:
                    continue
                if id1 in excluded[project_id]:
                    _p_id, _p_i_id = excluded[project_id][id1]
                    new_id1 = new_idxs[_p_id][_p_i_id]
                else:
                    new_id1 = new_idxs[project_id][id1]
                if id2 in excluded[project_id]:
                    _p_id, _p_i_id = excluded[project_id][id2]
                    new_id2 = new_idxs[_p_id][_p_i_id]
                else:
                    new_id2 = new_idxs[project_id][id2]
                new_pair_id = str(image_ids_to_pair_id(new_id1, new_id2))
                match_data["pair_id"] = new_pair_id
                # print('Match data:', id1,id2, new_id1, new_id2, new_pair_id)
                try:
                    temp_db.execute(
                        """INSERT INTO matches
    (pair_id, cols, rows, data)
    VALUES (:pair_id, :matches_cols, :matches_rows, :matches_data)""",
                        match_data,
                    )
                    temp_db.execute(
                        """INSERT INTO two_view_geometries
    (pair_id, cols, rows, data, config, F, E, H)
    VALUES (:pair_id, :two_view_geometries_cols, :two_view_geometries_rows, :two_view_geometries_data, :config, :F, :E, :H)""",
                        match_data,
                    )
                except sqlite3.IntegrityError:
                    continue
        temp_db.commit()
        print("Done extracting!")
        # Create output dir
        os.mkdir(output_dir)
        with sqlite3.connect(os.path.join(output_dir, "main.db")) as out_db:
            temp_db.backup(out_db)
            out_db.commit()
        print("Done writing to disk! ({})".format(output_dir))
