# Polytwisters

[Polytwisters](https://www.polytope.net/hedrondude/twisters.htm) are a class of strange curved four-dimensional shapes related to [uniform polyhedra](https://en.wikipedia.org/wiki/Uniform_polyhedron) and [Hopf fibration](https://en.wikipedia.org/wiki/Hopf_fibration). They were discovered by Jonathan Bowers circa 2007, who found 222 of these shapes plus three infinite families, and produced POV-Ray renders of their 3D cross sections.

This repository is a project to clean up and port the original POV-Ray code (unpublished) to a modern toolchain using Blender's Python scripting capabilities. Computing the polytwisters as meshes enables professional-quality animations, as well as digital fabrication for realizing physical cross sections.

**This software is in an early stage of development.** You will probably have to make some minor changes to get it working on your machine.

## Overview

This software has many components due to some feature creep. However, those components are fairly cleanly separated. Here they are from most essential to least essential:

* `hard_polytwisters.py` and `soft_polytwisters.py`, which contain declarative definitions of polytwisters based on the locations of their rings or cycloplanes. These scripts are nearly dependency-free, although `soft_polytwisters.py` requires NumPy.
* `make_soft_polytwister.py` takes definitions from `soft_polytwisters.py` and renders their cross sections as meshes. It requires SciPy for 4D and 3D convex hull computation.
* `make_polytwister.py` uses all of the above to create a Blender project file for a given cross section. It can open up Blender interactively, can render an image, or export an STL mesh. It must be run in Blender (which can be done using Blender's command-line options).
** It runs `make_soft_polytwister` as a subprocess using the system Python, because getting the SciPy dependency into the Blender Python environment is a massive pain.
* `render_animation.py` repeatedly calls `make_polytwister.py` to render a full animation as a sequence of PNG files. It is to be run with the system Python.
** Why call Blender for each frame rather than using Blender's built-in animation feature? The main reason is for rendering frames out of order so the time resolution progressively increases. But I may change this in the future.
* `make_video.py` takes the output of `render_animation`, adds a background to each frame, and renders an MP4 video file.
* `gui.py` wraps up all the high-level features in a very crude GUI. It requires PySimpleGUI and a working Tkinter installation.
* `notify.py` allows you to use Twilio to send SMS to your phone. It's completely optional.

## Basic usage with GUI

I've managed to run this on macOS, Linux, and Windows. Requirements:

* Blender 3.3
* The following Python deps: `pip install numpy scipy PySimpleGUI twilio`. Last two are optional.
* A working version of Tkinter if you want to run a simple GUI. See here: https://stackoverflow.com/a/76105219.
* ffmpeg and ImageMagick if video export is desired.

To run GUI:

```
python3 gui.py  # macOS
py -3 gui.py  # Windows
```

## Advanced usage

To view a single cross section in the Blender GUI:

    blender --python make_polytwister.py -- bloated_icosatwister 0.13 --normalize

where `blender` is substituted with the path of the Blender executable, `bloated_icosatwister` is the name of a polytwister, and `0.13` is the W-coordinate of 3-space where the cross section is taken. `--normalize` is optional and ensures that the cross section is scaled to fit in the camera's view. The above command sets up a camera and lights and is ready for rendering a still image.

To render an animation, run the following and wait a few hours:

    python3 render_animation.py bloated_icosatwister

To compile the frames into a video at `out.mp4`:

    python3 make_video.py out/bloated_icosatwister

If you are impatient, you may run `make_video.py` during the execution of `render_animation.py` to see all frames so far. `render_animation.py` renders frames out of order so that the time resolution of the animation gradually increases.

To export all polytwisters as STL meshes, run:

    python3 export_meshes.py

## Cycloplane research code

This repo also includes code for an ongoing research effort to gather experimental data on how the boundaries of cycloplanes constructed from Hopf fibers intersect. `cycloplanes.py` implements the algorithms for analysis while `test_cycloplane.py` runs experiments using both random and fixed cycloplane configurations. All randomness is seeded, so the tests are deterministic.

Install `numpy scipy pytest`, then run `pytest`.
