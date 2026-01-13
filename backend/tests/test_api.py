"""
API endpoint tests for the Course Materials RAG System.

Tests cover:
- POST /api/query - Query processing endpoint
- GET /api/courses - Course statistics endpoint
- GET / - Root/health check endpoint
- Error handling scenarios
- Request/response validation
"""
import pytest


class TestQueryEndpoint:
    """Tests for POST /api/query endpoint."""

    def test_query_with_new_session(self, client, mock_rag_system):
        """Test query creates new session when session_id not provided."""
        response = client.post(
            "/api/query",
            json={"query": "What is machine learning?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "session_1"
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_query_with_existing_session(self, client, mock_rag_system):
        """Test query uses provided session_id."""
        response = client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": "existing_session"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing_session"
        mock_rag_system.session_manager.create_session.assert_not_called()

    def test_query_response_structure(self, client):
        """Test query response has correct structure."""
        response = client.post(
            "/api/query",
            json={"query": "What is machine learning?"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # Check sources structure
        for source in data["sources"]:
            assert "title" in source
            assert "link" in source or source.get("link") is None

    def test_query_calls_rag_system(self, client, mock_rag_system):
        """Test query endpoint calls RAG system with correct arguments."""
        query_text = "Explain neural networks"

        client.post("/api/query", json={"query": query_text})

        mock_rag_system.query.assert_called_once()
        call_args = mock_rag_system.query.call_args
        assert query_text in call_args[0][0]  # Query is in the prompt

    def test_query_missing_query_field(self, client):
        """Test query fails when query field is missing."""
        response = client.post("/api/query", json={})

        assert response.status_code == 422  # Validation error

    def test_query_empty_query(self, client):
        """Test query with empty string."""
        response = client.post("/api/query", json={"query": ""})

        # Empty string is technically valid, endpoint should handle
        assert response.status_code == 200

    def test_query_error_handling(self, error_client):
        """Test query returns 500 when RAG system fails."""
        response = error_client.post(
            "/api/query",
            json={"query": "This will fail"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Database connection failed" in data["detail"]


class TestCoursesEndpoint:
    """Tests for GET /api/courses endpoint."""

    def test_get_courses_success(self, client, sample_course_titles):
        """Test successful courses retrieval."""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3

    def test_get_courses_response_structure(self, client):
        """Test courses response has correct structure."""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        for title in data["course_titles"]:
            assert isinstance(title, str)

    def test_get_courses_calls_analytics(self, client, mock_rag_system):
        """Test courses endpoint calls get_course_analytics."""
        client.get("/api/courses")

        mock_rag_system.get_course_analytics.assert_called_once()

    def test_get_courses_error_handling(self, error_client):
        """Test courses returns 500 when analytics fails."""
        response = error_client.get("/api/courses")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Analytics unavailable" in data["detail"]


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_returns_health_check(self, client):
        """Test root endpoint returns health check response."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_root_includes_message(self, client):
        """Test root endpoint includes descriptive message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "RAG System" in data["message"]


class TestRequestValidation:
    """Tests for request validation and edge cases."""

    def test_query_with_special_characters(self, client):
        """Test query handles special characters."""
        response = client.post(
            "/api/query",
            json={"query": "What's the O(n²) complexity?"},
        )

        assert response.status_code == 200

    def test_query_with_unicode(self, client):
        """Test query handles unicode characters."""
        response = client.post(
            "/api/query",
            json={"query": "Explain λ calculus and π in ML"},
        )

        assert response.status_code == 200

    def test_query_with_long_text(self, client):
        """Test query handles long query text."""
        long_query = "What is machine learning? " * 100
        response = client.post(
            "/api/query",
            json={"query": long_query},
        )

        assert response.status_code == 200

    def test_invalid_json_body(self, client):
        """Test endpoint rejects invalid JSON."""
        response = client.post(
            "/api/query",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_wrong_http_method_query(self, client):
        """Test query endpoint rejects GET method."""
        response = client.get("/api/query")

        assert response.status_code == 405  # Method Not Allowed

    def test_wrong_http_method_courses(self, client):
        """Test courses endpoint rejects POST method."""
        response = client.post("/api/courses", json={})

        assert response.status_code == 405  # Method Not Allowed


class TestSessionManagement:
    """Tests for session handling in queries."""

    def test_session_creation_on_first_query(self, client, mock_rag_system):
        """Test new session is created for first query without session_id."""
        response = client.post(
            "/api/query",
            json={"query": "First question"},
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "session_1"
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_session_reuse_with_existing_id(self, client, mock_rag_system):
        """Test existing session is reused when session_id provided."""
        session_id = "my_existing_session"
        response = client.post(
            "/api/query",
            json={"query": "Follow-up question", "session_id": session_id},
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == session_id
        # Should not create new session
        mock_rag_system.session_manager.create_session.assert_not_called()

    def test_null_session_id_creates_new_session(self, client, mock_rag_system):
        """Test null session_id triggers new session creation."""
        response = client.post(
            "/api/query",
            json={"query": "Question", "session_id": None},
        )

        assert response.status_code == 200
        mock_rag_system.session_manager.create_session.assert_called_once()
