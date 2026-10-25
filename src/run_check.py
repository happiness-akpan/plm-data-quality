"""Run one SQL check file with DuckDB and print what it found."""
import sys
import duckdb

sql_file = sys.argv[1]
with open(sql_file) as f:
    query = f.read()

result = duckdb.sql(query).df()
print(f"{sql_file}: {len(result)} rows found")
print(result.head(10).to_string(index=False))