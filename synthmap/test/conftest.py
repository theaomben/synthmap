import importlib.resources
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time

import pytest
import requests
import uvicorn

from synthmap.db import manager as db_man
from synthmap.models import colmap as colmodels
from synthmap.projectManager import colmapParser
from synthmap.log.logger import getLogger

log = getLogger(__name__)

TEST_ROOT = importlib.resources.files("synthmap.test")


@pytest.fixture(scope="class")
def memconn():
    with db_man.mk_conn(":memory:") as memconn:
        yield memconn


@pytest.fixture(scope="module")
def temp_dir():
    dirn = tempfile.mkdtemp()
    yield dirn
    # shutil.rmtree(dirn)


@pytest.fixture(scope="module")
def sample_project_data():
    # TODO: change known-good to a reproducible in-repo sample
    project_path = TEST_ROOT / "sample_data" / "project.ini"
    return {
        "known_good": [
            {
                "label": str(project_path),
                "project_type": "colmap",
                "file_path": str(project_path),
                "db_path": str(TEST_ROOT / "sample_data" / "big_images.db"),
                "image_path": str(TEST_ROOT / "sample_data" / "sample_big_images"),
            }
        ]
    }


@pytest.fixture(scope="module")
def sample_entity_data():
    return [
        {
            "label": "Tallest Building",
            "detail": None,
            "way_number": "4",
            "way_name": "quai Charles Altorffer",
            "local_area_name": None,
            "postal_id": "67000",
            "town_name": "Strasbourg",
            "administrative_area_name": "Bas-Rhin",
            "greater_admin_area_name": "Grand Est",
            "country": "France",
        },
        {
            "label": "Corner Shop",
            "detail": None,
            "way_number": "4",
            "way_name": "rue du Faubourg National",
            "local_area_name": None,
            "postal_id": "67000",
            "town_name": "Strasbourg",
            "administrative_area_name": "Bas-Rhin",
            "greater_admin_area_name": "Grand Est",
            "country": "France",
        },
    ]


@pytest.fixture(scope="module")
def expected_projectImages():
    return [
        {
            "id": 1,
            "md5": "c1d5bc9dd5ab0a70087bf121c884d755",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 2,
            "md5": "e5161f8d5c2166b43f1d2068c2c555ff",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 3,
            "md5": "7504ebd5c2d99bd1d13964591d28a3d6",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 4,
            "md5": "4a49b555102d0aa722dda5287fc69958",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 5,
            "md5": "035e3cd51dace05c50ce2fc9642d040c",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 6,
            "md5": "8e74f9106c86e8afb2e36de8ae730ddc",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 7,
            "md5": "c54b0a1584973549b909c314d88c7292",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 8,
            "md5": "3e41d9898131c921336de1f1da676b4f",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 9,
            "md5": "523fc6bd7563f26df178cef97d0afbe6",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 10,
            "md5": "b758dfe59d400755cf97ea0c0f70eaa8",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 11,
            "md5": "c54cd72620b647cbfe77aebe098b4711",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 12,
            "md5": "963cabed471a8c80f9ab477d7812dda2",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 13,
            "md5": "37d3c3a43008c97f7397dccef54fdda1",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 14,
            "md5": "181fc394f27417dfa9010e88792e3150",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 15,
            "md5": "617ab1266f0b317fccc5f7cb3b8fb584",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 16,
            "md5": "6e61eaae783328a217e6297ff586622c",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 17,
            "md5": "cf2aa58df8e4fcb0ef627158b6ddf08c",
            "orig_uri": None,
            "orig_ipfs": None,
        },
    ]


@pytest.fixture(scope="class")
def initialised_db(memconn):
    db_man.setup_db(memconn)
    yield memconn


@pytest.fixture(scope="module")
def setup_db(sample_project_data, sample_entity_data):
    with db_man.mk_conn(":memory:") as memconn:
        initialised_db = db_man.setup_db(memconn)
        for sample in sample_project_data["known_good"]:
            db_man.insert_project(initialised_db, sample)
        for project in db_man.list_projects(initialised_db):
            colmapParser.list_project_images(initialised_db, project["project_id"])
        for entity in sample_entity_data:
            db_man.insert_entity(initialised_db, entity)
        known_data = {1: [1, 6, 12, 16], 2: [1, 13, 14]}
        for entity_id, image_ids in known_data.items():
            for image_id in image_ids:
                db_man.register_image_entity(initialised_db, image_id, entity_id)
        initialised_db.commit()
        yield initialised_db


###
#
# HTTP API
#
###


@pytest.fixture(scope="module")
def server(setup_db, temp_dir):
    """Sets a TemporaryDirectory up, inserts a blank db and runs the HTTP server"""
    db_path = os.path.join(temp_dir, "main.db")
    log.info(f"DB path for server {db_path}")
    with db_man.mk_conn(db_path) as temp_db:
        setup_db.backup(
            temp_db,
            progress=lambda status, remaining, total: print(
                f"Copied {total-remaining} of {total} pages..."
            ),
        )
        temp_db.commit()
    temp_db.close()
    # In order to pass the proper db_path through uvicorn to the app in
    # another process, we use an envfile
    env_path = os.path.join(temp_dir, ".env")
    with open(env_path, "w") as fd:
        fd.write(f"SYNTHMAP_DB_PATH={db_path}")
    mp.set_start_method("spawn")
    p = mp.Process(
        target=uvicorn.run,
        args=("synthmap.app.main:app",),
        kwargs={"env_file": env_path},
    )
    p.start()
    time.sleep(2)
    log.info(f"Providing a server on {db_path}")
    yield
    log.info("Done yielding server fixture, terminating")
    p.terminate()
    p.join()


###
#
# Pydantic Models
#
###


@pytest.fixture(scope="class")
def colmap_project_model(sample_project_data):
    """Returns a minimal models.colmap.ColmapProject(),
    for incremental testing"""
    return colmodels.ColmapProject(**sample_project_data["known_good"][0])
