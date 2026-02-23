"""
Nova — GraphQL Security Middleware
=====================================
Protects the GraphQL endpoint against abuse:

1. **Query Depth Limiting** – Prevents deeply nested queries that
   fan-out into exponential resolver calls (e.g. user→borrows→book→author→books…).

2. **Query Complexity / Cost Analysis** – Each field is assigned a
   cost multiplier; total cost must stay below the configured maximum.

3. **Introspection Control** – ``__schema`` / ``__type`` introspection
   queries are only allowed when ``settings.DEBUG`` is ``True``.

4. **Batch Request Limiting** – Prevents batched-array attacks where
   a single HTTP body contains dozens of operations.

5. **Query Size Limiting** – Rejects abnormally large query strings
   before the parser even starts.

All thresholds are read from ``settings.GRAPHQL_SECURITY`` with sane
production defaults so a missing key never degrades security.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse

logger = logging.getLogger("nova.security")

# =========================================================================
# Configuration helpers
# =========================================================================

_DEFAULTS: Dict[str, Any] = {
    "MAX_DEPTH": 10,
    "MAX_COMPLEXITY": 1000,
    "MAX_ALIASES": 15,
    "MAX_QUERY_SIZE_BYTES": 10_000,       # 10 KB
    "MAX_BATCH_SIZE": 5,
    "INTROSPECTION_ENABLED": None,        # None = follow DEBUG
    "FIELD_COSTS": {                       # custom per-field costs
        "books": 5,
        "users": 5,
        "allBorrows": 5,
        "auditLogs": 5,
        "recommendations": 8,
        "searchBooks": 10,
        "semanticSearch": 15,
        "readingPatterns": 5,
        "collectionGaps": 8,
        "overdueRiskPredictions": 10,
    },
}


def _conf(key: str):
    """Return GRAPHQL_SECURITY[key] or the built-in default."""
    return getattr(settings, "GRAPHQL_SECURITY", {}).get(key, _DEFAULTS[key])


# =========================================================================
# Lightweight AST helpers (regex-based – no graphql-core dependency)
# =========================================================================

_OPEN_BRACE = re.compile(r"\{")
_CLOSE_BRACE = re.compile(r"\}")
_FIELD_NAME = re.compile(r"([a-zA-Z_]\w*)\s*[\({]")
_ALIAS_PATTERN = re.compile(r"(\w+)\s*:")
_INTROSPECTION = re.compile(r"\b__schema\b|\b__type\b")
_FRAGMENT_SPREAD = re.compile(r"\.\.\.\s*(\w+)")
_FRAGMENT_DEF = re.compile(r"fragment\s+(\w+)\s+on\s+\w+\s*\{")


def _measure_depth(query: str) -> int:
    """Return the maximum nesting depth of ``{`` braces."""
    depth = 0
    max_depth = 0
    for ch in query:
        if ch == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == "}":
            depth -= 1
    return max_depth


def _count_aliases(query: str) -> int:
    """Count the number of GraphQL alias patterns (``alias: field``)."""
    # Remove string literals first to avoid false matches
    cleaned = re.sub(r'"[^"]*"', "", query)
    # Match `word:` that is NOT part of a fragment definition or variable
    aliases = _ALIAS_PATTERN.findall(cleaned)
    # Filter out known non-alias patterns (fragment, on, query, mutation, subscription)
    keywords = {"fragment", "on", "query", "mutation", "subscription", "true", "false", "null"}
    return sum(1 for a in aliases if a.lower() not in keywords)


def _estimate_complexity(query: str) -> int:
    """
    Estimate query complexity using field costs.

    Each selection field adds either its custom cost from ``FIELD_COSTS``
    or a baseline cost of 1.  ``first`` / ``last`` / ``limit`` argument
    values act as multipliers for the enclosing field.
    """
    field_costs: Dict[str, int] = _conf("FIELD_COSTS")
    total = 0

    # Extract all field names with their rough multiplier context
    for match in _FIELD_NAME.finditer(query):
        field = match.group(1)
        cost = field_costs.get(field, 1)
        total += cost

    # Add extra cost for pagination arguments (first: N, limit: N)
    for num_match in re.finditer(r"\b(?:first|last|limit)\s*:\s*(\d+)", query):
        n = int(num_match.group(1))
        total += max(0, n - 10)  # penalize large page sizes

    return total


def _has_introspection(query: str) -> bool:
    return bool(_INTROSPECTION.search(query))


# =========================================================================
# Middleware
# =========================================================================

class GraphQLSecurityMiddleware:
    """
    Django middleware that inspects incoming GraphQL requests *before*
    they reach graphene-django's view, enforcing depth / complexity /
    introspection / batch-size constraints.

    Place this **before** the GraphQL view in the middleware stack (or
    at least before ``ExceptionHandlerMiddleware`` so rejections are
    not accidentally caught and re-wrapped).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only inspect POST /graphql
        if request.method != "POST" or not request.path.rstrip("/").endswith("/graphql"):
            return self.get_response(request)

        # ----- Parse body ------------------------------------------------
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _reject("Invalid JSON body.", code="INVALID_REQUEST")

        # ----- Batch limiting --------------------------------------------
        if isinstance(body, list):
            max_batch = _conf("MAX_BATCH_SIZE")
            if len(body) > max_batch:
                logger.warning(
                    "Batch request rejected: %d operations (max %d)",
                    len(body), max_batch,
                )
                return _reject(
                    f"Batch requests limited to {max_batch} operations.",
                    code="BATCH_LIMIT_EXCEEDED",
                )
            queries = [item.get("query", "") for item in body if isinstance(item, dict)]
        elif isinstance(body, dict):
            queries = [body.get("query", "")]
        else:
            return _reject("Unexpected request format.", code="INVALID_REQUEST")

        # ----- Per-query checks ------------------------------------------
        for query in queries:
            rejection = self._check_query(query, request)
            if rejection is not None:
                return rejection

        return self.get_response(request)

    # -----------------------------------------------------------------
    # Per-query gate
    # -----------------------------------------------------------------

    def _check_query(self, query: str, request: HttpRequest) -> Optional[JsonResponse]:
        if not query:
            return None

        # --- Query size ---
        max_size = _conf("MAX_QUERY_SIZE_BYTES")
        if len(query.encode("utf-8")) > max_size:
            logger.warning("Query size exceeded: %d bytes", len(query.encode("utf-8")))
            return _reject(
                f"Query exceeds maximum size of {max_size} bytes.",
                code="QUERY_TOO_LARGE",
            )

        # --- Introspection ---
        introspection_enabled = _conf("INTROSPECTION_ENABLED")
        if introspection_enabled is None:
            introspection_enabled = settings.DEBUG
        if not introspection_enabled and _has_introspection(query):
            logger.warning("Introspection query blocked in production")
            return _reject(
                "Introspection queries are disabled.",
                code="INTROSPECTION_DISABLED",
            )

        # --- Depth ---
        max_depth = _conf("MAX_DEPTH")
        depth = _measure_depth(query)
        if depth > max_depth:
            _log_abuse("depth", request, depth=depth, max=max_depth)
            return _reject(
                f"Query depth {depth} exceeds maximum of {max_depth}.",
                code="QUERY_TOO_DEEP",
            )

        # --- Aliases ---
        max_aliases = _conf("MAX_ALIASES")
        alias_count = _count_aliases(query)
        if alias_count > max_aliases:
            _log_abuse("aliases", request, count=alias_count, max=max_aliases)
            return _reject(
                f"Too many aliases ({alias_count}). Maximum is {max_aliases}.",
                code="TOO_MANY_ALIASES",
            )

        # --- Complexity ---
        max_complexity = _conf("MAX_COMPLEXITY")
        complexity = _estimate_complexity(query)
        if complexity > max_complexity:
            _log_abuse("complexity", request, cost=complexity, max=max_complexity)
            return _reject(
                f"Query complexity {complexity} exceeds maximum of {max_complexity}.",
                code="QUERY_TOO_COMPLEX",
            )

        return None


# =========================================================================
# Helpers
# =========================================================================

def _reject(message: str, code: str = "FORBIDDEN", status: int = 400) -> JsonResponse:
    return JsonResponse(
        {
            "errors": [
                {
                    "message": message,
                    "extensions": {"code": code},
                }
            ]
        },
        status=status,
    )


def _log_abuse(kind: str, request: HttpRequest, **extra):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    user_id = getattr(getattr(request, "user", None), "id", None)
    logger.warning(
        "GraphQL abuse detected: %s",
        kind,
        extra={"ip": ip, "user_id": str(user_id) if user_id else None, **extra},
    )
