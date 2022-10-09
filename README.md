# Polytwisters

Polytwisters are strange curved four-dimensional shapes discovered by Jonathan Bowers. This repository is a port of Bowers' original POV-Ray file to Python, using Blender scripting.

## Running the script

This has only been tested on macOS, but should also work on Linux. You must have Blender installed, and ffmpeg if you want to make a video.

Currently this script renders a demo animation of the quasioctatwister. Run the following:

    python3 main.py

Currently, rendering this animation takes about an hour. To compile the frames into a video at `out.mp4`:

    python3 make_video.py

If you are impatient, you may run `make_video.py` DURING the execution of the `main.py` script to see all frames so far. `main.py` renders frames out of order so that the time resolution of the animation gradually increases.
