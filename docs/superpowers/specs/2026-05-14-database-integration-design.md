# Database Integration Design: omni_orm Support

**Date:** 2026-05-14
**Status:** Draft
**Phase:** 2 of 2 (Database Integration)
**Version:** 0.2.0

## Overview

Add database loading capability to `or_scenario` via omni_orm integration. Enables scenarios to load data from SQLAlchemy ORM models into `Register[Parameter]` alongside existing file-based loading.

## Motivation

- Enable database-backed scenarios alongside file-based scenarios
- Support mixed loading scenarios (database + files in single load)
- Provide convenient access to omni_orm factory functions
- Maintain backward compatibility with existing file-based loading

## Scope

**In Scope:**
- Add `load(session: Session)` method to `Scenario` base class
- Create `or_scenario.orm` proxy package for omni_orm access
- Support manual ORM-to-Register mapping in subclasses
- Mixed file/database loading in single `load()` call

**Out of Scope (deferred):**
- `aload(session: AsyncSession)` - async database loading
- ORM-to-Register helper functions - manual mapping only
- Persist scenarios to database - read-only for now
- Transaction management - caller handles
- Error wrapping - propagate raw exceptions

## Design

### File Structure

```
or_scenario/
├── __init__.py          # Exports: Scenario, orm (updated)
├── scenario.py          # Modified: load(session: Session)
├── schema.py            # Pydantic models (unchanged)
└── orm/                 # NEW: omni_orm proxy package
    └── __init__.py      # Re-exports omni_orm factories
```

### Core API Changes

**scenario.py:**

```python
from typing import Optional
from sqlalchemy.orm import Session

class Scenario:
    # ... existing attributes unchanged ...
    
    def load(self, session: Session) -> None:
        """Load scenario data from database.
        
        Caller manages transaction boundaries.
        
        Args:
            session: SQLAlchemy session with active transaction
            
        Raises:
            NotImplementedError: Subclass must override
        """
        raise NotImplementedError("Subclasses must implement load(session)")
```

### Subclass Pattern

Subclasses define their own omni_orm models and override `load()`:

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from or_scenario import Scenario
from or_scenario.orm import generate_dimension_table, generate_fact_table

# Subclass defines its own models
DimDistrict = generate_dimension_table("District")
DimOwner = generate_dimension_table("Owner")
FactDistrictOwner = generate_fact_table("District", "Owner")

class MyScenario(Scenario):
    def load(self, session: Session) -> None:
        """Load from database and files."""
        # File-based (existing DataHandler pattern)
        self._load_from_files(handler, path)
        
        # Database-based
        self._load_districts(session)
        self._load_facts(session)
    
    def _load_districts(self, session: Session) -> None:
        districts = session.execute(select(DimDistrict)).scalars().all()
        for d in districts:
            self.set(SomeParam, (District,), (d.id,), d.value)
    
    def _load_facts(self, session: Session) -> None:
        facts = session.execute(
            select(FactDistrictOwner).where(
                FactDistrictOwner.snapshot_id == self._request.request_id
            )
        ).scalars().all()
        
        for f in facts:
            self.set(SalesVolume, (District, Owner), 
                    (f.district_id, f.owner_id), f.quantity)
```

### orm/ Package

**or_scenario/orm/__init__.py:**

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

**or_scenario/__init__.py:**

```python
"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse
from .scenario import Scenario

# Re-export orm proxy for convenience
from . import orm  # type: ignore

__all__ = ["Scenario", "BaseRequest", "BaseResponse", "orm"]
__version__ = "0.2.0"
```

## Design Decisions

### 1. Required Session Parameter
`load(session: Session)` requires session, no default. Caller must provide explicit database connection.

**Rationale:** Dependency injection, easier testing, explicit lifecycle management.

### 2. Caller Manages Transactions
No automatic `begin()/commit()` inside `load()`. Caller wraps in transaction if needed.

**Rationale:** Maximum flexibility for composable operations, explicit boundaries.

### 3. Manual ORM-to-Register Mapping
No automatic mapping helpers. Subclasses write explicit SQLAlchemy queries and `self.set()` calls.

**Rationale:** Keep it simple, defer complexity until real use cases emerge.

### 4. orm/ Proxy Package
Re-export omni_orm factories for convenience, but consumers can import from omni_orm directly.

**Rationale:** Convenience import path, no lock-in.

### 5. Mixed File/Database Loading
Single `load()` call can mix file-based `_load_*()` helpers and database-backed `_load_*(session)` helpers.

**Rationale:** Real-world scenarios often need both sources.

## Usage Example

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from or_scenario import Scenario
from or_scenario.orm import generate_dimension_table, generate_fact_table

# Define models
DimProduct = generate_dimension_table("Product")
DimRegion = generate_dimension_table("Region")
FactSales = generate_fact_table("Product", "Region")

class SalesScenario(Scenario):
    def load(self, session: Session) -> None:
        # Load dimensions first
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

# Usage
engine = create_engine("sqlite:///or.db")
SessionLocal = sessionmaker(bind=engine)

scenario = SalesScenario()
with SessionLocal() as session:
    with session.begin():
        scenario.load(session)

# Now use the scenario
scenario.set_algorithm(MySolver)
scenario.exec_algorithm()
```

## Dependencies

**New:**
- `omni-orm` >= 0.1.0
- `sqlalchemy` >= 2.0 (transitive via omni-orm)

**Existing:**
- No changes to existing dependencies

## Migration Notes

**For existing users:**
- File-based scenarios continue to work unchanged
- New `load(session: Session)` is optional - only override if using database

**For database users:**
- Install: `pip install or-scenario[database]` (once extras are configured)
- Import: `from or_scenario.orm import generate_dimension_table, generate_fact_table`
- Override: `def load(self, session: Session) -> None` in subclass
