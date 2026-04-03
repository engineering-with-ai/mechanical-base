# cad/drawing/

Generated drawing exports — SVG projections and TechDraw PDF.

Run `uv run poe generate-model` (CadQuery SVG) or `uv run poe generate-asm` (TechDraw PDF) to populate.

## Files

| File | Purpose |
|------|---------|
| `drawing.py` | CadQuery SVG projections (front, side, iso) |
| `export_drawing.py` | FreeCAD TechDraw → PDF via rsvg-convert |
