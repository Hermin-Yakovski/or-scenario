# Generic Register Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Parameter type bound from Register generic class and move Parameter-specific validation logic to Scenario.validate()

**Architecture:** 
- Modify `register` package TypeVar to accept any key with `.vtype` attribute
- Move validation logic from `Register.validate()` to `Scenario.validate()` in `or_scenario`
- Preserve all existing validation behavior for `Scenario.validate()`

**Tech Stack:** Python 3.11, mypy, pytest, poetry

---

## File Structure

### Files to Modify

1. **`D:/github/register/register/register.py`**
   - Remove `bound=Parameter` from TypeVar
   - Remove `validate()` method

2. **`or_scenario/scenario.py`**
   - Add imports for validation logic
   - Inline validation logic in `validate()` method

3. **`D:/github/register/tests/test_register.py`**
   - Remove all tests for `Register.validate()` method

### Files to Rebuild

1. **`D:/github/register/dist/register-0.1.0-py3-none-any.whl`**
   - Rebuild wheel after changes

---

## Task 1: Modify register package - Remove TypeVar bound

**Files:**
- Modify: `D:/github/register/register/register.py:11`

- [ ] **Step 1: Read the current TypeVar definition**

```bash
# View line 11 in register.py
sed -n '11p' D:/github/register/register/register.py
```

Expected output: `K = TypeVar("K", bound=Parameter)`

- [ ] **Step 2: Remove the bound parameter from TypeVar**

```python
# Change line 11 from:
K = TypeVar("K", bound=Parameter)
# To:
K = TypeVar("K")
```

Edit `D:/github/register/register/register.py` line 11.

- [ ] **Step 3: Verify the change**

```bash
sed -n '11p' D:/github/register/register/register.py
```

Expected output: `K = TypeVar("K")`

- [ ] **Step 4: Run mypy on register package**

```bash
cd D:/github/register && python -m mypy register/
```

Expected: No mypy errors related to TypeVar bound

- [ ] **Step 5: Commit register package change**

```bash
cd D:/github/register
git add register/register.py
git commit -m "refactor: remove Parameter bound from Register TypeVar"
```

---

## Task 2: Modify register package - Remove validate() method

**Files:**
- Modify: `D:/github/register/register/register.py:110-193`

- [ ] **Step 1: Identify lines to remove**

```bash
# View lines 110-193
sed -n '110,193p' D:/github/register/register/register.py | head -5
```

Expected output: First 5 lines of the `validate()` method

- [ ] **Step 2: Remove the validate() method**

Delete lines 110-193 containing the entire `validate()` method including:
- Method signature: `def validate(self, dim: DimensionAsKey, raise_errors: bool = False) -> None:`
- All validation logic (index length check, index existence check, type validation)

The method to remove starts at line 110 and ends at line 193 (84 lines total).

```bash
# Remove lines 110-193 using sed
cd D:/github/register
sed -i '110,193d' register/register.py
```

- [ ] **Step 3: Verify the method was removed**

```bash
# Check that validate() no longer exists in Register class
grep -n "def validate" D:/github/register/register/register.py
```

Expected: No results (validate method should not exist)

- [ ] **Step 4: Run register tests (expect failures for validate tests)**

```bash
cd D:/github/register
pytest tests/test_register.py -v
```

Expected: Tests for `validate()` method will fail (we'll remove them in Task 5)

- [ ] **Step 5: Commit register package change**

```bash
cd D:/github/register
git add register/register.py
git commit -m "refactor: remove Register.validate() method"
```

---

## Task 3: Remove Register.validate() tests from register package

**Files:**
- Modify: `D:/github/register/tests/test_register.py`

- [ ] **Step 1: List all validate() test functions**

```bash
grep -n "^def test_validate" D:/github/register/tests/test_register.py
```

Expected: List of all test functions starting with `test_validate`

- [ ] **Step 2: Identify test lines to remove**

The following test functions need to be removed (lines 299-644):
- `test_validate_with_valid_data_no_errors` (lines 299-310)
- `test_validate_with_invalid_type_logs_warning` (lines 313-324)
- `test_validate_with_invalid_type_raises_error` (lines 327-339)
- `test_validate_with_any_type_accepts_anything` (lines 342-354)
- `test_validate_with_list_type` (lines 357-368)
- `test_validate_with_invalid_list_element_type` (lines 371-384)
- `test_validate_with_invalid_container_type_not_list` (lines 387-400)
- `test_validate_with_invalid_container_type_not_set` (lines 403-416)
- `test_validate_with_invalid_container_type_not_tuple` (lines 419-432)
- `test_validate_with_list_of_dimension_valid` (lines 435-457)
- `test_validate_with_list_of_dimension_invalid_element` (lines 460-484)
- `test_validate_with_dimension_type` (lines 487-506)
- `test_validate_with_invalid_dimension_value` (lines 509-530)
- `test_validate_with_invalid_dimension_value_logs_warning` (lines 533-552)
- `test_validate_with_valid_index_per_dimension` (lines 555-581)
- `test_validate_with_invalid_index_per_dimension` (lines 584-611)
- `test_validate_with_mismatch_length_index_per_dimension` (lines 614-643)

- [ ] **Step 3: Remove the validate() test functions**

Delete lines 299-644 (all validate tests):

```bash
cd D:/github/register
sed -i '299,644d' tests/test_register.py
```

- [ ] **Step 4: Verify tests were removed**

```bash
grep -c "^def test_validate" D:/github/register/tests/test_register.py
```

Expected: 0 (no validate tests remaining)

- [ ] **Step 5: Run register tests**

```bash
cd D:/github/register
pytest tests/test_register.py -v
```

Expected: All remaining tests pass

- [ ] **Step 6: Commit register test changes**

```bash
cd D:/github/register
git add tests/test_register.py
git commit -m "test: remove Register.validate() tests"
```

---

## Task 4: Rebuild register package wheel

**Files:**
- Create: `D:/github/register/dist/register-0.1.0-py3-none-any.whl`

- [ ] **Step 1: Build the register package**

```bash
cd D:/github/register
poetry build
```

Expected: Build completes successfully with new wheel in `dist/`

- [ ] **Step 2: Verify wheel was created**

```bash
ls -la D:/github/register/dist/
```

Expected: `register-0.1.0-py3-none-any.whl` exists with recent timestamp

- [ ] **Step 3: Update or-scenario to use new register wheel**

```bash
cd D:/github/or-scenario
poetry add register={path="D:/github/register/dist/register-0.1.0-py3-none-any.whl"}
```

Expected: Poetry updates dependencies successfully

- [ ] **Step 4: Commit register package build**

```bash
cd D:/github/register
git add dist/
git commit -m "build: rebuild register wheel without validate() method"
```

---

## Task 5: Add validation imports to or_scenario

**Files:**
- Modify: `or_scenario/scenario.py:1-19`

- [ ] **Step 1: Read current imports**

```bash
head -20 or_scenario/scenario.py
```

Expected: Current imports at top of file

- [ ] **Step 2: Add validation-related imports**

Add these imports to `or_scenario/scenario.py` after line 5 (after `from or_register import Dimension, Id, Parameter, Register`):

```python
from register.exception import DimensionError, ValidationError
from typing import get_origin, get_args
import logging

logger = logging.getLogger("or_scenario")
```

The imports section should now be:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

from or_register import Dimension, Id, Parameter, Register
from register.exception import DimensionError, ValidationError
from typing import get_origin, get_args
import logging

from .orm import generate_sol_table, generate_fact_table
from .schema import BaseRequest

logger = logging.getLogger("or_scenario")

if TYPE_CHECKING:
    # ... existing TYPE_CHECKING block
```

- [ ] **Step 3: Verify imports**

```bash
head -20 or_scenario/scenario.py
```

Expected: All imports present including new ones

- [ ] **Step 4: Run mypy on or_scenario**

```bash
python -m mypy or_scenario/
```

Expected: No mypy errors (new imports resolve correctly)

- [ ] **Step 5: Commit import changes**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: add validation imports to scenario"
```

---

## Task 6: Inline validation logic in Scenario.validate()

**Files:**
- Modify: `or_scenario/scenario.py:186-193`

- [ ] **Step 1: Read current validate() method**

```bash
sed -n '186,193p' or_scenario/scenario.py
```

Current method:
```python
def validate(self, param: Parameter = Id) -> None:
    """Validate scenario data.

    Args:
        param: The parameter to validate (defaults to Id)
    """
    dim = self._data[param]
    self._data.validate(dim, raise_errors=True)
```

- [ ] **Step 2: Replace validate() method with inlined logic**

Replace the current `validate()` method (lines 186-193) with the following complete implementation:

```python
def validate(self, param: Parameter = Id) -> None:
    """Validate scenario data.

    Validates all parameters in self._data against the reference dimension
    from the specified parameter (defaults to Id).

    Args:
        param: The parameter whose dimension serves as reference for validation
               (defaults to Id)

    Raises:
        DimensionError: If index length mismatch or invalid index reference
        ValidationError: If value doesn't match expected vtype
    """
    dim = self._data[param]

    for key in self._data:
        for dimension in self._data[key]:
            for index in self._data[key][dimension]:
                # Validate index length matches dimension length
                if len(dimension) != len(index):
                    msg = (
                        f"[v{key.id}] {key}{dimension}{index}: "
                        f"dimension length {len(dimension)} does not match index length {len(index)}"
                    )
                    raise DimensionError(msg)

                # Validate index exists in reference dimension
                for d, ix in zip(dimension, index):
                    if not ((ix,) in dim[d,] or isinstance(ix, Method) or d == Index):
                        msg = (
                            f"[v{key.id}] {key}{dimension}{index}: "
                            f"index {ix} does not match any index of dimension {d.name}"
                        )
                        raise DimensionError(msg)

                value = self._data[key][dimension][index]
                if key.vtype is None or key.vtype == Any:
                    pass

                elif get_origin(key.vtype) in [list, set, tuple]:
                    # Validate iterable type
                    origin = get_origin(key.vtype)
                    if origin is not None and not isinstance(value, origin):
                        msg = (
                            f"[v{key.id}] {key}{dimension}{index}: "
                            f"expected {origin}, got {type(value)}, value={value}"
                        )
                        raise ValidationError(msg)

                    arg = get_args(key.vtype)[0]
                    if get_args(arg):
                        arg = get_args(arg)[0]

                    for v in value:
                        if isinstance(arg, Dimension):
                            if (v,) not in dim[arg,]:
                                msg = (
                                    f"[v{key.id}] {key}{dimension}{index}: "
                                    f"value {v} does not match any index of dimension {arg.name}"
                                )
                                raise ValidationError(msg)
                        elif not isinstance(v, arg):
                            msg = (
                                f"[v{key.id}] {key}{dimension}{index}: "
                                f"{get_origin(key.vtype)} expected elements of {arg}, "
                                f"got {type(v)}, value={v}"
                            )
                            raise ValidationError(msg)

                elif isinstance(key.vtype, Dimension):
                    if (value,) not in dim[key.vtype,]:
                        msg = (
                            f"[v{key.id}] {key}{dimension}{index}: "
                            f"value {value} does not match any index of dimension {key.vtype.name}"
                        )
                        raise ValidationError(msg)

                elif not isinstance(value, key.vtype):
                    msg = (
                        f"[v{key.id}] {key}{dimension}{index}: "
                        f"expected {key.vtype}, got {type(value)}, value={value}"
                    )
                    raise ValidationError(msg)
```

- [ ] **Step 3: Fix Method import issue**

The inlined code references `Method` and `Index` which need to be imported. Add to imports:

```python
from or_register import Dimension, Id, Parameter, Register, Method, Index
```

Edit line 5 to include `Method, Index`:
```python
from or_register import Dimension, Id, Parameter, Register, Method, Index
```

- [ ] **Step 4: Run mypy on or_scenario**

```bash
python -m mypy or_scenario/
```

Expected: No mypy errors

- [ ] **Step 5: Run or_scenario tests**

```bash
pytest tests/test_scenario.py::test_scenario_validate -v
pytest tests/test_scenario.py::test_scenario_validate_default_param -v
```

Expected: Both tests pass

- [ ] **Step 6: Commit validate() implementation**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: inline validation logic in Scenario.validate()"
```

---

## Task 7: Run full test suite

**Files:**
- Test: `tests/test_scenario.py`
- Test: `D:/github/register/tests/test_register.py`

- [ ] **Step 1: Run all or_scenario tests**

```bash
cd D:/github/or-scenario
pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 2: Run all register tests**

```bash
cd D:/github/register
pytest tests/ -v
```

Expected: All tests pass (validate tests removed)

- [ ] **Step 3: Run mypy on both packages**

```bash
# or_scenario
cd D:/github/or-scenario
python -m mypy or_scenario/

# register
cd D:/github/register
python -m mypy register/
```

Expected: No mypy errors in either package

- [ ] **Step 4: Verify mypy allows Register[Var] usage**

Create a temporary test file to verify type flexibility:

```bash
cd D:/github/or-scenario
cat > /tmp/test_register_var.py << 'EOF'
from or_register import Register
from typing import Any

class Var:
    vtype: Any

# This should not produce mypy errors
reg = Register[Var]()
EOF

python -m mypy /tmp/test_register_var.py
```

Expected: No mypy errors about type bounds

- [ ] **Step 5: Cleanup test file**

```bash
rm /tmp/test_register_var.py
```

---

## Task 8: Final verification and commit

- [ ] **Step 1: Check git status**

```bash
cd D:/github/or-scenario
git status
```

Expected: No uncommitted changes

- [ ] **Step 2: Run ruff checks**

```bash
cd D:/github/or-scenario
ruff check or_scenario/
```

Expected: No ruff errors

- [ ] **Step 3: Verify Register.validate() is gone**

```bash
cd D:/github/or-scenario
python -c "from or_register import Register; print(dir(Register))" | grep validate
```

Expected: No output (validate method should not exist)

- [ ] **Step 4: Verify Scenario.validate() works**

```bash
cd D:/github/or-scenario
python -c "
from or_scenario import Scenario
from or_register import Id, Index
scenario = Scenario()
scenario._data[Id][(Index,)][(1,)] = 1
scenario.validate()
print('Validation passed')
"
```

Expected: Output "Validation passed"

- [ ] **Step 5: Create summary of changes**

```bash
cd D:/github/or-scenario
git log --oneline -10
```

Review commits to ensure all changes are documented.

- [ ] **Step 6: Tag completion (optional)**

```bash
cd D:/github/or-scenario
git tag -a refactor/generic-register -m "Remove Parameter bound from Register, move validation to Scenario"
```

---

## Summary

This implementation plan:
1. Removes the `Parameter` bound from `Register` TypeVar
2. Removes `Register.validate()` method entirely
3. Removes all `Register.validate()` tests from register package
4. Rebuilds and reinstalls the register package wheel
5. Adds necessary imports to `or_scenario/scenario.py`
6. Inlines all validation logic into `Scenario.validate()`
7. Preserves all existing validation behavior and error types
8. Enables `Register[Var]` usage where `Var` has a `vtype` attribute

**Total estimated time:** 45-60 minutes
**Risk level:** Low (changes are isolated, user confirmed validation is exclusively used by Scenario)