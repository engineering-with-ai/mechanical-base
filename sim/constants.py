from typing import Final

import pint
from uncertainties import ufloat

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# --- Beam geometry ---
# Reason: rectangular cross-section, dimensions typical of a small steel test coupon
BEAM_LENGTH: Final = 200.0 * ureg.mm
BEAM_WIDTH: Final = 20.0 * ureg.mm
BEAM_HEIGHT: Final = 10.0 * ureg.mm

# --- Material: structural steel (ASTM A36) ---
# Reason: most common structural steel, well-characterized properties
YOUNGS_MODULUS: Final = ufloat(200.0, 4.0) * ureg.GPa  # 200 GPa +/-2%, ASTM A36 typical
POISSONS_RATIO: Final = 0.3 * ureg.dimensionless  # ASTM A36, Roark's 8th ed. Table A.5

# --- Loading ---
POINT_LOAD: Final = 100.0 * ureg.N  # applied at free end, downward

# --- Derived: second moment of area ---
# I = b*h^3 / 12 for rectangular cross-section
SECOND_MOMENT: Final = (BEAM_WIDTH * BEAM_HEIGHT**3 / 12).to(ureg.mm**4)

# --- Analytical expected values (Euler-Bernoulli) ---
# delta_max = P*L^3 / (3*E*I) at free end
# sigma_max = M*c / I = P*L * (h/2) / I at fixed end
