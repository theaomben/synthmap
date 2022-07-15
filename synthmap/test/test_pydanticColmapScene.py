import importlib.resources


# from synthmap.models import colmapscene as colScene


TEST_ROOT = importlib.resources.files("synthmap.test")


class TestColmapScene:
    def test_scene_construction(self, colmap_scene):
        assert colmap_scene

    def test_load_cameras(self, colmap_scene):
        colmap_scene.parse_camera_file()

    def test_load_images(self, colmap_scene):
        colmap_scene.parse_image_file()

    def test_load_points(self, colmap_scene):
        colmap_scene.parse_point_file()
