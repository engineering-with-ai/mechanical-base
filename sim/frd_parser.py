"""Parse CalculiX .frd result files for displacement and stress."""

import math
from pathlib import Path

from sim.result import FemResult


def parse_frd(frd_path: Path) -> FemResult:
    """Parse .frd file for max displacement magnitude and max von Mises stress.

    The .frd format is line-oriented ASCII:
    - Blocks start with a header line (code in col 1-2)
    - " -4" line: component definition header
    - " -5" line: component name
    - " -1" lines: data values for each node
    - " -3" line: end of block

    Args:
        frd_path: Path to CalculiX .frd output

    Returns:
        FemResult with max deflection (mm) and max stress (MPa)
    """
    text = frd_path.read_text()
    lines = text.splitlines()

    displacements: list[float] = []
    stresses: list[float] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Reason: " -4  DISP" marks start of displacement block
        if line.strip().startswith("-4") and "DISP" in line:
            i = _skip_component_headers(lines, i + 1)
            i, displacements = _read_vector_magnitudes(lines, i)
            continue

        # Reason: " -4  STRESS" marks start of stress block
        if line.strip().startswith("-4") and "STRESS" in line:
            i = _skip_component_headers(lines, i + 1)
            i, stresses = _read_stress_von_mises(lines, i)
            continue

        i += 1

    return FemResult(
        max_deflection_mm=max(displacements),
        max_stress_mpa=max(stresses),
    )


def _skip_component_headers(lines: list[str], i: int) -> int:
    """Skip -5 component name lines."""
    while i < len(lines) and lines[i].strip().startswith("-5"):
        i += 1
    return i


def _read_vector_magnitudes(lines: list[str], i: int) -> tuple[int, list[float]]:
    """Read displacement vectors, compute magnitude."""
    magnitudes: list[float] = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("-3"):
            return i + 1, magnitudes
        if line.strip().startswith("-1"):
            # Reason: FRD format has fixed-width fields after node ID
            # node_id(3-12), val1(13-24), val2(25-36), val3(37-48)
            vals = _parse_frd_values(line)
            if len(vals) >= 3:
                mag = math.sqrt(vals[0] ** 2 + vals[1] ** 2 + vals[2] ** 2)
                magnitudes.append(mag)
        i += 1
    return i, magnitudes


def _read_stress_von_mises(lines: list[str], i: int) -> tuple[int, list[float]]:
    """Read stress tensor components, compute von Mises."""
    stresses: list[float] = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("-3"):
            return i + 1, stresses
        if line.strip().startswith("-1"):
            vals = _parse_frd_values(line)
            if len(vals) >= 6:
                # Reason: CalculiX outputs Sxx, Syy, Szz, Sxy, Syz, Szx
                sxx, syy, szz, sxy, syz, szx = vals[:6]
                vm = math.sqrt(
                    0.5
                    * (
                        (sxx - syy) ** 2
                        + (syy - szz) ** 2
                        + (szz - sxx) ** 2
                        + 6 * (sxy**2 + syz**2 + szx**2)
                    )
                )
                stresses.append(vm)
        i += 1
    return i, stresses


def _parse_frd_values(line: str) -> list[float]:
    """Parse fixed-width float values from an FRD -1 data line.

    FRD format: col 0-2 = code ( -1), col 3-12 = node id (10 chars),
    col 13+ = 12-char wide value fields.
    """
    # Reason: skip code (3 chars) + node id (10 chars) = 13 chars
    data = line[13:]
    vals: list[float] = []
    for j in range(0, len(data), 12):
        chunk = data[j : j + 12].strip()
        if chunk:
            vals.append(float(chunk))
    return vals
