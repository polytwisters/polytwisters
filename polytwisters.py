import math
import time
import bpy

EPSILON = 1e-10
LARGE = 10e3
PHI = (1 + math.sqrt(5)) / 2


def get_3d_squared_distance(point_1, point_2):
    """Get the distance between two points in 3D represented as tuples."""
    x_1, y_1, z_1 = point_1
    x_2, y_2, z_2 = point_2
    return (x_1 - x_2) ** 2 + (y_1 - y_2) ** 2 + (z_1 - z_2) ** 2


def get_3d_angle(a, b, c):
    """Given 3D points A, B, and C, get the angle ABC in radians."""
    a_2 = get_3d_squared_distance(b, c)
    b_2 = get_3d_squared_distance(a, c)
    c_2 = get_3d_squared_distance(a, b)
    # Law of cosines: b^2 = a^2 + c^2 - 2 a c cos(theta)
    return math.acos((a_2 + c_2 - b_2) / (2 * math.sqrt(a_2 * c_2)))


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


def intersect(objects, delete=True):
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

        if delete:
            deselect_all()
            other.select_set(True)
            bpy.ops.object.delete()

    first.select_set(True)
    return bpy.context.object


def difference(object_1, object_2):
    """Given a list of Blender objects, compute the intersection of all of
    them by creating and applying Boolean modifiers on the first object, then
    deleting the rest of the objects.

    It is assumed that there are no other modifiers on the first object."""
    deselect_all()
    object_1.select_set(True)
    bpy.context.view_layer.objects.active = object_1
    bpy.ops.object.modifier_add(type="BOOLEAN")
    modifier = bpy.context.object.modifiers[-1]
    modifier.operation = "DIFFERENCE"
    modifier.object = object_2
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    deselect_all()
    object_2.select_set(True)
    bpy.ops.object.delete()

    object_1.select_set(True)
    return bpy.context.object


def get_hosohedron(n):
    result = []
    for i in range(n):
        result.append((math.pi / 2, i * 2 * math.pi / n))
    return result


def get_tetrahedron():
    result = []
    result.append((math.pi, 0))

    # Let A and B be two vertices of a regular tetrahedron centered at C.
    # This is the angle ACB.
    # On https://en.wikipedia.org/wiki/Tetrahedron#Regular_tetrahedron
    # this is the "Vertex-Center-Vertex angle."
    latitude = get_3d_angle((1, 1, 1), (0, 0, 0), (1, -1, -1))

    for i in range(3):
        result.append((math.pi - latitude, i * 2 * math.pi / 3))
    return result


def get_cube():
    result = []
    result.append((0, 0))
    result.append((math.pi, 0))
    for i in range(4):
        result.append((math.pi / 2, i * math.pi / 2))
    return result


def get_octahedron():
    result = []
    # Let A be a vertex of a regular octahedron centered at C and let B be
    # the center of an adjacent face. This is the angle ACB.
    latitude = get_3d_angle((1, 0, 0), (0, 0, 0), (1, 1, 1))
    for i in range(4):
        result.append((latitude, i * math.pi / 2))
        result.append((math.pi - latitude, i * math.pi / 2))
    return result


def get_dodecahedron():
    result = []
    result.append((0, 0))
    result.append((math.pi, 0))
    # Let A and B be the centers of two adjacent faces of a regular
    # dodecahedron centered at C. This is the angle ACB.
    # Equivalently, A and B are two adjacent vertices of a regular
    # icosahedron centered at C. We are using the standard definition of
    # icosahedron coordinates.
    latitude = get_3d_angle((0, 1, PHI), (0, 0, 0), (0, -1, PHI))
    for j in range(5):
        result.append((latitude, j * 2 * math.pi / 5))
        result.append((math.pi - latitude, (j + 1 / 2) * 2 * math.pi / 5))
    return result


def get_icosahedron():
    result = []
    # Let A be the center of a face of a regular dodecahedron centered at C,
    # and let B be one of the three closest vertices. This is the angle ACB.
    latitude_1 = get_3d_angle((1, 1, 1), (0, 0, 0), (0, 1, PHI))
    # Same as above, but B is now one of the three second closest vertices
    # to A.
    latitude_2 = get_3d_angle((1, 1, 1), (0, 0, 0), (0, -1, PHI))
    for j in range(5):
        longitude_1 = j * 2 * math.pi / 5
        longitude_2 = (j + 1 / 2) * 2 * math.pi / 5
        result.append((latitude_1, longitude_1))
        result.append((latitude_2, longitude_1))
        result.append((math.pi - latitude_2, longitude_2))
        result.append((math.pi - latitude_1, longitude_2))
    return result


def create_convex_polytwister(polyhedron, z):
    cycloplanes = []
    for latitude, longitude in polyhedron:
        cycloplane = create_cycloplane(z, latitude, longitude)
        cycloplanes.append(cycloplane)
    return intersect(cycloplanes)


def create_platonic_solid_polytwisters(z, spacing=2.5, translate_z=1):
    polyhedra = [
        get_tetrahedron(),
        get_cube(),
        get_octahedron(),
        get_dodecahedron(),
        get_icosahedron(),
    ]
    for i, polyhedron in enumerate(polyhedra):
        create_convex_polytwister(polyhedron, z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(value=(i * spacing, 0, translate_z))


def create_quasitetratwister(z):
    # TODO reduce code duplication with get_tetrahedron()

    def create_south_pole_cycloplane():
        create_cycloplane(z, math.pi, 0)
        return bpy.context.object

    def create_other_cycloplanes():
        result = []
        for i in range(3):
            latitude = math.pi - math.acos(-1 / 3)
            longitude = i * 2 * math.pi / 3
            create_cycloplane(z, latitude, longitude)
            cycloplane = bpy.context.object
            result.append(cycloplane)
        return result

    ring_1 = difference(
        intersect(create_other_cycloplanes()),
        create_south_pole_cycloplane()
    )
    
    other = create_other_cycloplanes() 
    ring_2 = difference(
        intersect([create_south_pole_cycloplane(), other[0], other[1]]),
        other[2]
    )

    for i in range(2):
        bpy.ops.object.duplicate()
        rotate_about_axis("Y", 2 * math.pi / 3)

    return ring_1


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    create_platonic_solid_polytwisters(0.5)
