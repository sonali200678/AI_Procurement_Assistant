from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Document
from backend.utils.report_pdf import generate_pdf_report
from backend.utils.report_docx import generate_docx_report
from backend.config import settings
import os

router = APIRouter(prefix="/api/download", tags=["Download"])

@router.get("/{document_id}/pdf")
async def download_pdf(document_id: int, db: Session = Depends(get_db)):
    """
    Generates and returns a downloadable PDF report of the document analysis.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    reports_dir = os.path.join(settings.UPLOAD_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    report_filename = f"report_{doc.id}.pdf"
    report_path = os.path.join(reports_dir, report_filename)
    
    try:
        generate_pdf_report(
            doc_name=doc.filename,
            summary=doc.summary,
            stats=doc.doc_metadata,
            charts=doc.charts or [],
            output_path=report_path
        )
        
        # Format a friendly filename
        basename = doc.filename.rsplit(".", 1)[0]
        download_name = f"Summarizerr_Report_{basename}.pdf"
        
        return FileResponse(
            path=report_path,
            filename=download_name,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@router.get("/{document_id}/docx")
async def download_docx(document_id: int, db: Session = Depends(get_db)):
    """
    Generates and returns a downloadable Word (DOCX) report of the document analysis.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    reports_dir = os.path.join(settings.UPLOAD_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    report_filename = f"report_{doc.id}.docx"
    report_path = os.path.join(reports_dir, report_filename)
    
    try:
        generate_docx_report(
            doc_name=doc.filename,
            summary=doc.summary,
            stats=doc.doc_metadata,
            charts=doc.charts or [],
            output_path=report_path
        )
        
        basename = doc.filename.rsplit(".", 1)[0]
        download_name = f"Summarizerr_Report_{basename}.docx"
        
        return FileResponse(
            path=report_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Word report: {str(e)}")
