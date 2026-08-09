from video_utils import sample_and_crop_youtube_clip

if __name__ == "__main__":
    # Sample a 4-second clip at 16 fps and crop to the central-upper region
    VIDEO_URL = "https://www.youtube.com/watch?v=g6Ye4xwXyAw"

    sample_and_crop_youtube_clip(
        VIDEO_URL,
        start_time=10,
        duration=4,
        fps=16,
        x_frac=(0.3, 0.7),
        y_frac=(0.0, 0.5),
        video_filename="clip.mp4",
        output_dir="yt_frames_cropped",
    )
