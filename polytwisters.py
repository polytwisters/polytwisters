import math
import bpy
import mathutils

EPSILON = 1e-10
LARGE = 10e3

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


def create_cycloplane(theta, z):
    # if abs(theta - math.pi / 2) < EPSILON:

    scale_x = 1 / math.cos(theta)
    translate_x = z * math.tan(theta)

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cylinder_add(
        radius=1,
        depth=LARGE,
        vertices=32,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )

    # The cylinder is normally about the Z-axis. Rotate about the X-axis to
    # change Z-axis to Y-axis and match with the original "cyl" object.
    rotate_about_axis("X", math.pi / 2)

    bpy.ops.transform.resize(value=(scale_x, 1, 1))
    rotate_about_axis("X", -theta)
    bpy.ops.transform.translate(value=(translate_x, 0, 0))


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    z = 0.1
    theta = math.pi / 4
    n = 5
    for k in range(n):
        create_cycloplane(theta, z) 
        rotate_about_axis("Y", k * 2 * math.pi / n)
