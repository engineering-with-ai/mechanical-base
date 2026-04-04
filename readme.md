# [mechanical-model]

![](https://img.shields.io/gitlab/pipeline-status/engineering-with-ai/mechanical-model?branch=main&logo=gitlab)
![](https://gitlab.com/engineering-with-ai/mechanical-model/badges/main/coverage.svg)

L-bracket bolted connection — verifies bolt reaction forces and bracket stress for a Nylon PA12 (HP MJF) L-bracket bolted to a wall plate under a vertical point load.

An engineer sizing a mounting bracket needs to confirm that the bolts and bracket meet strength requirements before fabrication. The bolt group hand calculation provides expected reaction forces (rigid bracket assumption). The CalculiX FEM simulation solves the same problem numerically on a 3D mesh. Agreement validates the model and toolchain; the bracket stress must remain below yield.

**[View generated deliverables](output/)**

## Bracket Spec

```mermaid
graph LR
    WALL["Wall Plate"] --- BOLTS["2x M8 Bolts<br/>40mm spacing"]
    BOLTS --- VERT["Vertical Leg<br/>80 x 50 x 14mm"]
    VERT --- BEND["Fillet R8mm"]
    BEND --- HORIZ["Horizontal Leg<br/>60 x 50 x 14mm"]
    HORIZ --- LOAD["500N downward"]

    style WALL fill:#666,stroke:#333
    style BOLTS fill:#888,stroke:#333
    style VERT fill:#49a,stroke:#333
    style BEND fill:#49a,stroke:#333
    style HORIZ fill:#49a,stroke:#333
    style LOAD fill:#a94,stroke:#333
```

Material: Nylon PA12 (HP Multi Jet Fusion) — E = 1.7 GPa, tensile strength = 48 MPa

## Workflow

```
theory.ipynb (sympy + pint) -> cad/model/model.py (CadQuery -> STEP) -> sim/model.py (pygccx -> CalculiX FEM) -> pytest (assert FEM matches theory)
```

1. `theory.ipynb` derives bolt group forces symbolically, plugs in parameters with pint
2. `cad/model/model.py` generates the parametric L-bracket via CadQuery, exports STEP
3. `cad/model/assembly.py` builds assembly with bracket + M8 bolts
4. `sim/model.py` meshes STEP with gmsh, builds CalculiX model via pygccx, solves, extracts results
5. `sim/test_run.py` asserts FEM bolt force matches hand calc within 35%, stress below yield
6. `/generate-gdt` refines dimension presentation on the manufacturing drawing

## Quick Start

```bash
uv sync
uv run poe checks          # black + ruff lint
uv run poe notebook         # execute theory.ipynb
uv run poe build            # CadQuery -> STEP
uv run poe sim              # pygccx + pytest (2/2 tests)
uv run poe validate-model   # BRep validity + bbox vs constants
uv run poe validate-asm     # assembly validation
```

## Code to Fabrication

```
build -> sim -> validate-model -> generate-model -> validate-asm -> generate-asm
```

1. `uv run poe build` — CadQuery generates parametric L-bracket STEP
2. `uv run poe sim` — FEM simulation + assertions (2/2 pass)
3. `uv run poe validate-model` — BRep validity + bounding box vs constants
4. `uv run poe generate-model` — GD&T dimensioned drawing (PDF + web SVG + dark SVG + DXF)
5. `uv run poe validate-asm` — assembly validation
6. `uv run poe generate-asm` — assembly STEP to `output/fab/`

## Structure

- `theory.ipynb` — sympy bolt group derivation, pint + uncertainties, expected values
- `sim/` — simulation + pytest assertions against theory
- `cad/model/` — CadQuery geometry (model.py, assembly.py, validate_model.py, validate_asm.py)
- `cad/drawing/` — drawing exports (dimensions.py, layout.py, export_drawing.py)
- `cad/layout_spec.yaml` — drawing layout + tolerance config (sheet size, views, ISO 2768-m)
- `cad/model/templates/` — EWAI ISO 5457 drawing sheet template
- `output/drawings/` — manufacturing drawing (PDF), web SVGs (light + dark), DXF
- `output/fab/` — STEP files (part + assembly) for fabrication
