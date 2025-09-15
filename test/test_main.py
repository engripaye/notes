import os
import shutil
import pytest
import main
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
    return JSONResponse(content=context)


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
