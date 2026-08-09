from video_utils import (
    get_video_info,
    print_video_info,
    sample_and_crop_youtube_clip,
)

if __name__ == "__main__":
    # Sample a 4-second clip at 16 fps and crop to the central-upper region
    VIDEO_URL = "https://www.youtube.com/watch?v=g6Ye4xwXyAw"

    print_video_info(get_video_info(VIDEO_URL))

    sample_and_crop_youtube_clip(
        VIDEO_URL,
        start_time=10,
        duration=10,
        fps=30,
        x_frac=(0.25, 0.75),
        y_frac=(0.0, 0.8),
        video_filename="clip.mp4",
        output_dir="yt_frames_cropped",
    )
