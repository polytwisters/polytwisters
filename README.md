# Polytwisters

[Polytwisters](https://www.polytope.net/hedrondude/twisters.htm) are a class of strange curved four-dimensional shapes related to [uniform polyhedra](https://en.wikipedia.org/wiki/Uniform_polyhedron) and [Hopf fibration](https://en.wikipedia.org/wiki/Hopf_fibration). They were discovered by Jonathan Bowers circa 2007, who found 222 of these shapes plus three infinite families, and produced POV-Ray renders of their 3D cross sections.

This repository is a project to clean up and port the original POV-Ray code (unpublished) to a modern toolchain using Blender's Python scripting capabilities. Computing the polytwisters as meshes enables professional-quality animations, as well as digital fabrication for realizing physical cross sections.

**This software is in an early stage of development.** You will probably have to make some minor changes to get it working on your machine.

## Project structure

This software has many components due to some feature creep, and has gotten fairly messy. However, those components are fairly cleanly separated.

* `core`: All geometric specifications of polytwisters, and code to compute them as meshes.
  * `hard_polytwisters.py` and `soft_polytwisters.py` contain declarative definitions of polytwisters based on the locations of their rings or cycloplanes. These scripts are nearly dependency-free, although `soft_polytwisters.py` requires NumPy.
  * `make_soft_polytwister.py` takes definitions from `soft_polytwisters.py` and renders a cross section as a Wavefront OBJ file. It requires SciPy for 4D and 3D convex hull computation (which internally uses QHull).
  * `make_hard_polytwister.py` takes a definition from `hard_polytwisters.py` and allows rendering a single Wavefront OBJ cross section, a directory of .obj cross sections, a single .svg file, or a montage of .svg files. It requires CadQuery. Unfortunately CadQuery does not run on Python 3.11 as of this writing due a dependency on nlopt, so you will nee to use Python 3.8-3.10.
* `scripts`: Somewhat disorganized scripts for processing the output of the above scripts and computing animations.
  * `blender_script.py` is a Blender Python script that takes a directory of .obj cross sections and rolls them into an animation with proper studio lighting and materials. It must be run with the Blender Python interpreter, not a standard Python interpreter.
  * `blender_wrapper.py` is a small wrapper that runs `blender_script.py` with the Blender Python interpreter.
  * `make_gif.py` converts a video to a GIF with ffmpeg, as animated GIF functionality is not provided by Blender.

## Basic usage

I've managed to run this on macOS, Linux, and Windows. Requirements:

* Blender 3.3
* Python 3.8-3.10 with these deps: `pip install numpy scipy cadquery`. Python 3.11 does NOT work as of this writing.
* ffmpeg for GIF conversion.

Generate 100 OBJ files for the cross sections of the tetratwister to the `tetratwister_obj` directory:

```
python core/make_hard_polytwister.py tetratwister -n 100 -f obj tetratwister_obj/
```

Load these files interactively as a Blender animation:

```
python scripts/blender_wrapper.py tetratwister_obj
```

Initially the animation is at frame 1, which is empty. Drag around the animation frame to view different cross sections.

## Other goodies

To generate a SVG vector lineart montage: 

```
python core/make_hard_polytwister.py tetratwister -f svg_montage tetratwister_svg
```

See `python core/make_hard_polytwister.py --help` for full options.

## Cycloplane research code

This repo also includes code for an ongoing research effort to gather experimental data on how the boundaries of cycloplanes constructed from Hopf fibers intersect. `cycloplanes.py` implements the algorithms for analysis while `test_cycloplane.py` runs experiments using both random and fixed cycloplane configurations. All randomness is seeded, so the tests are deterministic.

Install `numpy scipy pytest`, then run `pytest`.
