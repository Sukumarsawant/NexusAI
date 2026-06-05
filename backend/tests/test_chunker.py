import pytest
from app.ingestion.chunker import TextChunker


def test_chunker_basic_splitting():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = (
        "This is paragraph one of an enterprise compliance document. "
        "It contains crucial security and retention instructions.\n\n"
        "This is paragraph two outlining role-based access control and tenant isolation."
    )
    chunks = chunker.split_text(text)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 120  # Allows minor padding for word bounds


def test_chunker_preserves_metadata():
    chunker = TextChunker(chunk_size=80, chunk_overlap=15)
    sections = [
        ("Section A content about encryption standards in transit and at rest.", {"page_number": 1}),
        ("Section B content regarding authentication protocols including OAuth2 and JWT.", {"page_number": 2}),
    ]
    chunks_with_meta = chunker.chunk_extracted_sections(sections)
    assert len(chunks_with_meta) >= 2
    assert chunks_with_meta[0][1]["page_number"] == 1
    assert chunks_with_meta[-1][1]["page_number"] == 2


def test_chunker_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, chunk_overlap=120)
