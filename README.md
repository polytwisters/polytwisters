# Polytwisters

[Polytwisters](https://www.polytope.net/hedrondude/twisters.htm) are a class of strange curved four-dimensional shapes related to [uniform polyhedra](https://en.wikipedia.org/wiki/Uniform_polyhedron) and [Hopf fibration](https://en.wikipedia.org/wiki/Hopf_fibration). They were discovered by Jonathan Bowers circa 2007, who found 222 of these shapes plus three infinite families, and produced POV-Ray renders of their 3D cross sections.

This repository is a project to clean up and port the original POV-Ray code (unpublished) to a modern toolchain using Blender's Python scripting capabilities. Computing the polytwisters as meshes enables professional-quality animations, as well as digital fabrication for realizing physical cross sections.

## Running the scripts

This has only been tested on macOS, but should also work on Linux. You must have Blender installed, and ffmpeg and ImageMagick if you want to make a video.

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
