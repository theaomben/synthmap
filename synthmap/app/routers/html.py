from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from synthmap.db import manager as db_man
from synthmap.projectManager import colmapParser

env = Environment(
    loader=FileSystemLoader("templates"),
)

htmlrouter = APIRouter(
    prefix="/view",
    tags=["HTML/Frontend"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@htmlrouter.get("/", response_class=HTMLResponse)
def main_view():
    # TODO: Table for entities
    # TODO: Show N random images?
    tmpl = env.get_template("main.html")
    db = db_man.mk_conn(read_only=True)
    projects = db_man.list_projects(db)
    entities = db.execute("SELECT * FROM Entities")
    print("inview", projects)
    return tmpl.render(projects=projects, entities=entities)


@htmlrouter.get("/image/{image_id}", response_class=HTMLResponse)
def view_single_image(image_id: int):
    template = env.get_template("image_view.html")
    with db_man.mk_conn(read_only=True) as db:
        image = db.execute(
            """SELECT id, md5 FROM Images WHERE id=?""", [image_id]
        ).fetchone()
        projects = db_man.get_image_projects(db, image_id)
        entities = db_man.get_image_entities(db, image_id)
        related_images = set()
        for project in projects:
            related_images = related_images.union(
                list(
                    colmapParser.list_project_matches_old(
                        db, project["project_id"], image_id
                    )
                )
            )
            print(f"len rel img {related_images}")
        related_images = sorted(related_images)
        related_entities = {entity["entity_id"]: None for entity in entities}
        for i in related_images:
            for entity in db_man.get_image_entities(db, i):
                if entity["entity_id"] not in related_entities:
                    related_entities[entity["entity_id"]] = entity
        return template.render(
            image=image,
            projects=projects,
            entities=entities,
            related_images=related_images,
            related_entities=[i for i in related_entities.values() if i],
        )


@htmlrouter.get("/projects", response_class=HTMLResponse)
def view_projects():
    def count_images(x):
        return db.execute(
            "select count(*) from projectImages where project_id=?", [x]
        ).fetchone()[0]

    db = db_man.mk_conn(read_only=True)
    project_ids = [
        i[0]
        for i in db.execute("SELECT distinct(project_id) from projectImages").fetchall()
    ]
    project_images = {k: count_images(k) for k in project_ids}
    return f"<p>Found {len(project_ids)} projects</p><p>{str(project_images)}</p>"


@htmlrouter.get("/projects/{project_id}", response_class=HTMLResponse)
def view_project(project_id: int):
    template = env.get_template("project_view.html")
    with db_man.mk_conn(read_only=True) as db:
        project = db.execute(
            "SELECT * FROM Projects WHERE project_id=?", [project_id]
        ).fetchone()
        images = db_man.get_project_images(db, project_id)
        return template.render(project=project, images=images)


@htmlrouter.get("/entities/{entity_id}", response_class=HTMLResponse)
def view_entity(entity_id: int):
    # TODO: Unlink image
    # TODO: Show related entities
    # TODO: Show candidate Images
    db = db_man.mk_conn(read_only=True)
    entity = db.execute(
        "SELECT * FROM Entities WHERE entity_id=?", [entity_id]
    ).fetchone()
    images = db_man.get_entity_images(db, entity_id)
    template = env.get_template("entity_view.html")
    return template.render(entity=entity, images=images)


@htmlrouter.post("/entities/{entity_id}", response_class=HTMLResponse)
def redir_to_view(entity_id: int):
    return view_entity(entity_id)


# TODO: view_project_images
#   --> cluster project images by entity
#   --> thumbnail/image link/registerq multiple images to entity/add entity
