"""
Downloads a clip of the source video, as defined in a YAML params file
(default clip_params.yaml), without doing any analysis.

Usage:
    python download_clip.py [params_file]
"""

import sys

import yaml

from video_utils import (
    download_youtube_video,
    get_video_info,
    print_video_info,
)

PARAMS_FILE = "clip_params.yaml"


def load_params(params_file):
    with open(params_file) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    params_file = sys.argv[1] if len(sys.argv) > 1 else PARAMS_FILE
    params = load_params(params_file)

    print_video_info(get_video_info(params["VIDEO_URL"]))

    start_time = params["START_TIME"]
    print(
        f"\nDownloading {params['DURATION']}s clip starting at "
        f"{start_time}s to '{params['OUTPUT_FILENAME']}'..."
    )
    download_youtube_video(
        params["VIDEO_URL"],
        output_filename=params["OUTPUT_FILENAME"],
        start_time=start_time,
        end_time=start_time + params["DURATION"],
    )
