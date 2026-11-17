from fastapi.testclient import TestClient
from app.main import app, calls

client = TestClient(app)

def setup_function():
    calls.clear()

def test_health():
    result = client.get("/health").json()
    assert result["status"] == "ok"
    assert result["telephony"] == "Asterisk AudioSocket"

def test_outbound_requires_consent():
    response = client.post("/calls/outbound", json={
        "phone_number": "1001", "lead_name": "Demo", "consent_confirmed": False
    })
    assert response.status_code == 400

def test_outbound_validates_number():
    response = client.post("/calls/outbound", json={
        "phone_number": "bad-number", "lead_name": "Demo", "consent_confirmed": True
    })
    assert response.status_code == 422
