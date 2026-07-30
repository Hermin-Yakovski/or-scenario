# dump() Usage Examples

## Overview

The `dump()` method persists optimization results from `Register[Parameter]` to database solution (sol) tables.

## Basic Usage

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from or_scenario import Scenario
from or_scenario.orm import generate_dimension_table, generate_sol_table
from or_register import Dimension, Parameter

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
    scenario.dump(session, {SalesVolume}, (Product, Region), (1, 2))
```

## Dumping Multiple Parameters

```python
# Dump multiple results at once
scenario.dump(session, {SalesVolume, SalesRevenue, Margin}, (Product, Region), (1, 2))
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
