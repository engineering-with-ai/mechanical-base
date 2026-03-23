"""Export L-bracket drawing views via CadQuery SVG export.

Generates front, side, and isometric projection SVGs directly from
the CadQuery model.
"""

from pathlib import Path

from cadquery import exporters

from cad.model import build_bracket

DRAWINGS_DIR = Path("spec/drawings")

# Reason: standard engineering drawing projections
VIEWS = {
    "front": {"projectionDir": (0, -1, 0)},
    "side": {"projectionDir": (1, 0, 0)},
    "iso": {"projectionDir": (1, -1, 1)},
}


def export_views() -> list[Path]:
    """Export bracket projections as SVG files."""
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    bracket = build_bracket()

    exported: list[Path] = []
    for name, opts in VIEWS.items():
        svg_path = DRAWINGS_DIR / f"l_bracket_{name}.svg"
        exporters.export(
            bracket,
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
