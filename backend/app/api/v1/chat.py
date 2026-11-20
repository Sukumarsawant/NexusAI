import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, ConversationResponse, MessageResponse
from app.agents.workflow import nexus_workflow
from app.observability.tracer import ObservabilityService
from app.services.cost_calculator import calculate_cost

router = APIRouter(tags=["Chat & Multi-Agent Orchestration"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # 1. Manage Conversation
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()

    if not conv:
        conv = Conversation(
            id=req.conversation_id or str(uuid.uuid4()),
            user_id=current_user.id,
            title=req.query[:45] + ("..." if len(req.query) > 45 else ""),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Record User Message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.query,
    )
    db.add(user_msg)
    db.commit()

    # 2. Invoke Multi-Agent LangGraph Workflow
    initial_state = {
        "query": req.query,
        "user_id": current_user.id,
        "conversation_id": conv.id,
        "request_id": request_id,
        "top_k": req.top_k or 5,
        "filter_filenames": req.filter_filenames,
        "agent_traces": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }

    thread_config = {"configurable": {"thread_id": conv.id}}
    state_result = nexus_workflow.invoke(initial_state, config=thread_config)

    total_duration_ms = round((time.time() - start_time) * 1000, 2)
    final_answer = state_result.get("final_answer", "")
    citations = state_result.get("citations", [])
    retrieved_chunks = state_result.get("retrieved_chunks", [])
    traces = state_result.get("agent_traces", [])
    total_in = state_result.get("total_input_tokens", 0)
    total_out = state_result.get("total_output_tokens", 0)
    total_tokens = total_in + total_out
    cost_usd = calculate_cost(total_in, total_out)

    # 3. Record Assistant Message in DB
    asst_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=final_answer,
        citations=citations,
        retrieved_context=retrieved_chunks,
        agent_trace_summary={"traces": traces, "duration_ms": total_duration_ms},
    )
    db.add(asst_msg)
    db.commit()
    db.refresh(asst_msg)

    # 4. Observability & Metrics Logging
    ObservabilityService.record_request_metric(
        db=db,
        request_id=request_id,
        endpoint="/api/chat",
        total_duration_ms=total_duration_ms,
        input_tokens=total_in,
        output_tokens=total_out,
        status_code=200,
        conversation_id=conv.id,
        user_id=current_user.id,
    )

    ObservabilityService.record_agent_traces(
        db=db,
        request_id=request_id,
        conversation_id=conv.id,
        traces=traces,
        user_id=current_user.id,
    )

    return ChatResponse(
        conversation_id=conv.id,
        message_id=asst_msg.id,
        query=req.query,
        answer=final_answer,
        citations=citations,
        retrieved_contexts=retrieved_chunks,
        agent_traces=traces,
        total_tokens=total_tokens,
        estimated_cost_usd=cost_usd,
        total_duration_ms=total_duration_ms,
        is_grounded=state_result.get("is_grounded", True),
        confidence=state_result.get("confidence", "high"),
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully", "id": conversation_id}
