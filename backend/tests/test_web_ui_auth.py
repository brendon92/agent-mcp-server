import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add project root to path so we can import frontend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.src.web_ui import app, AUTH_TOKEN

client = TestClient(app)

def test_health_check_unauthorized():
    """Test that health check requires auth"""
    response = client.get("/api/health")
    assert response.status_code == 401

def test_health_check_authorized():
    """Test that health check works with token"""
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = client.get("/api/health", headers=headers)
    assert response.status_code == 200
    assert "status" in response.json()

def test_login_success():
    """Test login with correct token"""
    response = client.post("/api/login", json={"token": AUTH_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == AUTH_TOKEN
    assert data["token_type"] == "bearer"

def test_login_failure():
    """Test login with incorrect token"""
    response = client.post("/api/login", json={"token": "wrong_token"})
    assert response.status_code == 401
