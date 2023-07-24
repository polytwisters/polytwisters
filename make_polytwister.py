import argparse
import json
import math
import os
import subprocess
import sys
import traceback
import warnings

import bpy
import mathutils

directory = os.path.dirname(bpy.data.filepath)
if directory not in sys.path:
    sys.path.append(directory)

import hard_polytwisters
import soft_polytwisters

EXPECTED_BLENDER_VERSION = (3, 3)

EPSILON = 1e-10
LARGE = 10e3
DEFAULT_CYLINDER_RESOLUTION = 64

# Amount by which all polytwisters are scaled to fit nicely in frame.
DEFAULT_SCALE = 2.0


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
    w,
    zenith,
    azimuth,
    cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION,
):
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
    translate_x = w * math.tan(theta)
    bpy.ops.transform.translate(value=(translate_x, 0, 0))

    # In Bowers' code this rotation about the X-axis comes before the
    # translation. It doesn't matter because translation along the X-axis
    # commutes with rotations about the X-axis, but I prefer to group the
    # rotations together.
    rotate_about_axis("X", -theta)
    rotate_about_axis("Y", phi)

    return bpy.context.object


def create_empty_mesh():
    bpy.ops.mesh.primitive_cylinder_add()
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.editmode_toggle()


def _create_south_pole_cycloplane(w):
    """Create the cross section of a cycloplane whose point is located at the
    south pole."""
    deselect_all()
    if abs(w) >= 1:
        create_empty_mesh()
    else:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=LARGE,
            depth=2 * math.sqrt(1 - w * w),
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


def shade_auto_smooth():
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = math.radians(30.0)


class _Realizer:

    def __init__(self, w, cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION, scale=1):
        self.w = w
        self.cylinder_resolution = cylinder_resolution
        self.scale = scale

    def realize(self, polytwister):
        parts = self.traverse_root(polytwister["tree"])

        bpy.ops.material.new()
        material = bpy.data.materials[-1]

        for part in parts:
            deselect_all()
            part.select_set(True)
            bpy.context.view_layer.objects.active = part
            shade_auto_smooth()
            bpy.context.object.active_material = material

        group_under_empty(parts)
        do_scale(DEFAULT_SCALE * self.scale)
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
            return operands
        return [self.traverse(node)]

    def traverse(self, node):
        type_ = node["type"]
        if type_ == "cycloplane":
            create_cycloplane(
                self.w,
                node["zenith"],
                node["azimuth"],
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


def realize(polytwister, w, cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION, scale=1):
    realizer = _Realizer(w, cylinder_resolution=cylinder_resolution, scale=scale)
    return realizer.realize(polytwister)


def realize_soft_polytwister(polytwister, w, cylinder_resolution=DEFAULT_CYLINDER_RESOLUTION, scale=1):
    obj_path = "tmp.obj"
    subprocess.run([
        "py",
        "-3",
        "make_soft_polytwister.py",
        polytwister["names"][0],
        str(w),
        obj_path,
        "--resolution",
        str(cylinder_resolution),
        "--scale",
        str(scale),
    ], check=True)
    bpy.ops.import_scene.obj(filepath=obj_path)

    # The imported mesh is not automatically made active, but it is selected.
    for object_ in bpy.context.scene.objects:
        if object_.select_get():
            break
    else:
        raise RuntimeError("Selected mesh not found, may be a bug")
    bpy.context.view_layer.objects.active = object_

    do_scale(DEFAULT_SCALE)

    bpy.ops.object.modifier_add(type="REMESH")
    modifier = bpy.context.object.modifiers[-1]
    modifier.mode = "SHARP"
    modifier.octree_depth = 8
    modifier.use_smooth_shade = True

    bpy.ops.material.new()
    material = bpy.data.materials[-1]
    bpy.context.object.active_material = material

    principled_bsdf = material.node_tree.nodes["Principled BSDF"]
    settings = {
        "Base Color": (0.0634336, 0.493001, 0.8, 1),
        "Roughness": 0.1,
        "Transmission": 0.7,
    }
    settings = {
        "Base Color": (0.327, 0.217, 0.595, 1),
        "Roughness": 0.1,
        "Subsurface": 0.403,
        "Subsurface Radius": (0.02, 0.02, 0.02),
        "Subsurface Color": (0.327, 0.217, 0.595, 1),
        "Transmission": 0.05,
    }
    for key, value in settings.items():
        principled_bsdf.inputs[key].default_value = value


def get_max_distance_from_origin():
    result = 0.0
    objects = [bpy.context.object] + list(bpy.context.object.children)
    for object_ in objects:
        if object_.data is None:
            continue
        for vertex in object_.data.vertices:
            result = max(result, vertex.co.length)
    return result


def rotation_to_point_to_origin(point):
    """Given a location of an object pointing along the X-axis, return a set of
    Euler angles that will rotate that object so it points at the origin."""
    # See https://blender.stackexchange.com/a/5220.
    direction = -mathutils.Vector(point)
    rotation_quaternion = direction.to_track_quat("-Z", "Y")
    return rotation_quaternion.to_euler()


def convert_spherical_to_cartesian(radius, latitude, longitude):
    """Convert radius, latitude, and longitude to Cartesian coordinates.
    Angles are in radians. The north pole/south pole axis is the Z axis,
    which looks vertical by default in Blender.

    Note the use of latitude (signed angle from equator) rather than
    zenith angle (angle from the north pole).
    """
    return (
        radius * math.cos(longitude) * math.cos(latitude),
        radius * math.sin(longitude) * math.cos(latitude),
        radius * math.sin(latitude),
    )


def set_up_for_render():
    """This function does the following:

    - Add a camera object and set it to the primary camera of the scene.
    - Add lighting.
    - Add ambient occlusion.
    - Set the background to transparent.
    - Ensure the scene renders a square 1080x1080 image.
    - Set the engine to Cycles and the device to the GPU.
    - Reduce the sample count to 128 and the preview sample count to 16.
    - Set Render Properties -> Color Management -> Look to "High Contrast."

    When adjusting lighting and rendering, we are aiming for a decently
    photographic look with good depth perception but without distracting
    from the polytwister's shape. The lighting is a one-size-fits-all
    solution; ideally we would adjust lighting for individual
    polytwisters but that would take too much effort.

    We are using big area lights for soft shadows. Hard shadows can give
    the impression of features that aren't really there, and aren't
    appropriate for presenting mathematical objects.

    However, dark areas are not themselves bad -- insufficient contrast can
    inhibit depth perception and lead to an unattractive, washed-out
    appearance. I am told by my YouTube education that inadequate shadows
    are a common beginner mistake.

    Standard three-point lighting is used to light the object. Ambient
    occlusion adds some darkness to the crevices of nonconvex polytwisters,
    preventing overexposure in the area directly facing the key light.

    The Look setting in Color Management controls the nonlinear mapping
    from physical units to color values that look good on a monitor or
    projector. See the Blender docs on color management.
    """

    camera_distance = 14.5
    # Just enough angle to see the tops of convex polytwister sections.
    camera_latitude = math.radians(15)
    camera_longitude = math.radians(10)
    camera_location = convert_spherical_to_cartesian(
        camera_distance, camera_latitude, camera_longitude
    )
    bpy.ops.object.camera_add(
        location=camera_location,
        rotation=rotation_to_point_to_origin(camera_location)
    )
    camera = bpy.context.object
    bpy.context.scene.camera = bpy.context.object

    world_node_tree = bpy.context.scene.world.node_tree
    nodes = world_node_tree.nodes
    nodes.clear()

    background_node = nodes.new(type="ShaderNodeBackground")
    environment_node = nodes.new(type="ShaderNodeTexEnvironment")
    environment_node.image = bpy.data.images.load("//assets/studio_environment_2k.exr")
    output_node = nodes.new(type="ShaderNodeOutputWorld")
    links = world_node_tree.links
    links.new(environment_node.outputs["Color"], background_node.inputs["Color"])
    links.new(background_node.outputs["Background"], output_node.inputs["Surface"])

    # Latitude and longitude are given in degrees for readability.
    # Longitudes are relative to the camera: a longitude of 0 degrees
    # is directly behind the camera, 90 degrees is directly from the
    # right, -90 degrees is directly from the left. Latitudes are
    # absolute.
    light_specs = [
        # Key light
        {"latitude": 40, "longitude": -50, "power": 900, "radius": 5.0},
        # Fill light
        {"latitude": 0, "longitude": 50, "power": 300, "radius": 5.0},
        # Back light
        {"latitude": -20, "longitude": 180 + 45, "power": 400, "radius": 15.0},
    ]
    power_multiplier = 0.3
    distance = 10.0

    for light_spec in light_specs:
        latitude = math.radians(light_spec["latitude"])
        longitude = camera_longitude + math.radians(light_spec["longitude"])
        location = convert_spherical_to_cartesian(
            distance, latitude, longitude
        )
        bpy.ops.object.light_add(
            type="AREA",
            radius=light_spec["radius"],
            location=location,
            rotation=rotation_to_point_to_origin(location)
        )
        bpy.context.object.data.energy = light_spec["power"] * power_multiplier

    # Add some ambient occlusion.
    bpy.context.scene.cycles.use_fast_gi = True
    bpy.context.scene.world.light_settings.distance = 0.2

    # Set background to transparent.
    bpy.context.scene.render.film_transparent = True

    # Ensure a square image is produced.
    old_resolution = max([
        bpy.context.scene.render.resolution_x,
        bpy.context.scene.render.resolution_y,
    ])
    resolution = 1080
    bpy.context.scene.render.resolution_x = resolution
    bpy.context.scene.render.resolution_y = resolution

    # Adjust the camera width to compensate for the change in resolution.
    # See https://blender.stackexchange.com/a/105805/154615.
    camera.data.sensor_width *= resolution / old_resolution

    # Use Cycles and hardware acceleration.
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "GPU"

    # Greatly reduce the sample count. OpenImageDenoise is on by default,
    # and it does an excellent job.
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.preview_samples = 16

    # Improve contrast.
    bpy.context.scene.view_settings.look = "High Contrast"


def main():
    major, minor, patch = bpy.app.version
    if (major, minor) != EXPECTED_BLENDER_VERSION:
        warnings.warn(
            "This script is tested with Blender "
            f"{EXPECTED_BLENDER_VERSION[0]}.{EXPECTED_BLENDER_VERSION[1]}, but you have "
            f"{major}.{minor}.{patch}. Errors may occur."
        )

    # Delete the default objects.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    set_up_for_render()

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
        "-r",
        "--resolution",
        type=int,
        default=DEFAULT_CYLINDER_RESOLUTION,
        help="Number of segments used for cylinders.",
    )
    parser.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        help="If specified, normalize the size of the object so it fits nicely in camera.",
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
    parser.add_argument(
        "-m",
        "--metadata-out",
        type=str,
        help="If specified, write out a JSON file with information about the cross section."
    )
    parser.add_argument(
        "--mesh-out",
        type=str,
        help="If specified, write out a mesh file. Only .stl is supported."
    )

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
        "w": args.w,
        "cylinder_resolution": args.resolution,
        "scale": args.scale,
    }

    all_polytwisters = (
        hard_polytwisters.ALL_HARD_POLYTWISTERS
        + soft_polytwisters.ALL_SOFT_POLYTWISTERS
    )

    if polytwister_name == "all":
        for i, polytwister in enumerate(all_polytwisters):
            realize(polytwister, **kwargs)
            bpy.ops.transform.translate(value=(i * args.spacing, 0, 0))
    else:
        for polytwister in all_polytwisters:
            if polytwister_name in polytwister["names"]:
                break
        else:
            raise ValueError(f'Polytwister "{polytwister_name}" not found.')
        if polytwister["type"] == "hard":
            realize(polytwister, **kwargs)
        elif polytwister["type"] == "soft":
            realize_soft_polytwister(polytwister, **kwargs)
        else:
            raise ValueError("Invalid polytwister type")

    if args.normalize:
        max_distance_from_origin = get_max_distance_from_origin()
        if max_distance_from_origin != 0:
            do_scale(args.scale / max_distance_from_origin)

    if args.metadata_out is not None:
        with open(args.metadata_out, "w") as f:
            max_distance_from_origin = get_max_distance_from_origin()
            out_json = {
                "max_distance_from_origin": max_distance_from_origin
            }
            json.dump(out_json, f)

    if args.mesh_out is not None:
        bpy.ops.export_mesh.stl(filepath=args.mesh_out)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
