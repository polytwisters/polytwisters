"""
A Blender script for creating polytwister cross sections.
"""

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


def cycloplane(latitude, longitude):
    """Shortcut function for the cycloplane node type."""
    return {"type": "cycloplane", "latitude": latitude, "longitude": longitude}


def intersection(nodes):
    """Shortcut function for the intersection node type."""
    return {"type": "intersection", "operands": nodes}


def difference(nodes):
    """Shortcut function for the difference node type."""
    return {"type": "difference", "operands": nodes}


def rotated_copies(node, order):
    """Shortcut function the rotated_copies node type."""
    return {"type": "rotated_copies", "order": order, "operand": node}


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


def do_boolean(operation, objects, delete=True):
    """Given a list of Blender objects, compute a Boolean op of all of
    them by creating and applying Boolean modifiers on the first object, then
    optionally deleting the rest of the objects.

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
        modifier.operation = operation
        modifier.object = other
        bpy.ops.object.modifier_apply(modifier=modifier.name)

        if delete:
            deselect_all()
            other.select_set(True)
            bpy.ops.object.delete()

    first.select_set(True)
    return bpy.context.object


def do_intersect(objects):
    return do_boolean("INTERSECT", objects)


def do_difference(object_1, object_2):
    return do_boolean("DIFFERENCE", [object_1, object_2])


def make_rotated_copies(n):
    copies = []
    for i in range(n - 1):
        bpy.ops.object.duplicate()
        rotate_about_axis("Y", 2 * math.pi / n)
        copies.append(bpy.context.object)
    return copies


class _Realizer:

    def __init__(self, z):
        self.z = z

    def realize(self, node):
        type_ = node["type"]
        if type_ == "root":
            parts = []
            for child in node["parts"]:
                part = self.realize(child)
                if isinstance(part, list):
                    parts.extend(part)
                else:
                    parts.append(part)
            return group_under_empty(parts)
        elif type_ == "cycloplane":
            create_cycloplane(
                self.z, node["latitude"], node["longitude"]
            )
            return bpy.context.object
        elif type_ == "rotated_copies":
            first = self.realize(node["operand"])
            return [first] + make_rotated_copies(node["order"])
        elif type_ == "intersection":
            operands = []
            for child in node["operands"]:
                operand = self.realize(child)
                operands.append(operand)
            return do_boolean("INTERSECT", operands)
        elif type_ == "difference":
            operands = []
            for child in node["operands"]:
                operand = self.realize(child)
                operands.append(operand)
            return do_boolean("DIFFERENCE", operands)
        else:
            raise ValueError(f'Invalid node type {type_}')


def realize(node, z):
    realizer = _Realizer(z)
    return realizer.realize(node)


def get_dyadic_twister(n):
    return intersection([
        cycloplane(math.pi / 2, i * 2 * math.pi / n) for i in range(n)
    ])

# Let A and B be two vertices of a regular tetrahedron centered at C.
# This is the angle ACB.
# On https://en.wikipedia.org/wiki/Tetrahedron#Regular_tetrahedron
# this is the "Vertex-Center-Vertex angle."
TETRAHEDRON_LATITUDE = get_3d_angle((1, 1, 1), (0, 0, 0), (1, -1, -1))

def get_tetratwister():
    points = []
    points.append((math.pi, 0))
    for i in range(3):
        points.append((math.pi - TETRAHEDRON_LATITUDE, i * 2 * math.pi / 3))
    return intersection([cycloplane(*point) for point in points])


def get_cubetwister():
    points = []
    points.append((0, 0))
    points.append((math.pi, 0))
    for i in range(4):
        points.append((math.pi / 2, i * math.pi / 2))
    return intersection([cycloplane(*point) for point in points])

# Let A be a vertex of a regular octahedron centered at C and let B be
# the center of an adjacent face. This is the angle ACB.
OCTAHEDRON_LATITUDE = get_3d_angle((1, 0, 0), (0, 0, 0), (1, 1, 1))

def get_octatwister():
    points = []
    for i in range(4):
        points.append((OCTAHEDRON_LATITUDE, i * math.pi / 2))
        points.append((math.pi - OCTAHEDRON_LATITUDE, i * math.pi / 2))
    return intersection([cycloplane(*point) for point in points])

# Let A and B be the centers of two adjacent faces of a regular
# dodecahedron centered at C. This is the angle ACB.
# Equivalently, A and B are two adjacent vertices of a regular
# icosahedron centered at C. We are using the standard definition of
# icosahedron coordinates.
DODECAHEDRON_LATITUDE = get_3d_angle((0, 1, PHI), (0, 0, 0), (0, -1, PHI))

def get_dodecatwister():
    points = []
    points.append((0, 0))
    points.append((math.pi, 0))
    for j in range(5):
        points.append((DODECAHEDRON_LATITUDE, j * 2 * math.pi / 5))
        points.append((math.pi - DODECAHEDRON_LATITUDE, (j + 1 / 2) * 2 * math.pi / 5))
    return intersection([cycloplane(*point) for point in points])


# Let A be the center of a face of a regular dodecahedron centered at C,
# and let B be one of the three closest vertices. This is the angle ACB.
ICOSAHEDRON_LATITUDE_1 = get_3d_angle((1, 1, 1), (0, 0, 0), (0, 1, PHI))

# Same as above, but B is now one of the three second closest vertices
# to A.
ICOSAHEDRON_LATITUDE_2 = get_3d_angle((1, 1, 1), (0, 0, 0), (0, -1, PHI))


def get_icosatwister():
    points = []
    for j in range(5):
        longitude_1 = j * 2 * math.pi / 5
        longitude_2 = (j + 1 / 2) * 2 * math.pi / 5
        points.append((ICOSAHEDRON_LATITUDE_1, longitude_1))
        points.append((ICOSAHEDRON_LATITUDE_2, longitude_1))
        points.append((math.pi - ICOSAHEDRON_LATITUDE_1, longitude_2))
        points.append((math.pi - ICOSAHEDRON_LATITUDE_2, longitude_2))
    return intersection([cycloplane(*point) for point in points])


def create_convex_regular_polytwisters(z, spacing=2.5, translate_z=1):
    platonic_solid_polytwisters = [
        get_tetratwister(),
        get_cubetwister(),
        get_octatwister(),
        get_dodecatwister(),
        get_icosatwister(),
    ]
    dyadic_twisters = [
        get_dyadic_twister(3 + n)
        for n in range(len(platonic_solid_polytwisters))
    ]

    for i, polytwister in enumerate(platonic_solid_polytwisters):
        realize(polytwister, z=z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(value=(i * spacing, 0, translate_z))

    for i, polytwister in enumerate(dyadic_twisters):
        realize(polytwister, z=z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(
            value=(i * spacing, 0, translate_z + spacing)
        )


def get_quasitetratwister():
    south_pole = cycloplane(math.pi, 0)
    others = [
        cycloplane(math.pi - TETRAHEDRON_LATITUDE, i * 2 * math.pi / 3)
        for i in range(3)
    ]

    ring_1 = difference([intersection(others), south_pole])
    ring_2 = rotated_copies(
        difference([
            intersection([south_pole, others[0], others[1]]), others[2]
        ]),
        3
    )

    polytwister = {
        "type": "root",
        "parts": [ring_1, ring_2]
    }

    return polytwister


def get_bloated_tetratwister():
    south_pole = cycloplane(math.pi, 0)
    others = [
        cycloplane(math.pi - TETRAHEDRON_LATITUDE, i * 2 * math.pi / 3)
        for i in range(3)
    ]

    ring_1 = difference([
        intersection([others[0], others[1]]),
        south_pole,
        others[2],
    ])
    ring_2 = difference([
        intersection([south_pole, others[0]]),
        others[1],
        others[2],
    ])

    polytwister = {
        "type": "root",
        "parts": [
            rotated_copies(ring_1, 3),
            rotated_copies(ring_2, 3),
        ]
    }

    return polytwister


def get_quasicubetwister():
    north_pole = cycloplane(0, 0)
    equators = [
        cycloplane(math.pi / 2, i * math.pi / 2)
        for i in range(4)
    ]
    south_pole = cycloplane(math.pi, 0)

    north_ring = difference([
        intersection([north_pole, equators[0], equators[1]]),
        intersection([south_pole, equators[2], equators[3]])
    ])
    
    south_ring = difference([
        intersection([south_pole, equators[0], equators[1]]),
        intersection([north_pole, equators[2], equators[3]])
    ])

    polytwister = {
        "type": "root",
        "parts": [
            rotated_copies(north_ring, 4),
            rotated_copies(south_ring, 4),
        ],
    }

    return polytwister


def get_bloated_cubetwister():
    north_pole = cycloplane(0, 0)
    equators = [
        cycloplane(math.pi / 2, i * math.pi / 2)
        for i in range(4)
    ]
    south_pole = cycloplane(math.pi, 0)

    parts = []

    ring_1 = intersection([north_pole, equators[0]])
    ring_2 = intersection([equators[0], equators[1]])
    ring_3 = intersection([equators[0], south_pole])

    polytwister = {
        "type": "root",
        "parts": [
            rotated_copies(ring_1, 4),
            rotated_copies(ring_2, 4),
            rotated_copies(ring_3, 4),
        ],
    }

    return polytwister


def get_quasioctatwister():
    latitude = get_3d_angle((1, 0, 0), (0, 0, 0), (1, 1, 1))
    north = [cycloplane(latitude, i * math.pi / 2) for i in range(4)]
    south = [cycloplane(math.pi - latitude, i * math.pi / 2) for i in range(4)]

    ring_1 = intersection(north)
    ring_2 = rotated_copies(
        intersection([north[0], north[1], south[0], south[1]]), 4
    )
    ring_3 = intersection(south)

    polytwister = {
        "type": "root",
        "parts": [ring_1, ring_2, ring_3],
    }

    return polytwister


def get_bloated_octatwister():
    latitude = get_3d_angle((1, 0, 0), (0, 0, 0), (1, 1, 1))
    north = [cycloplane(latitude, i * math.pi / 2) for i in range(4)]
    south = [cycloplane(math.pi - latitude, i * math.pi / 2) for i in range(4)]

    ring_1 = intersection([north[0], north[1]])
    ring_2 = intersection([north[0], south[0]])
    ring_3 = intersection([south[0], south[1]])

    polytwister = {
        "type": "root",
        "parts": [
            rotated_copies(ring_1, 4),
            rotated_copies(ring_2, 4),
            rotated_copies(ring_3, 4),
        ],
    }

    return polytwister


if __name__ == "__main__":
    # Delete the default cube.
    bpy.ops.object.delete(use_global=False)

    spacing = 5.0

    z = 0.14

    create_convex_regular_polytwisters(z)

    polytwisters = [
        get_quasitetratwister(),
        get_bloated_tetratwister(),
        get_quasicubetwister(),
        get_bloated_cubetwister(),
        get_quasioctatwister(),
        get_bloated_octatwister(),
    ]

    for i, polytwister in enumerate(polytwisters):
        realize(polytwister, z=z)
        rotate_about_axis("X", math.pi / 2)
        bpy.ops.transform.translate(
            value=(i * spacing, 0, -spacing)
        )
