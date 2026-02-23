"""
OpenAI Provider — via the openai SDK.

Requires: pip install openai
"""

from __future__ import annotations

import logging
from typing import Any

from .base import AIProvider, ChatResponse, EmbeddingResponse

logger = logging.getLogger('nova.intelligence.ai_providers.openai')


class OpenAIProvider(AIProvider):
    """OpenAI API provider (GPT-4, GPT-3.5, text-embedding-ada-002, etc.)."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    'openai is required for the OpenAI provider. '
                    'Install it: pip install openai'
                )
            kwargs: dict[str, Any] = {'api_key': self.api_key}
            if self.api_base_url:
                kwargs['base_url'] = self.api_base_url
            self._client = OpenAI(**kwargs)
        return self._client

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> tuple[bool, str]:
        try:
            client = self._get_client()
            models = client.models.list()
            model_ids = [m.id for m in models.data[:50]]

            target = self.model_name or 'gpt-4o-mini'
            found = any(target in mid for mid in model_ids)
            if not found:
                return (
                    False,
                    f'Model "{target}" not found in your OpenAI account. '
                    f'Check API key permissions and model access.',
                )
            return True, f'OpenAI API accessible. Model "{target}" available.'
        except ImportError as e:
            return False, str(e)
        except Exception as e:
            return False, f'OpenAI health check failed: {e}'

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
            client = self._get_client()

            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})

            params: dict[str, Any] = {
                'model': self.model_name or 'gpt-4o-mini',
                'messages': messages,
            }
            temp = temperature if temperature is not None else self.extra_config.get('temperature')
            if temp is not None:
                params['temperature'] = temp
            if max_tokens is not None:
                params['max_tokens'] = max_tokens

            response = client.chat.completions.create(**params)
            choice = response.choices[0]

            usage = {}
            if response.usage:
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens,
                }

            return ChatResponse(
                text=choice.message.content or '',
                model=response.model,
                usage=usage,
                finish_reason=choice.finish_reason or '',
                raw={},
            )
        except Exception as e:
            logger.error('OpenAI generate error: %s', e)
            raise RuntimeError(f'OpenAI generation failed: {e}') from e

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(self, texts: list[str]) -> EmbeddingResponse:
        try:
            client = self._get_client()
            model = self.extra_config.get('embedding_model', 'text-embedding-3-small')

            response = client.embeddings.create(
                model=model,
                input=texts,
            )

            embeddings = [item.embedding for item in response.data]
            dimension = len(embeddings[0]) if embeddings else 0

            usage = {}
            if response.usage:
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens,
                }

            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                dimension=dimension,
                usage=usage,
            )
        except ImportError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            logger.error('OpenAI embed error: %s', e)
            raise RuntimeError(f'OpenAI embedding failed: {e}') from e

    @property
    def provider_name(self) -> str:
        return 'OpenAI'
