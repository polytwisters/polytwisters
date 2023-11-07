"""Tools for converting descriptions of hard polytwisters into 3D cross sections using CadQuery.
Can output Wavefront OBJ files and also SVG lineart.
"""
import argparse
import math
import logging
import pathlib

import cadquery
import cadquery.utils
import numpy as np
import tqdm

from . import common
from . import hard_polytwisters
from .cadquery_to_svg import export_svg, render_as_polylines, export_montage_as_svg

LARGE = 100.0
EPSILON = 1e-3


# https://github.com/CadQuery/cadquery/issues/638
def scale_workplane(workplane: cadquery.Workplane, x: float, y: float, z: float) -> cadquery.Workplane:
    matrix = cadquery.Matrix([
        [x, 0, 0, 0],
        [0, y, 0, 0],
        [0, 0, z, 0],
        [0, 0, 0, 1]
    ])
    return workplane.newObject([
        object_.transformGeometry(matrix) if isinstance(object_, cadquery.Shape) else object_
        for object_ in workplane.objects
    ])


def scale_workplane_uniform(workplane: cadquery.Workplane, amount: float) -> cadquery.Workplane:
    return scale_workplane(workplane, amount, amount, amount)


def create_cycloplane(w, zenith, azimuth):
    """Create a cross section of a cycloplane constructed from a Hopf fiber.
    w is the cross section coordinate, zenith is the angle from the north pole,
    and azimuth is another word for longitude. Said point is transformed via
    the preimage of the Hopf fibration into a unit circle, then the cycloplane
    is constructed from that unit circle.

    See "cylli" macro in Bowers' original code.
    """
    theta = zenith / 2
    phi = azimuth

    if abs(theta - math.pi / 2) < EPSILON:
        return _create_south_pole_cycloplane(w)

    part = cadquery.Workplane()
    part = part.cylinder(LARGE, 1)

    # The cylinder is along the Z-axis. Rotate about the X-axis to
    # change Z-axis to Y-axis and match with the original "cyl" object
    # in Bowers' POV-Ray code.
    part = part.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), math.degrees(math.pi / 2))

    scale_x = 1 / math.cos(theta)
    part = scale_workplane(part, scale_x, 1.0, 1.0)
    translate_x = w * math.tan(theta)
    part = part.translate((translate_x, 0, 0))

    # In Bowers' code this rotation about the X-axis comes before the
    # translation. It doesn't matter because translation along the X-axis
    # commutes with rotations about the X-axis, but I prefer to group the
    # rotations together.
    part = part.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), math.degrees(-theta))
    part = part.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), math.degrees(phi))

    return part


def _create_south_pole_cycloplane(w):
    """Create the cross section of a cycloplane whose point is located at the
    south pole."""
    if abs(w) >= 1:
        return cadquery.Workplane()
    part = cadquery.Workplane()
    half_height = math.sqrt(1 - w * w)
    part = part.cylinder(height=half_height * 2, radius=LARGE)
    # See comment in create_cycloplane.
    part = part.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), math.degrees(math.pi / 2))
    return part


def make_rotated_copies(part, n):
    parts = []
    for i in range(n):
        new_part = part.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), math.degrees(i * 2 * math.pi / n))
        parts.append(new_part)
    return parts


def bubble(x):
    if isinstance(x, list):
        return x
    return [x]


def is_empty(part):
    return len(part.solids().vals()) == 0


def safe_intersect(part_1, part_2):
    """Compute the intersection of two cadquery.Workplanes, but if the output is empty don't throw
    an error."""
    try:
        return part_1.intersect(part_2)
    except ValueError:
        return cadquery.Workplane()


def safe_cut(part_1, part_2):
    """Compute the difference of two cadquery.Workplanes, but don't throw an error for empty inputs."""
    if is_empty(part_1):
        return cadquery.Workplane()
    elif is_empty(part_2):
        return part_1
    return part_1.cut(part_2)


def safe_union(part_1, part_2):
    """Compute the union of two cadquery.Workplanes, but don't throw an error for empty inputs."""
    if is_empty(part_1):
        return part_2
    elif is_empty(part_2):
        return part_1
    return part_1.union(part_2)


class Realizer:

    def __init__(self, w):
        # HACK: CadQuery seems to have some problems with polytwister cross sections at w = 0.
        # Annoying.
        self.w = w if abs(w) > EPSILON else EPSILON

    def realize(self, polytwister):
        return self.traverse(polytwister["tree"])

    def traverse(self, node):
        type_ = node["type"]
        if type_ == "cycloplane":
            return create_cycloplane(
                self.w,
                node["zenith"],
                node["azimuth"],
            )
        elif type_ == "rotated_copies":
            first = self.traverse(node["operand"])
            return make_rotated_copies(first, node["order"])
        elif type_ == "intersection":
            result = None
            for child in node["operands"]:
                operands = bubble(self.traverse(child))
                for operand in operands:
                    if result is None:
                        result = operand
                    else:
                        result = safe_intersect(result, operand)
            return result
        elif type_ == "difference":
            result = None
            for child in node["operands"]:
                operands = bubble(self.traverse(child))
                for operand in operands:
                    if result is None:
                        result = operand
                    else:
                        result = safe_cut(result, operand)
            return result
        elif type_ == "union":
            result = None
            for child in node["operands"]:
                operands = bubble(self.traverse(child))
                for operand in operands:
                    if result is None:
                        result = operand
                    else:
                        result = safe_union(result, operand)
            return result
        else:
            raise ValueError(f'Invalid node type {type_}')


def make_polytwister_cross_section(polytwister, w):
    workplane = Realizer(w).realize(polytwister)
    return workplane


def discretize_workplane(workplane, tolerance=0.1, angular_tolerance=0.1):
    """Given a workplane containing a single shape, return a tuple comprising a set of vertices and
    triangles. The vertices are a list of cadquery.Vectors, and the triangles a list of 3-tuples of
    ints indexing into the vertex list. Vertex indices start at 0."""
    shapes = [thing for thing in workplane.objects if isinstance(thing, cadquery.Shape)]
    if len(shapes) == 0:
        return [], []
    if len(shapes) != 1:
        raise RuntimeError("Workplane has two or more Shapes, this doesn't make sense")
    shape: cadquery.Compound = shapes[0]
    vertices, triangles = shape.tessellate(tolerance, angular_tolerance)
    return vertices, triangles


def write_mesh_as_obj(mesh, file):
    vertices, triangles = mesh
    vertices = np.array([[point.x, point.y, point.z] for point in vertices])
    common.write_obj(vertices, triangles, file)


def get_max_distance_from_origin(polytwister, w):
    workplane = make_polytwister_cross_section(polytwister, w)
    vertices, __ = discretize_workplane(workplane)
    if len(vertices) == 0:
        return 0.0
    return max([abs(vertex) for vertex in vertices])


def get_scale_and_max_w(polytwister):
    """Hard polytwisters are highly variable in size, and must be normalized
    in two ways. They are scaled spatially so they fit in the camera's
    view and appear roughly the same size, and the animation must set
    the range of W (cross section coordinate) so that the cross section
    starts from nothing exactly at the beginning and shrinks back to
    nothing exactly at the end.

    Bowers used trial and error to compute scaling for the POV-Ray code.
    An automated solution is used here.

    To aid in these calculations, get_max_distance_from_origin finds the
    furthest point from the origin for a given polytwister cross section
    and returns its distance from the origin. This gives maximum distance
    from the origin as a function of W; call this D(W) and define D(W) = 0
    if the mesh is empty.

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
    if max_distance_from_origin_zero == 0.0:
        raise ValueError("Cross section at w = 0 is empty, something is wrong.")
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
        logging.debug(f"D({max_w:.2f}) = {distance:.2f}")
        if distance > 0:
            max_w_lower_bound = max_w
        else:
            max_w_upper_bound = max_w
    logging.debug(f"Bisection search complete. Max W = {max_w_upper_bound:.2f}")
    return scale, max_w_upper_bound


def scale_mesh(mesh, scale):
    vertices, triangles = mesh
    if len(vertices) == 0:
        return mesh
    vertices = [vertex * scale for vertex in vertices]
    return vertices, triangles


def normalize_mesh(mesh):
    vertices, triangles = mesh
    if len(vertices) == 0:
        return mesh
    scale = 1 / max([abs(vertex) for vertex in vertices])
    vertices = [vertex * scale for vertex in vertices]
    return vertices, triangles


def get_w_coordinates_and_file_names(polytwister, num_frames, max_w):
    num_digits = int(math.ceil(math.log10(num_frames)))
    result = []
    for i in range(num_frames):
        # Originally this was -max_w + max_w * 2 * i / (num_frames - 1) so the first frame has
        # w = -max_w and the final frame has w = max_w, but that results in the first and final
        # frames being empty, so we leave those out.
        w = -max_w + max_w * 2 * (i + 1) / (num_frames + 1)
        file_stem = f"out_{str(i).rjust(num_digits, '0')}"
        frame_number = i + 1
        result.append((frame_number, w, file_stem))
    return result


def render_one_section_as_obj(polytwister, w, out_file, normalize=False, scale=1.0):
    workplane = make_polytwister_cross_section(polytwister, w)
    mesh = discretize_workplane(workplane)
    if normalize:
        mesh = normalize_mesh(mesh)
    if scale != 1.0:
        mesh = scale_mesh(mesh, scale)
    with open(out_file, "x") as f:
        write_mesh_as_obj(mesh, f)


def render_one_section_as_svg(polytwister, w, out_file, normalize=False, scale=1.0):
    workplane = make_polytwister_cross_section(polytwister, w)
    svg_document = export_svg(workplane, normalize=normalize, additional_scale=scale)
    with open(out_file, "x") as f:
        f.write(svg_document)


def render_svg_montage(polytwister, num_frames, progress_bar=False):
    polylines_list = []
    scale, max_w = get_scale_and_max_w(polytwister)
    iterable = get_w_coordinates_and_file_names(polytwister, num_frames, max_w)
    if progress_bar:
        iterable = tqdm.tqdm(iterable, f"Computing SVG montage for '{polytwister['name']}'")
    for w, file_stem in iterable:
        workplane = make_polytwister_cross_section(polytwister, w)
        polylines_list.append(render_as_polylines(workplane))
    return export_montage_as_svg(polylines_list, scale)


def render_all_sections_as_svgs(polytwister, num_frames, out_dir, progress_bar=False):
    out_dir.mkdir()
    scale, max_w = get_scale_and_max_w(polytwister)
    iterable = get_w_coordinates_and_file_names(polytwister, num_frames, max_w)
    if progress_bar:
        iterable = tqdm.tqdm(iterable, f"Computing SVG lineart for '{polytwister['name']}'")
    for frame_number, w, file_stem in iterable:
        logging.debug(f"Computing frame {frame_number} of {num_frames}.")
        out_file = out_dir / (file_stem + ".svg")
        render_one_section_as_svg(polytwister, w, out_file, scale=scale)


def render_all_sections_as_objs(polytwister, num_frames, out_dir, progress_bar=False):
    out_dir.mkdir()
    scale, max_w = get_scale_and_max_w(polytwister)
    file_names = []
    iterable = get_w_coordinates_and_file_names(polytwister, num_frames, max_w)
    if progress_bar:
        iterable = tqdm.tqdm(iterable, f"Computing meshes for '{polytwister['name']}'")
    for frame_number, w, file_stem in iterable:
        logging.debug(f"Computing frame {frame_number} of {num_frames}.")
        file_name = file_stem + ".obj"
        out_file = out_dir / file_name
        render_one_section_as_obj(polytwister, w, out_file, scale=scale)
        file_names.append(file_name)
    common.write_manifest_file(polytwister, file_names, out_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "polytwister",
        help="Name of the polytwister. For convenience, underscores are replaced with spaces.",
    )
    parser.add_argument(
        "-w",
        type=float,
        help=(
            "W-coordinate of the 3-space where the cross section is taken. If not given, render "
            "an animation. Not allowed for the format 'svg_montage'."
        ),
    )
    parser.add_argument(
        "-n",
        "--num-frames",
        type=int,
        help="Number of frames.",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="obj",
        help="obj (default), svg, or svg_montage.",
    )
    parser.add_argument(
        "out",
        type=str,
        help="Output file name if a single file, output directory if an animation."
    )

    args = parser.parse_args()
    w = args.w
    num_frames = args.num_frames
    out_path = pathlib.Path(args.out)
    polytwister_name = common.normalize_polytwister_name(args.polytwister)

    polytwister = hard_polytwisters.get_all_hard_polytwisters()[polytwister_name]

    if w is None and num_frames is None:
        raise ValueError(
            "You must specify one of -w (for a single cross section) or "
            "-n (for multiple cross sections)."
        )

    if w is not None and num_frames is not None:
        raise ValueError(f"You cannot specify both -w and -n.")

    if args.format == "svg_montage":
        document = render_svg_montage(polytwister, num_frames)
        with open(out_path, "x") as f:
            f.write(document)

    elif args.format == "svg":
        if w is not None:
            render_one_section_as_svg(polytwister, w, out_path, normalize=True)
        elif num_frames is not None:
            render_all_sections_as_svgs(polytwister, num_frames, out_path)

    elif args.format == "obj":
        if w is not None:
            render_one_section_as_obj(polytwister, w, out_path, normalize=True)
        elif num_frames is not None:
            render_all_sections_as_objs(polytwister, num_frames, out_path)

    else:
        raise ValueError('Unsupported format: {args.format}')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()