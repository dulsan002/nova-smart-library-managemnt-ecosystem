"""
Nova — LLM-Powered Search Assistant
=======================================
Takes a user's search query (including natural language questions),
finds relevant books via the hybrid search engine, then sends the
question + book context to the configured LLM for a conversational answer.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger('nova.intelligence.llm_search')


@dataclass
class AISearchResult:
    """Result from an AI-powered search."""
    answer: str = ''
    sources: list[dict[str, Any]] = field(default_factory=list)
    model_used: str = ''
    error: str = ''


SEARCH_SYSTEM_PROMPT = """You are NovaLib AI, an intelligent library assistant for the Nova Smart Library Management System.
You help users find books, answer questions about the library's collection, and provide reading recommendations.

You will be given the user's question/query and a list of relevant books from the library catalog.

RULES:
- Answer the user's question directly and conversationally
- Reference specific books from the provided catalog data when relevant
- If the user is asking for recommendations, explain WHY each book is a good fit
- If asking about availability, mention copy counts
- If the query is a simple search (just a title or author name), summarize the top matches
- Keep answers concise but helpful (3-8 sentences)
- If no relevant books are found, say so honestly and suggest alternative search terms
- Do NOT make up books that aren't in the provided data
- Use a friendly, knowledgeable tone — like a helpful librarian
- Format your response in plain text (no markdown headers or code blocks)"""


def ai_search(query: str, user_id: str | None = None) -> AISearchResult:
    """
    Perform an AI-powered search:
    1. Search the catalog using the hybrid search engine
    2. Send query + results context to the LLM
    3. Return the AI's conversational answer + source books
    """
    from apps.intelligence.infrastructure.ai_providers.factory import (
        get_chat_provider,
    )
    from apps.intelligence.infrastructure.search_engine import (
        SearchEngine, SearchRequest,
    )

    # 1. Get the active CHAT provider
    provider = get_chat_provider()
    if not provider:
        return AISearchResult(
            error='No active AI provider configured. '
                  'Please ask an administrator to configure one in AI Config settings.'
        )

    # 2. Search the catalog for relevant books
    search_results = []
    try:
        request = SearchRequest(
            query=query,
            user_id=user_id,
            page=1,
            page_size=10,  # Top 10 results for context
            filters={},
        )
        search_response = SearchEngine.search(request)
        search_results = search_response.results if search_response else []
    except Exception as e:
        logger.warning('Search engine failed, falling back to simple query: %s', e)

    # Fallback: simple DB query if search engine returned nothing
    if not search_results:
        try:
            from apps.catalog.domain.models import Book
            from django.db.models import Q as DQ

            terms = query.strip().split()
            q_filter = DQ()
            for term in terms[:5]:  # Limit terms
                q_filter |= DQ(title__icontains=term) | DQ(description__icontains=term)

            fallback_books = (
                Book.objects
                .filter(q_filter)
                .prefetch_related('authors', 'categories')
                .distinct()[:10]
            )
            # Convert to a lightweight list for the enrichment step below
            search_results = [
                type('FakeResult', (), {'book_id': str(b.id), 'title': b.title, 'score': 0})()
                for b in fallback_books
            ]
        except Exception as e2:
            logger.warning('Fallback search also failed: %s', e2)

    # 3. Enrich results with full book details
    sources = []
    book_context_lines = []

    if search_results:
        from apps.catalog.domain.models import Book

        book_ids = [r.book_id for r in search_results]
        books_qs = (
            Book.all_objects
            .filter(id__in=book_ids, deleted_at__isnull=True)
            .prefetch_related('authors', 'categories')
        )
        book_map = {str(b.id): b for b in books_qs}

        for i, r in enumerate(search_results, 1):
            book = book_map.get(r.book_id)
            if not book:
                continue

            authors = [a.full_name for a in book.authors.all()]
            categories = [c.name for c in book.categories.all()]
            description = (book.description or '')[:300]

            source = {
                'bookId': r.book_id,
                'title': book.title,
                'subtitle': book.subtitle or '',
                'authors': authors,
                'categories': categories,
                'isbn': book.isbn_13 or '',
                'rating': float(book.average_rating) if book.average_rating else 0,
                'availableCopies': book.available_copies,
                'totalCopies': book.total_copies,
                'totalBorrows': book.total_borrows,
            }
            sources.append(source)

            # Build context for the LLM
            avail_text = (
                f"{book.available_copies} of {book.total_copies} copies available"
            )
            book_context_lines.append(
                f"{i}. \"{book.title}\""
                f"{' — ' + book.subtitle if book.subtitle else ''}"
                f"\n   Authors: {', '.join(authors) if authors else 'Unknown'}"
                f"\n   Categories: {', '.join(categories) if categories else 'Uncategorized'}"
                f"\n   Rating: {book.average_rating}/5.00 | Borrowed {book.total_borrows} times | {avail_text}"
                f"\n   Description: {description}{'…' if len(book.description or '') > 300 else ''}"
            )

    book_context = '\n\n'.join(book_context_lines) if book_context_lines else 'No matching books found in the catalog.'

    # 4. Build prompt
    prompt = (
        f"USER QUERY: {query}\n\n"
        f"RELEVANT BOOKS FROM CATALOG ({len(sources)} results):\n\n"
        f"{book_context}"
    )

    # 5. Send to LLM
    try:
        response = provider.generate(
            prompt,
            system_prompt=SEARCH_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=1000,
        )
    except Exception as e:
        logger.exception('LLM generation failed for search query: %s', query)
        return AISearchResult(
            sources=sources,
            error=f'AI assistant is temporarily unavailable: {e}',
            model_used=getattr(provider, 'model_name', ''),
        )

    answer = response.text.strip()
    model_used = response.model or getattr(provider, 'model_name', '')

    return AISearchResult(
        answer=answer,
        sources=sources,
        model_used=model_used,
    )
