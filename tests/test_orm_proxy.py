"""Tests for orm proxy - isolated to avoid ortools dependency issues."""

import importlib.util
import sys
from pathlib import Path


def test_orm_proxy():
    """Test that orm proxy re-exports omni_orm factory functions."""
    # Load orm module directly to avoid or_scenario import chain with broken ortools
    orm_path = Path(__file__).parent.parent / "or_scenario" / "orm" / "__init__.py"
    spec = importlib.util.spec_from_file_location("orm", str(orm_path))
    orm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orm)

    # Import factory functions from the loaded module
    generate_dimension_table = orm.generate_dimension_table
    generate_fact_table = orm.generate_fact_table

    # Verify factory functions work
    DimDistrict = generate_dimension_table("District")
    FactDistrictOwner = generate_fact_table("District", "Owner")

    assert DimDistrict.__name__ == "DimDistrict"
    assert FactDistrictOwner.__name__ == "FactDistrictOwner"


if __name__ == "__main__":
    test_orm_proxy()
    print("All orm proxy tests passed!")
