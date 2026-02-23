"""
Ollama Provider — local LLM inference via Ollama REST API.
Supports models like llama3.1, mistral, codellama, etc.

Requires Ollama running locally (default: http://localhost:11434).
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .base import AIProvider, ChatResponse, EmbeddingResponse

logger = logging.getLogger('nova.intelligence.ai_providers.ollama')

DEFAULT_OLLAMA_URL = 'http://localhost:11434'


class OllamaProvider(AIProvider):
    """Ollama local LLM provider."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        if not self.api_base_url:
            self.api_base_url = DEFAULT_OLLAMA_URL

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> tuple[bool, str]:
        try:
            # Check server is running
            resp = requests.get(f'{self.api_base_url}/api/tags', timeout=10)
            resp.raise_for_status()
            models = resp.json().get('models', [])
            model_names = [m.get('name', '').split(':')[0] for m in models]

            if self.model_name and self.model_name not in model_names:
                # Check if any variant matches
                if not any(self.model_name in n for n in model_names):
                    return (
                        False,
                        f'Model "{self.model_name}" not found. '
                        f'Available: {", ".join(model_names[:10])}. '
                        f'Run: ollama pull {self.model_name}',
                    )

            return True, f'Ollama is running with {len(models)} model(s) available.'
        except requests.ConnectionError:
            return False, f'Cannot connect to Ollama at {self.api_base_url}. Is it running?'
        except Exception as e:
            return False, f'Ollama health check failed: {e}'

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
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        options: dict[str, Any] = {}
        temp = temperature if temperature is not None else self.extra_config.get('temperature')
        if temp is not None:
            options['temperature'] = temp
        if max_tokens is not None:
            options['num_predict'] = max_tokens

        payload: dict[str, Any] = {
            'model': self.model_name,
            'messages': messages,
            'stream': False,
            'options': options,
        }

        try:
            resp = requests.post(
                f'{self.api_base_url}/api/chat',
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

            return ChatResponse(
                text=data.get('message', {}).get('content', ''),
                model=data.get('model', self.model_name),
                usage={
                    'prompt_tokens': data.get('prompt_eval_count', 0),
                    'completion_tokens': data.get('eval_count', 0),
                    'total_duration_ns': data.get('total_duration', 0),
                },
                finish_reason=data.get('done_reason', ''),
                raw=data,
            )
        except requests.RequestException as e:
            logger.error('Ollama generate error: %s', e)
            raise RuntimeError(f'Ollama generation failed: {e}') from e

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def embed(self, texts: list[str]) -> EmbeddingResponse:
        all_embeddings = []
        dimension = 0

        for text in texts:
            payload = {
                'model': self.model_name,
                'prompt': text,
            }
            try:
                resp = requests.post(
                    f'{self.api_base_url}/api/embeddings',
                    json=payload,
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                embedding = data.get('embedding', [])
                all_embeddings.append(embedding)
                if not dimension and embedding:
                    dimension = len(embedding)
            except requests.RequestException as e:
                logger.error('Ollama embed error: %s', e)
                raise RuntimeError(f'Ollama embedding failed: {e}') from e

        return EmbeddingResponse(
            embeddings=all_embeddings,
            model=self.model_name,
            dimension=dimension,
        )

    @property
    def provider_name(self) -> str:
        return 'Ollama'
