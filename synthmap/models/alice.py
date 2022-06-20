# pylint: disable=E0213

from typing import List, Optional, Tuple

from pydantic import conlist

from synthmap.models.common import BaseModel
from synthmap.log.logger import getLogger


log = getLogger(__name__)


class Observation(BaseModel):
    featureId: int
    observationId: int
    scale: int
    x: Tuple[float, float]


class Structure(BaseModel):
    X: Tuple[float, float, float]
    color: Tuple[int, int, int]
    descType: str
    landmarkId: int
    observations: List[Observation]


class View(BaseModel):
    viewId: int
    poseId: int
    intrinsicId: int
    resectionId: Optional[int]
    path: str
    width: int
    height: int
    metadata: dict


class Intrinsics(BaseModel):
    intrinsicId: int
    width: int
    height: int
    sensorWidth: float
    sensorHeight: float
    serialNumber: str
    type: str
    initializationMode: str
    pxInitialFocalLength: float
    pxFocalLength: float
    principalPoint: Tuple[float, float]
    distortionParams: conlist(item_type=float, min_items=3, max_items=3)
    locked: bool


class PoseTransform(BaseModel):
    center: conlist(item_type=float, min_items=3, max_items=3)
    rotation: conlist(item_type=float, min_items=9, max_items=9)


class Pose(BaseModel):
    locked: Optional[bool]
    transform: Optional[PoseTransform]


class AliceProject(BaseModel):
    file_path: str
    project_type: str = "alice"
    label: Optional[str] = None
    version: Optional[Tuple[int, int, int]]
    featuresFolders: Optional[str]
    matchesFolders: Optional[str]
    views: Optional[List[View]]
    intrinsics: Optional[List[Intrinsics]]
    poses: Optional[List[Pose]]
    structure: Optional[List[Structure]]

    def load_all(cls):
        pass
