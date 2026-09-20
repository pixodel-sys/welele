import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_security_headers_present_on_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "SAMEORIGIN"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"

def test_security_headers_present_on_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "SAMEORIGIN"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"
    # Verify response body remains completely intact
    data = response.json()
    assert data.get("status") == "healthy"

def test_security_headers_present_on_api_experience_page(client):
    response = client.get("/api/experience/page/home")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "SAMEORIGIN"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"
    data = response.json()
    assert data.get("page_id") == "home"

def test_security_headers_present_on_series_feed(client):
    response = client.get("/api/v1/series/")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "SAMEORIGIN"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"
    data = response.json()
    assert "series" in data
    assert isinstance(data["series"], list)
    assert len(data["series"]) >= 1
