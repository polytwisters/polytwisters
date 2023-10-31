import argparse
import json
import pathlib

from . import common


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir", type=str)
    parser.add_argument("out_dir", type=str)
    args = parser.parse_args()

    root_in_dir = pathlib.Path(args.in_dir)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir()

    with open(root_in_dir / "manifest.json") as file:
        manifest = json.load(file)
    for polytwister_name in manifest["polytwister_names"]:
        dir_ = root_in_dir / polytwister_name
        out_file = out_dir / (polytwister_name + ".blend")
        common.run_blender_script(
            common.BLENDER_SCRIPT,
            blender_args=[],
            script_args=[dir_, "-o", str(out_file)],
            interactive=False,
        )


if __name__ == "__main__":
    main()