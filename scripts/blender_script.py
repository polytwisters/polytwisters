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

import common

EXPECTED_BLENDER_VERSION = (3, 3)

EPSILON = 1e-10
LARGE = 10e3
DEFAULT_CYLINDER_RESOLUTION = 64

# Radius of polytwister's minimum containing sphere.
# 20cm feels like a good size.
DEFAULT_SCALE = 20e-2 / 2


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


def make_material_from_config(config):
    """Create a material on the active object and configure a Principled BSDF."""
    bpy.ops.material.new()
    material = bpy.data.materials[-1]
    bpy.context.object.active_material = material

    if config is None:
        return material

    principled_bsdf = material.node_tree.nodes["Principled BSDF"]
    for key, value in config.items():
        if isinstance(value, list):
            value = tuple(value)
        principled_bsdf.inputs[key].default_value = value

    return material


def shade_auto_smooth():
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = math.radians(30.0)


def realize_hard_polytwister(
    polytwister,
    w,
    material_config=None,
    scale=1.0,
):
    pass

def realize_soft_polytwister(
    polytwister,
    w,
    resolution=DEFAULT_CYLINDER_RESOLUTION,
    material_config=None,
    scale=1.0,
):
    obj_path = "tmp.obj"
    subprocess.run(common.PYTHON + [
        "make_soft_polytwister.py",
        polytwister["names"][0],
        str(w),
        obj_path,
        "--resolution",
        str(resolution),
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

    make_material_from_config(material_config)


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


def set_up_for_render(config):
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

    camera_distance = 1.0

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
    # Close-up shot with low perspective distortion.
    camera.data.lens = 85
    camera.data.display_size = 0.2
    bpy.context.scene.camera = bpy.context.object

    world_node_tree = bpy.context.scene.world.node_tree
    nodes = world_node_tree.nodes
    nodes.clear()
    background_node = nodes.new(type="ShaderNodeBackground")
    background_node.inputs["Strength"].default_value = config.get("environment_strength", 0.5)
    environment_node = nodes.new(type="ShaderNodeTexEnvironment")
    environment_node.image = bpy.data.images.load(
        config.get("environment_image", "//assets/studio_environment_2k.exr")
    )
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
        # Key light illuminates most of the front of the object
        {"latitude": 10, "longitude": -50, "power": 100, "radius": 3.0},
        # Fill light gently illuminates the shadows left by the key light
        # Don't make this too strong, shadows are good
        {"latitude": 0, "longitude": 50, "power": 25, "radius": 3.0},
        # I used to have a back light here but it didn't work too well. The HDRI is sufficient for
        # preventing really dark areas.
    ]
    # If the lights are too bright, then this variable allows dimming all at once.
    power_multiplier = 1.0
    distance = 5.0

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
    resolution = config.get("resolution", 1080)
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
    bpy.context.scene.cycles.samples = config.get("samples", 128)
    bpy.context.scene.cycles.preview_samples = config.get("preview_samples", 16)

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

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "obj_file",
        help="Input Wavefront OBJ file.",
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
        "-c",
        "--config",
        type=str,
        help=(
            "JSON string for render configuration."
        ),
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

    if args.config is not None:
        config = json.loads(args.config)
    elif args.config_file is not None:
        with open(args.config_file) as file:
            config = json.load(file)
    else:
        with open("config.json") as file:
            config = json.load(file)

    polytwister_config = config.get("defaults", {})
    for candidate in config["polytwisters"]:
        # hack, sorry
        if candidate["name"].replace("_", " ") == polytwister_name:
            polytwister_config.update(candidate)

    kwargs = {
        "w": args.w,
        "scale": args.scale,
        "material_config": polytwister_config.get("material", None),
    }

    # Delete the default objects.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
