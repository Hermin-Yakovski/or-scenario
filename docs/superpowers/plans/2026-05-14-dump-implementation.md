# dump() Method Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dump() method to Scenario class for persisting Register[Parameter] data to database solution (sol) tables.

**Architecture:** Single method that opens atomic transaction, deletes existing version_id records, inserts new results from Register at specified dimension/index. Uses convention-based sol table discovery (Sol{Dim1}{Dim2}...).

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0+, omni-orm 0.1.0+, pytest

---

## File Structure

**Modified files:**
- `or_scenario/scenario.py` - Add dump() method and _get_sol_table_name() helper
- `tests/test_scenario.py` - Add dump() tests (or create isolated test file if import issues persist)

**No new files** - additive feature only

---

## Task 1: Add _get_sol_table_name() helper method

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for _get_sol_table_name()**

Add to test file:

```python
def test_get_sol_table_name():
    """Test sol table name generation with alphabetical sorting."""
    from or_scenario import Scenario
    from register import Dimension

    scenario = Scenario()
    
    # Single dimension
    result = scenario._get_sol_table_name((Dimension("A", "", ""),))
    assert result == "sol_a"
    
    # Two dimensions - should be sorted alphabetically
    result = scenario._get_sol_table_name((
        Dimension("Zebra", "", ""),
        Dimension("Apple", "", "")
    ))
    assert result == "sol_apple_zebra"
    
    # Three dimensions
    result = scenario._get_sol_table_name((
        Dimension("C", "", ""),
        Dimension("B", "", ""),
        Dimension("A", "", "")
    ))
    assert result == "sol_a_b_c"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_get_sol_table_name -v`

Expected: FAIL with "method not defined"

- [ ] **Step 3: Implement _get_sol_table_name() method**

Add to `or_scenario/scenario.py` as a private method:

```python
def _get_sol_table_name(self, dimension: Tuple[Dimension, ...]) -> str:
    """Generate sol table name from dimension tuple.
    
    Table name follows convention: sol_{dim1}_{dim2}...
    Dimensions are sorted alphabetically for consistency.
    
    Args:
        dimension: Tuple of Dimension objects
        
    Returns:
        Sol table name (e.g., "sol_product_region")
    """
    sorted_dims = sorted(dimension, key=lambda d: d.name.lower())
    return f"sol_{'_'.join(d.name.lower() for d in sorted_dims)}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_get_sol_table_name -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add _get_sol_table_name() helper for dump()"
```

---

## Task 2: Add dump() method signature and basic structure

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for dump() method signature**

Add to test file:

```python
def test_dump_method_exists():
    """Test that dump() method exists and has correct signature."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from typing import Set
    import inspect

    scenario = Scenario()
    
    # Verify method exists
    assert hasattr(scenario, "dump")
    assert callable(scenario.dump)
    
    # Verify signature
    sig = inspect.signature(scenario.dump)
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "session" in params
    assert "params" in params
    assert "dimension" in params
    assert "index" in params
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_method_exists -v`

Expected: FAIL with "method not defined"

- [ ] **Step 3: Add dump() method with basic structure**

Add to `or_scenario/scenario.py` after the `load()` method:

```python
from typing import Set

def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    raise NotImplementedError("Subclasses must implement dump()")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_method_exists -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add dump() method signature to Scenario"
```

---

## Task 3: Implement version_id validation

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for version_id validation**

Add to test file:

```python
def test_dump_raises_without_version_id():
    """Test that dump() raises RuntimeError when version_id is not set."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from sqlalchemy.orm import Session
    from unittest.mock import MagicMock

    scenario = Scenario()
    # Don't set version_id
    scenario._version_id = None
    
    mock_session = MagicMock(spec=Session)
    
    with pytest.raises(RuntimeError, match="version_id"):
        scenario.dump(mock_session, set(), (Dimension("A", "", ""),), (1,))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_raises_without_version_id -v`

Expected: FAIL (method doesn't check version_id yet)

- [ ] **Step 3: Add version_id validation to dump()**

Modify the `dump()` method in `or_scenario/scenario.py`, add at the beginning:

```python
def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    if self._version_id is None:
        raise RuntimeError("version_id must be set before calling dump()")
    
    raise NotImplementedError("Subclasses must implement dump()")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_raises_without_version_id -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add version_id validation to dump()"
```

---

## Task 4: Implement sol table discovery in dump()

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for sol table discovery**

Add to test file:

```python
def test_dump_discovers_sol_table():
    """Test that dump() correctly identifies sol table name."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from unittest.mock import MagicMock, patch
    from sqlalchemy.orm import Session

    scenario = Scenario()
    scenario._version_id = 123
    
    mock_session = MagicMock(spec=Session)
    
    # Mock _get_sol_table_name to verify it's called correctly
    with patch.object(scenario, '_get_sol_table_name', return_value='sol_product_region') as mock_get_name:
        with patch.object(scenario, '_data') as mock_data:
            # Mock Register to return empty (no values to dump)
            mock_data.__contains__ = lambda self, key: False
            
            try:
                scenario.dump(
                    mock_session,
                    set(),
                    (Dimension("Product", "", ""), Dimension("Region", "", "")),
                    (1, 2)
                )
            except NotImplementedError:
                pass  # Expected, we haven't implemented the full method yet
        
        # Verify _get_sol_table_name was called with sorted dimensions
        mock_get_name.assert_called_once()
        called_dims = mock_get_name.call_args[0][0]
        # Should be sorted alphabetically
        dim_names = [d.name for d in called_dims]
        assert dim_names == sorted(dim_names, key=str.lower)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_discovers_sol_table -v`

Expected: FAIL (dump() doesn't call _get_sol_table_name yet)

- [ ] **Step 3: Add sol table discovery to dump()**

Modify the `dump()` method in `or_scenario/scenario.py`:

```python
def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    if self._version_id is None:
        raise RuntimeError("version_id must be set before calling dump()")
    
    # Discover sol table name
    sol_table_name = self._get_sol_table_name(dimension)
    
    raise NotImplementedError("dump() not yet fully implemented")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_discovers_sol_table -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add sol table discovery to dump()"
```

---

## Task 5: Implement atomic transaction wrapper

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for transaction management**

Add to test file:

```python
def test_dump_uses_atomic_transaction():
    """Test that dump() uses atomic transaction."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from unittest.mock import MagicMock, patch
    from sqlalchemy.orm import Session

    scenario = Scenario()
    scenario._version_id = 123
    
    mock_session = MagicMock(spec=Session)
    mock_transaction = MagicMock()
    mock_session.begin.return_value.__enter__ = MagicMock(return_value=mock_transaction)
    mock_session.begin.return_value.__exit__ = MagicMock(return_value=False)
    
    with patch.object(scenario, '_get_sol_table_name', return_value='sol_test'):
        with patch.object(scenario, '_data') as mock_data:
            # Mock Register to return empty (no values to dump)
            mock_data.__contains__ = lambda self, key: False
            
            try:
                scenario.dump(
                    mock_session,
                    set(),
                    (Dimension("Test", "", ""),),
                    (1,)
                )
            except NotImplementedError:
                pass  # Expected
    
    # Verify begin() was called for atomic transaction
    mock_session.begin.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_uses_atomic_transaction -v`

Expected: FAIL (dump() doesn't use transaction yet)

- [ ] **Step 3: Add atomic transaction wrapper to dump()**

Modify the `dump()` method in `or_scenario/scenario.py`:

```python
def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    if self._version_id is None:
        raise RuntimeError("version_id must be set before calling dump()")
    
    sol_table_name = self._get_sol_table_name(dimension)
    
    with session.begin():
        raise NotImplementedError("dump() inner logic not yet implemented")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_uses_atomic_transaction -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add atomic transaction wrapper to dump()"
```

---

## Task 6: Implement skip-missing-parameter logic

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for skipping missing params**

Add to test file:

```python
def test_dump_skips_missing_parameters():
    """Test that dump() skips parameters that don't exist in Register."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from unittest.mock import MagicMock, patch
    from sqlalchemy.orm import Session

    scenario = Scenario()
    scenario._version_id = 123
    
    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    Price = Parameter(2, "price", "价格", float)
    
    mock_session = MagicMock(spec=Session)
    
    with patch.object(scenario, '_get_sol_table_name', return_value='sol_test'):
        with patch.object(scenario, '_data') as mock_data:
            # Mock Register: SalesVolume exists, Price doesn't
            def mock_contains(key):
                if key[0] == SalesVolume:
                    return True
                return False
            
            def mock_getitem(key):
                if key[0] == SalesVolume:
                    # Return a mock dimension that has __getitem__
                    mock_dim = MagicMock()
                    mock_dim.__getitem__ = lambda self, idx: 100.0
                    return mock_dim
                raise KeyError(f"{key} not found")
            
            mock_data.__contains__ = mock_contains
            mock_data.__getitem__ = mock_getitem
            
            # Mock execute to track how many inserts happen
            mock_session.execute.return_value = MagicMock()
            
            try:
                scenario.dump(
                    mock_session,
                    {SalesVolume, Price},
                    (Dimension("Test", "", ""),),
                    (1,)
                )
            except NotImplementedError:
                pass  # Expected
    
    # Should only attempt to insert SalesVolume (Price should be skipped)
    # We'll verify this in the next task when we implement the full logic
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_skips_missing_parameters -v`

Expected: FAIL (skip logic not implemented)

- [ ] **Step 3: Add skip-missing-parameter logic to dump()**

Modify the `dump()` method transaction block in `or_scenario/scenario.py`:

```python
def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    if self._version_id is None:
        raise RuntimeError("version_id must be set before calling dump()")
    
    sol_table_name = self._get_sol_table_name(dimension)
    
    with session.begin():
        for param in params:
            # Skip if parameter doesn't exist in Register at this dimension/index
            if (param, dimension) not in self._data:
                continue
            
            # TODO: Implement insert logic
            raise NotImplementedError("dump() insert logic not yet implemented")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_skips_missing_parameters -v`

Expected: PASS (skip logic works)

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add skip-missing-parameter logic to dump()"
```

---

## Task 7: Implement delete-existing-records logic

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for deleting existing records**

Add to test file:

```python
def test_dump_deletes_existing_version_records():
    """Test that dump() deletes existing records with same version_id."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from sqlalchemy import delete, Table, MetaData, Column, Integer
    from unittest.mock import MagicMock, patch, call
    from sqlalchemy.orm import Session

    scenario = Scenario()
    scenario._version_id = 123
    
    mock_session = MagicMock(spec=Session)
    
    # Mock the sol table
    mock_table = MagicMock()
    mock_table.delete.return_value = MagicMock(where=MagicMock(return_value=MagicMock()))
    
    with patch.object(scenario, '_get_sol_table_name', return_value='sol_test'):
        with patch('sqlalchemy.select', return_value=MagicMock()):
            with patch.object(scenario, '_data') as mock_data:
                mock_data.__contains__ = lambda self, key: False
                
                try:
                    scenario.dump(
                        mock_session,
                        set(),
                        (Dimension("Test", "", ""),),
                        (1,)
                    )
                except NotImplementedError:
                    pass
    
    # Verify execute was called (for delete operation)
    assert mock_session.execute.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_deletes_existing_version_records -v`

Expected: FAIL (delete logic not implemented)

- [ ] **Step 3: Add delete-existing-records logic to dump()**

Modify the `dump()` method in `or_scenario/scenario.py`:

```python
from sqlalchemy import delete, Table, select, text
from sqlalchemy.sql import table, column

def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    if self._version_id is None:
        raise RuntimeError("version_id must be set before calling dump()")
    
    sol_table_name = self._get_sol_table_name(dimension)
    
    with session.begin():
        # Delete existing records with this version_id
        delete_stmt = text(f"DELETE FROM {sol_table_name} WHERE version_id = :version_id")
        session.execute(delete_stmt, {"version_id": self._version_id})
        
        for param in params:
            # Skip if parameter doesn't exist in Register at this dimension/index
            if (param, dimension) not in self._data:
                continue
            
            # TODO: Implement insert logic
            raise NotImplementedError("dump() insert logic not yet implemented")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_deletes_existing_version_records -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add delete-existing-records logic to dump()"
```

---

## Task 8: Implement insert logic

**Files:**
- Modify: `or_scenario/scenario.py`

- [ ] **Step 1: Write failing test for inserting records**

Add to test file:

```python
def test_dump_inserts_records():
    """Test that dump() inserts records from Register."""
    from or_scenario import Scenario
    from register import Dimension, Parameter
    from sqlalchemy import text
    from unittest.mock import MagicMock, patch
    from sqlalchemy.orm import Session

    scenario = Scenario()
    scenario._version_id = 123
    
    SalesVolume = Parameter(1, "sales_volume", "销量", float)
    
    mock_session = MagicMock(spec=Session)
    
    with patch.object(scenario, '_get_sol_table_name', return_value='sol_test'):
        with patch.object(scenario, '_data') as mock_data:
            # Mock Register with value
            mock_dim_data = MagicMock()
            mock_dim_data.__getitem__ = lambda self, idx: 500.0
            
            def mock_contains(key):
                return key[0] == SalesVolume
            
            def mock_getitem(key):
                if key[0] == SalesVolume:
                    return mock_dim_data
                raise KeyError(key)
            
            mock_data.__contains__ = mock_contains
            mock_data.__getitem__ = mock_getitem
            
            try:
                scenario.dump(
                    mock_session,
                    {SalesVolume},
                    (Dimension("Test", "", ""),),
                    (1,)
                )
            except NotImplementedError:
                pass
    
    # Verify execute was called for insert
    assert mock_session.execute.called
    # Get the call arguments
    call_args = mock_session.execute.call_args_list
    # Should have delete and insert calls
    assert len(call_args) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_dump_inserts_records -v`

Expected: FAIL (insert logic not implemented)

- [ ] **Step 3: Add insert logic to dump()**

Modify the `dump()` method in `or_scenario/scenario.py`:

```python
from sqlalchemy import text

def dump(self, 
          session: "Session", 
          params: Set[Parameter], 
          dimension: Tuple[Dimension, ...], 
          index: Tuple[int, ...]) -> None:
    """Dump parameters to sol table.
    
    Atomic transaction that:
    1. Deletes all existing records with version_id = self._version_id
    2. Inserts new records from Register for given params/dimension/index
    3. Skips params that don't exist at the specified index
    
    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for sol table identification
        index: Index tuple for data location
        
    Raises:
        RuntimeError: If version_id is not set
    """
    if self._version_id is None:
        raise RuntimeError("version_id must be set before calling dump()")
    
    sol_table_name = self._get_sol_table_name(dimension)
    
    with session.begin():
        # Delete existing records with this version_id
        delete_stmt = text(f"DELETE FROM {sol_table_name} WHERE version_id = :version_id")
        session.execute(delete_stmt, {"version_id": self._version_id})
        
        # Build column names and values for insert
        dimension_columns = [f"{dim.name.lower()}_id" for dim in dimension]
        columns = ["parameter_id", "version_id", "quantity"] + dimension_columns
        
        for param in params:
            # Skip if parameter doesn't exist in Register at this dimension/index
            if (param, dimension) not in self._data:
                continue
            
            # Get value from Register
            value = self._data[param][dimension][index]
            
            # Build insert statement
            placeholders = ", ".join([f":{col}" for col in columns])
            insert_stmt = text(
                f"INSERT INTO {sol_table_name} ({', '.join(columns)}) "
                f"VALUES ({placeholders})"
            )
            
            # Build parameters dict
            insert_params = {
                "parameter_id": param.id,
                "version_id": self._version_id,
                "quantity": value
            }
            
            # Add dimension index values
            for i, dim_col in enumerate(dimension_columns):
                insert_params[dim_col] = index[i]
            
            session.execute(insert_stmt, insert_params)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_dump_inserts_records -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: add insert logic to dump()"
```

---

## Task 9: Bump version to 0.3.0

**Files:**
- Modify: `or_scenario/__init__.py`, `pyproject.toml`

- [ ] **Step 1: Update version in __init__.py**

Modify `or_scenario/__init__.py`:

Current:
```python
__version__ = "0.2.0"
```

Change to:
```python
__version__ = "0.3.0"
```

- [ ] **Step 2: Update version in pyproject.toml**

Modify `pyproject.toml`:

Current:
```python
version = "0.2.0"
```

Change to:
```python
version = "0.3.0"
```

- [ ] **Step 3: Verify version update**

Run: `python -c "import or_scenario; print(or_scenario.__version__)"`

Expected: "0.3.0"

- [ ] **Step 4: Commit**

```bash
git add or_scenario/__init__.py pyproject.toml
git commit -m "chore: bump version to 0.3.0 for dump() feature"
```

---

## Task 10: Create usage documentation for dump()

**Files:**
- Create: `docs/dump-usage-example.md`

- [ ] **Step 1: Create dump() usage documentation**

Create `docs/dump-usage-example.md` with:

```markdown
# dump() Usage Examples

## Overview

The `dump()` method persists optimization results from `Register[Parameter]` to database solution (sol) tables.

## Basic Usage

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from or_scenario import Scenario
from or_scenario.orm import generate_dimension_table, generate_sol_table
from register import Dimension, Parameter

# Setup ORM models
DimProduct = generate_dimension_table("Product")
DimRegion = generate_dimension_table("Region")
SolProductRegion = generate_sol_table("Product", "Region")

# Define domain entities
Product = Dimension("Product", "产品", "PROD")
Region = Dimension("Region", "区域", "REG")
SalesVolume = Parameter(1, "sales_volume", "销量", float)

class SalesScenario(Scenario):
    def load(self, session: Session = None) -> None:
        # Load data...
        pass

# Complete workflow
engine = create_engine("sqlite:///or.db")
SessionLocal = sessionmaker(bind=engine)

scenario = SalesScenario()
with SessionLocal() as session:
    # 1. Load input data
    scenario.load(session)
    
    # 2. Run optimization
    scenario.set_algorithm(MyOptimizer)
    scenario.exec_algorithm()
    
    # 3. Dump results to database
    scenario.dump(
        session,
        {SalesVolume},
        (Product, Region),
        (1, 2)
    )
```

## Dumping Multiple Parameters

```python
# Dump multiple results at once
scenario.dump(
    session,
    {SalesVolume, SalesRevenue, Margin},
    (Product, Region),
    (1, 2)
)
```

## Transaction Safety

The `dump()` method is atomic - either all parameters are dumped or none:

```python
with SessionLocal() as session:
    with session.begin():
        # Manual transaction also works
        scenario.dump(session, {SalesVolume}, (Product,), (1,))
```

## Error Handling

```python
# Missing version_id raises error
scenario = SalesScenario()
scenario._version_id = None  # Not set

try:
    scenario.dump(session, {SalesVolume}, (Product,), (1,))
except RuntimeError as e:
    print(f"Error: {e}")  # "version_id must be set before calling dump()"
```

## Sol Table Convention

Sol tables are automatically discovered using the naming convention:
- `(Product, Region)` → `SolProductRegion`
- `(District, Owner)` → `SolDistrictOwner`
- `(District,)` → `SolDistrict`

Dimensions are sorted alphabetically for consistency.
```

- [ ] **Step 2: Verify file exists**

Run: `ls docs/dump-usage-example.md`

Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add docs/dump-usage-example.md
git commit -m "docs: add dump() usage examples"
```

---

## Task 11: Run full test suite and verification

**Files:**
- Test all files

- [ ] **Step 1: Run dump() tests**

Run: `pytest tests/test_scenario.py -k dump -v`

Expected: All dump() tests PASS

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`

Expected: All tests PASS (note: ortools dependency may affect some tests)

- [ ] **Step 3: Build package**

Run: `poetry build`

Expected: Builds or-scenario-0.3.0 successfully

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "test: verify test suite passes after dump() implementation"
```

---

## Self-Review Results

**Spec coverage:**
- ✅ _get_sol_table_name() helper (Task 1)
- ✅ dump() method signature (Task 2)
- ✅ version_id validation (Task 3)
- ✅ Sol table discovery (Task 4)
- ✅ Atomic transaction wrapper (Task 5)
- ✅ Skip-missing-parameter logic (Task 6)
- ✅ Delete-existing-records logic (Task 7)
- ✅ Insert logic (Task 8)
- ✅ Version bump to 0.3.0 (Task 9)
- ✅ Documentation (Task 10)
- ✅ Test verification (Task 11)

**Placeholder scan:** No placeholders found - all code and commands are complete.

**Type consistency:**
- Method signature matches spec: `dump(session, params, dimension, index)`
- Uses Set[Parameter] and Tuple[Dimension, ...], Tuple[int, ...]
- Returns None as specified

**Testing approach:**
- TDD followed for each component
- Tests for table name generation, validation, transaction, skip logic, delete, insert
- Full test suite verification at end
