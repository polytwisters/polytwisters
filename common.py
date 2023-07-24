import pathlib
import platform
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent

system = platform.system()
if system == "Darwin":
    BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
    BLENDER_ROOT = None
    PYTHON = ["python3"]
elif system == "Windows":
    BLENDER_ROOT = pathlib.Path("C:\\Program Files\\Blender Foundation\\Blender 3.3\\")
    BLENDER = str(BLENDER_ROOT / "blender.exe")
    PYTHON = ["py", "-3"]
else:
    BLENDER = "blender"
    BLENDER_ROOT = None
    PYTHON = ["python3"]
MAKE_POLYTWISTER_SCRIPT = pathlib.Path(__file__).resolve().parent / "make_polytwister.py"


def run_script(script_path, blender_args, script_args, interactive=False):
    blender = [BLENDER]
    if not interactive:
        blender.append("-b")
    command = blender + ["--python", script_path]
    subprocess.run(command + blender_args + ["--"] + script_args, check=True)
