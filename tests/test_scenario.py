# tests/test_scenario.py
from pathlib import Path
from typing import Any, Dict, List
from dal import JsonHandler
from or_scenario import LoadStep


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
