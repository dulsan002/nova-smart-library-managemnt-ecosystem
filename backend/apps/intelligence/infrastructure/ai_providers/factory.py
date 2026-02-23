"""
AI Provider Factory — resolves the active provider from DB configuration.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from .base import AIProvider

logger = logging.getLogger('nova.intelligence.ai_providers.factory')

# Registry mapping provider enum → class
_PROVIDER_MAP: dict[str, type[AIProvider]] = {}


def _ensure_registry():
    """Populate the registry on first use."""
    if _PROVIDER_MAP:
        return
    from .ollama import OllamaProvider
    from .gemini import GeminiProvider
    from .openai_provider import OpenAIProvider

    _PROVIDER_MAP.update({
        'OLLAMA': OllamaProvider,
        'GEMINI': GeminiProvider,
        'OPENAI': OpenAIProvider,
    })


def build_provider(config_record) -> AIProvider:
    """
    Build an AIProvider instance from an AIProviderConfig model instance.
    """
    _ensure_registry()

    provider_key = config_record.provider
    provider_cls = _PROVIDER_MAP.get(provider_key)
    if not provider_cls:
        raise ValueError(
            f'Unknown AI provider "{provider_key}". '
            f'Available: {", ".join(_PROVIDER_MAP.keys())}'
        )

    config_dict: dict[str, Any] = {
        'model_name': config_record.model_name,
        'api_base_url': config_record.api_base_url,
        'api_key': config_record.api_key,
        'extra_config': config_record.extra_config or {},
    }

    return provider_cls(config_dict)


def get_provider(capability: str) -> AIProvider | None:
    """
    Get the currently active AI provider for a given capability.

    Parameters
    ----------
    capability : str
        One of 'CHAT', 'EMBEDDING', 'SUMMARIZATION', 'CLASSIFICATION'.

    Returns
    -------
    AIProvider | None
        The active provider, or None if no active config exists.
    """
    from apps.intelligence.domain.models import AIProviderConfig

    try:
        config = AIProviderConfig.objects.get(
            capability=capability,
            is_active=True,
        )
        return build_provider(config)
    except AIProviderConfig.DoesNotExist:
        logger.debug('No active AI provider for capability=%s', capability)
        return None
    except AIProviderConfig.MultipleObjectsReturned:
        # Pick the most recently updated one
        config = AIProviderConfig.objects.filter(
            capability=capability,
            is_active=True,
        ).order_by('-updated_at').first()
        if config:
            return build_provider(config)
        return None


def get_chat_provider() -> AIProvider | None:
    """Shortcut for the active CHAT provider."""
    return get_provider('CHAT')


def get_embedding_provider() -> AIProvider | None:
    """Shortcut for the active EMBEDDING provider."""
    return get_provider('EMBEDDING')


def get_all_configs() -> list[dict[str, Any]]:
    """Return all provider configs (for admin listing)."""
    from apps.intelligence.domain.models import AIProviderConfig
    return list(AIProviderConfig.objects.all().values(
        'id', 'provider', 'capability', 'display_name', 'model_name',
        'api_base_url', 'is_active', 'is_healthy', 'last_health_check',
        'last_error', 'extra_config', 'created_at', 'updated_at',
    ))


def test_provider_config(config_id: str) -> tuple[bool, str]:
    """
    Run a health check against a specific provider config.
    Updates the config's health status in the database.

    Returns
    -------
    (healthy, message) : tuple[bool, str]
    """
    from apps.intelligence.domain.models import AIProviderConfig

    config = AIProviderConfig.objects.get(id=config_id)
    provider = build_provider(config)
    healthy, message = provider.health_check()

    if healthy:
        config.mark_healthy()
    else:
        config.mark_unhealthy(message)

    return healthy, message
