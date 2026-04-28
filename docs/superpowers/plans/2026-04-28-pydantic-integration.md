# Pydantic Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Pydantic integration to or-scenario package for structured configuration and response handling.

**Architecture:** Base Scenario class stores optional BaseRequest and defines abstract response() method. Domain scenarios accept BaseRequest in __init__, use it for configuration, and return BaseResponse from response().

**Tech Stack:** Python 3.11+, Pydantic 2.0+, poetry, pytest, existing or-scenario infrastructure

---

## File Structure

```
or-scenario/
├── or_scenario/
│   ├── __init__.py          # Update: export BaseRequest, BaseResponse
│   ├── scenario.py          # Modify: add BaseRequest, BaseResponse, _request, response()
│   └── py.typed             # No change
├── tests/
│   ├── __init__.py          # No change
│   ├── test_scenario.py     # Modify: add Pydantic integration tests
│   └── fixtures/            # No change
├── pyproject.toml           # Modify: add pydantic dependency
├── README.md                # No change
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-28-pydantic-integration-design.md  # No change (already exists)
```

---

## Task 1: Add Pydantic dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pydantic to dependencies**

```toml
[tool.poetry.dependencies]
python = "^3.11"
register = "^0.1.0"
or-algo = "^0.2.0"
data-access-layer = "^0.1.0"
pydantic = "^2.0"  # Add this line
```

- [ ] **Step 2: Install new dependency**

Run: `poetry lock && poetry install`
Expected: Dependencies installed successfully, pydantic added to virtual environment

- [ ] **Step 3: Verify pydantic is importable**

Run: `poetry run python -c "import pydantic; print(pydantic.__version__)"`
Expected: Version number printed (e.g., "2.x.x")

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "deps: add pydantic ^2.0 dependency"
```

---

## Task 2: Create BaseRequest and BaseResponse classes

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Add imports for datetime and pydantic**

```python
# or_scenario/scenario.py
from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple, Type
from datetime import datetime  # Add this

from dal import DataHandler
from or_algo import Algorithm
from register import Dimension, Id, Parameter, Register
from pydantic import BaseModel, Field, Any  # Add this
```

- [ ] **Step 2: Write failing test for BaseRequest**

```python
# tests/test_scenario.py
from or_scenario import BaseRequest
from datetime import datetime

def test_baserequest_creation():
    """Test BaseRequest can be created with default request_id."""
    request = BaseRequest()
    assert isinstance(request.request_id, int)
    assert len(str(request.request_id)) == 14  # YYMMDDHHMMSSFF format
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_baserequest_creation -v`
Expected: FAIL with "BaseRequest not defined" or ImportError

- [ ] **Step 4: Implement BaseRequest class**

```python
# or_scenario/scenario.py - add after imports, before LoadStep class

class BaseRequest(BaseModel):
    """Base request with common fields."""
    request_id: int = Field(default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")),
                            description="identity of the data")
```

- [ ] **Step 5: Write failing test for BaseResponse**

```python
# tests/test_scenario.py
from or_scenario import BaseResponse

def test_baseresponse_creation():
    """Test BaseResponse can be created with all fields."""
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
    custom_data = {"key": "value", "number": 42}
    response = BaseResponse(
        request_id=12345,
        status=200,
        message="Success",
        response=custom_data
    )
    assert response.response == custom_data
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/test_scenario.py::test_baseresponse_creation -v`
Expected: FAIL with "BaseResponse not defined" or ImportError

- [ ] **Step 7: Implement BaseResponse class**

```python
# or_scenario/scenario.py - add after BaseRequest class

class BaseResponse(BaseModel):
    """Base response with common fields."""
    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/test_scenario.py::test_baserequest_creation tests/test_scenario.py::test_baseresponse_creation tests/test_scenario.py::test_baseresponse_with_response_field -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add BaseRequest and BaseResponse pydantic models"
```

---

## Task 3: Add _request attribute to Scenario class

**Files:**
- Modify: `or_scenario/scenario.py`
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Write failing test for _request attribute**

```python
# tests/test_scenario.py
def test_scenario_request_attribute():
    """Test Scenario has _request attribute initialized to None."""
    scenario = Scenario(1)
    assert hasattr(scenario, '_request')
    assert scenario._request is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_scenario_request_attribute -v`
Expected: FAIL (scenario doesn't have _request attribute yet)

- [ ] **Step 3: Add _request attribute to Scenario class**

```python
# or_scenario/scenario.py - modify Scenario class

class Scenario:
    """Base class for domain-specific OR scenarios."""

    _version_id: Hashable
    _algorithm: Optional[Algorithm]
    _data: Register[Parameter]
    _load_steps: List[LoadStep]
    _request: Optional[BaseRequest]  # Add this line

    def __init__(self, version_id: Hashable) -> None:
        self._version_id = version_id
        self._algorithm = None
        self._data = Register[Parameter]()
        self._load_steps = []
        self._request = None  # Add this line
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_request_attribute -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add _request attribute to Scenario class"
```

---

## Task 4: Add abstract response() method to Scenario class

**Files:**
- Modify: `or_scenario/scenario.py`
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Write failing test for response() method**

```python
# tests/test_scenario.py
def test_scenario_response_not_implemented():
    """Test Scenario.response() raises NotImplementedError."""
    scenario = Scenario(1)
    with pytest.raises(NotImplementedError, match="Subclasses must implement response"):
        scenario.response()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_scenario_response_not_implemented -v`
Expected: FAIL (scenario doesn't have response method, or doesn't raise NotImplementedError)

- [ ] **Step 3: Add response() method to Scenario class**

```python
# or_scenario/scenario.py - add to Scenario class, after validate() method

    def response(self, *args: Any, **kwargs: Any) -> BaseResponse:
        """Package results into BaseResponse. Subclasses must implement."""
        raise NotImplementedError("Subclasses must implement response()")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_response_not_implemented -v`
Expected: PASS

- [ ] **Step 5: Test that response() accepts arbitrary arguments**

```python
# tests/test_scenario.py
def test_scenario_response_accepts_any_arguments():
    """Test response() signature accepts *args and **kwargs."""
    scenario = Scenario(1)
    # This should not raise TypeError for argument signature
    with pytest.raises(NotImplementedError):
        scenario.response("arg1", "arg2", key1="value1", key2="value2")
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_response_accepts_any_arguments -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add abstract response() method to Scenario class"
```

---

## Task 5: Update public API exports

**Files:**
- Modify: `or_scenario/__init__.py`

- [ ] **Step 1: Write failing test for public API exports**

```python
# tests/test_scenario.py
def test_public_api_exports():
    """Test BaseRequest and BaseResponse are exported in public API."""
    import or_scenario
    assert hasattr(or_scenario, 'BaseRequest')
    assert hasattr(or_scenario, 'BaseResponse')
    assert 'BaseRequest' in or_scenario.__all__
    assert 'BaseResponse' in or_scenario.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_public_api_exports -v`
Expected: FAIL (BaseRequest/BaseResponse not in __all__)

- [ ] **Step 3: Update __init__.py to export new classes**

```python
# or_scenario/__init__.py
"""or-scenario: Template framework for Operations Research workflows."""

from .scenario import BaseRequest, BaseResponse, Scenario

__all__ = ["Scenario", "BaseRequest", "BaseResponse"]
__version__ = "0.1.0"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_public_api_exports -v`
Expected: PASS

- [ ] **Step 5: Verify imports work from public API**

Run: `poetry run python -c "from or_scenario import BaseRequest, BaseResponse; print('Imports work')"`
Expected: "Imports work"

- [ ] **Step 6: Commit**

```bash
git add or_scenario/__init__.py tests/test_scenario.py
git commit -m "feat: export BaseRequest and BaseResponse in public API"
```

---

## Task 6: Add integration test with Pydantic models

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Write domain-specific request/response models for testing**

```python
# tests/test_scenario.py
from pydantic import BaseModel
from typing import Dict

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
```

- [ ] **Step 2: Write integration test with domain scenario**

```python
# tests/test_scenario.py
def test_scenario_pydantic_integration():
    """Integration test: Scenario with Pydantic request/response."""
    # Create a test scenario that uses Pydantic models
    class TestScenario(Scenario):
        def __init__(self, request: BaseRequest):
            self._request = request  # type: TestRequest
            super().__init__(request.request_id)

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
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_pydantic_integration -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: add Pydantic integration test"
```

---

## Task 7: Test backward compatibility (scenarios without Pydantic)

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Write test for legacy scenario pattern**

```python
# tests/test_scenario.py
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_backward_compatibility -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: verify backward compatibility with non-Pydantic scenarios"
```

---

## Task 8: Run full test suite and verify

**Files:**
- All files

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/test_scenario.py -v`
Expected: All tests PASS

- [ ] **Step 2: Run tests with coverage**

Run: `pytest tests/test_scenario.py --cov=or_scenario --cov-report=term-missing`
Expected: All tests PASS, good coverage (no critical gaps)

- [ ] **Step 3: Run type checking**

Run: `poetry run mypy or_scenario/`
Expected: No type errors (may need to adjust for pydantic dynamic types)

- [ ] **Step 4: Run linting**

Run: `poetry run ruff check or_scenario/ tests/`
Expected: No linting errors

- [ ] **Step 5: Fix any issues found**

If any checks fail, fix issues and re-run until all pass.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "test: verify all tests, coverage, type checking, and linting pass"
```

---

## Task 9: Update README with Pydantic usage example

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Pydantic integration section to README**

```markdown
# or-scenario

Template framework for Operations Research scenarios.

## Overview

`or-scenario` provides a base class for orchestrating data, resources, and algorithms in OR workflows. It integrates:

- **register** - Multi-dimensional data storage
- **dal** - File-based data loading (JSON, CSV, pickle, XLSX)
- **or-algo** - Algorithm orchestration
- **pydantic** - Structured configuration and response handling

## Installation

```bash
poetry add or-scenario
```

## Quick Start

### Basic Usage (without Pydantic)

```python
from pathlib import Path
from dal import JsonHandler
from register import Dimension, Parameter
from or_scenario import Scenario

Product = Dimension("Product", "产品", "PROD")
SalesVolume = Parameter(1, "sales_volume", "销量", float)

class MyScenario(Scenario):
    def __init__(self, version_id):
        super().__init__(version_id)

        def map_data(records):
            for r in records:
                self.set(SalesVolume, (Product,),
                        (r["product_id"],), r["volume"])

        self._load_steps = [LoadStep(
            handler=JsonHandler(),
            mapping=map_data,
            path=Path("data") / str(version_id),
            table="sales.json"
        )]

scenario = MyScenario("run-001")
scenario.load()
scenario.validate()
```

### Pydantic Integration

For structured configuration and response handling, use Pydantic models:

```python
from pathlib import Path
from pydantic import BaseModel, Field
from or_scenario import Scenario, BaseRequest, BaseResponse

class DomainRequest(BaseRequest):
    """Domain-specific configuration."""
    data_path: Path = Field(..., description="Path to data directory")
    algorithm_type: str = Field(default="optimizer")

class DomainResult(BaseModel):
    """Computation results."""
    objective_value: float
    solution: dict

class DomainResponse(BaseResponse):
    """Domain-specific response."""
    response: DomainResult

class DomainScenario(Scenario):
    def __init__(self, request: BaseRequest):
        self._request = request  # type: DomainRequest
        super().__init__(request.request_id)
        self._load_steps = self._build_load_steps()

    def response(self, include_debug: bool = False) -> BaseResponse:
        """Package results into response."""
        result = DomainResult(
            objective_value=100.0,
            solution={"x": 10, "y": 20}
        )
        return DomainResponse(
            request_id=self._request.request_id,
            status=200,
            message="Optimization completed",
            response=result
        )

# Usage
try:
    request = DomainRequest(data_path=Path("data/run-001"))
    scenario = DomainScenario(request)
    scenario.load()
    scenario.validate()
    scenario.exec_algorithm()
    response = scenario.response()
except Exception as e:
    response = DomainResponse(
        request_id=request.request_id,
        status=500,
        message=str(e)
    )
```

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add Pydantic integration section to README"
```

---

## Self-Review Results

**1. Spec Coverage:**
- ✓ BaseRequest with request_id and default factory
- ✓ BaseResponse with request_id, status, message, timestamp, response fields
- ✓ Scenario._request attribute (Optional[BaseRequest])
- ✓ Scenario.response(*args, **kwargs) -> BaseResponse abstract method
- ✓ Public API exports (BaseRequest, BaseResponse)
- ✓ Pydantic dependency added
- ✓ Backward compatibility maintained
- ✓ Tests for all new functionality
- ✓ Documentation updates

**2. Placeholder Scan:**
- ✓ No "TBD", "TODO", or similar placeholders
- ✓ All steps contain actual code
- ✓ All commands are complete with expected outputs
- ✓ No "similar to" references

**3. Type Consistency:**
- ✓ BaseRequest and BaseResponse names consistent throughout
- ✓ Method signatures match (response(*args, **kwargs))
- ✓ Import paths are consistent
- ✓ Field names match spec (request_id, status, message, timestamp, response)

**4. Task Decomposition:**
- ✓ Each step is 2-5 minutes
- ✓ TDD pattern: fail test → implement → pass
- ✓ Frequent commits
- ✓ Clear file boundaries

**Plan complete and saved to `docs/superpowers/plans/2026-04-28-pydantic-integration.md`.**
