import random

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize

import polytwisters


def rotate_2d(x, y, theta):
    return (
        x * np.cos(theta) - y * np.sin(theta),
        x * np.sin(theta) + y * np.cos(theta)
    )


def get_cycloplane_error(point, spec):
    radius, zenith, azimuth = spec
    x, y, z, w = point / radius
    theta = zenith / 2
    phi = azimuth
    x, y = rotate_2d(x, y, -phi)
    z, w = rotate_2d(z, w, -phi)
    x, w = rotate_2d(x, w, -theta)
    y, z = rotate_2d(y, z, -theta)
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
    return temp.x


def find_cycloplanes_intersection(cycloplane_specs, rng, count=1000):
    points = np.zeros((count, 4))
    radii = np.zeros(count)
    for i in range(count):
        point = rng.uniform(-3.0, 3.0, size=(4,))
        minimum = find_minimum(point, cycloplane_specs)
        radius = np.sqrt(np.sum(np.square(minimum)))
        radii[i] = radius
        points[i, :] = minimum
    midpoint = (np.max(radii) + np.min(radii)) / 2
    lower = radii[radii < midpoint]
    upper = radii[radii >= midpoint]
    if np.std(lower) < 1e-4 and np.std(upper) < 1e-4:
        radii = [np.mean(lower), np.mean(upper)]
        standard_deviations = [np.std(lower), np.std(upper)]
    else:
        radii = [np.mean(radii)]
        standard_deviations = [np.std(radii)]
    return {
        "points": points,
        "radii": radii,
        "standard_deviations": standard_deviations,
    }

def main():
    rng = np.random.default_rng(0)
    """
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, np.pi / 2, 0.0),
        (1.0, np.pi / 2, np.pi / 2),
    ]
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, 0.5 * np.pi / 2, 0.0),
        (1.0, 0.5 * np.pi / 2, 0.5 * np.pi / 2),
    ]
    cycloplane_specs = [
        (1.0, polytwisters.OCTAHEDRON_ZENITH, 0.0),
        (1.0, polytwisters.OCTAHEDRON_ZENITH, 0.0),
        (1.0, np.pi - polytwisters.OCTAHEDRON_ZENITH, np.pi / 2),
    ]
    zenith = 0.5 * np.pi * 0.5
    cycloplane_specs = [
        (1.0, zenith, 0.0),
        (1.0, zenith, 2 * np.pi * (1 / 3)),
        (1.0, zenith, 2 * np.pi * (2 / 3)),
    ]
    """
    for i in range(10):
        cycloplane_specs = [
            (1.0, rng.uniform(0, np.pi), rng.uniform(0, 2 * np.pi))
            for i in range(3)
        ]
        result = find_cycloplanes_intersection(cycloplane_specs, rng)
        radii = result["radii"]
        standard_deviations = result["standard_deviations"]
        for i in range(len(radii)):
            print(f"Radius = {radii[i]:.5}, standard deviation = {standard_deviations[i]:.5}")
        if any([x > 1e-4 for x in standard_deviations]):
            print(f"Verdict: not a circle")
        else:
            print(f"Verdict: may be a circle")
        points = result["points"]
        X, Y, Z, W = points[:, 0], points[:, 1], points[:, 2], points[:, 3]

    plt.gca().set_aspect("equal")
    plt.scatter(X, Y, 1)
    plt.show()

    plt.gca().set_aspect("equal")
    plt.scatter(Z, W, 1)
    plt.show()

    plt.gca().set_aspect("equal")
    plt.scatter(X, Z, 1)
    plt.show()


if __name__ == "__main__":
    main()