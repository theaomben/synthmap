class TestWorkspace:
    def test_setup(self, synthmap_workspace_model):
        synthmap_workspace_model.db_is_init(synthmap_workspace_model.db_path)

    def test_load_Projects(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Projects()

    def test_load_ColmapProjects(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ColmapProjects()

    def test_load_AliceProjects(self, synthmap_workspace_model):
        synthmap_workspace_model.load_AliceProjects()

    def test_load_Images(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Images()

    def test_load_ProjectImages(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ProjectImages()

    def test_load_ImageFiles(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ImageFiles()

    def test_load_ImageViews(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ImageViews()

    def test_load_Entities(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Entities()

    def test_load_ImageEntities(self, synthmap_workspace_model):
        synthmap_workspace_model.load_ImageEntities()

    def test_load_Sessions(self, synthmap_workspace_model):
        synthmap_workspace_model.load_Sessions()

    def test_load_SessionImages(self, synthmap_workspace_model):
        synthmap_workspace_model.load_SessionImages()
