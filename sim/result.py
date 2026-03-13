from pydantic import BaseModel


class FemResult(BaseModel):
    """FEM solution results for cantilever beam."""

    max_deflection_mm: float
    max_stress_mpa: float
