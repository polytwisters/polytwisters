# Polytwisters

Polytwisters are strange curved four-dimensional shapes discovered by Jonathan Bowers. This repository is a port of Bowers' original POV-Ray file to Python, using Blender scripting.

## Running the scripts

This has only been tested on macOS, but should also work on Linux. You must have Blender installed, and ffmpeg if you want to make a video.

Run the following and wait a few hours:

    python3 render_animation.py bloated_icosatwister

To compile the frames into a video at `out.mp4`:

    python3 make_video.py out/bloated_icosatwister

If you are impatient, you may run `make_video.py` during the execution of `render_animation.py` to see all frames so far. `render_animation.py` renders frames out of order so that the time resolution of the animation gradually increases.
