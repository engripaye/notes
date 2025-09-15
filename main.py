from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os

from database import Base, engine, SessionLocal
from models import User, Note

# CREATE TABLES
Base.metadata.create_all(bind=engine)

app = FastAPI()

# uploads folder
os.makedirs("uploads", exist_ok=True)

# STATIC + TEMPLATES
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
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
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    # check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "msg": "⚠️ Email already registered try login in."})

    # check password length
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "msg": "❌ Password must be at least 6 characters"}
        )

    # create new user
    user = User(username=username, email=email, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)

    # success message
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "msg": "✅ Registration successful! Please log in."}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


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

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "msg": "❌ Invalid login, please try again."})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, success: str = None):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/", status_code=302)

    msg = "✅ Note successfully uploaded!" if success else None
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": username, "msg": msg})


@app.post("/notes")
async def upload_note(
        title: str = Form(...),
        content: str = Form(None),  # optional text content
        file: Optional[UploadFile] = File(None),  # Optional file
        db: Session = Depends(get_db)
):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/", status_code=302)

    user = db.query(User).filter(User.username == username).first()

    filename = None
    if file and file.filename:  # check if a file is uploaded
        os.makedirs("uploads", exist_ok=True)
        file_location = os.path.join("uploads", file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        filename = file.filename

    note = Note(
        title=title,
        content=content,
        filename=file.filename,
        user_id=user.id)

    db.add(note)
    db.commit()

    # ✅ redirect with a query param
    return RedirectResponse("/dashboard?success=1", status_code=302)


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


# MY NOTES
@app.get("/mynotes", response_class=HTMLResponse)
async def my_notes(request: Request, db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.username == username).first()
    notes = db.query(Note).filter(Note.user_id == user.id).all()

    return templates.TemplateResponse(
        "mynotes.html",
        {"request": request, "username": username, "notes": notes}
    )


@app.get("/viewfile/{note_id}", response_class=HTMLResponse)
async def view_file(request: Request, note_id: int, db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    # fetch note
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return templates.TemplateResponse(
        "viewfile.html",
        {"request": request, "note": note}
    )


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.get("/editnote/{note_id}", response_class=HTMLResponse)
async def edit_note_page(request: Request, note_id: int, db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return templates.TemplateResponse("editnote.html", {"request": request, "note": note})


@app.get("/editnote/{note_id}")
async def update_note(
        note_id: int,
        title: str = Form(...),
        content: str = Form(None),
        db: Session = Depends(get_db)
):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # update fields
    note.title = title
    note.content = content
    db.commit()

    return RedirectResponse("/mynotes", status_code=303)


@app.get("/deletenote/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()

    return RedirectResponse("/mynotes", status_code=303)
