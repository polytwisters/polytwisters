import argparse
import json
import pathlib
import subprocess

from . import common


def render_blend(in_file, out_file):
    subprocess.run(
        [
            common.BLENDER,
            "--background",
            str(in_file),
            # Order matters here! Set up the render format and output path first, then --render-anim.
            "--render-output",
            out_file.resolve() / "render_####.png",
            "--render-format",
            "PNG",
            "--render-anim",
        ],
        check=True,
    )


def render_directory_of_blends(in_dir, out_dir):
    with open(in_dir / "manifest.json") as file:
        manifest = json.load(file)
    out_dir.mkdir()
    for file_name in manifest["blend_files"]:
        in_file = in_dir / file_name
        render_blend(in_file, out_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("in", type=str)
    parser.add_argument("out", type=str)
    args = parser.parse_args()

    in_path = pathlib.Path(getattr(args, "in"))
    out_path = pathlib.Path(args.out)

    if in_path.is_file():
        render_blend(in_path, out_path)
    else:
        render_directory_of_blends(in_path, out_path)


if __name__ == "__main__":
    main()
