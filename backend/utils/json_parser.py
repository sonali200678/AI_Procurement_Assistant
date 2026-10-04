import json
import pandas as pd
import os

def parse_file(file_path: str) -> dict:
    """
    Parses a JSON file. If it contains tabular data (a list of dictionaries),
    it uses pandas to extract structural details. Otherwise, it handles it as 
    a nested JSON document and outputs formatted keys and values.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Detect tabular format: a list of dictionaries
        is_tabular = False
        df = None
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            try:
                df = pd.DataFrame(data)
                is_tabular = True
            except:
                pass

        if is_tabular and df is not None:
            rows, cols = df.shape
            col_names = list(df.columns)
            col_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
            missing_values = {str(col): int(val) for col, val in df.isnull().sum().items()}

            lines = [
                "JSON Data: Detected Tabular Array of Records",
                f"Dimensions: {rows} rows x {cols} columns",
                f"Columns and Data Types: {col_types}",
                f"Missing Values: {missing_values}",
                "\nDescriptive Statistics for Numeric Columns:"
            ]

            desc = df.describe()
            if not desc.empty:
                lines.append(desc.to_string())
            else:
                lines.append("No numeric columns found to generate statistics.")

            lines.append("\nSample Records (First 20 items in CSV-like format):")
            lines.append(df.head(20).to_csv(index=False))

            metadata = {
                "format": "json_tabular",
                "row_count": rows,
                "column_count": cols,
                "columns": col_names,
                "column_types": col_types,
                "missing_values": missing_values,
                "numeric_columns": list(df.select_dtypes(include=['number']).columns)
            }
        else:
            # Standard hierarchical or nested JSON
            pretty_json = json.dumps(data, indent=2)
            # Prevent excessive context bloat if the JSON is huge
            truncated = False
            if len(pretty_json) > 50000:
                pretty_json = pretty_json[:50000] + "\n... [TRUNCATED due to size] ..."
                truncated = True

            top_keys = []
            if isinstance(data, dict):
                top_keys = list(data.keys())
            elif isinstance(data, list):
                top_keys = [f"Array (length: {len(data)})"]

            lines = [
                "JSON Data: Hierarchical / Nested Structure",
                f"Top Level Elements/Keys: {top_keys}",
                "\nJSON Document Content:"
            ]
            if truncated:
                lines.append("[Note: Document was long and has been truncated for context]")
            lines.append(pretty_json)

            metadata = {
                "format": "json_nested",
                "top_level_keys": top_keys,
                "word_count": len(pretty_json.split()),
                "character_count": len(pretty_json)
            }

        return {
            "text": "\n".join(lines),
            "metadata": metadata
        }

    except Exception as e:
        raise ValueError(f"Failed to parse JSON file: {str(e)}")