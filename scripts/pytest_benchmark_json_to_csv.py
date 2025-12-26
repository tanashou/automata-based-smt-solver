import pandas as pd
import json
import sys
from pathlib import Path

# Check arguments
if len(sys.argv) < 2:
    print("Usage: python pytest_benchmark_json_to_csv.py <json input path>")
    sys.exit(1)

# Get input path from arguments and convert to Path object
input_path = Path(sys.argv[1])

# Create output path by changing the input path extension to .csv
# Example: benchmark_result/data.json -> benchmark_result/data.csv
output_path = input_path.with_suffix(".csv")

# Load JSON file
try:
    with open(input_path, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Error: File not found: {input_path}")
    sys.exit(1)

# Convert data to flat table
if "benchmarks" not in data:
    print("Error: 'benchmarks' key not found in JSON")
    sys.exit(1)

df = pd.json_normalize(data["benchmarks"])

# Rename 'param' to 'filename'
df.rename(columns={"param": "filename"}, inplace=True)

# List of columns to drop
columns_to_drop = {
    "group",
    "name",
    "fullname",
    "params.benchmark_file",
    "options.disable_gc",
    "options.timer",
    "options.warmup",
}

# Drop columns only if they exist
df.drop(columns=[c for c in columns_to_drop if c in df.columns], inplace=True)

# Reorder columns (filename first)
cols = df.columns.tolist()
if "filename" in cols:
    cols.insert(0, cols.pop(cols.index("filename")))
    df = df[cols]

# Clean column names (remove extra_info. and stats. prefixes)
new_columns = []
for c in df.columns:
    # Keep filename as is, remove prefixes from others
    if c == "filename":
        new_columns.append(c)
    else:
        name = c.replace("extra_info.", "").replace("stats.", "")
        new_columns.append(name)

df.columns = new_columns

# Output CSV
df.to_csv(output_path, index=False)
print(f"Completed: {output_path}")
