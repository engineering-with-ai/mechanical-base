"""Parametric cantilever beam geometry via CadQuery.

Generates a rectangular beam and exports to STEP for downstream meshing.
"""

import cadquery as cq

from sim.constants import BEAM_HEIGHT, BEAM_LENGTH, BEAM_WIDTH, ureg

STEP_PATH = "cad/cantilever_beam.step"


def build_beam() -> cq.Workplane:
    """Build rectangular cantilever beam.

    Returns:
        CadQuery Workplane with beam solid
    """
    l = BEAM_LENGTH.to(ureg.mm).magnitude
    w = BEAM_WIDTH.to(ureg.mm).magnitude
    h = BEAM_HEIGHT.to(ureg.mm).magnitude

    return cq.Workplane("XY").box(l, w, h)


if __name__ == "__main__":
    beam = build_beam()
    beam.export(STEP_PATH)
    print(f"Exported beam to {STEP_PATH}")
