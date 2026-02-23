"""
Google Gemini Provider — via the google-generativeai SDK.

Requires: pip install google-generativeai
"""

from __future__ import annotations

import logging
from typing import Any

from .base import AIProvider, ChatResponse, EmbeddingResponse

logger = logging.getLogger('nova.intelligence.ai_providers.gemini')


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._genai = None
        self._model = None

    def _get_genai(self):
        """Lazy-import and configure the google.generativeai SDK."""
        if self._genai is None:
            try:
                import google.generativeai as genai
            except ImportError:
                raise ImportError(
                    'google-generativeai is required for Gemini. '
                    'Install it: pip install google-generativeai'
                )
            genai.configure(api_key=self.api_key)
            self._genai = genai
        return self._genai

    def _get_model(self):
        if self._model is None:
            genai = self._get_genai()
            model_name = self.model_name or 'gemini-pro'
            generation_config = {}
            if 'temperature' in self.extra_config:
                generation_config['temperature'] = self.extra_config['temperature']
            if 'max_output_tokens' in self.extra_config:
                generation_config['max_output_tokens'] = self.extra_config['max_output_tokens']

            self._model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config or None,
            )
        return self._model

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> tuple[bool, str]:
        try:
            genai = self._get_genai()
            models = list(genai.list_models())
            model_names = [m.name for m in models]

            target = self.model_name or 'gemini-pro'
            found = any(target in name for name in model_names)
            if not found:
                return (
                    False,
                    f'Model "{target}" not found in available Gemini models. '
                    f'Check your API key and model name.',
                )
            return True, f'Gemini API accessible. {len(models)} model(s) available.'
        except ImportError as e:
            return False, str(e)
        except Exception as e:
            return False, f'Gemini health check failed: {e}'

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str = '',
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        try:
            model = self._get_model()

            full_prompt = prompt
            if system_prompt:
                full_prompt = f'{system_prompt}\n\n{prompt}'

            generation_config = {}
            if temperature is not None:
                generation_config['temperature'] = temperature
            if max_tokens is not None:
                generation_config['max_output_tokens'] = max_tokens

            response = model.generate_content(
                full_prompt,
                generation_config=generation_config or None,
            )

            text = ''
            if response.parts:
                text = response.text
            elif response.prompt_feedback:
                text = f'[Blocked: {response.prompt_feedback}]'

            usage = {}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                }

            return ChatResponse(
                text=text,
                model=self.model_name or 'gemini-pro',
                usage=usage,
                finish_reason=getattr(response.candidates[0], 'finish_reason', '') if response.candidates else '',
                raw={},
            )
        except Exception as e:
            logger.error('Gemini generate error: %s', e)
            raise RuntimeError(f'Gemini generation failed: {e}') from e

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(self, texts: list[str]) -> EmbeddingResponse:
        try:
            genai = self._get_genai()
            embed_model = self.extra_config.get('embedding_model', 'models/embedding-001')

            result = genai.embed_content(
                model=embed_model,
                content=texts,
                task_type='retrieval_document',
            )

            embeddings = result['embedding']
            # If single text, wrap in list
            if texts and isinstance(embeddings[0], float):
                embeddings = [embeddings]

            dimension = len(embeddings[0]) if embeddings else 0

            return EmbeddingResponse(
                embeddings=embeddings,
                model=embed_model,
                dimension=dimension,
            )
        except ImportError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            logger.error('Gemini embed error: %s', e)
            raise RuntimeError(f'Gemini embedding failed: {e}') from e

    @property
    def provider_name(self) -> str:
        return 'Google Gemini'
