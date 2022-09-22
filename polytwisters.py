import math
import bpy

EPSILON = 1e-10
LARGE = 10e3


def create_cycloplane(theta, z, rotation):
    # if abs(theta - math.pi / 2) < EPSILON:

    scale_x = 1 / math.cos(theta)
    translate_x = z * math.tan(theta)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cylinder_add(
        radius=1,
        depth=LARGE,
        vertices=32,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    bpy.ops.transform.resize(value=(scale_x, 1, 1))
    bpy.ops.transform.translate(value=(translate_x, 0, 0))

    # See https://stackoverflow.com/a/67697363.
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            view_3d = area
            break 
    else:
        raise RuntimeError("VIEW_3D area not found")

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    with bpy.context.temp_override(area=view_3d):
        axes = ["X", "Y", "Z"]
        for i in range(3):
            bpy.ops.transform.rotate(
                value=rotation[i],
                orient_axis=axes[i],
            )


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    z = 0.5
    create_cycloplane(0, z, (0.1, 0, 0)) 
    create_cycloplane(1.3, z, (1.4, 1.4, 0)) 
