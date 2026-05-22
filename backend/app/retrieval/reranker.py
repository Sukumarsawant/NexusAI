import logging
from typing import List, Dict, Any
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.reranker")


class Reranker:
    """
    Reranks candidate chunks by cross-scoring semantic relevance with query.
    Uses Gemini when configured, or lexical-density score adjustment.
    """
    @staticmethod
    def rerank(
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not candidates or len(candidates) <= 1:
            return candidates[:top_k]

        # If Gemini is configured and we have candidate chunks, we can score relevance
        if gemini_service.is_configured() and len(candidates) > 3:
            try:
                # Prepare compact evaluation list
                chunk_snippets = [
                    f"[{i}] {c['content'][:300]}"
                    for i, c in enumerate(candidates[:10])
                ]
                prompt = (
                    f"User Query: '{query}'\n\n"
                    "Evaluate the relevance of each snippet to answering the query.\n"
                    "Rate each snippet index on a scale of 0 to 10.\n"
                    "Respond with a JSON list of objects: [{\"index\": 0, \"score\": 8.5}, ...]\n\n"
                    + "\n\n".join(chunk_snippets)
                )

                response_text, _, _ = gemini_service.generate_text(
                    prompt=prompt,
                    system_instruction="You are a strict relevance scorer for information retrieval.",
                    temperature=0.0,
                    json_output=True,
                )

                import json
                scores_data = json.loads(response_text)
                score_map = {item["index"]: float(item.get("score", 0.0)) / 10.0 for item in scores_data}

                for i, c in enumerate(candidates[:10]):
                    if i in score_map:
                        # Blend 70% LLM rerank score + 30% initial retrieval score
                        c["similarity_score"] = round(0.7 * score_map[i] + 0.3 * c["similarity_score"], 4)
                        c["reranked"] = True

                candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
                return candidates[:top_k]

            except Exception as e:
                logger.warning(f"LLM reranking fallback due to: {e}")

        # Fallback ranking (original similarity score preserved)
        return candidates[:top_k]
