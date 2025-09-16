from fastapi import FastAPI, Query, Request, Form, UploadFile, File, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os
import secrets
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
async def my_notes(
        request: Request,
        updated: str = Query(None),
        db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.username == username).first()
    notes = db.query(Note).filter(Note.user_id == user.id).all()

    msg = "✅ Note successfully updated!" if updated else None

    return templates.TemplateResponse(
        "mynotes.html",
        {"request": request, "username": username, "notes": notes, "msg": msg}
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


# EDIT NOTE SUBMIT (POST)
@app.post("/editnote/{note_id}")
async def update_note(
        request: Request,
        note_id: int,
        title: str = Form(...),
        content: str = Form(...),
        db: Session = Depends(get_db)
):
    username = session_data.get("user")
    if not username:
        return RedirectResponse("/login", status_code=303)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # update values
    note.title = title
    note.content = content
    db.commit()
    db.refresh(note)

    # redirect with ?updated=1
    return RedirectResponse("/mynotes?updated=1", status_code=303)


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


# ========================
# JSON API ENDPOINTS
# ========================

# REGISTER
@app.post("/api/register")
async def api_register_user(
        username: str = Body(...),
        email: str = Body(...),
        password: str = Body(...),
        db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")

    user = User(username=username, email=email, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "username": user.username, "email": user.email}


# LOGIN
@app.post("/api/login")
async def api_login(
        email: str = Body(...),
        password: str = Body(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_data["user"] = user.username
    return {"message": "Login successful", "username": user.username}


# CREATE NOTE
@app.post("/api/notes")
async def api_upload_note(
        title: str = Body(...),
        content: Optional[str] = Body(None),
        db: Session = Depends(get_db)
):
    username = session_data.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.username == username).first()
    note = Note(title=title, content=content, user_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)

    return {"id": note.id, "title": note.title, "content": note.content}


# GET ALL NOTES
@app.get("/api/notes")
async def api_get_notes(db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.username == username).first()
    notes = db.query(Note).filter(Note.user_id == user.id).all()

    return [
        {"id": n.id, "title": n.title, "content": n.content, "filename": n.filename}
        for n in notes
    ]


# GET SINGLE NOTE
@app.get("/api/notes/{note_id}")
async def api_get_note(note_id: int, db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return {"id": note.id, "title": note.title, "content": note.content, "filename": note.filename}


# UPDATE NOTE
@app.put("/api/notes/{note_id}")
async def api_update_note(
        note_id: int,
        title: str = Body(...),
        content: str = Body(...),
        db: Session = Depends(get_db)
):
    username = session_data.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = title
    note.content = content
    db.commit()
    db.refresh(note)

    return {"id": note.id, "title": note.title, "content": note.content}


# DELETE NOTE
@app.delete("/api/notes/{note_id}")
async def api_delete_note(note_id: int, db: Session = Depends(get_db)):
    username = session_data.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()
    return {"message": "Note deleted successfully"}


# FORGOT PASSWORD PAGE
@app.get("/forgot-password", response_class=HTMLResponse)
async def forget_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.post("/forgot-password")
async def forget_password(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return templates.TemplateResponse("forgot_password.html", {"request": request, "msg": "❌ Email not found."})

    # generate reset token
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    db.commit()

    # in real life: send email
    reset_link = f"/reset-password/{token}"
    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "msg": f"✅ Reset link generated! Visit {reset_link} "
    })


# RESET PASSWORD PAGE
@app.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


@app.post("/reset-password/{token}")
async def reset_password(request: Request, token: str, password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail= "Invalid or expired token")

    if len(password) < 6:
        return templates.TemplateResponse("reset_password.html", {
            "request": request, "token": token, "msg": "❌ Password must be at least 6 characters"
        })

    #update password
    user.password = password
    user.reset_token = None
    db.commit()

    return templates.TemplateResponse("login.html", {"request": request, "msg": "✅ Password reset successful! Please log in."})
