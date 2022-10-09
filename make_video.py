import subprocess

if __name__ == "__main__":
    subprocess.run([
        "ffmpeg",
        "-framerate",
        "24",
        "-pattern_type",
        "glob",
        "-i",
        "out/*.png",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "out.mp4",
    ], check=True)
