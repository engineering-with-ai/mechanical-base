"""Export engineering drawing as PDF via FreeCAD TechDraw.

Uses DrawProjGroup for auto-layout of standard projection views.
Export path: TechDraw SVG → rsvg-convert → PDF (bypasses Qt's thick
stroke rendering in exportPageAsPdf).

Run via poe task:
    uv run poe drawing
"""

import os
import shutil
import time
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import FreeCAD as App
import FreeCADGui as Gui

Gui.showMainWindow()

import Part  # noqa: E402
import subprocess  # noqa: E402
import TechDrawGui  # noqa: E402

STEP_FILE = Path("cad/cantilever_beam.step")
TEMPLATE = Path("cad/templates/A1_Landscape_EWAI.svg")
DRAWINGS_DIR = Path("cad/drawings")
SPEC_DIR = Path("spec")

TITLE_BLOCK = {
    "title": "Cantilever Beam",
    "creator": "Engineering with AI",
    "document_type": "General Arrangement",
    "approval_person": "",
    "identification_number": "MECH-001",
    "part_material": "Structural Steel",
    "revision_index": "A",
    "legal_owner_1": "",
    "legal_owner_2": "",
    "legal_owner_3": "",
    "legal_owner_4": "",
}


def export_drawing() -> Path:
    """Build TechDraw page with auto-layout and export as PDF."""
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)

    doc = App.newDocument("beam")
    shape = Part.read(str(STEP_FILE))
    part_obj = doc.addObject("Part::Feature", "Beam")
    part_obj.Shape = shape
    doc.recompute()

    page = doc.addObject("TechDraw::DrawPage", "Page")
    page.KeepUpdated = True
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tmpl.Template = str(TEMPLATE)
    page.Template = tmpl

    texts = tmpl.EditableTexts
    texts.update(TITLE_BLOCK)
    tmpl.EditableTexts = texts
    doc.recompute()

    # Reason: DrawProjGroup auto-positions views in third-angle projection.
    # ScaleType=Page lets FreeCAD pick the best fit for the sheet.
    proj = doc.addObject("TechDraw::DrawProjGroup", "ProjGroup")
    page.addView(proj)
    proj.Source = [part_obj]
    proj.ScaleType = "Page"
    proj.AutoDistribute = True
    proj.addProjection("Front")
    proj.addProjection("Right")
    proj.addProjection("Top")
    proj.addProjection("FrontTopRight")
    doc.recompute()

    # Update scale field to match auto-calculated scale
    scale = proj.Scale
    if scale >= 1:
        texts["scale"] = f"{scale:.0f} : 1"
    else:
        texts["scale"] = f"1 : {1/scale:.0f}"
    tmpl.EditableTexts = texts
    doc.recompute()

    # Force Qt scene graph to render template border + title block
    page.ViewObject.ForceUpdate = True
    page.ViewObject.doubleClicked()
    for _ in range(15):
        Gui.updateGui()
        time.sleep(0.3)

    svg_path = DRAWINGS_DIR / "cantilever_beam_sheet.svg"
    pdf_path = DRAWINGS_DIR / "cantilever_beam.pdf"

    TechDrawGui.exportPageAsSvg(page, str(svg_path))

    # Reason: rsvg-convert preserves SVG stroke widths. TechDraw's
    # exportPageAsPdf uses QPdfWriter which inflates line weights.
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", str(svg_path), "-o", str(pdf_path)],
        check=True,
    )

    shutil.copy(pdf_path, SPEC_DIR / "cantilever_beam.pdf")
    print(f"Exported {pdf_path} ({pdf_path.stat().st_size} bytes)")
    return pdf_path


if __name__ == "__main__":
    export_drawing()
    App.closeDocument("beam")
