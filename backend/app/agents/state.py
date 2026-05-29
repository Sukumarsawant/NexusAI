from typing import TypedDict, List, Dict, Any, Optional


class NexusAgentState(TypedDict, total=False):
    # User Request & Context
    query: str
    user_id: str
    conversation_id: str
    request_id: str
    top_k: int
    filter_filenames: Optional[List[str]]

    # A. Query Understanding Outputs
    intent: str
    question_type: str
    entities: List[str]
    needs_retrieval: bool
    rewritten_query: str

    # B. Retrieval Outputs
    retrieved_chunks: List[Dict[str, Any]]
    context_text: str
    context_sufficient: bool
    retrieval_cycle: int

    # C. Reasoning Outputs
    reasoning_draft: str
    identified_contradictions: List[str]

    # D. Verification Outputs
    verification_passed: bool
    unsupported_claims: List[str]
    verification_feedback: str

    # E. Response Outputs
    final_answer: str
    citations: List[Dict[str, Any]]
    confidence: str
    is_grounded: bool

    # Observability & Loop Safeguards
    retry_count: int
    loop_count: int
    agent_traces: List[Dict[str, Any]]
    total_input_tokens: int
    total_output_tokens: int
    error: Optional[str]
