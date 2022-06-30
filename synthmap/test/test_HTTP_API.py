# pylint: disable=R0201
import importlib.resources
import os

import pytest
import requests


TEST_ROOT = importlib.resources.files("synthmap.test")


def get(uri, **kwargs):
    return requests.get(f"http://127.0.0.1:8000/api/{uri}/", timeout=10, **kwargs)


class TestServer:
    def test_is_server_up(self, server):
        r = requests.get("http://127.0.0.1:8000/docs")
        assert r.status_code == 200

    def test_api_up(self, server):
        r = get("images")
        assert r.status_code == 200


class TestProjectEndpoints:
    def test_get_projects(self, server):
        r = get("projects")
        known_data = {
            "project_id": 1,
            "label": str(TEST_ROOT / "sample_data" / "project.ini"),
            "project_type": "colmap",
        }
        db_data = r.json()[0]
        db_data.pop("created")
        assert db_data == known_data

    def test_get_projectid(self, server):
        r = get("projects/1")
        db_data = r.json()
        assert db_data["count_images"] == 17

    def test_get_projectimages(self, server, expected_projectImages):
        r = get("projects/1/images")
        known_data = [i["md5"] for i in expected_projectImages]
        db_data = r.json()
        assert [row["md5"] for row in db_data] == known_data

    # TODO: db_man.get_project_entities()
    # def test_get_projectentities(self, server):
    #    r = get("projects/1/entities")
    #    db_data = r.json()
    #    print(db_data)
    #    assert False


class TestEntities:
    def test_get_entities(self, server):
        r = get("entities")
        db_data = r.json()
        print(db_data)
        assert len(db_data) == 2

    # TODO: def test_get_entityid(self, server):

    def test_get_entityimages(self, server):
        r = get("entities/1/images")
        db_data = r.json()
        print(db_data)
        assert len(db_data) == 4
