"""
AI Provider Abstraction Layer
=================================
Factory-based provider system supporting Ollama, Google Gemini, OpenAI,
and local transformer models. Configuration is stored in the database
and managed by super-admins via GraphQL.
"""

from .base import AIProvider, ChatResponse, EmbeddingResponse
from .factory import get_provider, get_chat_provider, get_embedding_provider

__all__ = [
    'AIProvider',
    'ChatResponse',
    'EmbeddingResponse',
    'get_provider',
    'get_chat_provider',
    'get_embedding_provider',
]
