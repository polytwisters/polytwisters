import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize


def get_cycloplane_error(point, cycloplane_spec):
    radius = np.linalg.norm(cycloplane_spec)
    x, y, z = np.array(cycloplane_spec) / radius
    if x == -1:
        a, b, c, d = 0, 0, 0, -1
    else:
        temp = 1 / np.sqrt(2 * (1 + x))
        a, b, c, d = (1 + x) * temp, 0, -z * temp, y * temp

    matrix = np.array([
        [a, -b, -c, -d],
        [b, a, -d, c],
        [c, d, a, -b],
        [d, -c, b, a],
    ])

    x, y, z, w = matrix @ point
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
        "radii": np.array(radii),
        "points": np.array(points),
    }


def main():
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ]
    result = find_cycloplanes_intersection(cycloplane_specs, rng)
    radii = result["radii"]
    midrange = (np.max(radii) + np.min(radii)) / 2
    radii_large = radii[radii > midrange]
    radii_small = radii[radii < midrange]

    print(np.median(radii_large))
    print(np.median(radii_small))


if __name__ == "__main__":
    main()