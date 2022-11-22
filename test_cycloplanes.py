import numpy as np
import pytest

import cycloplanes
import polytwisters

STANDARD_DEVIATION_EPSILON = 1e-4
RADIUS_EPSILON = 1e-4


@pytest.mark.skip
@pytest.mark.parametrize("seed", range(10))
def test_random_unit_cycloplane(seed):
    """Three randomly selected unit cycloplanes constructed from Hopf fibers have boundaries
    that intersect in two circles. The chance of this not being true is extremely small."""
    rng = np.random.default_rng(seed)
    cycloplane_specs = [
        (1.0, rng.uniform(0, np.pi), rng.uniform(0, 2 * np.pi))
        for i in range(3)
    ]
    result = cycloplanes.find_cycloplanes_intersection(cycloplane_specs, rng)
    assert result["standard_deviation"] < STANDARD_DEVIATION_EPSILON


def test_cube():
    """Three faces of a cube intersect in a single circle whose radius is sqrt(2)."""
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, np.pi / 2, 0.0),
        (1.0, np.pi / 2, np.pi / 2),
    ]
    result = cycloplanes.find_cycloplanes_intersection(cycloplane_specs, rng)
    assert result["standard_deviation"] < STANDARD_DEVIATION_EPSILON


def test_tetrahedron():
    """Three faces of a tetrahedron intersect in two circles."""
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, np.pi - polytwisters.TETRAHEDRON_ZENITH, 0.0),
        (1.0, np.pi - polytwisters.TETRAHEDRON_ZENITH, 2 * np.pi / 3),
    ]
    result = cycloplanes.find_cycloplanes_intersection(cycloplane_specs, rng)
    assert result["standard_deviation"] < STANDARD_DEVIATION_EPSILON


def test_octahedron():
    """Three vertex-adjacent faces of an octahedron intersect in a single circle of radius
    sqrt(2)."""
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, polytwisters.OCTAHEDRON_ZENITH, 0.0),
        (1.0, polytwisters.OCTAHEDRON_ZENITH, np.pi / 2),
        (1.0, np.pi / 2 - polytwisters.OCTAHEDRON_ZENITH, np.pi / 2),
    ]
    result = cycloplanes.find_cycloplanes_intersection(cycloplane_specs, rng)
    assert result["standard_deviation"] < STANDARD_DEVIATION_EPSILON


def test_dodecatwister():
    """Three vertex-adjacent faces of a dodecahedron intersect in two circles."""
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, polytwisters.DODECAHEDRON_ZENITH, 0.0),
        (1.0, polytwisters.DODECAHEDRON_ZENITH, 2 * np.pi / 5),
    ]
    result = cycloplanes.find_cycloplanes_intersection(cycloplane_specs, rng)
    assert result["standard_deviation"] < STANDARD_DEVIATION_EPSILON


def test_icosatwister():
    """Three vertex-adjacent faces of an icosahedron intersect in two circles."""
    rng = np.random.default_rng(0)
    cycloplane_specs = [
        (1.0, 0.0, 0.0),
        (1.0, polytwisters.ICOSAHEDRON_ZENITH_1, 0.0),
        (1.0, polytwisters.ICOSAHEDRON_ZENITH_1, 2 * np.pi / 5),
    ]
    result = cycloplanes.find_cycloplanes_intersection(cycloplane_specs, rng)
    assert result["standard_deviation"] < STANDARD_DEVIATION_EPSILON
