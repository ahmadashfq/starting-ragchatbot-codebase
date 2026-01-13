"""
Shared test fixtures for RAG system API tests.

This module provides fixtures for mocking backend components and creating
a test FastAPI application without static file dependencies.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from typing import List

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Optional

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# --- Pydantic Models (inline to avoid import issues) ---

class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class Source(BaseModel):
    """Model for a source citation with optional link"""
    title: str
    link: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[Source]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


# --- Mock Data Fixtures ---

@pytest.fixture
def sample_course_titles():
    """Sample course titles for testing."""
    return [
        "Introduction to Machine Learning",
        "Advanced Python Programming",
        "Data Structures and Algorithms",
    ]


@pytest.fixture
def sample_sources():
    """Sample source citations for testing."""
    return [
        Source(title="Introduction to Machine Learning", link="https://example.com/ml"),
        Source(title="Advanced Python Programming", link="https://example.com/python"),
    ]


@pytest.fixture
def sample_query_response():
    """Sample query response data."""
    return {
        "answer": "Machine learning is a subset of artificial intelligence...",
        "sources": [
            {"title": "Introduction to Machine Learning", "link": "https://example.com/ml"}
        ],
        "session_id": "session_1",
    }


# --- Mock Component Fixtures ---

@pytest.fixture
def mock_session_manager():
    """Create a mock SessionManager."""
    manager = MagicMock()
    manager.create_session.return_value = "session_1"
    manager.get_conversation_history.return_value = None
    manager.add_exchange = MagicMock()
    return manager


@pytest.fixture
def mock_rag_system(mock_session_manager, sample_sources):
    """Create a mock RAGSystem with configured responses."""
    rag_system = MagicMock()
    rag_system.session_manager = mock_session_manager
    rag_system.query.return_value = (
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
        sample_sources,
    )
    rag_system.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": [
            "Introduction to Machine Learning",
            "Advanced Python Programming",
            "Data Structures and Algorithms",
        ],
    }
    return rag_system


# --- Test App Fixtures ---

@pytest.fixture
def test_app(mock_rag_system):
    """
    Create a test FastAPI app with API endpoints defined inline.

    This avoids the static file mounting issue from the production app.
    """
    app = FastAPI(title="Course Materials RAG System - Test")

    # Store mock in app state for access in endpoints
    app.state.rag_system = mock_rag_system

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources."""
        try:
            rag_system = app.state.rag_system
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()

            answer, sources = rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics."""
        try:
            rag_system = app.state.rag_system
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        """Health check endpoint for testing."""
        return {"status": "ok", "message": "Course Materials RAG System"}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_app)


# --- Error Simulation Fixtures ---

@pytest.fixture
def mock_rag_system_with_error():
    """Create a mock RAGSystem that raises exceptions."""
    rag_system = MagicMock()
    rag_system.session_manager = MagicMock()
    rag_system.session_manager.create_session.return_value = "session_1"
    rag_system.query.side_effect = Exception("Database connection failed")
    rag_system.get_course_analytics.side_effect = Exception("Analytics unavailable")
    return rag_system


@pytest.fixture
def error_client(mock_rag_system_with_error):
    """Create a test client with error-throwing RAG system."""
    app = FastAPI(title="Course Materials RAG System - Error Test")
    app.state.rag_system = mock_rag_system_with_error

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            rag_system = app.state.rag_system
            session_id = request.session_id or rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = app.state.rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return TestClient(app)
