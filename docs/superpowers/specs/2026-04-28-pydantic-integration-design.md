# Pydantic Integration Design for or-scenario

**Date**: 2026-04-28
**Status**: Draft
**Author**: Design Specification

## Overview

Integrate Pydantic models into the `or-scenario` package to provide structured configuration and response handling for domain-specific scenarios. This design maintains the existing Register-based data storage while adding Pydantic as a control/configuration layer.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DomainScenario                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   _request   │  │   _data      │  │ _algorithm   │   │
│  │ (BaseRequest)│  │  (Register)  │  │  (Algorithm) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                   │                │            │
│         │                   │                │            │
│    ┌────▼───────────────────▼────────────────▼─────┐    │
│    │              response(*args, **kwargs)          │    │
│    │              returns BaseResponse              │    │
│    └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Separation of Concerns

| Layer | Purpose | Technology |
|-------|---------|------------|
| Configuration/Control | Scenario definition, algorithm selection, parameters | Pydantic Models |
| Data Storage | Multi-dimensional business data | Register[Parameter] |

**Pydantic Models** answer:
- Which data sources to load
- Which algorithm to use
- Algorithm parameters (tolerance, iterations, etc.)

**Register** stores:
- Actual business data (sales volumes, prices, inventory levels)

## Base Classes

### BaseRequest

```python
from pydantic import BaseModel, Field
from datetime import datetime

class BaseRequest(BaseModel):
    """Base request with common fields"""
    request_id: int = Field(default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")),
                            description="identity of the data")
```

### BaseResponse

```python
class BaseResponse(BaseModel):
    """Base response with common fields"""
    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")
```

## Base Scenario Changes

```python
# or_scenario/scenario.py
from typing import Any, Optional

class Scenario:
    # Existing attributes
    _version_id: Hashable
    _algorithm: Optional[Algorithm]
    _data: Register[Parameter]

    # Request storage (always set, either provided or default)
    _request: BaseRequest

    def __init__(self, request: Optional[BaseRequest] = None) -> None:
        """Initialize scenario with a base request.

        Args:
            request: Optional BaseRequest containing scenario configuration.
                    If None, a default BaseRequest with auto-generated request_id is created.
        """
        if request is None:
            self._request = BaseRequest()
        self._version_id = self._request.request_id
        self._algorithm = None
        self._data = Register[Parameter]()

    # Abstract response method
    def response(self, *args, **kwargs) -> BaseResponse:
        """Package results into BaseResponse. Subclasses must implement."""
        raise NotImplementedError("Subclasses must implement response()")
```

## Domain-Specific Pattern

### Directory Structure

```
domain_xyz/
├── scenario.py          # DomainScenario(Scenario)
├── dimension.py         # Product = Dimension(...)
├── parameter.py         # SalesVolume = Parameter(...)
└── config.py            # DomainRequest, DomainResponse
```

### Domain Configuration Models

```python
# domain/config.py
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Dict
from datetime import datetime

class DomainRequest(BaseRequest):
    """Domain-specific configuration"""
    data_path: Path = Field(..., description="Path to data directory")
    algorithm_type: str = Field(default="optimizer", description="Algorithm type")
    tolerance: float = Field(default=1e-6, description="Solver tolerance")

class DomainResult(BaseModel):
    """Actual computation results"""
    objective_value: float
    solution: Dict[str, float]
    iterations: int

class DomainResponse(BaseResponse):
    """Domain-specific response envelope"""
    response: DomainResult  # Override Any with specific type
```

### Domain Scenario Implementation

```python
# domain/scenario.py
from or_scenario import Scenario, BaseRequest, BaseResponse, LoadStep
from dal import JsonHandler
from .config import DomainRequest, DomainResponse, DomainResult
from .dimension import Product, Region
from .parameter import SalesVolume, Price

class DomainScenario(Scenario):
    def __init__(self, request: BaseRequest):
        # Store request (actually DomainRequest at runtime)
        self._request = request
        super().__init__(request.request_id)

        # Build load steps using domain dimensions/parameters
        self._load_steps = self._build_load_steps()

    def _build_load_steps(self) -> List[LoadStep]:
        """Build load steps based on request configuration"""
        return [
            LoadStep(
                handler=JsonHandler(),
                mapping=self._map_sales_data,
                path=self._request.data_path,
                table="sales.json"
            )
        ]

    def _map_sales_data(self, records):
        """Mapping closure with access to self"""
        for r in records:
            self.set(SalesVolume, (Product, Region),
                    (r["product_id"], r["region_id"]), r["volume"])

    def response(self, include_debug: bool = False) -> BaseResponse:
        """Package results into response"""
        result = DomainResult(
            objective_value=self._algorithm.objective_value,
            solution=self._extract_solution(),
            iterations=self._algorithm.iterations
        )

        return DomainResponse(
            request_id=self._request.request_id,
            status=200,
            message="Optimization completed",
            response=result
        )

    def _extract_solution(self) -> Dict[str, float]:
        """Extract solution data from Register"""
        # Implementation depends on domain structure
        return {}
```

## Usage Pattern

### Standard Workflow

```python
# Create request
request = DomainRequest(
    data_path=Path("data/run-001"),
    algorithm_type="optimizer",
    tolerance=1e-8
)

# Execute workflow
try:
    scenario = DomainScenario(request)
    scenario.load()
    scenario.validate()
    scenario.exec_algorithm()

    # Get response with domain-specific arguments
    response = scenario.response(include_debug=True)

except ValueError as e:
    # Build error response
    response = DomainResponse(
        request_id=request.request_id,
        status=400,
        message=f"Validation error: {e}"
    )
except Exception as e:
    # Handle other errors
    response = DomainResponse(
        request_id=request.request_id,
        status=500,
        message=f"Internal error: {e}"
    )
```

### Response Handling

```python
# Check status
if response.status == 200:
    print(f"Objective: {response.response.objective_value}")
    print(f"Solution: {response.response.solution}")
else:
    print(f"Error: {response.message}")
```

## Key Design Decisions

### 1. Generic Base Type Signatures

Domain scenarios use `BaseRequest` and `BaseResponse` in signatures, not domain-specific types:

```python
def __init__(self, request: BaseRequest) -> None:
    # Actual runtime type is DomainRequest

def response(self, *args, **kwargs) -> BaseResponse:
    # Actual return type is DomainResponse
```

This preserves signature consistency with the base `Scenario` class.

### 2. Request Storage

The request is stored as `self._request` for:
- Building load steps in `_build_load_steps()`
- Packaging response with matching `request_id`
- Accessing configuration during execution

### 3. Flexible Response Arguments

`response(*args, **kwargs)` allows each domain to define its own arguments:

```python
def response(self, result_key: str, include_metadata: bool = False) -> BaseResponse:
    # Domain-specific behavior
```

### 4. Error Handling Outside response()

The `response()` method is only called after successful execution. Error handling happens at the call site:

```python
try:
    scenario.exec_algorithm()
    response = scenario.response()  # Only on success
except Exception:
    # Build error response separately
```

### 5. Direct Import Pattern

Dimensions and parameters are imported directly, no string name resolution:

```python
from .dimension import *
from .parameter import *

# Use directly in _build_load_steps()
self.set(SalesVolume, (Product,), (1,), value)
```

## Dependencies

### Existing Dependencies (Unchanged)
- `python`: ^3.11
- `register`: ^0.1.0
- `or-algo`: ^0.2.0
- `data-access-layer`: ^0.1.0

### New Dependency
- `pydantic`: ^2.0 - Configuration and response models

## Package Exports

```python
# or_scenario/__init__.py
from .scenario import Scenario, BaseRequest, BaseResponse, LoadStep

__all__ = ["Scenario", "BaseRequest", "BaseResponse", "LoadStep"]
__version__ = "0.1.0"
```

## Testing Considerations

### Unit Tests
- Mock Pydantic models for configuration testing
- Verify request → load steps mapping
- Test response packaging

### Integration Tests
- Full workflow with temporary data files
- Verify Pydantic validation catches invalid configs
- Test error response construction

### Test Example

```python
def test_domain_scenario_with_pydantic():
    request = DomainRequest(
        data_path=Path("test/data"),
        algorithm_type="optimizer"
    )

    scenario = DomainScenario(request)
    scenario.load()

    response = scenario.response(include_debug=False)

    assert response.request_id == request.request_id
    assert response.status == 200
    assert isinstance(response.response, DomainResult)
```

## Migration Path

### For Existing Code

Existing scenarios without Pydantic integration continue to work:

```python
# Old pattern still works
class LegacyScenario(Scenario):
    def __init__(self, version_id: int):
        super().__init__(version_id)
        # Direct initialization without request
```

### New Code

New scenarios use Pydantic for configuration:

```python
# New pattern with Pydantic
class ModernScenario(Scenario):
    def __init__(self, request: BaseRequest):
        super().__init__(request.request_id)
        self._request = request
```