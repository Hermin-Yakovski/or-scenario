# as_frames() Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move as_frames() method from Register to Scenario, removing pandas dependency from register package

**Architecture:**
- Remove as_frames() method and pandas dependency from register package
- Add as_frames() method to Scenario class in or_scenario package
- Transfer pandas dependency from register → or_scenario

**Tech Stack:** Python 3.11, pandas, poetry, pytest, mypy

---

## File Structure

### Files to Modify (register package)
1. **`D:/github/register/register/register.py`**
   - Remove `import pandas as pd` (line 5)
   - Remove `as_frames()` method (lines 77-106)

2. **`D:/github/register/pyproject.toml`**
   - Remove `pandas = "^2.0"` from dependencies
   - Remove `pandas-stubs = "^2.0"` from dev dependencies

3. **`D:/github/register/tests/test_register.py`**
   - Remove 6 `as_frames()` tests (lines 208-297)

### Files to Modify (or_scenario package)
4. **`or_scenario/scenario.py`**
   - Add `import pandas as pd`
   - Add `as_frames()` method

5. **`or_scenario/pyproject.toml`**
   - Add `pandas = "^2.0"` to dependencies
   - Add `pandas-stubs = "^2.0"` to dev dependencies

6. **`tests/test_scenario.py`**
   - Add 6 `as_frames()` tests

### Files to Rebuild
7. **`D:/github/register/dist/register-0.1.0-py3-none-any.whl`**
   - Rebuild wheel after changes

---

## Task 1: Remove as_frames() method from register package

**Files:**
- Modify: `D:/github/register/register/register.py`

- [ ] **Step 1: Read current as_frames() method**

```bash
sed -n '77,106p' D:/github/register/register/register.py
```

Expected output: The full as_frames() method

- [ ] **Step 2: Remove pandas import**

Remove line 5 (`import pandas as pd`):

```bash
cd D:/github/register
sed -i '5d' register/register.py
```

- [ ] **Step 3: Verify pandas import removed**

```bash
head -10 D:/github/register/register/register.py | grep pandas
```

Expected: No output (pandas import removed)

- [ ] **Step 4: Remove as_frames() method**

Remove lines 77-106 (30 lines total, adjusting for removed import):

```bash
cd D:/github/register
sed -i '76,105d' register/register.py
```

Note: Line range adjusted from 77-106 to 76-105 because we removed line 5

- [ ] **Step 5: Verify as_frames() method removed**

```bash
grep -n "def as_frames" D:/github/register/register/register.py
```

Expected: No results (as_frames method should not exist)

- [ ] **Step 6: Commit changes**

```bash
cd D:/github/register
git add register/register.py
git commit -m "refactor: remove as_frames() method and pandas import from Register"
```

---

## Task 2: Remove as_frames() tests from register package

**Files:**
- Modify: `D:/github/register/tests/test_register.py`

- [ ] **Step 1: List as_frames() test functions**

```bash
grep -n "^def test_as_frames" D:/github/register/tests/test_register.py
```

Expected output: Lines showing 6 test functions

- [ ] **Step 2: View first as_frames test**

```bash
sed -n '208,214p' D:/github/register/tests/test_register.py
```

Expected: First test `test_as_frames_empty_register`

- [ ] **Step 3: View last as_frames test**

```bash
sed -n '275,297p' D:/github/register/tests/test_register.py
```

Expected: Last test `test_as_frames_multiple_dimension_keys_for_same_parameter`

- [ ] **Step 4: Remove all as_frames() tests**

Remove lines 208-297 (90 lines total):

```bash
cd D:/github/register
sed -i '208,297d' tests/test_register.py
```

- [ ] **Step 5: Verify tests removed**

```bash
grep -c "^def test_as_frames" D:/github/register/tests/test_register.py
```

Expected: 0 (no as_frames tests remaining)

- [ ] **Step 6: Run register tests**

```bash
cd D:/github/register
poetry run pytest tests/test_register.py -v
```

Expected: All remaining tests pass

- [ ] **Step 7: Commit changes**

```bash
cd D:/github/register
git add tests/test_register.py
git commit -m "test: remove Register.as_frames() tests"
```

---

## Task 3: Remove pandas dependencies from register pyproject.toml

**Files:**
- Modify: `D:/github/register/pyproject.toml`

- [ ] **Step 1: Read current dependencies**

```bash
cat D:/github/register/pyproject.toml
```

Expected output: Show current pandas dependencies

- [ ] **Step 2: Remove pandas from dependencies**

Remove line containing `pandas = "^2.0"` from `[tool.poetry.dependencies]` section:

```bash
cd D:/github/register
sed -i '/^pandas = /d' pyproject.toml
```

- [ ] **Step 3: Remove pandas-stubs from dev dependencies**

Remove line containing `pandas-stubs = "^2.0"` from `[tool.poetry.group.dev.dependencies]` section:

```bash
cd D:/github/register
sed -i '/^pandas-stubs = /d' pyproject.toml
```

- [ ] **Step 4: Verify pandas dependencies removed**

```bash
grep pandas D:/github/register/pyproject.toml
```

Expected: No output (pandas dependencies removed)

- [ ] **Step 5: Update poetry lock file**

```bash
cd D:/github/register
poetry lock --no-update
```

Expected: Lock file updated successfully

- [ ] **Step 6: Commit changes**

```bash
cd D:/github/register
git add pyproject.toml poetry.lock
git commit -m "deps: remove pandas dependency from register package"
```

---

## Task 4: Add pandas dependencies to or_scenario

**Files:**
- Modify: `or_scenario/pyproject.toml`

- [ ] **Step 1: Read current dependencies**

```bash
cat or_scenario/pyproject.toml
```

Expected output: Show current dependencies

- [ ] **Step 2: Add pandas to dependencies**

Add `pandas = "^2.0"` to `[tool.poetry.dependencies]` section. Use Edit tool to add after line 16:

```bash
# Add this line after the last dependency in [tool.poetry.dependencies]
pandas = "^2.0"
```

Edit `or_scenario/pyproject.toml`, find `[tool.poetry.dependencies]` section and add:
```toml
pandas = "^2.0"
```

- [ ] **Step 3: Add pandas-stubs to dev dependencies**

Add `pandas-stubs = "^2.0"` to `[tool.poetry.group.dev.dependencies]` section. Use Edit tool:

```toml
pandas-stubs = "^2.0"
```

- [ ] **Step 4: Verify pandas dependencies added**

```bash
grep pandas or_scenario/pyproject.toml
```

Expected: Two lines showing pandas and pandas-stubs

- [ ] **Step 5: Install pandas dependency**

```bash
poetry lock
poetry install
```

Expected: Dependencies installed successfully

- [ ] **Step 6: Commit changes**

```bash
git add or_scenario/pyproject.toml poetry.lock
git commit -m "deps: add pandas dependency to or_scenario package"
```

---

## Task 5: Add pandas import to or_scenario

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Read current imports**

```bash
head -20 or_scenario/scenario.py
```

Expected output: Show current import structure

- [ ] **Step 2: Add pandas import**

Add `import pandas as pd` after the logging imports. Use Edit tool to add after line 9:

```python
import pandas as pd
```

The imports section should look like:
```python
from register import Dimension, Id, Parameter, Register, Index
from register.register import Method
from register.exception import DimensionError, ValidationError
from typing import get_origin, get_args, Any
import logging
import pandas as pd

from .orm import generate_sol_table, generate_fact_table
from .schema import BaseRequest
```

- [ ] **Step 3: Verify import added**

```bash
head -15 or_scenario/scenario.py | grep pandas
```

Expected: `import pandas as pd`

- [ ] **Step 4: Run mypy to verify import resolves**

```bash
poetry run mypy or_scenario/
```

Expected: No mypy errors

- [ ] **Step 5: Commit import changes**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: add pandas import to scenario"
```

---

## Task 6: Add as_frames() method to Scenario

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Find location to add as_frames() method**

Find the end of the `validate()` method (around line 260):

```bash
grep -n "def response" or_scenario/scenario.py | head -1
```

Expected output: Line number where `response()` method starts

- [ ] **Step 2: Add as_frames() method after validate()**

Use Edit tool to insert the complete `as_frames()` method between `validate()` and `response()` methods:

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
        columns: dict[tuple[Dimension, ...], list[str]]] = {}

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
            dataframe_rows: list[list[Any]]] = []
            for index in rows[dimension]:
                dataframe_rows.append([i for i in index] + rows[dimension][index])
            frames[dimension] = pd.DataFrame(dataframe_rows, columns=dataframe_columns)

        return frames
```

Insert this method after the `validate()` method ends and before `response()` method starts.

- [ ] **Step 3: Verify method added**

```bash
grep -n "def as_frames" or_scenario/scenario.py
```

Expected: Line number where as_frames() was added

- [ ] **Step 4: Run mypy**

```bash
poetry run mypy or_scenario/
```

Expected: No mypy errors

- [ ] **Step 5: Run ruff checks**

```bash
poetry run ruff check or_scenario/
```

Expected: No ruff errors

- [ ] **Step 6: Commit method addition**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: add as_frames() method to Scenario class"
```

---

## Task 7: Add as_frames() tests to test_scenario.py

**Files:**
- Create: `tests/test_scenario.py` (add tests)

- [ ] **Step 1: Read end of test_scenario.py to find insertion point**

```bash
tail -20 tests/test_scenario.py
```

Expected output: End of file showing where to add new tests

- [ ] **Step 2: Add test_scenario_as_frames_empty()**

Add this test to the end of `tests/test_scenario.py`:

```python
def test_scenario_as_frames_empty():
    """Test Scenario.as_frames() returns empty dict for empty scenario."""
    from register import Id

    scenario = Scenario()
    frames = scenario.as_frames()
    assert frames == {}
```

- [ ] **Step 3: Add test_scenario_as_frames_single_value()**

```python
def test_scenario_as_frames_single_value():
    """Test Scenario.as_frames() with single value."""
    from register import Id, Index

    scenario = Scenario()
    scenario._data[Id][(Index,)][(1,)] = 42
    frames = scenario.as_frames()
    assert len(frames) == 1
    df = frames[(Index,)]
    assert df.iloc[0]["id"] == 42
```

- [ ] **Step 4: Add test_scenario_as_frames_multiple_parameters()**

```python
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
```

- [ ] **Step 5: Add test_scenario_as_frames_display_cn()**

```python
def test_scenario_as_frames_display_cn():
    """Test Scenario.as_frames() with Chinese names."""
    from register import Id, Index

    scenario = Scenario()
    scenario._data[Id][(Index,)][(1,)] = 42
    frames = scenario.as_frames(display_cn=True)
    df = frames[(Index,)]
    assert "索引" in df.columns
    assert df.iloc[0]["ID"] == 42
```

- [ ] **Step 6: Add test_scenario_as_frames_multiple_dimensions()**

```python
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
```

- [ ] **Step 7: Add test_scenario_as_frames_multiple_dimension_keys_for_same_parameter()**

```python
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
```

- [ ] **Step 8: Run the new tests**

```bash
poetry run pytest tests/test_scenario.py::test_scenario_as_frames_empty -v
poetry run pytest tests/test_scenario.py::test_scenario_as_frames_single_value -v
poetry run pytest tests/test_scenario.py::test_scenario_as_frames_multiple_parameters -v
poetry run pytest tests/test_scenario.py::test_scenario_as_frames_display_cn -v
poetry run pytest tests/test_scenario.py::test_scenario_as_frames_multiple_dimensions -v
poetry run pytest tests/test_scenario.py::test_scenario_as_frames_multiple_dimension_keys_for_same_parameter -v
```

Expected: All 6 tests pass

- [ ] **Step 9: Run all scenario tests**

```bash
poetry run pytest tests/test_scenario.py -v
```

Expected: All tests pass (41 total: 35 existing + 6 new)

- [ ] **Step 10: Commit test additions**

```bash
git add tests/test_scenario.py
git commit -m "test: add Scenario.as_frames() tests"
```

---

## Task 8: Rebuild register package and update or_scenario

**Files:**
- Create: `D:/github/register/dist/register-0.1.0-py3-none-any.whl`

- [ ] **Step 1: Build register package**

```bash
cd D:/github/register
poetry build
```

Expected: Build completes successfully

- [ ] **Step 2: Verify wheel was created**

```bash
ls -la D:/github/register/dist/
```

Expected: Wheel file with recent timestamp

- [ ] **Step 3: Update or_scenario to use new register wheel**

```bash
cd D:/github/or-scenario
rm -rf .venv/Lib/site-packages/register*
unzip -o D:/github/register/dist/register-0.1.0-py3-none-any.whl -d .venv/Lib/site-packages/
```

Expected: Wheel extracted successfully

- [ ] **Step 4: Verify register package has no pandas dependency**

```bash
cat .venv/Lib/site-packages/register/register.py | head -10
```

Expected: No pandas import

- [ ] **Step 5: Commit register package build**

```bash
cd D:/github/register
git add dist/
git commit -m "build: rebuild register wheel without as_frames() method"
```

---

## Task 9: Run full test suite

**Files:**
- Test: `tests/test_scenario.py`
- Test: `D:/github/register/tests/test_register.py`

- [ ] **Step 1: Run all or_scenario tests**

```bash
poetry run pytest tests/ -v
```

Expected: All 41 tests pass

- [ ] **Step 2: Run all register tests**

```bash
cd D:/github/register
poetry run pytest tests/ -v
```

Expected: All 28 tests pass (no as_frames tests)

- [ ] **Step 3: Run mypy on both packages**

```bash
# or_scenario
cd D:/github/or-scenario
poetry run mypy or_scenario/

# register
cd D:/github/register
poetry run mypy register/
```

Expected: No mypy errors in either package

- [ ] **Step 4: Run ruff on or_scenario**

```bash
cd D:/github/or-scenario
poetry run ruff check or_scenario/
```

Expected: No ruff errors

- [ ] **Step 5: Run ruff on register**

```bash
cd D:/github/register
poetry run ruff check register/
```

Expected: No ruff errors

---

## Task 10: Final verification

- [ ] **Step 1: Verify Register.as_frames() is gone**

```bash
poetry run python -c "from register import Register; print(dir(Register))" | grep as_frames
```

Expected: No output (as_frames method should not exist)

- [ ] **Step 2: Verify Scenario.as_frames() works**

```bash
poetry run python -c "
from or_scenario import Scenario
from register import Id, Index
scenario = Scenario()
scenario._data[Id][(Index,)][(1,)] = 42
frames = scenario.as_frames()
print(f'Frames: {len(frames)}')
print(f'Columns: {list(frames[(Index,)].columns)}')
"
```

Expected output showing DataFrame was created successfully

- [ ] **Step 3: Verify register has no pandas dependency**

```bash
cd D:/github/register
grep pandas pyproject.toml
```

Expected: No output (pandas not in dependencies)

- [ ] **Step 4: Verify or_scenario has pandas dependency**

```bash
grep pandas or_scenario/pyproject.toml
```

Expected: Two lines showing pandas and pandas-stubs

- [ ] **Step 5: Check git status**

```bash
cd D:/github/or-scenario
git status
```

Expected: Clean working directory (all changes committed)

- [ ] **Step 6: View recent commits**

```bash
git log --oneline -10
```

Review commits to ensure all changes are documented

- [ ] **Step 7: Summary of changes**

Count commits in each repo:

```bash
# or-scenario commits
cd D:/github/or-scenario
git log --oneline --since="1 hour ago" | wc -l

# register commits
cd D:/github/register
git log --oneline --since="1 hour ago" | wc -l
```

---

## Summary

This implementation plan:
1. Removes `as_frames()` method and pandas dependency from register package
2. Adds `as_frames()` method to Scenario class in or_scenario package
3. Transfers pandas dependency from register → or_scenario
4. Ports all tests from register to or_scenario
5. Preserves exact functionality and API

**Total estimated time:** 30-40 minutes
**Risk level:** Low (changes are isolated, following proven pattern from validate() refactor)
