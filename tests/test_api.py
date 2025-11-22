from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "VisiLens API",
        "version": "0.1.0",
        "websocket": "/ws"
    }

