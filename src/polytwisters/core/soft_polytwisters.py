import numpy as np


PHI = (1 + np.sqrt(5)) / 2


TETRAHEDRON_VERTICES = [
    (1, 1, 1),
    (-1, -1, 1),
    (1, -1, -1),
    (-1, 1, -1),
]


CUBE_VERTICES = [
    (1, 1, 1),
    (1, 1, -1),
    (1, -1, 1),
    (1, -1, -1),
    (-1, 1, 1),
    (-1, 1, -1),
    (-1, -1, 1),
    (-1, -1, -1),
]


OCTAHEDRON_VERTICES = [
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
]


PHI1 = PHI + 1
DODECAHEDRON_VERTICES = CUBE_VERTICES + [
    (0, 1, PHI1),
    (0, 1, -PHI1),
    (0, -1, PHI1),
    (0, -1, -PHI1),
    (1, PHI1, 0),
    (1, -PHI1, 0),
    (-1, PHI1, 0),
    (-1, -PHI1, 0),
    (PHI1, 0, 1),
    (PHI1, 0, -1),
    (-PHI1, 0, 1),
    (-PHI1, 0, -1),
]
DODECAHEDRON_FACE_CENTER = np.mean(
    np.array([
        (0, 1, PHI1),
        (0, -1, PHI1),
        (1, 1, 1),
        (1, -1, 1),
        (PHI1, 0, 1),
    ]),
    axis=0,
)


ICOSAHEDRON_VERTICES = [
    (0, 1, PHI),
    (0, 1, -PHI),
    (0, -1, PHI),
    (0, -1, -PHI),
    (1, PHI, 0),
    (1, -PHI, 0),
    (-1, PHI, 0),
    (-1, -PHI, 0),
    (PHI, 0, 1),
    (PHI, 0, -1),
    (-PHI, 0, 1),
    (-PHI, 0, -1),
]


def normalize_points(points):
    result = np.array(points, dtype="float32")
    result /= np.linalg.norm(result, axis=1)[:, np.newaxis]
    return result


def orient_along_x_axis(reference_point, points):
    x_axis = np.array([1.0, 0.0, 0.0])
    normalized_point = np.array(reference_point) / np.linalg.norm(reference_point)
    axis = np.cross(normalized_point, x_axis)
    axis /= np.linalg.norm(axis)
    cos_angle = np.dot(normalized_point, x_axis)
    sin_angle = np.sqrt(1 - cos_angle * cos_angle)

    x, y, z = axis
    cross_matrix = np.array([
        [0, -z, y],
        [z, 0, -x],
        [-y, x, 0]
    ])

    # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
    matrix = (
        np.eye(3)
        + sin_angle * cross_matrix
        + (1 - cos_angle) * (cross_matrix @ cross_matrix)
    )

    return (matrix @ points.T).T


def get_soft_tetratwister():
    points = normalize_points(TETRAHEDRON_VERTICES)
    return {
        "names": ["soft tetratwister"],
        "points": orient_along_x_axis(points[0], points),
    }


def get_soft_cubetwister():
    return {
        "names": ["soft cubetwister"],
        "points": normalize_points(CUBE_VERTICES),
    }


def get_soft_octatwister():
    return {
        "names": ["soft octatwister"],
        "points": normalize_points(OCTAHEDRON_VERTICES),
    }


def get_soft_dodecatwister():
    points = normalize_points(DODECAHEDRON_VERTICES)
    return {
        "names": ["soft dodecatwister"],
        "points": orient_along_x_axis(DODECAHEDRON_FACE_CENTER, points),
    }


def get_soft_icosatwister():
    points = normalize_points(ICOSAHEDRON_VERTICES)
    return {
        "names": ["soft icosatwister"],
        "points": orient_along_x_axis(points[0], points),
    }


def get_soft_dyadic_twister(n, special_names=None):
    names = [f"order-{n} soft dyadic twister"]
    if special_names is not None:
        names = special_names + names
    return {
        "names": names,
        "points": [
            (0, np.cos(2 * np.pi * i / n), np.sin(2 * np.pi * i / n))
            for i in range(n)
        ]
    }


def get_all_soft_polytwisters():
    polytwisters_list = [
        get_soft_dyadic_twister(2, ["duospindle"]),
        get_soft_dyadic_twister(3),
        get_soft_dyadic_twister(4),
        get_soft_dyadic_twister(5),
        get_soft_tetratwister(),
        get_soft_cubetwister(),
        get_soft_octatwister(),
        get_soft_dodecatwister(),
        get_soft_icosatwister(),
    ]
    result = {}
    for polytwister in polytwisters_list:
        polytwister["type"] = "soft"
        name = polytwister["names"][0]
        polytwister["name"] = name
        result[name] = polytwister
    return result
