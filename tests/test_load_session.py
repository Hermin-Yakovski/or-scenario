"""Tests for load(session) method - isolated to avoid ortools dependency issues."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_scenario_load_session():
    """Test that load(session) raises NotImplementedError by default."""
    # Load schema module first (needed by scenario module)
    schema_path = Path(__file__).parent.parent / "or_scenario" / "schema.py"
    schema_spec = importlib.util.spec_from_file_location("or_scenario.schema", str(schema_path))
    schema_module = importlib.util.module_from_spec(schema_spec)
    sys.modules["or_scenario.schema"] = schema_module
    schema_spec.loader.exec_module(schema_module)

    # Load scenario module directly to avoid or_scenario import chain with broken ortools
    scenario_path = Path(__file__).parent.parent / "or_scenario" / "scenario.py"
    spec = importlib.util.spec_from_file_location("or_scenario.scenario", str(scenario_path))
    scenario_module = importlib.util.module_from_spec(spec)

    # Mock the or_algo module to avoid ortools dependency
    sys.modules["or_algo"] = MagicMock()
    sys.modules["or_algo.Algorithm"] = MagicMock()

    # Now execute the module
    spec.loader.exec_module(scenario_module)

    # Get the Scenario class
    Scenario = scenario_module.Scenario

    # Create mock session
    mock_session = MagicMock()
    scenario = Scenario()

    # Test that load(session) raises NotImplementedError
    with pytest.raises(NotImplementedError, match="Subclasses must implement load"):
        scenario.load(mock_session)


if __name__ == "__main__":
    test_scenario_load_session()
    print("test_scenario_load_session passed!")
