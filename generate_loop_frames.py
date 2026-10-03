"""
Writes the display LED data for the chosen loop (LOOP_START_FRAME to
LOOP_END_FRAME - 1 in the params file) to one compressed .npz file
(LOOP_FRAMES_FILE: array "led_frames", shape (n_frames, 1593, 3), uint8,
plus the source "fps"), from the LED values cached by find_loops.py.
Copy it to fireplace/data/fire_frames.npz in the display1593 repo.

Usage:
    python generate_loop_frames.py [params_file]
"""

import sys

import numpy as np

from download_clip import load_params
from find_loops import load_or_compute_led_frames
from generate_led_frames import scale_led_values

PARAMS_FILE = "clip_params.yaml"


if __name__ == "__main__":
    params_file = sys.argv[1] if len(sys.argv) > 1 else PARAMS_FILE
    params = load_params(params_file)

    led_frames, fps = load_or_compute_led_frames(params)
    start, end = params["LOOP_START_FRAME"], params["LOOP_END_FRAME"]
    loop = scale_led_values(led_frames[start:end], params["DIMNESS"])

    output_path = params["LOOP_FRAMES_FILE"]
    np.savez_compressed(output_path, led_frames=loop, fps=fps)
    print(
        f"Saved {len(loop)} LED frames ({len(loop) / fps:.2f}s at "
        f"{fps:.0f} fps, source frames {start}-{end - 1}) to '{output_path}'."
    )
