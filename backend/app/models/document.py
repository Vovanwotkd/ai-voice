"""
Document model for RAG knowledge base
"""

from sqlalchemy import Column, String, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(BaseModel):
    """
    Model for storing uploaded documents for RAG knowledge base.
    Documents are split into chunks and indexed in ChromaDB.
    """

    __tablename__ = "documents"

    name = Column(
        String(255),
        nullable=False,
        comment="Document filename"
    )

    file_path = Column(
        String(500),
        nullable=False,
        unique=True,
        comment="Path to the uploaded file"
    )

    doc_type = Column(
        SQLEnum(DocumentType),
        nullable=False,
        comment="Document type (pdf, docx, txt, md)"
    )

    status = Column(
        SQLEnum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
        comment="Processing status"
    )

    file_size = Column(
        Integer,
        nullable=True,
        comment="File size in bytes"
    )

    chunks_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of chunks created from this document"
    )

    meta_data = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional metadata (author, keywords, etc.)"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )

    # Relationship
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(name='{self.name}', type={self.doc_type}, status={self.status})>"
