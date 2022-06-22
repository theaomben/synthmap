from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from synthmap.app.routers.entities import CreateEntity
from synthmap.app.routers.utils import db_conn
import synthmap.db.manager as db_man
from synthmap.models.synthmap import Image
from synthmap.projectManager import colmapParser


imagerouter = APIRouter(prefix="/images", tags=["Images"])


@imagerouter.get("/", response_model=List[Image])
def list_images() -> List[Image]:
    """Not Implemented. Returns all registered Images"""
    pass


class ImageCount(BaseModel):
    image_count: int


@imagerouter.get("/count", response_model=ImageCount)
def count_images(db_path=Depends(db_conn)) -> ImageCount:
    """Returns the number of registered Images"""
    print(f"DB_PATH {db_path}")
    with db_man.mk_conn(db_path, read_only=True) as db:
        return db_man.count_images(db)


@imagerouter.post("/")
def create_image(
    images: List[UploadFile] = File(..., description="Any number of jpeg image files")
):
    pass


@imagerouter.get("/{image_id}")
def get_imageinfo(image_id: int, db_path=Depends(db_conn)):
    """Returns this Image's data, its Project's Data, and its Keypoints."""
    with db_man.mk_conn(db_path, read_only=True) as db:
        image_md5 = db.execute(
            """SELECT md5 FROM Images WHERE id=?""", [image_id]
        ).fetchone()["md5"]
        image_project_data = db_man.get_image_info(db, image_id)
        image_keypoints = colmapParser.list_image_keypoints(db, image_id)
    return {
        "image_id": image_id,
        "md5": image_md5,
        "project_data": image_project_data,
        #'matches': image_matches,
        "keypoints": image_keypoints,
    }


@imagerouter.delete("/{image_id}")
def del_image(image_id: int):
    """Not Implemented. Un-registers an image and all references to it."""
    pass


@imagerouter.get("/{image_id}/entities", tags=["Entities"])
def get_image_entities(image_id: int, db_path=Depends(db_conn)):
    """returns this Image's registered Entities"""
    with db_man.mk_conn(db_path, read_only=True) as db:
        cnt = db_man.get_image_entities(db, image_id)
    return cnt


@imagerouter.get("/{image_id}/reg_entity", tags=["Entities"])
def register_image_entity_get(
    image_id: int, entity_id: int = None, db_path=Depends(db_conn)
):
    """Register an (existing) Entity to this Image."""
    with db_man.mk_conn(db_path) as db:
        db_man.register_image_entity(db, image_id, entity_id)
        db_man.get_image_entities(db, image_id)
        db.commit()
    return RedirectResponse(f"/view/entities/{entity_id}")


# TODO: directly use CreateEntity in fn args?
@imagerouter.post("/{image_id}/entities", tags=["Entities"])
def register_image_entity_post(
    image_id: int,
    label: str = Form(...),
    detail: str = Form(None),
    way_number: str = Form(None),
    way_name: str = Form(None),
    local_area_name: str = Form(None),
    postal_id: str = Form(None),
    town_name: str = Form(None),
    administrative_area_name: str = Form(None),
    greater_admin_area_name: str = Form(None),
    country: str = Form(None),
    db_path=Depends(db_conn),
):
    """Create a new Entity, then register it to this Image."""
    entity = CreateEntity(
        label=label,
        detail=detail,
        way_number=way_number,
        way_name=way_name,
        local_area_name=local_area_name,
        postal_id=postal_id,
        town_name=town_name,
        administrative_area_name=administrative_area_name,
        greater_admin_area_name=greater_admin_area_name,
        country=country,
    )
    with db_man.mk_conn(db_path) as db:
        entity_id = db_man.insert_entity(db, dict(entity))
        db.commit()
    # FIXME: Currently doesn't return anything
    ret = db_man.register_image_entity(db, image_id, entity_id)
    return ret


@imagerouter.get("/file/{md5}", response_class=FileResponse)
def get_imagefile(md5: str, db_path=Depends(db_conn)):
    """Returns an image file. This is the src you want to use in an HTML img."""
    with db_man.mk_conn(db_path, read_only=True) as db:
        image = db_man.md5_to_filepath(db, md5)
    if not image:
        raise HTTPException(
            status_code=404,
        )
    return FileResponse(image["file_path"])


@imagerouter.post("/size")
def get_imagelist_size(
    image_ids: Optional[List[int]] = None,
    all_images: bool = False,
    id_lower_bound: Optional[int] = None,
    id_upper_bound: Optional[int] = None,
    db_path=Depends(db_conn),
) -> int:
    """Get the total size of a list of images.

    Either:
    - pass a list of image_ids as POST data
    - set the all_images query parameter to true,
    - specify a range of ids with the lower & upper bound query parameter.

    Returns the cumulated size in bytes of the queried images."""
    with db_man.mk_conn(db_path, read_only=True) as db:
        if image_ids:
            print("recv image_ids")
            return db_man.get_imagelist_size(db, image_ids=[str(i) for i in image_ids])
        if all_images:
            print("recv all_images")
            return db_man.get_imagelist_size(db, all_images=True)
        if (
            isinstance(id_lower_bound, int)
            and isinstance(id_upper_bound, int)
            and id_lower_bound < id_upper_bound
        ):
            print("recv gt/lt")
            return db_man.get_imagelist_size(db, gt=id_lower_bound, lt=id_upper_bound)
    raise HTTPException(
        status_code=400,
        detail="Invalid parameters",
    )
