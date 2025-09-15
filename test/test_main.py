import os
import shutil
import pytest
from fastapi.testclient import TestClient
from main import app, get_db, Base, engine
from sqlalchemy import sessionmaker

# set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# override dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    # fresh DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    os.makedirs("uploads", exist_ok=True)
    yield
    # cleanup
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")


# TEST PING
def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# TEST REGISTER USER
def test_register_user():
    response = client.post("/register", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    assert "Registration successful" in response.text

