# Data Ingress

ADQA supports a wide variety of data sources through its `data_ingress` module.

## Supported Formats

- **CSV**: Local or remote CSV files.
- **JSON**: Local or remote JSON files.
- **Parquet**: Local or remote Parquet files.
- **Excel**: Local Excel workbooks.
- **SQL**: Database connections (PostgreSQL, MySQL, SQLite, etc.) via SQLAlchemy.
- **PyAirByte**: Integration with Airbyte connectors for 300+ sources.

## Using `DataSource`

The easiest way to initialize ADQA is via the `DataSource` factory or the convenience method `ADQA.from_path()`.

### Example: CSV

```python
from adqa import DataSource
source = DataSource.csv(path="data.csv")
```

### Example: SQL

```python
source = DataSource.sql(
    uri="postgresql://user:pass@localhost/db",
    query="SELECT * FROM my_table"
)
```

## Internal Workflow

1. **Factory Identification**: ADQA identifies the reader based on the file extension or URI prefix.
2. **Reader Instantiation**: A specialized reader (e.g., `CSVReader`) is created.
3. **Lazy/Eager Loading**: Data is loaded into a pandas DataFrame for processing.
