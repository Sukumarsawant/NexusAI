import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentChunkResponse, ReindexResponse
from app.ingestion.pipeline import IngestionPipeline, compute_file_hash

router = APIRouter(prefix="/documents", tags=["Documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(settings.DEFAULT_CHUNK_SIZE),
    chunk_overlap: Optional[int] = Form(settings.DEFAULT_CHUNK_OVERLAP),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Validate file extension
    filename = file.filename or "unknown"
    _, ext = os.path.splitext(filename.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: PDF, TXT, MD, CSV.",
        )

    # 2. Read bytes & check size limit
    content_bytes = await file.read()
    file_size = len(content_bytes)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # 3. Duplicate detection via SHA-256 content hash per user
    content_hash = compute_file_hash(content_bytes)
    existing = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.content_hash == content_hash,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document detected: '{filename}' has already been uploaded.",
        )

    # 4. Save file to disk
    doc_id = str(uuid.uuid4())
    save_filename = f"{doc_id}_{filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)
    with open(save_path, "wb") as f:
        f.write(content_bytes)

    # 5. Create Document record
    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=filename,
        file_type=ext.lstrip("."),
        file_size=file_size,
        content_hash=content_hash,
        storage_path=save_path,
        status="pending",
        doc_metadata={"original_filename": filename, "uploaded_by": current_user.email},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Execute Ingestion synchronously so client receives processed status
    processed_doc = IngestionPipeline.process_document(
        db=db,
        document_id=doc.id,
        chunk_size=chunk_size or settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP,
    )
    return DocumentResponse.model_validate(processed_doc)


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    IngestionPipeline.delete_document(db=db, document_id=document_id)
    return {"message": "Document and associated chunks deleted successfully", "id": document_id}


@router.post("/{document_id}/reindex", response_model=ReindexResponse)
def reindex_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    updated = IngestionPipeline.reindex_document(db=db, document_id=document_id)
    return ReindexResponse(
        message="Re-indexing completed",
        document_id=updated.id,
        status=updated.status,
        chunk_count=updated.chunk_count,
    )
