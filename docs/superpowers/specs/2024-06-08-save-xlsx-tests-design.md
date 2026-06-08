# Design: save_xlsx() Tests

**Date:** 2024-06-08
**Author:** Design discussion with user
**Status:** Proposed

## Overview

Add comprehensive tests for the existing `Scenario.save_xlsx()` method to verify Excel file generation functionality.

## Current Implementation

**`or_scenario/scenario.py:318-321`:**
```python
def save_xlsx(self, path: Path, display_cn: bool = False):
    with pd.ExcelWriter(path / f'{type(self).__name__}_version_{self._version_id}.xlsx', engine='openpyxl') as writer:
        for dimension, df in self.as_frames(display_cn).items():
            df.to_excel(writer, sheet_name='_'.join(d.name_cn if display_cn else d.name for d in dimension), index=False)
```

The method:
1. Takes a `path` (Path object) and `display_cn` (boolean) parameter
2. Creates an Excel file named `{ClassName}_version_{version_id}.xlsx` in the specified path
3. Uses `as_frames(display_cn)` to get pandas DataFrames
4. Writes each dimension's DataFrame to a separate sheet
5. Sheet names are dimension names joined with underscores

## Dependencies

**Required:**
- `openpyxl` - Excel writer engine

**Verification needed:** Check if `openpyxl` is already in `or_scenario/pyproject.toml` dependencies. If not present, add `openpyxl = "^3.0"` to dependencies.

## Test Design

### Test File

**`tests/test_scenario.py`** - Add new test functions at the end of the file

### Test Scenarios

1. **Empty scenario** - Tests with empty `self._data` (no parameters populated)
   - Should create Excel file (possibly with no sheets or empty sheets)

2. **Single parameter with single dimension** - Tests with one parameter (`Id`) and one dimension (`Index`)
   - Populates `Id` with one value
   - Verifies file is created

3. **Multiple parameters with same dimension** - Tests with multiple parameters (`Id`, `Name`) sharing the same dimension (`Index`)
   - Populates both parameters with values
   - Verifies file is created

4. **Multiple dimension combinations** - Tests with one parameter having different dimension combinations
   - Creates two dimensions (`dim1`, `dim2`)
   - Populates `Id` with data for both dimension combinations
   - Verifies file is created

5. **display_cn=True** - Tests with `display_cn=True` to verify Chinese names work
   - Populates `Id` with value
   - Calls `save_xlsx(display_cn=True)`
   - Verifies file is created

### Verification Approach

**Location:** Use `/tmp` directory for test files

**Verification steps:**
1. Check file exists: `os.path.exists(file_path)`
2. Check file has content: `os.path.getsize(file_path) > 0`
3. Clean up: `os.remove(file_path)`

**Expected file naming:** `Scenario_version_{version_id}.xlsx`

Where `{version_id}` is `scenario._version_id` (defaults to request.request_id)

## Test Implementation

### Test Function Signatures

```python
def test_scenario_save_xlsx_empty_scenario():
    """Test save_xlsx() with empty scenario data."""
    from pathlib import Path
    import os
    
    scenario = Scenario()
    path = Path("/tmp")
    scenario.save_xlsx(path)
    expected_file = path / f"Scenario_version_{scenario._version_id}.xlsx"
    assert os.path.exists(expected_file)
    assert os.path.getsize(expected_file) > 0
    os.remove(expected_file)


def test_scenario_save_xlsx_single_parameter_single_dimension():
    """Test save_xlsx() with one parameter and one dimension."""
    from pathlib import Path
    from register import Id, Index
    import os
    
    scenario = Scenario()
    path = Path("/tmp")
    scenario._data[Id][(Index,)][(1,)] = 42
    scenario.save_xlsx(path)
    expected_file = path / f"Scenario_version_{scenario._version_id}.xlsx"
    assert os.path.exists(expected_file)
    assert os.path.getsize(expected_file) > 0
    os.remove(expected_file)


def test_scenario_save_xlsx_multiple_parameters_same_dimension():
    """Test save_xlsx() with multiple parameters sharing same dimension."""
    from pathlib import Path
    from register import Id, Name, Index
    import os
    
    scenario = Scenario()
    path = Path("/tmp")
    scenario._data[Id][(Index,)][(1,)] = 42
    scenario._data[Name][(Index,)][(1,)] = "test_name"
    scenario.save_xlsx(path)
    expected_file = path / f"Scenario_version_{scenario._version_id}.xlsx"
    assert os.path.exists(expected_file)
    assert os.path.getsize(expected_file) > 0
    os.remove(expected_file)


def test_scenario_save_xlsx_multiple_dimension_combinations():
    """Test save_xlsx() with parameter having multiple dimension combinations."""
    from pathlib import Path
    from register import Id, Dimension
    import os
    
    scenario = Scenario()
    path = Path("/tmp")
    dim1 = Dimension("test1", "测试1", "T1")
    dim2 = Dimension("test2", "测试2", "T2")
    scenario._data[Id][(dim1,)][(1,)] = 100
    scenario._data[Id][(dim2,)][(2,)] = 200
    scenario.save_xlsx(path)
    expected_file = path / f"Scenario_version_{scenario._version_id}.xlsx"
    assert os.path.exists(expected_file)
    assert os.path.getsize(expected_file) > 0
    os.remove(expected_file)


def test_scenario_save_xlsx_display_cn():
    """Test save_xlsx() with display_cn=True for Chinese names."""
    from pathlib import Path
    from register import Id, Index
    import os
    
    scenario = Scenario()
    path = Path("/tmp")
    scenario._data[Id][(Index,)][(1,)] = 42
    scenario.save_xlsx(path, display_cn=True)
    expected_file = path / f"Scenario_version_{scenario._version_id}.xlsx"
    assert os.path.exists(expected_file)
    assert os.path.getsize(expected_file) > 0
    os.remove(expected_file)
```

## Benefits

1. **Confidence:** Ensures Excel export functionality works correctly
2. **Regression prevention:** Catches breaking changes to save_xlsx() method
3. **Documentation:** Tests serve as usage examples

## Risks

1. **File cleanup:** Test files in `/tmp` should be cleaned up properly
   - Mitigation: Use `try-finally` or `pytest` autouse fixtures for cleanup
2. **Platform differences:** `/tmp` path may not work on Windows
   - Mitigation: Use `Path(tempfile.gettempdir())` for cross-platform compatibility

## Open Questions

None identified.

## Dependencies

- `or_scenario/scenario.py` - Contains `save_xlsx()` method
- `tests/test_scenario.py` - Where tests will be added
- `openpyxl` - Required for Excel writing (verify present in pyproject.toml)
