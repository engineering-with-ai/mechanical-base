"""CalculiX FEM solver for cantilever beam.

Reads gmsh-generated mesh, adds BCs/material/loading, runs ccx, parses results.
"""

import subprocess
from pathlib import Path

from sim.constants import BEAM_LENGTH, POINT_LOAD, YOUNGS_MODULUS, POISSONS_RATIO, ureg
from sim.inp_writer import write_ccx_inp
from sim.frd_parser import parse_frd
from sim.result import FemResult

RESULTS_DIR = Path("sim/results")
MESH_INP = RESULTS_DIR / "cantilever_beam.inp"
CCX_INP = RESULTS_DIR / "ccx_cantilever"
CCX_INP_FILE = RESULTS_DIR / "ccx_cantilever.inp"


def solve() -> FemResult:
    """Run CalculiX FEM solve and extract results.

    Returns:
        FemResult with max deflection and stress from FEM
    """
    # Reason: gmsh exports nodes+elements only; we need full CalculiX input deck
    write_ccx_inp(
        mesh_inp=MESH_INP,
        output_inp=CCX_INP_FILE,
        youngs_mpa=YOUNGS_MODULUS.magnitude.nominal_value * 1e3,
        poissons=POISSONS_RATIO.magnitude,
        load_n=POINT_LOAD.to(ureg.N).magnitude,
        fixed_x=-BEAM_LENGTH.to(ureg.mm).magnitude / 2,
        loaded_x=BEAM_LENGTH.to(ureg.mm).magnitude / 2,
    )

    # Reason: ccx expects input name without .inp extension
    subprocess.run(
        ["ccx", "-i", str(CCX_INP)],
        check=True,
        capture_output=True,
        text=True,
    )

    return parse_frd(RESULTS_DIR / "ccx_cantilever.frd")
