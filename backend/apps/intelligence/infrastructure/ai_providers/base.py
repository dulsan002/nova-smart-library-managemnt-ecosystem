"""
Base AI Provider — abstract interface for all providers.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger('nova.intelligence.ai_providers')


@dataclass
class ChatResponse:
    """Standardised response from a chat/generation provider."""
    text: str
    model: str = ''
    usage: dict[str, Any] = field(default_factory=dict)
    finish_reason: str = ''
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Standardised response from an embedding provider."""
    embeddings: list[list[float]]
    model: str = ''
    dimension: int = 0
    usage: dict[str, Any] = field(default_factory=dict)


class AIProvider(abc.ABC):
    """
    Abstract base class for all AI provider integrations.

    Each concrete provider implements:
    - health_check() to verify connectivity
    - generate() for text generation / chat
    - embed() for embedding text (optional — raises NotImplementedError)
    """

    def __init__(self, config: dict[str, Any]):
        """
        Parameters
        ----------
        config : dict
            Contains at minimum:
            - model_name: str
            - api_base_url: str
            - api_key: str
            - extra_config: dict
        """
        self.model_name = config.get('model_name', '')
        self.api_base_url = config.get('api_base_url', '').rstrip('/')
        self.api_key = config.get('api_key', '')
        self.extra_config = config.get('extra_config', {})
        self._config = config

    @abc.abstractmethod
    def health_check(self) -> tuple[bool, str]:
        """
        Verify the provider is reachable and the model is available.

        Returns
        -------
        (healthy, message) : tuple[bool, str]
        """
        ...

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str = '',
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate text from a prompt."""
        ...

    def embed(self, texts: list[str]) -> EmbeddingResponse:
        """
        Generate embeddings for a list of texts.
        Not all providers support this — default raises NotImplementedError.
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} does not support embeddings.'
        )

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__
