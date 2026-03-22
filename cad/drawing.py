"""Export cantilever beam drawing views via CadQuery SVG export.

Generates front, side, and isometric projection SVGs directly from
the CadQuery model. No FreeCAD dependency required.
"""

from pathlib import Path

from cadquery import exporters

from cad.model import build_beam

DRAWINGS_DIR = Path("spec/drawings")

# Reason: standard engineering drawing projections
VIEWS = {
    "front": {"projectionDir": (0, -1, 0)},
    "side": {"projectionDir": (1, 0, 0)},
    "iso": {"projectionDir": (1, -1, 1)},
}


def export_views() -> list[Path]:
    """Export beam projections as SVG files.

    Returns:
        List of exported SVG file paths
    """
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    beam = build_beam()

    exported: list[Path] = []
    for name, opts in VIEWS.items():
        svg_path = DRAWINGS_DIR / f"cantilever_beam_{name}.svg"
        exporters.export(
            beam,
            str(svg_path),
            opt={
                "width": 300,
                "height": 200,
                "showHidden": True,
                **opts,
            },
        )
        exported.append(svg_path)
        print(f"Exported {svg_path}")

    return exported


if __name__ == "__main__":
    paths = export_views()
    print(f"Generated {len(paths)} drawing views")
