import math
import bpy
import mathutils

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

def create_cycloplane(theta, z):
    """Create a cycloplane cross section. This corresponds to the "cylli" macro
    in Bowers' original code."""
    if abs(theta - math.pi / 2) < EPSILON:
        _create_90_degree_cycloplane(z)
        return

    deselect_all()
    bpy.ops.mesh.primitive_cylinder_add(
        radius=1,
        depth=LARGE,
        vertices=32,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )

    # The cylinder is along the Z-axis. Rotate about the X-axis to
    # change Z-axis to Y-axis and match with the original "cyl" object
    # in Bowers' POV-Ray code.
    rotate_about_axis("X", math.pi / 2)

    scale_x = 1 / math.cos(theta)
    bpy.ops.transform.resize(value=(scale_x, 1, 1))
    rotate_about_axis("X", -theta)
    translate_x = z * math.tan(theta)
    bpy.ops.transform.translate(value=(translate_x, 0, 0))


def _create_90_degree_cycloplane(z):
    """Create the cross section of a cycloplane that has been rotated 90 degrees
    in the xz-axis, with cross section coordinate z."""
    deselect_all()
    bpy.ops.mesh.primitive_cylinder_add(
        radius=LARGE,
        depth=2 * math.sqrt(1 - z * z),
        vertices=32,
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    rotate_about_axis("X", math.pi / 2)


def intersect(objects):
    """Given a list of Blender objects, compute the intersection of all of
    them by creating and applying Boolean modifiers on the first object, then
    deleting the rest of the objects.

    It is assumed that there are no other modifiers on the first object."""
    first = objects[0]
    for other in objects[1:]:
        deselect_all()
        first.select_set(True)
        bpy.context.view_layer.objects.active = first
        bpy.ops.object.modifier_add(type="BOOLEAN")
        modifier = bpy.context.object.modifiers[-1]
        modifier.operation = "INTERSECT"
        modifier.object = other
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        deselect_all()
        other.select_set(True)
        bpy.ops.object.delete()


def create_dyster(n, z):
    """Compute the cross section of a convex dyster (hosohedral polytwister) of
    order n at coordinate z."""
    cycloplanes = []
    for i in range(n):
        create_cycloplane(math.pi / 4, z) 
        rotate_about_axis("Y", i * 2 * math.pi / n)
        cycloplanes.append(bpy.context.object)
    intersect(cycloplanes)


def create_tetratwister(z):
    """Compute the cross section of a tetratwister at coordinate z."""
    cycloplanes = []
    create_cycloplane(math.pi / 2, z)
    cycloplanes.append(bpy.context.object)
    for i in range(3):
        # Let C be the center of a regular tetrahedron and A, B two vertices.
        # This is the angle ACB: math.acos(-1 / 3) = 54.736 degrees
        # On https://en.wikipedia.org/wiki/Tetrahedron#Regular_tetrahedron
        # this is the "Vertex-Center-Vertex angle."
        # Not sure why Bowers divides it by 2 subtracts it from pi/2.
        create_cycloplane(math.pi / 2 - math.acos(-1 / 3) / 2, z)
        rotate_about_axis("Y", i * 2 * math.pi / 3)
        cycloplanes.append(bpy.context.object)
    intersect(cycloplanes)


def create_cubetwister(z):
    """Compute the cross section of a cubetwister at coordinate z."""
    cycloplanes = []
    for theta in [0, math.pi / 2]:
        create_cycloplane(theta, z)
        cycloplanes.append(bpy.context.object)
    for i in range(4):
        create_cycloplane(math.pi / 4, z)
        rotate_about_axis("Y", i * math.pi / 2)
        cycloplanes.append(bpy.context.object)
    intersect(cycloplanes)


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    create_tetratwister(0.5)
