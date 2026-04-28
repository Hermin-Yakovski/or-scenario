# or-scenario

Template framework for Operations Research scenarios.

## Overview

`or-scenario` provides a base class for orchestrating data, resources, and algorithms in OR workflows. It integrates:

- **register** - Multi-dimensional data storage
- **dal** - File-based data loading (JSON, CSV, pickle, XLSX)
- **or-algo** - Algorithm orchestration

## Installation

```bash
poetry add or-scenario
```

## Quick Start

```python
from pathlib import Path
from dal import JsonHandler
from register import Dimension, Parameter
from or_scenario import Scenario

Product = Dimension("Product", "产品", "PROD")
SalesVolume = Parameter(1, "sales_volume", "销量", float)

class MyScenario(Scenario):
    def __init__(self, version_id):
        super().__init__(version_id)

        def map_data(records):
            for r in records:
                self.set(SalesVolume, (Product,), (r["product_id"],), r["volume"])

        self._load_steps = [LoadStep(
            handler=JsonHandler(),
            mapping=map_data,
            path=Path("data") / str(version_id),
            table="sales.json"
        )]

scenario = MyScenario("run-001")
scenario.load()
scenario.validate()
```

## License

MIT
