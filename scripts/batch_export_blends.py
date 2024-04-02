from pathlib import Path
import re

from polytwisters.core.common import normalize_polytwister_name
from polytwisters.core.hard_polytwisters import get_all_hard_polytwisters
from polytwisters.core.hard_polytwister_section import render_all_sections_as_objs
from polytwisters.blender.export_blends import export_directory_as_blend


def hex_color_to_blender_color(color: str) -> list[float]:
    if len(color) != 7:
        raise ValueError("String must be 7 characters long")
    if color[0] != "#":
        raise ValueError("String does not start with #")
    red_hex = int(color[1:3], 16)
    green_hex = int(color[3:5], 16)
    blue_hex = int(color[5:7], 16)
    return [
        red_hex / 255,
        green_hex / 255,
        blue_hex / 255,
        1.0,
    ]



def main():
    all_hard_polytwisters = get_all_hard_polytwisters()

    polytwister_configs = {
        "tetratwister": {
            "Base Color": hex_color_to_blender_color("#e03131"),  # red
            "Roughness": 0.1,
        },
        "quasitetratwister": {
            "Base Color": hex_color_to_blender_color("#228be6"),  # blue
            "Roughness": 0.1,
        },
        "bloated_tetratwister": {
            "Base Color": hex_color_to_blender_color("#37b24d"),  # green
            "Roughness": 0.1,
        },
        "octatwister": {
            "Base Color": hex_color_to_blender_color("#da77f2"),  # grape
            "Roughness": 0.1,
        },
        "quasioctatwister": {
            "Base Color": hex_color_to_blender_color("#3bc9db"),  # cyan
            "Roughness": 0.1,
        },
        "bloated octatwister": {
            "Base Color": hex_color_to_blender_color("#a9e34b"),  # lime
            "Roughness": 0.1,
        },
    }

    out_root = Path(__file__).resolve().parent / "out"
    out_root.mkdir(exist_ok=True, parents=True)

    for polytwister_name, material_config in polytwister_configs.items():
        normalized_name = normalize_polytwister_name(polytwister_name)
        polytwister = all_hard_polytwisters[normalized_name]
        out_dir = out_root / polytwister_name
        blend_path = out_root / f"{polytwister_name}.blend"
        if out_dir.exists():
            continue
        if blend_path.exists():
            continue
        render_all_sections_as_objs(
            polytwister,
            num_frames=100,
            out_dir=out_dir,
            progress_bar=True,
        )
        config = {
            "material": material_config
        }
        export_directory_as_blend(out_dir, blend_path, config=config)


if __name__ == "__main__":
    main()