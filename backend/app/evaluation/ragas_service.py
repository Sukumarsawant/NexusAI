import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.evaluation")


class RagasEvaluator:
    """
    RAGAS Metric Evaluation Engine:
    Calculates:
    1. Faithfulness: Grounding score of answer against retrieved context (0.0 to 1.0)
    2. Answer Relevancy: Relevancy score of generated answer to question (0.0 to 1.0)
    3. Context Precision: Rank-weighted precision of relevant context chunks (0.0 to 1.0)
    4. Context Recall: Extent to which ground truth is represented in retrieved contexts (0.0 to 1.0)
    """

    @staticmethod
    def evaluate_faithfulness(answer: str, contexts: List[str]) -> float:
        """Measures claims in answer supported by contexts."""
        if not contexts or not answer.strip():
            return 0.0

        if gemini_service.is_configured():
            prompt = (
                f"Contexts:\n{' '.join(contexts)[:3000]}\n\n"
                f"Generated Answer:\n{answer}\n\n"
                "Evaluate the faithfulness of the answer to the provided contexts.\n"
                "Extract all factual claims from the answer, and determine how many are directly supported by the contexts.\n"
                "Respond in JSON format: {\"total_claims\": 4, \"supported_claims\": 4, \"score\": 1.0}"
            )
            try:
                resp, _, _ = gemini_service.generate_text(
                    prompt=prompt,
                    system_instruction="You are a strict RAG evaluation auditor measuring factual faithfulness.",
                    temperature=0.0,
                    json_output=True,
                )
                data = json.loads(resp)
                return max(0.0, min(1.0, float(data.get("score", 0.85))))
            except Exception as e:
                logger.warning(f"Faithfulness eval LLM fallback: {e}")

        # Deterministic token overlap heuristic fallback
        combined_context = " ".join(contexts).lower()
        answer_words = [w for w in answer.lower().split() if len(w) > 3]
        if not answer_words:
            return 1.0
        matches = sum(1 for w in answer_words if w in combined_context)
        return round(min(1.0, matches / len(answer_words)), 2)

    @staticmethod
    def evaluate_answer_relevancy(question: str, answer: str) -> float:
        """Measures how well the answer addresses the question."""
        if not answer.strip() or not question.strip():
            return 0.0

        if gemini_service.is_configured():
            prompt = (
                f"User Question: \"{question}\"\n\n"
                f"Generated Answer: \"{answer}\"\n\n"
                "Evaluate how relevant, complete, and directly responsive this answer is to the question on a scale of 0.0 to 1.0.\n"
                "Penalize redundancy, evasiveness, and off-topic information.\n"
                "Respond in JSON format: {\"relevancy_score\": 0.95, \"reasoning\": \"...\"}"
            )
            try:
                resp, _, _ = gemini_service.generate_text(
                    prompt=prompt,
                    system_instruction="You are an enterprise answer relevancy evaluator.",
                    temperature=0.0,
                    json_output=True,
                )
                data = json.loads(resp)
                return max(0.0, min(1.0, float(data.get("relevancy_score", 0.9))))
            except Exception as e:
                logger.warning(f"Relevancy eval LLM fallback: {e}")

        # Token overlap heuristic fallback
        q_words = set(w for w in question.lower().split() if len(w) > 3)
        ans_lower = answer.lower()
        if not q_words:
            return 1.0
        hits = sum(1 for w in q_words if w in ans_lower)
        return round(min(1.0, hits / len(q_words)), 2)

    @staticmethod
    def evaluate_context_precision(question: str, contexts: List[str], ground_truth: Optional[str]) -> float:
        """Checks if the most relevant contexts appear at the top ranks."""
        if not contexts:
            return 0.0
        if not ground_truth:
            return 0.85

        gt_tokens = set(w for w in ground_truth.lower().split() if len(w) > 3)
        if not gt_tokens:
            return 1.0

        precisions = []
        hits = 0
        for i, ctx in enumerate(contexts, start=1):
            ctx_lower = ctx.lower()
            if any(t in ctx_lower for t in gt_tokens):
                hits += 1
                precisions.append(hits / i)

        if not precisions:
            return 0.0
        return round(sum(precisions) / len(contexts), 2)

    @staticmethod
    def evaluate_context_recall(ground_truth: str, contexts: List[str]) -> float:
        """Measures how much of the ground truth is captured in retrieved contexts."""
        if not contexts or not ground_truth:
            return 0.0

        combined = " ".join(contexts).lower()
        gt_tokens = [w for w in ground_truth.lower().split() if len(w) > 3]
        if not gt_tokens:
            return 1.0

        found = sum(1 for t in gt_tokens if t in combined)
        return round(min(1.0, found / len(gt_tokens)), 2)
