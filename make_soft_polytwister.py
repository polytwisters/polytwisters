import argparse
import itertools

import numpy as np
import scipy.spatial
import scipy.spatial.transform

import soft_polytwisters


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


def get_soft_polytwister_cross_section(soft_polytwister_spec, w, resolution=200):
    soft_polytwister = get_soft_polytwister(soft_polytwister_spec["points"], resolution)
    return get_cross_section(soft_polytwister, w)


def write_hull_as_obj(hull_3d, f):
    """Given a 3D scipy.spatial.ConvexHull and a writable file-like object, write the hull as a
    Wavefront OBJ file."""
    for point in hull_3d.points:
        f.write(f"v {point[0]} {point[1]} {point[2]}\n")
    for triangle in hull_3d.simplices:
        f.write(f"f {triangle[0] + 1} {triangle[1] + 1} {triangle[2] + 1}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "polytwister",
        help="Name of the polytwister. For convenience, underscores are replaced with spaces.",
    )
    parser.add_argument(
        "w",
        type=float,
        help="W-coordinate of the 3-space where the cross section is taken.",
    )
    parser.add_argument(
        "obj_out",
        type=str,
        help="If specified, write out a Wavefront OBJ file."
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        default=100,
        help="Number of segments used for cylinders.",
    )
    parser.add_argument(
        "-s",
        "--scale",
        type=float,
        default=1,
        help=(
            "Uniform scaling applied to object. "
            "If --normalize is provided, scaling is done after normalization."
        ),
    )
    args = parser.parse_args()

    polytwister_name = args.polytwister
    polytwister_name = polytwister_name.replace("_", " ")
    resolution = args.resolution

    for polytwister in soft_polytwisters.ALL_SOFT_POLYTWISTERS:
        if polytwister_name in polytwister["names"]:
            break
    else:
        raise ValueError(f'Polytwister "{polytwister_name}" not found.')

    soft_polytwister = get_soft_polytwister(polytwister["points"], resolution)
    cross_section = get_cross_section(soft_polytwister, args.w)
    with open(args.obj_out, "w") as f:
        if cross_section is not None:
            write_hull_as_obj(cross_section, f)


if __name__ == "__main__":
    main()
