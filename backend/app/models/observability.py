import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from app.core.database import Base


class RequestMetric(Base):
    __tablename__ = "request_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(64), index=True, nullable=False)
    conversation_id = Column(String(36), index=True, nullable=True)
    user_id = Column(String(36), index=True, nullable=True)
    endpoint = Column(String(128), nullable=False)
    total_duration_ms = Column(Float, nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    status_code = Column(Integer, default=200, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(64), index=True, nullable=False)
    conversation_id = Column(String(36), index=True, nullable=True)
    agent_name = Column(String(100), nullable=False)
    execution_order = Column(Integer, default=1, nullable=False)
    duration_ms = Column(Float, nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    model_name = Column(String(100), nullable=True)
    status = Column(String(50), default="success", nullable=False)  # success, error, retry
    inputs_summary = Column(JSON, default=dict, nullable=True)
    outputs_summary = Column(JSON, default=dict, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
