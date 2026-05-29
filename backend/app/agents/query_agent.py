import time
import json
import logging
from typing import Dict, Any
from app.agents.state import NexusAgentState
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.agents.query")


def query_understanding_agent(state: NexusAgentState) -> Dict[str, Any]:
    """
    Query Understanding Agent:
    - Classifies intent and question type
    - Extracts named entities
    - Determines whether knowledge retrieval is required
    - Rewrites query into an optimized search representation
    """
    start_time = time.time()
    query = state.get("query", "")
    traces = list(state.get("agent_traces", []))
    total_in = state.get("total_input_tokens", 0)
    total_out = state.get("total_output_tokens", 0)

    # Defaults
    intent = "factual_inquiry"
    question_type = "analytical"
    entities = []
    needs_retrieval = True
    rewritten = query
    input_tokens = 0
    output_tokens = 0

    if gemini_service.is_configured():
        prompt = (
            f"Analyze this enterprise user query:\n\"{query}\"\n\n"
            "Respond in JSON format with these exact fields:\n"
            "{\n"
            "  \"intent\": \"factual_inquiry | comparison | summarization | general_conversation\",\n"
            "  \"question_type\": \"factoid | complex_reasoning | exploratory | conversational\",\n"
            "  \"entities\": [\"extracted\", \"key\", \"entities\"],\n"
            "  \"needs_retrieval\": true or false,\n"
            "  \"rewritten_query\": \"expanded, keyword-rich query optimized for search\"\n"
            "}"
        )
        try:
            resp_text, in_tok, out_tok = gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are an expert Query Analysis & Retrieval Router for enterprise search systems.",
                temperature=0.0,
                json_output=True,
            )
            input_tokens = in_tok
            output_tokens = out_tok
            data = json.loads(resp_text)
            intent = data.get("intent", intent)
            question_type = data.get("question_type", question_type)
            entities = data.get("entities", entities)
            needs_retrieval = data.get("needs_retrieval", True)
            rewritten = data.get("rewritten_query", query)
        except Exception as e:
            logger.warning(f"Query Understanding Agent LLM fallback: {e}")
            # Heuristic fallback
            lowered = query.lower()
            if any(greeting in lowered for greeting in ["hello", "hi", "hey", "who are you"]):
                needs_retrieval = False
                intent = "general_conversation"

    duration_ms = round((time.time() - start_time) * 1000, 2)
    traces.append({
        "agent_name": "Query Understanding Agent",
        "execution_order": len(traces) + 1,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": "success",
        "summary": f"Intent: {intent}, Needs Retrieval: {needs_retrieval}",
    })

    return {
        "intent": intent,
        "question_type": question_type,
        "entities": entities,
        "needs_retrieval": needs_retrieval,
        "rewritten_query": rewritten,
        "agent_traces": traces,
        "total_input_tokens": total_in + input_tokens,
        "total_output_tokens": total_out + output_tokens,
    }
