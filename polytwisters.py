import math

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

# Let A and B be two vertices of a regular tetrahedron centered at C.
# This is the angle ACB.
# On https://en.wikipedia.org/wiki/Tetrahedron#Regular_tetrahedron
# this is the "Vertex-Center-Vertex angle."
TETRAHEDRON_LATITUDE = get_3d_angle((1, 1, 1), (0, 0, 0), (1, -1, -1))

# Let A be a vertex of a regular octahedron centered at C and let B be
# the center of an adjacent face. This is the angle ACB.
OCTAHEDRON_LATITUDE = get_3d_angle((1, 0, 0), (0, 0, 0), (1, 1, 1))

# Let A and B be the centers of two adjacent faces of a regular
# dodecahedron centered at C. This is the angle ACB.
# Equivalently, A and B are two adjacent vertices of a regular
# icosahedron centered at C. We are using the standard definition of
# icosahedron coordinates.
DODECAHEDRON_LATITUDE = get_3d_angle((0, 1, PHI), (0, 0, 0), (0, -1, PHI))

# Let A be the center of a face of a regular icosahedron centered at C,
# and let B be one of the three closest vertices. This is the angle ACB.
ICOSAHEDRON_LATITUDE_1 = get_3d_angle((1, 1, 1), (0, 0, 0), (0, 1, PHI))

# Same as above, but B is now one of the three second closest vertices
# to A.
ICOSAHEDRON_LATITUDE_2 = get_3d_angle((1, 1, 1), (0, 0, 0), (0, -1, PHI))


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


def get_dyadic_twister(n):
    return intersection([
        cycloplane(math.pi / 2, i * 2 * math.pi / n) for i in range(n)
    ])


NORTH_POLE = cycloplane(0, 0)
SOUTH_POLE = cycloplane(math.pi, 0)


TETRAHEDRON_NORTH = []
for i in range(3):
    TETRAHEDRON_NORTH.append(
        cycloplane(math.pi - TETRAHEDRON_LATITUDE, i * 2 * math.pi / 3)
    )

CUBE_EQUATOR = []
for i in range(4):
    CUBE_EQUATOR.append(cycloplane(math.pi / 2, i * math.pi / 2))


OCTAHEDRON_NORTH = []
OCTAHEDRON_SOUTH = []
for i in range(4):
    OCTAHEDRON_NORTH.append(
        cycloplane(OCTAHEDRON_LATITUDE, i * math.pi / 2)
    )
    OCTAHEDRON_SOUTH.append(
        cycloplane(math.pi - OCTAHEDRON_LATITUDE, i * math.pi / 2)
    )


DODECAHEDRON_NORTH = []
DODECAHEDRON_SOUTH = []
for i in range(5):
    DODECAHEDRON_NORTH.append(
        cycloplane(DODECAHEDRON_LATITUDE, i * 2 * math.pi / 5)
    )
    DODECAHEDRON_SOUTH.append(
        cycloplane(math.pi - DODECAHEDRON_LATITUDE, (i + 1 / 2) * 2 * math.pi / 5)
    )

ICOSAHEDRON_NORTH_1 = []
ICOSAHEDRON_NORTH_2 = []
ICOSAHEDRON_SOUTH_1 = []
ICOSAHEDRON_SOUTH_2 = []
for i in range(5):
    longitude_1 = i * 2 * math.pi / 5
    longitude_2 = (i + 1 / 2) * 2 * math.pi / 5
    ICOSAHEDRON_NORTH_1.append(
        cycloplane(ICOSAHEDRON_LATITUDE_1, longitude_1)
    )
    ICOSAHEDRON_NORTH_2.append(
        cycloplane(ICOSAHEDRON_LATITUDE_2, longitude_1)
    )
    ICOSAHEDRON_SOUTH_1.append(
        cycloplane(math.pi - ICOSAHEDRON_LATITUDE_1, longitude_2)
    )
    ICOSAHEDRON_SOUTH_2.append(
        cycloplane(math.pi - ICOSAHEDRON_LATITUDE_2, longitude_2)
    )

def get_tetratwister():
    cycloplanes = [SOUTH_POLE] + TETRAHEDRON_NORTH
    return intersection(cycloplanes)


def get_cubetwister():
    cycloplanes = [NORTH_POLE, SOUTH_POLE] + CUBE_EQUATOR
    return intersection(cycloplanes)


def get_octatwister():
    cycloplanes = OCTAHEDRON_NORTH + OCTAHEDRON_SOUTH
    return intersection(cycloplanes)


def get_dodecatwister():
    cycloplanes = [NORTH_POLE, SOUTH_POLE] + DODECAHEDRON_NORTH + DODECAHEDRON_SOUTH
    return intersection(cycloplanes)


def get_icosatwister():
    cycloplanes = (
        ICOSAHEDRON_NORTH_1
        + ICOSAHEDRON_NORTH_2
        + ICOSAHEDRON_SOUTH_1
        + ICOSAHEDRON_SOUTH_2
    )
    return intersection(cycloplanes)


def get_quasitetratwister():
    others = TETRAHEDRON_NORTH

    ring_1 = difference([intersection(others), SOUTH_POLE])
    ring_2 = rotated_copies(
        difference([
            intersection([SOUTH_POLE, others[0], others[1]]), others[2]
        ]),
        3
    )

    polytwister = {
        "type": "root",
        "parts": [ring_1, ring_2]
    }

    return polytwister


def get_bloated_tetratwister():
    others = TETRAHEDRON_NORTH

    ring_1 = difference([
        intersection([others[0], others[1]]),
        SOUTH_POLE,
        others[2],
    ])
    ring_2 = difference([
        intersection([SOUTH_POLE, others[0]]),
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
    equators = CUBE_EQUATOR

    north_ring = difference([
        intersection([NORTH_POLE, equators[0], equators[1]]),
        intersection([SOUTH_POLE, equators[2], equators[3]])
    ])
    
    south_ring = difference([
        intersection([SOUTH_POLE, equators[0], equators[1]]),
        intersection([NORTH_POLE, equators[2], equators[3]])
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
    equators = CUBE_EQUATOR

    ring_1 = intersection([NORTH_POLE, equators[0]])
    ring_2 = intersection([equators[0], equators[1]])
    ring_3 = intersection([equators[0], SOUTH_POLE])

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
    north = OCTAHEDRON_NORTH
    south = OCTAHEDRON_SOUTH

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
    north = OCTAHEDRON_NORTH
    south = OCTAHEDRON_SOUTH

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


def get_quasidodecatwister():
    north = DODECAHEDRON_NORTH
    south = DODECAHEDRON_SOUTH

    ring_1 = intersection([NORTH_POLE, north[0], north[1]])
    ring_2 = intersection([north[0], north[1], south[0]])
    ring_3 = intersection([north[1], south[0], south[1]])
    ring_4 = intersection([SOUTH_POLE, south[0], south[1]])

    polytwister = {
        "type": "root",
        "parts": [
            rotated_copies(ring_1, 5),
            rotated_copies(ring_2, 5),
            rotated_copies(ring_3, 5),
            rotated_copies(ring_4, 5),
        ],
    }

    return polytwister
