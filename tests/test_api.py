from fastapi.testclient import TestClient
from app.main import app, sessions, voice

client = TestClient(app)

def setup_function():
    sessions.clear()

def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["stt"] == "faster-whisper"

def test_message_and_history(monkeypatch):
    monkeypatch.setattr(voice, "reply", lambda text, history: "Local test reply")
    response = client.post("/sessions/demo/messages", json={"text": "Hello"})
    assert response.status_code == 200
    assert response.json()["reply"] == "Local test reply"
    assert response.json()["message_count"] == 2
    assert len(client.get("/sessions/demo").json()["messages"]) == 2

def test_unknown_session():
    assert client.get("/sessions/missing").status_code == 404

def test_empty_message_rejected():
    assert client.post("/sessions/demo/messages", json={"text": ""}).status_code == 422
