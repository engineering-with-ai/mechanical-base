"""Write a complete CalculiX .inp file from gmsh mesh + BCs + material."""

from pathlib import Path

# Reason: nodes within this tolerance of the target x-coordinate are on the face
NODE_TOL = 0.1  # mm


def _parse_nodes(mesh_inp: Path) -> dict[int, tuple[float, float, float]]:
    """Extract node ID -> (x, y, z) from gmsh .inp file."""
    nodes: dict[int, tuple[float, float, float]] = {}
    in_nodes = False
    for line in mesh_inp.read_text().splitlines():
        if line.startswith("*NODE"):
            in_nodes = True
            continue
        if line.startswith("*"):
            in_nodes = False
            continue
        if in_nodes and line.strip():
            parts = line.split(",")
            nid = int(parts[0])
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            nodes[nid] = (x, y, z)
    return nodes


def _extract_volume_mesh(mesh_inp: Path) -> str:
    """Extract only NODE and C3D4 ELEMENT blocks from gmsh .inp.

    Reason: gmsh also writes T3D2 (truss) and CPS3 (plane stress) elements
    for edges/surfaces. CalculiX errors on CPS3 without thickness. We only
    need the volume mesh for a 3D solid analysis.
    """
    lines_out: list[str] = []
    copying = False
    for line in mesh_inp.read_text().splitlines():
        if line.startswith("*NODE") or (line.startswith("*ELEMENT") and "C3D4" in line):
            copying = True
        elif line.startswith("*"):
            copying = False
            continue

        if copying:
            lines_out.append(line)
    return "\n".join(lines_out)


def _nodes_at_x(
    nodes: dict[int, tuple[float, float, float]], target_x: float
) -> list[int]:
    """Find node IDs on a face at a given x-coordinate."""
    return [nid for nid, (x, _, _) in nodes.items() if abs(x - target_x) < NODE_TOL]


def write_ccx_inp(
    mesh_inp: Path,
    output_inp: Path,
    youngs_mpa: float,
    poissons: float,
    load_n: float,
    fixed_x: float,
    loaded_x: float,
) -> None:
    """Write complete CalculiX input deck.

    Args:
        mesh_inp: Path to gmsh-generated .inp (nodes + elements only)
        output_inp: Path for output CalculiX .inp
        youngs_mpa: Young's modulus in MPa
        poissons: Poisson's ratio (dimensionless)
        load_n: Total point load in Newtons
        fixed_x: x-coordinate of the fixed face (mm)
        loaded_x: x-coordinate of the loaded face (mm)
    """
    nodes = _parse_nodes(mesh_inp)
    fixed_nodes = _nodes_at_x(nodes, fixed_x)
    loaded_nodes = _nodes_at_x(nodes, loaded_x)

    # Reason: distribute total load evenly across free-end face nodes
    load_per_node = load_n / len(loaded_nodes)

    mesh_text = _extract_volume_mesh(mesh_inp)

    lines = [mesh_text]

    # Material
    lines.append("*MATERIAL, NAME=STEEL")
    lines.append("*ELASTIC")
    lines.append(f"{youngs_mpa}, {poissons}")

    # Assign material to element set from gmsh
    lines.append("*SOLID SECTION, MATERIAL=STEEL, ELSET=Volume1")
    lines.append("")

    # Boundary conditions: fix all DOFs at fixed face
    lines.append("*BOUNDARY")
    lines.extend(f"{nid}, 1, 3, 0.0" for nid in fixed_nodes)

    # Step
    lines.append("*STEP")
    lines.append("*STATIC")

    # Loading: distributed point load in -Z direction (direction 3, negative)
    lines.append("*CLOAD")
    lines.extend(f"{nid}, 3, {-load_per_node:.6f}" for nid in loaded_nodes)

    # Output requests
    lines.append("*NODE FILE")
    lines.append("U")
    lines.append("*EL FILE")
    lines.append("S")

    lines.append("*END STEP")

    output_inp.write_text("\n".join(lines))
