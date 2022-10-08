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


# Let A be the center of a face of a regular icosahedron centered at C,
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
