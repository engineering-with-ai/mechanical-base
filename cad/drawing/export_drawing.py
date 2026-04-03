"""Export engineering drawing as PDF via FreeCAD TechDraw.

Uses DrawProjGroup for auto-layout of standard projection views.
Export path: TechDraw SVG -> rsvg-convert -> PDF (bypasses Qt's thick
stroke rendering in exportPageAsPdf).

Reads title block and projection config from layout_spec.yaml.
"""

import time
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui

Gui.showMainWindow()

import Part  # noqa: E402
import subprocess  # noqa: E402
import TechDrawGui  # noqa: E402
import yaml  # noqa: E402

# ISO 216 landscape dimensions (width, height) in mm
SHEET_DIMS = {
    "A4": (297, 210),
    "A3": (420, 297),
    "A2": (594, 420),
    "A1": (841, 594),
    "A0": (1189, 841),
}

STEP_FILE = Path("cad/l_bracket.step")
TEMPLATES_DIR = Path("cad/model/templates")
LAYOUT_SPEC_PATH = Path("cad/layout_spec.yaml")
DRAWINGS_DIR = Path("output/drawings")


def _load_spec() -> dict:
    return yaml.safe_load(LAYOUT_SPEC_PATH.read_text())


def _resolve_template(sheet_size: str) -> Path:
    """Pick template SVG based on sheet_size from layout_spec."""
    template = TEMPLATES_DIR / f"{sheet_size}_Landscape_EWAI.svg"
    if not template.exists():
        raise FileNotFoundError(
            f"No template for sheet_size '{sheet_size}': {template}"
        )
    return template


def export_drawing() -> Path:
    """Build TechDraw page with auto-layout and export as PDF."""
    spec = _load_spec()
    title_block = spec["title_block"]
    td = spec["techdraw"]
    template_path = _resolve_template(spec["sheet_size"])

    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)

    doc = App.newDocument("bracket")
    shape = Part.read(str(STEP_FILE))
    part_obj = doc.addObject("Part::Feature", "LBracket")
    part_obj.Shape = shape
    doc.recompute()

    page = doc.addObject("TechDraw::DrawPage", "Page")
    page.KeepUpdated = True
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tmpl.Template = str(template_path)
    page.Template = tmpl

    texts = tmpl.EditableTexts
    texts["title"] = spec["title"]
    texts.update(title_block)
    tmpl.EditableTexts = texts
    doc.recompute()

    # Reason: use individual DrawViewPart objects for full position control.
    # FreeCAD's DrawProjGroup.AutoDistribute doesn't know about the title
    # block. We compute view sizes from the shape's bounding box projected
    # along each view direction, then place each view explicitly.
    sheet_w, sheet_h = SHEET_DIMS[spec["sheet_size"]]
    margin_left, margin_top = 20, 10
    padding = td.get("padding", 5)
    gap = td.get("gap", 15)
    title_block_h = 58  # ISO 5457
    scale = td.get("scale", 1.0)

    bb = shape.BoundBox
    usable_l = margin_left + padding
    usable_r = sheet_w - margin_left - padding
    usable_top_y = sheet_h - margin_top - padding
    usable_bot_y = margin_top + title_block_h + padding
    usable_w = usable_r - usable_l
    usable_h = usable_top_y - usable_bot_y
    has_iso = "FrontTopRight" in td["projections"]

    # Reason: compute total layout extent at a given scale to check fit.
    # Returns (view_defs, required_width, required_height).
    def _layout_at_scale(s):
        fw, fh = bb.XLength * s, bb.ZLength * s
        rw, _ = bb.YLength * s, bb.ZLength * s
        _, th = bb.XLength * s, bb.YLength * s
        iso_est = max(fw, fh) * 1.2

        # Width: Right + gap + Front + gap + (Iso if present)
        total_w = fw + gap + rw
        if has_iso:
            total_w += gap + iso_est
        # Height: Top + gap + Front (Front and Right share the row)
        total_h = th + gap + fh

        # Compute positions (Y-up coordinate system)
        top_cy = usable_top_y - th / 2
        front_cy = top_cy - th / 2 - gap - fh / 2
        front_cx = usable_l + fw / 2
        right_cx = front_cx + fw / 2 + gap + rw / 2

        defs = {
            "Front": ((0, -1, 0), front_cx, front_cy),
            "Right": ((1, 0, 0), right_cx, front_cy),
            "Top": ((0, 0, 1), front_cx, top_cy),
        }
        if has_iso:
            iso_cx = right_cx + rw / 2 + gap + iso_est / 2
            defs["Iso"] = ((1, -1, 1), iso_cx, front_cy)

        return defs, total_w, total_h

    # Reason: auto-scale down if views don't fit the usable area.
    # Try the requested scale first; if it overflows, shrink to fit.
    view_defs, total_w, total_h = _layout_at_scale(scale)
    if total_w > usable_w or total_h > usable_h:
        fit_scale_w = usable_w / (total_w / scale)
        fit_scale_h = usable_h / (total_h / scale)
        scale = min(fit_scale_w, fit_scale_h) * 0.95  # 5% margin
        view_defs, total_w, total_h = _layout_at_scale(scale)
        print(f"Auto-scaled to {scale:.2f} to fit {spec['sheet_size']} sheet")

    for name, (direction, cx, cy) in view_defs.items():
        v = doc.addObject("TechDraw::DrawViewPart", name)
        page.addView(v)
        v.Source = [part_obj]
        v.Direction = App.Vector(*direction)
        v.Scale = scale
        v.X = cx
        v.Y = cy
    doc.recompute()

    # Update scale field in title block
    if scale >= 1:
        texts["scale"] = f"{scale:.0f} : 1"
    else:
        texts["scale"] = f"1 : {1 / scale:.0f}"
    tmpl.EditableTexts = texts
    doc.recompute()

    # Force Qt scene graph to render template border + title block
    page.ViewObject.ForceUpdate = True
    page.ViewObject.doubleClicked()
    for _ in range(15):
        Gui.updateGui()
        time.sleep(0.3)

    svg_path = DRAWINGS_DIR / "l_bracket_sheet.svg"
    pdf_path = DRAWINGS_DIR / "l_bracket.pdf"

    TechDrawGui.exportPageAsSvg(page, str(svg_path))

    # Reason: rsvg-convert preserves SVG stroke widths. TechDraw's
    # exportPageAsPdf uses QPdfWriter which inflates line weights.
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", str(svg_path), "-o", str(pdf_path)],
        check=True,
    )

    # DXF export for CNC shops — geometry + dimensions, no title block
    dxf_path = DRAWINGS_DIR / "l_bracket.dxf"
    import TechDraw

    TechDraw.writeDXFPage(page, str(dxf_path))

    print(f"Exported {pdf_path} ({pdf_path.stat().st_size} bytes)")
    print(f"Exported {dxf_path} ({dxf_path.stat().st_size} bytes)")
    return pdf_path


if __name__ == "__main__":
    export_drawing()
    App.closeDocument("bracket")
