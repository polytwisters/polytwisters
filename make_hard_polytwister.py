import argparse
import math
import cadquery
import cadquery.utils
import hard_polytwisters

LARGE = 1000.0
EPSILON = 1e-3


# https://github.com/CadQuery/cadquery/issues/638
def scale(workplane: cadquery.Workplane, x: float, y: float, z: float) -> cadquery.Workplane:
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
    part = scale(part, scale_x, 1.0, 1.0)
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
    part = part.cylinder(height=2.0, radius=LARGE)
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


class Realizer:

    def __init__(self, w):
        self.w = w

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
                        result = result.intersect(operand)
            return result
        elif type_ == "difference":
            result = None
            for child in node["operands"]:
                operands = bubble(self.traverse(child))
                for operand in operands:
                    if result is None:
                        result = operand
                    else:
                        result = result.cut(operand)
            return result
        elif type_ == "union":
            result = None
            for child in node["operands"]:
                operands = bubble(self.traverse(child))
                for operand in operands:
                    if result is None:
                        result = operand
                    else:
                        result = result.union(operand)
            return result
        else:
            raise ValueError(f'Invalid node type {type_}')


def compute_polytwister_cross_section(polytwister, w, tolerance=0.1, angular_tolerance=0.1):
    """Given a hard polytwister spec and a W coordinate, find the cross section.

    Return a tuple comprising a set of vertices and triangles. The vertices are a list of
    cadquery.Vectors, and the triangles a list of 3-tuples of ints indexing into the vertex list.
    Vertex indices start at 1."""
    workplane = Realizer(w).realize(polytwister)
    shapes = [thing for thing in workplane.objects if isinstance(thing, cadquery.Shape)]
    if len(shapes) != 1:
        raise RuntimeError("Workplane has to have exactly one Shape")
    shape = shapes[0]
    vertices, triangles = shape.tessellate(tolerance, angular_tolerance)
    return vertices, triangles


def write_mesh_as_obj(mesh, file):
    vertices, triangles = mesh
    for point in vertices:
        file.write(f"v {point.x} {point.y} {point.z}\n")
    for triangle in triangles:
        file.write(f"f {triangle[0]} {triangle[1]} {triangle[2]}\n")


def get_mesh_radius(vertices):
    return max([abs(vertex) for vertex in vertices])


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
        help="Wavefront OBJ file output."
    )
    parser.add_argument(
        "-s",
        "--scale",
        type=float,
        default=1,
        help="Uniform scaling applied to object.",
    )
    args = parser.parse_args()

    polytwister_name = args.polytwister
    polytwister_name = polytwister_name.replace("_", " ")

    for polytwister in hard_polytwisters.ALL_HARD_POLYTWISTERS:
        if polytwister_name in polytwister["names"]:
            break
    else:
        raise ValueError(f'Polytwister "{polytwister_name}" not found.')

    mesh = compute_polytwister_cross_section(polytwister, args.w)
    with open(args.obj_out, "w") as f:
        write_mesh_as_obj(mesh, f)


if __name__ == "__main__":
    main()
