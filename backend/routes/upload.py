import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import get_db
from backend.models import Document
from backend.utils import (
    pdf_parser, docx_parser, csv_parser, excel_parser, json_parser, xml_parser,
    statistics, chart_generator, gemini_helper
)

router = APIRouter(prefix="/api/upload", tags=["Upload"])

PARSERS = {
    "pdf": pdf_parser.parse_file,
    "docx": docx_parser.parse_file,
    "csv": csv_parser.parse_file,
    "xlsx": excel_parser.parse_file,
    "xls": excel_parser.parse_file,
    "json": json_parser.parse_file,
    "xml": xml_parser.parse_file,
}

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    x_groq_api_key: str = Header(None, alias="X-Groq-API-Key"),
    db: Session = Depends(get_db)
):
    # Validate extension
    filename = file.filename
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in PARSERS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format '.{ext}'. Supported: PDF, DOCX, CSV, XLSX, XLS, JSON, XML"
        )
    
    # Save the file with a unique name to avoid naming collisions
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file to disk: {str(e)}")

    try:
        # Parse document content
        parser_func = PARSERS[ext]
        parsed_data = parser_func(file_path)
        
        extracted_text = parsed_data.get("text", "")
        extracted_metadata = parsed_data.get("metadata", {})
        
        # Calculate statistics
        doc_stats = statistics.calculate_statistics(parsed_data, ext)
        
        # Save placeholder document first in DB to get an ID for charts
        db_doc = Document(
            filename=filename,
            filepath=file_path,
            file_type=ext,
            doc_metadata=doc_stats,
            summary="Generating summary...",
            charts=[]
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        # Generate summary using Groq when a key is provided
        ai_summary = ""
        summary_error = None
        try:
            ai_summary = gemini_helper.generate_summary(
                text=extracted_text,
                file_type=ext,
                groq_api_key=x_groq_api_key
            )
        except Exception as e:
            summary_error = str(e)
            ai_summary = gemini_helper.generate_local_summary(extracted_text, ext)

        # Generate charts if it is a tabular file
        charts_list = []
        if doc_stats.get("is_tabular"):
            charts_list = chart_generator.generate_charts(file_path, db_doc.id, ext, extracted_metadata)

        # Update document in DB with final summary and charts
        db_doc.summary = ai_summary
        db_doc.charts = charts_list
        db.commit()
        db.refresh(db_doc)
        
        return {
            "id": db_doc.id,
            "filename": db_doc.filename,
            "file_type": db_doc.file_type,
            "uploaded_at": db_doc.uploaded_at,
            "summary": db_doc.summary,
            "doc_metadata": db_doc.doc_metadata,
            "charts": db_doc.charts,
            "summary_error": summary_error
        }
        
    except Exception as e:
        # Clean up file on disk if insertion/parsing failed completely
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
