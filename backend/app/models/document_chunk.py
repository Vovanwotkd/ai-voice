"""
DocumentChunk model for RAG text chunks with embeddings
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DocumentChunk(BaseModel):
    """
    Model for storing text chunks from documents.
    Each chunk is indexed in ChromaDB with its vector embedding.
    """

    __tablename__ = "document_chunks"

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent document"
    )

    chunk_index = Column(
        Integer,
        nullable=False,
        comment="Order of this chunk in the document (0-based)"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Text content of this chunk"
    )

    chromadb_id = Column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="ID in ChromaDB for this chunk"
    )

    token_count = Column(
        Integer,
        nullable=True,
        comment="Number of tokens in this chunk"
    )

    meta_data = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional metadata (page number, section, etc.)"
    )

    # Relationship
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk(doc_id={self.document_id}, index={self.chunk_index})>"
