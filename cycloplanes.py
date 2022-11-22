import random

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize




def rotate_2d(x, y, theta):
    return (
        x * np.cos(theta) - y * np.sin(theta),
        x * np.sin(theta) + y * np.cos(theta)
    )


def rotate_hopf_inverse(x, y, z, w, theta, phi):
    x, y = rotate_2d(x, y, -phi)
    z, w = rotate_2d(z, w, -phi)
    w, x = rotate_2d(w, x, -theta)
    y, z = rotate_2d(y, z, -theta)
    return x, y, z, w


def get_cycloplane_error(point, spec):
    radius, zenith, azimuth = spec
    x, y, z, w = point / radius
    theta = zenith / 2
    phi = azimuth / 2
    # Inverse transformation.
    x, y, z, w = rotate_hopf_inverse(x, y, z, w, theta, phi)
    signed_distance = np.hypot(x, y) - radius
    return signed_distance * signed_distance


def get_summed_cycloplane_error(point, cycloplane_specs):
    return sum([
        get_cycloplane_error(point, spec)
        for spec in cycloplane_specs
    ])


def find_minimum(start, cycloplane_specs):
    temp = scipy.optimize.minimize(
        lambda x: get_summed_cycloplane_error(x, cycloplane_specs),
        start
    )
    if not temp.success:
        raise RuntimeError(f"Convergence failed: {temp.message}")
    return temp.x


def find_cycloplanes_intersection(cycloplane_specs, rng, count=1000):
    points = []
    radii = []
    for i in range(count):
        point = rng.uniform(-1, 1, size=(4,)) * 3
        minimum = find_minimum(point, cycloplane_specs)
        error = get_summed_cycloplane_error(minimum, cycloplane_specs)
        if error > 1e-3:
            raise ValueError(f"Convergence to local minimum that is not 0: {error}.")
        radius = np.sqrt(np.sum(np.square(minimum)))
        radii.append(radius)
        points.append(minimum)
    return {
        "points": np.array(points),
        "radius": np.mean(radii),
        "standard_deviation": np.std(radius),
    }


def get_hopf_fiber_cost(points, cycloplane_spec):
    result = 0.0
    for i in range(points.shape[0]):
        result += get_cycloplane_error(points[i, :], cycloplane_spec)
    return result


def fit_hopf_fiber_to_points(points, radius):
    increments = 10
    start = None
    for i in range(1, increments):
        for j in range(increments):
            zenith = np.pi * i / increments
            azimuth = 2 * np.pi * i / increments
            cost = get_hopf_fiber_cost(points, (radius, zenith, azimuth))
    raise ValueError
    return scipy.optimize.minimize(
        lambda x: get_hopf_fiber_cost(points, (radius, x[0], x[1])),
        start,
    )

def main():
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, np.pi / 2, 0.0),
        (1.0, np.pi / 2, np.pi / 2),
    ]
    result = find_cycloplanes_intersection(cycloplane_specs, rng)
    radius = result["radius"]
    print(f"Standard deviation: {result['standard_deviation']}")

    points = result["points"]

    X, Y, Z, W = points[:, 0], points[:, 1], points[:, 2], points[:, 3]
    plt.gca().set_aspect("equal")
    plt.scatter(X, Y, 1)
    plt.show()

    plt.gca().set_aspect("equal")
    plt.scatter(X, Z, 1)
    plt.show()

    plt.gca().set_aspect("equal")
    plt.scatter(X, W, 1)
    plt.show()

    """
    temp = fit_hopf_fiber_to_points(points, radius)
    zenith, azimuth = temp.x
    print(f"Success = {temp.success}")
    print(f"Message = {temp.message}")
    print(f"Cost = {temp.fun}")
    print(f"Radius = {radius}")
    print(f"Zenith = {np.degrees(zenith)}")
    print(f"Azimuth = {np.degrees(azimuth)}")
    """


if __name__ == "__main__":
    main()