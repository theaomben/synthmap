from fastapi import APIRouter

# from app.routers.users import userrouter
from synthmap.app.routers.images import imagerouter
from synthmap.app.routers.entities import entityrouter
from synthmap.app.routers.projects import projectrouter

apirouter = APIRouter(
    prefix="/api",
    # tags=["items"],
    # dependencies=[Depends(get_current_username)],
    responses={404: {"description": "Not found"}},
)


@apirouter.get("/")
def api_root():
    return {"ok": True}


# ???
# class ProjectImageInfo(BaseModel):
#    image_id: int
#    project_id: int
#    project_image_id: int
#    label: str
#    file_path: str
#    db_path: str
#    image_path: str
#    created: str


###
#
# Routers
#
###

# apirouter.include_router(userrouter)
apirouter.include_router(imagerouter)
apirouter.include_router(entityrouter)
apirouter.include_router(projectrouter)
