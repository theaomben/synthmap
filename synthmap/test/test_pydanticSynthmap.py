class TestWorkspace:
    def test_setup(self, synthmap_workspace_model):
        synthmap_workspace_model.db_is_init(synthmap_workspace_model.db_path)

    def test_load_Projects(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Projects()
        assert len(synthmap_workspace_model.projects.keys()) == 1

    def test_load_ColmapProjects(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ColmapProjects()
        assert len(synthmap_workspace_model.colmapProjects.keys()) == 1

    def test_load_AliceProjects(self, synthmap_workspace_model):
        synthmap_workspace_model.load_AliceProjects()
        assert len(synthmap_workspace_model.aliceProjects.keys()) == 0

    def test_load_Images(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Images()
        assert len(synthmap_workspace_model.images.keys()) == 17

    def test_load_ProjectImages(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ProjectImages()
        assert len(synthmap_workspace_model.projectImages) == 17

    def test_load_ImageFiles(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ImageFiles()
        assert len(synthmap_workspace_model.imageFiles.keys()) == 17

    def test_load_ImageViews(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ImageViews()
        assert len(synthmap_workspace_model.imageViews.keys()) == 17

    def test_load_Entities(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Entities()
        assert len(synthmap_workspace_model.entities) == 2

    def test_load_ImageEntities(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ImageEntities()
        assert len(synthmap_workspace_model.imageEntities) == 7

    def test_load_ColmapScenes(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ColmapScenes()
        assert len(synthmap_workspace_model.colmapScenes.keys()) == 1

    def test_load_Sessions(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Sessions()
        assert len(synthmap_workspace_model.sessions.keys()) == 0

    def test_load_SessionImages(self, synthmap_workspace_model):
        synthmap_workspace_model.load_SessionImages()
        assert len(synthmap_workspace_model.sessionImages) == 0
