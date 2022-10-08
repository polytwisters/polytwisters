import math
import os
import sys
import warnings
import bpy

directory = os.path.dirname(bpy.data.filepath)
if directory not in sys.path:
    sys.path.append(directory)
import polytwisters

EPSILON = 1e-10
LARGE = 10e3


def deselect_all():
    bpy.ops.object.select_all(action="DESELECT")


def rotate_about_axis(axis, angle):
    # See https://stackoverflow.com/a/67697363.
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            view_3d = area
            break 
    else:
        raise RuntimeError("VIEW_3D area not found")

    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    with bpy.context.temp_override(area=view_3d):
        bpy.ops.transform.rotate(
            value=angle,
            orient_axis=axis,
        )


def group_under_empty(parts):
    """Create an empty and group every object in parts as the child of
    that empty."""
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    parent = bpy.context.object
    for part in parts:
        part.select_set(True)
    bpy.ops.object.parent_set(type="OBJECT")
    deselect_all()
    bpy.context.view_layer.objects.active = parent
    parent.select_set(True)
    return parent


def create_cycloplane(z, latitude, longitude):
    """Create a cross section of a cycloplane constructed from a Hopf fiber.
    z is the cross section coordinate, latitude and longitude are the
    coordinates of the point on the sphere. Said point is transformed via the
    preimage of the Hopf fibration into a unit circle, then the cycloplane is
    constructed from that unit circle.

    Note that latitude is defined differently from normal -- it is the angle
    from the north pole, not the angle from the equator.

    See "cylli" macro in Bowers' original code."""

    # Reason for division by 2 currently unclear, sorry.
    theta = latitude / 2
    phi = longitude

    if abs(theta - math.pi / 2) < EPSILON:
        return _create_south_pole_cycloplane(z)

    deselect_all()
    bpy.ops.mesh.primitive_cylinder_add(
        radius=1,
        depth=LARGE,
        vertices=64,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )

    # The cylinder is along the Z-axis. Rotate about the X-axis to
    # change Z-axis to Y-axis and match with the original "cyl" object
    # in Bowers' POV-Ray code.
    rotate_about_axis("X", math.pi / 2)

    scale_x = 1 / math.cos(theta)
    bpy.ops.transform.resize(value=(scale_x, 1, 1))
    translate_x = z * math.tan(theta)
    bpy.ops.transform.translate(value=(translate_x, 0, 0))

    # In Bowers' code this rotation about the X-axis comes before the
    # translation. It doesn't matter because translation along the X-axis
    # commutes with rotations about the X-axis, but I prefer to group the
    # rotations together.
    rotate_about_axis("X", -theta)
    rotate_about_axis("Y", phi)

    return bpy.context.object


def _create_south_pole_cycloplane(z):
    """Create the cross section of a cycloplane whose point is located at the
    south pole."""
    deselect_all()
    bpy.ops.mesh.primitive_cylinder_add(
        radius=LARGE,
        depth=2 * math.sqrt(1 - z * z),
        vertices=32,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )

    # See comment in create_cycloplane.
    rotate_about_axis("X", math.pi / 2)
    
    return bpy.context.object


def do_boolean(operation, objects, delete=True):
    """Given a list of Blender objects, compute a Boolean op of all of
    them by creating and applying Boolean modifiers on the first object, then
    optionally deleting the rest of the objects.

    It is assumed that there are no other modifiers on the first object."""
    first = objects[0]
    for i, other in enumerate(objects[1:]):
        index = i + 1

        deselect_all()
        first.select_set(True)
        bpy.context.view_layer.objects.active = first
        bpy.ops.object.modifier_add(type="BOOLEAN")
        modifier = bpy.context.object.modifiers[-1]
        modifier.operation = operation
        modifier.object = other
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        if delete:
            deselect_all()
            other.select_set(True)
            bpy.ops.object.delete()

    first.select_set(True)
    return bpy.context.object


def make_rotated_copies(n):
    copies = []
    for i in range(n - 1):
        bpy.ops.object.duplicate()
        rotate_about_axis("Y", 2 * math.pi / n)
        copies.append(bpy.context.object)
    return copies


class _Realizer:

    def __init__(self, z):
        self.z = z

    def realize(self, polytwister):
        self.traverse_root(polytwister["tree"])

    def traverse_root(self, node):
        type_ = node["type"]
        # If the root node is a union, save some computation time by grouping the
        # operands under an empty rather than computing the actual union.
        if type_ == "union":
            operands = []
            for node in node["operands"]:
                child = self.traverse(node)
                if isinstance(child, list):
                    operands.extend(child)
                else:
                    operands.append(child)
            return group_under_empty(operands)
        return self.traverse(node)

    def traverse(self, node):
        type_ = node["type"]
        if type_ == "cycloplane":
            create_cycloplane(
                self.z, node["latitude"], node["longitude"]
            )
            return bpy.context.object
        elif type_ == "rotated_copies":
            first = self.traverse(node["operand"])
            return [first] + make_rotated_copies(node["order"])
        elif type_ == "intersection":
            operands = []
            for child in node["operands"]:
                operand = self.traverse(child)
                operands.append(operand)
            return do_boolean("INTERSECT", operands)
        elif type_ == "difference":
            operands = []
            for child in node["operands"]:
                operand = self.traverse(child)
                operands.append(operand)
            return do_boolean("DIFFERENCE", operands)
        elif type_ == "union":
            operands = []
            for child in node["operands"]:
                operand = self.traverse(child)
                operands.append(operand)
            return do_boolean("UNION", operands)
        else:
            raise ValueError(f'Invalid node type {type_}')


def realize(polytwister, z):
    realizer = _Realizer(z)
    return realizer.realize(polytwister)


def create_convex_regular_polytwisters(z, spacing=2.5, translate_z=1):
    platonic_solid_polytwisters = [
        polytwisters.get_tetratwister(),
        polytwisters.get_cubetwister(),
        polytwisters.get_octatwister(),
        polytwisters.get_dodecatwister(),
        polytwisters.get_icosatwister(),
    ]
    dyadic_twisters = [
        polytwisters.get_dyadic_twister(3 + n)
        for n in range(len(platonic_solid_polytwisters))
    ]

    for i, polytwister in enumerate(platonic_solid_polytwisters):
        realize(polytwister, z=z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(value=(i * spacing, 0, translate_z))

    for i, polytwister in enumerate(dyadic_twisters):
        realize(polytwister, z=z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(
            value=(i * spacing, 0, translate_z + spacing)
        )


if __name__ == "__main__":
    import argparse

    expected_version = (3, 2)
    major, minor, patch = bpy.app.version
    if (major, minor) != expected_version:
        warnings.warn(
            "This script is tested with Blender "
            f"{expected_version[0]}.{expected_version[1]}, but you have "
            f"{major}.{minor}.{patch}. Errors may occur."
        )

    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    spacing = 5.0

    z = 0.14

    create_convex_regular_polytwisters(z)

    polytwisters = [
        polytwisters.get_quasitetratwister(),
        polytwisters.get_bloated_tetratwister(),
        polytwisters.get_quasicubetwister(),
        polytwisters.get_bloated_cubetwister(),
        polytwisters.get_quasioctatwister(),
        polytwisters.get_bloated_octatwister(),
        polytwisters.get_quasidodecatwister(),
    ]

    for i, polytwister in enumerate(polytwisters):
        realize(polytwister, z=z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(
            value=(i * spacing, 0, -spacing)
        )
