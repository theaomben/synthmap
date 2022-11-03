"""Interface for a Synthmap SQLite database."""

from datetime import datetime
import hashlib
import os.path
from pathlib import Path
import sqlite3
from typing import List, Optional

from pydantic import BaseModel

from synthmap.imageProcessing import imgproc
from synthmap.log.logger import getLogger
from synthmap.models import synthmap as synthmodels


log = getLogger(__name__)

DB_PATH = os.path.join(os.path.expanduser("~"), ".synthmap", "main.db")

if not os.path.exists(DB_PATH):
    log.error("System-wide database file is missing, have you run `cli setup`?")


###
#
# Sqlite setup
#
###

schemas = {
    "projects": """CREATE TABLE Projects (project_id INTEGER PRIMARY KEY,
        label TEXT,
        project_type TEXT NOT NULL,
        orig_uri TEXT UNIQUE NOT NULL,
        created TEXT)""",
    "colmapprojects": """CREATE TABLE ColmapProjects (project_id INTEGER PRIMARY KEY,
        db_path TEXT NOT NULL,
        image_path TEXT NOT NULL)""",
    "aliceprojects": """CREATE TABLE AliceProjects (project_id INTEGER PRIMARY KEY,
        file_path TEXT UNIQUE NOT NULL)""",
    "images": """CREATE TABLE Images (id INTEGER PRIMARY KEY,
        orig_uri TEXT UNIQUE,
        orig_ipfs TEXT UNIQUE)""",
    "projectImages": """CREATE TABLE projectImages(file_id INT NOT NULL,
        project_id INT NOT NULL,
        project_image_id INT NOT NULL,

        UNIQUE(file_id, project_id),
        UNIQUE(project_id, project_image_id))""",
    "imageFiles": """CREATE TABLE imageFiles(file_id INTEGER PRIMARY KEY,
        file_path TEXT UNIQUE NOT NULL,
        md5 TEXT UNIQUE NOT NULL,
        ipfs TEXT UNIQUE,
        w INT,
        h INT)""",
    "imageViews": """CREATE TABLE imageViews(image_id INTEGER NOT NULL,
        file_id INTEGER NOT NULL,

        UNIQUE(image_id, file_id))""",
    "entities": """CREATE TABLE Entities(entity_id INTEGER PRIMARY KEY,
        label TEXT,
        detail TEXT,
        way_number TEXT,
        way_name TEXT,
        local_area_name TEXT,
        postal_id TEXT,
        town_name TEXT,
        administrative_area_name TEXT,
        greater_admin_area_name TEXT,
        country TEXT)""",
    "imageEntities": """CREATE TABLE imageEntities(image_id INT NOT NULL,
        entity_id INT NOT NULL,
        tiles16 TEXT,
        bbox16 TEXT)""",
    "ColmapScenes": """CREATE TABLE ColmapScenes (scene_id INTEGER PRIMARY KEY,
        cameras_path TEXT,
        images_path TEXT,
        points_path TEXT,

        UNIQUE(cameras_path, images_path, points_path))""",
    "projectScenes": """CREATE TABLE projectScenes(scene_id INT NOT NULL,
        project_id INT NOT NULL)""",
    "sessions": """CREATE TABLE Sessions(session_id INTEGER PRIMARY KEY,
        orig_uri TEXT NOT NULL,
        label TEXT,
        created TEXT,
        notes TEXT)""",
    "sessionImages": """CREATE TABLE sessionImages(session_id INTEGER NOT NULL,
        image_id INTEGER UNIQUE NOT NULL)""",
    "users": """CREATE TABLE Users(user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        pwhash TEXT NOT NULL)""",
    "accounts": """CREATE TABLE Accounts(user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL)""",
}
###
#
# Connection Creation
#
###


def dict_factory(cursor, row):
    """Maps a query's columns (and aliases) to its values."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def mk_conn(db_path=DB_PATH, read_only=False, as_dicts=True) -> sqlite3.Connection:
    """Creates a new sqlite connection to the database at <db_path>.
    Defaults to R/W access and row->dict enabled"""
    if read_only:
        log.debug(f"New SQLite connection (RO) to {db_path}")
        db_uri = f"file:{db_path}?mode=ro"
        db = sqlite3.connect(db_uri, uri=True)
    else:
        log.debug(f"New SQLite connection (RW) to {db_path}")
        db = sqlite3.connect(db_path)
    if as_dicts:
        db.row_factory = dict_factory
    return db


def setup_db(db: sqlite3.Connection) -> sqlite3.Connection:
    """Creates the expected tables in the passed database.
    See <schemas> in this module."""
    for table_name, stmt in schemas.items():
        try:
            log.debug(f"Creating table {table_name}")
            db.execute(stmt)
        except sqlite3.OperationalError as e:
            log.error(f"Creation error in {table_name}: {e}")
            continue
    return db


###
#
# Models
#
###


class CreateProject(BaseModel):
    label: str
    project_type: synthmodels.EnumProjectTypes
    file_path: str
    db_path: Optional[str]
    image_path: Optional[str]


class DBProject(CreateProject):
    project_id: int
    created: datetime


class InfoProject(BaseModel):
    project_data: DBProject  # errors!!!
    count_images: int
    count_entities: int
    project_images: list
    project_entities: list  # List[synthmodels.Entity]


###
#
# Project Management
#
###


def insert_project(db: sqlite3.Connection, project_data: CreateProject) -> None:
    """Registers a photogrammetric project (any backend) to the passed database."""
    stmt_proj_insert = """INSERT OR IGNORE INTO Projects
    (label, project_type, orig_uri, created)
    VALUES (:label, :project_type, :orig_uri, :created)"""
    stmt_colmap_insert = """INSERT OR IGNORE INTO ColmapProjects
    (project_id, db_path, image_path)
    VALUES (:project_id, :db_path, :image_path)"""
    stmt_alice_insert = """INSERT OR IGNORE INTO AliceProjects
    (project_id, file_path)
    VALUES (:project_id, :file_path)"""
    if isinstance(project_data, BaseModel):
        project_data = dict(project_data)
    if "file_path" in project_data:
        # This is an AliceProject
        project_data["orig_uri"] = "file://" + str(project_data["file_path"])
    else:
        # This is a ColmapProject
        project_data["orig_uri"] = "file://" + str(project_data["project_file"])
    project_data["created"] = str(datetime.utcnow())
    log.debug(f"Attempt project creation: {project_data['orig_uri']}")
    db.execute(stmt_proj_insert, project_data)
    project_id = db.execute(
        """SELECT project_id FROM Projects
        WHERE orig_uri=?""",
        [project_data["orig_uri"]],
    ).fetchone()["project_id"]
    project_data["project_id"] = project_id
    log.info(f"Created project {project_id} based on {project_data['orig_uri']}")
    if project_data["project_type"] == "colmap":
        db.execute(stmt_colmap_insert, project_data)
    elif project_data["project_type"] == "alice":
        db.execute(stmt_alice_insert, project_data)
    else:
        log.error(f"Invalid project_type: {project_data['project_type']}")
        raise ValueError
    return project_id


def list_projects(db: sqlite3.Connection) -> List[synthmodels.CommonProject]:
    """Returns a Project's basic, backend-agnostic information from the passed db."""
    return db.execute("""SELECT * FROM Projects""")


def get_project_images(
    db: sqlite3.Connection, project_id: int
) -> List[synthmodels.ImageFile]:
    """Returns all Image data associated to a Project from the passed db.
    TODO: Results will be messed up with resized images pointing to the same image_id"""
    stmt_proj_imgs = """SELECT imageFiles.* FROM imageFiles
    INNER JOIN projectImages ON projectImages.file_id = imageFiles.file_id
    WHERE projectImages.project_id=?"""
    return list(db.execute(stmt_proj_imgs, [project_id]).fetchall())


def get_project_info(db: sqlite3.Connection, project_id: int):
    """Returns the Project's data and associated images"""
    stmt_proj_data = """SELECT * FROM Projects WHERE project_id=?"""
    proj_data = db.execute(stmt_proj_data, [project_id]).fetchone()
    proj_imgs = get_project_images(db, project_id)
    return {
        "project_data": proj_data,
        "count_images": len(proj_imgs),
        "project_images": proj_imgs,
    }


def delete_project(db: sqlite3.Connection, project_id: int):
    """Removes a Project, its backend data and all it's relations to Images, Entities, etc.
    Does not delete Images, Entities, etc."""
    # TODO: Handle backend specific tables
    log.info(f"Deleting project {project_id}")
    stmt_del_pimg = "DELETE FROM projectImages WHERE project_id=?"
    stmt_del_proj = "DELETE FROM Projects WHERE project_id=?"
    for stmt in [stmt_del_pimg, stmt_del_proj]:
        db.execute(stmt, [project_id])


###
#
# Image Management
#
###


def get_md5(fp: Path):
    """Returns a hex string assumed to be uniquely identifying for any file.
    Bridge solution en attendant Godo-^W^W^W... IPFS."""
    BUF_SIZE = 2**16
    md5 = hashlib.md5()
    with open(fp, "rb") as fd:
        while True:
            data = fd.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def insert_image(
    db: sqlite3.Connection,
    file_path: Path,
    existing_image_id: int = None,
    orig_uri: str = None,
    orig_ipfs: str = None,
) -> int:
    """Creates a new Image from <file_path> if it is not already registered in this database."""
    log.debug(f"Attempt to insert image {file_path}")
    md5 = get_md5(file_path)
    stmt_add_image = """INSERT OR IGNORE INTO Images
    (orig_uri, orig_ipfs) VALUES (?, ?)"""
    stmt_add_file = """INSERT OR IGNORE INTO imageFiles
    (file_path, md5, ipfs, w, h) VALUES (?, ?, ?, ?, ?)"""
    file_id = db.execute(
        """SELECT file_id FROM imageFiles WHERE md5=?""", [md5]
    ).fetchone()
    if file_id:
        return file_id.get("file_id")
    if existing_image_id:
        image_id = existing_image_id
    else:
        # Since we don't have a local md5 match, assume the file is original
        if not orig_uri:
            orig_uri = f"file://{file_path}"
        db.execute(stmt_add_image, [orig_uri, orig_ipfs])
        image_id = db.execute(
            """SELECT id FROM Images WHERE orig_uri=?""", [orig_uri]
        ).fetchone()["id"]
    w, h = imgproc.get_size(file_path)
    db.execute(stmt_add_file, [str(file_path), md5, orig_ipfs, w, h])
    file_id = db.execute(
        """SELECT file_id FROM imageFiles WHERE md5=?""", [md5]
    ).fetchone()["file_id"]
    # TODO: associate image_id & file_id
    register_image_view(db, image_id, file_id)
    log.debug(f"Created imageFile #{file_id} related to Image #{image_id}")
    return file_id


def filepath2image(db: sqlite3.Connection, file_path: Path) -> int:
    stmt = """SELECT image_id FROM imageViews
    INNER JOIN imageFiles ON imageViews.file_id = imageFiles.file_id
    WHERE imageFiles.file_path = ?"""
    return db.execute(stmt, file_path).fetchone()["image_id"]


def register_image_view(db: sqlite3.Connection, image_id: int, file_id: int):
    stmt_add_imageView = """INSERT OR IGNORE INTO imageViews
    (image_id, file_id) VALUES (?, ?)"""
    db.execute(stmt_add_imageView, [image_id, file_id])


def count_images(db: sqlite3.Connection):
    """Returns the count of all registered Images in this database."""
    return db.execute("SELECT count(*) AS image_count FROM Images").fetchone()


def list_images(db: sqlite3.Connection) -> List[synthmodels.ImageFile]:
    """Returns all Images in this database."""
    rows = db.execute("""SELECT * FROM imageFiles""")
    return [synthmodels.ImageFile(**i) for i in rows]


def md5_to_filepath(db: sqlite3.Connection, md5):
    """Returns the filepath associated to the given md5 hash."""
    stmt = """SELECT file_path FROM imageFiles WHERE md5=?"""
    return db.execute(stmt, [md5]).fetchone()


def get_image_projectdata(db: sqlite3.Connection, file_id: int):
    """Returns this a list of this Image's data from each Project in which it appears."""
    image_project_data = db.execute(
        """SELECT * FROM projectImages
        INNER JOIN Projects
        ON Projects.project_id = projectImages.project_id
        WHERE file_id=?""",
        [file_id],
    ).fetchall()
    return image_project_data


def get_imagelist_size(
    db: sqlite3.Connection,
    file_ids=None,
    all_images=False,
    gt: Optional[int] = None,
    lt: Optional[int] = None,
):
    """Returns the on-disk size of (in order of priority):
    - <all_images> if set to True
    - if both <gt> & <lt> are specified as integers,
        the range of ids `gt <= file_id < lt`
    - the specified Images in <file_ids>
    -"""
    if all_images:
        stmt = """SELECT file_path FROM imageFiles"""
    elif isinstance(lt, int) and isinstance(gt, int) and gt < lt:
        stmt = f"""SELECT file_path FROM imageFiles WHERE file_id >= {gt} AND file_id < {lt}"""
    elif file_ids:
        param_string = ", ".join(file_ids)
        stmt = f"""SELECT file_path FROM imageFiles WHERE file_id IN ({param_string})"""
    else:
        return None
    cumul_size = 0
    for i in db.execute(stmt):
        file_path = i["file_path"]
        print("file_path:", file_path)
        if not os.path.exists(file_path):
            continue
        size = os.path.getsize(file_path)
        cumul_size += size
        print(f"Size: {size}\tTotal Size:{cumul_size}")
    return cumul_size


def get_image_projects(db: sqlite3.Connection, file_id: int):
    """List Projects in which Image appears."""
    stmt = """SELECT Projects.* FROM Projects
    INNER JOIN projectImages ON projectImages.project_id = Projects.project_id
    WHERE projectImages.file_id=?"""
    return db.execute(stmt, [file_id]).fetchall()


def get_image_entities(db: sqlite3.Connection, image_id: int):
    """List Entities registered to this Image."""
    stmt = """SELECT Entities.* FROM Entities
    INNER JOIN imageEntities ON Entities.entity_id=imageEntities.entity_id
    WHERE imageEntities.image_id=?"""
    return db.execute(stmt, [image_id]).fetchall()


def register_image_entity(db: sqlite3.Connection, image_id: int, entity_id: int):
    """Register an (existing) Entity to this Image."""
    log.debug(f"Attempt registration of I{image_id}-E{entity_id}")
    stmt = """INSERT OR IGNORE INTO imageEntities
    (image_id, entity_id)
    VALUES (?, ?)"""
    db.execute(stmt, [image_id, entity_id])


###
#
# Entity Management
#
###


def insert_entity(db: sqlite3.Connection, entitydata) -> int:
    """Create a new Entity"""
    log.debug(f"Attempt insertion of Entity {entitydata}")
    stmt = """INSERT OR IGNORE INTO Entities
    (label, detail, way_number, way_name, local_area_name, postal_id,
    town_name, administrative_area_name, greater_admin_area_name, country)
    VALUES (:label, :detail, :way_number, :way_name, :local_area_name,
    :postal_id, :town_name, :administrative_area_name,
    :greater_admin_area_name, :country)"""
    params = {}
    for k in [
        "label",
        "detail",
        "way_number",
        "way_name",
        "local_area_name",
        "postal_id",
        "town_name",
        "administrative_area_name",
        "greater_admin_area_name",
        "country",
    ]:
        params[k] = entitydata.get(k, None)
    db.execute(stmt, params)
    q_str = " AND ".join([f"{k}=:{k}" for k, v in params.items() if v])
    stmt_entity_id = f"SELECT entity_id FROM Entities WHERE {q_str}"
    entity_id = db.execute(
        stmt_entity_id,
        params,
    ).fetchone()["entity_id"]
    log.info(f"Created Entity #{entity_id}")
    return entity_id


def list_entities(db: sqlite3.Connection) -> List[synthmodels.Entity]:
    """Returns all Entities in this database."""
    rows = db.execute("""SELECT * FROM Entities""")
    return [synthmodels.Entity(**i) for i in rows]


def get_entity_images(db: sqlite3.Connection, entity_id: int):
    """Returns Images registered to this Entity."""
    # FIXME: INNER JOIN imageEntities through Images
    stmt = """SELECT imageFiles.file_id, md5 FROM imageFiles
    INNER JOIN imageEntities ON imageEntities.image_id = imageFiles.file_id
    WHERE imageEntities.entity_id=?"""
    return db.execute(stmt, [entity_id]).fetchall()


###
#
# Scene Management
#
###


def insert_scene(db: sqlite3.Connection, project_id: int, scene_data):
    stmt_scene_insert = """INSERT OR IGNORE INTO ColmapScenes
    (cameras_path, images_path, points_path)
    VALUES (:cameras_path, :images_path, :points_path)"""
    scene_data = [str(i) for i in scene_data]
    db.execute(stmt_scene_insert, scene_data)
    scene_id = db.execute(
        """SELECT scene_id FROM ColmapScenes
    WHERE cameras_path=:cameras_path AND images_path=:images_path AND points_path=:points_path""",
        scene_data,
    ).fetchone()["scene_id"]
    db.execute(
        """INSERT OR IGNORE INTO projectScenes
        (scene_id, project_id)
        VALUES (?, ?)""",
        [scene_id, project_id],
    )


###
#
# Session Management
#
###


def insert_session(
    db: sqlite3.Connection, session_folder: Path, label: str = None, notes: str = None
):
    """Creates a new Session."""
    log.debug(f"Attempt insertion of Session {session_folder}")
    stmt = """INSERT OR IGNORE INTO Sessions
    (orig_uri, label, created, notes)
    VALUES (:orig_uri, :label, :created, :notes)"""
    if not label:
        label = os.path.split(session_folder)[-1]
    data = {
        "orig_uri": "file://" + session_folder,
        "label": label,
        "created": str(datetime.utcnow()),
        "notes": notes,
    }
    db.execute(stmt, data)
    log.info(f"Insertion of Session {session_folder}")


def get_session_images(db: sqlite3.Connection, session_id: int) -> List[int]:
    """Returns Images registered to this Session"""
    stmt = """SELECT image_id FROM sessionImages WHERE session_id = ?"""
    return [i["image_id"] for i in db.execute(stmt, [session_id])]


def register_image_session(db, image_id: int, session_id: int):
    """Register an (existing) Session to this Image."""
    log.debug(f"Attempt registration of I{image_id}-S{session_id}")
    stmt = """INSERT OR IGNORE INTO sessionImages
    (session_id, image_id)
    VALUES (?, ?)"""
    db.execute(stmt, [session_id, image_id])
    log.info(f"Registration of I{image_id}-S{session_id}")
