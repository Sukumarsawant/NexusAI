from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CitationItem(BaseModel):
    source_id: str
    filename: str
    chunk_index: int
    page_or_row: Optional[str] = None
    snippet: str
    relevance_score: float


class AgentTraceItem(BaseModel):
    agent_name: str
    execution_order: int
    duration_ms: float
    input_tokens: int
    output_tokens: int
    status: str
    summary: Optional[str] = None


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str
    top_k: Optional[int] = 5
    stream: Optional[bool] = False
    filter_filenames: Optional[List[str]] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    query: str
    answer: str
    citations: List[CitationItem]
    retrieved_contexts: List[Dict[str, Any]]
    agent_traces: List[AgentTraceItem]
    total_tokens: int
    estimated_cost_usd: float
    total_duration_ms: float
    is_grounded: bool
    confidence: str  # high, medium, low


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]
    agent_trace_summary: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None
    model_config = ConfigDict(from_attributes=True)
