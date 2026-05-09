import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name = Column(String(255), nullable=False)
    model_name = Column(String(100), nullable=False)
    dataset_size = Column(Integer, default=0, nullable=False)
    mean_faithfulness = Column(Float, nullable=True)
    mean_answer_relevancy = Column(Float, nullable=True)
    mean_context_precision = Column(Float, nullable=True)
    mean_context_recall = Column(Float, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    ground_truth = Column(Text, nullable=True)
    generated_answer = Column(Text, nullable=False)
    retrieved_contexts = Column(JSON, default=list, nullable=False)
    faithfulness = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)
    context_precision = Column(Float, nullable=True)
    context_recall = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("EvaluationRun", back_populates="results")
