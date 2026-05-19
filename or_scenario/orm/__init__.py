"""omni_orm proxy for or-scenario consumers.

Convenience re-exports of omni_orm factory functions.
Consumers can also import directly from omni_orm if preferred.
"""

from omni_orm import (
    generate_dimension_table,
    generate_fact_table,
    generate_sol_table,
)

DimParameter = generate_dimension_table("DimParameter")
DimVersion = generate_dimension_table("DimVersion")
DimSnapshot = generate_dimension_table("DimSnapshot")

__all__ = [
    "generate_dimension_table",
    "generate_fact_table",
    "generate_sol_table",
    "DimParameter",
    "DimVersion",
    "DimSnapshot",
]
