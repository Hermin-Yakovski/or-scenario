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
                self.set(SalesVolume, (Product,), (r["product_id"],), r["volume"])

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
    response = BaseResponse(
        request_id=request.request_id,
        status=500,
        message=str(e)
    )
```

## License

MIT
