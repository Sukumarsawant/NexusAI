import pytest
from app.agents.state import NexusAgentState
from app.agents.workflow import (
    route_after_query_understanding,
    route_after_retrieval,
    route_after_verification,
    nexus_workflow,
)


def test_routing_conversational_bypasses_retrieval():
    state: NexusAgentState = {
        "needs_retrieval": False,
        "query": "Hello! How can you help me?",
    }
    destination = route_after_query_understanding(state)
    assert destination == "response"


def test_routing_factual_routes_to_retrieval():
    state: NexusAgentState = {
        "needs_retrieval": True,
        "query": "What is the Q3 ARR revenue in the financial report?",
    }
    destination = route_after_query_understanding(state)
    assert destination == "retrieval"


def test_routing_insufficient_context_retries():
    state: NexusAgentState = {
        "context_sufficient": False,
        "retrieval_cycle": 1,
    }
    destination = route_after_retrieval(state)
    assert destination == "retrieval"


def test_routing_sufficient_context_advances_to_reasoning():
    state: NexusAgentState = {
        "context_sufficient": True,
        "retrieval_cycle": 1,
    }
    destination = route_after_retrieval(state)
    assert destination == "reasoning"


def test_routing_failed_verification_loops_back():
    state: NexusAgentState = {
        "verification_passed": False,
        "retry_count": 0,
    }
    destination = route_after_verification(state)
    assert destination == "retrieval"


def test_routing_retry_limit_exceeded_exits_to_response():
    state: NexusAgentState = {
        "verification_passed": False,
        "retry_count": 5,  # Exceeds max retries
    }
    destination = route_after_verification(state)
    assert destination == "response"
