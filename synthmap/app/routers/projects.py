"""Holds the routes & Router for Project-related actions."""
from typing import List
from fastapi import APIRouter, Depends

from synthmap.app.routers.utils import db_conn
from synthmap.db import manager as db_man
from synthmap.models import synthmap as synthmodels

projectrouter = APIRouter(prefix="/projects", tags=["Projects"])


@projectrouter.get("/", response_model=List[synthmodels.CommonProject])
def list_projects(db_path=Depends(db_conn)):
    """Returns all registered Projects."""
    with db_man.mk_conn(db_path, read_only=True) as db:
        return list(db_man.list_projects(db))


@projectrouter.post("/")
def create_project(projectdata: db_man.CreateProject, db_path=Depends(db_conn)):
    """Insert a new Project"""
    with db_man.mk_conn(db_path) as db:
        db_man.insert_project(db, dict(projectdata))


@projectrouter.get("/{project_id}")  # , response_model=db_man.InfoProject)
def get_projectinfo(project_id: int, db_path=Depends(db_conn)):
    """Returns this Project's data"""
    with db_man.mk_conn(db_path, read_only=True) as db:
        project_info = db_man.get_project_info(db, project_id)
    return project_info


@projectrouter.get("/{project_id}/images", response_model=List[db_man.DBImage])
def list_project_images(project_id: int, db_path=Depends(db_conn)):
    """Returns a list of this Project's Images"""
    with db_man.mk_conn(db_path, read_only=True) as db:
        project_images = db_man.get_project_images(db, project_id)
    return project_images


# @projectrouter.get("/{project_id}/entities", response_model=List[synthmodels.Entity])
# def list_project_entities(project_id: int, db=Depends(conn_ro)):
#    """Returns a list of this Project's Entities"""
#    project_entities = db_man.get_project_entities(db, project_id)
#    return project_entities


@projectrouter.put("/{project_id}")
def update_project(project_id: int, project_data: db_man.CreateProject):
    """Not implemented. Modify this Project's data"""


@projectrouter.delete("/{project_id}")
def del_project(project_id: int, db_path=Depends(db_conn)):
    """Removes a Project, its backend data and all it's relations to Images, Entities, etc.
    Does not delete Images, Entities, etc."""
    with db_man.mk_conn(db_path) as db:
        db_man.delete_project(db, project_id)
        db.commit()
