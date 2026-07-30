# save_xlsx() Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comprehensive tests for Scenario.save_xlsx() method to verify Excel file generation

**Architecture:** Add 5 test functions to test_scenario.py covering empty scenario, single parameter, multiple parameters, multiple dimensions, and Chinese names

**Tech Stack:** Python 3.11, pytest, openpyxl, tempfile

---

## File Structure

### Files to Modify
1. **`tests/test_scenario.py`** - Add 5 new test functions at the end of the file
2. **`pyproject.toml`** - Verify `openpyxl` is in dependencies (add if missing)

---

## Task 1: Verify openpyxl dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Check if openpyxl is in dependencies**

```bash
grep openpyxl pyproject.toml
```

Expected output: Line showing `openpyxl = "^3.0"` or similar

- [ ] **Step 2: If openpyxl is not found, add it**

If grep returns no output, add `openpyxl = "^3.0"` to dependencies section:

Read pyproject.toml to find `[tool.poetry.dependencies]` section and add:
```toml
openpyxl = "^3.0"
```

- [ ] **Step 3: Verify openpyxl is available**

```bash
poetry run python -c "import openpyxl; print(openpyxl.__version__)"
```

Expected output: openpyxl version number

- [ ] **Step 4: Commit if dependency was added**

```bash
git add pyproject.toml poetry.lock
git commit -m "deps: ensure openpyxl is available for Excel export"
```

Skip this step if openpyxl was already present.

---

## Task 2: Add test_scenario_save_xlsx_empty_scenario()

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Write test function**

Add this test to the end of `tests/test_scenario.py`:

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
```

- [ ] **Step 2: Run test to verify it passes**

```bash
poetry run pytest tests/test_scenario.py::test_scenario_save_xlsx_empty_scenario -v
```

Expected: PASS

- [ ] **Step 3: Verify cleanup works**

Check that no test file remains:

```bash
ls /tmp/Scenario_version_*.xlsx 2>/dev/null || echo "No test files found (cleanup successful)"
```

Expected: "No test files found (cleanup successful)"

---

## Task 3: Add test_scenario_save_xlsx_single_parameter_single_dimension()

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Write test function**

Add this test after the previous test:

```python
def test_scenario_save_xlsx_single_parameter_single_dimension():
    """Test save_xlsx() with one parameter and one dimension."""
    from pathlib import Path
    from or_register import Id, Index
    import os
    
    scenario = Scenario()
    path = Path("/tmp")
    scenario._data[Id][(Index,)][(1,)] = 42
    scenario.save_xlsx(path)
    expected_file = path / f"Scenario_version_{scenario._version_id}.xlsx"
    assert os.path.exists(expected_file)
    assert os.path.getsize(expected_file) > 0
    os.remove(expected_file)
```

- [ ] **Step 2: Run test to verify it passes**

```bash
poetry run pytest tests/test_scenario.py::test_scenario_save_xlsx_single_parameter_single_dimension -v
```

Expected: PASS

---

## Task 4: Add test_scenario_save_xlsx_multiple_parameters_same_dimension()

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Write test function**

Add this test after the previous test:

```python
def test_scenario_save_xlsx_multiple_parameters_same_dimension():
    """Test save_xlsx() with multiple parameters sharing same dimension."""
    from pathlib import Path
    from or_register import Id, Name, Index
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
```

- [ ] **Step 2: Run test to verify it passes**

```bash
poetry run pytest tests/test_scenario.py::test_scenario_save_xlsx_multiple_parameters_same_dimension -v
```

Expected: PASS

---

## Task 5: Add test_scenario_save_xlsx_multiple_dimension_combinations()

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Write test function**

Add this test after the previous test:

```python
def test_scenario_save_xlsx_multiple_dimension_combinations():
    """Test save_xlsx() with parameter having multiple dimension combinations."""
    from pathlib import Path
    from or_register import Id, Dimension
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
```

- [ ] **Step 2: Run test to verify it passes**

```bash
poetry run pytest tests/test_scenario.py::test_scenario_save_xlsx_multiple_dimension_combinations -v
```

Expected: PASS

---

## Task 6: Add test_scenario_save_xlsx_display_cn()

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Write test function**

Add this test after the previous test:

```python
def test_scenario_save_xlsx_display_cn():
    """Test save_xlsx() with display_cn=True for Chinese names."""
    from pathlib import Path
    from or_register import Id, Index
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

- [ ] **Step 2: Run test to verify it passes**

```bash
poetry run pytest tests/test_scenario.py::test_scenario_save_xlsx_display_cn -v
```

Expected: PASS

---

## Task 7: Run all save_xlsx tests together

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Run all 5 save_xlsx tests**

```bash
poetry run pytest tests/test_scenario.py -k "save_xlsx" -v
```

Expected: All 5 tests PASS

- [ ] **Step 2: Verify no test files remain**

```bash
ls /tmp/Scenario_version_*.xlsx 2>/dev/null || echo "No test files found (cleanup successful)"
```

Expected: "No test files found (cleanup successful)"

---

## Task 8: Run full test suite

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Run all scenario tests**

```bash
poetry run pytest tests/test_scenario.py -v 2>&1 | tail -10
```

Expected: All tests pass (46 total: 41 existing + 5 new save_xlsx tests)

- [ ] **Step 2: Run mypy**

```bash
poetry run mypy or_scenario/
```

Expected: No mypy errors

- [ ] **Step 3: Run ruff**

```bash
poetry run ruff check or_scenario/
```

Expected: No ruff errors

---

## Task 9: Final verification and commit

- [ ] **Step 1: Check git status**

```bash
git status
```

Expected: Only tests/test_scenario.py modified (or clean if dependency was added)

- [ ] **Step 2: Count new tests**

```bash
grep -c "def test_scenario_save_xlsx" tests/test_scenario.py
```

Expected: 5 (one for each test scenario)

- [ ] **Step 3: Commit test additions**

```bash
git add tests/test_scenario.py
git commit -m "test: add Scenario.save_xlsx() tests"
```

---

## Summary

This implementation plan:
1. Verifies `openpyxl` dependency is available
2. Adds 5 comprehensive test functions for `save_xlsx()` method
3. Tests cover: empty scenario, single parameter, multiple parameters, multiple dimensions, Chinese names
4. Uses `/tmp` for test files with proper cleanup
5. Verifies all tests pass and code quality checks pass

**Total estimated time:** 20-25 minutes
**Risk level:** Low (test-only changes, no production code modification)
