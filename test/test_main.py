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



# ------------------------
# USER TESTS
# ------------------------

def test_register_user():
    response = client.post("/api/register", json={
        "username": "testuser",
        "email": "test@gmail.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@gmail.com"


def test_register_deplicate_email():
    client.post("/api/register", json={
        "username": "bob",
        "email": "@bob@gmail.com",
        "password": "secret123"
    })
    response = client.post("/api/register", json={
        "username": "bob2",
        "email": "@bob@gmail.com",
        "password": "secret123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_user():
    client.post("/api/register", json={
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "secret123"
    })
    res = client.post("/api/login", json={
        "email": "charlie@example.com",
        "password": "secret123"
    })
    assert res.status_code == 200
    assert res.json()["username"] == "charlie"


def test_login_invalid_credentials():
    client.post("/api/register", json={
        "username": "david",
        "email": "david@example.com",
        "password": "secret123"
    })
    res = client.post("/api/login", json={
        "email": "david@example.com",
        "password": "wrongpass"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


# ------------------------
# NOTES TESTS
# ------------------------

def test_create_note():
    client.post("/api/register", json={
        "username": "eve",
        "email": "eve@example.com",
        "password": "secret123"
    })
    client.post("/api/login", json={
        "email": "eve@example.com",
        "password": "secret123"
    })
    res = client.post("/api/notes", json={"title": "Test Note", "content": "Some content"})
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Note"
    assert data["content"] == "Some content"


def test_get_all_notes():
    client.post("/api/register", json={
        "username": "frank",
        "email": "frank@example.com",
        "password": "secret123"
    })
    client.post("/api/login", json={
        "email": "frank@example.com",
        "password": "secret123"
    })
    client.post("/api/notes", json={"title": "Note 1", "content": "Content 1"})
    client.post("/api/notes", json={"title": "Note 2", "content": "Content 2"})
    res = client.get("/api/notes")
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 2


def test_get_single_note():
    client.post("/api/register", json={
        "username": "george",
        "email": "george@example.com",
        "password": "secret123"
    })
    client.post("/api/login", json={
        "email": "george@example.com",
        "password": "secret123"
    })
    res = client.post("/api/notes", json={"title": "My Note", "content": "Test"})
    note_id = res.json()["id"]
    res = client.get(f"/api/notes/{note_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "My Note"


def test_update_note():
    client.post("/api/register", json={
        "username": "harry",
        "email": "harry@example.com",
        "password": "secret123"
    })
    client.post("/api/login", json={
        "email": "harry@example.com",
        "password": "secret123"
    })
    res = client.post("/api/notes", json={"title": "Old Title", "content": "Old content"})
    note_id = res.json()["id"]

    res = client.put(f"/api/notes/{note_id}", json={"title": "New Title", "content": "New content"})
    assert res.status_code == 200
    assert res.json()["title"] == "New Title"


def test_delete_note():
    client.post("/api/register", json={
        "username": "ian",
        "email": "ian@example.com",
        "password": "secret123"
    })
    client.post("/api/login", json={
        "email": "ian@example.com",
        "password": "secret123"
    })
    res = client.post("/api/notes", json={"title": "Delete Me", "content": "Trash"})
    note_id = res.json()["id"]

    res = client.delete(f"/api/notes/{note_id}")
    assert res.status_code == 200
    assert res.json()["message"] == "Note deleted successfully"

    # confirm deletion
    res = client.get(f"/api/notes/{note_id}")
    assert res.status_code == 404

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

