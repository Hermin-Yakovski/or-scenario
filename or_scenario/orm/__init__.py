"""omni_orm proxy for or-scenario consumers.

Convenience re-exports of omni_orm factory functions.
Consumers can also import directly from omni_orm if preferred.
"""

from omni_orm import (
    generate_dimension_table,
    generate_fact_table,
    generate_sol_table,
)

Parameter = generate_dimension_table("Parameter")
Version = generate_dimension_table("Version")
Snapshot = generate_dimension_table("Snapshot")

__all__ = [
    "generate_dimension_table",
    "generate_fact_table",
    "generate_sol_table",
    "Parameter",
    "Version",
    "Snapshot",
]
