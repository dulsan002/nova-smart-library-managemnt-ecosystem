"""
Tests for Nova Middleware
==========================
Covers all five middleware classes:
- SecurityHeadersMiddleware
- GraphQLSecurityMiddleware
- RateLimitingMiddleware
- ExceptionHandlerMiddleware
- RequestLoggingMiddleware
"""

import json
import time
import pytest
import django.test
from unittest.mock import MagicMock, patch, PropertyMock

from django.http import HttpResponse
from django.test import RequestFactory, override_settings

# ═══════════════════════════════════════════════════════════════════════
#  SecurityHeadersMiddleware
# ═══════════════════════════════════════════════════════════════════════

from nova.middleware.security_headers import SecurityHeadersMiddleware


class TestSecurityHeadersUniversal:
    """Headers added to every response regardless of DEBUG."""

    @pytest.fixture()
    def mw(self):
        return SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))

    @pytest.fixture()
    def rf(self):
        return RequestFactory()

    def test_nosniff(self, mw, rf):
        resp = mw(rf.get("/"))
        assert resp["X-Content-Type-Options"] == "nosniff"

    def test_xss_protection_zero(self, mw, rf):
        resp = mw(rf.get("/"))
        assert resp["X-XSS-Protection"] == "0"

    def test_referrer_policy(self, mw, rf):
        resp = mw(rf.get("/"))
        assert resp["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_dns_prefetch_off(self, mw, rf):
        resp = mw(rf.get("/"))
        assert resp["X-DNS-Prefetch-Control"] == "off"

    def test_permissions_policy(self, mw, rf):
        resp = mw(rf.get("/"))
        pp = resp["Permissions-Policy"]
        assert "camera=()" in pp
        assert "microphone=()" in pp

    def test_cross_origin_opener(self, mw, rf):
        resp = mw(rf.get("/"))
        assert resp["Cross-Origin-Opener-Policy"] == "same-origin"

    def test_cross_origin_resource(self, mw, rf):
        resp = mw(rf.get("/"))
        assert resp["Cross-Origin-Resource-Policy"] == "same-origin"

    def test_csp_nonce_on_request(self, mw, rf):
        req = rf.get("/")
        mw(req)
        assert hasattr(req, "csp_nonce")
        assert len(req.csp_nonce) == 32

    def test_nonce_is_unique(self, mw, rf):
        r1, r2 = rf.get("/"), rf.get("/")
        mw(r1)
        mw(r2)
        assert r1.csp_nonce != r2.csp_nonce


class TestSecurityHeadersProduction:
    """Production-only headers (DEBUG=False)."""

    @override_settings(DEBUG=False)
    def test_adds_csp(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/"))
        csp = resp["Content-Security-Policy"]
        assert "strict-dynamic" in csp
        assert "default-src 'self'" in csp

    @override_settings(DEBUG=False)
    def test_csp_contains_request_nonce(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        req = RequestFactory().get("/")
        resp = mw(req)
        assert f"nonce-{req.csp_nonce}" in resp["Content-Security-Policy"]

    @override_settings(DEBUG=False)
    def test_x_frame_deny(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/"))
        assert resp["X-Frame-Options"] == "DENY"

    @override_settings(DEBUG=False)
    def test_coep(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/"))
        assert resp["Cross-Origin-Embedder-Policy"] == "require-corp"


@override_settings(DEBUG=True)
class TestSecurityHeadersDebug(django.test.SimpleTestCase):
    def test_no_csp(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/"))
        assert "Content-Security-Policy" not in resp

    def test_no_x_frame(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/"))
        assert "X-Frame-Options" not in resp


class TestSecurityHeadersGraphQL:
    def test_graphql_no_cache(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/graphql"))
        assert "no-store" in resp["Cache-Control"]
        assert resp["Pragma"] == "no-cache"

    def test_non_graphql_no_cache_header_absent(self):
        mw = SecurityHeadersMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(RequestFactory().get("/api/healthz"))
        assert "Cache-Control" not in resp


# ═══════════════════════════════════════════════════════════════════════
#  GraphQLSecurityMiddleware
# ═══════════════════════════════════════════════════════════════════════

from nova.middleware.graphql_security import (
    GraphQLSecurityMiddleware,
    _measure_depth,
    _count_aliases,
    _estimate_complexity,
    _has_introspection,
)


class TestGraphQLHelpers:
    def test_measure_depth_flat(self):
        assert _measure_depth("{ me { email } }") == 2

    def test_measure_depth_nested(self):
        q = "{ a { b { c { d } } } }"
        assert _measure_depth(q) == 4

    def test_count_aliases_none(self):
        assert _count_aliases("{ me { email } }") == 0

    def test_count_aliases_present(self):
        q = "{ first: me { email } second: me { id } }"
        assert _count_aliases(q) == 2

    def test_count_aliases_ignores_keywords(self):
        q = "query MyQuery { me { email } }"
        assert _count_aliases(q) == 0

    def test_estimate_complexity_simple(self):
        assert _estimate_complexity("{ me { email } }") >= 1

    def test_estimate_complexity_expensive_field(self):
        c = _estimate_complexity("{ books { title } }")
        assert c >= 5  # books is cost=5

    def test_has_introspection_schema(self):
        assert _has_introspection("{ __schema { types { name } } }") is True

    def test_has_introspection_type(self):
        assert _has_introspection('{ __type(name: "User") { name } }') is True

    def test_has_introspection_none(self):
        assert _has_introspection("{ me { email } }") is False


class TestGraphQLSecurityMiddleware:
    @pytest.fixture()
    def mw(self):
        return GraphQLSecurityMiddleware(lambda r: HttpResponse("OK"))

    @pytest.fixture()
    def rf(self):
        return RequestFactory()

    def _post_gql(self, rf, body_dict):
        return rf.post(
            "/graphql",
            data=json.dumps(body_dict),
            content_type="application/json",
        )

    def test_passthrough_non_graphql(self, mw, rf):
        assert mw(rf.get("/healthz/")).status_code == 200

    def test_passthrough_get(self, mw, rf):
        assert mw(rf.get("/graphql")).status_code == 200

    def test_normal_query_allowed(self, mw, rf):
        req = self._post_gql(rf, {"query": "{ me { email } }"})
        assert mw(req).status_code == 200

    def test_invalid_json(self, mw, rf):
        req = rf.post("/graphql", data=b"NOT JSON", content_type="application/json")
        resp = mw(req)
        assert resp.status_code == 400
        assert "INVALID_REQUEST" in resp.content.decode()

    @override_settings(GRAPHQL_SECURITY={"MAX_QUERY_SIZE_BYTES": 20})
    def test_oversized_query(self):
        mw = GraphQLSecurityMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "x" * 100}).encode()
        req = RequestFactory().post("/graphql", data=body, content_type="application/json")
        resp = mw(req)
        assert resp.status_code == 400
        assert "QUERY_TOO_LARGE" in resp.content.decode()

    @override_settings(GRAPHQL_SECURITY={"MAX_DEPTH": 3})
    def test_depth_exceeded(self):
        mw = GraphQLSecurityMiddleware(lambda r: HttpResponse("OK"))
        q = "{ a { b { c { d { e } } } } }"  # depth=5
        body = json.dumps({"query": q}).encode()
        req = RequestFactory().post("/graphql", data=body, content_type="application/json")
        resp = mw(req)
        assert resp.status_code == 400
        assert "QUERY_TOO_DEEP" in resp.content.decode()

    @override_settings(GRAPHQL_SECURITY={"MAX_ALIASES": 1})
    def test_too_many_aliases(self):
        mw = GraphQLSecurityMiddleware(lambda r: HttpResponse("OK"))
        q = "{ a1: me { email } a2: me { id } a3: me { name } }"
        body = json.dumps({"query": q}).encode()
        req = RequestFactory().post("/graphql", data=body, content_type="application/json")
        resp = mw(req)
        assert resp.status_code == 400
        assert "TOO_MANY_ALIASES" in resp.content.decode()

    @override_settings(DEBUG=False, GRAPHQL_SECURITY={"INTROSPECTION_ENABLED": False})
    def test_introspection_blocked_in_production(self):
        mw = GraphQLSecurityMiddleware(lambda r: HttpResponse("OK"))
        q = "{ __schema { types { name } } }"
        body = json.dumps({"query": q}).encode()
        req = RequestFactory().post("/graphql", data=body, content_type="application/json")
        resp = mw(req)
        assert resp.status_code == 400
        assert "INTROSPECTION_DISABLED" in resp.content.decode()

    @override_settings(GRAPHQL_SECURITY={"MAX_BATCH_SIZE": 2})
    def test_batch_limit_exceeded(self):
        mw = GraphQLSecurityMiddleware(lambda r: HttpResponse("OK"))
        batch = [{"query": "{ me { email } }"}] * 5
        body = json.dumps(batch).encode()
        req = RequestFactory().post("/graphql", data=body, content_type="application/json")
        resp = mw(req)
        assert resp.status_code == 400
        assert "BATCH_LIMIT_EXCEEDED" in resp.content.decode()

    def test_batch_within_limit_ok(self, mw, rf):
        batch = [{"query": "{ me { email } }"}] * 2
        body = json.dumps(batch).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        assert mw(req).status_code == 200

    def test_empty_query_body_passes(self, mw, rf):
        req = self._post_gql(rf, {"query": ""})
        assert mw(req).status_code == 200


# ═══════════════════════════════════════════════════════════════════════
#  ExceptionHandlerMiddleware
# ═══════════════════════════════════════════════════════════════════════

from nova.middleware.exception_handler import ExceptionHandlerMiddleware
from apps.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    RateLimitExceededError,
    NovaBaseException,
)


class TestExceptionHandler:
    @pytest.fixture()
    def rf(self):
        return RequestFactory()

    def _make_mw(self, exc):
        def get_response(request):
            raise exc
        return ExceptionHandlerMiddleware(get_response)

    def test_auth_error_401(self, rf):
        mw = self._make_mw(AuthenticationError("Invalid token"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 401
        body = json.loads(resp.content)
        assert body["errors"][0]["message"] == "Invalid token"

    def test_authorization_error_403(self, rf):
        mw = self._make_mw(AuthorizationError("Forbidden"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 403

    def test_not_found_error_404(self, rf):
        mw = self._make_mw(NotFoundError("No such book"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 404

    def test_validation_error_400(self, rf):
        mw = self._make_mw(ValidationError("Bad input"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 400

    def test_rate_limit_429_with_retry(self, rf):
        exc = RateLimitExceededError(retry_after=30)
        mw = self._make_mw(exc)
        resp = mw(rf.get("/"))
        assert resp.status_code == 429
        assert resp["Retry-After"] == "30"

    def test_generic_nova_exception_400(self, rf):
        mw = self._make_mw(NovaBaseException("Something wrong"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 400

    @override_settings(DEBUG=False)
    def test_unhandled_exception_500_production_hides_details(self, rf):
        mw = self._make_mw(RuntimeError("kaboom"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 500
        body = json.loads(resp.content)
        assert "kaboom" not in body["errors"][0]["message"]
        assert body["errors"][0]["extensions"]["code"] == "INTERNAL_ERROR"

    @override_settings(DEBUG=True)
    def test_unhandled_exception_500_debug_shows_details(self, rf):
        mw = self._make_mw(RuntimeError("kaboom"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 500
        body = json.loads(resp.content)
        assert "kaboom" in body["errors"][0]["message"]
        assert "traceback" in body["errors"][0]["extensions"]

    def test_process_exception_hook(self, rf):
        mw = ExceptionHandlerMiddleware(lambda r: HttpResponse("OK"))
        resp = mw.process_exception(rf.get("/"), NotFoundError("Gone"))
        assert resp.status_code == 404

    def test_no_exception_passes_through(self, rf):
        mw = ExceptionHandlerMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(rf.get("/"))
        assert resp.status_code == 200

    def test_error_details_in_body(self, rf):
        exc = ValidationError("Bad", details={"field": "email"})
        mw = self._make_mw(exc)
        resp = mw(rf.get("/"))
        body = json.loads(resp.content)
        assert body["errors"][0]["extensions"]["details"] == {"field": "email"}


# ═══════════════════════════════════════════════════════════════════════
#  RequestLoggingMiddleware
# ═══════════════════════════════════════════════════════════════════════

from nova.middleware.request_logging import RequestLoggingMiddleware


class TestRequestLogging:
    @pytest.fixture()
    def mw(self):
        return RequestLoggingMiddleware(lambda r: HttpResponse("OK"))

    @pytest.fixture()
    def rf(self):
        return RequestFactory()

    def test_request_id_assigned(self, mw, rf):
        req = rf.get("/")
        mw(req)
        assert hasattr(req, "request_id")
        assert len(req.request_id) == 8

    def test_request_id_in_response_header(self, mw, rf):
        resp = mw(rf.get("/"))
        assert "X-Request-ID" in resp

    def test_request_id_matches(self, mw, rf):
        req = rf.get("/")
        resp = mw(req)
        assert resp["X-Request-ID"] == req.request_id

    def test_logs_info_for_200(self, mw, rf, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="nova"):
            mw(rf.get("/"))
        assert any("Request completed" in r.message for r in caplog.records)

    def test_logs_warning_for_4xx(self, rf, caplog):
        import logging
        mw = RequestLoggingMiddleware(lambda r: HttpResponse("Nope", status=404))
        with caplog.at_level(logging.WARNING, logger="nova"):
            mw(rf.get("/"))
        assert any("Request completed" in r.message for r in caplog.records)

    def test_logs_error_for_5xx(self, rf, caplog):
        import logging
        mw = RequestLoggingMiddleware(lambda r: HttpResponse("Error", status=500))
        with caplog.at_level(logging.ERROR, logger="nova"):
            mw(rf.get("/"))
        assert any("Request completed" in r.message for r in caplog.records)

    def test_client_ip_from_forwarded(self, mw, rf):
        req = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
        resp = mw(req)
        # Just verify middleware ran (IP is in log, not response)
        assert resp.status_code == 200

    def test_unique_request_ids(self, mw, rf):
        r1, r2 = rf.get("/"), rf.get("/")
        mw(r1)
        mw(r2)
        assert r1.request_id != r2.request_id


# ═══════════════════════════════════════════════════════════════════════
#  RateLimitingMiddleware
# ═══════════════════════════════════════════════════════════════════════

from nova.middleware.rate_limiting import RateLimitingMiddleware


class TestRateLimitingMiddleware:
    @pytest.fixture()
    def rf(self):
        return RequestFactory()

    @override_settings(RATE_LIMIT_ENABLED=False)
    def test_skip_when_disabled(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(rf.get("/graphql"))
        assert resp.status_code == 200

    @override_settings(RATE_LIMIT_ENABLED=True)
    def test_skip_non_graphql(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        resp = mw(rf.get("/healthz/"))
        assert resp.status_code == 200

    def test_determine_tier_auth(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "mutation { login(email: \"x\") { token } }"}).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        assert mw._determine_tier(req) == "AUTH"

    def test_determine_tier_upload(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "mutation { uploadDigitalAsset { id } }"}).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        assert mw._determine_tier(req) == "UPLOAD"

    def test_determine_tier_mutation(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "mutation { createBook { id } }"}).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        assert mw._determine_tier(req) == "MUTATION"

    def test_determine_tier_query(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "{ me { email } }"}).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        assert mw._determine_tier(req) == "QUERY"

    def test_determine_tier_heartbeat(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "mutation { heartbeat { ok } }"}).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        assert mw._determine_tier(req) == "HEARTBEAT"

    def test_determine_tier_get_fallback(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        req = rf.get("/graphql")
        assert mw._determine_tier(req) == "QUERY"

    def test_get_limit_config_auth(self):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        cfg = mw._get_limit_config("AUTH")
        assert cfg["requests"] == 5
        assert cfg["window"] == 60

    def test_get_limit_config_unknown_defaults_to_query(self):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        cfg = mw._get_limit_config("UNKNOWN")
        assert cfg == mw._get_limit_config("QUERY")

    def test_generate_key_anonymous(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        req = rf.get("/")
        req.user = MagicMock(is_authenticated=False)
        key = mw._generate_key(req, "QUERY")
        assert key.startswith("rl:ip:")
        assert ":QUERY" in key

    def test_generate_key_authenticated(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        req = rf.get("/")
        req.user = MagicMock(is_authenticated=True, id=42)
        key = mw._generate_key(req, "AUTH")
        assert key == "rl:user:42:AUTH"

    @override_settings(RATE_LIMIT_ENABLED=True)
    def test_rate_limit_adds_remaining_header(self, rf):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        body = json.dumps({"query": "{ me { email } }"}).encode()
        req = rf.post("/graphql", data=body, content_type="application/json")
        req.user = MagicMock(is_authenticated=False)
        resp = mw(req)
        assert "X-RateLimit-Remaining" in resp

    @override_settings(RATE_LIMIT_ENABLED=True)
    def test_check_rate_limit_fail_open_on_cache_error(self):
        mw = RateLimitingMiddleware(lambda r: HttpResponse("OK"))
        with patch("django.core.cache.cache") as mock_cache:
            mock_cache.get.side_effect = ConnectionError("Redis down")
            allowed, remaining, retry = mw._check_rate_limit("key", 10, 60)
            assert allowed is True

    def test_client_ip_direct(self, rf):
        req = rf.get("/", REMOTE_ADDR="10.0.0.1")
        assert RateLimitingMiddleware._get_client_ip(req) == "10.0.0.1"

    def test_client_ip_forwarded(self, rf):
        req = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 10.0.0.1")
        assert RateLimitingMiddleware._get_client_ip(req) == "1.2.3.4"
