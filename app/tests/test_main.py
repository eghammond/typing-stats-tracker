from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..main import app
from ..models import Base
from ..database import get_db
import pytest


client = TestClient(app)

SQLITE_URL = "sqlite:///./test.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# POST /auth/register
def test_register():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200

def test_register_twice():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 400

# POST /auth/login
def test_login_correct():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200

def test_login_incorrect():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "wrongpass"})
    assert response.status_code == 401

# POST /results
def test_result_create():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    response = client.post("/results", json={"wpm":22, "accuracy":97, "duration":15}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_result_create_unauth():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/results", json={"wpm":22, "accuracy":97, "duration":15})
    assert response.status_code == 401

# GET /results
def test_result_fetch():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    response = client.post("/results", json={"wpm":22, "accuracy":97, "duration":15}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    response = client.get("/results", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["wpm"] == 22
    assert data[0]["accuracy"] == 97
    assert data[0]["duration"] == 15
    assert data[0]["user_id"] == 1

def test_result_fetch_no_results():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    response = client.get("/results", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

# GET /results/stats

def test_stats_fetch():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    response = client.post("/results", json={"wpm":22, "accuracy":97, "duration":15}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    response = client.get("/results/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert data["avg_wpm"] == 22
    assert data["best_wpm"] == 22
    assert data["avg_accuracy"] == 97
    assert data["total_tests"] == 1

def test_stats_fetch_no_stats():
    response = client.post("/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "testpass"})
    assert response.status_code == 200
    response = client.post("/auth/login", json = {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    response = client.get("/results/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert data["avg_wpm"] == 0
    assert data['best_wpm'] == 0
    assert data["avg_accuracy"] == 0
    assert data["total_tests"] == 0


