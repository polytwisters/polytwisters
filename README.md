# Polytwisters

Polytwisters are strange curved four-dimensional shapes discovered by Jonathan Bowers. This repository is a port of Bowers' original POV-Ray file to Python, using Blender scripting.

## Running the script

Assuming Blender is in your PATH:

    blender --python polytwisters_blender.py -- all 0.14

On macOS, alias `/Applications/Blender.app/Contents/MacOS/Blender` to `blender` before running the above.

The first argument after `--` is the name of the polytwister. The name must be in lowercase and either underscores or spaces may separate the words, such as `bloated_cubetwister`. Use `all` to render all polytwisters that have been ported. The second argument determines the coordinate of the cross section.
