from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class MetricOverview(BaseModel):
    total_documents: int
    indexed_documents: int
    total_conversations: int
    total_requests: int
    avg_latency_ms: float
    total_tokens: int
    total_cost_usd: float


class AgentPerformance(BaseModel):
    agent_name: str
    call_count: int
    avg_duration_ms: float
    avg_tokens: float
    error_rate_percent: float


class TraceItem(BaseModel):
    id: str
    request_id: str
    conversation_id: Optional[str]
    agent_name: str
    execution_order: int
    duration_ms: float
    input_tokens: int
    output_tokens: int
    model_name: Optional[str]
    status: str
    inputs_summary: Optional[Dict[str, Any]]
    outputs_summary: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LatencyTrendPoint(BaseModel):
    timestamp: str
    latency_ms: float
    token_count: int


class MetricsResponse(BaseModel):
    overview: MetricOverview
    agent_performance: List[AgentPerformance]
    recent_traces: List[TraceItem]
    latency_trend: List[LatencyTrendPoint]
