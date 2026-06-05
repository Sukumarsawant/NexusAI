import pytest
from app.agents.verification_agent import verification_agent
from app.agents.response_agent import response_agent


def test_verification_agent_passes_when_insufficient_info_noted():
    state = {
        "reasoning_draft": "I cannot find sufficient information in the provided knowledge base to answer this question accurately.",
        "context_text": "",
        "query": "What is the secret formula?",
        "retry_count": 0,
        "agent_traces": [],
    }
    result = verification_agent(state)
    assert result["verification_passed"] is True


def test_response_agent_builds_citations_and_structure():
    state = {
        "query": "What is the audit interval?",
        "reasoning_draft": "Audits are conducted annually per SOC2 guidelines.",
        "context_text": "SOC2 Compliance requires annual audits.",
        "retrieved_chunks": [
            {
                "content": "SOC2 Compliance requires annual audits.",
                "filename": "SOC2_Report.pdf",
                "chunk_index": 0,
                "similarity_score": 0.94,
                "page_or_row": "Page 4",
            }
        ],
        "unsupported_claims": [],
        "identified_contradictions": [],
        "agent_traces": [],
    }
    result = response_agent(state)
    assert len(result["citations"]) == 1
    assert result["citations"][0]["filename"] == "SOC2_Report.pdf"
    assert result["citations"][0]["page_or_row"] == "Page 4"
    assert result["is_grounded"] is True
