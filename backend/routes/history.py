from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Document, ChatMessage
from backend.config import settings
import os

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """
    Lists all processed documents in reverse chronological order.
    """
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "uploaded_at": doc.uploaded_at
        }
        for doc in docs
    ]

@router.get("/{document_id}")
async def get_document_details(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieves complete details (summary, metadata, charts) of a document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "uploaded_at": doc.uploaded_at,
        "summary": doc.summary,
        "doc_metadata": doc.doc_metadata,
        "charts": doc.charts
    }

@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Deletes the document from SQLite, deletes its raw file on disk, 
    and removes any charts generated for it.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete file from disk
    if doc.filepath and os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception as e:
            print(f"Error removing raw file {doc.filepath}: {str(e)}")
            
    # Delete charts from disk
    if doc.charts:
        charts_dir = os.path.join(settings.UPLOAD_DIR, "charts")
        for chart_file in doc.charts:
            chart_path = os.path.join(charts_dir, chart_file)
            if os.path.exists(chart_path):
                try:
                    os.remove(chart_path)
                except Exception as e:
                    print(f"Error removing chart {chart_path}: {str(e)}")
                    
    # Delete from DB (cascading will delete ChatMessages)
    db.delete(doc)
    db.commit()
    
    return {"detail": "Document and associated files deleted successfully"}
