"""
Writes the display LED data for the chosen loop (LOOP_START_FRAME to
LOOP_END_FRAME - 1 in the params file) as one CSV per frame, from the LED
values cached by find_loops.py.

Usage:
    python generate_loop_frames.py [params_file]
"""

import sys
from pathlib import Path

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

    output_dir = Path(params["LOOP_FRAMES_DIR"])
    output_dir.mkdir(exist_ok=True)
    for old_path in output_dir.glob("frame_*.csv"):
        old_path.unlink()
    for i, z in enumerate(loop):
        np.savetxt(
            output_dir / f"frame_{i:04d}.csv", z, fmt="%d", delimiter=","
        )
    print(
        f"Saved {len(loop)} LED frame CSVs ({len(loop) / fps:.2f}s at "
        f"{fps:.0f} fps, source frames {start}-{end - 1}) to '{output_dir}'."
    )
