from datetime import timedelta
import math
import os

import rich_click as click  # import click
import cv2

from synthmap.log.logger import getLogger


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
    video = cv2.VideoCapture(video_path)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = round(video.get(cv2.CAP_PROP_FPS), 0)
    duration = timedelta(seconds=frame_count / fps)
    log.debug(f"Duration of file {video_path}: {duration}@{fps}FPS")
    if not frame_step or not isinstance(frame_step, int):
        if not time_step:
            raise ValueError
        frame_step = math.ceil(time_step * fps)
    count = 0
    done = 0
    log.debug("Begin seeking frames...")
    for frame_idx in range(0, frame_count, frame_step):
        while count < frame_idx:
            _, image = video.read()
            count += 1
        _, image = video.read()
        done += 1
        if print_only:
            log.debug(
                f"Fake writing #{done}: "
                + os.path.join(output_path, f"frame-{count}.JPG")
            )
        else:
            cv2.imwrite(os.path.join(output_path, f"frame-{count}.JPG"), image)
        count += 1
    log.debug("...done seeking.")
    if register_images:
        raise NotImplementedError
