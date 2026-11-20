import hashlib
import logging
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.ingestion.extractors import extract_document_content
from app.ingestion.chunker import TextChunker
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.ingestion")


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content for duplicate detection."""
    sha256 = hashlib.sha256()
    sha256.update(content)
    return sha256.hexdigest()


class IngestionPipeline:
    @staticmethod
    def process_document(
        db: Session,
        document_id: str,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP,
    ) -> Document:
        """
        Execute full document ingestion: extraction, chunking, embedding generation,
        and persistence.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        doc.status = "processing"
        doc.error_message = None
        db.commit()

        try:
            if not doc.storage_path or not os.path.exists(doc.storage_path):
                raise FileNotFoundError(f"Source file not found at {doc.storage_path}")

            # 1. Extract content and metadata
            extracted = extract_document_content(doc.storage_path, doc.file_type)
            if not extracted:
                raise ValueError("No extractable content found in document")

            # 2. Chunk text
            chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks_with_meta = chunker.chunk_extracted_sections(extracted)

            if not chunks_with_meta:
                raise ValueError("Document yielded 0 chunks after splitting")

            chunk_texts = [text for text, _ in chunks_with_meta]

            # 3. Generate embeddings using Gemini
            embeddings: List[List[float]] = []
            if gemini_service.is_configured():
                # Process in batches of 20
                batch_size = 20
                for i in range(0, len(chunk_texts), batch_size):
                    batch = chunk_texts[i:i + batch_size]
                    batch_embeddings = gemini_service.generate_embeddings(batch)
                    embeddings.extend(batch_embeddings)
            else:
                if settings.ENVIRONMENT == "production" and not os.environ.get("TESTING"):
                    raise RuntimeError(
                        "GEMINI_API_KEY is not configured in production environment. "
                        "Refusing to ingest document with silent zero embeddings."
                    )
                logger.warning("GEMINI_API_KEY is not configured; using fallback zero embeddings for local test/dev only.")
                embeddings = [[0.0] * settings.EMBEDDING_DIMENSION for _ in chunk_texts]

            # 4. Save chunks in database
            for idx, ((chunk_text, meta), embedding) in enumerate(zip(chunks_with_meta, embeddings)):
                meta["source_filename"] = doc.filename
                meta["file_type"] = doc.file_type
                meta["chunk_index"] = idx

                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    user_id=doc.user_id,
                    chunk_index=idx,
                    content=chunk_text,
                    embedding=embedding,
                    chunk_metadata=meta,
                )
                db.add(chunk_obj)

            # 5. Mark document as indexed
            doc.status = "indexed"
            doc.chunk_count = len(chunks_with_meta)
            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            logger.error(f"Ingestion failed for document {document_id}: {e}", exc_info=True)
            db.rollback()
            # Reload document and set status to failed
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                db.commit()
            raise

    @staticmethod
    def reindex_document(
        db: Session,
        document_id: str,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP,
    ) -> Document:
        """
        Delete all existing chunks for this document and re-execute ingestion.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Delete existing chunks
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.commit()

        # Re-run ingestion
        return IngestionPipeline.process_document(
            db=db,
            document_id=document_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    @staticmethod
    def delete_document(db: Session, document_id: str) -> bool:
        """
        Delete a document, all associated chunks (cascade), and the local storage file.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False

        if doc.storage_path and os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except OSError as e:
                logger.warning(f"Could not remove physical file {doc.storage_path}: {e}")

        db.delete(doc)
        db.commit()
        return True
