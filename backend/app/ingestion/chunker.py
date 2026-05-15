from typing import List, Dict, Any, Tuple
from app.core.config import settings


class TextChunker:
    """
    Configurable chunker with overlap and metadata preservation.
    """
    def __init__(
        self,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        return self._recursive_split(text, separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        final_chunks: List[str] = []
        separator = separators[-1]
        for s in separators:
            if s == "":
                separator = ""
                break
            if s in text:
                separator = s
                break

        splits = text.split(separator) if separator else list(text)

        current_chunk: List[str] = []
        current_len = 0

        for piece in splits:
            piece_len = len(piece) + (len(separator) if separator else 0)
            if current_len + piece_len > self.chunk_size:
                if current_chunk:
                    chunk_str = separator.join(current_chunk).strip()
                    if chunk_str:
                        final_chunks.append(chunk_str)
                    
                    overlap_pieces = []
                    overlap_len = 0
                    for p in reversed(current_chunk):
                        if overlap_len + len(p) <= self.chunk_overlap:
                            overlap_pieces.insert(0, p)
                            overlap_len += len(p)
                        else:
                            break
                    current_chunk = overlap_pieces
                    current_len = overlap_len

                if piece_len > self.chunk_size:
                    idx = separators.index(separator) if separator in separators else -1
                    if idx < len(separators) - 1:
                        sub_chunks = self._recursive_split(piece, separators[idx + 1:])
                        final_chunks.extend(sub_chunks)
                        continue

            current_chunk.append(piece)
            current_len += piece_len

        if current_chunk:
            chunk_str = separator.join(current_chunk).strip()
            if chunk_str:
                final_chunks.append(chunk_str)

        return final_chunks

    def chunk_extracted_sections(
        self,
        extracted_sections: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        chunks_with_meta: List[Tuple[str, Dict[str, Any]]] = []

        for section_text, meta in extracted_sections:
            if meta.get("source_type") == "csv":
                chunks_with_meta.append((section_text, meta))
            else:
                sub_chunks = self.split_text(section_text)
                for chunk in sub_chunks:
                    chunks_with_meta.append((chunk, meta.copy()))

        return chunks_with_meta
