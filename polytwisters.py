import math
import time
import bpy

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
        _create_south_pole_cycloplane(z)
        return

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
    rotate_about_axis("X", -theta)
    translate_x = z * math.tan(theta)
    bpy.ops.transform.translate(value=(translate_x, 0, 0))

    rotate_about_axis("Y", phi)


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


def intersect(objects):
    """Given a list of Blender objects, compute the intersection of all of
    them by creating and applying Boolean modifiers on the first object, then
    deleting the rest of the objects.

    It is assumed that there are no other modifiers on the first object."""
    first = objects[0]
    for i, other in enumerate(objects[1:]):
        index = i + 1
        print(f"Computing intersection {index}/{len(objects) - 1}...")

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

    first.select_set(True)


def get_hosohedron(n):
    result = []
    for i in range(n):
        result.append((math.pi / 2, i * 2 * math.pi / n))
    return result


def get_tetrahedron():
    result = []
    result.append((math.pi, 0))
    for i in range(3):
        # Let C be the center of a regular tetrahedron and A, B two vertices.
        # This is the angle ACB: math.acos(-1 / 3) = 54.736 degrees
        # On https://en.wikipedia.org/wiki/Tetrahedron#Regular_tetrahedron
        # this is the "Vertex-Center-Vertex angle."
        result.append((
            math.pi - math.acos(-1 / 3),
            i * 2 * math.pi / 3
        ))
    return result


def get_cube():
    result = []
    for latitude in [0, math.pi]:
        result.append((latitude, 0))
    for i in range(4):
        result.append((math.pi / 2, i * math.pi / 2))
    return result


def get_octahedron():
    result = []
    # Ported from Bowers' code. Origin of constant unclear, sorry.
    ano = 2 * math.radians(27.3678052)
    for latitude in [ano, math.pi - ano]:
        for i in range(4):
            result.append((latitude, i * math.pi / 2))
    return result


def get_dodecahedron():
    result = []
    for latitude in [0, math.pi]:
        result.append((latitude, 0))
    # Ported from Bowers' code. Origin of constant unclear, sorry.
    an = 2 * math.radians(31.7147441)
    for i, latitude in enumerate([an, math.pi - an]):
        for j in range(5):
            result.append((latitude, (j + i / 2) * 2 * math.pi / 5))
    return result


def get_icosahedron():
    result = []
    # Ported from Bowers' code. Origin of constants unclear, sorry.
    am2 = 2 * math.radians(18.68868407041)
    am3 = 2 * math.radians(39.593841518)
    angles = [am2, am3, math.pi - am3, math.pi - am2]
    for i, latitude in enumerate(angles):
        offset = 1 if i >= 2 else 0
        for j in range(5):
            result.append((latitude, (j + offset / 2) * 2 * math.pi / 5))
    return result


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    z = 0.5

    polyhedra = [
        get_tetrahedron(),
        get_cube(),
        get_octahedron(),
        get_dodecahedron(),
        get_icosahedron(),
    ]

    for i, polyhedron in enumerate(polyhedra):
        cycloplanes = []
        for latitude, longitude in polyhedron:
            create_cycloplane(z, latitude, longitude)
            cycloplanes.append(bpy.context.object)
        intersect(cycloplanes)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(value=(i * 2, 0, 1))
