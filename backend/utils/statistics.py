import re

def calculate_statistics(parsed_data: dict, file_type: str) -> dict:
    """
    Computes analytics and metadata stats for a parsed document.
    Handles text documents (PDF/DOCX) and tabular documents (CSV/Excel/JSON/XML).
    """
    text = parsed_data.get("text", "")
    parser_metadata = parsed_data.get("metadata", {})
    
    # Check if the parser detected tabular format
    is_tabular = file_type in ["csv", "xlsx", "xls"] or parser_metadata.get("format") in ["json_tabular", "xml_tabular"]
    
    stats = {
        "is_tabular": is_tabular,
        "file_type": file_type,
    }
    
    # Calculate text statistics (always useful as context)
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    char_count = len(text)
    
    # Sentences count
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    if sentence_count == 0:
        sentence_count = 1
        
    reading_time = max(1, round(word_count / 200)) # 200 WPM average
    
    # Calculate top keywords (excluding common english stopwords)
    stopwords = {
        'the', 'and', 'of', 'to', 'a', 'in', 'is', 'that', 'it', 'for', 'on', 'with', 'as', 'this', 
        'by', 'an', 'be', 'are', 'at', 'or', 'from', 'but', 'not', 'your', 'from', 'have', 'were', 
        'which', 'their', 'was', 'has', 'will', 'about', 'can', 'would', 'there', 'if', 'all', 'more',
        'who', 'what', 'some', 'than', 'into', 'our', 'them', 'out', 'up', 'so', 'been', 'its'
    }
    
    word_freq = {}
    for word in words:
        if len(word) > 3 and word not in stopwords:
            word_freq[word] = word_freq.get(word, 0) + 1
            
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [item[0] for item in sorted_keywords[:10]]
    
    stats["text_stats"] = {
        "word_count": word_count,
        "char_count": char_count,
        "sentence_count": sentence_count,
        "reading_time_minutes": reading_time,
        "top_keywords": top_keywords
    }
    
    # Include tabular statistics if relevant
    if is_tabular:
        stats["tabular_stats"] = {
            "row_count": parser_metadata.get("row_count", 0),
            "column_count": parser_metadata.get("column_count", 0),
            "columns": parser_metadata.get("columns", []),
            "column_types": parser_metadata.get("column_types", {}),
            "missing_values": parser_metadata.get("missing_values", {}),
            "numeric_columns": parser_metadata.get("numeric_columns", [])
        }
    
    return stats