import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.observability import RequestMetric, AgentTrace
from app.services.cost_calculator import calculate_cost

logger = logging.getLogger("nexusai.observability.tracer")

# Try to initialize OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    otel_tracer = trace.get_tracer("nexusai.orchestrator")
except Exception:
    otel_tracer = None


class ObservabilityService:
    @staticmethod
    def record_request_metric(
        db: Session,
        request_id: str,
        endpoint: str,
        total_duration_ms: float,
        input_tokens: int,
        output_tokens: int,
        status_code: int = 200,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> RequestMetric:
        """
        Record complete end-to-end request metrics in database.
        """
        total_tokens = input_tokens + output_tokens
        cost = calculate_cost(input_tokens=input_tokens, output_tokens=output_tokens)

        metric = RequestMetric(
            request_id=request_id,
            conversation_id=conversation_id,
            user_id=user_id,
            endpoint=endpoint,
            total_duration_ms=total_duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            status_code=status_code,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric

    @staticmethod
    def record_agent_traces(
        db: Session,
        request_id: str,
        conversation_id: Optional[str],
        traces: List[Dict[str, Any]],
        model_name: Optional[str] = "gemini-2.5-flash",
    ) -> None:
        """
        Persist structured traces for each multi-agent node execution.
        """
        for t in traces:
            trace_obj = AgentTrace(
                request_id=request_id,
                conversation_id=conversation_id,
                agent_name=t.get("agent_name", "Unknown Agent"),
                execution_order=t.get("execution_order", 1),
                duration_ms=t.get("duration_ms", 0.0),
                input_tokens=t.get("input_tokens", 0),
                output_tokens=t.get("output_tokens", 0),
                model_name=model_name,
                status=t.get("status", "success"),
                inputs_summary={"summary": t.get("summary")},
                outputs_summary={"status": t.get("status")},
                error_message=t.get("error"),
            )
            db.add(trace_obj)
        db.commit()
