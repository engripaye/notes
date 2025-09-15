import os
import shutil
import pytest
from fastapi.testclient import TestClient
from main import app, get_db, Base, engine
from sqlalchemy.orm import sessionmaker
from fastapi.responses import JSONResponse

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


# 🔹 Patch template rendering so tests return JSON only
def fake_template_response(name, context):
    # filter out non-json objects
    safe_context = {
        key: str(value) if not isinstance(value, (str, int, float, list, dict, bool, type(None)))
        else value
        for key, value in context.items()
    }
    # add templates
    safe_context["template"] = name
    return JSONResponse(content=safe_context)


import main

main.templates.TemplateResponse = fake_template_response

# Dependency override
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
        "email": "testuser@gmail.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "Registration successful" in data["msg"]
    assert data["template"] == "login.html"