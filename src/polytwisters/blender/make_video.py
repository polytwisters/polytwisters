import argparse
import pathlib
import subprocess

from .common import FFMPEG


def make_mp4(in_dir, out_file):
    fps = 24
    # It would be better to get this from the file, but I'm not sure how.
    size = 1080
    # The x264 codec does not support transparent video and the alpha channel will be automatically
    # removed from transparent images. However, this causes some weird jaggies in the output. To
    # get around that we have to explicitly add a black background.
    command = [
        FFMPEG,
        "-framerate", f"{fps}",
        # Create a solid black image.
        "-f", "lavfi",
        "-i", f"color=black:s={size}x{size}",
        # Load in input frames.
        "-i", in_dir / "render_%04d.png",
        # Superimpose input video on black image.
        # Use the 'shortest' setting in the framesync options to ensure the length is exactly that
        # of the video. If shortest=1 is not set, ffmpeg outputs an infinitely long video!
        "-filter_complex", "overlay=shortest=1",
        # Set video codec.
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
        "-vf", "scale=400:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        out_file
    ], check=True)