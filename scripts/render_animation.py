import argparse
import json
import logging
import math
import pathlib
import sys
import time

import common


def render_frame(args, file_name):
    out_prefix = "out"
    common.run_blender_script(common.BLENDER_SCRIPT, ["-o", "//" + out_prefix, "-f", "1"], args)
    out_file = out_prefix + "0001.png"
    pathlib.Path(out_file).rename(file_name)


def get_max_distance_from_origin(polytwister, w):
    metadata_json = "metadata.json"
    args = [polytwister, str(w), "--metadata-out", metadata_json]
    common.run_blender_script(common.BLENDER_SCRIPT, [], args)
    with open(metadata_json) as f:
        root = json.load(f)
    return root["max_distance_from_origin"]



def render_animation(
    polytwister,
    max_w,
    num_frames,
    additional_args=(),
):
    """Given a polytwister and its precomputed max W, render frames of
    an animation by calling make_polytwister.py as a subprocess.
    additional_args specifies command-line arguments to make_polytwister.py,
    including the overall spatial scale of the meshes.

    Blender has built-in features to render an animated video, but I
    went with rendering frames individually so they could be rendered
    out of order. Out-of-order rendering has two advantages: 1. I'm
    impatient and want to see a lower-res animation before it completes,
    2. issues can be caught early to avoid wasting hours of render time.

    The rendering order is done with the following heuristically
    determined algorithm. Start with N frames. Cross off every other
    frame. Then go through the uncrossed frames and cross off every
    other one of those. Repeat until there is only one frame left, then
    cross it off. Now sort all the frames in order of when they were
    crossed off, but backwards. This gives you an ordering of the frames
    that roughly increases in resolution.

    As a special exception, the first and last frames are rendered
    first so they can be visually confirmed to be blank. If they
    aren't blank then the max W is too small and the animation will
    be cut off.
    """
    directory = common.ROOT / "out" / polytwister / "transparent_frames"
    directory.mkdir(parents=True, exist_ok=True)

    remaining_frames = list(range(1, num_frames - 1))
    frame_order = []

    while len(remaining_frames) >= 2:
        frame_order = remaining_frames[0::2] + frame_order
        remaining_frames = remaining_frames[1::2]
    frame_order.extend(remaining_frames)
    frame_order = [0, num_frames - 1] + frame_order

    num_digits = int(math.ceil(math.log10(num_frames)))
    frame_names = [f"frame{str(i).rjust(num_digits, '0')}.png" for i in range(num_frames)]

    for frame_index in frame_order:
        w = (frame_index / max(frame_order) * 2 - 1) * max_w
        args = [polytwister, str(w)] + list(additional_args)
        render_frame(args, str(directory / frame_names[frame_index]))


def render_animation_with_proper_scaling(polytwister, num_frames):
    # Stupid hack to change settings for soft vs. hard polytwisters
    if "soft" in polytwister:
        scale = 1.0
        max_w = 1.0
    else:
        scale, max_w = get_scale_and_max_w(polytwister)

    render_animation(
        polytwister,
        max_w=max_w,
        num_frames=num_frames,
        additional_args=["--scale", str(scale)],
    )


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("polytwister", help="Name of the polytwister.")
    parser.add_argument("-n", "--num-frames", type=int, default=100, help="Number of frames, >= 2.")
    args = parser.parse_args()

    if args.num_frames < 2:
        raise ValueError("--num-frames must be >= 2")

    start_time = time.time()

    try:
        render_animation_with_proper_scaling(args.polytwister, args.num_frames)
    finally:
        end_time = time.time()
        duration_in_seconds = int(end_time - start_time)
        duration_in_minutes, seconds = divmod(duration_in_seconds, 60)
        hours, minutes = divmod(duration_in_minutes, 60)

        duration_string = f"{hours}:{minutes:0>2}:{seconds:0>2}"
        print(f"Took {duration_string}.", file=sys.stderr)


if __name__ == "__main__":
    main()
