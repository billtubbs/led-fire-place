from video_utils import (
    get_video_info,
    print_video_info,
    sample_and_crop_youtube_clip,
)

if __name__ == "__main__":
    VIDEO_URL = "https://www.youtube.com/watch?v=g6Ye4xwXyAw"

    print_video_info(get_video_info(VIDEO_URL))

    # Best stitch-point pair found by analyse_video.py: RMSE 30.175 between
    # t=34.50s and t=65.00s within that script's analysis window, which
    # itself starts at ANALYSIS_START=60s into the source video - so the
    # absolute clip is 94.5s-125.0s (still a 30.5s gap). Sampling at 30 fps
    # and letting extract_frames_at_fps drop the trailing (non-inclusive)
    # frame at t=125.0s means the clip can loop from its last frame back to
    # its first with minimal visible discontinuity.
    sample_and_crop_youtube_clip(
        VIDEO_URL,
        start_time=94.5,
        duration=30.5,
        fps=30,
        x_frac=(0.25, 0.75),
        y_frac=(0.0, 0.8),
        video_filename="clip.mp4",
        output_dir="yt_frames_cropped",
    )
