import argparse
import pathlib
import subprocess

from .common import FFMPEG


def make_mp4(in_dir, out_file):
    command = [
        FFMPEG,
        "-i", in_dir / "render_%04d.png",
        # Video codec.
        "-c:v", "libx264",
        # Do not overwrite.
        "-n",
        out_file
    ]
    subprocess.run(command, check=True)


def make_gif(in_dir, out_file):
    subprocess.run([
        FFMPEG,
        "-i", in_dir / "render_%04d.png",
        "-vf", "scale=200:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        out_file
    ], check=True)