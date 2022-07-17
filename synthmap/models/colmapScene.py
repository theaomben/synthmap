from typing import List, Optional, Dict

from pydantic import conlist

from synthmap.log.logger import getLogger
from synthmap.models.common import BaseModel


log = getLogger(__name__)


###
#
# Scene Model... Models
#
###


class Camera(BaseModel):
    camera_id: int
    # TODO: Enum valid values for model
    model: str
    width: int
    height: int
    params: conlist(item_type=float, min_items=2, max_items=12)


class Feature(BaseModel):
    x: float
    y: float
    landmark_id: int


class Image(BaseModel):
    image_id: int
    qw: float
    qx: float
    qy: float
    qz: float
    tx: float
    ty: float
    tz: float
    camera_id: int
    name: str
    features: List[Feature]


class Landmark(BaseModel):
    landmark_id: int
    x: float
    y: float
    z: float
    r: Optional[float]
    g: Optional[float]
    b: Optional[float]
    error: float
    track: Dict[int, int]  # image_id: feature_id


class Scene(BaseModel):
    scene_id: Optional[int]
    cameras_path: str
    cameras: Optional[Dict[int, Camera]]
    images_path: str
    images: Optional[Dict[int, Image]]
    points_path: str
    points: Optional[Dict[int, Landmark]]

    def parse_camera_file(cls, file_path=None):
        assert cls.cameras_path or file_path
        with open(cls.cameras_path or file_path, "r") as fd:
            line = fd.readline().strip()
            while line:
                if line[0] == "#":
                    line = fd.readline().strip()
                    continue
                tokens = line.split()
                camera_data = dict(
                    zip(
                        ["camera_id", "model", "width", "height"],
                        [int(tokens[0]), tokens[1], int(tokens[2]), int(tokens[3])],
                    )
                )
                # TODO: Fancify parameter handling based on declared model
                # cf. http://colmap.github.io/cameras.html
                camera_data["params"] = [float(i) for i in tokens[4:]]
                print(f"Done Camera {tokens[0]}")
                yield camera_data
                line = fd.readline().strip()

    def parse_image_file(cls, file_path=None):
        assert cls.images_path or file_path
        image_data = {}
        with open(cls.images_path or file_path, "r") as fd:
            line = fd.readline().strip()
            while line:
                if line[0] == "#":
                    line = fd.readline().strip()
                    continue
                tokens = line.split()
                if len(tokens) == 10:
                    image_data = dict(
                        zip(
                            [
                                "image_id",
                                "qw",
                                "qx",
                                "qy",
                                "qz",
                                "tx",
                                "ty",
                                "tz",
                                "camera_id",
                                "name",
                            ],
                            [
                                int(tokens[0]),
                                float(tokens[1]),
                                float(tokens[2]),
                                float(tokens[3]),
                                float(tokens[4]),
                                float(tokens[5]),
                                float(tokens[6]),
                                float(tokens[7]),
                                int(tokens[8]),
                                tokens[9],
                            ],
                        )
                    )
                    line = fd.readline().strip()
                    continue
                features = []
                iteration = 0
                while 3 * iteration < len(tokens):
                    x, y, landmark = (
                        float(tokens[3 * iteration]),
                        float(tokens[3 * iteration + 1]),
                        int(tokens[3 * iteration + 2]),
                    )
                    features.append([x, y, landmark])
                    iteration += 1
                image_data["features"] = features
                print(f"Done Image {image_data['image_id']}")
                yield image_data
                line = fd.readline().strip()

    def parse_point_file(cls, file_path=None):
        assert cls.points_path or file_path
        with open(cls.points_path or file_path, "r") as fd:
            line = fd.readline().strip()
            while line:
                if line[0] == "#":
                    line = fd.readline().strip()
                    continue
                tokens = line.split()
                point_data = dict(
                    zip(
                        ["landmark_id", "x", "y", "z", "r", "g", "b", "error"],
                        [
                            int(tokens[0]),
                            float(tokens[1]),
                            float(tokens[2]),
                            float(tokens[3]),
                            int(tokens[4]),
                            int(tokens[5]),
                            int(tokens[6]),
                            float(tokens[7]),
                        ],
                    )
                )
                point_data["track"] = dict(zip(tokens[8::2], tokens[9::2]))
                yield point_data
                line = fd.readline().strip()

    def load_all(cls):
        print("Starting load complete Scene")
        assert cls.cameras_path and cls.images_path and cls.points_path
        cls.cameras = {i["camera_id"]: i for i in cls.parse_camera_file()}
        print(f"Done {len(cls.cameras)} Cameras")
        cls.images = {i["image_id"]: i for i in cls.parse_image_file()}
        print(f"Done {len(cls.images)} Images")
        cls.points = {i["landmark_id"]: i for i in cls.parse_point_file()}
        print(f"Done {len(cls.points)} Points")
