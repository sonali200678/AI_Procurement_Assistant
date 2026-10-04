from fastapi import APIRouter, Header, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Document, ChatMessage
from backend.utils import gemini_helper
from backend.routes.upload import PARSERS
import os

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

@router.post("/{document_id}")
async def chat_with_doc(
    document_id: int,
    request: ChatRequest,
    x_groq_api_key: str = Header(None, alias="X-Groq-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Chats with the document. Retrieves history, feeds it to Groq along with
    the parsed text as context, saves the exchange, and returns the model response.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not os.path.exists(doc.filepath):
        raise HTTPException(
            status_code=410, 
            detail="Original document file has been deleted or moved from server disk"
        )
        
    # Get previous chat history for this document
    db_history = (
        db.query(ChatMessage)
        .filter(ChatMessage.document_id == document_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    
    chat_history = [{"role": msg.role, "content": msg.content} for msg in db_history]
    
    try:
        # Reparse document text from path
        parser_func = PARSERS.get(doc.file_type)
        if not parser_func:
            raise HTTPException(status_code=400, detail="Unsupported parser type")
            
        parsed_data = parser_func(doc.filepath)
        extracted_text = parsed_data.get("text", "")
        
        try:
            response_text = gemini_helper.chat_with_document(
                text=extracted_text,
                chat_history=chat_history,
                new_message=request.message,
                groq_api_key=x_groq_api_key
            )
        except Exception:
            response_text = gemini_helper.generate_local_chat_response(
                text=extracted_text,
                new_message=request.message
            )
        
        # Save messages to database
        user_msg = ChatMessage(document_id=document_id, role="user", content=request.message)
        model_msg = ChatMessage(document_id=document_id, role="model", content=response_text)
        
        db.add(user_msg)
        db.add(model_msg)
        db.commit()
        
        return {
            "response": response_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/history")
async def get_chat_history(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves the chat message history for a specific document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.document_id == document_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp
        }
        for msg in messages
    ]
