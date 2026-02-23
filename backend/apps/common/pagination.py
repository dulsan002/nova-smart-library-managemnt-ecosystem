"""
Nova — Cursor-Based Pagination
================================
GraphQL-compatible cursor-based pagination for all list queries.
"""

import base64
from typing import Any, List, Optional, Tuple

from django.db.models import QuerySet

import graphene


class Edge:
    """Generic edge wrapper for Relay-style cursor pagination."""
    __slots__ = ('node', 'cursor')

    def __init__(self, node, cursor):
        self.node = node
        self.cursor = cursor


def encode_cursor(value: Any) -> str:
    """Encode a cursor value to a base64 string."""
    return base64.b64encode(str(value).encode('utf-8')).decode('utf-8')


def decode_cursor(cursor: str) -> str:
    """Decode a base64 cursor string to its original value."""
    try:
        return base64.b64decode(cursor.encode('utf-8')).decode('utf-8')
    except Exception:
        return ''


class PageInfo(graphene.ObjectType):
    """Pagination metadata for connections."""
    has_next_page = graphene.Boolean(required=True)
    has_previous_page = graphene.Boolean(required=True)
    start_cursor = graphene.String()
    end_cursor = graphene.String()
    total_count = graphene.Int()


def paginate_queryset(
    queryset: QuerySet,
    first: Optional[int] = None,
    after: Optional[str] = None,
    last: Optional[int] = None,
    before: Optional[str] = None,
    order_by: str = '-created_at',
    max_page_size: int = 50,
) -> Tuple[QuerySet, dict]:
    """
    Apply cursor-based pagination to a queryset.

    Args:
        queryset: The Django QuerySet to paginate.
        first: Number of items to return from the start.
        after: Cursor after which to start returning items.
        last: Number of items to return from the end.
        before: Cursor before which to start returning items.
        order_by: Field to order by (prefix with '-' for descending).
        max_page_size: Maximum allowed page size.

    Returns:
        Tuple of (paginated_queryset, page_info_dict).
    """
    total_count = queryset.count()

    # Apply ordering
    queryset = queryset.order_by(order_by)

    # Determine page size
    page_size = min(first or last or 20, max_page_size)

    # Handle 'after' cursor (forward pagination)
    offset = 0
    if after:
        try:
            offset = int(decode_cursor(after)) + 1
        except (ValueError, TypeError):
            offset = 0

    # Handle 'before' cursor (backward pagination)
    if before:
        try:
            before_offset = int(decode_cursor(before))
            offset = max(0, before_offset - page_size)
        except (ValueError, TypeError):
            pass

    # Apply slice
    items = list(queryset[offset:offset + page_size])

    has_next_page = (offset + page_size) < total_count
    has_previous_page = offset > 0

    start_cursor = encode_cursor(offset) if items else None
    end_cursor = encode_cursor(offset + len(items) - 1) if items else None

    # Build Relay-style edges with node + cursor
    edges = [
        Edge(node=item, cursor=encode_cursor(offset + i))
        for i, item in enumerate(items)
    ]

    page_info = {
        'has_next_page': has_next_page,
        'has_previous_page': has_previous_page,
        'start_cursor': start_cursor,
        'end_cursor': end_cursor,
        'total_count': total_count,
    }

    return {
        'edges': edges,
        'has_next_page': has_next_page,
        'has_previous_page': has_previous_page,
        'start_cursor': start_cursor,
        'end_cursor': end_cursor,
        'total_count': total_count,
        'page_info': page_info,
    }
