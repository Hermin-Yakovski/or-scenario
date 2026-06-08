# tests/test_scenario.py
import pytest
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock
from datetime import datetime
from data_access_layer import JsonHandler, DataHandler
from or_scenario import Scenario
from or_scenario.schema import BaseRequest, BaseResponse
from register import Register
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


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
    """Test Scenario can be initialized."""
    scenario = Scenario()
    assert scenario._version_id == scenario._request.request_id
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
        def __init__(self):
            super().__init__()
            self.mapping_called = False
            self.received_records = None

        @Scenario._load_step(JsonHandler(), Path("test"), "data.json")
        def load_data(self, records):
            self.mapping_called = True
            self.received_records = records

    # Create scenario and verify decorated method exists
    scenario = DecoratorTestScenario()
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
    scenario = DecoratorTestScenario()
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

    scenario = DecoratorTestScenario()

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

    scenario = DecoratorTestScenario()

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

    scenario = DecoratorTestScenario()

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
    scenario = Scenario()
    scenario._data[SalesVolume][(Product,)][(1,)] = 100.0
    result = scenario.get(SalesVolume, (Product,), (1,))
    assert result == 100.0


def test_scenario_set():
    """Test Scenario.set() sets values in _data."""
    from register import Dimension, Parameter
    Product = Dimension("Product", "产品", "PROD")
    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    scenario = Scenario()
    scenario.set(SalesVolume, (Product,), (1,), 150.0)
    result = scenario.get(SalesVolume, (Product,), (1,))
    assert result == 150.0


def test_scenario_set_algorithm():
    """Test Scenario.set_algorithm() creates algorithm instance."""
    from or_algo import Algorithm
    # Check if Algorithm is the real class (not a mock from test_get_sol_table_name)
    if hasattr(Algorithm, '__module__') and 'or_algo' in Algorithm.__module__:
        scenario = Scenario()
        scenario.set_algorithm(Algorithm)
        assert scenario._algorithm is not None
        assert isinstance(scenario._algorithm, Algorithm)
    else:
        # Algorithm is mocked, just verify the set_algorithm method works
        scenario = Scenario()
        scenario.set_algorithm(Algorithm)
        assert scenario._algorithm is not None


def test_scenario_exec_algorithm():
    """Test Scenario.exec_algorithm() calls algorithm.solve()."""
    from or_algo import Algorithm
    # Check if Algorithm is the real class (not a mock from test_get_sol_table_name)
    if hasattr(Algorithm, '__module__') and 'or_algo' in Algorithm.__module__:
        scenario = Scenario()
        mock_algo = MagicMock(spec=Algorithm)
        scenario._algorithm = mock_algo
        scenario.exec_algorithm()
        mock_algo.solve.assert_called_once_with(scenario._data)
    else:
        # Algorithm is mocked, create a simple mock for testing
        scenario = Scenario()
        mock_algo = MagicMock()
        scenario._algorithm = mock_algo
        scenario.exec_algorithm()
        mock_algo.solve.assert_called_once_with(scenario._data)


def test_scenario_exec_algorithm_not_set():
    """Test Scenario.exec_algorithm() raises error when algorithm not set."""
    scenario = Scenario()
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

    scenario = LoadTestScenario()
    scenario.load()

    assert run_order == ["step1", "step2"]


def test_scenario_validate():
    """Test Scenario.validate() validates data with default parameter."""
    from register import Id, Index
    scenario = Scenario()
    scenario._data[Id][(Index,)][(1,)] = 1
    scenario.validate()


def test_scenario_validate_default_param():
    """Test Scenario.validate() with explicit default parameter."""
    from register import Id, Index
    scenario = Scenario()
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
        scenario = TestScenario()
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
    from or_scenario.schema import BaseResponse
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
    from or_scenario.schema import BaseResponse
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
    # When initialized without arguments, _request is auto-created
    scenario = Scenario()
    assert hasattr(scenario, '_request')
    assert scenario._request is not None
    assert isinstance(scenario._request, BaseRequest)

    # When initialized with BaseRequest (explicit pattern), _request is set
    request = BaseRequest()
    scenario2 = Scenario(request)
    assert scenario2._request is request
    assert scenario2._version_id == request.request_id


def test_scenario_response_not_implemented():
    """Test Scenario.response() raises NotImplementedError."""
    scenario = Scenario()
    with pytest.raises(NotImplementedError, match="Subclasses must implement response"):
        scenario.response()


def test_scenario_load_not_implemented():
    """Test Scenario.load() raises NotImplementedError."""
    scenario = Scenario()
    with pytest.raises(NotImplementedError, match="Subclasses must implement load"):
        scenario.load()


def test_scenario_response_accepts_any_arguments():
    """Test response() signature accepts *args and **kwargs."""
    scenario = Scenario()
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
            super().__init__(request)
            # self._request is already set by parent, preserving DemoRequest type

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
    """Test that scenarios work with default BaseRequest."""
    # Scenario without custom __init__ - uses default BaseRequest
    class SimpleScenario(Scenario):
        def __init__(self):
            super().__init__()
            self.custom_value = 100

        def custom_method(self) -> int:
            return self.custom_value * 2

    # Create and use simple scenario
    scenario = SimpleScenario()
    assert scenario._version_id == scenario._request.request_id
    assert scenario._request is not None
    assert scenario.custom_method() == 200

    # response() should still raise NotImplementedError
    with pytest.raises(NotImplementedError):
        scenario.response()


def test_dump_method_exists():
    """Test that dump() method exists and has correct signature."""
    from register import Dimension, Parameter
    import inspect

    scenario = Scenario()

    # Verify method exists
    assert hasattr(scenario, "dump")
    assert callable(scenario.dump)

    # Verify signature (self is not included for bound methods)
    sig = inspect.signature(scenario.dump)
    params = list(sig.parameters.keys())
    assert "session" in params
    assert "params" in params
    assert "dimension" in params
    assert "fact" in params
    # index parameter should NOT exist in new signature
    assert "index" not in params


def test_dump_skips_missing_parameters():
    """Test that dump() skips parameters that don't exist in Register."""
    from register import Dimension, Parameter
    from unittest.mock import MagicMock, patch

    scenario = Scenario()
    scenario._version_id = 123

    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    Price = Parameter(2, "price", "价格", float)
    TestDimension = Dimension("Test", "", "")

    # Only add SalesVolume to Register, not Price
    scenario.set(SalesVolume, (TestDimension,), (1,), 100.0)

    mock_session = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_query.filter.return_value.delete.return_value = 0
    mock_session.query.return_value = mock_query

    scenario.dump(
        mock_session,
        {SalesVolume, Price},  # Both params passed, but only SalesVolume exists
        (TestDimension,),
        fact=False
    )

    # Should only insert SalesVolume (Price should be skipped)
    assert mock_session.query.called
    assert mock_session.add_all.called


def test_dump_deletes_existing_version_records():
    """Test that dump() deletes existing records with same version_id."""
    from register import Dimension, Parameter
    from unittest.mock import MagicMock

    scenario = Scenario()
    scenario._version_id = 123

    mock_session = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_query.filter.return_value.delete.return_value = 0
    mock_session.query.return_value = mock_query

    scenario.dump(
        mock_session,
        set(),
        (Dimension("Test", "", ""),),
        fact=False
    )

    # Verify query was called for delete operation
    assert mock_session.query.called
    mock_query.filter.assert_called_once()


def test_dump_uses_fact_table_when_fact_true():
    """Test that dump() uses fact table and snapshot_id when fact=True."""
    from register import Dimension, Parameter
    from unittest.mock import MagicMock, patch
    import importlib

    TestDimension = Dimension("Test", "", "")

    mock_session = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_query.filter.return_value.delete.return_value = 0
    mock_session.query.return_value = mock_query

    with patch('or_scenario.orm.generate_fact_table') as mock_fact_table:
        mock_table_cls = MagicMock()
        mock_fact_table.return_value = mock_table_cls

        # Reload scenario module to apply the patch
        import or_scenario.scenario
        importlib.reload(or_scenario.scenario)
        Scenario = or_scenario.scenario.Scenario

        scenario = Scenario()
        scenario._version_id = 123

        scenario.dump(
            mock_session,
            set(),
            (TestDimension,),
            fact=True
        )

        # Verify generate_fact_table was called
        mock_fact_table.assert_called_once()
        # Verify filter used snapshot_id column
        mock_query.filter.assert_called_once()

        # Reload scenario module to restore original state
        importlib.reload(or_scenario.scenario)


def test_dump_inserts_records_for_all_indexes():
    """Test that dump() inserts records for all indexes in Register."""
    from register import Dimension, Parameter
    from unittest.mock import MagicMock, patch

    scenario = Scenario()
    scenario._version_id = 123

    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    TestDimension = Dimension("Test", "", "")

    # Add multiple indexes for same parameter/dimension
    scenario.set(SalesVolume, (TestDimension,), (1,), 100.0)
    scenario.set(SalesVolume, (TestDimension,), (2,), 200.0)
    scenario.set(SalesVolume, (TestDimension,), (3,), 300.0)

    mock_session = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_query.filter.return_value.delete.return_value = 0
    mock_session.query.return_value = mock_query

    scenario.dump(
        mock_session,
        {SalesVolume},
        (TestDimension,),
        fact=False
    )

    # Verify add_all was called for insert
    assert mock_session.add_all.called
    # Verify all 3 records were inserted
    call_args = mock_session.add_all.call_args[0][0]
    assert len(call_args) == 3


def test_scenario_as_frames_empty():
    """Test Scenario.as_frames() returns empty dict for empty scenario."""
    from register import Id, Index

    scenario = Scenario()
    frames = scenario.as_frames()
    assert frames == {}


def test_scenario_as_frames_single_value():
    """Test Scenario.as_frames() with single value."""
    from register import Id, Index

    scenario = Scenario()
    scenario._data[Id][(Index,)][(1,)] = 42
    frames = scenario.as_frames()
    assert len(frames) == 1
    df = frames[(Index,)]
    assert df.iloc[0]["id"] == 42


def test_scenario_as_frames_multiple_parameters():
    """Test Scenario.as_frames() with multiple parameters."""
    from register import Id, Name, Index

    scenario = Scenario()
    scenario._data[Id][(Index,)][(1,)] = 42
    scenario._data[Name][(Index,)][(1,)] = "test_name"
    frames = scenario.as_frames()
    df = frames[(Index,)]
    assert df.iloc[0]["id"] == 42
    assert df.iloc[0]["name"] == "test_name"


def test_scenario_as_frames_display_cn():
    """Test Scenario.as_frames() with Chinese names."""
    from register import Id, Index

    scenario = Scenario()
    scenario._data[Id][(Index,)][(1,)] = 42
    frames = scenario.as_frames(display_cn=True)
    df = frames[(Index,)]
    assert "下标" in df.columns
    assert df.iloc[0]["ID"] == 42


def test_scenario_as_frames_multiple_dimensions():
    """Test Scenario.as_frames() with multiple dimensions."""
    from register import Id, Dimension

    dim1 = Dimension("test1", "测试1", "T1")
    dim2 = Dimension("test2", "测试2", "T2")
    scenario = Scenario()
    scenario._data[Id][(dim1, dim2)][(1, 10)] = 42
    frames = scenario.as_frames()
    df = frames[(dim1, dim2)]
    assert df.iloc[0]["test1"] == 1
    assert df.iloc[0]["test2"] == 10
    assert df.iloc[0]["id"] == 42


def test_scenario_as_frames_multiple_dimension_keys_for_same_parameter():
    """Test Scenario.as_frames() with same parameter, different dimensions."""
    from register import Id, Dimension

    dim1 = Dimension("test1", "测试1", "T1")
    dim2 = Dimension("test2", "测试2", "T2")
    scenario = Scenario()
    # Same parameter (Id) with different dimension combinations
    scenario._data[Id][(dim1,)][(1,)] = 100
    scenario._data[Id][(dim2,)][(2,)] = 200
    frames = scenario.as_frames()
    # Should have two separate frames
    assert len(frames) == 2
    # Check first frame
    df1 = frames[(dim1,)]
    assert df1.iloc[0]["test1"] == 1
    assert df1.iloc[0]["id"] == 100
    # Check second frame
    df2 = frames[(dim2,)]
    assert df2.iloc[0]["test2"] == 2
    assert df2.iloc[0]["id"] == 200
