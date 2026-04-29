# tests/test_scenario.py
import pytest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock
from datetime import datetime
from dal import JsonHandler, DataHandler
from or_scenario import Scenario
from or_scenario.scenario import LoadStep, BaseRequest, BaseResponse
from register import Register
from pydantic import BaseModel, Field


# Pydantic models for integration testing
class TestRequest(BaseRequest):
    """Test request model for integration testing."""
    value: int = Field(default=10, description="test value")


class TestResult(BaseModel):
    """Test result model."""
    computed_value: int
    metadata: Dict[str, str]


class TestResponse(BaseResponse):
    """Test response model with specific response type."""
    response: TestResult


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


def test_scenario_get():
    """Test Scenario.get() retrieves values from _data."""
    from register import Dimension, Parameter
    Product = Dimension("Product", "产品", "PROD")
    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    scenario = Scenario(1)
    scenario._data[SalesVolume][(Product,)][(1,)] = 100.0
    result = scenario.get(SalesVolume, (Product,), (1,))
    assert result == 100.0


def test_scenario_set():
    """Test Scenario.set() sets values in _data."""
    from register import Dimension, Parameter
    Product = Dimension("Product", "产品", "PROD")
    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    scenario = Scenario(1)
    scenario.set(SalesVolume, (Product,), (1,), 150.0)
    result = scenario.get(SalesVolume, (Product,), (1,))
    assert result == 150.0


def test_scenario_set_algorithm():
    """Test Scenario.set_algorithm() creates algorithm instance."""
    from or_algo import Algorithm
    scenario = Scenario(1)
    scenario.set_algorithm(Algorithm)
    assert scenario._algorithm is not None
    assert isinstance(scenario._algorithm, Algorithm)


def test_scenario_exec_algorithm():
    """Test Scenario.exec_algorithm() calls algorithm.solve()."""
    from or_algo import Algorithm
    scenario = Scenario(1)
    mock_algo = MagicMock(spec=Algorithm)
    scenario._algorithm = mock_algo
    scenario.exec_algorithm()
    mock_algo.solve.assert_called_once_with(scenario._data)


def test_scenario_exec_algorithm_not_set():
    """Test Scenario.exec_algorithm() raises error when algorithm not set."""
    scenario = Scenario(1)
    import pytest
    with pytest.raises(RuntimeError, match="Algorithm not set"):
        scenario.exec_algorithm()


def test_scenario_load():
    """Test Scenario.load() executes all load steps in order."""
    run_order = []
    def make_step(name: str) -> LoadStep:
        handler = MagicMock(spec=DataHandler)
        handler.fetch.return_value = []
        def mapping(records):
            run_order.append(name)
        return LoadStep(handler=handler, mapping=mapping, path=Path("test"), table=f"{name}.json")
    scenario = Scenario(1)
    scenario._load_steps = [make_step("step1"), make_step("step2")]
    scenario.load()
    assert run_order == ["step1", "step2"]


def test_scenario_validate():
    """Test Scenario.validate() validates data with default parameter."""
    from register import Id, Index
    scenario = Scenario(1)
    scenario._data[Id][(Index,)][(1,)] = 1
    scenario.validate()


def test_scenario_validate_default_param():
    """Test Scenario.validate() with explicit default parameter."""
    from register import Id, Index
    scenario = Scenario(1)
    scenario._data[Id][(Index,)][(1,)] = 1
    scenario.validate()


def test_scenario_integration():
    """Integration test with domain-specific scenario loading JSON data."""
    import tempfile
    import json
    from register import Dimension, Parameter

    # Define domain-specific dimensions and parameters
    Product = Dimension("Product", "产品", "PROD")
    Region = Dimension("Region", "区域", "REG")
    TestSalesVolume = Parameter(100, "test_sales", "test_sales", float)
    TestPrice = Parameter(101, "test_price", "test_price", float)

    # Create domain-specific scenario class
    class TestScenario(Scenario):
        def __init__(self, version_id, data_dir):
            super().__init__(version_id)

            def map_sales_data(records):
                for r in records:
                    self.set(TestSalesVolume, (Product, Region), (r["product_id"], r["region_id"]), r["volume"])
                    self.set(TestPrice, (Product, Region), (r["product_id"], r["region_id"]), r["price"])

            self._load_steps = [LoadStep(handler=JsonHandler(), mapping=map_sales_data, path=data_dir, table="sales.json", strict=True)]

    # Create temporary directory with test data
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)
        test_data = [
            {"product_id": 1, "region_id": 1, "volume": 100.0, "price": 10.0},
            {"product_id": 1, "region_id": 2, "volume": 150.0, "price": 12.0}
        ]

        with open(data_path / "sales.json", "w") as f:
            json.dump(test_data, f)

        # Create scenario and load data
        scenario = TestScenario("test-001", data_path)
        scenario.load()

        # Verify data was loaded correctly
        assert scenario.get(TestSalesVolume, (Product, Region), (1, 1)) == 100.0
        assert scenario.get(TestPrice, (Product, Region), (1, 2)) == 12.0


def test_baserequest_creation():
    """Test BaseRequest can be created with default request_id."""
    request = BaseRequest()
    assert isinstance(request.request_id, int)
    assert len(str(request.request_id)) == 14  # YYMMDDHHMMSSFF format


def test_baseresponse_creation():
    """Test BaseResponse can be created with all fields."""
    from or_scenario.scenario import BaseResponse
    response = BaseResponse(
        request_id=12345,
        status=200,
        message="Success"
    )
    assert response.request_id == 12345
    assert response.status == 200
    assert response.message == "Success"
    assert isinstance(response.timestamp, datetime)
    assert response.response is None


def test_baseresponse_with_response_field():
    """Test BaseResponse can hold custom response data."""
    from or_scenario.scenario import BaseResponse
    custom_data = {"key": "value", "number": 42}
    response = BaseResponse(
        request_id=12345,
        status=200,
        message="Success",
        response=custom_data
    )
    assert response.response == custom_data


def test_scenario_request_attribute():
    """Test Scenario has _request attribute initialized to None."""
    scenario = Scenario(1)
    assert hasattr(scenario, '_request')
    assert scenario._request is None


def test_scenario_response_not_implemented():
    """Test Scenario.response() raises NotImplementedError."""
    scenario = Scenario(1)
    with pytest.raises(NotImplementedError, match="Subclasses must implement response"):
        scenario.response()


def test_scenario_response_accepts_any_arguments():
    """Test response() signature accepts *args and **kwargs."""
    scenario = Scenario(1)
    # This should not raise TypeError for argument signature
    with pytest.raises(NotImplementedError):
        scenario.response("arg1", "arg2", key1="value1", key2="value2")


def test_public_api_exports():
    """Test BaseRequest and BaseResponse are exported in public API."""
    import or_scenario
    assert hasattr(or_scenario, 'BaseRequest')
    assert hasattr(or_scenario, 'BaseResponse')
    assert 'BaseRequest' in or_scenario.__all__
    assert 'BaseResponse' in or_scenario.__all__


def test_scenario_pydantic_integration():
    """Integration test: Scenario with Pydantic request/response."""
    # Create a test scenario that uses Pydantic models
    class TestScenario(Scenario):
        def __init__(self, request: BaseRequest):
            super().__init__(request.request_id)
            self._request = request  # type: TestRequest

        def response(self, multiplier: int = 1) -> BaseResponse:
            """Return response with computed result."""
            result = TestResult(
                computed_value=self._request.value * multiplier,
                metadata={"multiplier": str(multiplier)}
            )
            return TestResponse(
                request_id=self._request.request_id,
                status=200,
                message="Test completed",
                response=result
            )

    # Create request and scenario
    request = TestRequest(value=10)
    scenario = TestScenario(request)

    # Get response
    response = scenario.response(multiplier=5)

    # Verify response structure
    assert isinstance(response, TestResponse)
    assert response.request_id == request.request_id
    assert response.status == 200
    assert response.response.computed_value == 50
    assert response.response.metadata["multiplier"] == "5"


def test_scenario_backward_compatibility():
    """Test that scenarios without Pydantic still work."""
    # Old-style scenario without Pydantic
    class LegacyScenario(Scenario):
        def __init__(self, version_id: int):
            super().__init__(version_id)
            self.custom_value = 100

        def custom_method(self) -> int:
            return self.custom_value * 2

    # Create and use legacy scenario
    scenario = LegacyScenario(42)
    assert scenario._version_id == 42
    assert scenario._request is None
    assert scenario.custom_method() == 200

    # response() should still raise NotImplementedError
    with pytest.raises(NotImplementedError):
        scenario.response()
