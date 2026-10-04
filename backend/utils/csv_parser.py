import pandas as pd
import os

def parse_file(file_path: str) -> dict:
    """
    Parses a CSV file using pandas and returns a text representation of the data
    (metadata, statistics, sample rows) along with structured metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")

    try:
        # Load CSV using pandas
        df = pd.read_csv(file_path)
        
        rows, cols = df.shape
        col_names = list(df.columns)
        
        # Convert pandas types and missing values counts to python native formats
        col_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        missing_values = {str(col): int(val) for col, val in df.isnull().sum().items()}
        
        # Build a textual representation of the dataset for LLM consumption
        lines = [
            f"Tabular Dataset: CSV File",
            f"Dimensions: {rows} rows x {cols} columns",
            f"Columns and Data Types: {col_types}",
            f"Missing Values Count: {missing_values}",
            "\nDescriptive Statistics for Numeric Columns:"
        ]
        
        # Append df.describe() if there are numeric columns
        numeric_desc = df.describe()
        if not numeric_desc.empty:
            lines.append(numeric_desc.to_string())
        else:
            lines.append("No numeric columns found to generate descriptive statistics.")
            
        lines.append("\nSample Data (First 20 rows):")
        # Use to_csv instead of to_markdown to avoid requiring 'tabulate' library
        lines.append(df.head(20).to_csv(index=False))
        
        full_text = "\n".join(lines)
        
        metadata = {
            "row_count": rows,
            "column_count": cols,
            "columns": col_names,
            "column_types": col_types,
            "missing_values": missing_values,
            "numeric_columns": list(df.select_dtypes(include=['number']).columns)
        }
        
        return {
            "text": full_text,
            "metadata": metadata
        }
        
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")