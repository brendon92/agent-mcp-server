import pytest
from fastapi.testclient import TestClient
from gateway.src.server import app, registered_servers

client = TestClient(app)

def test_register_server():
    """Test server registration"""
    response = client.post("/api/gateway/register", json={
        "name": "test-server",
        "url": "http://localhost:8001",
        "token": "test-token"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "registered"
    assert "test-server" in registered_servers

def test_list_servers():
    """Test listing registered servers"""
    # Ensure we have a server registered
    client.post("/api/gateway/register", json={
        "name": "test-server-2",
        "url": "http://localhost:8002"
    })
    
    response = client.get("/api/gateway/servers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["servers"]) >= 2
    assert any(s["name"] == "test-server-2" for s in data["servers"])
