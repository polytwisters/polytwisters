import pathlib
import platform
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent

system = platform.system()
if system == "Darwin":
    BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
    BLENDER_ROOT = None
elif system == "Windows":
    BLENDER_ROOT = pathlib.Path("C:\\Program Files\\Blender Foundation\\Blender 3.3\\")
    BLENDER = str(BLENDER_ROOT / "blender.exe")
else:
    BLENDER = "blender"
    BLENDER_ROOT = None
BLENDER_SCRIPT = pathlib.Path(__file__).resolve().parent / "make_polytwister.py"


def run_script(blender_args, script_args):
    command = [BLENDER, "-b", "--python", str(BLENDER_SCRIPT)]
    subprocess.run(command + blender_args + ["--"] + script_args, check=True)
