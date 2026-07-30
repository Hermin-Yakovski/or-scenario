# Design: Generic Register Refactor

**Date:** 2024-06-08
**Author:** Design discussion with user
**Status:** Proposed

## Overview

Refactor the `Register` generic class to remove the `Parameter` type bound, enabling `Register[Var]` usage where `Var` is not a `Parameter`. Move Parameter-specific validation logic from `Register.validate()` to `Scenario.validate()`.

## Problem Statement

1. `Register` is currently bounded to `Parameter`: `K = TypeVar("K", bound=Parameter)`
2. `or_algo` package needs `Register[Var]` where `Var` is not a `Parameter`
3. This causes mypy errors and code inconsistency
4. `Register.validate()` contains Parameter-specific logic that doesn't belong in a generic container

## Current State

### `register/register.py`

- `K = TypeVar("K", bound=Parameter)` - enforces Parameter bound
- `Register.validate(dim: DimensionAsKey, raise_errors: bool)` - validates Parameter-specific logic

### `or_scenario/scenario.py`

- `Scenario._data: Register[Parameter]` - definitely contains Parameters
- `Scenario.validate(param: Parameter = Id)` - delegates to `Register.validate()`
- Uses `Id` parameter as reference dimension for validating all other parameters

## Design

### Changes to `register/register.py`

1. **Remove type bound:**
   ```python
   # Before
   K = TypeVar("K", bound=Parameter)

   # After
   K = TypeVar("K")
   ```

2. **Remove validate() method:** Delete lines 110-193 containing the entire `validate()` method

### Changes to `or_scenario/scenario.py`

1. **Inline validation logic in `Scenario.validate()`:**
   - Retrieve reference dimension: `dim = self._data[param]`
   - Iterate through all keys in `self._data`
   - For each key, iterate through its dimensions
   - For each dimension, iterate through indices
   - Perform validation checks:
     - Index length matches dimension length
     - Each index exists in reference dimension
     - Value matches expected `vtype` (handling scalar, iterable, Dimension reference)

2. **Preserve behavior:**
   - Default parameter: `Id`
   - Raise `DimensionError` or `ValidationError` on validation failure
   - Always raise exceptions (current `raise_errors=True` behavior)

## Data Flow

### Validation Flow (After Refactor)

```
User calls scenario.validate()
  ↓
Get reference dimension: dim = self._data[Id]
  ↓
For each key in self._data:
  For each dimension in key:
    For each index in dimension:
      - Validate index length
      - Validate index exists in dim
      - Validate value type matches key.vtype
  ↓
Raise DimensionError or ValidationError on failure
```

## Error Handling

**Preserve existing behavior:**

- `DimensionError`: Index length mismatch or invalid index reference
- `ValidationError`: Value doesn't match expected `vtype`
- Exception types: Continue using `DimensionError` and `ValidationError` from `register` package
- Logging: Use `or_scenario` logger instead of `register` logger

## Implementation Notes

### Validation Logic Details

The inlined validation logic must handle:

1. **Index length validation:** `len(dimension) != len(index)` → `DimensionError`
2. **Index existence validation:** Check `(ix,) in dim[d,]` for each index component
3. **Type validation for `key.vtype`:**
   - `None` or `Any`: Skip type check
   - `list`/`set`/`tuple`: Validate iterable type and element types
   - `Dimension` reference: Validate value exists in dimension
   - Scalar type: Validate `isinstance(value, key.vtype)`

### Import Changes

**`or_scenario/scenario.py`** needs additional imports:
```python
from register.exception import DimensionError, ValidationError
from typing import get_origin, get_args
import logging

logger = logging.getLogger("or_scenario")
```

## Testing

### Test Files to Update

1. **`or_scenario` tests:** Verify `Scenario.validate()` behavior preserved
2. **`register` tests:** Remove tests for `Register.validate()` method
3. **Integration tests:** Verify `or_algo` can use `Register[Var]` without mypy errors

### Test Cases

- Index length mismatch detection
- Invalid index reference detection
- Type mismatch: scalar types
- Type mismatch: iterable types
- Type mismatch: Dimension reference types
- Optional `vtype` (Any) passes validation
- Default parameter (`Id`) behavior
- Custom parameter as reference

## Benefits

1. **Type flexibility:** `Register` can work with any key type having `.vtype` attribute
2. **Separation of concerns:** Validation logic moves to where Parameter semantics are known
3. **No runtime impact:** Behavior preserved, only type system improved
4. **Enables `Register[Var]`:** Removes mypy errors in `or_algo` package

## Risks

1. **Breaking change:** If other code depends on `Register.validate()`, will break
   - Mitigation: User confirmed validation is exclusively used by `Scenario`
2. **Logger location:** Logging moves from `register` to `or_scenario`
   - Impact: Minimal, just a logger name change

## Open Questions

None identified.

## Dependencies

- `register` package source location (user has access to `D:/github/register/`)
- `or_algo` package (already using `Var` with `vtype` attribute)