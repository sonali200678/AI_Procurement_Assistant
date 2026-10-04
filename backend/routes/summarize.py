from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Document
from backend.utils import gemini_helper
from backend.routes.upload import PARSERS
import os

router = APIRouter(prefix="/api/summarize", tags=["Summarize"])

@router.post("/{document_id}/regenerate")
async def regenerate_summary(
    document_id: int,
    x_groq_api_key: str = Header(None, alias="X-Groq-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Regenerates the AI summary for a document that has already been uploaded.
    Useful if the original summary failed due to missing API keys or network errors.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not os.path.exists(doc.filepath):
        raise HTTPException(
            status_code=410, 
            detail="Original document file has been deleted or moved from server disk"
        )
        
    try:
        # Reparse document text from path
        parser_func = PARSERS.get(doc.file_type)
        if not parser_func:
            raise HTTPException(status_code=400, detail="Unsupported parser type")
            
        parsed_data = parser_func(doc.filepath)
        extracted_text = parsed_data.get("text", "")
        
        summary_error = None
        try:
            new_summary = gemini_helper.generate_summary(
                text=extracted_text,
                file_type=doc.file_type,
                groq_api_key=x_groq_api_key
            )
        except Exception as e:
            summary_error = str(e)
            new_summary = gemini_helper.generate_local_summary(
                text=extracted_text,
                file_type=doc.file_type
            )
        
        doc.summary = new_summary
        db.commit()
        db.refresh(doc)
        
        return {
            "id": doc.id,
            "filename": doc.filename,
            "summary": doc.summary,
            "summary_error": summary_error
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate summary: {str(e)}")
