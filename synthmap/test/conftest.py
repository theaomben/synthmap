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
            "md5": "4bb344e1284b506b19f606ce6c392cd3",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 2,
            "md5": "41124998f2e131494ab62604870f0947",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 3,
            "md5": "15d35a71054bd682b710e532b6cc31bd",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 4,
            "md5": "e4fccacc64a2b49b918eec7da2dc2dd7",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 5,
            "md5": "fbc86c099952aa962da9dbb050fad638",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 6,
            "md5": "3e98f72249e9eeca84c6acc418d01767",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 7,
            "md5": "7a5c4321a598a07514cc0d0d2c3adefe",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 8,
            "md5": "250e31f9326d8a2b86e01c0096e525ab",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 9,
            "md5": "939e8dd46a1d3b724248179aa464accb",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 10,
            "md5": "c89ac823c4573abad4d1c57eadcc0fae",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 11,
            "md5": "23c791a6ca17607651fab5fa7f9e8896",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 12,
            "md5": "9b272ef29219a807ef78fd2c8a2e9f43",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 13,
            "md5": "dab34469e06ef020bdcaac69c7dc5c6b",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 14,
            "md5": "5deebffc5ff42ee59407a53b2d81518d",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 15,
            "md5": "5ccee996cb3a0250cd1ec98d5d5b5abc",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 16,
            "md5": "ece8f66bdb00b25bc3408b7adbfd316d",
            "orig_uri": None,
            "orig_ipfs": None,
        },
        {
            "id": 17,
            "md5": "f70797c4e617575552cecfe30a6dd1c5",
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
