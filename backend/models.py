import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    file_type = Column(String)  # pdf, docx, csv, xlsx, json, xml
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    summary = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=True)  # Store word count, columns, missing values etc.
    charts = Column(JSON, nullable=True)  # List of chart filenames or details

    # Relationship to ChatMessages
    messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    role = Column(String)  # "user" or "model"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship back to Document
    document = relationship("Document", back_populates="messages")