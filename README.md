# 📒 Notes API with File Uploads

A simple but professional **FastAPI** project where users can:

* Register and log in with **email and password** (stored in SQLite).
* Upload **images/PDFs with notes**.
* View a personalized dashboard:

  > *“Hello Tunde 👋 Welcome to Notes API”*

This project demonstrates **file handling, user authentication, SQLite integration, and HTML templating with FastAPI**.

---

## 📂 Project Structure

```
notes_api_project/
│── main.py                # FastAPI app entry point
│── database.py            # Database setup (SQLite + SQLAlchemy)
│── models.py              # ORM models (User, Note)
│── static/                # CSS styling
│   └── style.css
│── templates/             # HTML templates (Jinja2)
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│── uploads/               # Uploaded files (images, PDFs)
│── requirements.txt       # Project dependencies
│── notes.db               # SQLite database (auto-generated)
```

---

## ⚡ Features

✅ User **registration** (username, email, password)
✅ User **login** (session-based, no tokens)
✅ Personalized **dashboard greeting**
✅ Upload **notes with file attachments (PDF/Image)**
✅ Store all data in **SQLite database**
✅ Simple **HTML pages styled with CSS**

---

## 🛠️ Tech Stack

* **FastAPI** – Web framework
* **SQLite + SQLAlchemy** – Database & ORM
* **Jinja2** – HTML templating
* **python-multipart** – File uploads
* **Uvicorn** – ASGI server

---

## 🚀 Getting Started

### 1️⃣ Clone the repo

```bash
git clone https://github.com/your-username/notes-api-upload.git
cd notes-api-upload
```

### 2️⃣ Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the app

```bash
uvicorn main:app --reload
```

---

## 🌐 Usage

1. Open your browser → `http://127.0.0.1:8000/register` → Create account
2. Login at → `http://127.0.0.1:8000/`
3. Access dashboard → Upload notes & files
4. Files are stored in the `uploads/` directory

---

## 📸 Screenshots

🔹 **Register Page**
🔹 **Login Page**
🔹 **Dashboard with Greeting & Upload Form**

*(You can add screenshots here for GitHub presentation)*

---

## 📦 Requirements

See [`requirements.txt`](requirements.txt):

```txt
fastapi==0.115.0
uvicorn==0.30.6
SQLAlchemy==2.0.34
jinja2==3.1.4
python-multipart==0.0.9
```

Install all with:

```bash
pip install -r requirements.txt
```

---

## 🔒 Security Note

Currently, passwords are stored in plain text (for learning purposes).
👉 For production, use **password hashing** with `passlib[bcrypt]`.

---

## 🤝 Contributing

Pull requests are welcome! Feel free to fork this repo and improve the project.

---

## 📜 License

This project is licensed under the MIT License.

---

