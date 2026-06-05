from app.core.config import settings


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    embedding_tokens: int = 0,
    model: str = settings.GEMINI_MODEL
) -> float:
    """
    Calculate estimated API cost in USD based on provider reported token counts
    and configurable model pricing tiers.
    """
    input_cost = (input_tokens / 1_000_000.0) * settings.COST_PER_1M_INPUT_TOKENS
    output_cost = (output_tokens / 1_000_000.0) * settings.COST_PER_1M_OUTPUT_TOKENS
    embedding_cost = (embedding_tokens / 1_000_000.0) * settings.COST_PER_1M_EMBEDDING_TOKENS
    return round(input_cost + output_cost + embedding_cost, 6)
