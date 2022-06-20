# pylint: disable=E0213

import sqlite3
from typing import Dict, Optional, Tuple, Union

import numpy as np
from pydantic import validator, FilePath, DirectoryPath


from synthmap.log.logger import getLogger
from synthmap.models.common import BaseModel


log = getLogger(__name__)


###
#
# Cameras
#
###


class Camera(BaseModel):
    camera_id: int
    model: int
    width: int
    height: int
    params: Optional[Union[bytes, np.ndarray]] = None
    prior_focal_length: float

    class Config:
        arbitrary_types_allowed = True


###
#
# Images
#
###


class RotationQuaternion(BaseModel):
    qw: float
    qx: float
    qy: float
    qz: float


class PositionError(BaseModel):
    # smallest significant unit of measure
    resolution: float
    # accuracy: real_x IN [prior_x-x, prior_x+x] etc
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class PositionPrior(BaseModel):
    tx: float
    ty: float
    tz: Optional[float] = None
    error: Optional[PositionError] = None


class ImagePrior(BaseModel):
    Q: Optional[RotationQuaternion] = None
    T: PositionPrior


class Image(BaseModel):
    id: int
    name: str
    camera_id: int
    priors: Optional[ImagePrior] = None


###
#
# Keypoints & Descriptors
#
###


class KeypointBase(BaseModel):
    x: float
    y: float


class KeypointSimilarity(KeypointBase):
    scale: float
    orientation: float


class KeypointAffinity(KeypointBase):
    s1: float
    s2: float
    s3: float
    s4: float


class RowData(BaseModel):
    rows: int
    cols: int
    data: Optional[Union[str, np.ndarray]] = None

    class Config:
        arbitrary_types_allowed = True


class ImageData(RowData):
    image_id: int


class ImageKeypoints(ImageData):
    data: np.ndarray  # Union[List[KeypointSimilarity], List[KeypointAffinity]]

    class Config:
        arbitrary_types_allowed = True


class ImageDescriptors(ImageData):
    data: np.ndarray

    class Config:
        arbitrary_types_allowed = True


###
#
# Matches & Geometry
#
###


class PairData(RowData):
    pair_id: int

    def ids_i2p(cls, image_id1: int, image_id2: int) -> int:
        if image_id1 > image_id2:
            image_id1, image_id2 = image_id2, image_id1
        return image_id1 * 2147483647 + image_id2

    def ids_p2i(cls, pair_id: int) -> Tuple[int, int]:
        image_id2 = pair_id % 2147483647
        image_id1 = (pair_id - image_id2) / 2147483647
        return int(image_id1), int(image_id2)

    def p2i(cls):
        return cls.ids_p2i(cls.pair_id)


class Match(BaseModel):
    kp1: int
    kp2: int


class PairMatches(PairData):
    data: Optional[np.ndarray] = None

    class Config:
        arbitrary_types_allowed = True


class PairGeometry(PairData):
    data: Optional[np.ndarray] = None
    F: Optional[np.ndarray] = None
    E: Optional[np.ndarray] = None
    H: Optional[np.ndarray] = None

    class Config:
        arbitrary_types_allowed = True


###
#
# Project
#
###


class ColmapProject(BaseModel):
    db_path: FilePath
    image_path: DirectoryPath
    project_type: str = "colmap"
    label: Optional[str] = None
    cameras: Optional[Dict[int, Camera]] = None
    images: Optional[Dict[int, Image]] = None
    keypoints: Optional[Dict[int, ImageKeypoints]] = None
    descriptors: Optional[Dict[int, ImageDescriptors]] = None
    matches: Optional[Dict[int, PairMatches]] = None
    geometries: Optional[Dict[int, PairGeometry]] = None

    @validator("images")
    def valid_images_camera_ids(cls, images):
        if images and {i.camera_id for i in images.values()} - set(cls.cameras.keys()):
            raise ValueError("Some images reference inexistent camera ids")
        return images

    @validator("keypoints")
    def valid_keypoint_image_ids(cls, keypoints):
        if keypoints and {i.image_id for i in keypoints.values()} - set(
            cls.images.keys()
        ):
            raise ValueError("Some keypoints reference inexistent image ids")
        return keypoints

    @validator("descriptors")
    def valid_descriptor_image_ids(cls, descriptors):
        if descriptors and {i.image_id for i in descriptors.values()} - set(
            cls.images.keys()
        ):
            raise ValueError("Some descriptors reference inexistent image ids")
        return descriptors

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
                    "cameras",
                    "images",
                    "keypoints",
                    "descriptors",
                    "matches",
                    "two_view_geometries",
                ]
            )
            if expected_tables - tables:
                raise ValueError(
                    f"db is missing some tables: {expected_tables - tables}"
                )
        return db_path

    def load_cameras(cls):
        log.debug(f"Attempt extraction of Cameras from {cls.db_path}")
        if not cls.cameras:
            cls.cameras = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("SELECT * FROM cameras"):
                cls.cameras[row[0]] = Camera(
                    camera_id=row[0],
                    model=row[1],
                    width=row[2],
                    height=row[3],
                    params=np.frombuffer(row[4]),
                    prior_focal_length=row[5],
                )
        log.info(f"Extraction of {len(cls.cameras)} Cameras from {cls.db_path}")

    def load_images(cls):
        log.debug(f"Attempt extraction of Images from {cls.db_path}")
        if not cls.images:
            cls.images = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("SELECT * FROM images"):
                cls.images[row[0]] = Image(
                    id=row[0], name=row[1], camera_id=row[2], priors=row[3]
                )
        log.info(f"Extraction of {len(cls.images)} Images from {cls.db_path}")

    def load_keypoints(cls):
        if not cls.keypoints:
            cls.keypoints = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("SELECT * FROM keypoints"):
                data = None
                if row[3]:
                    data = np.frombuffer(row[3], dtype=np.float32).reshape(
                        (row[1], row[2])
                    )
                cls.keypoints[row[0]] = ImageKeypoints(
                    image_id=row[0], rows=row[1], cols=row[2], data=data
                )
                log.info(f"Extracted {len(cls.keypoints)} Keypoints from {cls.db_path}")

    def load_descriptors(cls):
        if not cls.descriptors:
            cls.descriptors = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("SELECT * FROM descriptors"):
                data = None
                if row[3]:
                    data = np.frombuffer(row[3], dtype=np.uint8).reshape(
                        (row[1], row[2])
                    )
                cls.descriptors[row[0]] = ImageDescriptors(
                    image_id=row[0], rows=row[1], cols=row[2], data=data
                )
        log.info(f"Extraction of {len(cls.descriptors)} Descriptors from {cls.db_path}")

    def load_matches(cls):
        if not cls.matches:
            cls.matches = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("SELECT * FROM matches"):
                data = None
                if row[3]:
                    data = np.frombuffer(row[3], dtype=np.uint32).reshape(
                        (row[1], row[2])
                    )
                cls.matches[row[0]] = PairMatches(
                    pair_id=row[0], rows=row[1], cols=row[2], data=data
                )
        log.info(f"Extraction of {len(cls.matches)} Matches from {cls.db_path}")

    def load_geometries(cls):
        def parse_blob(blob):
            return np.frombuffer(blob, dtype=np.float64).reshape((3, 3))

        if not cls.geometries:
            cls.geometries = {}
        with sqlite3.connect(cls.db_path) as db:
            for row in db.execute("SELECT * FROM two_view_geometries"):
                data = None
                if row[3]:
                    data = np.frombuffer(row[3], dtype=np.uint32).reshape(
                        (row[1], row[2])
                    )
                table = {}
                for i in range(5, 8):
                    if row[i]:
                        table[i] = parse_blob(row[i])
                cls.geometries[row[0]] = PairGeometry(
                    pair_id=row[0],
                    rows=row[1],
                    cols=row[2],
                    data=data,
                    config=row[4],
                    F=table.get(5),
                    E=table.get(6),
                    H=table.get(7),
                )
        log.info(f"Extraction of {len(cls.geometries)} Geometries from {cls.db_path}")

    def load_all(cls):
        for fn in [
            cls.load_cameras,
            cls.load_images,
            cls.load_keypoints,
            cls.load_descriptors,
            cls.load_matches,
            cls.load_geometries,
        ]:
            try:
                fn()
                continue
            # TODO: sqlite.OperationalError et al.
            except Exception as e:
                print(e)
            break

    def yield_pairs_for(cls, image_id: int, pair_dict: Dict[int, PairData]):
        for pair_id, pair_data in pair_dict.items():
            if pair_data.data is None:
                continue
            p1, p2 = pair_data.p2i()
            if image_id == p1:
                yield p2, pair_data
            elif image_id == p2:
                # If we are the second image, reverse the data columns so the
                # indexed image's keypoints remain in the second column.
                # aka: pair_data.T[::-1].T
                pair_data.data = pair_data.data[:, ::-1]
                yield p1, pair_data

    class Config:
        validate_assignment = True


# class Entity(BaseModel)
# class Image(BaseModel)
# class Mask(BaseModel)
