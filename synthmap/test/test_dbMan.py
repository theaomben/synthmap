# pylint: disable=R0201

import sqlite3

import numpy as np
import pytest

from synthmap.db import manager as db_man
from synthmap.models import synthmap as synthmodels, colmap as colmodels
from synthmap.projectManager import colmapParser


###
#
# DB Creation & Setup
#
###


class TestConnectionCreation:
    def test_setup_new_db(self, memconn):
        expected_names = [
            "Accounts",
            "Entities",
            "Images",
            "Projects",
            "AliceProjects",
            "ColmapProjects",
            "Sessions",
            "Users",
            "imageEntities",
            "imageFiles",
            "projectImages",
            "sessionImages",
        ]
        db_man.setup_db(memconn)
        cursor = memconn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        db_table_names = [i["name"] for i in cursor]
        assert set(db_table_names) == set(expected_names)


###
#
# Reading/Writing items
#
###


class TestProjectManagement:
    def test_register_projects(self, initialised_db, sample_project_data):
        for sample in sample_project_data["known_good"]:
            db_man.insert_project(initialised_db, sample)

    def test_R_projects(self, initialised_db, sample_project_data):
        db_projects = db_man.list_projects(initialised_db).fetchall()
        assert len(db_projects) == len(sample_project_data["known_good"])
        for project in db_projects:
            assert synthmodels.CommonProject(**project)

    # TODO: check for valid insertion?
    def test_W_projectImages(self, initialised_db):
        for project in db_man.list_projects(initialised_db):
            colmapParser.list_project_images(initialised_db, project["project_id"])

    def test_R_projectImages(self, initialised_db, expected_projectImages):
        images = db_man.get_project_images(initialised_db, 1)
        for image in images:
            assert synthmodels.Image(**image)
            assert image == expected_projectImages[image["id"] - 1]

    def test_R_projectInfo(self, initialised_db):
        for project in db_man.list_projects(initialised_db):
            assert db_man.get_project_info(initialised_db, project["project_id"])

    def test_W_entities(self, initialised_db, sample_entity_data):
        for entity in sample_entity_data:
            db_man.insert_entity(initialised_db, entity)

    def test_R_entities(self, initialised_db, sample_entity_data):
        for db_entity in initialised_db.execute("SELECT * FROM Entities"):
            sample_entity = sample_entity_data[db_entity["entity_id"] - 1]
            db_entity.pop("entity_id")
            assert db_entity == sample_entity

    def test_W_imageEntities(self, initialised_db):
        known_data = {1: [1, 6, 12, 16], 2: [1, 13, 14]}
        for entity_id, image_ids in known_data.items():
            for image_id in image_ids:
                db_man.register_image_entity(initialised_db, image_id, entity_id)

    def test_R_imageEntities(self, initialised_db, sample_entity_data):
        known_data = {1: [1, 6, 12, 16], 2: [1, 13, 14]}
        for entity_id, observations in known_data.items():
            db_images = db_man.get_entity_images(initialised_db, entity_id)
            assert observations == [i["image_id"] for i in db_images]
