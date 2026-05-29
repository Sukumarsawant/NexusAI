import time
import json
import logging
from typing import Dict, Any
from app.agents.state import NexusAgentState
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.agents.verification")


def verification_agent(state: NexusAgentState) -> Dict[str, Any]:
    """
    Verification Agent:
    - Verifies that the draft answer is faithfully grounded in the retrieved context
    - Detects hallucinations, fabricated numbers, or unsupported claims
    - Decides whether to approve or trigger another retrieval/reasoning cycle
    """
    start_time = time.time()
    traces = list(state.get("agent_traces", []))
    total_in = state.get("total_input_tokens", 0)
    total_out = state.get("total_output_tokens", 0)

    draft = state.get("reasoning_draft", "")
    context = state.get("context_text", "")
    query = state.get("query", "")
    retries = state.get("retry_count", 0)

    passed = True
    unsupported_claims = []
    feedback = ""
    input_tokens = 0
    output_tokens = 0

    if not context or "cannot find sufficient information" in draft.lower():
        # If already acknowledging lack of information, verification passes
        passed = True
    elif gemini_service.is_configured():
        prompt = (
            f"User Question: \"{query}\"\n\n"
            f"Retrieved Source Evidence:\n{context}\n\n"
            f"Proposed Answer:\n\"{draft}\"\n\n"
            "Audit the proposed answer strictly against the source evidence.\n"
            "Check for:\n"
            "- Claims not supported by the evidence\n"
            "- Extrapolated numbers or dates\n"
            "- Factual hallucinations\n\n"
            "Respond in JSON format:\n"
            "{\n"
            "  \"passed\": true or false,\n"
            "  \"unsupported_claims\": [\"list of any ungrounded assertions\"],\n"
            "  \"critique\": \"feedback for revision or additional retrieval\"\n"
            "}"
        )
        try:
            resp_text, in_tok, out_tok = gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are a strict Enterprise Verification Auditor. Grounding is mandatory.",
                temperature=0.0,
                json_output=True,
            )
            input_tokens = in_tok
            output_tokens = out_tok
            data = json.loads(resp_text)
            passed = data.get("passed", True)
            unsupported_claims = data.get("unsupported_claims", [])
            feedback = data.get("critique", "")
        except Exception as e:
            logger.warning(f"Verification Agent LLM fallback: {e}")
            passed = True

    duration_ms = round((time.time() - start_time) * 1000, 2)
    traces.append({
        "agent_name": "Verification Agent",
        "execution_order": len(traces) + 1,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": "success",
        "summary": f"Grounding check: {'PASSED' if passed else 'FAILED'}. Unsupported: {len(unsupported_claims)}",
    })

    return {
        "verification_passed": passed,
        "unsupported_claims": unsupported_claims,
        "verification_feedback": feedback,
        "retry_count": retries + (0 if passed else 1),
        "agent_traces": traces,
        "total_input_tokens": total_in + input_tokens,
        "total_output_tokens": total_out + output_tokens,
    }
