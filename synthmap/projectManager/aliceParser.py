import json
import os
from pathlib import Path


def resolve_folders(project_path, folder_path):
    """Used to transform AliceVision relative folder paths ("../../foo/bar") to
    absolute paths. Returns the absolute path merging the relative path with the project
    file's grandparent folder."""
    parent_p = list(Path(project_path).parents)[1]
    return os.path.join(parent_p, folder_path[6:])


def parse_sfm(file_path):
    data = {"file_path": file_path, "project_type": "alice"}
    with open(file_path) as fd:
        file_data = json.load(fd)
    if isinstance(file_data["featuresFolders"], list):
        fp = file_data["featuresFolders"][0]
        file_data["featuresFolders"] = resolve_folders(file_path, fp)
    if isinstance(file_data["matchesFolders"], list):
        fp = file_data["matchesFolders"][0]
        file_data["matchesFolders"] = resolve_folders(file_path, fp)
    return {**file_data, **data}
