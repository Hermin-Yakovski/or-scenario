# dump() Method Design Specification

**Date:** 2026-05-14
**Status:** Implemented
**Phase:** 3 (Database Persistence)
**Version:** 0.3.0
**Updated:** 2026-05-19

## Overview

Add `dump()` method to `Scenario` class for persisting algorithm results from `Register[Parameter]` to database solution (sol) or fact tables. Completes the OR workflow: load → solve → dump.

## Motivation

- Enable persisting optimization results to database for audit and analysis
- Support result sharing across scenarios and time periods
- Support both sol tables (version-based) and fact tables (snapshot-based)
- Allow caller-controlled transaction boundaries for flexibility

## Scope

**In Scope:**
- Add `dump(session, params, dimension, fact=False)` method to Scenario class
- Delete existing version_id/snapshot_id records, insert new results
- Skip parameters that don't exist in Register
- Use convention-based sol/fact table discovery
- Caller controls transaction boundaries

**Out of Scope:**
- Async version (adump) - deferred to future phase
- Complex filtering beyond parameter sets

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
             fact: bool = False) -> None:
        """Dump parameters to sol or fact table.

        Deletes all existing records with version_id/snapshot_id = self._version_id,
        then inserts new records from Register for given params/dimension.
        Iterates over all indexes for each parameter/dimension combination.
        Skips params that don't exist in Register.

        Caller is responsible for transaction management.

        Args:
            session: SQLAlchemy session
            params: Set of parameters to dump
            dimension: Dimension tuple for table identification
            fact: If True, dump to fact table using snapshot_id column.
                  If False, dump to sol table using version_id column.
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

**Caller controls transaction boundaries.** Method does NOT manage transactions.

Within the caller's transaction:

1. **Delete existing** - Remove all records where `version_id/snapshot_id = self._version_id`
2. **Insert new** - For each param in `params`:
   - For each index in Register at `(param, dimension)`:
     - Insert into sol/fact table with:
       - `version_id` or `snapshot_id` = `self._version_id` (based on `fact` param)
       - `parameter_id` = from param
       - `quantity` = value from Register
       - `{dimension}_id` = from index tuple
   - If parameter/dimension doesn't exist, skip (no error)

### Versioning

Uses `self._version_id` which is set during initialization from `BaseRequest.request_id`.

**Column selection:**
- When `fact=False`: uses `version_id` column (sol tables)
- When `fact=True`: uses `snapshot_id` column (fact tables)

### Error Handling

| Condition | Behavior |
|-----------|----------|
| Param/dimension doesn't exist in Register | Skip param (continue with others) |
| Sol/fact table doesn't exist | Propagate database error |
| Database constraint violation | Propagate error |
| Transaction failures | Caller handles rollback |

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
    with session.begin():  # Caller controls transaction
        # Load data
        scenario.load(session)

        # Solve
        scenario.set_algorithm(MyOptimizer)
        scenario.exec_algorithm()

        # Dump results to sol table (version_id column)
        scenario.dump(
            session,
            {SalesVolume},
            (Product, Region),
            fact=False
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
1. Dump single parameter across all indexes
2. Dump multiple parameters at same dimension
3. Skip missing parameter (parameter doesn't exist in Register)
4. Delete existing version_id records before insert
5. Delete existing snapshot_id records when fact=True
6. Sol table name generation (alphabetical sorting)
7. Caller controls transaction boundaries

## Next Phase

Phase 4 may include:
- Async version: `adump(session, params, dimension, fact=False)`
- Advanced filtering: dump by parameter value ranges
- Upsert modes: configurable update/insert behavior
