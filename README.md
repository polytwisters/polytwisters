# Polytwisters

[Polytwisters](https://www.polytope.net/hedrondude/twisters.htm) are a class of strange curved four-dimensional shapes related to [uniform polyhedra](https://en.wikipedia.org/wiki/Uniform_polyhedron) and [Hopf fibration](https://en.wikipedia.org/wiki/Hopf_fibration). They were discovered by Jonathan Bowers circa 2007, who found 222 of these shapes plus three infinite families, and produced POV-Ray renders of their 3D cross sections.

This repository is a project to clean up and port the original POV-Ray code (unpublished) to a modern toolchain using Blender's Python scripting capabilities. Computing the polytwisters as meshes enables professional-quality animations, as well as digital fabrication for realizing physical cross sections.

**This software is in an early stage of development.** You will probably have to make some minor changes to get it working on your machine.

## Basic usage

I've managed to run this on macOS, Linux, and Windows. Requirements:

* Python 3.10 (Python 3.11 does not work due to the CadQuery dependency)
* [PDM](https://pdm.fming.dev/latest/)
* Blender 3.3
* ffmpeg if GIFs are desired.

Set up repo:

```
pdm install
```

Compute 50 cross sections of all currently entered polytwisters:

```
mkdir scratch
pdm run all_sections -n 50 scratch/objs
```

Export .blend files:

```
pdm run export_blends scratch/objs scratch/blends
```

When opening these Blender files, note that initially the animation is at frame 1, which is empty. Drag around the animation frame to view different cross sections.

## Other goodies

To generate a SVG vector lineart montage: 

```
python core/make_hard_polytwister.py tetratwister -f svg_montage tetratwister_svg
```

See `python core/make_hard_polytwister.py --help` for full options.

## Cycloplane research code

This repo also includes code for an ongoing research effort to gather experimental data on how the boundaries of cycloplanes constructed from Hopf fibers intersect. `cycloplanes.py` implements the algorithms for analysis while `test_cycloplane.py` runs experiments using both random and fixed cycloplane configurations. All randomness is seeded, so the tests are deterministic.

Install `numpy scipy pytest`, then run `pytest`.
