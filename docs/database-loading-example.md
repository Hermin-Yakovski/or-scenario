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
        facts = (
            session.execute(
                select(FactSales).where(FactSales.snapshot_id == self._request.request_id)
            )
            .scalars()
            .all()
        )

        # Map to Register
        for fact in facts:
            self.set(
                SalesVolume, (Product, Region), (fact.product_id, fact.region_id), fact.quantity
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
    def load(self, session: Session = None) -> None:
        # Load reference data from files
        self._load_reference_data(handler, path)

        # Load transactional data from database
        self._load_facts(session)
```
