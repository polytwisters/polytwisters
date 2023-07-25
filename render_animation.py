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
    common.run_script(common.MAKE_POLYTWISTER_SCRIPT, ["-o", "//" + out_prefix, "-f", "1"], args)
    out_file = out_prefix + "0001.png"
    pathlib.Path(out_file).rename(file_name)


def get_max_distance_from_origin(polytwister, w):
    metadata_json = "metadata.json"
    args = [polytwister, str(w), "--metadata-out", metadata_json]
    common.run_script([], args)
    with open(metadata_json) as f:
        root = json.load(f)
    return root["max_distance_from_origin"]


def get_scale_and_max_w(polytwister):
    """Polytwisters are highly variable in size, and must be normalized
    in two ways. They are scaled spatially so they fit in the camera's
    view and appear roughly the same size, and the animation must set
    the range of W (cross section coordinate) so that the cross section
    starts from nothing exactly at the beginning and shrinks back to
    nothing exactly at the end.

    Bowers used trial and error to compute scaling for the POV-Ray code.
    An automated solution is used here.

    To aid in these calculations, make_polytwister.py has a feature
    that finds the furthest point from the origin for a given polytwister
    cross section and returns its distance from the origin. This gives
    maximum distance from the origin as a function of W; call this D(W)
    and define D(W) = 0 if the mesh is empty.

    For the scale, we simply scale by 1 / D(0). This appears sufficient
    as polytwisters are reasonably round.

    For proper timing, let W_min be the value of W at the start of the
    animation and W_max be W at the end. We want W_min to be the
    minimum W-coordinate of any point in the 4D polytwister and W_max
    to be the maximum W-coordinate of any point. Due to symmetry of uniform
    and regular polytwisters, and the symmetry of the angle at which
    we take cross sections, it is safe to assume W_min = -W_max.
    W_max is the minimum W > 0 such that D(W) = 0.

    If W_max is too large then there are blank frames at the beginning
    and end of the animation, and if W_max is too small the animation is
    cut off, so it's important that W_max is accurate. W_max = D(0) is
    a good estimate but tends to be too small in practice.

    To find W_max, we use the bisection method, which must be initialized
    with lower and upper bounds. W = 0 is a lower bound because D(0) is
    always nonzero. W = 2 * D(0) is almost certainly a safe upper bound,
    but just to be sure we perform a grid search by adding 1 to W until
    D(W) = 0. With initial lower and upper bounds, the bisection
    method can be used to find W_max with high accuracy.
    """
    max_distance_from_origin_zero = get_max_distance_from_origin(polytwister, 0.0)
    scale = 1 / max_distance_from_origin_zero
    logging.debug(f"Max distance from origin at w = 0: {max_distance_from_origin_zero:.2}")
    logging.debug(f"Scale = {scale:.2}")

    max_w_lower_bound = 0
    max_w_upper_bound = max_distance_from_origin_zero * 2

    logging.debug("Performing grid search to find upper bound for max W.")
    while True:
        logging.debug(f"Testing upper bound {max_w_upper_bound:.2}")
        max_distance_from_origin = get_max_distance_from_origin(polytwister, max_w_upper_bound)
        if max_distance_from_origin == 0:
            break
        max_w_upper_bound += 1
    logging.debug(f"Grid search complete, upper bound = {max_w_upper_bound:.2}")

    logging.debug(f"Performing bisection search.")
    while max_w_upper_bound - max_w_lower_bound > 0.01:
        logging.debug(f"Search range = [{max_w_lower_bound:.2f}, {max_w_upper_bound:.2f}].")
        max_w = (max_w_lower_bound + max_w_upper_bound) / 2
        distance = get_max_distance_from_origin(polytwister, max_w)
        if distance > 0:
            max_w_lower_bound = max_w
        else:
            max_w_upper_bound = max_w
    logging.debug(f"Bisection search complete. Max W = {max_w_upper_bound:.2f}")
    return scale, max_w_upper_bound


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
        polytwister = args.polytwister
        # Stupid hack to change settings for soft vs. hard polytwisters
        if "soft" in polytwister:
            scale = 1.0
            max_w = 1.0
            resolution = 450
        else:
            scale, max_w = get_scale_and_max_w(polytwister)
            resolution = 200

        render_animation(
            polytwister,
            max_w=max_w,
            num_frames=args.num_frames,
            additional_args=["--scale", str(scale)],
        )
    finally:
        end_time = time.time()
        duration_in_seconds = int(end_time - start_time)
        duration_in_minutes, seconds = divmod(duration_in_seconds, 60)
        hours, minutes = divmod(duration_in_minutes, 60)

        duration_string = f"{hours}:{minutes:0>2}:{seconds:0>2}"
        print(f"Took {duration_string}.", file=sys.stderr)


if __name__ == "__main__":
    main()
