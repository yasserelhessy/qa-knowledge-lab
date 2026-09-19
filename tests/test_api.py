import pytest
from jsonschema import Draft202012Validator
from app.main import create_app
from fastapi.testclient import TestClient


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "mode": "demo", "documents": 6}


def test_answer_matches_pinned_contract(client):
    import json
    from pathlib import Path
    response = client.post("/api/ask", json={"question": "What are release gates?"})
    assert response.status_code == 200
    schema = json.loads((Path(__file__).parent / "answer.schema.json").read_text())
    Draft202012Validator(schema).validate(response.json())
    assert response.json()["sources"][0]["id"] == "release"


@pytest.mark.parametrize("payload", [{}, {"question": "  "}, {"question": "a"},
    {"question": "x" * 501}, {"question": 123}, {"question": "release gates", "mode": "openai"}])
def test_invalid_payload(client, payload):
    assert client.post("/api/ask", json=payload).status_code == 422


def test_bad_json(client):
    assert client.post("/api/ask", content="{", headers={"Content-Type": "application/json"}).status_code == 422


def test_refusal(client):
    body = client.post("/api/ask", json={"question": "Who is the CEO?"}).json()
    assert body["status"] == "refused"
    assert body["sources"] == []


def test_provider_failure_is_sanitized():
    class Broken:
        mode = "openai"
        documents = []
        def invoke(self, question):
            raise RuntimeError("secret-provider-token")
    response = TestClient(create_app(Broken())).post("/api/ask", json={"question": "release gates"})
    assert response.status_code == 502
    assert "secret" not in response.text


def test_static_application(client):
    assert "QA Knowledge Lab" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
