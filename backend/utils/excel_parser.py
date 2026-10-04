import pandas as pd
import os

def parse_file(file_path: str) -> dict:
    """
    Parses an Excel file (.xlsx or .xls) using pandas, compiles text/statistics
    for each sheet, and returns a detailed text representation and structured metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")

    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        
        lines = [
            f"Tabular Dataset: Excel Workbook",
            f"Total Sheets: {len(sheet_names)}",
            f"Sheets: {', '.join(sheet_names)}",
            "---------------------------------------"
        ]
        
        sheets_metadata = {}
        
        # Parse each sheet (limit to first 3 sheets to prevent excessive context size)
        for idx, sheet_name in enumerate(sheet_names[:3]):
            df = xl.parse(sheet_name)
            rows, cols = df.shape
            
            col_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
            missing_values = {str(col): int(val) for col, val in df.isnull().sum().items()}
            
            lines.append(f"\nSheet '{sheet_name}' ({rows} rows x {cols} columns):")
            lines.append(f"Columns and Data Types: {col_types}")
            lines.append(f"Missing Values Count: {missing_values}")
            
            # Statistics
            desc = df.describe()
            if not desc.empty:
                lines.append("Descriptive Statistics:")
                lines.append(desc.to_string())
            
            lines.append("Sample Data (First 15 rows):")
            lines.append(df.head(15).to_csv(index=False))
            lines.append("---------------------------------------")
            
            # Store metadata for this sheet
            sheets_metadata[sheet_name] = {
                "row_count": rows,
                "column_count": cols,
                "columns": list(df.columns),
                "column_types": col_types,
                "missing_values": missing_values,
                "numeric_columns": list(df.select_dtypes(include=['number']).columns)
            }
            
        full_text = "\n".join(lines)
        
        metadata = {
            "sheets": sheet_names,
            "sheets_details": sheets_metadata,
            "sheet_count": len(sheet_names)
        }
        
        return {
            "text": full_text,
            "metadata": metadata
        }
        
    except Exception as e:
        raise ValueError(f"Failed to parse Excel file: {str(e)}")
