from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.observability import RequestMetric, AgentTrace


class MetricsAggregator:
    @staticmethod
    def get_overview(db: Session, user_id: str) -> Dict[str, Any]:
        """
        Calculates live SaaS dashboard statistics from actual database records.
        """
        total_docs = db.query(Document).filter(Document.user_id == user_id).count()
        indexed_docs = db.query(Document).filter(
            Document.user_id == user_id,
            Document.status == "indexed"
        ).count()
        total_convs = db.query(Conversation).filter(Conversation.user_id == user_id).count()

        metrics_query = db.query(
            func.count(RequestMetric.id),
            func.avg(RequestMetric.total_duration_ms),
            func.sum(RequestMetric.total_tokens),
            func.sum(RequestMetric.estimated_cost_usd),
        ).filter(RequestMetric.user_id == user_id).first()

        total_requests = metrics_query[0] or 0
        avg_latency = round(float(metrics_query[1] or 0.0), 2)
        total_tokens = int(metrics_query[2] or 0)
        total_cost = round(float(metrics_query[3] or 0.0), 5)

        return {
            "total_documents": total_docs,
            "indexed_documents": indexed_docs,
            "total_conversations": total_convs,
            "total_requests": total_requests,
            "avg_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
        }

    @staticmethod
    def get_agent_performance(db: Session, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Aggregates performance by agent name: execution count, average latency, tokens, error rates.
        Filtered by tenant user_id when provided.
        """
        query = db.query(
            AgentTrace.agent_name,
            func.count(AgentTrace.id).label("call_count"),
            func.avg(AgentTrace.duration_ms).label("avg_duration"),
            func.avg(AgentTrace.input_tokens + AgentTrace.output_tokens).label("avg_tokens"),
            func.sum(case((AgentTrace.status == "error", 1), else_=0)).label("errors")
        )
        if user_id:
            query = query.filter(AgentTrace.user_id == user_id)
        results = query.group_by(AgentTrace.agent_name).all()

        perf = []
        for row in results:
            agent_name = row[0]
            call_count = row[1] or 0
            avg_duration = round(float(row[2] or 0.0), 2)
            avg_tokens = round(float(row[3] or 0.0), 1)
            errors = row[4] or 0
            err_rate = round((errors / call_count * 100.0) if call_count > 0 else 0.0, 1)

            perf.append({
                "agent_name": agent_name,
                "call_count": call_count,
                "avg_duration_ms": avg_duration,
                "avg_tokens": avg_tokens,
                "error_rate_percent": err_rate,
            })
        return perf

    @staticmethod
    def get_recent_traces(db: Session, user_id: Optional[str] = None, limit: int = 50) -> List[AgentTrace]:
        query = db.query(AgentTrace)
        if user_id:
            query = query.filter(AgentTrace.user_id == user_id)
        return query.order_by(AgentTrace.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_latency_trend(db: Session, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        query = db.query(RequestMetric)
        if user_id:
            query = query.filter(RequestMetric.user_id == user_id)
        metrics = query.order_by(RequestMetric.created_at.desc()).limit(limit).all()
        trend = []
        for m in reversed(metrics):
            trend.append({
                "timestamp": m.created_at.strftime("%H:%M:%S"),
                "latency_ms": round(m.total_duration_ms, 2),
                "token_count": m.total_tokens,
            })
        return trend

