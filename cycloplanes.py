import random

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize


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


def main():
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, np.pi / 2, 0.0),
        (1.0, np.pi / 2, np.pi / 2),
    ]
    count = 1000
    points = np.zeros((count, 4))
    radii = np.zeros(count)
    for i in range(count):
        point = [(random.random() * 2 - 1) * 3 for i in range(4)]
        minimum = find_minimum(point, cycloplane_specs)
        error = get_summed_cycloplane_error(minimum, cycloplane_specs)
        radius = np.sqrt(np.sum(np.square(minimum)))
        radii[i] = radius
        points[i, :] = minimum
    average_radius = np.mean(radii)
    print(f"Average radius = {average_radius:.5}")
    standard_deviation = np.std(radii)
    print(f"Standard deviation of radii = {standard_deviation:.5}")

    plt.scatter(points[:, 0], points[:, 1], 1)
    plt.show()
    plt.scatter(points[:, 2], points[:, 3], 1)
    plt.show()


if __name__ == "__main__":
    main()