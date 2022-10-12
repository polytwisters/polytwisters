import math
import os
import pathlib
import platform
import subprocess

system = platform.system()
if system == "Darwin":
    BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
else:
    BLENDER = "blender"
BLENDER_SCRIPT = pathlib.Path(__file__).resolve().parent / "polytwisters_blender.py"

def render_frame(args, file_name):
    out_prefix = "out"
    subprocess.run([
        BLENDER,
        "-b",
        "--python",
        str(BLENDER_SCRIPT),
        "-o",
        out_prefix,
        "-f",
        "1",
        "--",
    ] + args, check=True)
    out_file = out_prefix + "0001.png"
    os.rename(out_file, file_name)


def render_animation(
    polytwister,
    max_z,
    num_frames,
    additional_args=(),
):
    directory = pathlib.Path("out")
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
    render_animation(
        "bloated icosatwister",
        max_z=8.0,
        num_frames=100,
        additional_args=["--scale", "0.4"],
    )
