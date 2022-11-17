import pathlib
import platform
import subprocess

system = platform.system()
if system == "Darwin":
    BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
else:
    BLENDER = "blender"
BLENDER_SCRIPT = pathlib.Path(__file__).resolve().parent / "make_polytwister.py"


def run_script(blender_args, script_args):
    command = [BLENDER, "-b", "--python", str(BLENDER_SCRIPT)]
    subprocess.run(command + blender_args + ["--"] + script_args, check=True)
