from pathlib import Path

import numpy as np
from display1593.image_conversion import convert_image, prepare_image
from PIL import Image


def image_to_led_frame(image, dimness=6):
    """
    Converts a source image into 1593 gamma-corrected LED RGB values, ready
    to send directly to the display (matches the scaling test_fire_frames.py
    applies before calling set_all_leds).
    """
    return scale_led_values(convert_image(prepare_image(image)), dimness)


def scale_led_values(z, dimness=6):
    """
    Gamma-corrects and dims raw convert_image() output (0-255) into the
    values sent to the display.
    """
    z = z.astype(float) ** 2 / (256 * dimness)
    return z.astype("uint8")


def generate_led_frames(image_dir, output_dir, dimness=6, pattern="*.jpg"):
    """
    Converts every image in image_dir to a 1593x3 LED RGB frame and saves
    each as an integer CSV file (one row per LED) in output_dir.
    """
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(image_dir.glob(pattern))
    print(f"Converting {len(image_paths)} images from '{image_dir}'...")
    for image_path in image_paths:
        image = Image.open(image_path)
        z = image_to_led_frame(image, dimness=dimness)
        csv_path = output_dir / (image_path.stem + ".csv")
        np.savetxt(csv_path, z, fmt="%d", delimiter=",")

    print(f"Saved {len(image_paths)} LED frame CSVs to '{output_dir}'.")
    return image_paths


if __name__ == "__main__":
    generate_led_frames(
        image_dir="yt_frames_cropped",
        output_dir="led_frames",
        dimness=6,
    )
