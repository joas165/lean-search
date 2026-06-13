"""
Lightweight tests for the FastAPI endpoint functions.

Run from the repository root with:
    python tests/test_api.py
"""

from pathlib import Path
import sys
import types

# Resolve the project root and locate the python/ directory where api.py lives
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = PROJECT_ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


def install_fake_search():
    fake_search = types.ModuleType("search")

    def search(query, top_k=5):
        if query == "explode":
            raise RuntimeError("mock search failure")
        return [("Nat.add_comm", "forall a b : Nat, a + b = b + a")][:top_k]

    fake_search.search = search
    sys.modules["search"] = fake_search


# Install mock before importing api to avoid loading heavy transformers/FAISS models
install_fake_search()

import api  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from starlette.requests import Request  # noqa: E402


def test_query_returns_results():
    response = api.query(q="commutativity of addition", k=1)

    assert response["query"] == "commutativity of addition"
    assert response["results"] == [
        {"name": "Nat.add_comm", "type": "forall a b : Nat, a + b = b + a"}
    ]


def test_query_rejects_empty_query():
    try:
        api.query(q="   ", k=1)
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "cannot be empty" in exc.detail
    else:
        raise AssertionError("Expected HTTPException for empty query")


def test_query_rejects_invalid_k():
    for value in (0, 101):
        try:
            api.query(q="addition", k=value)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "between 1 and 100" in exc.detail
        else:
            raise AssertionError(f"Expected HTTPException for k={value}")


def test_query_wraps_search_errors():
    try:
        api.query(q="explode", k=1)
    except HTTPException as exc:
        assert exc.status_code == 500
        assert "mock search failure" in exc.detail
    else:
        raise AssertionError("Expected HTTPException for search failure")


def test_api_info_matches_current_routes():
    response = api.api_info()

    assert response["message"] == "Lean RAG API v1.0.0"
    assert response["usage"] == "GET /query/?q=<query>&k=<num_results>"
    assert response["example"] == "GET /query/?q=continuous+and+differentiable+functions+on+real+vector+spaces&k=5"


def test_root_renders_search_page_context():
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

    response = api.root(request=request, q="addition", k=1)

    assert response.template.name == "index.html"
    assert response.context["query"] == "addition"
    assert response.context["k"] == 1
    assert response.context["searched"] is True
    assert response.context["results"] == [
        {"name": "Nat.add_comm", "type": "forall a b : Nat, a + b = b + a"}
    ]


def run_all():
    tests = [
        test_query_returns_results,
        test_query_rejects_empty_query,
        test_query_rejects_invalid_k,
        test_query_wraps_search_errors,
        test_api_info_matches_current_routes,
        test_root_renders_search_page_context,
    ]

    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    try:
        run_all()
    except Exception as exc:
        print(f"FAIL {exc}")
        sys.exit(1)