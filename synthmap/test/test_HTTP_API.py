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

    def test_get_projectimages(self, server):
        r = get("projects/1/images")
        known_data = [
            "c1d5bc9dd5ab0a70087bf121c884d755",
            "e5161f8d5c2166b43f1d2068c2c555ff",
            "7504ebd5c2d99bd1d13964591d28a3d6",
            "4a49b555102d0aa722dda5287fc69958",
            "035e3cd51dace05c50ce2fc9642d040c",
            "8e74f9106c86e8afb2e36de8ae730ddc",
            "c54b0a1584973549b909c314d88c7292",
            "3e41d9898131c921336de1f1da676b4f",
            "523fc6bd7563f26df178cef97d0afbe6",
            "b758dfe59d400755cf97ea0c0f70eaa8",
            "c54cd72620b647cbfe77aebe098b4711",
            "963cabed471a8c80f9ab477d7812dda2",
            "37d3c3a43008c97f7397dccef54fdda1",
            "181fc394f27417dfa9010e88792e3150",
            "617ab1266f0b317fccc5f7cb3b8fb584",
            "6e61eaae783328a217e6297ff586622c",
            "cf2aa58df8e4fcb0ef627158b6ddf08c",
        ]
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
