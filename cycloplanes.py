import math
import random

import matplotlib.pyplot as plt


def rotate_2d(x, y, theta):
    return (
        x * math.cos(theta) - y * math.sin(theta),
        x * math.sin(theta) + y * math.cos(theta)
    )


def get_cycloplane_error(point, latitude, longitude, radius=1.0):
    x, y, z, w = point
    theta = latitude / 2
    phi = longitude
    x, y = rotate_2d(x, y, -phi)
    z, w = rotate_2d(z, w, -phi)
    x, w = rotate_2d(x, w, -theta)
    y, z = rotate_2d(y, z, -theta)
    signed_distance = math.hypot(x, y) - radius
    return signed_distance * signed_distance


def get_summed_cycloplane_error(point, cycloplane_specs):
    return sum([
        get_cycloplane_error(point, latitude, longitude)
        for latitude, longitude in cycloplane_specs
    ])


def find_minimum(start, cycloplane_specs, step=0.001):
    point = list(start)
    best_error = math.inf
    while best_error > 0.05:
        new_points = []
        for i in range(len(point)):
            new_point_1 = point[:]
            new_point_1[i] += step
            new_points.append(new_point_1)
            new_point_2 = point[:]
            new_point_2[i] -= step
            new_points.append(new_point_2)
        for new_point in new_points:
            error = get_summed_cycloplane_error(new_point, cycloplane_specs)
            if error < best_error:
                point = new_point
                best_error = error
    return point


def main():
    cycloplane_specs = [
        (0.0, 0.0),
        (math.pi / 2, 0.0),
        (math.pi / 2, math.pi / 2),
    ]
    X = []
    Y = []
    radii = []
    for i in range(100):
        point = [(random.random() * 2 - 1) * 3 for i in range(4)]
        minimum = find_minimum(point, cycloplane_specs)
        error = get_summed_cycloplane_error(minimum, cycloplane_specs)
        X.append(minimum[0])
        Y.append(minimum[1])
        radius = math.hypot(*minimum)
        radii.append(radius)
        print(minimum)
        print(f"Radius = {radius:.5f}, error = {error:.5f}")
    average_radius = sum(radii) / len(radii)
    print(f"Average radius = {average_radius:.5f}")

    plt.scatter(X, Y, 1)
    plt.show()


if __name__ == "__main__":
    main()