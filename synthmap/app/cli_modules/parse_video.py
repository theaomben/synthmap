import rich_click as click  # import click


from synthmap.log.logger import getLogger
from synthmap.imageProcessing import imgproc


log = getLogger(__name__)


@click.command()
@click.option(
    "-i",
    "--video-path",
    "--input",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path of the video file to be parsed.",
)
@click.option(
    "-o",
    "--output-path",
    "--output",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path of the directory in which to store the extracted images.",
)
@click.option(
    "--frame-step",
    default=None,
    type=int,
    help="""Capture every Nth frame of the video. This value (in frames) or `--time_step`
(in seconds) must be specified.""",
)
@click.option(
    "--time-step",
    default=None,
    type=float,
    help="""Capture every Nth second of the video. Accepts non-integer values which it interprets
as seconds. Ignored if `--frame_step` is passed.""",
)
@click.option(
    "--register-images",
    default=False,
    is_flag=True,
    help="Register the resulting images into the current workspace. Default False. (See `--db-path`)",
)
@click.option(
    "--print-only",
    default=False,
    is_flag=True,
    help="Do not write anything to disk, only print information as it is parsed.",
)
def parse_video(
    video_path, output_path, frame_step, time_step, register_images, print_only
):
    """Extract JPEG images from video to a folder, optionally registering them into
    the current workspace."""
    for img_path in imgproc.parse_video(
        video_path, output_path, frame_step, time_step, print_only
    ):
        print(img_path)
        if register_images:
            raise NotImplementedError
