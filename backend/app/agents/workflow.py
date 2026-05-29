import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.agents.state import NexusAgentState
from app.agents.query_agent import query_understanding_agent
from app.agents.retrieval_agent import retrieval_agent
from app.agents.reasoning_agent import reasoning_agent
from app.agents.verification_agent import verification_agent
from app.agents.response_agent import response_agent

logger = logging.getLogger("nexusai.workflow")


def route_after_query_understanding(state: NexusAgentState) -> Literal["retrieval", "response"]:
    """If user asks something purely conversational or greetings, skip retrieval."""
    if not state.get("needs_retrieval", True):
        return "response"
    return "retrieval"


def route_after_retrieval(state: NexusAgentState) -> Literal["retrieval", "reasoning"]:
    """If context is insufficient and retries remain, attempt another retrieval."""
    cycle = state.get("retrieval_cycle", 1)
    sufficient = state.get("context_sufficient", True)
    
    if not sufficient and cycle < settings.MAX_AGENT_RETRIES:
        logger.info(f"Retrieval insufficient. Triggering retry cycle {cycle + 1}")
        return "retrieval"
    return "reasoning"


def route_after_verification(state: NexusAgentState) -> Literal["retrieval", "response"]:
    """If verification fails and retries remain, loop back for evidence refinement."""
    passed = state.get("verification_passed", True)
    retry_count = state.get("retry_count", 0)

    if not passed and retry_count <= settings.MAX_AGENT_RETRIES:
        logger.info(f"Verification failed. Looping back with retry count: {retry_count}")
        return "retrieval"
    return "response"


def build_nexus_graph():
    """
    Constructs the compiled LangGraph workflow with loop protection and conditional routing.
    """
    builder = StateGraph(NexusAgentState)

    # 1. Register agent nodes
    builder.add_node("query_understanding", query_understanding_agent)
    builder.add_node("retrieval", retrieval_agent)
    builder.add_node("reasoning", reasoning_agent)
    builder.add_node("verification", verification_agent)
    builder.add_node("response", response_agent)

    # 2. Add edges and conditional branches
    builder.add_edge(START, "query_understanding")

    builder.add_conditional_edges(
        "query_understanding",
        route_after_query_understanding,
        {
            "retrieval": "retrieval",
            "response": "response",
        }
    )

    builder.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {
            "retrieval": "retrieval",
            "reasoning": "reasoning",
        }
    )

    builder.add_edge("reasoning", "verification")

    builder.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "retrieval": "retrieval",
            "response": "response",
        }
    )

    builder.add_edge("response", END)

    # In-memory checkpointer for state isolation across turns
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph


# Singleton graph instance
nexus_workflow = build_nexus_graph()
