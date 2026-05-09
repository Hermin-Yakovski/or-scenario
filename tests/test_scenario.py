# tests/test_scenario.py
import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock
from datetime import datetime
from dal import JsonHandler, DataHandler
from or_scenario import Scenario
from or_scenario.scenario import BaseRequest, BaseResponse
from register import Register
from pydantic import BaseModel, Field


# Pydantic models for integration testing
class DemoRequest(BaseRequest):
    """Demo request model for integration testing."""
    value: int = Field(default=10, description="test value")


class DemoResult(BaseModel):
    """Demo result model."""
    computed_value: int
    metadata: Dict[str, str]


class DemoResponse(BaseResponse):
    """Demo response model with specific response type."""
    response: DemoResult


def test_scenario_init():
    """Test Scenario can be initialized with version_id."""
    scenario = Scenario(1)
    assert scenario._version_id == 1
    assert scenario._algorithm is None
    assert isinstance(scenario._data, Register)
    # After refactor, _load_step is a static decorator method, not an instance attribute
    assert callable(Scenario._load_step)


def test_scenario_init_with_default_request():
    """Test Scenario can be initialized with default BaseRequest."""
    scenario = Scenario()
    assert scenario._request is not None
    assert isinstance(scenario._request, BaseRequest)
    assert scenario._request.request_id is not None
    assert isinstance(scenario._request.request_id, int)
    # _version_id should be extracted from request_id
    assert scenario._version_id == scenario._request.request_id


def test_scenario_init_with_explicit_request():
    """Test Scenario can be initialized with explicit BaseRequest."""
    request = BaseRequest()
    scenario = Scenario(request)
    assert scenario._request is request  # Same object reference
    assert scenario._version_id == request.request_id


def test_decorator_transforms_method():
    """Test that @_load_step decorator transforms method signature."""
    class DecoratorTestScenario(Scenario):
        def __init__(self, version_id):
            super().__init__(version_id)
            self.mapping_called = False
            self.received_records = None

        @Scenario._load_step(JsonHandler(), Path("test"), "data.json")
        def load_data(self, records):
            self.mapping_called = True
            self.received_records = records

    # Create scenario and verify decorated method exists
    scenario = DecoratorTestScenario(1)
    assert hasattr(scenario, 'load_data')
    assert callable(scenario.load_data)
    # Decorated method should be callable without records argument
    import inspect
    sig = inspect.signature(scenario.load_data)
    # Wrapper accepts **kwargs, so signature should be flexible (only **kwargs, no 'records')
    assert len(sig.parameters) == 1  # Only **kwargs parameter
    assert 'kwargs' in sig.parameters


def test_decorator_fetches_and_maps():
    """Test decorator fetches data via handler and calls mapping function."""
    from register import Dimension, Parameter
    from unittest.mock import MagicMock

    Product = Dimension("Product", "产品", "PROD")
    TestVolume = Parameter(1, "test_volume", "test_volume", float)

    # Create mock handler
    mock_handler = MagicMock(spec=DataHandler)
    test_data = [{"id": 1, "volume": 100.0}, {"id": 2, "volume": 200.0}]
    mock_handler.fetch.return_value = test_data

    class DecoratorTestScenario(Scenario):
        @Scenario._load_step(mock_handler, Path("test"), "data.json")
        def load_data(self, records):
            for r in records:
                self.set(TestVolume, (Product,), (r["id"],), r["volume"])

    # Create scenario and load data
    scenario = DecoratorTestScenario(1)
    scenario.load_data()

    # Verify handler.fetch was called with correct arguments
    mock_handler.fetch.assert_called_once_with(
        path=Path("test"),
        table="data.json",
        cols=None,
        filter_=None,
        limit=None,
        strict=True
    )

    # Verify data was mapped correctly
    assert scenario.get(TestVolume, (Product,), (1,)) == 100.0
    assert scenario.get(TestVolume, (Product,), (2,)) == 200.0


def test_decorator_strict_propagates():
    """Test decorator with strict=True propagates exceptions."""
    from unittest.mock import MagicMock

    # Create mock handler that raises error
    mock_handler = MagicMock(spec=DataHandler)
    mock_handler.fetch.side_effect = IOError("File not found")

    class DecoratorTestScenario(Scenario):
        @Scenario._load_step(mock_handler, Path("test"), "data.json", strict=True)
        def load_data(self, records):
            pass

    scenario = DecoratorTestScenario(1)

    # Should raise IOError
    with pytest.raises(IOError, match="File not found"):
        scenario.load_data()


def test_decorator_non_strict_continues():
    """Test decorator with strict=False continues on error."""
    from unittest.mock import MagicMock

    # Create mock handler that raises error
    mock_handler = MagicMock(spec=DataHandler)
    mock_handler.fetch.side_effect = IOError("File not found")

    class DecoratorTestScenario(Scenario):
        error_caught = False

        @Scenario._load_step(mock_handler, Path("test"), "data.json", strict=False)
        def load_data(self, records):
            pass

    scenario = DecoratorTestScenario(1)

    # Should NOT raise error
    scenario.load_data()
    # If we get here, strict=False worked
    assert True


def test_decorator_kwargs_passthrough():
    """Test decorator passes **kwargs to mapping function."""
    from register import Dimension, Parameter

    Product = Dimension("Product", "产品", "PROD")
    TestVolume = Parameter(1, "test_volume", "test_volume", float)

    # Create mock handler
    mock_handler = MagicMock(spec=DataHandler)
    mock_handler.fetch.return_value = [
        {"id": 1, "volume": 100.0, "region": "US"},
        {"id": 2, "volume": 200.0, "region": "EU"}
    ]

    class DecoratorTestScenario(Scenario):
        @Scenario._load_step(mock_handler, Path("test"), "data.json")
        def load_data(self, records, region_filter=None):
            for r in records:
                if region_filter and r["region"] not in region_filter:
                    continue
                self.set(TestVolume, (Product,), (r["id"],), r["volume"])

    scenario = DecoratorTestScenario(1)

    # Without filter - all data loaded
    scenario.load_data()
    assert scenario.get(TestVolume, (Product,), (1,)) == 100.0
    assert scenario.get(TestVolume, (Product,), (2,)) == 200.0

    # Clear and reload with filter
    scenario._data = Register[Parameter]()
    scenario.load_data(region_filter=["US"])
    assert scenario.get(TestVolume, (Product,), (1,)) == 100.0
    # ID 2 (EU) should not be loaded
    with pytest.raises(KeyError):
        scenario.get(TestVolume, (Product,), (2,))


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
    """Test that decorated load methods are called in order."""
    from unittest.mock import MagicMock

    run_order = []

    # Create mock handlers
    handler1 = MagicMock(spec=DataHandler)
    handler1.fetch.return_value = [{"id": 1}]
    handler2 = MagicMock(spec=DataHandler)
    handler2.fetch.return_value = [{"id": 2}]

    class LoadTestScenario(Scenario):
        @Scenario._load_step(handler1, Path("test"), "step1.json")
        def load_step1(self, records):
            run_order.append("step1")

        @Scenario._load_step(handler2, Path("test"), "step2.json")
        def load_step2(self, records):
            run_order.append("step2")

        def load(self):
            self.load_step1()
            self.load_step2()

    scenario = LoadTestScenario(1)
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
    """Integration test with domain-specific scenario using decorator pattern."""
    import json
    from register import Dimension, Parameter

    # Define domain-specific dimensions and parameters
    Product = Dimension("Product", "产品", "PROD")
    Region = Dimension("Region", "区域", "REG")
    TestSalesVolume = Parameter(100, "test_sales", "test_sales", float)
    TestPrice = Parameter(101, "test_price", "test_price", float)

    # Use current working directory for test (simpler approach)
    test_data = [
        {"product_id": 1, "region_id": 1, "volume": 100.0, "price": 10.0},
        {"product_id": 1, "region_id": 2, "volume": 150.0, "price": 12.0}
    ]

    # Create test data file
    test_file = Path("test_sales.json")
    try:
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        # Create domain-specific scenario class with decorator
        class TestScenario(Scenario):
            @Scenario._load_step(JsonHandler(), Path("."), "test_sales.json", strict=True)
            def load_sales(self, records):
                for r in records:
                    self.set(TestSalesVolume, (Product, Region), (r["product_id"], r["region_id"]), r["volume"])
                    self.set(TestPrice, (Product, Region), (r["product_id"], r["region_id"]), r["price"])

            def load(self):
                self.load_sales()

        # Create scenario and load data
        scenario = TestScenario("test-001")
        scenario.load()

        # Verify data was loaded correctly
        assert scenario.get(TestSalesVolume, (Product, Region), (1, 1)) == 100.0
        assert scenario.get(TestPrice, (Product, Region), (1, 2)) == 12.0
    finally:
        # Cleanup test file
        if test_file.exists():
            test_file.unlink()


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
    """Test Scenario has _request attribute."""
    # When initialized with version_id (legacy pattern), _request is None
    scenario = Scenario(1)
    assert hasattr(scenario, '_request')
    assert scenario._request is None

    # When initialized with BaseRequest (new pattern), _request is set
    request = BaseRequest()
    scenario2 = Scenario(request)
    assert scenario2._request is request
    assert scenario2._version_id == request.request_id

    # When initialized without arguments, _request is auto-created
    scenario3 = Scenario()
    assert scenario3._request is not None
    assert isinstance(scenario3._request, BaseRequest)


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
            self._request = request  # type: DemoRequest

        def response(self, multiplier: int = 1) -> BaseResponse:
            """Return response with computed result."""
            result = DemoResult(
                computed_value=self._request.value * multiplier,
                metadata={"multiplier": str(multiplier)}
            )
            return DemoResponse(
                request_id=self._request.request_id,
                status=200,
                message="Test completed",
                response=result
            )

    # Create request and scenario
    request = DemoRequest(value=10)
    scenario = TestScenario(request)

    # Get response
    response = scenario.response(multiplier=5)

    # Verify response structure
    assert isinstance(response, DemoResponse)
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
