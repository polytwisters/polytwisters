import argparse
import json
import pathlib

from . import common


def export_directory_as_blend(in_dir, out_file):
    common.run_blender_script(
        common.BLENDER_SCRIPT,
        blender_args=[],
        script_args=[str(in_dir.resolve()), "-o", str(out_file)],
        interactive=False,
    )


def export_multiple_directories_as_blends(in_dir, out_dir):
    out_dir.mkdir()
    with open(in_dir / "manifest.json") as file:
        manifest = json.load(file)
    blend_file_names = []
    for polytwister_name in manifest["polytwister_names"]:
        blend_file_name = polytwister_name + ".blend"
        export_directory_as_blend(
            in_dir / polytwister_name,
            out_dir / blend_file_name
        )
    with open(out_dir / "manifest.json", "x") as file:
        json.dump({
            "directory_type": "blend_files",
            "blend_file_names": blend_file_names
        }, file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir", type=str)
    parser.add_argument("out", type=str)
    args = parser.parse_args()

    in_dir = pathlib.Path(args.in_dir)
    out = pathlib.Path(args.out)

    with open(in_dir / "manifest.json") as file:
        manifest = json.load(file)
    if manifest["directory_type"] == "sections_of_multiple_polytwisters":
        export_multiple_directories_as_blends(in_dir, out)
    else:
        export_directory_as_blend(in_dir, out)


if __name__ == "__main__":
    main()
