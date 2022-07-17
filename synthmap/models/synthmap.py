# pylint: disable=E0213

from enum import Enum
import sqlite3
from typing import Dict, List, NewType, Optional, Union

from pydantic import conlist, constr, validator, FilePath

from synthmap.models.alice import AliceProject
from synthmap.models.colmap import ColmapProject
from synthmap.models.colmapScene import Scene as ColmapScene
from synthmap.models.common import BaseModel, IPFSURI, GenericURI, GenericURL, MD5Hex
from synthmap.log.logger import getLogger


log = getLogger(__name__)


class EnumProjectTypes(str, Enum):
    colmap = "colmap"
    alice = "alice"


class CommonProject(BaseModel):
    project_id: int
    label: str
    project_type: EnumProjectTypes
    created: str


###
#
# Image Models
#
###


class Image(BaseModel):
    id: int
    orig_uri: Optional[GenericURL]
    orig_ipfs: Optional[IPFSURI]


class ProjectImages(BaseModel):
    file_id: int
    project_id: int
    project_image_id: int


class ImageFile(BaseModel):
    file_id: int
    file_path: Optional[str]
    md5: MD5Hex
    ipfs: Optional[str]
    w: Optional[int]
    h: Optional[int]


class ImageView(BaseModel):
    image_id: int
    file_id: int


###
#
# Entity Models
#
###

EntityTree = NewType("EntityTree", Dict[str, Union[list, "EntityTree"]])


class Entity(BaseModel):
    entity_id: int
    label: str
    detail: Optional[str]
    way_number: Optional[str]
    way_name: Optional[str]
    local_area_name: Optional[str]
    postal_id: Optional[str]
    town_name: Optional[str]
    administrative_area_name: Optional[str]
    greater_admin_area_name: Optional[str]
    country: Optional[str]

    def to_tree(self, tree=None) -> EntityTree:
        """Serialises an entity into a tree as a nested dict.
        Adds a nesting level for each additional entity in a given location."""

        def merge_list(tree: dict, data: list):
            """Recursively merge the list into the nested dict till there are
            no duplicate locations to insert."""
            if not data[0] in tree:
                tree[data[0]] = data[1:]
                return tree
            old_val = tree[data[0]]
            if isinstance(old_val, list):
                new_val = merge_list({old_val[0]: old_val[1:]}, data[1:])
            elif isinstance(old_val, dict):
                new_val = merge_list(old_val, data[1:])
            tree[data[0]] = new_val
            return tree

        if not tree:
            tree = {}
        sd = dict(self)
        keys = [
            "country",
            "greater_admin_area_name",
            "administrative_area_name",
            "town_name",
            "postal_id",
            "local_area_name",
            "way_name",
            "way_number",
            "detail",
            "label",
            "entity_id",
        ]
        data = [sd[k] for k in keys]
        return merge_list(tree, data)


class ImageEntities(BaseModel):
    image_id: int
    entity_id: int
    tiles16: Optional[str]
    bbox16: Optional[str]


###
#
# Session Models
#
###


class Session(BaseModel):
    session_id: int
    orig_uri: GenericURI
    label: Optional[str]
    created: Optional[str]
    notes: Optional[str]


class SessionImages(BaseModel):
    session_id: int
    image_id: int


###
#
# SFMScene Models
#
###


class View(BaseModel):
    image_file_id: int
    file_path: str
    ipfs: str


class Intrinsic(BaseModel):
    width: int
    height: int
    sensorWidth: float
    sensorHeight: float
    type: str
    pxInitialFocalLength: float
    pxFocalLength: float
    principalPoint: conlist(item_type=float, min_items=2, max_items=2)


class Extrinsic(BaseModel):
    rotation_quaternion: conlist(item_type=float, min_items=4, max_items=4)
    position: conlist(item_type=float, min_items=3, max_items=3)


class Feature(BaseModel):
    x: float
    y: float
    landmark_id: int


class Landmark(BaseModel):
    landmark_id: int
    x: float
    y: float
    z: float
    r: Optional[float]
    g: Optional[float]
    b: Optional[float]
    track: Dict[int, int]  # image_file_id: feature_id


class SFMScene(BaseModel):
    views: Dict[int, View]
    intrinsics: Dict[int, Intrinsic]
    extrinsics: Dict[int, Extrinsic]
    features: Dict[int, List[Feature]]
    landmarks: List[Landmark]

    def colmap2SFMScene(colmap_scene):
        return SFMScene(
            views=views,
            intrinsics=intrinsics,
            extrinsics=extrinsics,
            features=features,
            landmarks=landmarks,
        )

    def alice2SFMScene(project):
        return SFMScene(
            views=views,
            intrinsics=intrinsics,
            extrinsics=extrinsics,
            features=features,
            landmarks=landmarks,
        )


###
#
# "Root" Workspace Model
#
###


class Workspace(BaseModel):
    """Represents and loads the content of an entire synthmap database"""

    db_path: FilePath
    projects: Optional[Dict[int, CommonProject]] = None
    colmapProjects: Optional[Dict[int, ColmapProject]] = None
    aliceProjects: Optional[Dict[int, str]] = None  # AliceProject]] = None
    images: Optional[Dict[int, Image]] = None
    projectImages: Optional[List[ProjectImages]] = None
    imageFiles: Optional[Dict[int, ImageFile]] = None
    imageViews: Optional[Dict[int, ImageView]] = None
    entities: Optional[Dict[int, Entity]] = None
    imageEntities: Optional[List[ImageEntities]] = None
    colmapScenes: Optional[Dict[int, ColmapScene]] = None
    aliceScenes: Optional[Dict[int, str]] = None  # AliceScene.Scene]] = None
    projectScenes: Optional[list] = None
    sessions: Optional[Dict[int, Session]] = None
    sessionImages: Optional[List[SessionImages]] = None

    @validator("db_path")
    def db_is_init(cls, db_path):
        with sqlite3.connect(db_path) as db:
            print("validating db")
            tables = {
                i[0]
                for i in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            expected_tables = set(
                [
                    "Projects",
                    "ColmapProjects",
                    "AliceProjects",
                    "Images",
                    "projectImages",
                    "imageFiles",
                    "imageViews",
                    "Entities",
                    "imageEntities",
                    "Sessions",
                    "sessionImages",
                    "Users",
                    "Accounts",
                ]
            )
            if expected_tables - tables:
                raise ValueError(
                    f"db is missing some tables: {expected_tables - tables}"
                )
        return db_path

    def load_Projects(cls):
        log.debug(f"Attempt extraction of Projects from {cls.db_path}")
        if not cls.projects:
            cls.projects = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM Projects"""):
                cls.projects[row[0]] = CommonProject(
                    project_id=row[0],
                    label=row[1],
                    project_type=row[2],
                    orig_uri=row[3],
                    created=row[4],
                )
        log.info(f"Extraction of {len(cls.projects)} Projects from {cls.db_path}")

    def load_ColmapProjects(cls, populate=False):
        log.debug(f"Attempt extraction of ColmapProjects from {cls.db_path}")
        if not cls.colmapProjects:
            cls.colmapProjects = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM ColmapProjects"""):
                # TODO: if populate ColmapProject.load_all()
                cls.colmapProjects[row[0]] = ColmapProject(
                    db_path=row[1], image_path=row[2]
                )
        log.info(
            f"Extraction of {len(cls.colmapProjects)} ColmapProjects from {cls.db_path}"
        )

    def load_AliceProjects(cls):
        log.debug(f"Attempt extraction of AliceProjects from {cls.db_path}")
        if not cls.aliceProjects:
            cls.aliceProjects = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM AliceProjects"""):
                cls.aliceProjects[row[0]] = AliceProject(
                    db_path=row[1], image_path=row[2]
                )
        log.info(
            f"Extraction of {len(cls.aliceProjects)} AliceProjects from {cls.db_path}"
        )

    def load_Images(cls):
        log.debug(f"Attempt extraction of Images from {cls.db_path}")
        if not cls.images:
            cls.images = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM Images"""):
                cls.images[row[0]] = Image(id=row[0], orig_uri=row[1], orig_ipfs=row[2])
        log.info(f"Extraction of {len(cls.images)} Images from {cls.db_path}")

    def load_ProjectImages(cls):
        log.debug(f"Attempt extraction of ProjectImages from {cls.db_path}")
        if not cls.projectImages:
            cls.projectImages = []
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM projectImages"""):
                cls.projectImages.append(
                    ProjectImages(
                        file_id=row[0], project_id=row[1], project_image_id=row[2]
                    )
                )
        log.info(
            f"Extraction of {len(cls.projectImages)} ProjectImages from {cls.db_path}"
        )

    def load_ImageFiles(cls):
        log.debug(f"Attempt extraction of ImageFiles from {cls.db_path}")
        if not cls.imageFiles:
            cls.imageFiles = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM imageFiles"""):
                cls.imageFiles[row[0]] = ImageFile(
                    file_id=row[0],
                    file_path=row[1],
                    md5=row[2],
                    ipfs=row[3],
                    w=row[4],
                    h=row[5],
                )
        log.info(f"Extraction of {len(cls.imageFiles)} ImageFiles from {cls.db_path}")

    def load_ImageViews(cls):
        log.debug(f"Attempt extraction of ImageViews from {cls.db_path}")
        if not cls.imageViews:
            cls.imageViews = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM imageViews"""):
                cls.imageViews[row[0]] = ImageView(
                    image_id=row[0],
                    file_id=row[1],
                )
        log.info(f"Extraction of {len(cls.imageViews)} ImageViews from {cls.db_path}")

    def load_Entities(cls):
        log.debug(f"Attempt extraction of Entities from {cls.db_path}")
        if not cls.entities:
            cls.entities = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM Entities"""):
                cls.entities[row[0]] = Entity(
                    entity_id=row[0],
                    label=row[1],
                    detail=row[2],
                    way_number=row[3],
                    way_name=row[4],
                    local_area_name=row[5],
                    postal_id=row[6],
                    town_name=row[7],
                    administrative_area_name=row[8],
                    greater_admin_area_name=row[9],
                    country=row[10],
                )
        log.info(f"Extraction of {len(cls.entities)} Entities from {cls.db_path}")

    def load_ImageEntities(cls):
        log.debug(f"Attempt extraction of ImageEntities from {cls.db_path}")
        if not cls.imageEntities:
            cls.imageEntities = []
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM imageEntities"""):
                cls.imageEntities.append(
                    ImageEntities(
                        image_id=row[0],
                        entity_id=row[1],
                        tiles16=row[2],
                        bbox16=row[3],
                    )
                )
        log.info(f"Extraction of {len(cls.imageEntities)} Entities from {cls.db_path}")

    def load_ColmapScenes(cls):
        log.debug(f"Attempt extraction of ColmapScenes from {cls.db_path}")
        if not cls.colmapScenes:
            cls.colmapScenes = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM ColmapScenes"""):
                cls.colmapScenes[row[0]] = ColmapScene(
                    scene_id=row[0],
                    cameras_path=row[1],
                    images_path=row[2],
                    points_path=row[3],
                )
        log.info(
            f"Extraction of {len(cls.colmapScenes)} ColmapScenes from {cls.db_path}"
        )

    def load_AliceScenes(cls):
        pass

    def load_Sessions(cls):
        log.debug(f"Attempt extraction of Sessions from {cls.db_path}")
        if not cls.sessions:
            cls.sessions = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM Sessions"""):
                cls.sessions[row[0]] = Session(
                    orig_uri=row[1],
                    label=row[2],
                    created=row[3],
                    notes=row[4],
                )
        log.info(f"Extraction of {len(cls.sessions)} Sessions from {cls.db_path}")

    def load_SessionImages(cls):
        log.debug(f"Attempt extraction of SessionImages from {cls.db_path}")
        if not cls.sessionImages:
            cls.sessionImages = []
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("""SELECT * FROM sessionImages"""):
                cls.sessionImages.append(
                    SessionImages(
                        session_id=row[0],
                        image_id=row[1],
                    )
                )
        log.info(f"Extraction of {len(cls.sessionImages)} Images from {cls.db_path}")
