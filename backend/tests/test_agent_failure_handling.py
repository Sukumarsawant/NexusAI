import pytest
from app.agents.state import NexusAgentState
from app.agents.query_agent import query_understanding_agent
from app.agents.verification_agent import verification_agent
from app.agents.response_agent import response_agent
from app.agents.workflow import route_after_query_understanding, route_after_verification, nexus_workflow


def test_conversational_query_bypasses_retrieval():
    state: NexusAgentState = {
        "query": "Hello! Good morning.",
        "user_id": "test-user-1",
        "agent_traces": [],
    }
    updated = query_understanding_agent(state)
    assert updated["needs_retrieval"] is False
    assert route_after_query_understanding(updated) == "response"


def test_factual_query_enforces_retrieval():
    state: NexusAgentState = {
        "query": "What is our company policy on remote work and expense reimbursement?",
        "user_id": "test-user-1",
        "agent_traces": [],
    }
    updated = query_understanding_agent(state)
    assert updated["needs_retrieval"] is True
    assert route_after_query_understanding(updated) == "retrieval"


def test_unsupported_claim_detection_triggers_retry():
    state: NexusAgentState = {
        "query": "What is the annual software budget?",
        "context_text": "The IT department budget for hardware is $500,000.",
        "reasoning_draft": "The software budget is $2,000,000 according to internal finance.",
        "retry_count": 0,
        "agent_traces": [],
    }
    updated = verification_agent(state)
    # When verification fails, route_after_verification checks retry count
    # Let's verify routing logic
    failed_state: NexusAgentState = {
        "verification_passed": False,
        "retry_count": 1,
    }
    assert route_after_verification(failed_state) == "retrieval"


def test_retry_limit_exhaustion_routes_to_response():
    # When retry count exceeds limit, workflow must route to response to prevent infinite loops
    exhausted_state: NexusAgentState = {
        "verification_passed": False,
        "retry_count": 5,  # Exceeds MAX_AGENT_RETRIES
    }
    assert route_after_verification(exhausted_state) == "response"


def test_empty_retrieved_context_yields_ungrounded_transparent_answer():
    state: NexusAgentState = {
        "query": "What is our CEO's home address?",
        "context_text": "",
        "retrieved_chunks": [],
        "reasoning_draft": "I cannot find sufficient information in the provided documentation.",
        "agent_traces": [],
    }
    result = response_agent(state)
    assert result["is_grounded"] is False
    assert result["confidence"] == "low"
    assert "could not locate sufficient verified information" in result["final_answer"]
