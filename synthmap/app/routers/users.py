from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, constr

import synthmap.app.auth.httpbasic as auth
from synthmap.app.auth.httpbasic import get_current_username
from synthmap.app.routers.utils import db_conn
from synthmap.db import manager as db_man

userrouter = APIRouter(prefix="/user", tags=["Users"])


class DBUser(BaseModel):
    id: int
    name: str


class CreateUser(BaseModel):
    name: constr(regex="^[a-zA-Z0-9]$", max_length=16)
    pw: str


@userrouter.get("/", response_model=DBUser)
def get_users(
    username: str = Depends(get_current_username), db_path=Depends(db_conn)
) -> List[DBUser]:
    with db_man.mk_conn(db_path, read_only=True) as db:
        stmt = """SELECT id, name FROM Users"""
        return db.execute(stmt).fetchall()


@userrouter.post("/")
def create_user(
    userdata: CreateUser,
    db_path=Depends(db_conn),
):  # , username: str = Depends(get_current_username)):
    # TODO: Verify user
    with db_man.mk_conn(db_path) as db:
        auth.insert_user(db, userdata)
        db.commit()


@userrouter.get("/{user_id}")
def get_userinfo(user_id: int, username: str = Depends(get_current_username)):
    pass


@userrouter.put("/{user_id}")
def update_user(user_id: int, userdata: CreateUser):
    pass


@userrouter.delete("/{user_id}")
def del_user(user_id: int):
    pass
