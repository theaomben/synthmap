from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from synthmap.app.routers.utils import db_conn
import synthmap.db.manager as db_man
from synthmap.models import synthmap as synthmodels

entityrouter = APIRouter(prefix="/entities", tags=["Entities"])


class CreateEntity(BaseModel):
    label: str
    detail: Optional[str] = None
    way_number: Optional[str] = None
    way_name: Optional[str] = None
    local_area_name: Optional[str] = None
    postal_id: Optional[str] = None
    town_name: Optional[str] = None
    administrative_area_name: Optional[str] = None
    greater_admin_area_name: Optional[str] = None
    country: Optional[str] = None


@entityrouter.get("/")
def get_entities(db_path=Depends(db_conn)) -> List[synthmodels.Entity]:
    """Returns the list of all registered Entities."""
    with db_man.mk_conn(db_path, read_only=True) as db:
        return db_man.list_entities(db)


@entityrouter.post("/")
def create_entity(entitydata: CreateEntity, db_path=Depends(db_conn)):
    """Inserts a new Entity"""
    with db_man.mk_conn(db_path) as db:
        ret = db_man.insert_entity(db, dict(entitydata))
        db.commit()
    return ret


@entityrouter.get("/{entity_id}")
def get_entityinfo(entity_id: int):
    """Not Implemented. Returns this Entity's details."""
    pass


@entityrouter.get("/{entity_id}/images")
def get_entityimages(entity_id: int, db_path=Depends(db_conn)):
    """Returns the Images registered to this Entity"""
    with db_man.mk_conn(db_path, read_only=True) as db:
        return db_man.get_entity_images(db, entity_id)


@entityrouter.put("/{entity_id}")
def update_entity(entity_id: int, entitydata: CreateEntity):
    """Not implemented. Change (some subset of) an Entity's properties in-place."""
    pass


@entityrouter.delete("/{entity_id}")
def delete_entity(entity_id: int):
    """Not Implemented. Un-registers an Entity and all references to it."""
    pass


@entityrouter.get("/{entity_id}/reg_image", tags=["Images"])
def register_entity_image_get(
    entity_id: int, image_id: int = None, db_path=Depends(db_conn)
):
    """Register an (existing) Image to this Entity."""
    with db_man.mk_conn(db_path, read_only=True) as db:
        return db_man.register_image_entity(db, image_id, entity_id)
