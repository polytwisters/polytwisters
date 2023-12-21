import argparse
import json
import pathlib

import tqdm

from .core.all_polytwisters import get_all_polytwisters
from .core import section
from .blender import export_blends


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--num-frames",
        type=int,
        default=100,
        help="Number of animation frames."
    )
    parser.add_argument("out", type=str, help="Output directory.")
    args = parser.parse_args()

    with open("config.json") as file:
        full_config = json.load(file)
    config = {}
    config.update(full_config.get("defaults", {}))
    config.update(
        full_config.get("polytwisters", {}).get(polytwister_name, {})
    )

    num_frames = args.num_frames

    root_out_dir = pathlib.Path(args.out)
    root_out_dir.mkdir(exist_ok=True)

    polytwister_names = []

    all_polytwisters = get_all_polytwisters()

    for name, polytwister in tqdm.tqdm(all_polytwisters.items()):
        type_ = polytwister["type"]
        polytwister_root_dir = root_out_dir / name
        if polytwister_root_dir.exists():
            polytwister_names.append(name)
            continue

        tqdm.tqdm.write(f"Computing {type_} polytwister '{name}'...")

        sections_dir = polytwister_root_dir / "sections"
        blend_file = polytwister_root_dir / "animation.blend"

        section.render_all_sections_as_objs(
            polytwister, num_frames, sections_dir, progress_bar=True
        )
        with open(sections_dir / "config.json", "x") as file:
            json.dump(config, file)
        export_blends.export_directory_as_blend(sections_dir, blend_file)

        polytwister_names.append(name)
        with open(root_out_dir / "manifest.json", "w") as file:
            json.dump({
                "directory_type": "sections_of_multiple_polytwisters",
                "polytwister_names": polytwister_names
            }, file)


if __name__ == "__main__":
    main()