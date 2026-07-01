"""Integration-test fixtures for MiccoRAG-v3 backend.

These tests hit a RUNNING backend (default http://127.0.0.1:8001) over HTTP using
the dev-skip auth bypass. Zero external deps (stdlib urllib) so they run in any venv.
They SKIP (not fail) when the backend/workspaces are unavailable, so CI without a
live VPS stays green. Enable in harness via: RUN_INTEGRATION=1 harness/run.sh be

Grounded in the real stack: LLM=Gemini, vector store=ChromaDB, RAG query endpoint
`POST /api/v1/rag/query/{workspace_id}` returns retrieval context (total_chunks,
chunks, context, citations) — NOT a generated answer.
"""
import json
import os
import urllib.error
import urllib.request

import pytest

BASE_URL = os.environ.get("HARNESS_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
AUTH = {"Authorization": "Bearer dev-skip"}


def _req(method, path, body=None, timeout=90):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", **AUTH}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw
    except Exception as e:  # connection refused, timeout, ...
        return 0, str(e)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: end-to-end test against a running backend"
    )


@pytest.fixture(scope="session")
def api():
    return _req


@pytest.fixture(scope="session")
def _backend_up():
    status, _ = _req("GET", "/health", timeout=6)
    if status != 200:
        pytest.skip(f"backend not reachable at {BASE_URL} (status={status})")
    return True


@pytest.fixture(scope="session")
def workspace_id(_backend_up):
    status, body = _req("GET", "/api/v1/workspaces", timeout=15)
    if status != 200 or not isinstance(body, list) or not body:
        pytest.skip(f"no workspaces available (status={status})")
    return body[0]["id"]
