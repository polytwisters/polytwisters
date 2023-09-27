import pathlib
import platform
import subprocess

SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_ROOT.parent
ROOT = SCRIPT_ROOT  # backward compat

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

BLENDER_SCRIPT = SCRIPT_ROOT / "blender_script.py"
RENDER_ANIMATION_SCRIPT = SCRIPT_ROOT / "render_animation.py"
MAKE_VIDEO_SCRIPT = SCRIPT_ROOT / "make_video.py"
NOTIFY_SCRIPT = SCRIPT_ROOT / "notify.py"


def blender_command(script_path, blender_args, script_args, interactive=False):
    blender = [BLENDER]
    if not interactive:
        blender.append("-b")
    command = blender + ["--python", script_path]
    command += blender_args + ["--"] + script_args
    return command


def run_blender_script(script_path, blender_args, script_args, interactive=False):
    command = blender_command(script_path, blender_args, script_args, interactive=interactive)
    subprocess.run(command, check=True)
