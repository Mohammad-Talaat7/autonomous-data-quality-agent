# ADQA Data Ingress with PyAirByte

ADQA uses the [PyAirByte](https://github.com/airbytehq/pyairbyte) library as an optional method for data ingestion, which supports 600+ connectors for both remote and local databases.

## Integration Overview

ADQA integrates PyAirByte through its `DataSource` abstraction, allowing you to use any Airbyte connector as a source for your data quality analysis.

### Prerequisites

To use Airbyte connectors, ensure you have the `airbyte` extra installed:

```bash
pip install "adqa[airbyte]"
```

## Using `DataSource.airbyte`

The recommended way to use Airbyte with ADQA is through the `DataSource` factory.

### Example: Using the Faker Source

```python
from adqa import ADQA, DataSource

# 1. Define the Airbyte source
source = DataSource.airbyte(
    source_name="source-faker",
    config={"count": 500},
    stream="users"
)

# 2. Initialize and run ADQA
agent = ADQA(data_source=source)
result = agent.analyze()

print(result.summary())
```

## Direct Access to PyAirByte

If you need lower-level access to PyAirByte functionality, you can import it directly (if installed). ADQA uses it internally in `adqa.data_ingress.readers.airbyte`.

```python
import airbyte as ab

# List available connectors
connectors = ab.get_available_connectors()
print(connectors)
```

## Local Data Support

For local data, PyAirByte supports local files (CSV/JSON/Parquet via `source-file`) and local databases (e.g., SQLite, PostgreSQL on localhost) directly.

## Advanced Examples

### Reading from a Remote HTTPS URL

```python
from adqa import DataSource

source = DataSource.airbyte(
    source_name="source-file",
    config={
        "dataset_name": "epidemiology",
        "provider": {
            "storage": "HTTPS",
            "user_agent": False
        },
        "url": "https://storage.googleapis.com/covid19-open-data/v2/latest/epidemiology.csv",
        "format": "csv"
    },
    stream="epidemiology"
)
```

## Why use Airbyte with ADQA?

1. **Broad Connectivity**: Access 300+ SaaS platforms and databases.
2. **Standardization**: Airbyte handles the complexity of API pagination, rate limiting, and schema discovery.
3. **Seamless Integration**: Once configured as a `DataSource`, the data flows through ADQA's profiling and detection engines like any other local file.
