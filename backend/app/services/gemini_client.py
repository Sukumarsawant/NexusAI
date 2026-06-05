import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger("nexusai.gemini")


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please set GEMINI_API_KEY in your environment or .env file."
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        json_output: bool = False,
    ) -> Tuple[str, int, int]:
        """
        Generate text using official google-genai SDK with automated model fallback.
        Returns: (response_text, input_tokens, output_tokens)
        """
        candidate_models = [model or settings.GEMINI_MODEL, "gemini-3.5-flash", "gemini-3.1-flash-lite"]
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction if system_instruction else None,
            response_mime_type="application/json" if json_output else "text/plain",
        )

        last_err = None
        for m in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config,
                )

                input_tokens = 0
                output_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

                return response.text or "", input_tokens, output_tokens

            except Exception as e:
                last_err = e
                logger.warning(f"Gemini API model {m} retry with fallback due to: {e}")
                continue

        logger.error(f"Gemini API error during generate_text across all candidate models: {last_err}")
        raise last_err

    def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        Generate vector embeddings for a batch of text chunks using Gemini.
        Returns list of 768-dimensional float vectors.
        """
        if not texts:
            return []

        model_name = model or settings.GEMINI_EMBEDDING_MODEL
        emb_config = types.EmbedContentConfig(output_dimensionality=settings.EMBEDDING_DIMENSION)

        try:
            response = self.client.models.embed_content(
                model=model_name,
                contents=texts,
                config=emb_config,
            )

            embeddings = []
            if hasattr(response, "embeddings") and response.embeddings:
                for item in response.embeddings:
                    embeddings.append(item.values)
            elif hasattr(response, "embedding") and response.embedding:
                embeddings.append(response.embedding.values)

            return embeddings

        except Exception as e:
            logger.error(f"Gemini API error during generate_embeddings: {e}")
            raise


# Singleton instance
gemini_service = GeminiService()
