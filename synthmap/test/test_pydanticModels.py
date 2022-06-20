# pylint: disable=R0201

import importlib.resources
import os
from pathlib import Path

import pytest

from synthmap.models import colmap as colmodels


TEST_ROOT = importlib.resources.files("synthmap.test")


class TestColmap:
    def test_project_construction(self, sample_project_data):
        project_path = os.path.join(TEST_ROOT, "sample_data", "project.ini")
        db_path = os.path.join(TEST_ROOT, "sample_data", "big_images.db")
        image_path = os.path.join(TEST_ROOT, "sample_data", "sample_big_images")
        projmodel = colmodels.ColmapProject(**sample_project_data["known_good"][0])
        assert projmodel.dict() == {
            "db_path": Path(db_path),
            "image_path": Path(image_path),
            "project_type": "colmap",
            "label": project_path,
            "cameras": None,
            "images": None,
            "keypoints": None,
            "descriptors": None,
            "matches": None,
            "geometries": None,
        }

    def test_load_cameras(self, colmap_project_model):
        colmap_project_model.load_cameras()
        assert len(colmap_project_model.cameras) == 17

    def test_load_images(self, colmap_project_model):
        colmap_project_model.load_images()
        assert len(colmap_project_model.images) == 17

    def test_load_keypoints(self, colmap_project_model):
        colmap_project_model.load_keypoints()
        assert len(colmap_project_model.keypoints) == 17

    def test_load_descriptors(self, colmap_project_model):
        colmap_project_model.load_descriptors()
        assert len(colmap_project_model.descriptors) == 17

    def test_load_matches(self, colmap_project_model):
        colmap_project_model.load_matches()
        l = len(colmap_project_model.matches)
        assert 100 < l < 150

    def test_load_geometries(self, colmap_project_model):
        colmap_project_model.load_geometries()
        l = len(colmap_project_model.geometries)
        print("geoms:", colmap_project_model.geometries)
        assert 100 < l < 150

    def test_load_all(self, colmap_project_model, sample_project_data):
        twin_project_model = colmodels.ColmapProject(
            **sample_project_data["known_good"][0]
        )
        twin_project_model.load_all()
        assert twin_project_model.is_eq(colmap_project_model)
