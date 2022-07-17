"""Defines the CLI commands for registering data into the synthmap DB."""
from glob import glob
import itertools
import os
from pathlib import Path

import rich_click as click  # import click

from synthmap.db import manager as db_man
from synthmap.log.logger import getLogger
from synthmap.models import colmap as colmodels, alice as alicemodels
from synthmap.projectManager import colmapParser, aliceParser


log = getLogger(__name__)


@click.group()
@click.option(
    "-i",
    "--root-folder",
    required=True,
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--exclude-folders",
    multiple=True,
    type=str,
)
@click.pass_context
def register(ctx, root_folder, exclude_folders):
    """Holds Item discovery methods.

    Used to find Items (Projects, Images, Entities...) in the local filesystem and
    add them to the current workspace.
    /!\\: this group's parameters must be passed *before* the Item's subcommand
    and its parameters. Note how the subcommand "image" appears after
    "register"'s --params:

        `cli register --root-folder XYZ --print-only images --some-img-param`"""
    ctx.obj["register_root"] = root_folder
    ctx.obj["exclude_folders"] = exclude_folders


@register.command()
@click.pass_context
def images(ctx):
    """Seeks all .JPG files under --root-folder"""
    log.info(f"Seeking Images under {ctx.obj['register_root']}")
    q_strings = [
        os.path.join(ctx.obj["register_root"], "**", "*") + f".{ext}"
        for ext in ["JPG", "jpg"]
    ]
    paths = list(
        itertools.chain.from_iterable(
            [glob(q_string, recursive=True) for q_string in q_strings]
        )
    )
    count = 0
    for path in paths:
        for exclude in ctx.obj["exclude_folders"]:
            if exclude in path:
                continue
        with db_man.mk_conn(ctx.obj["db_path"]) as db:
            db_man.insert_image(db, path)
            count += 1
    log.info(f"Found {count} images under {ctx.obj['register_root']}")


def seek_projects(ctx, filename, extractor_fn, model):
    """Applies the specified extractor function to all files matching the given filename
    under the root folder (see `cli register --root-folder`)."""
    q_string = os.path.join(ctx.obj["register_root"], f"**\\{filename}")
    for path in glob(q_string, recursive=True):
        excluded = False
        for exclude in ctx.obj["exclude_folders"]:
            if exclude in path:
                excluded = True
                break
        if excluded:
            continue
        data = extractor_fn(path)
        if not data:
            continue
        if data and not "label" in data:
            data["label"] = data.get("project_file") or data.get("file_path")
        log.debug(f"Found project data {data}")
        m = model(**data)
        yield m


@register.command()
@click.option(
    "--project-type",
    "--type",
    default="all",
    required=True,
    type=click.Choice(["all", "colmap", "alice"]),
)
@click.pass_context
def projects(ctx, project_type):
    """Seeks project files for different backends under --root-folder.
    Colmap: project.ini
    AliceVision: sfm.json"""
    candidates = []
    if project_type in ["all", "colmap"]:
        log.debug(f"Seeking Colmap Projects under {ctx.obj['register_root']}")
        candidates += seek_projects(
            ctx, "project.ini", colmapParser.get_proj_dirs, colmodels.ColmapProject
        )
    if project_type in ["all", "alice"]:
        log.debug(f"Seeking AliceVision Projects under {ctx.obj['register_root']}")
        candidates += seek_projects(
            ctx, "sfm.json", aliceParser.parse_sfm, alicemodels.AliceProject
        )
    log.debug(f"Found {len(candidates)} projects under {ctx.obj['register_root']}")
    with db_man.mk_conn(ctx.obj["db_path"]) as db:
        for project in candidates:
            project = {k: str(v) for k, v in dict(project).items()}
            project["project_file"] = project["label"]
            project_id = db_man.insert_project(db, project)
            colmapParser.register_project_images(db, project_id)
            for model_data in colmapParser.get_model_files(
                Path(project["project_file"]).parent.absolute()
            ):
                db_man.insert_scene(db, project_id, model_data)


@register.command()
@click.pass_context
def entities(ctx):
    """Not Implemented. Seeks entity files under --root-folder."""
    raise NotImplementedError
