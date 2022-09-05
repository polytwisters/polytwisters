import bpy

LARGE = 10e3
IDENTITY_MATRIX = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


if __name__ == "__main__":
    bpy.ops.object.delete(use_global=False)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cylinder_add(
        radius=1,
        depth=LARGE,
        vertices=32,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    bpy.ops.transform.resize(
        value=(4.0667, 1, 1),
        orient_matrix=IDENTITY_MATRIX,
        constraint_axis=(True, False, False),
    )
    bpy.ops.transform.translate(
        value=(3.19481, 0, 0),
        orient_matrix=IDENTITY_MATRIX,
        constraint_axis=(True, False, False),
    )
    bpy.ops.view3d.snap_cursor_to_center()
    bpy.ops.transform.rotate(
        value=1.9713,
        orient_axis='X',
        orient_type='GLOBAL',
        orient_matrix=IDENTITY_MATRIX,
        constraint_axis=(True, False, False),
    )
