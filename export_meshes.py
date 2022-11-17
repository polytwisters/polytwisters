import pathlib

import common
import polytwisters


def main():
    out_directory = pathlib.Path("./out/meshes")
    out_directory.mkdir(exist_ok=True)
    w = 0.15
    for i, polytwister in len(polytwisters.ALL_POLYTWISTERS):
        name = polytwister["names"][0].replace(" ", "_")
        print(f'Exporting polytwister "{name}" ({i + 1}/{len(polytwisters.ALL_POLYTWISTERS)})...')
        args = [
            name,
            str(w),
            "--normalize",
            "--mesh-out",
            str(out_directory / f"{name}_{w:.5}.stl"),
        ]
        common.run_script([], args)
        print(f'Polytwister "{name}" exported ({i + 1}/{len(polytwisters.ALL_POLYTWISTERS)})')


if __name__ == "__main__":
    main()