from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    content_hash: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    doc_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    chunk_metadata: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReindexResponse(BaseModel):
    message: str
    document_id: str
    status: str
    chunk_count: int
