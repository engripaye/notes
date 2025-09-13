from fastapi import FastAPI, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import shutil
import os

from database import Base, engine, SessionLocal
from models import User, Note

# CREATE TABLES
Base.metadata.create_all(bind=engine)

app = FastAPI()

# STATIC + TEMPLATES
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# DEPENDENCY TO GET DB SESSION
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FAKE SESSION, SIMPLE FOR DEMO (NO JWT)
session_data = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register_user(
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = User(username=username, email=email, password=password)
    db.add(user)
    db.commit()
    return RedirectResponse("/", status_code=302)


@app.post("/login")
async def login_user(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    if user:
        session_data["user"] = user.username
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "msg": "Invalid login, try again"})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username})


@app.post("/notes")
async def upload_note(
        title: str = Form(...),
        content: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/", status_code=302)

    user = db.query(User).filter(User.username == username).first()
    file_location = f"uploads/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    note = Note(title=title, content=content, filename=file.filename, user_id=user.id)
    db.add(note)
    db.commit()

    return RedirectResponse("/dashboard", status_code=302)


@app.get("/notes")
async def get_notes(db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/", status_code=302)

    user = db.query(User).filter(User.username == username).first()
    notes = db.query(Note).filter(Note.user_id == user.id).all()

    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "filename": note.filename
        }

        for note in notes
    ]

