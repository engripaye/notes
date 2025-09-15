import pytest
from fastapi.testclient import TestClient
from main import app, Base, engine, get_db, session_data
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override DB
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session_data.clear()
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_and_login():
    # Register user
    response = client.post("/api/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "alice"

    # Login user
    response = client.post("/api/login", json={
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

def test_create_and_get_notes():
    # Register + Login
    client.post("/api/register", json={"username": "bob", "email": "bob@example.com", "password": "mypassword"})
    client.post("/api/login", json={"email": "bob@example.com", "password": "mypassword"})

    # Create note
    response = client.post("/api/notes", json={"title": "Test Note", "content": "This is a note"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Note"

    # Fetch notes
    response = client.get("/api/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Test Note"
