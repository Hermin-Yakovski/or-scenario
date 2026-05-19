# dump() Method Implementation Plan (Revised)

> **Note:** This plan documents the final implementation after refactoring.
> The original implementation used an `index` parameter and managed transactions internally.
> The revised implementation removes the `index` parameter (dumps all indexes), adds a `fact` parameter,
> and lets the caller control transaction boundaries.

**Goal:** Add dump() method to Scenario class for persisting Register[Parameter] data to database solution (sol) or fact tables.

**Architecture:** Single method that deletes existing version_id/snapshot_id records, inserts new results from Register for all indexes at given params/dimension. Uses convention-based table discovery and lets caller manage transactions.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0+, omni-orm 0.1.0+, pytest

---

## File Structure

**Modified files:**
- `or_scenario/scenario.py` - Add dump() method
- `or_scenario/orm.py` - Ensure generate_fact_table is exported

**Modified tests:**
- `tests/test_scenario.py` - Update dump() tests for new signature

---

## Implementation Details

### Method Signature

```python
def dump(self,
         session: "Session",
         params: Set[Parameter],
         dimension: Tuple[Dimension, ...],
         fact: bool = False,
) -> None:
```

**Parameters:**
- `session`: SQLAlchemy session (caller manages transaction)
- `params`: Set of parameters to dump
- `dimension`: Dimension tuple for table identification
- `fact`: If True, dump to fact table using snapshot_id column. If False, dump to sol table using version_id column.

### Key Implementation Points

1. **Dynamic table generation**: Uses `generate_fact_table()` or `generate_sol_table()` based on `fact` parameter
2. **Dynamic column selection**: Uses `snapshot_id` or `version_id` based on `fact` parameter
3. **All indexes**: Iterates over all indexes using `Register.select(param, dimension)`
4. **No transaction management**: Caller controls transaction boundaries
5. **Skip missing**: Parameters/dimensions not in Register are silently skipped

### Implementation

```python
def dump(self,
         session: "Session",
         params: Set[Parameter],
         dimension: Tuple[Dimension, ...],
         fact: bool = False,
) -> None:
    """Dump parameters to sol or fact table.

    Deletes all existing records with version_id/snapshot_id = self._version_id,
    then inserts new records from Register for given params/dimension.
    Skips params that don't exist in Register.

    Caller is responsible for transaction management.

    Args:
        session: SQLAlchemy session
        params: Set of parameters to dump
        dimension: Dimension tuple for table identification
        fact: If True, dump to fact table using snapshot_id column.
              If False, dump to sol table using version_id column.
    """
    identifier: str = 'snapshot_id' if fact else 'version_id'

    # Generate the table class dynamically
    dimension_names = [dim.name for dim in dimension]
    table = generate_fact_table(*dimension_names) if fact else generate_sol_table(*dimension_names)

    # Delete existing records with this version_id/snapshot_id
    session.query(table).filter(getattr(table, identifier) == self._version_id).delete()

    # Collect all records to insert
    records = []
    for param in params:
        for index in self._data.select(param, dimension):
            row = {
                "parameter_id": param.id,
                identifier: self._version_id,
                "quantity": self._data[param][dimension][index],
            }
            for i, dim in enumerate(dimension):
                row[f"{dim.name.lower()}_id"] = index[i]
            records.append(table(**row))

    if records:
        session.add_all(records)
```

---

## Test Coverage

### test_dump_method_exists
Verifies the method signature includes `session`, `params`, `dimension`, and `fact` parameters.

### test_dump_skips_missing_parameters
Tests that parameters not present in Register are skipped without error.

### test_dump_deletes_existing_version_records
Tests that existing records with the same version_id are deleted before insert.

### test_dump_uses_fact_table_when_fact_true
Tests that `fact=True` uses `generate_fact_table()` and `snapshot_id` column.

### test_dump_inserts_records_for_all_indexes
Tests that all indexes for a parameter/dimension are dumped, not just one.

---

## Usage Examples

### Sol Table (fact=False, default)

```python
with SessionLocal() as session:
    with session.begin():  # Caller manages transaction
        scenario.dump(
            session,
            {SalesVolume},
            (Product, Region),
            fact=False  # Default
        )
```

### Fact Table (fact=True)

```python
with SessionLocal() as session:
    with session.begin():  # Caller manages transaction
        scenario.dump(
            session,
            {SalesVolume},
            (Product, Region),
            fact=True  # Uses fact table and snapshot_id
        )
```

### Multiple Parameters in One Transaction

```python
with SessionLocal() as session:
    with session.begin():
        scenario.dump(session, {SalesVolume}, (Product, Region), fact=False)
        scenario.dump(session, {Inventory}, (Product, Warehouse), fact=False)
        # Both dumps succeed or both roll back together
```

---

## Changes from Original Design

| Aspect | Original | Revised |
|--------|----------|---------|
| `index` parameter | Required tuple | Removed - dumps all indexes |
| `fact` parameter | Not present | Added - switches between sol/fact tables |
| Transaction management | Internal `with session.begin()` | Caller controls |
| `_get_sol_table_name()` helper | Used for table name | Removed - use generate_*_table() directly |
| Column name | Fixed `version_id` | Dynamic (`version_id` or `snapshot_id`) |
| Index iteration | Single index from parameter | `Register.select()` for all indexes |

---

## Verification

Run tests:
```bash
pytest tests/test_scenario.py -k dump -v
```

Expected: All dump tests pass.