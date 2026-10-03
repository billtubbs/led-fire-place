"""
Converts the JPEG frames saved by extract_frames.py (yt_frames_cropped/)
into one LED CSV per frame (led_frames/) - the original 30.5s fireplace
clip. The current loop is generated with `gen-video-frames generate
clip_params.yaml` instead.
"""

from gen_video_frames.led_frames import generate_led_frames

if __name__ == "__main__":
    generate_led_frames(
        image_dir="yt_frames_cropped",
        output_dir="led_frames",
        dimness=6,
    )
