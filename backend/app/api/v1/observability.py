from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.observability import MetricOverview, AgentPerformance, TraceItem, MetricsResponse
from app.observability.metrics import MetricsAggregator

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/overview", response_model=MetricOverview)
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = MetricsAggregator.get_overview(db=db, user_id=current_user.id)
    return MetricOverview(**data)


@router.get("/agents", response_model=List[AgentPerformance])
def get_agent_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = MetricsAggregator.get_agent_performance(db=db)
    return [AgentPerformance(**item) for item in data]


@router.get("/traces", response_model=List[TraceItem])
def get_traces(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    traces = MetricsAggregator.get_recent_traces(db=db, limit=limit)
    return [TraceItem.model_validate(t) for t in traces]


@router.get("/metrics", response_model=MetricsResponse)
def get_full_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    overview_data = MetricsAggregator.get_overview(db=db, user_id=current_user.id)
    agents_data = MetricsAggregator.get_agent_performance(db=db)
    traces = MetricsAggregator.get_recent_traces(db=db, limit=30)
    latency_trend = MetricsAggregator.get_latency_trend(db=db, limit=20)

    return MetricsResponse(
        overview=MetricOverview(**overview_data),
        agent_performance=[AgentPerformance(**item) for item in agents_data],
        recent_traces=[TraceItem.model_validate(t) for t in traces],
        latency_trend=latency_trend,
    )
