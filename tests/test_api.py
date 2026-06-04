"""
API Tests
=======
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    """Test health endpoint."""
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_check_version():
    """Test health response has version."""
    response = client.get("/api/v2/health")
    assert "version" in response.json()

def test_health_check_timestamp():
    """Test health response has timestamp."""
    response = client.get("/api/v2/health")
    assert "timestamp" in response.json()

def test_unauthorized_access():
    """Test measurement endpoint without auth."""
    response = client.post("/api/v2/measurements/extract")
    assert response.status_code == 401

def test_invalid_api_key():
    """Test with invalid API key."""
    response = client.post(
        "/api/v2/measurements/extract",
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 403

def test_subscription_status_no_key():
    """Test subscription status without auth."""
    response = client.get("/api/v2/subscriptions/status")
    assert response.status_code == 401
