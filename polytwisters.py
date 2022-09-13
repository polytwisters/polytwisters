import math
import bpy

EPSILON = 1e-10
LARGE = 10e3
IDENTITY_MATRIX = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


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
    bpy.ops.transform.resize(
        value=(scale_x, 1, 1),
        orient_matrix=IDENTITY_MATRIX,
        constraint_axis=(True, False, False),
    )
    bpy.ops.transform.translate(
        value=(translate_x, 0, 0),
        orient_matrix=IDENTITY_MATRIX,
        constraint_axis=(True, False, False),
    )

    # bpy.ops.view3d.snap_cursor_to_center()
    # bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'

    context = bpy.context.copy()
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            context["area"] = area
            break 
    else:
        raise RuntimeError("VIEW_3D area not found")

    axes = ["X", "Y", "Z"]
    for i in range(3):
        bpy.ops.transform.rotate(
            context,
            value=rotation[i],
            orient_axis=axes[i],
            orient_type='GLOBAL',
            orient_matrix=IDENTITY_MATRIX,
        )


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    z = 0.1
    create_cycloplane(0, z, (0.1, 0, 0)) 
    create_cycloplane(0.3, z, (1.4, 0, 0)) 
