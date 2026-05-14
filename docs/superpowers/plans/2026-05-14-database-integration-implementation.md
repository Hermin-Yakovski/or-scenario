# Database Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add database loading capability to or_scenario via omni_orm integration, enabling scenarios to load data from SQLAlchemy ORM models into Register[Parameter].

**Architecture:** Create orm/ package as omni_orm proxy, add load(session: Session) method to Scenario base class. Subclasses define their own omni_orm models and override load() with manual ORM-to-Register mapping. Caller manages transactions.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0+, omni-orm 0.1.0+, pytest

---

## File Structure

**New files:**
- `or_scenario/orm/__init__.py` - omni_orm proxy package re-exporting factory functions

**Modified files:**
- `or_scenario/__init__.py` - Add orm export, bump version to 0.2.0
- `or_scenario/scenario.py` - Add load(session: Session) method signature
- `tests/test_scenario.py` - Add tests for orm proxy and load(session) signature

---

## Task 1: Create orm package directory

**Files:**
- Create: `or_scenario/orm/__init__.py`

- [ ] **Step 1: Create orm package directory**

Run: `mkdir -p or_scenario/orm`

Expected: Directory created successfully

- [ ] **Step 2: Create __init__.py with omni_orm proxy**

Create `or_scenario/orm/__init__.py` with:

```python
"""omni_orm proxy for or-scenario consumers.

Convenience re-exports of omni_orm factory functions.
Consumers can also import directly from omni_orm if preferred.
"""

from omni_orm import (
    generate_dimension_table,
    generate_fact_table,
    generate_sol_table,
)

__all__ = [
    "generate_dimension_table",
    "generate_fact_table",
    "generate_sol_table",
]
```

- [ ] **Step 3: Verify syntax**

Run: `python -m py_compile or_scenario/orm/__init__.py`

Expected: SUCCESS - no syntax errors

- [ ] **Step 4: Test import works**

Run: `python -c "from or_scenario.orm import generate_dimension_table, generate_fact_table, generate_sol_table; print('Import successful')"`

Expected: Prints "Import successful"

- [ ] **Step 5: Commit**

```bash
git add or_scenario/orm/__init__.py
git commit -m "feat: add orm package as omni_orm proxy"
```

---

## Task 2: Update __init__.py to export orm and bump version

**Files:**
- Modify: `or_scenario/__init__.py`

- [ ] **Step 1: Update imports and version**

Current content of `or_scenario/__init__.py`:
```python
"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse
from .scenario import Scenario

__all__ = ["Scenario", "BaseRequest", "BaseResponse"]
__version__ = "0.1.0"
```

Replace with:
```python
"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse
from .scenario import Scenario

# Re-export orm proxy for convenience
from . import orm  # type: ignore

__all__ = ["Scenario", "BaseRequest", "BaseResponse", "orm"]
__version__ = "0.2.0"
```

- [ ] **Step 2: Verify syntax**

Run: `python -m py_compile or_scenario/__init__.py`

Expected: SUCCESS - no syntax errors

- [ ] **Step 3: Test package imports work**

Run: `python -c "from or_scenario import orm; print('orm export:', orm); print('version:', or_scenario.__version__)"`

Expected: Prints "orm export: <module 'or_scenario.orm'...>" and "version: 0.2.0"

- [ ] **Step 4: Commit**

```bash
git add or_scenario/__init__.py
git commit -m "feat: export orm proxy, bump version to 0.2.0"
```

---

## Task 3: Add load(session: Session) method to Scenario class

**Files:**
- Modify: `or_scenario/scenario.py:121-127`

- [ ] **Step 1: Import Session type**

Add import to imports section of `or_scenario/scenario.py` (around line 6, after existing typing imports):

Current imports section:
```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Tuple, Type
from datetime import datetime
```

Add after line 6:
```python
from typing import TYPE_CHECKING
```

Then add after the datetime import:
```python
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
```

The imports section should now include the TYPE_CHECKING import and conditional Session import.

- [ ] **Step 2: Add load(session) method before existing load() method**

Find the existing `load()` method at line 121-127:
```python
def load(self) -> None:
    """Execute all load steps to populate scenario data.

    Subclasses should override this method to call their specific
    decorated load methods in the desired order.
    """
    raise NotImplementedError("Subclasses must implement load()")
```

Add the new `load(session)` method BEFORE the existing `load()` method:

```python
def load(self, session: "Session") -> None:
    """Load scenario data from database.

    Caller manages transaction boundaries.

    Args:
        session: SQLAlchemy session with active transaction

    Raises:
        NotImplementedError: Subclass must override
    """
    raise NotImplementedError("Subclasses must implement load(session)")
```

The file should now have both `load(session)` and the original `load()` methods.

- [ ] **Step 3: Verify syntax**

Run: `python -m py_compile or_scenario/scenario.py`

Expected: SUCCESS - no syntax errors

- [ ] **Step 4: Test Scenario still works**

Run: `python -c "from or_scenario import Scenario; print('Scenario import successful')"`

Expected: Prints "Scenario import successful"

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py
git commit -m "feat: add load(session: Session) method to Scenario"
```

---

## Task 4: Add simplified tests for orm proxy

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Write test for orm proxy**

Add to `tests/test_scenario.py`:

```python
def test_orm_proxy():
    """Test that orm proxy re-exports omni_orm factory functions."""
    from or_scenario.orm import generate_dimension_table, generate_fact_table

    # Verify factory functions work
    DimDistrict = generate_dimension_table("District")
    FactDistrictOwner = generate_fact_table("District", "Owner")

    assert DimDistrict.__name__ == "DimDistrict"
    assert FactDistrictOwner.__name__ == "FactDistrictOwner"
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_orm_proxy -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: add test for orm proxy"
```

---

## Task 5: Add test for load(session) method

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Write test for load(session) method**

Add to `tests/test_scenario.py`:

```python
def test_scenario_load_session():
    """Test that load(session) raises NotImplementedError by default."""
    from or_scenario import Scenario
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    scenario = Scenario()

    with pytest.raises(NotImplementedError, match="load\\(session\\)"):
        scenario.load(mock_session)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_load_session -v`

Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/test_scenario.py -v`

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: add test for load(session) method"
```

---

## Task 6: Add omni_orm to dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Check current dependencies**

Run: `cat pyproject.toml | grep -A 20 "dependencies"`

Expected: Shows current dependencies list

- [ ] **Step 2: Add omni-orm dependency**

Find the dependencies section in `pyproject.toml`. Add omni-orm to the dependencies list.

If it looks like:
```toml
dependencies = [
    "register>=0.1.0",
    "or-algo>=0.2.0",
    "data-access-layer>=0.1.0",
    "pydantic>=2.0.0",
]
```

Add omni-orm:
```toml
dependencies = [
    "register>=0.1.0",
    "or-algo>=0.2.0",
    "data-access-layer>=0.1.0",
    "pydantic>=2.0.0",
    "omni-orm>=0.1.0",
]
```

- [ ] **Step 3: Verify pyproject.toml is valid**

Run: `python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"`

Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add omni-orm>=0.1.0 dependency"
```

---

## Task 7: Create usage example documentation

**Files:**
- Create: `docs/database-loading-example.md`

- [ ] **Step 1: Create usage example documentation**

Create `docs/database-loading-example.md` with:

```markdown
# Database Loading Example

This example shows how to use omni_orm integration for database-backed scenarios.

## Setup

First, define your ORM models using omni_orm factories:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from or_scenario import Scenario
from or_scenario.orm import generate_dimension_table, generate_fact_table

# Define dimension tables
DimProduct = generate_dimension_table("Product")
DimRegion = generate_dimension_table("Region")

# Define fact table
FactSales = generate_fact_table("Product", "Region")
```

## Create Scenario Subclass

Override the `load(session)` method to fetch from database:

```python
from sqlalchemy import select
from register import Dimension, Parameter

# Define domain-specific dimensions
Product = Dimension("Product", "产品", "PROD")
Region = Dimension("Region", "区域", "REG")

# Define domain-specific parameters
SalesVolume = Parameter(1, "sales_volume", "销量", float)

class SalesScenario(Scenario):
    def load(self, session: Session) -> None:
        # Load dimensions
        products = session.execute(select(DimProduct)).scalars().all()
        regions = session.execute(select(DimRegion)).scalars().all()
        
        # Load facts for this snapshot
        facts = session.execute(
            select(FactSales).where(
                FactSales.snapshot_id == self._request.request_id
            )
        ).scalars().all()
        
        # Map to Register
        for fact in facts:
            self.set(
                SalesVolume,
                (Product, Region),
                (fact.product_id, fact.region_id),
                fact.quantity
            )
```

## Usage

```python
# Setup database connection
engine = create_engine("sqlite:///or.db")
SessionLocal = sessionmaker(bind=engine)

# Create and load scenario
scenario = SalesScenario()
with SessionLocal() as session:
    with session.begin():
        scenario.load(session)

# Use the scenario
scenario.set_algorithm(MySolver)
scenario.exec_algorithm()
```

## Mixed File/Database Loading

You can mix file-based and database-based loading:

```python
class MixedScenario(Scenario):
    def load(self, session: Session) -> None:
        # Load reference data from files
        self._load_reference_data(handler, path)
        
        # Load transactional data from database
        self._load_facts(session)
```
```

- [ ] **Step 2: Verify file exists**

Run: `ls docs/database-loading-example.md`

Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add docs/database-loading-example.md
git commit -m "docs: add database loading example documentation"
```

---

## Task 8: Final verification

**Files:**
- Test all files

- [ ] **Step 1: Run complete test suite**

Run: `pytest tests/ -v`

Expected: All tests PASS

- [ ] **Step 2: Final commit**

```bash
git add -A
git commit -m "test: verify test suite passes after database integration"
```

---

## Self-Review Results

**Spec coverage:**
- ✅ orm/ package as omni_orm proxy (Task 1)
- ✅ load(session: Session) method signature (Task 3)
- ✅ Update __init__.py exports and version (Task 2)
- ✅ Tests for orm proxy (Task 4)
- ✅ Tests for load(session) (Task 5)
- ✅ Dependencies updated (Task 6)
- ✅ Documentation example (Task 7)
- ✅ Full test suite verification (Task 8)

**Placeholder scan:** No placeholders found - all code and commands are complete.

**Type consistency:**
- Session imported via TYPE_CHECKING for type hints
- Method signature consistent: `load(session: "Session") -> None`
- Error message consistent: "Subclasses must implement load(session)"

**Testing approach:**
- Simplified orm proxy test verifies factory functions work
- Simplified load(session) test verifies NotImplementedError is raised
- Existing tests continue to pass (no behavioral changes to file-based loading)
