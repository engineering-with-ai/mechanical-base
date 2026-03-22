import pytest

from sim.constants import (
    BEAM_HEIGHT,
    BEAM_LENGTH,
    POINT_LOAD,
    SECOND_MOMENT,
    YOUNGS_MODULUS,
    ureg,
)
from sim.model import solve


def _expected_deflection_mm() -> float:
    """Euler-Bernoulli: delta = P*L^3 / (3*E*I)."""
    p = POINT_LOAD.to(ureg.N).magnitude
    l = BEAM_LENGTH.to(ureg.mm).magnitude
    e = YOUNGS_MODULUS.magnitude.nominal_value * 1e3  # GPa -> MPa for mm units
    i = SECOND_MOMENT.magnitude
    return p * l**3 / (3 * e * i)


def _expected_stress_mpa() -> float:
    """Bending stress: sigma = P*L*c / I."""
    p = POINT_LOAD.to(ureg.N).magnitude
    l = BEAM_LENGTH.to(ureg.mm).magnitude
    c = BEAM_HEIGHT.to(ureg.mm).magnitude / 2
    i = SECOND_MOMENT.magnitude
    return p * l * c / i


class TestCantileverBeam:
    """Assertions against theory.ipynb expected values."""

    def test_tip_deflection(self) -> None:
        """FEM tip deflection matches Euler-Bernoulli within 5%."""
        # arrange
        expected_mm = _expected_deflection_mm()

        # act
        max_deflection_mm, _ = solve()

        # assert
        assert max_deflection_mm == pytest.approx(expected_mm, rel=0.05)

    def test_max_bending_stress(self) -> None:
        """FEM max stress matches analytical M*c/I within 10%."""
        # arrange
        expected_mpa = _expected_stress_mpa()

        # act
        _, max_stress_mpa = solve()

        # assert
        assert max_stress_mpa == pytest.approx(expected_mpa, rel=0.10)
