# Design: Move as_frames() from Register to Scenario

**Date:** 2024-06-08
**Author:** Design discussion with user
**Status:** Proposed

## Overview

Move the `as_frames()` method from `Register` to `Scenario`, following the same pattern as the `validate()` refactor. This removes Parameter-specific logic and pandas dependency from the generic `Register` class, making it lighter and more focused.

## Problem Statement

1. `Register.as_frames()` contains Parameter-specific logic (uses `key.name`, `key.name_cn`)
2. Register package depends on pandas solely for this one method
3. Consistency with `validate()` refactor - Parameter-specific logic should live in `Scenario`

## Current State

### `register/register.py`

- `as_frames(display_cn: bool = False)` method (lines 77-106)
- Depends on `import pandas as pd`
- Uses `key.name` and `key.name_cn` attributes (Parameter-specific)
- Returns `dict[tuple[Dimension, ...], pd.DataFrame]`

### `register/pyproject.toml`

- `pandas = "^2.0"` dependency
- `pandas-stubs = "^2.0"` dev dependency

### `or_scenario/scenario.py`

- No `as_frames()` method currently

### `or_scenario/pyproject.toml`

- No pandas dependency

## Design

### Changes to `register` package

1. **`register/register.py`**:
   - Remove `as_frames()` method (lines 77-106)
   - Remove `import pandas as pd` (line 5)

2. **`register/pyproject.toml`**:
   - Remove `pandas = "^2.0"` from dependencies
   - Remove `pandas-stubs = "^2.0"` from dev dependencies

3. **`register/tests/test_register.py`**:
   - Remove 6 `as_frames()` tests (lines 208-297):
     - `test_as_frames_empty_register`
     - `test_as_frames_single_value`
     - `test_as_frames_multiple_parameters`
     - `test_as_frames_display_cn`
     - `test_as_frames_multiple_dimensions`
     - `test_as_frames_multiple_dimension_keys_for_same_parameter`

### Changes to `or_scenario` package

1. **`or_scenario/scenario.py`**:
   - Add `import pandas as pd`
   - Add `as_frames(display_cn: bool = False)` method with identical logic to current Register implementation
   - Method signature: `def as_frames(self, display_cn: bool = False) -> dict[tuple[Dimension, ...], pd.DataFrame]`

2. **`or_scenario/pyproject.toml`**:
   - Add `pandas = "^2.0"` to dependencies
   - Add `pandas-stubs = "^2.0"` to dev dependencies (for mypy)

3. **`tests/test_scenario.py`**:
   - Port 6 tests from register package
   - Rename tests to use `test_scenario_as_frames_*` naming convention
   - Update to use `Scenario` instance instead of `Register`

## Implementation Details

### as_frames() Method Implementation

The method to add to `Scenario`:

```python
def as_frames(self, display_cn: bool = False) -> dict[tuple[Dimension, ...], pd.DataFrame]:
    """Convert scenario data to pandas DataFrames.

    Args:
        display_cn: If True, use Chinese names; otherwise use English names

    Returns:
        Dictionary mapping dimension tuples to DataFrames. Each DataFrame has
        columns for each dimension followed by columns for each parameter.
    """
    frames: dict[tuple[Dimension, ...], pd.DataFrame] = {}
    rows: dict[tuple[Dimension, ...], dict[tuple[int, ...], list[Any]]] = {}
    columns: dict[tuple[Dimension, ...], list[str]] = {}

    for key in self._data:
        col: str = key.name_cn if display_cn else key.name
        for dimension in self._data[key]:
            if dimension not in rows:
                rows[dimension] = {}
                columns[dimension] = []
            if col not in columns[dimension]:
                for index in rows[dimension]:
                    rows[dimension][index].append(None)
                columns[dimension].append(col)
            for index, value in self._data[key][dimension].items():
                if index not in rows[dimension]:
                    rows[dimension][index] = [None for _ in columns[dimension]]
                rows[dimension][index][-1] = value

    for dimension in columns:
        dataframe_columns: list[str] = [
            d.name_cn if display_cn else d.name for d in dimension
        ] + columns[dimension]
        dataframe_rows: list[list[Any]] = []
        for index in rows[dimension]:
            dataframe_rows.append([i for i in index] + rows[dimension][index])
        frames[dimension] = pd.DataFrame(dataframe_rows, columns=dataframe_columns)

    return frames
```

### Test Migration Example

**Before (register package):**
```python
def test_as_frames_single_value():
    reg = Register()
    dim = Dimension("test", "测试", "TST")
    reg[Id][(dim,)][(1,)] = 42
    frames = reg.as_frames()
    assert len(frames) == 1
    df = frames[(dim,)]
    assert df.iloc[0]["id"] == 42
```

**After (or_scenario package):**
```python
def test_scenario_as_frames_single_value():
    scenario = Scenario()
    dim = Dimension("test", "测试", "TST")
    scenario._data[Id][(dim,)][(1,)] = 42
    frames = scenario.as_frames()
    assert len(frames) == 1
    df = frames[(dim,)]
    assert df.iloc[0]["id"] == 42
```

## Data Flow

**as_frames() Flow (after refactor):**

1. User calls `scenario.as_frames(display_cn=False/True)`
2. Method accesses `self._data` (Register[Parameter])
3. Iterate through all Parameters in `self._data`
4. For each Parameter, iterate through its dimension combinations
5. Build row/column structure:
   - Rows: dimension indices with parameter values
   - Columns: dimension names + parameter names
6. Create pandas DataFrame for each unique dimension combination
7. Return dict mapping dimension tuples to DataFrames

**No changes to data flow** - identical logic, just moved location.

## Error Handling

**No explicit errors raised by `as_frames()`:**
- Empty Register → returns empty dict `{}`
- Missing data → fills with `None` values
- Invalid input types → pandas will raise errors naturally

**No error handling changes needed** - behavior preserved exactly.

## Testing

### Test Files to Update

1. **`register/tests/test_register.py`**: Remove 6 `as_frames()` tests
2. **`tests/test_scenario.py`**: Add 6 `as_frames()` tests

### Test Cases to Port

1. **Empty scenario data**: Returns empty dict
2. **Single value**: Creates single DataFrame with one row
3. **Multiple parameters**: Multiple columns in DataFrame
4. **Chinese names (display_cn=True)**: Uses Chinese column names
5. **Multiple dimensions**: Multiple dimension columns in DataFrame
6. **Same parameter, different dimensions**: Creates separate DataFrames per dimension combination

## Benefits

1. **Lighter register package:** No pandas dependency (~10MB smaller install)
2. **Consistent pattern:** Same as `validate()` refactor
3. **Separation of concerns:** Data export logic where Parameters are used
4. **Faster installs:** Fewer dependencies for register package

## Risks

1. **Breaking change:** If other code uses `Register.as_frames()`, will break
   - Mitigation: Search codebase for usages before proceeding
   - User confirmed: Similar to `validate()` - exclusively used by Scenario
2. **Dependency management:** Need to update two pyproject.toml files
   - Impact: Low, straightforward changes

## Open Questions

None identified.

## Dependencies

- `register` package source location: `D:/github/register/`
- `or_scenario` package: Current working directory
