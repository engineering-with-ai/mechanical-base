"""Mesh the cantilever beam STEP file using gmsh.

Exports .inp (Abaqus format) for CalculiX consumption.
"""

import gmsh

from cad.model import STEP_PATH

INP_PATH = "sim/results/cantilever_beam.inp"
MESH_SIZE = 1.0  # mm — fine mesh needed for bending accuracy with linear C3D4 tets


def generate_mesh() -> str:
    """Mesh STEP geometry and write Abaqus .inp file.

    Returns:
        Path to generated .inp file
    """
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("cantilever_beam")

    gmsh.model.occ.importShapes(STEP_PATH)
    gmsh.model.occ.synchronize()

    # Reason: uniform mesh size for simple geometry, no adaptive refinement needed
    gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_SIZE)
    gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_SIZE)

    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("Netgen")

    # Reason: Abaqus format is CalculiX-compatible
    gmsh.write(INP_PATH)

    node_tags, _, _ = gmsh.model.mesh.getNodes()
    print(f"Mesh: {len(node_tags)} nodes")

    gmsh.finalize()
    return INP_PATH


if __name__ == "__main__":
    generate_mesh()
