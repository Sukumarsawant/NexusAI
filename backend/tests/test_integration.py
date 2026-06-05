import os
import pytest
from app.services.gemini_client import gemini_service
from app.core.config import settings


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="Integration test requires live GEMINI_API_KEY environment variable"
)
def test_live_gemini_integration():
    """
    Optional live integration test with real Google Gemini API credentials.
    Runs only when GEMINI_API_KEY is explicitly supplied in the environment.
    """
    text, in_tok, out_tok = gemini_service.generate_text(
        prompt="Reply with the exact word 'PONG'.",
        model=settings.GEMINI_MODEL,
        temperature=0.0
    )
    assert "PONG" in text
    assert in_tok > 0
    assert out_tok > 0

    embeddings = gemini_service.generate_embeddings(["NexusAI enterprise test text."])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == settings.EMBEDDING_DIMENSION
