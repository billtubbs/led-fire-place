"""
Searches a downloaded clip for the best loop of a given length range.

Every frame is cropped and converted to 1593 LED values (the same
conversion used for the display), and a loop from frame t to frame t + g
(played t, ..., t + g - 1, then back to t) is scored by the RMS difference
between the LED frames either side of the seam:

    frames t - k, ..., t + k - 1  vs.  t + g - k, ..., t + g + k - 1

so the flame motion has to match across the join, not just one frame.
Only gaps g in [MIN_LOOP_SECONDS, MAX_LOOP_SECONDS] are computed (a band
of the full frame-to-frame distance matrix).

Writes the top candidates to LOOP_CANDIDATES_FILE and, for each one, a
short video of the cropped source around the seam to LOOP_SEAMS_DIR.

Usage:
    python find_loops.py [params_file]
"""

import csv
import sys
from pathlib import Path

import cv2
import numpy as np
from display1593.image_conversion import convert_image, prepare_image
from PIL import Image

from download_clip import load_params
from video_utils import crop_frame

PARAMS_FILE = "clip_params.yaml"
BLOCK_SIZE = 500  # rows of the distance band computed at a time
SEAM_PREVIEW_SECONDS = 3  # each side of the seam in the preview videos


def compute_led_frames(video_path, x_frac, y_frac):
    """
    Reads every frame of a video in order, crops it and converts it to
    1593 RGB LED values. Returns (frames, fps), frames shape (n, 1593, 3).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file '{video_path}'")
    fps = cap.get(cv2.CAP_PROP_FPS)
    n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Converting {n_total} frames of '{video_path}' to LED values...")
    led_frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cropped = crop_frame(frame, x_frac=x_frac, y_frac=y_frac)
        image = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        led_frames.append(convert_image(prepare_image(image)))
        if len(led_frames) % 1800 == 0:
            print(f"  {len(led_frames)} / {n_total}")
    cap.release()
    return np.array(led_frames, dtype="uint8"), fps


def load_or_compute_led_frames(params):
    path = Path(params["LED_FRAMES_FILE"])
    if path.exists():
        print(f"Loading cached LED frames from '{path}'")
        data = np.load(path)
        return data["led_frames"], float(data["fps"])
    led_frames, fps = compute_led_frames(
        params["OUTPUT_FILENAME"], params["CROP_X_FRAC"], params["CROP_Y_FRAC"]
    )
    np.savez_compressed(path, led_frames=led_frames, fps=fps)
    print(f"Saved LED frames to '{path}'")
    return led_frames, fps


def distance_band(x, min_gap, max_gap):
    """
    Squared RMS distance between rows t and t + g of x, for every t and
    every gap g in [min_gap, max_gap]. Returns array shape
    (max_gap - min_gap + 1, n) with NaN where t + g is past the end.
    """
    n = x.shape[0]
    gaps = np.arange(min_gap, max_gap + 1)
    band = np.full((len(gaps), n), np.nan, dtype="float32")
    sq_norms = (x**2).sum(axis=1)
    for i0 in range(0, n - min_gap, BLOCK_SIZE):
        i1 = min(i0 + BLOCK_SIZE, n - min_gap)
        j0, j1 = i0 + min_gap, min(i1 + max_gap, n)
        # |a - b|^2 = |a|^2 + |b|^2 - 2 a.b, as one matrix product
        d2 = (
            sq_norms[i0:i1, None]
            + sq_norms[None, j0:j1]
            - 2 * x[i0:i1] @ x[j0:j1].T
        )
        rows = np.arange(i1 - i0)
        for k, g in enumerate(gaps):
            cols = rows + g - min_gap
            ok = cols < j1 - j0
            band[k, i0 + rows[ok]] = d2[rows[ok], cols[ok]]
    return np.maximum(band, 0) / x.shape[1]


def seam_scores(band, half_window):
    """
    RMS of band over frames t - half_window ... t + half_window - 1 for
    each t (inf where the window runs off either end of the clip).
    """
    w = 2 * half_window
    valid = ~np.isnan(band)
    csum = np.cumsum(np.where(valid, band, 0), axis=1, dtype="float64")
    ccount = np.cumsum(valid, axis=1)
    pad = np.zeros((band.shape[0], 1))
    csum = np.hstack([pad, csum])
    ccount = np.hstack([pad, ccount])
    scores = np.full(band.shape, np.inf)
    t = np.arange(half_window, band.shape[1] - half_window + 1)
    window_sum = csum[:, t + half_window] - csum[:, t - half_window]
    window_count = ccount[:, t + half_window] - ccount[:, t - half_window]
    scores[:, t] = np.where(
        window_count == w, np.sqrt(window_sum / w), np.inf
    )
    return scores


def best_candidates(scores, min_gap, n_candidates, min_separation):
    """
    Picks the n_candidates lowest-scoring (start, gap) loops, skipping any
    whose start and end are both within min_separation frames of an
    already-picked loop.
    """
    order = np.argsort(scores, axis=None)
    picked = []
    for idx in order:
        k, t = np.unravel_index(idx, scores.shape)
        if not np.isfinite(scores[k, t]):
            break
        start, end = t, t + min_gap + k
        if all(
            abs(start - s) >= min_separation or abs(end - e) >= min_separation
            for s, e, _ in picked
        ):
            picked.append((start, end, scores[k, t]))
            if len(picked) == n_candidates:
                break
    return picked


def save_seam_preview(video_path, start, end, fps, x_frac, y_frac, path):
    """
    Writes a video of the cropped source playing up to the end of the loop
    and then on from its start, i.e. what the seam will look like.
    """
    n = round(SEAM_PREVIEW_SECONDS * fps)
    cap = cv2.VideoCapture(video_path)
    writer = None
    for first, last in [(end - n, end), (start, start + n)]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, first)
        for _ in range(last - first):
            ret, frame = cap.read()
            if not ret:
                break
            frame = crop_frame(frame, x_frac=x_frac, y_frac=y_frac)
            if writer is None:
                height, width = frame.shape[:2]
                writer = cv2.VideoWriter(
                    str(path),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (width, height),
                )
            writer.write(frame)
    writer.release()
    cap.release()


if __name__ == "__main__":
    params_file = sys.argv[1] if len(sys.argv) > 1 else PARAMS_FILE
    params = load_params(params_file)

    led_frames, fps = load_or_compute_led_frames(params)
    n = led_frames.shape[0]
    x = led_frames.reshape(n, -1).astype("float32")
    min_gap = round(params["MIN_LOOP_SECONDS"] * fps)
    max_gap = round(params["MAX_LOOP_SECONDS"] * fps)
    half_window = round(params["SEAM_HALF_WINDOW_SECONDS"] * fps)
    print(
        f"{n} frames at {fps} fps; searching loops of {min_gap}-{max_gap} "
        f"frames, seam window +/-{half_window} frames"
    )

    band = distance_band(x, min_gap, max_gap)
    scores = seam_scores(band, half_window)

    # Reference levels for the seam scores (same RMS units, 0-255 scale)
    consecutive = np.sqrt(((x[1:] - x[:-1]) ** 2).mean(axis=1))
    print(
        "\nRMS LED difference between consecutive frames: "
        f"median {np.median(consecutive):.2f}, "
        f"90th percentile {np.percentile(consecutive, 90):.2f}"
    )
    print(
        "RMS LED difference across a typical loop gap: "
        f"median {np.sqrt(np.nanmedian(band)):.2f}"
    )

    candidates = best_candidates(
        scores,
        min_gap,
        params["N_CANDIDATES"],
        round(params["MIN_CANDIDATE_SEPARATION_SECONDS"] * fps),
    )

    seams_dir = Path(params["LOOP_SEAMS_DIR"])
    seams_dir.mkdir(exist_ok=True)
    print(f"\n{'rank':>4}  {'start (s)':>9}  {'end (s)':>8}  "
          f"{'length (s)':>10}  {'seam RMS':>8}")
    rows = []
    for rank, (start, end, score) in enumerate(candidates):
        print(
            f"{rank:4d}  {start / fps:9.2f}  {end / fps:8.2f}  "
            f"{(end - start) / fps:10.2f}  {score:8.2f}"
        )
        rows.append(
            [rank, start, end, f"{start / fps:.3f}", f"{end / fps:.3f}",
             f"{(end - start) / fps:.3f}", f"{score:.3f}"]
        )
        save_seam_preview(
            params["OUTPUT_FILENAME"],
            start,
            end,
            fps,
            params["CROP_X_FRAC"],
            params["CROP_Y_FRAC"],
            seams_dir / f"seam_{rank:02d}_{start / fps:.2f}s_{end / fps:.2f}s.mp4",
        )

    with open(params["LOOP_CANDIDATES_FILE"], "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["rank", "start_frame", "end_frame", "start_s", "end_s",
             "length_s", "seam_rms"]
        )
        writer.writerows(rows)
    print(
        f"\nSaved candidates to '{params['LOOP_CANDIDATES_FILE']}' and seam "
        f"previews to '{seams_dir}/'. Loop = frames start_frame to "
        "end_frame - 1."
    )
