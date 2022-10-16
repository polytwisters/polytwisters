import argparse
import subprocess
import pathlib

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    subprocess.run([
        "ffmpeg",
        "-framerate",
        "24",
        "-pattern_type",
        "glob",
        "-i",
        str(directory / "*.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "out.mp4",
    ], check=True)
