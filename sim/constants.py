"""Physical parameters for L-bracket bolted connection analysis.

L-bracket bolted to a wall plate with 2x M8 bolts. 500N vertical load
at the free end of the horizontal leg.
"""

from typing import Final

import numpy as np
import pint
from uncertainties import ufloat

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# --- Bracket geometry ---
# Reason: typical small steel mounting bracket, vertical leg bolted to wall
VERTICAL_LEG_HEIGHT: Final = 80.0 * ureg.mm
HORIZONTAL_LEG_LENGTH: Final = 60.0 * ureg.mm
BRACKET_WIDTH: Final = 50.0 * ureg.mm
BRACKET_THICKNESS: Final = 14.0 * ureg.mm
FILLET_RADIUS: Final = 8.0 * ureg.mm

# --- Bolt holes ---
# Reason: M8 clearance hole per ISO 273, 2 bolts symmetric about bracket centerline
BOLT_DIAMETER: Final = 8.0 * ureg.mm  # M8 nominal
HOLE_DIAMETER: Final = 8.5 * ureg.mm  # M8 clearance, ISO 273
BOLT_SPACING: Final = 50.0 * ureg.mm  # center-to-center vertical distance
NUM_BOLTS: Final = 2

# --- Material: Nylon PA12 (HP Multi Jet Fusion) ---
# Reason: most common structural 3D print material for functional parts.
# Source: HP 3D High Reusability PA 12 datasheet (4AA8-2745ENW)
YOUNGS_MODULUS: Final = ufloat(1.7, 0.1) * ureg.GPa  # 1700 MPa XY, 1800 Z
POISSONS_RATIO: Final = 0.4 * ureg.dimensionless  # typical for nylon
YIELD_STRESS: Final = 48.0 * ureg.MPa  # tensile strength (no sharp yield point)

# --- Loading ---
APPLIED_LOAD: Final = 500.0 * ureg.N  # vertical, downward at free end

# --- Derived: bolt group analysis ---
# Reason: eccentricity = horizontal leg length + half thickness (load line to bolt group centroid)
ECCENTRICITY: Final = (HORIZONTAL_LEG_LENGTH + BRACKET_THICKNESS / 2).to(ureg.mm)
BOLT_GROUP_RADIUS: Final = (BOLT_SPACING / 2).to(ureg.mm)

# Direct shear per bolt: V/n
DIRECT_SHEAR_PER_BOLT: Final = (APPLIED_LOAD / NUM_BOLTS).to(ureg.N)

# Moment-induced shear per bolt: V*e / (n*r)
# Reason: moment = V*e, divided equally among n bolts at radius r from centroid
MOMENT_SHEAR_PER_BOLT: Final = (
    APPLIED_LOAD * ECCENTRICITY / (NUM_BOLTS * BOLT_GROUP_RADIUS)
).to(ureg.N)

# Critical bolt resultant (direct + moment shears are collinear for top bolt)
CRITICAL_BOLT_FORCE: Final = (
    np.sqrt(DIRECT_SHEAR_PER_BOLT.magnitude**2 + MOMENT_SHEAR_PER_BOLT.magnitude**2)
    * ureg.N
)
