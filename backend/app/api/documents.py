"""
Documents API endpoints for RAG knowledge base management
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db
from app.models import Document, DocumentStatus
from app.services.document_processor import document_processor
from app.services.rag_service import rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload and process a document

    Supported formats: PDF, DOCX, TXT, MD
    """
    try:
        # Read file content
        content = await file.read()

        # Save file and create DB record
        document = await document_processor.save_uploaded_file(
            file_content=content,
            filename=file.filename,
            db=db
        )

        # Process document in background
        if background_tasks:
            background_tasks.add_task(
                process_document_task,
                document.id,
                db
            )
        else:
            # Process synchronously if no background tasks
            await process_document_task(document.id, db)

        return {
            "id": str(document.id),
            "name": document.name,
            "type": document.doc_type,
            "status": document.status,
            "message": "Document uploaded and processing started"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


async def process_document_task(document_id: str, db: Session):
    """Background task to process document"""
    from app.database import SessionLocal

    # Create new session for background task
    db = SessionLocal()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            logger.error(f"Document {document_id} not found")
            return

        # Process document (extract text, create chunks)
        await document_processor.process_document(document, db)

        # Get chunks
        chunks = document.chunks

        if chunks:
            # Index chunks in vector store
            await rag_service.index_document_chunks(chunks, db)

        logger.info(f"✅ Document {document.name} fully processed and indexed")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")

        # Update document status
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            db.commit()

    finally:
        db.close()


@router.get("/")
async def list_documents(db: Session = Depends(get_db)):
    """Get list of all documents"""
    documents = db.query(Document).order_by(Document.created_at.desc()).all()

    return {
        "documents": [
            {
                "id": str(doc.id),
                "name": doc.name,
                "type": doc.doc_type,
                "status": doc.status,
                "file_size": doc.file_size,
                "chunks_count": doc.chunks_count,
                "created_at": doc.created_at.isoformat(),
                "error_message": doc.error_message
            }
            for doc in documents
        ],
        "total": len(documents)
    }


@router.get("/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(document.id),
        "name": document.name,
        "type": document.doc_type,
        "status": document.status,
        "file_size": document.file_size,
        "chunks_count": document.chunks_count,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
        "meta_data": document.meta_data,
        "error_message": document.error_message
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its chunks"""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Delete from vector store
        await rag_service.delete_document_from_index(str(document.id))

        # Delete file
        import os
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        # Delete from database (chunks will be cascade deleted)
        db.delete(document)
        db.commit()

        logger.info(f"Deleted document {document.name}")

        return {"message": "Document deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/{document_id}/reindex")
async def reindex_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Reindex a document"""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    await rag_service.delete_document_from_index(str(document.id))

    # Delete existing chunks
    for chunk in document.chunks:
        db.delete(chunk)

    document.chunks_count = 0
    document.status = DocumentStatus.PENDING
    db.commit()

    # Reprocess
    background_tasks.add_task(process_document_task, document.id, db)

    return {"message": "Document reindexing started"}


@router.get("/stats/collection")
async def get_collection_stats():
    """Get vector store collection statistics"""
    from app.services.vector_store_service import vector_store_service

    stats = await vector_store_service.get_collection_stats()

    return stats
