import tempfile
import os
import pytest
from app.ingestion.extractors import (
    extract_text_from_txt,
    extract_text_from_markdown,
    extract_text_from_csv,
    extract_document_content,
)


def test_txt_extraction():
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Enterprise Data Policy 2026. Data retention is set to 7 years.")
        temp_path = f.name

    try:
        results = extract_text_from_txt(temp_path)
        assert len(results) == 1
        content, meta = results[0]
        assert "Enterprise Data Policy" in content
        assert meta["source_type"] == "txt"
    finally:
        os.remove(temp_path)


def test_markdown_extraction_preserves_headers():
    md_content = """# Overview
NexusAI is an enterprise platform.

## Architecture
Built with LangGraph and pgvector.
"""
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md_content)
        temp_path = f.name

    try:
        results = extract_text_from_markdown(temp_path)
        assert len(results) >= 2
        assert any(r[1].get("header") == "Overview" for r in results)
        assert any(r[1].get("header") == "Architecture" for r in results)
    finally:
        os.remove(temp_path)


def test_csv_extraction_preserves_structure():
    csv_content = """Department,Headcount,Budget_M
Engineering,140,24.5
Marketing,45,8.2
Operations,60,11.0
"""
    with tempfile.NamedTemporaryFile("w+", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        results = extract_text_from_csv(temp_path, rows_per_chunk=2)
        assert len(results) >= 1
        content, meta = results[0]
        assert "Dataset Schema:" in content
        assert "Department" in meta["headers"]
        assert "Row 1:" in content
        assert "Budget_M: 24.5" in content
    finally:
        os.remove(temp_path)
