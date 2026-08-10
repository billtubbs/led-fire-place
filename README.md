# led-fire-place
Python scripts used to generate LED intensity data sequences to mimic fireplace video.

Click image below to see YouTube video of the LED fireplace:

[![IMAGE ALT TEXT](http://img.youtube.com/vi/rBeaxTevjns/0.jpg)](https://youtu.be/rBeaxTevjns "Video Title")

See also this instructables articles I wrote:
 - [Electronic LED Fireplace](https://www.instructables.com/Electronic-LED-Fireplace/)

## YouTube video sampling and LED frame generation

Scripts for pulling a clip from a YouTube fireplace video, analysing it for
loop points, and converting it into per-frame LED RGB intensity data for the
[display1593](https://github.com/billtubbs/display1593) 1593-LED display,
played back on a Raspberry Pi via `fireplace/play_fire_frames.py` in that
repo.

### Scripts

- **`video_utils.py`** - shared functions: `get_video_info`/`print_video_info`
  (fetch/print title, resolution, fps, duration, format), `download_youtube_video`
  (yt-dlp, optionally clipped to a start/end time range), `extract_frames_at_fps`
  (sample a local video file at a target fps by seeking to each timestamp),
  `crop_frame` (fractional rectangular crop), and `sample_and_crop_youtube_clip`
  (combines all of the above into one call).
- **`extract_frames.py`** - downloads and samples a specific clip (currently
  the 94.5s-125.0s / 30.5s @ 30fps range picked as the best available near-loop,
  see Results below), crops it, and saves the frames as JPEGs to
  `yt_frames_cropped/`.
- **`analyse_video.py`** - downloads a window of the video, samples every frame
  at native fps, downscales each to a 64x64 greyscale thumbnail, and computes
  the RMSE between every pair of frames more than `MIN_GAP_SECONDS` apart. Ranks
  the 1000 most similar pairs as loop/stitch-point candidates, checks whether
  their time gaps cluster around one period (evidence of a true repeating loop),
  saves the full ranked list to `frame_similarity.csv`, and saves the top pairs
  as images to `loop_candidates/` for visual inspection.
- **`generate_led_frames.py`** - converts a directory of image frames (e.g.
  `yt_frames_cropped/`) into 1593-LED RGB intensity CSVs (one file per frame,
  integer values, gamma-corrected to match the scaling `test_fire_frames.py`
  applies) using `prepare_image`/`convert_image` imported from the sibling
  `display1593` repo. Output goes to `led_frames/`, which then gets copied to
  `fireplace/data` on the Pi.

### Setup

Requires `ffmpeg` on the PATH (used by yt-dlp to trim clips) and Python 3.10+.

```
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install -e /path/to/display1593 --no-deps
```

The `display1593` package is installed editable with `--no-deps` so that
`generate_led_frames.py` can import its lightweight `image_conversion` module
(numpy/Pillow only) without pulling in the hardware-only dependencies
(`serial`, `numba`, `serial_comm`) that `Display1593` itself needs.

### Results

Analysed ["Cozy Fireplace 4K (12 hours)"](https://www.youtube.com/watch?v=g6Ye4xwXyAw)
for a repeating loop, using `analyse_video.py` over both a 300s window (2fps)
and a 60s window (native 30fps, every frame compared against every other).
In both cases the most similar non-adjacent frame pairs were visually similar
but clearly not identical (RMSE ~29-30 on downscaled thumbnails), and the time
gaps between top matches never clustered strongly around one period - i.e.
this is genuine long-form footage with no definite short loop, not a
short clip repeated by the uploader.

Since there's no natural loop point, `extract_frames.py` is instead
configured to sample a stretch that looks visually continuous
(94.5s-125.0s) as a manually-chosen near-loop; there will be a small
discontinuity at the seam.

## Archived content

The following relates to an earlier, separate ~90-LED cardboard fireplace
build (a different physical display to the 1593-LED display1593 project
above) and its own now-superseded video-processing pipeline.

### 1. Build LED display

I used just under 90 RGB WS2812 LEDS connected to a [Teensy microcontroller](https://www.pjrc.com/teensy/) running the [FastLED library](https://fastled.io).

To create a flame-like effect, I used strips of white paper glued to a carboard frame with the LEDs pushed through holes in a random pattern and black paper for the simulated logs.

<img src="images/led-fireplace-construction-sm.jpg" width=480></img>

### 2. Switch each LED on separately in a sequence and film it with a smartphone video camera

Here is the Arduino script for the Teensy:
 - [fire-test/fire-test.ino](fire-test/fire-test.ino)

### 3. Load video file and select a frame to represent the effect of each LED

See this Jupyter notebook:
- [Analyse-images-from-LED-display-video-capture.ipynb](Analyse-images-from-LED-display-video-capture.ipynb)

Frame from phone camera video:

<img src="images/im_010_adj.png" width=480></img>

### 4. Download a video from YouTube of a real fire in a fireplace and extract image frames

See this Jupyter notebook (superseded by `video_utils.py`/`extract_frames.py` above):
- [Prepare-data-from-YouTube-video.ipynb](Prepare-data-from-YouTube-video.ipynb)

I used this video on YouTube: [YouTube video](https://www.youtube.com/watch?v=L_LUpnjgPso):

### 5. Compute LED intensities to mimic the real fire video

This involves mimicking the LED display using the image masks for each LED and finding a set of LED intensities (RGB) that best reproduce the image.

<img src="images/fig_image_mask_opt.png">


See this Jupyter notebook (superseded by `generate_led_frames.py` above):
- [Load-Fire-Video-and-Compute-display-LED-intensities.ipynb](Load-Fire-Video-and-Compute-display-LED-intensities.ipynb)


### 6. Adjust LED intensities and upload to microcontroller

See this Jupyter notebook:
- [Process-data-for-LED-display.ipynb](Process-data-for-LED-display.ipynb)

Here is the final Arduino script to run the LED sequence on the Teensy:
 - [fire/fire_data.h](fire/fire_data.h)
 - [fire/fire.ino](fire/fire.ino)
