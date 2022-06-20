import importlib.resources
import os

import pytest

from synthmap.projectManager import aliceParser
from synthmap.models import alice as alicemodels


TEST_ROOT = importlib.resources.files("synthmap.test")


@pytest.fixture
def known_projects():
    return [str(TEST_ROOT / "sample_data" / "meshroom_big_images" / "sfm.json")]


class TestParser:
    def test_sfm_construction(self, known_projects):
        proj_data = aliceParser.parse_sfm(known_projects[0])
        assert alicemodels.AliceProject(**proj_data)
