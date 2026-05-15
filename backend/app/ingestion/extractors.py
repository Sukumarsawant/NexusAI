import csv
import io
import os
from typing import List, Tuple, Dict, Any
from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extracts text page-by-page from a PDF file.
    Returns list of (text_content, metadata).
    """
    results = []
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)

    for page_idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        clean_text = page_text.strip()
        if clean_text:
            results.append((
                clean_text,
                {
                    "page_number": page_idx + 1,
                    "total_pages": total_pages,
                    "source_type": "pdf"
                }
            ))
    return results


def extract_text_from_txt(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extracts plain text with basic encoding detection.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()
    
    if not content:
        return []
    
    return [(content, {"source_type": "txt", "char_length": len(content)})]


def extract_text_from_markdown(file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extracts markdown text, identifying sections by header (#, ##, ###).
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    sections = []
    current_header = "Introduction"
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                text_block = "".join(current_lines).strip()
                if text_block:
                    sections.append((
                        text_block,
                        {"header": current_header, "source_type": "markdown"}
                    ))
                current_lines = []
            current_header = stripped.lstrip("#").strip()
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines:
        text_block = "".join(current_lines).strip()
        if text_block:
            sections.append((
                text_block,
                {"header": current_header, "source_type": "markdown"}
            ))

    return sections if sections else [("".join(lines).strip(), {"source_type": "markdown"})]


def extract_text_from_csv(file_path: str, rows_per_chunk: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extracts CSV tabular data, preserving column headers and row context.
    Does not treat the entire file as an ordinary paragraph.
    Groups rows into structured chunks with schema descriptions.
    """
    results = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.reader(f, delimiter=delimiter)
        try:
            headers = next(reader)
        except StopIteration:
            return []

        headers = [h.strip() for h in headers if h.strip()]
        header_str = ", ".join(headers)

        current_rows = []
        for row_idx, row in enumerate(reader, start=1):
            if not any(cell.strip() for cell in row):
                continue

            row_items = []
            for col_idx, cell in enumerate(row):
                header_name = headers[col_idx] if col_idx < len(headers) else f"Column_{col_idx+1}"
                row_items.append(f"{header_name}: {cell.strip()}")

            row_text = f"Row {row_idx}: (" + "; ".join(row_items) + ")"
            current_rows.append((row_idx, row_text))

            if len(current_rows) >= rows_per_chunk:
                chunk_text = (
                    f"Dataset Schema: [{header_str}]\n"
                    f"Rows {current_rows[0][0]} to {current_rows[-1][0]}:\n"
                    + "\n".join(r[1] for r in current_rows)
                )
                results.append((
                    chunk_text,
                    {
                        "source_type": "csv",
                        "headers": headers,
                        "row_start": current_rows[0][0],
                        "row_end": current_rows[-1][0]
                    }
                ))
                current_rows = []

        if current_rows:
            chunk_text = (
                f"Dataset Schema: [{header_str}]\n"
                f"Rows {current_rows[0][0]} to {current_rows[-1][0]}:\n"
                + "\n".join(r[1] for r in current_rows)
            )
            results.append((
                chunk_text,
                {
                    "source_type": "csv",
                    "headers": headers,
                    "row_start": current_rows[0][0],
                    "row_end": current_rows[-1][0]
                }
            ))

    return results


def extract_document_content(file_path: str, file_type: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Dispatcher for document extraction based on file extension / type.
    """
    ft = file_type.lower().replace(".", "")
    if ft == "pdf":
        return extract_text_from_pdf(file_path)
    elif ft in ("txt", "text"):
        return extract_text_from_txt(file_path)
    elif ft in ("md", "markdown"):
        return extract_text_from_markdown(file_path)
    elif ft == "csv":
        return extract_text_from_csv(file_path)
    else:
        return extract_text_from_txt(file_path)
