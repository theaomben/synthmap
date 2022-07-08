"""Defines the CLI commands for making smaller images while preserving EXIF data."""
import os
from pathlib import Path

import rich_click as click


from synthmap.db import manager as db_man
from synthmap.log.logger import getLogger
from synthmap.imageProcessing import imgproc


log = getLogger(__name__)


@click.command()
@click.option(
    "-i",
    "--image-path",
    "--input",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path of the image file to be resized.",
)
@click.option(
    "-o",
    "--output-path",
    "--output",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path of the directory in which to store the resized image.",
)
@click.option(
    "--max-size",
    "--size",
    default=3000,
    type=int,
    help="Desired size in pixels for the image's biggest edge.",
)
@click.option(
    "--orig-uri",
    default=None,
    type=str,
    help="Original URI of the source image.",
)
@click.option(
    "--orig-ipfs",
    default=None,
    type=str,
    help="Original ipfs address of the source image.",
)
@click.option(
    "--register-images",
    default=False,
    is_flag=True,
    help="Register the resulting image into the current workspace.",
)
@click.pass_context
def resize(
    ctx, image_path, output_path, max_size, orig_uri, orig_ipfs, register_images
):
    """Makes a resized copy of the input image in the output directory.
    Preserves aspect ratio and EXIF data. Will error if max_size > max(image.shape)"""
    image_path = Path(image_path)
    output_path = Path(output_path)
    fname, fext = image_path.parts[-1].split(".", maxsplit=1)
    destination_path = os.path.join(output_path, f"{fname}-{max_size}{fext}")
    imgproc.resize(image_path, destination_path, max_size)
    if register_images:
        with db_man.mk_conn(ctx.obj["db_path"]) as db:
            file_id = db_man.insert_image(db, destination_path, orig_uri, orig_ipfs)
            orig_image_id = db_man.filepath2image(db, image_path)
            db_man.register_image_view(db, orig_image_id, file_id)
