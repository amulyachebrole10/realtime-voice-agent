from fastapi.testclient import TestClient
from app.main import app,sessions
client=TestClient(app)
def setup_function(): sessions.clear()
def test_health(): assert client.get("/health").json()=={"status":"ok"}
def test_message_and_history():
    r=client.post("/sessions/demo/messages",json={"text":"Hello"})
    assert r.status_code==200 and r.json()["message_count"]==2
    assert "You said: Hello" in r.json()["reply"]
    assert len(client.get("/sessions/demo").json()["messages"])==2
def test_unknown_session(): assert client.get("/sessions/missing").status_code==404
