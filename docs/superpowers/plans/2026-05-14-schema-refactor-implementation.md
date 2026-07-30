# Schema Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Pydantic models (BaseRequest, BaseResponse) from scenario.py to schema.py to establish convention for domain-specific subclasses.

**Architecture:** Create new schema.py file with BaseRequest/BaseResponse, update scenario.py to import from schema, update __init__.py to export from canonical sources.

**Tech Stack:** Python 3.11+, pytest, pydantic

---

## File Structure

**New files:**
- `or_scenario/schema.py` - Pydantic models (BaseRequest, BaseResponse)

**Modified files:**
- `or_scenario/scenario.py` - Remove BaseRequest/BaseResponse definitions, import from schema
- `or_scenario/__init__.py` - Update imports to export from canonical sources

**No test files modified** - existing tests import from `or_scenario` package, which continues to work after refactor.

---

## Task 1: Create schema.py with BaseRequest class

**Files:**
- Create: `or_scenario/schema.py`

- [ ] **Step 1: Create schema.py file with BaseRequest**

Create the file `or_scenario/schema.py` with the following content:

```python
# or_scenario/schema.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request with common fields."""

    request_id: int = Field(
        default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")[:-4]),
        description="identity of the data",
    )
```

- [ ] **Step 2: Verify file syntax**

Run: `python -m py_compile or_scenario/schema.py`

Expected: SUCCESS - no syntax errors

- [ ] **Step 3: Commit**

```bash
git add or_scenario/schema.py
git commit -m "feat: add schema.py with BaseRequest class"
```

---

## Task 2: Add BaseResponse class to schema.py

**Files:**
- Modify: `or_scenario/schema.py`

- [ ] **Step 1: Add BaseResponse class**

Add the BaseResponse class after BaseRequest in `or_scenario/schema.py`:

```python
# or_scenario/schema.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request with common fields."""

    request_id: int = Field(
        default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")[:-4]),
        description="identity of the data",
    )


class BaseResponse(BaseModel):
    """Base response with common fields."""

    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")
```

- [ ] **Step 2: Verify file syntax**

Run: `python -m py_compile or_scenario/schema.py`

Expected: SUCCESS - no syntax errors

- [ ] **Step 3: Commit**

```bash
git add or_scenario/schema.py
git commit -m "feat: add BaseResponse class to schema.py"
```

---

## Task 3: Add import for schema in scenario.py

**Files:**
- Modify: `or_scenario/scenario.py:1-11`

- [ ] **Step 1: Add relative import for schema module**

Add the import statement after line 11 (after the existing imports, before BaseRequest class definition):

Current imports section (lines 1-11):
```python
# or_scenario/scenario.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple, Type
from datetime import datetime

from dal import DataHandler
from or_algo import Algorithm
from or_register import Dimension, Id, Parameter, Register  # type: ignore[import-untyped]
from pydantic import BaseModel, Field
```

Add this import after line 11:
```python
from .schema import BaseRequest, BaseResponse
```

The imports section should now end with:
```python
from dal import DataHandler
from or_algo import Algorithm
from or_register import Dimension, Id, Parameter, Register  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from .schema import BaseRequest, BaseResponse
```

- [ ] **Step 2: Verify file syntax**

Run: `python -m py_compile or_scenario/scenario.py`

Expected: SUCCESS - no syntax errors (note: duplicate BaseRequest/BaseResponse will exist temporarily)

- [ ] **Step 3: Commit**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: import BaseRequest and BaseResponse from schema module"
```

---

## Task 4: Remove BaseRequest class definition from scenario.py

**Files:**
- Modify: `or_scenario/scenario.py:14-17`

- [ ] **Step 1: Delete BaseRequest class definition**

Remove lines 14-17 (the BaseRequest class definition):

Delete:
```python
class BaseRequest(BaseModel):
    """Base request with common fields."""

    request_id: int = Field(
        default_factory=lambda: int(datetime.now().strftime("%y%m%d%H%M%S%f")[:-4]),
        description="identity of the data",
    )
```

The file should now have the BaseResponse class immediately after the imports.

- [ ] **Step 2: Verify tests still pass**

Run: `pytest tests/test_scenario.py -v`

Expected: All tests PASS (BaseRequest is now imported from schema)

- [ ] **Step 3: Commit**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: remove BaseRequest definition, use import from schema"
```

---

## Task 5: Remove BaseResponse class definition from scenario.py

**Files:**
- Modify: `or_scenario/scenario.py:14-20`

- [ ] **Step 1: Delete BaseResponse class definition**

Remove the BaseResponse class definition (now at lines 14-20 after removing BaseRequest):

Delete:
```python
class BaseResponse(BaseModel):
    """Base response with common fields."""

    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")
```

The file should now have the Scenario class immediately after the imports.

- [ ] **Step 2: Verify tests still pass**

Run: `pytest tests/test_scenario.py -v`

Expected: All tests PASS (BaseResponse is now imported from schema)

- [ ] **Step 3: Commit**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: remove BaseResponse definition, use import from schema"
```

---

## Task 6: Remove unused pydantic imports from scenario.py

**Files:**
- Modify: `or_scenario/scenario.py:11`

- [ ] **Step 1: Remove unused pydantic imports**

Since BaseModel and Field are no longer used in scenario.py (they're only in schema.py now), remove them from the imports:

Current line 11:
```python
from pydantic import BaseModel, Field
```

Replace with:
```python
# pydantic imports removed - now in schema.py
```

Or simply delete line 11 entirely.

- [ ] **Step 2: Verify tests still pass**

Run: `pytest tests/test_scenario.py -v`

Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add or_scenario/scenario.py
git commit -m "refactor: remove unused pydantic imports from scenario.py"
```

---

## Task 7: Update __init__.py to import from canonical source

**Files:**
- Modify: `or_scenario/__init__.py:3-4`

- [ ] **Step 1: Update imports in __init__.py**

Current content of `or_scenario/__init__.py`:
```python
"""or-scenario: Template framework for Operations Research workflows."""

from .scenario import BaseRequest, BaseResponse, Scenario

__all__ = ["Scenario", "BaseRequest", "BaseResponse"]
__version__ = "0.1.0"
```

Update the imports to source from canonical locations:

```python
"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse
from .scenario import Scenario

__all__ = ["Scenario", "BaseRequest", "BaseResponse"]
__version__ = "0.1.0"
```

- [ ] **Step 2: Verify package imports work**

Run: `python -c "from or_scenario import BaseRequest, BaseResponse, Scenario; print('Imports successful')"`

Expected: SUCCESS - prints "Imports successful"

- [ ] **Step 3: Commit**

```bash
git add or_scenario/__init__.py
git commit -m "refactor: update __init__ imports from canonical sources"
```

---

## Task 8: Verify backward compatibility - import from scenario module

**Files:**
- Test: `or_scenario/scenario.py`, `or_scenario/schema.py`

- [ ] **Step 1: Verify direct import from scenario module works**

Run: `python -c "from or_scenario.scenario import BaseRequest, BaseResponse, Scenario; print('Direct imports successful')"`

Expected: SUCCESS - prints "Direct imports successful"

This verifies that even though BaseRequest/BaseResponse are defined in schema.py, they can still be imported from scenario.py due to the import statement.

- [ ] **Step 2: Verify direct import from schema module**

Run: `python -c "from or_scenario.schema import BaseRequest, BaseResponse; print('Schema imports successful')"`

Expected: SUCCESS - prints "Schema imports successful"

- [ ] **Step 3: Commit if all verifications pass**

```bash
# No changes to commit - this is a verification step
```

---

## Task 9: Run full test suite

**Files:**
- Test all files

- [ ] **Step 1: Run complete test suite**

Run: `pytest tests/ -v`

Expected: All tests PASS (no test changes needed - they import from or_scenario package)

- [ ] **Step 2: Run coverage check**

Run: `pytest --cov=or_scenario tests/`

Expected: Coverage at 100%

- [ ] **Step 3: Final verification commit**

```bash
git add -A
git commit -m "test: verify full test suite passes after schema refactor"
```

---

## Task 10: Verify module exports

**Files:**
- Test: `or_scenario/__init__.py`

- [ ] **Step 1: Verify __all__ exports correctly**

Run: `python -c "import or_scenario; assert sorted(or_scenario.__all__) == sorted(['BaseRequest', 'BaseResponse', 'Scenario']); print('__all__ exports verified')"`

Expected: SUCCESS - prints "__all__ exports verified"

- [ ] **Step 2: Verify each exported item is accessible**

Run: `python -c "from or_scenario import *; assert 'BaseRequest' in dir(); assert 'BaseResponse' in dir(); assert 'Scenario' in dir(); print('Wildcard imports verified')"`

Expected: SUCCESS - prints "Wildcard imports verified"

- [ ] **Step 3: Commit if needed**

```bash
# No changes to commit - this is a verification step
```

---

## Self-Review Results

**Spec coverage:**
- ✓ Create schema.py file (Task 1)
- ✓ Add BaseRequest to schema.py (Task 1)
- ✓ Add BaseResponse to schema.py (Task 2)
- ✓ Import from schema in scenario.py (Task 3)
- ✓ Remove BaseRequest definition from scenario.py (Task 4)
- ✓ Remove BaseResponse definition from scenario.py (Task 5)
- ✓ Remove unused pydantic imports (Task 6)
- ✓ Update __init__.py imports (Task 7)
- ✓ Testing verification (Tasks 8-10)

**Placeholder scan:** No placeholders found - all code and commands are complete.

**Type consistency:** All imports and class definitions match the spec. BaseRequest and BaseResponse are identical to their original definitions.

**Testing approach:** Existing tests require no changes because they import from the `or_scenario` package level, which continues to export the same symbols after the refactor.
