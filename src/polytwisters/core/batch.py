import argparse
import json
import pathlib

import tqdm

from . import hard_polytwisters
from . import soft_polytwisters
from . import hard_polytwister_section
from . import soft_polytwister_section


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--num-frames",
        type=int,
        default=50,
        help="Number of animation frames."
    )
    parser.add_argument(
        "-sr",
        "--soft-resolution",
        type=int,
        default=100,
        help="Number of ring segments for soft polytwisters."
    )
    parser.add_argument("out", type=str, help="Output directory.")
    args = parser.parse_args()

    num_frames = args.num_frames
    soft_polytwister_resolution = args.soft_resolution

    root_out_dir = pathlib.Path(args.out)
    root_out_dir.mkdir(exist_ok=True)

    polytwister_names = []

    all_polytwisters = {}
    all_polytwisters.update(hard_polytwisters.get_all_hard_polytwisters())
    all_polytwisters.update(soft_polytwisters.get_all_soft_polytwisters())

    for name, polytwister in tqdm.tqdm(all_polytwisters.items()):
        type_ = polytwister["type"]
        out_dir = root_out_dir / name
        if out_dir.exists():
            polytwister_names.append(name)
            continue

        tqdm.tqdm.write(f"Computing {type_} polytwister '{name}'...")

        if type_ == "soft":
            soft_polytwister_section.render_all_sections_as_objs(
                polytwister, num_frames, soft_polytwister_resolution, out_dir
            )
        else:
            hard_polytwister_section.render_all_sections_as_objs(polytwister, num_frames, out_dir)

        polytwister_names.append(name)
        with open(root_out_dir / "manifest.json", "w") as file:
            json.dump({
                "directory_type": "sections_of_multiple_polytwisters",
                "polytwister_names": polytwister_names
            }, file)


if __name__ == "__main__":
    main()