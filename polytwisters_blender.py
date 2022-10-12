import math
import os
import sys
import warnings

import bpy
import mathutils

directory = os.path.dirname(bpy.data.filepath)
if directory not in sys.path:
    sys.path.append(directory)
import polytwisters

EPSILON = 1e-10
LARGE = 10e3
DEFAULT_CYLINDER_RESOLUTION = 64


def deselect_all():
    bpy.ops.object.select_all(action="DESELECT")


def do_scale(amount):
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.transform.resize(value=(amount, amount, amount))


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


def create_cycloplane(
    z,
    latitude,
    longitude,
    cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION,
):
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
        vertices=cylinder_resolution,
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

    bpy.ops.object.shade_smooth()
    bpy.context.object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = math.radians(30.0)

    return bpy.context.object


def _create_south_pole_cycloplane(z):
    """Create the cross section of a cycloplane whose point is located at the
    south pole."""
    deselect_all()
    if z >= 1:
        bpy.ops.object.empty_add(type="PLAIN_AXES")
    else:
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

    def __init__(self, z, cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION, scale=1):
        self.z = z
        self.cylinder_resolution = cylinder_resolution
        self.scale = scale

    def realize(self, polytwister):
        self.traverse_root(polytwister["tree"])
        do_scale(self.scale)
        # Change the polytwister's axis of symmetry from Y to Z so it stands
        # upright in Blender, purely for aesthetic reasons.
        rotate_about_axis("X", math.pi / 2)

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
                self.z,
                node["latitude"],
                node["longitude"],
                cylinder_resolution=self.cylinder_resolution,
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


def realize(polytwister, z, cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION, scale=1):
    realizer = _Realizer(z, cylinder_resolution=cylinder_resolution, scale=scale)
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
        bpy.ops.transform.translate(value=(i * spacing, 0, translate_z))

    for i, polytwister in enumerate(dyadic_twisters):
        realize(polytwister, z=z)
        bpy.ops.transform.translate(
            value=(i * spacing, 0, translate_z + spacing)
        )


def rotation_to_point_to_origin(point):
    """Given a location of an object pointing along the X-axis, return a set of
    Euler angles that will rotate that object so it points at the origin."""
    # See https://blender.stackexchange.com/a/5220.
    direction = -mathutils.Vector(point)
    rotation_quaternion = direction.to_track_quat("-Z", "Y")
    return rotation_quaternion.to_euler()


def set_up_camera_and_lights():
    camera_location = (10, 10, 3)
    bpy.ops.object.camera_add(
        location=camera_location,
        rotation=rotation_to_point_to_origin(camera_location)
    )
    bpy.context.scene.camera = bpy.context.object

    light_specs = [
        {"location": (-10, 10, 10), "power": 500},
        {"location": (10, -10, -10), "power": 200},
        {"location": (10, -10, 5), "power": 500},
    ]

    for light_spec in light_specs:
        location = light_spec["location"]
        bpy.ops.object.light_add(
            type="AREA",
            radius=5,
            location=location,
            rotation=rotation_to_point_to_origin(location)
        )
        bpy.context.object.data.energy = light_spec["power"]

    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "GPU"


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

    # Delete the default objects.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    set_up_camera_and_lights()

    parser = argparse.ArgumentParser()
    parser.add_argument("polytwister")
    parser.add_argument("z", type=float)
    parser.add_argument("-r", "--resolution", type=int, default=DEFAULT_CYLINDER_RESOLUTION)
    parser.add_argument("-s", "--scale", type=float, default=1)

    argv = sys.argv
    for i, argument in enumerate(argv):
        if argument == "--":
            argv = argv[i + 1:]
            break
    else:
        argv = []
    args = parser.parse_args(argv)

    polytwister_name = args.polytwister
    polytwister_name = polytwister_name.replace("_", " ")

    kwargs = {
        "z": args.z,
        "cylinder_resolution": args.resolution,
        "scale": args.scale,
    }

    if polytwister_name == "all":
        for i, polytwister in enumerate(polytwisters.ALL_POLYTWISTERS):
            realize(polytwister, **kwargs)
            bpy.ops.transform.translate(value=(i * args.spacing, 0, 0))
    else:
        for polytwister in polytwisters.ALL_POLYTWISTERS:
            if polytwister_name in polytwister["names"]:
                break
        else:
            raise ValueError(f'Polytwister "polytwister_name" not found.')
        realize(polytwister, **kwargs)
