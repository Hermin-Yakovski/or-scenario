# dump() Method Design Specification

**Date:** 2026-05-14
**Status:** Draft
**Phase:** 3 (Database Persistence)
**Version:** 0.3.0

## Overview

Add `dump()` method to `Scenario` class for persisting algorithm results from `Register[Parameter]` to database solution (sol) tables. Completes the OR workflow: load → solve → dump.

## Motivation

- Enable persisting optimization results to database for audit and analysis
- Support result sharing across scenarios and time periods
- Provide transaction-safe, atomic result storage

## Scope

**In Scope:**
- Add `dump(session, params, dimension, index)` method to Scenario class
- Atomic transaction: delete existing version_id records, insert new results
- Skip parameters that don't exist in Register
- Use convention-based sol table discovery

**Out of Scope:**
- Async version (adump) - deferred to future phase
- Complex filtering beyond single index tuple
- Batch operations beyond Set[Parameter]

## Design

### Method Signature

```python
from typing import Set, Tuple
from sqlalchemy.orm import Session
from register import Dimension, Parameter

class Scenario:
    def dump(self, 
             session: Session, 
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
```

### Sol Table Discovery

**Convention:** `Sol{Dim1}{Dim2}...` where dimensions are sorted alphabetically.

**Examples:**
- `(Product, Region)` → `SolProductRegion`
- `(District, Owner)` → `SolDistrictOwner`  
- `(District,)` → `SolDistrict`

**Implementation:**
```python
def _get_sol_table_name(dimension: Tuple[Dimension, ...]) -> str:
    """Generate sol table name from dimension tuple."""
    sorted_dims = sorted(dimension, key=lambda d: d.name.lower())
    return f"sol_{'_'.join(d.name.lower() for d in sorted_dims)}"
```

### Transaction Flow

1. **Begin transaction** - Open atomic transaction boundary
2. **Delete existing** - Remove all records where `version_id = self._version_id`
3. **Insert new** - For each param in `params`:
   - Check if value exists in Register at `(dimension, index)`
   - If exists, insert into sol table with:
     - `version_id` = `self._version_id`
     - `parameter_id` = from param
     - `quantity` = value from Register
     - `{dimension}_id` = from index tuple
   - If not exists, skip (no error)
4. **Commit transaction** - Atomic commit or rollback

### Versioning

Uses `self._version_id` which is set during initialization from `BaseRequest.request_id`.

**Raises:** `RuntimeError` if `self._version_id` is not set.

### Error Handling

| Condition | Behavior |
|-----------|----------|
| Param value doesn't exist at index | Skip param (continue with others) |
| Sol table doesn't exist | Propagate database error |
| Version_id not set | Raise RuntimeError |
| Database constraint violation | Propagate error |
| Transaction fails | Rollback all changes |

## Usage Example

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from or_scenario import Scenario
from or_scenario.orm import generate_dimension_table, generate_sol_table
from register import Dimension, Parameter

# Setup
DimProduct = generate_dimension_table("Product")
DimRegion = generate_dimension_table("Region")
SolProductRegion = generate_sol_table("Product", "Region")

Product = Dimension("Product", "产品", "PROD")
Region = Dimension("Region", "区域", "REG")
SalesVolume = Parameter(1, "sales_volume", "销量", float)

class SalesScenario(Scenario):
    def load(self, session: Session = None) -> None:
        # Load from database or files...
        pass

# Workflow
engine = create_engine("sqlite:///or.db")
SessionLocal = sessionmaker(bind=engine)

scenario = SalesScenario()
with SessionLocal() as session:
    # Load data
    scenario.load(session)
    
    # Solve
    scenario.set_algorithm(MyOptimizer)
    scenario.exec_algorithm()
    
    # Dump results
    scenario.dump(
        session, 
        {SalesVolume}, 
        (Product, Region), 
        (1, 2)
    )
```

## File Structure

**Modified files:**
- `or_scenario/scenario.py` - Add dump() method
- `tests/test_scenario.py` - Add dump() tests

## Dependencies

**Existing:**
- SQLAlchemy 2.0+ (already required for load())
- omni-orm 0.1.0+ (already required)

**No new dependencies.**

## Implementation Notes

- Sol table classes must be generated using omni_orm before calling dump()
- Dimension tuples are sorted alphabetically for table name consistency
- Transaction is atomic - either all params dumped or none
- Missing values in Register are silently skipped (not errors)

## Migration Notes

**Breaking changes:** None - additive feature only

**For existing users:**
- load() behavior unchanged
- New dump() method is optional
- No migration required unless using dump()

## Testing

**Test cases:**
1. Dump single parameter at specific index
2. Dump multiple parameters at same index
3. Skip missing parameter (value doesn't exist in Register)
4. Delete existing version_id records before insert
5. Transaction rollback on error
6. Version_id not set raises RuntimeError
7. Sol table name generation (alphabetical sorting)

## Next Phase

Phase 4 may include:
- Async version: `adump(session, params, dimension, index)`
- Batch operations: dump multiple index tuples
- Advanced filtering: dump by parameter value ranges
- Upsert modes: configurable update/insert behavior
