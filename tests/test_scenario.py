# tests/test_scenario.py
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock
from dal import JsonHandler, DataHandler
from or_scenario import LoadStep, Scenario
from register import Register, Parameter


def test_loadstep_init():
    """Test LoadStep can be initialized with all parameters."""
    handler = JsonHandler()

    def dummy_mapping(records: List[Dict[str, Any]]) -> None:
        pass

    step = LoadStep(
        handler=handler,
        mapping=dummy_mapping,
        path=Path("test/path"),
        table="test.json",
        cols=["col1", "col2"],
        filter_=lambda x: True,
        limit=100,
        strict=True
    )

    assert step.handler is handler
    assert step.mapping is dummy_mapping
    assert step.path == Path("test/path")
    assert step.table == "test.json"
    assert step.cols == ["col1", "col2"]
    assert step.limit == 100
    assert step.strict is True


def test_loadstep_init_with_defaults():
    """Test LoadStep initialization with default values."""
    handler = JsonHandler()

    def dummy_mapping(records: List[Dict[str, Any]]) -> None:
        pass

    step = LoadStep(
        handler=handler,
        mapping=dummy_mapping,
        path=Path("test/path"),
        table="test.json"
    )

    assert step.handler is handler
    assert step.mapping is dummy_mapping
    assert step.path == Path("test/path")
    assert step.table == "test.json"
    assert step.cols is None
    assert step.filter_ is None
    assert step.limit is None
    assert step.strict is True  # strict defaults to True


def test_loadstep_run():
    """Test LoadStep.run() fetches data and calls mapping."""
    # Create mock handler
    handler = MagicMock(spec=DataHandler)
    handler.fetch.return_value = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20}
    ]

    # Create mapping that tracks calls
    mapping_calls = []
    def track_mapping(records: List[Dict[str, Any]]) -> None:
        mapping_calls.append(records)

    step = LoadStep(
        handler=handler,
        mapping=track_mapping,
        path=Path("test/path"),
        table="test.json",
        strict=True
    )

    step.run()

    # Verify handler.fetch was called correctly
    handler.fetch.assert_called_once_with(
        path=Path("test/path"),
        table="test.json",
        cols=None,
        filter_=None,
        limit=None,
        strict=True
    )

    # Verify mapping was called with fetched data
    assert len(mapping_calls) == 1
    assert mapping_calls[0] == [{"id": 1, "value": 10}, {"id": 2, "value": 20}]


def test_scenario_init():
    """Test Scenario can be initialized with version_id."""
    scenario = Scenario(1)
    assert scenario._version_id == 1
    assert scenario._algorithm is None
    assert isinstance(scenario._data, Register)
    assert scenario._load_steps == []
