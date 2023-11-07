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
    FFMPEG = "ffmpeg"
elif system == "Windows":
    BLENDER_ROOT = pathlib.Path("C:\\Program Files\\Blender Foundation\\Blender 3.3\\")
    BLENDER = str(BLENDER_ROOT / "blender.exe")
    PYTHON = ["py", "-3"]
    FFMPEG = "ffmpeg.exe"
else:
    BLENDER = "blender"
    BLENDER_ROOT = None
    PYTHON = ["python3"]
    FFMPEG = "ffmpeg"

BLENDER_SCRIPT = SCRIPT_ROOT / "blender_script.py"


def blender_command(script_path, blender_args, script_args, interactive=False):
    blender = [BLENDER]
    if not interactive:
        blender.append("-b")
    command = blender + ["--python", script_path]
    command += blender_args + ["--"] + script_args
    return command


def run_blender_script(script_path, blender_args, script_args, interactive=False, log_handler=None):
    command = blender_command(script_path, blender_args, script_args, interactive=interactive)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Based on https://stackoverflow.com/a/21978778.
    with process.stdout:
        # iter, when passed in two arguments, assumes the first is callable and calls it repeatedly
        # until a value is returned equal to the second argument. proces.stdout.readline() returns
        # a bytes object of a single line of output, or an empty bytes if done. Thus this calls
        # process.stdout.readline repeatedly until there is nothing left to read.
        for raw_line in iter(process.stdout.readline, b""):
            line = raw_line.decode("utf-8", errors="replace").strip()
            if log_handler is None:
                print(line)
            else:
                log_handler(line)
    # Despite the use of stdout=subprocess.PIPE, it is okay to use .wait() here as stdout is closed.
    # .poll() gives me a nonzero retcode, I'm not sure why.
    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, process.args)
