from pathlib import Path

import cv2
import numpy as np

from video_utils import (
    download_youtube_video,
    extract_frames_at_fps,
    get_video_info,
    print_video_info,
)

VIDEO_URL = "https://www.youtube.com/watch?v=g6Ye4xwXyAw"

# Analysis window: how much of the video to sample and compare. A longer
# window catches longer loop periods but costs more download/compute time.
ANALYSIS_START = 0  # seconds
ANALYSIS_DURATION = 60  # seconds

# None = sample every frame at the video's native fps. The pairwise RMSE
# matrix grows with the square of the frame count, so for a long
# ANALYSIS_DURATION this can get slow/memory-hungry - set an explicit lower
# fps here (e.g. 2) to subsample if needed.
SAMPLE_FPS = None

# Ignore pairs of frames closer together than this: adjacent frames of any
# video look similar just from temporal continuity, which isn't evidence of
# looping/stitching.
MIN_GAP_SECONDS = 5

THUMB_SIZE = (64, 64)  # frames are downscaled to this before comparing

SIMILARITY_LIST_SIZE = 1000  # size of the running most-similar-pairs list
CONSOLE_PREVIEW_SIZE = 20  # how many of those to print to the console
IMAGES_TO_SAVE = 10  # how many of those to save as image pairs


def compute_thumbnails(frames, size=THUMB_SIZE):
    """Downscales frames to greyscale thumbnails, flattened for comparison."""
    thumbs = np.stack(
        [
            cv2.cvtColor(
                cv2.resize(frame, size, interpolation=cv2.INTER_AREA),
                cv2.COLOR_BGR2GRAY,
            )
            for frame in frames
        ]
    ).astype(float)
    return thumbs.reshape(len(frames), -1)


def pairwise_rmse(thumbnails):
    """Returns an (n, n) matrix of RMSE between every pair of thumbnails."""
    sq_norms = np.sum(thumbnails**2, axis=1)
    dist_sq = (
        sq_norms[:, None] + sq_norms[None, :] - 2 * thumbnails @ thumbnails.T
    )
    dist_sq = np.clip(dist_sq, 0, None)
    return np.sqrt(dist_sq / thumbnails.shape[1])


def find_similar_frame_pairs(rmse_matrix, timestamps, min_gap_seconds, top_n):
    """
    Ranks frame pairs more than min_gap_seconds apart by RMSE (most similar
    first) and returns the top_n as (rmse, i, j) tuples.
    """
    n = len(timestamps)
    gap = np.abs(timestamps[:, None] - timestamps[None, :])
    iu = np.triu_indices(n, k=1)
    valid = gap[iu] >= min_gap_seconds
    i_idx, j_idx = iu[0][valid], iu[1][valid]
    d_vals = rmse_matrix[iu][valid]

    order = np.argsort(d_vals)[:top_n]
    return [(d_vals[k], i_idx[k], j_idx[k]) for k in order]


def report_loop_period(pairs, timestamps):
    """Checks whether the best-matching pairs cluster around one time gap."""
    if not pairs:
        print("\nNo candidate pairs found.")
        return
    gaps = np.array([timestamps[j] - timestamps[i] for _, i, j in pairs])
    rounded = np.round(gaps).astype(int)
    values, counts = np.unique(rounded, return_counts=True)
    best_gap = values[np.argmax(counts)]
    votes = counts.max()
    print(
        f"\nMost common gap among the top {len(pairs)} matches: "
        f"~{best_gap}s ({votes}/{len(pairs)} agree)."
    )
    if votes >= len(pairs) // 2:
        print(
            f"This is consistent with the video looping every ~{best_gap}s "
            "within the analysed window."
        )
    else:
        print(
            "Gaps are scattered rather than clustered, so there's no strong "
            "evidence of a short repeating loop in this window (the source "
            "footage may just be long/non-looping, or the loop period is "
            "longer than ANALYSIS_DURATION)."
        )


def save_similarity_list(pairs, timestamps, csv_path):
    """Saves the full ranked list of similar frame pairs to a CSV file."""
    rows = [
        (d, timestamps[i], timestamps[j], timestamps[j] - timestamps[i], i, j)
        for d, i, j in pairs
    ]
    np.savetxt(
        csv_path,
        rows,
        delimiter=",",
        header="rmse,t1,t2,gap,frame_i,frame_j",
        comments="",
        fmt=["%.4f", "%.3f", "%.3f", "%.3f", "%d", "%d"],
    )
    print(f"Saved similarity list of {len(pairs)} pairs to '{csv_path}'.")


def save_candidate_pairs(frames, pairs, timestamps, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for rank, (d, i, j) in enumerate(pairs):
        prefix = f"pair_{rank:02d}_t{timestamps[i]:.2f}s_t{timestamps[j]:.2f}s_rmse{d:.2f}"
        cv2.imwrite(str(output_dir / f"{prefix}_a.jpg"), frames[i])
        cv2.imwrite(str(output_dir / f"{prefix}_b.jpg"), frames[j])
    print(f"Saved {len(pairs)} candidate frame pairs to '{output_dir}'.")


if __name__ == "__main__":
    video_info = get_video_info(VIDEO_URL)
    print_video_info(video_info)

    sample_fps = SAMPLE_FPS or video_info["fps"]

    print(
        f"\nDownloading {ANALYSIS_DURATION}s analysis clip starting at "
        f"{ANALYSIS_START}s..."
    )
    video_path = download_youtube_video(
        VIDEO_URL,
        output_filename="analysis_clip.mp4",
        start_time=ANALYSIS_START,
        end_time=ANALYSIS_START + ANALYSIS_DURATION,
    )

    frames = extract_frames_at_fps(
        video_path, fps=sample_fps, duration=ANALYSIS_DURATION
    )
    timestamps = np.arange(len(frames)) / sample_fps

    print(f"Comparing {len(frames)} sampled frames by RMSE...")
    thumbnails = compute_thumbnails(frames)
    rmse_matrix = pairwise_rmse(thumbnails)

    pairs = find_similar_frame_pairs(
        rmse_matrix, timestamps, MIN_GAP_SECONDS, SIMILARITY_LIST_SIZE
    )

    print(
        f"\nTop {min(CONSOLE_PREVIEW_SIZE, len(pairs))} of {len(pairs)} most "
        f"similar non-adjacent frame pairs "
        f"(potential loop points / stitching candidates):"
    )
    print(f"{'RMSE':>8}  {'t1 (s)':>8}  {'t2 (s)':>8}  {'gap (s)':>8}")
    for d, i, j in pairs[:CONSOLE_PREVIEW_SIZE]:
        print(
            f"{d:8.3f}  {timestamps[i]:8.2f}  {timestamps[j]:8.2f}  "
            f"{timestamps[j] - timestamps[i]:8.2f}"
        )

    report_loop_period(pairs, timestamps)
    save_similarity_list(pairs, timestamps, csv_path="frame_similarity.csv")
    save_candidate_pairs(
        frames,
        pairs[:IMAGES_TO_SAVE],
        timestamps,
        output_dir="loop_candidates",
    )
