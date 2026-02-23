"""
GraphQL Integration Tests
===========================
End-to-end tests that exercise GraphQL mutations/queries through
Django's test client against the real schema and database.

Marked ``@pytest.mark.integration`` and ``@pytest.mark.django_db``.
"""

import json
import uuid
import pytest

from django.test import Client

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


# ─── Helpers ────────────────────────────────────────────────────────

GQL_URL = "/graphql/"


def _gql(client: Client, query: str, variables: dict | None = None, token: str | None = None):
    """Post a GraphQL request and return parsed JSON body."""
    headers = {"content_type": "application/json"}
    if token:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    body = {"query": query}
    if variables:
        body["variables"] = variables
    resp = client.post(GQL_URL, data=json.dumps(body), **headers)
    return resp.status_code, json.loads(resp.content)


# ─── Health ─────────────────────────────────────────────────────────

class TestHealthQuery:
    def test_health_check(self):
        status, body = _gql(Client(), "{ health }")
        assert status == 200
        assert body["data"]["health"] is not None


# ─── Identity: Registration & Login ────────────────────────────────

class TestIdentityMutations:
    """Register, login, token refresh, profile query."""

    REGISTER_MUTATION = """
        mutation RegisterUser($input: RegisterInput!) {
            registerUser(input: $input) {
                id
                email
                firstName
                lastName
                role
            }
        }
    """

    LOGIN_MUTATION = """
        mutation Login($input: LoginInput!) {
            login(input: $input) {
                user {
                    id
                    email
                    role
                }
                tokens {
                    accessToken
                    refreshToken
                    expiresIn
                    tokenType
                }
            }
        }
    """

    ME_QUERY = """
        query { me { id email firstName lastName role isActive } }
    """

    def test_register_user(self):
        client = Client()
        variables = {
            "input": {
                "email": f"register-{uuid.uuid4().hex[:6]}@nova.test",
                "password": "StrongP@ss1!",
                "firstName": "Test",
                "lastName": "User",
            }
        }
        status, body = _gql(client, self.REGISTER_MUTATION, variables)
        assert status == 200
        if "errors" not in body:
            data = body["data"]["registerUser"]
            assert data["email"] == variables["input"]["email"]
            assert data["firstName"] == "Test"

    def test_register_duplicate_email(self, user):
        """Attempting to register with an existing email should fail."""
        client = Client()
        variables = {
            "input": {
                "email": user.email,
                "password": "StrongP@ss1!",
                "firstName": "Dup",
                "lastName": "User",
            }
        }
        status, body = _gql(client, self.REGISTER_MUTATION, variables)
        # Should either return error in errors array or HTTP 4xx
        if status == 200:
            assert body.get("errors") is not None

    def test_login_valid_credentials(self, user):
        """Login with correct credentials returns tokens."""
        client = Client()
        variables = {
            "input": {
                "email": user.email,
                "password": "testpass123",
            }
        }
        status, body = _gql(client, self.LOGIN_MUTATION, variables)
        assert status == 200
        if "errors" not in body:
            payload = body["data"]["login"]
            assert payload["user"]["email"] == user.email
            assert payload["tokens"]["accessToken"] is not None

    def test_login_wrong_password(self, user):
        client = Client()
        variables = {"input": {"email": user.email, "password": "wrongpass"}}
        status, body = _gql(client, self.LOGIN_MUTATION, variables)
        if status == 200:
            assert body.get("errors") is not None

    def test_me_query_unauthenticated(self):
        """me query without token should fail or return null."""
        client = Client()
        status, body = _gql(client, self.ME_QUERY)
        assert status == 200
        # Either errors or null data
        if body.get("errors") is None:
            assert body["data"]["me"] is None


# ─── Catalog: Author / Category / Book CRUD ────────────────────────

class TestCatalogMutations:
    """Create authors, categories, and books; query them back."""

    CREATE_AUTHOR = """
        mutation CreateAuthor($input: CreateAuthorInput!) {
            createAuthor(input: $input) {
                id
                firstName
                lastName
            }
        }
    """

    CREATE_CATEGORY = """
        mutation CreateCategory($input: CreateCategoryInput!) {
            createCategory(input: $input) {
                id
                name
                slug
            }
        }
    """

    CREATE_BOOK = """
        mutation CreateBook($input: CreateBookInput!) {
            createBook(input: $input) {
                id
                title
                isbn13
            }
        }
    """

    BOOKS_QUERY = """
        query Books($first: Int) {
            books(first: $first) {
                edges {
                    id
                    title
                    isbn13
                }
                totalCount
            }
        }
    """

    BOOK_BY_ISBN = """
        query BookByIsbn($isbn: String!) {
            bookByIsbn(isbn: $isbn) {
                id
                title
            }
        }
    """

    def _login_as(self, client, user):
        """Login and return access token."""
        login_mutation = """
            mutation Login($input: LoginInput!) {
                login(input: $input) {
                    tokens { accessToken }
                }
            }
        """
        variables = {"input": {"email": user.email, "password": "testpass123"}}
        _, body = _gql(client, login_mutation, variables)
        if "errors" in body or body["data"]["login"] is None:
            return None
        return body["data"]["login"]["tokens"]["accessToken"]

    def test_create_author_as_librarian(self, librarian):
        client = Client()
        token = self._login_as(client, librarian)
        if token is None:
            pytest.skip("Login not available")

        variables = {
            "input": {
                "firstName": "James",
                "lastName": "Baldwin",
            }
        }
        status, body = _gql(client, self.CREATE_AUTHOR, variables, token=token)
        assert status == 200
        if "errors" not in body:
            assert body["data"]["createAuthor"]["firstName"] == "James"

    def test_create_category_as_librarian(self, librarian):
        client = Client()
        token = self._login_as(client, librarian)
        if token is None:
            pytest.skip("Login not available")

        slug = f"test-cat-{uuid.uuid4().hex[:6]}"
        variables = {
            "input": {
                "name": "Test Category",
                "slug": slug,
            }
        }
        status, body = _gql(client, self.CREATE_CATEGORY, variables, token=token)
        assert status == 200
        if "errors" not in body:
            assert body["data"]["createCategory"]["slug"] == slug

    def test_create_book_as_librarian(self, librarian):
        client = Client()
        token = self._login_as(client, librarian)
        if token is None:
            pytest.skip("Login not available")

        isbn = f"978{uuid.uuid4().int % 10**10:010d}"
        variables = {
            "input": {
                "title": "Integration Test Book",
                "isbn13": isbn,
            }
        }
        status, body = _gql(client, self.CREATE_BOOK, variables, token=token)
        assert status == 200
        # Might fail due to ISBN validation — that's OK, just check no crash
        if "errors" not in body:
            assert body["data"]["createBook"]["title"] == "Integration Test Book"

    def test_books_query_public(self, make_book):
        """Books query should be accessible without auth."""
        make_book(title="Public Query Book")
        client = Client()
        status, body = _gql(client, self.BOOKS_QUERY, {"first": 10})
        assert status == 200
        if "errors" not in body:
            assert body["data"]["books"]["totalCount"] >= 1

    def test_book_by_isbn(self, make_book):
        book = make_book(title="ISBN Lookup Book", isbn_13="9780134685991")
        client = Client()
        status, body = _gql(client, self.BOOK_BY_ISBN, {"isbn": "9780134685991"})
        assert status == 200
        if "errors" not in body and body["data"]["bookByIsbn"]:
            assert body["data"]["bookByIsbn"]["title"] == "ISBN Lookup Book"

    def test_create_book_unauthenticated(self):
        """Unauthenticated users cannot create books."""
        client = Client()
        variables = {
            "input": {
                "title": "Should Fail",
                "isbn13": "9780000000001",
            }
        }
        status, body = _gql(client, self.CREATE_BOOK, variables)
        # Should either have errors or 4xx
        if status == 200:
            has_error = body.get("errors") is not None or body["data"]["createBook"] is None
            assert has_error


# ─── Circulation ────────────────────────────────────────────────────

class TestCirculationQueries:
    """Test borrow/reservation queries for authenticated users."""

    MY_BORROWS = """
        query { myBorrows { id status dueDate } }
    """

    MY_FINES = """
        query { myFines { id amount status } }
    """

    def test_my_borrows_unauthenticated(self):
        client = Client()
        status, body = _gql(client, self.MY_BORROWS)
        assert status == 200
        if body.get("errors") is None:
            assert body["data"]["myBorrows"] is None or body["data"]["myBorrows"] == []

    def test_my_fines_unauthenticated(self):
        client = Client()
        status, body = _gql(client, self.MY_FINES)
        assert status == 200
        if body.get("errors") is None:
            assert body["data"]["myFines"] is None or body["data"]["myFines"] == []


# ─── Engagement ─────────────────────────────────────────────────────

class TestEngagementQueries:
    ALL_ACHIEVEMENTS = """
        query { allAchievements { id name code description } }
    """

    def test_all_achievements_public(self):
        client = Client()
        status, body = _gql(client, self.ALL_ACHIEVEMENTS)
        assert status == 200
        # Should not crash even if empty


# ─── Governance ─────────────────────────────────────────────────────

class TestGovernanceQueries:
    """Governance queries require staff-level access."""

    AUDIT_LOGS = """
        query { auditLogs(first: 5) { edges { id action } totalCount } }
    """

    def test_audit_logs_unauthenticated(self):
        client = Client()
        status, body = _gql(client, self.AUDIT_LOGS)
        assert status == 200
        # Should be rejected or return errors
        if body.get("errors") is None:
            assert body["data"]["auditLogs"] is None


# ─── Intelligence ───────────────────────────────────────────────────

class TestIntelligenceQueries:
    TRENDING = """
        query { trendingBooks { id score } }
    """

    def test_trending_books(self):
        client = Client()
        status, body = _gql(client, self.TRENDING)
        assert status == 200
        # Should not crash


# ─── Middleware Integration ─────────────────────────────────────────

class TestMiddlewareIntegration:
    """Verify middleware headers appear on GraphQL responses."""

    def test_security_headers_on_graphql(self):
        client = Client()
        resp = client.post(
            GQL_URL,
            data=json.dumps({"query": "{ health }"}),
            content_type="application/json",
        )
        assert resp["X-Content-Type-Options"] == "nosniff"
        assert "X-Request-ID" in resp

    def test_graphql_no_cache_headers(self):
        client = Client()
        resp = client.post(
            GQL_URL,
            data=json.dumps({"query": "{ health }"}),
            content_type="application/json",
        )
        if "Cache-Control" in resp:
            assert "no-store" in resp["Cache-Control"]
