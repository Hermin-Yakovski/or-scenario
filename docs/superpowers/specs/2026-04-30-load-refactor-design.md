# Load Method Refactor Design

**Date:** 2026-04-30
**Status:** Approved
**Author:** Claude

## Overview

Refactor the way subclasses of `Scenario` implement the `load()` method by replacing the `LoadStep` class pattern with a decorator-based approach. The new design provides cleaner syntax, better error handling control per step, and more flexibility for subclasses to control load behavior based on algorithm or parameters.

## Architecture

### Current State (To Be Removed)

- `LoadStep` class encapsulates handler + mapping + configuration
- Subclasses populate `self._load_steps` list with `LoadStep` instances
- Base class `load()` iterates through `_load_steps` and calls `step.run()`
- All steps share the same error handling context

### New Design

- Remove `LoadStep` class entirely
- Add `_load_step` static decorator to `Scenario` class
- Decorator wraps instance methods to auto-fetch data before calling mapping logic
- Subclasses define decorated methods and implement `load()` to call them in desired order
- Each decorated method has independent `strict` error handling

## Implementation

### The `_load_step` Decorator

A static method on `Scenario` that transforms mapping methods:

```python
@staticmethod
def _load_step(
    handler: DataHandler,
    path: Path,
    table: str,
    *,
    cols: Optional[Iterable[str]] = None,
    filter_: Optional[Callable[[Dict[str, Any]], bool]] = None,
    limit: Optional[int] = None,
    strict: bool = True
) -> Callable[[Callable[[Scenario, List[Dict[str, Any]], ...], None]], Callable[..., None]]:
    """Decorator that wraps a method to auto-fetch data before calling mapping logic.

    The decorated method transforms from `mapping(self, records, **kwargs)` to
    `wrapper(self, **kwargs)` - the wrapper handles data fetching internally.

    Args:
        handler: DataHandler instance for fetching data
        path: Path to data directory
        table: Table/file name
        cols: Optional column filter
        filter_: Optional row filter function
        limit: Optional max records to fetch
        strict: If True, raise exceptions. If False, log and continue.

    Returns:
        Decorator function that transforms mapping methods
    """
    def decorator(mapping: Callable[[Scenario, List[Dict[str, Any]], ...], None]) -> Callable[..., None]:
        def wrapper(self: Scenario, **kwargs) -> None:
            try:
                records = handler.fetch(
                    path=path,
                    table=table,
                    cols=cols,
                    filter_=filter_,
                    limit=limit,
                    strict=strict
                )
                mapping(self, records, **kwargs)
            except Exception:
                if strict:
                    raise
                # TODO: Log error and continue
        return wrapper
    return decorator
```

### Base Class Changes

**Remove from `Scenario` class:**
- `LoadStep` class definition
- `_load_steps: List[LoadStep]` type annotation
- `self._load_steps = []` initialization

**Add to `Scenario` class:**
- `_load_step` static decorator method (implementation above)
- `load()` remains abstract (already raises `NotImplementedError`)

**Resulting structure:**
```python
class Scenario:
    """Base class for domain-specific OR scenarios."""

    _version_id: Hashable
    _algorithm: Optional[Algorithm]
    _data: Register[Parameter]
    _request: Optional[BaseRequest]

    def __init__(self, version_id: Hashable) -> None:
        self._version_id = version_id
        self._algorithm = None
        self._data = Register[Parameter]()
        self._request = None

    @staticmethod
    def _load_step(...) -> ...:
        # Decorator implementation

    # Existing methods: get, set, set_algorithm, exec_algorithm, validate, response
```

## Subclass Usage Pattern

### Basic Example

```python
class MyScenario(Scenario):
    def __init__(self, version_id, data_dir):
        super().__init__(version_id)
        self._data_dir = data_dir

    @Scenario._load_step(JsonHandler(), Path("data"), "sales.json", strict=True)
    def load_sales(self, records):
        for r in records:
            self.set(SalesVolume, (Product,), (r["id"],), r["vol"])

    @Scenario._load_step(JsonHandler(), Path("data"), "prices.json", strict=True)
    def load_prices(self, records):
        for r in records:
            self.set(Price, (Product,), (r["id"],), r["price"])

    def load(self):
        self.load_sales()
        self.load_prices()
```

### With Controlling Parameters

The `**kwargs` pass-through allows load behavior to be influenced by algorithm or other parameters:

```python
class MyScenario(Scenario):
    def __init__(self, version_id, data_dir, algorithm_type="standard"):
        super().__init__(version_id)
        self._data_dir = data_dir
        self._algorithm_type = algorithm_type

    @Scenario._load_step(JsonHandler(), Path("data"), "sales.json", strict=True)
    def load_sales(self, records, region_filter=None):
        for r in records:
            if region_filter and r["region"] not in region_filter:
                continue
            self.set(SalesVolume, (Product,), (r["id"],), r["vol"])

    def load(self):
        # Load behavior depends on algorithm type
        if self._algorithm_type == "premium":
            self.load_sales(region_filter=["US", "EU"])
        else:
            self.load_sales()
```

### With Optional Data

```python
class MyScenario(Scenario):
    @Scenario._load_step(JsonHandler(), Path("data"), "sales.json", strict=True)
    def load_sales(self, records):
        # Must succeed - critical data
        for r in records:
            self.set(SalesVolume, (Product,), (r["id"],), r["vol"])

    @Scenario._load_step(JsonHandler(), Path("data"), "optional.json", strict=False)
    def load_optional(self, records):
        # Nice to have - not critical
        for r in records:
            self.set(ExtraData, (Product,), (r["id"],), r["extra"])

    def load(self):
        self.load_sales()      # If this fails, load() raises immediately
        self.load_optional()   # Only runs if load_sales() succeeded
```

## Error Handling

**Per-step strict mode:**

- `strict=True` (default): Exceptions propagate immediately, subsequent steps don't run
- `strict=False`: Exceptions are caught and logged (TODO), execution continues

This provides fine-grained control over which data is critical vs optional.

## Testing Strategy

**Remove old tests:**
- `test_loadstep_init()`
- `test_loadstep_init_with_defaults()`
- `test_loadstep_run()`

**Add new tests:**
- Decorator transforms method signature correctly
- Decorator fetches data via handler and calls mapping
- `strict=True` propagates exceptions
- `strict=False` continues on error
- `**kwargs` are passed through to mapping function
- Integration test with full scenario

**Update existing tests:**
- `test_scenario_load()` - Test that decorated methods are called in order
- Integration tests - Convert to use new decorator pattern

## Implementation Plan

1. Commit this design document
2. Delete `LoadStep` class from `scenario.py`
3. Delete `_load_steps` type annotation and initialization
4. Add `_load_step` static decorator to `Scenario` class
5. Update tests - remove old, add new
6. Run full test suite to verify

## Compatibility

**Breaking change:** This is a breaking change for existing code using `LoadStep` and `_load_steps`. However, the library is in early development (v0.1.0), so this is an acceptable cost for a cleaner API.
