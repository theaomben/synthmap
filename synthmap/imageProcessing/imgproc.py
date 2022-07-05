from datetime import timedelta
import math
import os
from typing import Tuple

import cv2
from exif import Image as EXIFImage
from PIL import Image as PILImage

from synthmap.log.logger import getLogger


log = getLogger(__name__)


def get_size(image_path) -> Tuple[int, int]:
    y, x, depth = cv2.imread(image_path).shape
    return x, y


def new_size(x: int, y: int, max_size: int = 3000) -> (int, int):
    if max((x, y)) < max_size:
        return (x, y)
    if x >= y:
        new_x = max_size
        new_y = int(y / (x / max_size))
    else:
        new_y = max_size
        new_x = int(x / (y / max_size))
    return new_x, new_y


def resize(src_p, dest_p, max_size: int = 3000):
    exifdata = EXIFImage(src_p)
    x, y = exifdata.pixel_x_dimension, exifdata.pixel_y_dimension
    if max(x, y, max_size) == max_size:
        log.warning(f"Desired resize ({max_size}px) would enlarge image {src_p}")
        return None
    new_x, new_y = new_size(x, y)
    with PILImage.open(src_p) as img:
        img_s = img.resize((new_x, new_y))
        img_s.save(dest_p, format="JPEG")
    destexif = EXIFImage(dest_p)
    destexif.focal_length = exifdata.focal_length
    destexif.focal_length_in_35mm_film = exifdata.focal_length_in_35mm_film
    with open(dest_p, "wb") as fd:
        fd.write(destexif.get_file())


def get_image_size(image_path):
    return cv2.imread(image_path).shape


def parse_video(video_path, output_path, frame_step, time_step, print_only):
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
    img_paths = []
    log.debug("Begin seeking frames...")
    for frame_idx in range(0, frame_count, frame_step):
        while count < frame_idx:
            _, image = video.read()
            count += 1
        _, image = video.read()
        done += 1
        target_path = os.path.join(output_path, f"frame-{count}.JPG")
        if print_only:
            log.debug(f"Fake writing #{done}: {target_path}")
        else:
            cv2.imwrite(target_path, image)
        yield target_path
        count += 1
    log.debug("...done seeking.")
