import pathlib
import subprocess

BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
BLENDER_SCRIPT = pathlib.Path(__file__).resolve().parent / "polytwisters_blender.py"

if __name__ == "__main__":
    subprocess.run([
        BLENDER,
        "-b",
        "--python",
        str(BLENDER_SCRIPT),
        "-o",
        "out",
        "-f",
        "1",
        "--",
        "quasioctatwister",
        "0.14",
    ], check=True)
