# Schema Refactor Design: Move Pydantic Models to schema.py

**Date:** 2026-05-14
**Status:** Approved
**Phase:** 1 of 2 (Database Integration)

## Overview

Refactor `or_scenario` to establish `schema.py` as the canonical location for Pydantic models. This establishes a convention for domain-specific scenario subclasses while preparing for Phase 2 database integration via `omni_orm`.

## Motivation

- Establish clear separation: schema.py (Pydantic models) vs scenario.py (orchestration logic)
- Provide convention for subclasses to follow when defining domain-specific models
- Prepare for Phase 2: database integration where schema models will mirror ORM models

## Scope

**In Scope:**
- Move `BaseRequest` and `BaseResponse` from `scenario.py` to `schema.py`
- Update imports in `scenario.py` and `__init__.py`
- Maintain 100% test coverage

**Out of Scope:**
- Database integration (Phase 2)
- ORM model definitions (Phase 2)
- New Pydantic models beyond existing BaseRequest/BaseResponse

## Design

### File Structure

```
or_scenario/
├── __init__.py       # Export from canonical sources
├── schema.py         # NEW - BaseRequest, BaseResponse
└── scenario.py       # Imports from schema.py
```

### schema.py (New File)

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
        description="identity of the data"
    )


class BaseResponse(BaseModel):
    """Base response with common fields."""
    request_id: int = Field(..., description="identity of the data")
    status: int = Field(..., description="status of the service")
    message: str = Field(default="Default message", description="message of the service")
    timestamp: datetime = Field(default_factory=datetime.now, description="timestamp of the data")
    response: Any = Field(default=None, description="response of the data")
```

### scenario.py Changes

**Remove:**
- `BaseRequest` class definition (lines 14-17)
- `BaseResponse` class definition (lines 20-26)
- Unused `BaseModel`, `Field` imports from pydantic

**Add:**
```python
from .schema import BaseRequest, BaseResponse
```

### __init__.py Changes

```python
"""or-scenario: Template framework for Operations Research workflows."""

from .schema import BaseRequest, BaseResponse  # Updated: export from canonical source
from .scenario import Scenario

__all__ = ["Scenario", "BaseRequest", "BaseResponse"]
__version__ = "0.1.0"
```

## Testing

### Verification Commands

```bash
pytest tests/ -v
pytest --cov=or_scenario tests/
```

### Test Criteria

- All existing tests pass without modification (they import from `or_scenario`)
- Coverage remains at 100%
- Imports resolve from both `or_scenario` and `or_scenario.schema`

## Convention for Subclasses

Domain-specific scenario subclasses should follow this pattern:

```
domain_scenario/
├── __init__.py
├── schema.py        # DomainRequest, DomainResponse, etc.
└── scenario.py      # DomainScenario imports from schema
```

## Implementation Notes

- No behavioral changes - purely mechanical relocation
- Backward compatible - existing imports from `or_scenario` continue to work
- Test files require no changes

## Next Phase

Phase 2 will add database integration:
- `load(session: Session = None)` for sync database loading
- `async def aload(session: AsyncSession)` for async database loading
- Manual ORM-to-Register mapping with helper functions
