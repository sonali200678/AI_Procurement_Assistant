import pandas as pd
import os
import xml.etree.ElementTree as ET

def parse_file(file_path: str) -> dict:
    """
    Parses an XML file. If it fits a tabular database structure, uses pandas to
    extract schema and describe it. Otherwise, crawls the XML element tree and
    outputs a clean indented textual outline of elements, attributes, and text nodes.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")

    try:
        is_tabular = False
        df = None
        
        # Try parsing as a tabular dataframe first
        try:
            df = pd.read_xml(file_path)
            if df is not None and not df.empty and len(df.columns) > 1:
                is_tabular = True
        except:
            pass

        if is_tabular and df is not None:
            rows, cols = df.shape
            col_names = list(df.columns)
            col_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
            missing_values = {str(col): int(val) for col, val in df.isnull().sum().items()}

            lines = [
                "XML Data: Detected Tabular Row/Record Structure",
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
                "format": "xml_tabular",
                "row_count": rows,
                "column_count": cols,
                "columns": col_names,
                "column_types": col_types,
                "missing_values": missing_values,
                "numeric_columns": list(df.select_dtypes(include=['number']).columns)
            }
        else:
            # Fall back to XML outline parsing
            tree = ET.parse(file_path)
            root = tree.getroot()

            outline_lines = []
            
            # Recurse node to build structural outline
            def recurse_node(node, depth=0):
                if depth > 100:
                    return
                
                indent = "  " * depth
                node_text = (node.text or "").strip()
                attrs = f" {dict(node.attrib)}" if node.attrib else ""
                
                if node_text:
                    if len(node_text) > 150:
                        node_text = node_text[:147] + "..."
                    outline_lines.append(f"{indent}<{node.tag}{attrs}>{node_text}</{node.tag}>")
                else:
                    outline_lines.append(f"{indent}<{node.tag}{attrs}>")
                    for child in node:
                        recurse_node(child, depth + 1)
                    outline_lines.append(f"{indent}</{node.tag}>")

            recurse_node(root)
            xml_outline = "\n".join(outline_lines)
            
            # Prevent excessive context size
            truncated = False
            if len(xml_outline) > 50000:
                xml_outline = xml_outline[:50000] + "\n... [TRUNCATED due to size] ..."
                truncated = True

            lines = [
                f"XML Data: Hierarchical Markup Document",
                f"Root Element Tag: {root.tag}",
                "\nXML Structural Outline:"
            ]
            if truncated:
                lines.append("[Note: XML content was long and has been truncated]")
            lines.append(xml_outline)

            metadata = {
                "format": "xml_nested",
                "root_tag": root.tag,
                "word_count": len(xml_outline.split()),
                "character_count": len(xml_outline)
            }

        return {
            "text": "\n".join(lines),
            "metadata": metadata
        }

    except Exception as e:
        raise ValueError(f"Failed to parse XML file: {str(e)}")