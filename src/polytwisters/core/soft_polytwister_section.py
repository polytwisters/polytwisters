"""Tools for converting descriptions of soft polytwisters into 3D cross sections using CadQuery.
Outputs Wavefront OBJ files.
"""
import collections
import argparse
import itertools
import math
import pathlib

import numpy as np
import scipy.spatial
import scipy.spatial.transform

from . import common
from . import soft_polytwisters


def quat_to_4d_matrix(q):
    """Convert a unit quaternion q into the 4D matrix that performs the left-isoclinic rotation
    that corresponds to left-multiplication by q."""
    a, b, c, d = q
    return np.array([
        [a, -b, -c, -d],
        [b, a, -d, c],
        [c, d, a, -b],
        [d, -c, b, a],
    ])


def get_fiber_rotation_matrix(p):
    """Given a point in 3D space of distance 1 from the origin, produce a rotation matrix that
    takes the unit circle in the xy-plane to that point's corresponding Hopf fiber."""
    x, y, z = p
    if np.allclose(x, -1):
        # q = np.array([0, 1, 0, 0])
        q = np.array([0, 0, 0, 1])
    else:
        normalizer = 1 / np.sqrt(2 * (1 + x))
        q = np.array([1 + x, 0, -z, y]) * normalizer
    return quat_to_4d_matrix(q)


def get_soft_polytwister(points, resolution):
    """Produce a 4D mesh approximation of a soft polytwister corresponding to a set of points in 3D
    space. The parameter "resolution" controls the number of segments in the generalized Hopf
    fibers.

    The return value is a scipy.spatial.ConvexHull object. The most useful attributes are "points",
    which is a NumPy array of point coordinates shaped as (point index, coordinate), and
    "simplices", which is a NumPy array of tetrahedra in 4D space shaped as
    (tetrahedron index, vertex number) where each entry is an index into the "points" array.

    scipy.spatial.ConvexHull internally wraps QHull.
    """
    fibers = []
    theta = np.linspace(0, 2 * np.pi, resolution, endpoint=False)
    # Dimensions: 4D coordinate, point index
    base_fiber = np.stack([np.cos(theta), np.sin(theta), np.zeros_like(theta), np.zeros_like(theta)])
    for point in points:
        radius = np.linalg.norm(point)
        normalized_point = point / radius
        fiber_rotation_matrix = get_fiber_rotation_matrix(normalized_point)
        # Dimensions: 4D coordinate, point index
        fiber = fiber_rotation_matrix @ (base_fiber * radius)
        fibers.append(fiber)
    # Dimensions: 4D coordinate, point index
    fiber_points = np.concatenate(fibers, axis=-1)
    # ConvexHull expects dimensions (point index, coordinate), so take transpose here
    hull = scipy.spatial.ConvexHull(fiber_points.T)
    return hull


def get_cross_section(hull, w):
    """Given a 4D scipy.spatial.ConvexHull and a w-coordinate, slice that convex hull using a
    3-space that is orthogonal to the w-axis and intersects it at that w-coordinate, and return a
    3D scipy.spatial.ConvexHull of that cross section. In this case, the w-coordinate is assumed
    to be the final coordinate."""
    # Dimensions: point, 4D coordinate
    points = hull.points
    cross_section_points = []
    for simplex in hull.simplices:
        # Dimensions: point, 4D coordinate
        simplex_vertices = points[simplex, :]
        # Loop through all six line segments forming the edges of the tetrahedron.
        for i, j in itertools.combinations(range(4), 2):
            # Get endpoints of the line segment in 4D space.
            p_1 = simplex_vertices[i, :]
            p_2 = simplex_vertices[j, :]
            # Get w-coordinates of the end-points.
            w_1 = p_1[-1]
            w_2 = p_2[-1]
            # Check to see if the 3-space at w intersects the line segment, including at its
            # endpoints.
            if w_1 <= w < w_2 or w_2 <= w < w_1:
                if np.allclose(w_1, w_2):
                    # In the unlikely case where the line segment is contained entirely in the
                    # 3-space (with some wiggle room due to precision), project both points onto the
                    # 3-space and add both to the cross section.
                    cross_section_points.append(p_1[:-1])
                    cross_section_points.append(p_2[:-1])
                else:
                    # Find the position of the intersecting point along the line: 0 if the
                    # intersection is at p_1, 1 if the intersection is at p_2.
                    # Zero division is prevented by the above if conditional.
                    t = (w - w_1) / (w_2 - w_1)
                    # Find the intersection itself.
                    p = p_1 + (p_2 - p_1) * t
                    # Discard the w-coordinate to project onto the 3-space.
                    cross_section_points.append(p[:-1])
    if len(cross_section_points) < 4:
        return None
    # Dimensions: point, 3D coordinate
    cross_section_points = np.stack(cross_section_points)
    # Rotate 90 degrees in YZ-plane so the polytwister stands up.
    rotation = np.array([
        [1, 0, 0],
        [0, 0, -1],
        [0, 1, 0],
    ])
    cross_section_points = (rotation @ cross_section_points.T).T
    try:
        hull_3d = scipy.spatial.ConvexHull(cross_section_points)
    except scipy.spatial.QhullError:
        return None
    return hull_3d


MockHull = collections.namedtuple("MockHull", "points, simplices")


def merge_hulls(hulls):
    points = []
    simplices = []
    offset = 0
    for hull in hulls:
        points.append(hull.points)
        simplices.append(hull.simplices + offset)
        num_points = hull.points.shape[0]
        offset += num_points
    return MockHull(
        np.concatenate(points, axis=0),
        np.concatenate(simplices, axis=0),
    )



def get_soft_polytwister_cross_section(soft_polytwister_spec, w, resolution=200):
    if soft_polytwister_spec.get("compound", False):
        components = []
        for component_points in soft_polytwister_spec["pieces"]:
            component = get_soft_polytwister(component_points, resolution)
            component_cross_section = get_cross_section(component, w)
            if component_cross_section is not None:
                components.append(component_cross_section)
        if len(components) == 0:
            return None
        return merge_hulls(components)
    soft_polytwister = get_soft_polytwister(soft_polytwister_spec["points"], resolution)
    return get_cross_section(soft_polytwister, w)


def write_hull_as_obj(hull_3d, f):
    """Given a 3D scipy.spatial.ConvexHull and a writable file-like object, write the hull as a
    Wavefront OBJ file."""
    for point in hull_3d.points:
        f.write(f"v {point[0]} {point[1]} {point[2]}\n")
    for triangle in hull_3d.simplices:
        f.write(f"f {triangle[0] + 1} {triangle[1] + 1} {triangle[2] + 1}\n")


def render_one_section_as_obj(polytwister, w, resolution, out_file):
    cross_section = get_soft_polytwister_cross_section(polytwister, w, resolution)
    with open(out_file, "x") as f:
        if cross_section is not None:
            write_hull_as_obj(cross_section, f)


def get_w_coordinates_and_file_names(num_frames):
    num_digits = int(math.ceil(math.log10(num_frames)))
    for i in range(num_frames):
        w = -1 + 2 * (i + 1) / (num_frames + 1)
        file_stem = f"out_{str(i).rjust(num_digits, '0')}"
        yield w, file_stem


def render_all_sections_as_objs(polytwister, num_frames, resolution, out_dir):
    out_dir.mkdir()
    file_names = []
    for w, file_stem in get_w_coordinates_and_file_names(num_frames):
        file_name = file_stem + ".obj"
        out_file = out_dir / file_name
        render_one_section_as_obj(polytwister, w, resolution, out_file)
        file_names.append(file_name)
    common.write_metadata_file(polytwister, file_names, out_dir)


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
            "W-coordinate of the 3-space where the cross section is taken. "
            "If not given, render an animation."
        ),
    )
    parser.add_argument(
        "-n",
        "--num-frames",
        type=int,
        help="Number of frames."
    )
    parser.add_argument(
        "out",
        type=str,
        help="Output file name if a single file, output directory if an animation."
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="obj",
        help='Output format. Only "obj" (Wavefront OBJ) is supported currently.',
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        default=100,
        help="Number of segments used for rings.",
    )

    args = parser.parse_args()
    w = args.w
    num_frames = args.num_frames
    out_path = pathlib.Path(args.out)
    polytwister_name = common.normalize_polytwister_name(args.polytwister)
    resolution = args.resolution

    polytwister = soft_polytwisters.get_all_soft_polytwisters()[polytwister_name]

    if w is None and num_frames is None:
        raise ValueError(
            "You must specify one of -w (for a single cross section) or "
            "-n (for multiple cross sections)."
        )

    if w is not None and num_frames is not None:
        raise ValueError(f"You cannot specify both -w and -n.")

    if args.format == "obj":
        if w is not None:
            render_one_section_as_obj(polytwister, w, resolution, out_path)
        elif num_frames is not None:
            render_all_sections_as_objs(polytwister, num_frames, resolution, out_path)

    else:
        raise ValueError('Unsupported format: {args.format}')


if __name__ == "__main__":
    main()
