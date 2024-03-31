"""Tools for converting descriptions of hard polytwisters into 3D cross sections using OpenSCAD.
"""
import argparse
import math
import subprocess

from polytwisters.core import common
from polytwisters.core import hard_polytwisters

LARGE = 100.0
EPSILON = 1e-3


class CodeGenerator:

    def __init__(self):
        self.last_index = -1
        self.assignments = {}

    def assign(self, value):
        self.last_index += 1
        name = f"temp_{self.last_index}"
        self.assignments[name] = value
        return name + "()"

    def generate_assignments(self):
        result = []
        for key, value in self.assignments.items():
            result.append(f"module {key}() {{ {value};\n }}")
        return "".join(result)


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

    code = f"translate([0, 0, -{LARGE / 2}]) cylinder({LARGE}, 1, 1, $fn=100)"

    # The cylinder is along the Z-axis. Rotate about the X-axis to
    # change Z-axis to Y-axis and match with the original "cyl" object
    # in Bowers' POV-Ray code.
    code = f"rotate([90, 0, 0]) {code}"

    scale_x = 1 / math.cos(theta)
    code = f"scale([{scale_x}, 1, 1]) {code}"
    translate_x = w * math.tan(theta)
    code = f"translate([{translate_x}, 0, 0]) {code}"

    # In Bowers' code this rotation about the X-axis comes before the
    # translation. It doesn't matter because translation along the X-axis
    # commutes with rotations about the X-axis, but I prefer to group the
    # rotations together.
    code = f"rotate([{math.degrees(-theta)}, 0, 0]) {code}"
    code = f"rotate([0, {math.degrees(phi)}, 0]) {code}"

    return code


def _create_south_pole_cycloplane(w):
    """Create the cross section of a cycloplane whose point is located at the
    south pole."""
    if abs(w) >= 1:
        return ""
    half_height = math.sqrt(1 - w * w)
    code = f"translate([0, 0, {-half_height}]) cylinder({half_height * 2}, {LARGE}, {LARGE}, $fn=100)"
    # See comment in create_cycloplane.
    code = f"rotate([90, 0, 0]) {code}"
    return code


def make_rotated_copies(code_gen, part, n):
    name = code_gen.assign(part)
    parts = []
    for i in range(n):
        code = f"rotate([0, {360 * i / n}, 0]) {name}"
        parts.append(code)
    return parts


def bubble(x):
    if isinstance(x, list):
        return x
    return [x]


class Realizer:

    def __init__(self, w):
        self.w = w
        self.code_gen = None

    def realize(self, polytwister):
        self.code_gen = CodeGenerator()
        code = self.traverse(polytwister["tree"])
        return self.code_gen.generate_assignments() + code

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
            return make_rotated_copies(self.code_gen, first, node["order"])
        elif type_ in ["intersection", "difference", "union"]:
            code = []
            for child in node["operands"]:
                operands = bubble(self.traverse(child))
                for operand in operands:
                    code.append(operand + ";")
            return type_ + "() { " + "\n".join(code) + " }"
        else:
            raise ValueError(f'Invalid node type {type_}')


def make_polytwister_cross_section_openscad_code(polytwister, w):
    return Realizer(w).realize(polytwister)


def make_polytwister_cross_section(polytwister, w, out_stl):
    code = make_polytwister_cross_section_openscad_code(polytwister, w)
    file_name = "temp.scad"
    with open(file_name, "w") as file:
        file.write(code)
    subprocess.run([
        r"C:\Program Files\OpenSCAD\openscad.exe",
        file_name,
        "-o",
        out_stl, 
    ], check=True)


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
            "W-coordinate of the 3-space where the cross section is taken."
        ),
    )
    args = parser.parse_args()
    polytwister_name = common.normalize_polytwister_name(args.polytwister)

    polytwister = hard_polytwisters.get_all_hard_polytwisters()[polytwister_name]
    make_polytwister_cross_section(polytwister, 0.1, "out.stl")


if __name__ == "__main__":
    main()