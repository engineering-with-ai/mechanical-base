"""CalculiX FEM solver for cantilever beam via pygccx.

Meshes CadQuery STEP geometry, applies BCs/material/loading, solves, and
extracts tip deflection and max von Mises stress.
"""

import os
from pathlib import Path

from pygccx import model as ccx_model
from pygccx import model_keywords as mk
from pygccx import step_keywords as sk
from pygccx import enums
from pygccx.tools import stress_tools as st

from cad.model import STEP_PATH
from sim.constants import (
    BEAM_LENGTH,
    POINT_LOAD,
    POISSONS_RATIO,
    YOUNGS_MODULUS,
    ureg,
)

RESULTS_DIR = Path("sim/results")
MESH_SIZE = 1.0  # mm — fine mesh for bending accuracy with linear tets
# Reason: ccx is on PATH, cgx not needed for headless solve
CCX_PATH = "ccx"
CGX_PATH = "cgx"


def solve() -> tuple[float, float]:
    """Run FEM solve and return (max_deflection_mm, max_stress_mpa)."""

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    wkd = str(RESULTS_DIR.resolve())

    with ccx_model.Model(CCX_PATH, CGX_PATH, jobname="cantilever", working_dir=wkd) as model:
        # Mesh the STEP geometry
        gmsh = model.get_gmsh()
        gmsh.model.occ.importShapes(os.path.abspath(STEP_PATH))
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_SIZE)
        gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_SIZE)
        gmsh.model.mesh.generate(3)

        # Reason: physical groups define node/element sets for BCs and material
        gmsh.model.add_physical_group(3, [1], name="BEAM")
        _add_face_groups(gmsh)
        gmsh.model.occ.synchronize()

        model.update_mesh_from_gmsh()
        mesh = model.mesh

        # Material
        e_mpa = YOUNGS_MODULUS.magnitude.nominal_value * 1e3  # GPa -> MPa
        nu = POISSONS_RATIO.magnitude
        mat = mk.Material("STEEL")
        el = mk.Elastic((e_mpa, nu))
        sos = mk.SolidSection(
            elset=mesh.get_el_set_by_name("BEAM"),
            material=mat,
        )

        # BCs: fix all DOFs at fixed end
        fix_set = mesh.get_node_set_by_name("FIX")
        model.add_model_keywords(
            mk.Boundary(fix_set, first_dof=1, last_dof=3),
            mat, el, sos,
        )

        # Step: static with distributed load at free end
        load_set = mesh.get_node_set_by_name("LOAD")
        load_nids = list(load_set.ids)
        load_n = POINT_LOAD.to(ureg.N).magnitude
        load_per_node = load_n / len(load_nids)

        # Reason: one Cload keyword, many load lines — avoids repeated *CLOAD headers
        # Reason: cast to int() because pygccx isinstance check fails on numpy int64
        cload = sk.Cload(int(load_nids[0]), 3, -load_per_node)
        for nid in load_nids[1:]:
            cload.add_load(int(nid), 3, -load_per_node)

        step = sk.Step(nlgeom=False)
        step.add_step_keywords(
            sk.Static(),
            cload,
            sk.NodeFile([enums.ENodeFileResults.U]),
            sk.ElFile([enums.EElFileResults.S]),
        )
        model.add_steps(step)

        model.solve()

        # Extract results
        frd = model.get_frd_result()
        disp_sets = frd.get_result_sets_by(entity=enums.EFrdEntities.DISP)
        stress_sets = frd.get_result_sets_by(entity=enums.EFrdEntities.STRESS)

        all_nids = list(mesh.nodes.keys())
        disp_vals = disp_sets[-1].get_values_by_ids(all_nids)
        stress_vals = stress_sets[-1].get_values_by_ids(all_nids)

        # Reason: displacement magnitude = sqrt(ux^2 + uy^2 + uz^2)
        import numpy as np

        disp_mag = np.linalg.norm(disp_vals, axis=1)
        max_deflection_mm = float(np.max(disp_mag))

        mises = st.get_mises_stress(stress_vals)
        max_stress_mpa = float(np.max(mises))

    return max_deflection_mm, max_stress_mpa


def _add_face_groups(gmsh) -> None:
    """Add physical groups for fixed and loaded faces."""
    l_half = BEAM_LENGTH.to(ureg.mm).magnitude / 2
    tol = 0.1

    # Reason: find surface entities at fixed (-x) and loaded (+x) ends
    entities = gmsh.model.occ.getEntities(2)
    fix_tags = []
    load_tags = []
    for dim, tag in entities:
        bbox = gmsh.model.occ.getBoundingBox(dim, tag)
        xmin, _, _, xmax, _, _ = bbox
        if abs(xmin - (-l_half)) < tol and abs(xmax - (-l_half)) < tol:
            fix_tags.append(tag)
        elif abs(xmin - l_half) < tol and abs(xmax - l_half) < tol:
            load_tags.append(tag)

    gmsh.model.add_physical_group(2, fix_tags, name="FIX")
    gmsh.model.add_physical_group(2, load_tags, name="LOAD")
