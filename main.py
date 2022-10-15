import argparse
import json
import math
import os
import pathlib
import platform
import subprocess
import sys
import time

system = platform.system()
if system == "Darwin":
    BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
else:
    BLENDER = "blender"
BLENDER_SCRIPT = pathlib.Path(__file__).resolve().parent / "polytwisters_blender.py"


def run_script(blender_args, script_args):
    command = [BLENDER, "-b", "--python", str(BLENDER_SCRIPT)]
    subprocess.run(command + blender_args + ["--"] + script_args, check=True)


def render_frame(args, file_name):
    out_prefix = "out"
    run_script(["-o", out_prefix, "-f", "1"], args)
    out_file = out_prefix + "0001.png"
    os.rename(out_file, file_name)


def get_max_distance_from_origin(polytwister, z):
    metadata_json = "metadata.json"
    args = [polytwister, str(z), "--metadata-out", metadata_json]
    run_script([], args)
    with open(metadata_json) as f:
        root = json.load(f)
    return root["max_distance_from_origin"]


def get_scale_and_max_z(polytwister):
    max_distance_from_origin_zero = get_max_distance_from_origin(polytwister, 0.0)
    scale = 1 / max_distance_from_origin_zero

    max_z_lower_bound = 0
    max_z_upper_bound = max_distance_from_origin_zero * 1.5

    while max_z_upper_bound - max_z_lower_bound > 0.01:
        max_z = (max_z_lower_bound + max_z_upper_bound) / 2
        distance = get_max_distance_from_origin(polytwister, max_z)
        if distance > 0:
            max_z_lower_bound = max_z
        else:
            max_z_upper_bound = max_z
    return scale, max_z_upper_bound


def render_animation(
    polytwister,
    max_z,
    num_frames,
    additional_args=(),
):
    directory = pathlib.Path("out") / polytwister
    os.makedirs(str(directory), exist_ok=True)

    remaining_frames = list(range(1, num_frames - 1))
    frame_order = []

    while len(remaining_frames) >= 2:
        frame_order = remaining_frames[0::2] + frame_order
        remaining_frames = remaining_frames[1::2]
    frame_order.extend(remaining_frames)
    frame_order = [0, num_frames - 1] + frame_order

    num_digits = int(math.ceil(math.log10(num_frames)))
    frame_names = [f"frame{str(i).rjust(num_digits, '0')}.png" for i in range(num_frames)]

    for frame_index in frame_order:
        z = (frame_index / max(frame_order) * 2 - 1) * max_z
        args = [polytwister, str(z)] + list(additional_args)
        render_frame(args, str(directory / frame_names[frame_index]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("polytwister")
    args = parser.parse_args()

    start_time = time.time()

    try:
        polytwister = args.polytwister
        scale, max_z = get_scale_and_max_z(polytwister)

        render_animation(
            polytwister,
            max_z=max_z,
            num_frames=100,
            additional_args=["--scale", str(5 * scale), "--resolution", "128"],
        )
    finally:
        end_time = time.time()
        duration_in_seconds = int(end_time - start_time)
        duration_in_minutes, seconds = divmod(duration_in_seconds, 60)
        hours, minutes = divmod(duration_in_minutes, 60)

        duration_string = f"{hours}:{minutes:0>2}:{seconds:0>2}"
        print(f"Took {duration_string}.", file=sys.stderr)
