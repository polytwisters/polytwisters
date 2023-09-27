import argparse
import pathlib
import subprocess

FFMPEG = "ffmpeg.exe"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()
    input_file = args.input_file
    output_file = pathlib.Path(input_file)
    output_file = output_file.parent / (output_file.stem + ".gif")
    subprocess.run([
        FFMPEG,
        "-i", input_file,
        "-vf", "scale=500:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        output_file
    ])

if __name__ == "__main__":
    main()