import os
import matplotlib
matplotlib.use('Agg')  # Set backend to Agg for non-interactive plotting
import matplotlib.pyplot as plt
import pandas as pd
from backend.config import settings

def generate_charts(file_path: str, doc_id: int, file_type: str, metadata: dict) -> list[str]:
    """
    Generates 1 or 2 visual analysis charts for tabular datasets.
    Saves the charts as PNG files in the uploads/charts directory.
    Returns a list of generated chart filenames.
    """
    is_tabular = file_type in ["csv", "xlsx", "xls"] or metadata.get("format") == "json_tabular" or metadata.get("format") == "xml_tabular"
    if not is_tabular:
        return []

    try:
        # Load the dataframe
        df = None
        if file_type == "csv":
            df = pd.read_csv(file_path)
        elif file_type in ["xlsx", "xls"]:
            xl = pd.ExcelFile(file_path)
            # Use first sheet
            df = xl.parse(xl.sheet_names[0])
        elif metadata.get("format") == "json_tabular":
            df = pd.read_json(file_path)
        elif metadata.get("format") == "xml_tabular":
            df = pd.read_xml(file_path)
        
        if df is None or df.empty:
            return []

        # Identify columns
        numeric_cols = list(df.select_dtypes(include=['number']).columns)
        categorical_cols = list(df.select_dtypes(exclude=['number']).columns)

        charts_generated = []
        charts_dir = os.path.join(settings.UPLOAD_DIR, "charts")
        os.makedirs(charts_dir, exist_ok=True)

        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')

        # Limit row count for drawing to avoid overcrowding
        plot_df = df.head(30)

        # Chart 1: Bar or Line plot of the first numeric column
        if numeric_cols:
            y_col = numeric_cols[0]
            # Try to find a good X column (categorical or index)
            x_col = categorical_cols[0] if categorical_cols else None
            
            plt.figure(figsize=(10, 5))
            if x_col and plot_df[x_col].nunique() <= 30:
                # Group by categorical column to plot nicely
                grouped = plot_df.groupby(x_col)[y_col].mean().reset_index()
                plt.bar(grouped[x_col].astype(str), grouped[y_col], color='#4f46e5')
                plt.xlabel(x_col)
                plt.xticks(rotation=45, ha='right')
            else:
                # Plot as line/trend chart
                plt.plot(plot_df.index, plot_df[y_col], color='#4f46e5', marker='o', linewidth=2)
                plt.xlabel("Index")
                
            plt.ylabel(y_col)
            plt.title(f"Average of {y_col}" if x_col and plot_df[x_col].nunique() <= 30 else f"Trend of {y_col} (Top 30 Rows)")
            plt.tight_layout()
            
            chart1_filename = f"chart_{doc_id}_1.png"
            chart1_path = os.path.join(charts_dir, chart1_filename)
            plt.savefig(chart1_path, dpi=150)
            plt.close()
            charts_generated.append(chart1_filename)

        # Chart 2: Correlation Matrix or distribution chart
        if len(numeric_cols) >= 2:
            plt.figure(figsize=(8, 6))
            # Calculate correlation matrix
            corr = df[numeric_cols].corr()
            cax = plt.matshow(corr, cmap='coolwarm', fignum=1)
            plt.colorbar(cax)
            
            # Set labels
            ticks = range(len(numeric_cols))
            plt.xticks(ticks, numeric_cols, rotation=90)
            plt.yticks(ticks, numeric_cols)
            plt.title("Correlation Matrix Heatmap", y=1.15)
            plt.tight_layout()
            
            chart2_filename = f"chart_{doc_id}_2.png"
            chart2_path = os.path.join(charts_dir, chart2_filename)
            plt.savefig(chart2_path, dpi=150)
            plt.close()
            charts_generated.append(chart2_filename)
            
        elif numeric_cols:
            # Distribution histogram of the first numeric column
            plt.figure(figsize=(8, 5))
            plt.hist(df[numeric_cols[0]].dropna(), bins=15, color='#3b82f6', edgecolor='black', alpha=0.7)
            plt.xlabel(numeric_cols[0])
            plt.ylabel("Frequency")
            plt.title(f"Distribution Histogram of {numeric_cols[0]}")
            plt.tight_layout()
            
            chart2_filename = f"chart_{doc_id}_2.png"
            chart2_path = os.path.join(charts_dir, chart2_filename)
            plt.savefig(chart2_path, dpi=150)
            plt.close()
            charts_generated.append(chart2_filename)

        return charts_generated

    except Exception as e:
        print(f"Error generating charts: {str(e)}")
        plt.close('all')
        return []
