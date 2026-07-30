# or-scenario Design Specification

**Date**: 2026-04-28
**Status**: Draft
**Author**: Design Specification

## Overview

The `or-scenario` package provides a template-based framework for Operations Research workflows. It orchestrates three concerns:

1. **Data** - Multi-dimensional parameter storage via `Register[Parameter]` from the `register` package
2. **Resources** - File-based data loading via `DataHandler` from the `dal` package
3. **Algorithms** - Solver orchestration via `Algorithm` from the `or_algo` package

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Scenario                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │   Data     │  │   Load     │  │   Algorithm  │   │
│  │  Register  │← │   Steps    │  │  (optional)  │   │
│  └────────────┘  └────────────┘  └──────┬───────┘   │
│         ↑                                    │       │
│         │                                    │       │
└─────────┼────────────────────────────────────┼───────┘
          │                                    │
          │         exec_algorithm()           │
          │         calls solve(data)          │
          └────────────────────────────────────┘
```

## Core Components

### Scenario Class

Base class for domain-specific scenarios. Subclasses define their data sources and mapping logic in `__init__`.

**Attributes:**
- `_version_id: Hashable` - Identifier for this data instance/snapshot
- `_algorithm: Optional[Algorithm]` - The algorithm to execute
- `_data: Register[Parameter]` - Multi-dimensional data storage
- `_load_steps: List[LoadStep]` - Data loading operations

### LoadStep Class (Internal)

Encapsulates a single data loading operation. Not exposed in public API.

**Attributes:**
- `handler: DataHandler` - DAL handler (JsonHandler, CsvHandler, etc.)
- `mapping: Callable[[List[Dict[str, Any]]], None]` - Function to populate Register
- `path: Path` - Directory containing the data file
- `table: str` - Filename to fetch from
- `cols: Optional[Iterable[str]]` - Columns to include
- `filter_: Optional[Callable[[Dict[str, Any]], bool]]` - Row filter function
- `limit: Optional[int]` - Maximum rows to return
- `strict: bool` - Whether to raise exceptions

## Public API

### `Scenario.__init__(version_id: Hashable)`

Initialize a new Scenario.

```python
def __init__(self, version_id: Hashable):
    self._version_id = version_id
    self._algorithm = None
    self._data = Register[Parameter]()
    self._load_steps = []
```

### `Scenario.get(param, dim, ix) -> Any`

Get a single value from the Register.

```python
def get(self, param: Parameter, dim: Tuple[Dimension, ...], ix: Tuple[int, ...]) -> Any:
    return self._data[param][dim][ix]
```

### `Scenario.set(param, dim, ix, value) -> None`

Set a single value in the Register.

```python
def set(
    self, param: Parameter, dim: Tuple[Dimension, ...], ix: Tuple[int, ...], value: Any
) -> None:
    self._data[param][dim][ix] = value
```

### `Scenario.set_algorithm(algo, *args, **kwargs) -> None`

Configure the algorithm for this scenario.

```python
def set_algorithm(self, algo: Type[Algorithm], *args, **kwargs) -> None:
    self._algorithm = algo(*args, **kwargs)
```

### `Scenario.exec_algorithm() -> None`

Execute the configured algorithm.

```python
def exec_algorithm(self) -> None:
    if self._algorithm is None:
        raise RuntimeError("Algorithm not set. Call set_algorithm() first.")
    self._algorithm.solve(self._data)
```

### `Scenario.load() -> None`

Execute all registered load steps.

```python
def load(self) -> None:
    for step in self._load_steps:
        step.run()
```

### `Scenario.validate(param=Id) -> None`

Validate the Register data.

```python
def validate(self, param: Parameter = Id) -> None:
    dim = self._data[param]
    self._data.validate(dim, raise_errors=True)
```

## Internal API

### `LoadStep.run() -> None`

Fetch data via handler and call mapping function.

```python
def run(self) -> None:
    records = self.handler.fetch(
        path=self.path,
        table=self.table,
        cols=self.cols,
        filter_=self.filter_,
        limit=self.limit,
        strict=self.strict,
    )
    self.mapping(records)
```

The mapping function is defined as a closure in the Scenario subclass and writes directly to the Scenario's `_data` Register.

## Usage Pattern

### Creating a Domain-Specific Scenario

```python
from typing import Any, Dict, Hashable, List
from pathlib import Path
from dal import JsonHandler
from register import Dimension, Index, Parameter, Id
from or_scenario import Scenario

# Define domain-specific dimensions
Product = Dimension("Product", "产品", "PROD")
Region = Dimension("Region", "区域", "REG")

# Define domain-specific parameters
SalesVolume = Parameter(1, "sales_volume", "销量", float)
Price = Parameter(2, "price", "价格", float)


class SalesScenario(Scenario):
    def __init__(self, version_id: Hashable):
        super().__init__(version_id)

        def map_sales_data(records: List[Dict[str, Any]]) -> None:
            for r in records:
                self.set(
                    SalesVolume, (Product, Region), (r["product_id"], r["region_id"]), r["volume"]
                )
                self.set(Price, (Product, Region), (r["product_id"], r["region_id"]), r["price"])

        self._load_steps = [
            LoadStep(
                handler=JsonHandler(),
                mapping=map_sales_data,
                path=Path("data") / str(version_id),
                table="sales.json",
                strict=True,
            )
        ]
```

### Using a Scenario

```python
# Create scenario instance
scenario = SalesScenario("run-2024-04-28-001")

# Load data from configured sources
scenario.load()

# Validate the data
scenario.validate()

# Configure and execute algorithm
from or_algo import Algorithm

scenario.set_algorithm(Algorithm)
scenario.exec_algorithm()
```

## Package Structure

```
or-scenario/
├── or_scenario/
│   ├── __init__.py          # Public exports (Scenario only)
│   ├── scenario.py          # Scenario and LoadStep classes
│   └── py.typed             # Type hint marker
├── tests/
│   ├── __init__.py
│   ├── test_scenario.py
│   └── fixtures/
├── docs/
│   └── superpowers/
│       └── specs/
├── README.md
├── pyproject.toml
└── LICENSE
```

## Dependencies

- **python**: ^3.11
- **register**: ^0.1.0 - Multi-dimensional data registry
- **or-algo**: ^0.2.0 - Algorithm orchestration framework
- **data-access-layer**: ^0.1.0 - Data access handlers

## Development Dependencies

- **pytest**: ^8.0 - Testing framework
- **ruff**: ^0.8 - Linting and formatting
- **mypy**: ^1.10 - Type checking
- **pytest-cov**: ^7.1.0 - Code coverage