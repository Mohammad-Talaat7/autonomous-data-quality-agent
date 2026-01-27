# ADQA Data Ingress with PyAirByte

ADQA uses the PyAirByte library for data ingestion, which supports 600+ connectors for both remote and local databases. PyAirByte alone is sufficient for most data ingestion needs without requiring additional libraries.

You can explore available PyAirByte connectors by visiting [AirByte Connectors](https://airbyte.com/connectors) or by running the following code:

```python
from adqa.data_ingress.airbyte import ab

connectors = ab.get_available_connectors()
print(connectors)
```

## Local Data Support

For local data, PyAirByte supports local files (CSV/JSON/Parquet via source-file) and local databases (e.g., SQLite, PostgreSQL on localhost) directly—no extra libraries required for ingestion.

## Usage Examples

Below are several examples demonstrating how to use PyAirByte for different data ingestion scenarios:

### Example 1: Using Faker Source for Test Data

```python
from adqa.data_ingress.airbyte import ab
import pandas as pd

# Create a source using the faker connector to generate test data
# Available streams: {'users', 'purchases', 'products'}
source = ab.get_source(
    "source-faker",
    config={"count": 500},  # Generate 500 records
    install_if_missing=True,
)

# Validate the connection and select all available data streams
source.check()               # Validates the connection
source.select_all_streams()  # Selects all available data streams
result = source.read()      # Reads the data

# List available streams
print("Available streams:", list(result.streams.keys()))

# Convert the result to a dataframe and display the first few rows
df = result["users"].to_pandas()
print(df.head())
```

### Example 2: Reading CSV Data from HTTPS URL

```python
from adqa.data_ingress.airbyte import ab
import pandas as pd

# Create a source to read CSV data from a remote HTTPS URL
source = ab.get_source(
    "source-file",
    config={
        "dataset_name": "epidemiology",  # Name for the dataset
        "provider": {
            "storage": "HTTPS",          # Data is stored on HTTPS
            "user_agent": False          # Disable user agent
        },
        "url": "https://storage.googleapis.com/covid19-open-data/v2/latest/epidemiology.csv",
        "format": "csv"                 # File format is CSV
    },
    install_if_missing=True,
)

# Validate connection, select streams, and read data
source.check()
source.select_all_streams()
result = source.read()

# Convert the result to a dataframe and display the first few rows
df = result['epidemiology'].to_pandas()  # Use the same name as dataset_name
print(df.head())
```

### Example 3: Reading Local CSV File

```python
from adqa.data_ingress.airbyte import ab
import pandas as pd

# Create a source to read CSV data from a local file
source = ab.get_source(
    "source-file",
    config={
        "dataset_name": "local",        # Name for the dataset
        "provider": {
            "storage": "local",          # Data is stored locally
            "user_agent": False          # Disable user agent
        },
        "url": "path/to/your/local/file.csv",
        "format": "csv"                 # File format is CSV
    },
    install_if_missing=True,
)

# Validate connection, select streams, and read data
source.check()
source.select_all_streams()
result = source.read()

# Convert the result to a dataframe and display the first few rows
df = result['local'].to_pandas()  # Use the same name as dataset_name
print(df.head())
```