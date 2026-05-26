"""omni_orm proxy for or-scenario consumers.

Convenience re-exports of omni_orm factory functions.
Consumers can also import directly from omni_orm if preferred.
"""

from omni_orm import (
    generate_dimension_table,
    generate_fact_table,
    generate_sol_table,
    generate_extra_column,
)

DimParameter = generate_dimension_table("Parameter")
DimVersion = generate_dimension_table("Version",
    snapshot_id=generate_extra_column("snapshot_id", "integer", foreign_key='dim_snapshot.id', nullable=False),
)
DimSnapshot = generate_dimension_table("Snapshot")

__all__ = [
    "generate_dimension_table",
    "generate_fact_table",
    "generate_sol_table",
    "generate_extra_column",
    "DimParameter",
    "DimVersion",
    "DimSnapshot",
]
