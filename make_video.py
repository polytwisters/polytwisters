import argparse
import subprocess
import pathlib

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        help=(
            "Polytwister directory. Must have a subdirectory called transparent_frames. "
            "Normally this is of the form out/<polytwister_name>/."
        ),
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frames per second.",
    )
    parser.add_argument(
        "--background-color",
        type=str,
        default="black",
        help="Background color.",
    )
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    (directory / "frames").mkdir(exist_ok=True)

    # Use ImageMagick to add a background color to every frame.
    # ffmpeg automatically adds a black background color but it seems to add jagged
    # edges by using a white background on translucent pixels.
    for file_path in directory.glob("transparent_frames/*.png"):
        subprocess.run([
            "convert",
            str(file_path),
            "-background",
            "black",
            "-alpha",
            "remove",
            "-alpha",
            "off",
            str(directory / "frames" / file_path.name),
        ], check=True)

    subprocess.run([
        "ffmpeg",
        "-framerate",
        str(args.fps),
        "-pattern_type",
        "glob",
        "-i",
        str(directory / "frames/*.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(directory / "out.mp4"),
    ], check=True)
