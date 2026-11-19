import json
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from uuid import uuid4

import os

from flask_login import (
    LoginManager, UserMixin, current_user, login_required, login_user, logout_user
)

from flask_wtf.csrf import CSRFProtect

from werkzeug.security import check_password_hash, generate_password_hash




from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["POSTITS_SECRET_KEY"]

csrf=CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"



MAX_RESUME_BYTES = 16 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = 17 * 1024 * 1024

database = Path(app.instance_path) / "demo.sqlite3"

FORM_FIELDS = (
    "name", "email", "phone", "github",
    "motivation", "experience", "start_date", "end_date",
)


def connect():
    database.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL
        )
    """)

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")


    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            github TEXT NOT NULL,
            resume_filename TEXT,
            resume_pdf BLOB
        )
    """)
    return conn


@app.route("/demo/apply", methods=["GET", "POST"])
def apply():
    if request.method == "GET":
        return render_template("apply.html", values={})

    values = {
        key: request.form.get(key, "").strip()
        for key in FORM_FIELDS
    }

    def invalid(message):
        return render_template("apply.html", values=values, error=message), 400

    if not all(values[key] for key in ("name", "email", "phone", "motivation")):
        return invalid("Complete the name, email, phone, and motivation fields.")

    dates = {}
    for key in ("start_date", "end_date"):
        if values[key]:
            try:
                parsed = date.fromisoformat(values[key])
                if parsed.isoformat() != values[key]:
                    raise ValueError
                dates[key] = parsed
            except ValueError:
                label = key.replace("_", " ").capitalize()
                return invalid(f"{label} must be a valid date in YYYY-MM-DD format.")

    if len(dates) == 2 and dates["end_date"] < dates["start_date"]:
        return invalid("End date must be on or after the start date.")

    resume = request.files.get("resume")
    if resume is None or not resume.filename:
        return invalid("Attach a résumé PDF.")

    header = resume.stream.read(5)
    if header != b"%PDF-":
        return invalid("The attachment must be a PDF.")

    size = len(header) + len(resume.stream.read(MAX_RESUME_BYTES - len(header) + 1))
    if size > MAX_RESUME_BYTES:
        return invalid("The attachment must be 16 MiB or smaller.")

    payload = {
        **values,
        "resume_filename": resume.filename,
        "resume_bytes": size,
    }
    receipt_id = uuid4().hex

    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO receipts (id, payload) VALUES (?, ?)",
            (receipt_id, json.dumps(payload)),
        )

    return redirect(url_for("receipt", receipt_id=receipt_id), code=303)


@app.get("/demo/receipt/<receipt_id>")
def receipt(receipt_id):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT payload FROM receipts WHERE id = ?",
            (receipt_id,),
        ).fetchone()

    if row is None:
        abort(404)

    return render_template(
        "receipt.html",
        receipt_id=receipt_id,
        values=json.loads(row[0]),
    )

class User(UserMixin):

    def __init__(self, row):
        self.id = row["id"]
        self.email = row["email"]


@login_manager.user_loader
def load_user(user_id):
    with closing(connect()) as conn:
        row=conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    return User(row) if row else None



@app.route("/demo/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    if request.method == "POST":
        email  = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")


        if not email or "@" not in email or len(password) < 12:
            return render_template("auth.html", mode="register", error="Enter an email and a password of at least 12 characters."), 400

        try:
            with closing(connect()) as conn, conn:
                conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(password)),
                )

        except sqlite3.IntegrityError:
            return render_template("auth.html", mode="register", error="An account with that email already exists."), 409

        return redirect(url_for("login"), code=303)

    return render_template("auth.html", mode="register")

@app.route("/demo/login", methods=["GET", "POST"])

def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with closing(connect()) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,),
            ).fetchone()

        if row is None or not check_password_hash(row["password_hash"], password):
            return render_template("auth.html", mode="login", error="Invalid email or password."), 401

        login_user(User(row))
        return redirect(url_for("profile"), code=303)

    return render_template("auth.html", mode="login")

@app.post("/demo/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"), code=303)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT name, phone, github, resume_filename
            FROM profiles WHERE user_id = ?
            """,
            (current_user.id,),
        ).fetchone()

    values = dict(row) if row else {}

    if request.method == "POST":
        values.update({
            key: request.form.get(key, "").strip()
            for key in ("name", "phone", "github")
        })

        if not values["name"] or not values["phone"]:
            flash("Enter your full name and phone number.")
            return render_template("profile.html", values=values), 400

        resume = request.files.get("resume")
        filename = None
        pdf = None

        if resume and resume.filename:
            pdf = resume.stream.read(MAX_RESUME_BYTES + 1)
            if len(pdf) > MAX_RESUME_BYTES or not pdf.startswith(b"%PDF-"):
                flash("Choose a PDF up to 16 MiB.")
                return render_template("profile.html", values=values), 400
            filename = resume.filename

        with closing(connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO profiles (user_id, name, phone, github, resume_filename, resume_pdf)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = excluded.name,
                    phone = excluded.phone,
                    github = excluded.github,
                    resume_filename = COALESCE(excluded.resume_filename, profiles.resume_filename),
                    resume_pdf = COALESCE(excluded.resume_pdf, profiles.resume_pdf)
                """,
                (current_user.id, values["name"], values["phone"], values["github"], filename, pdf),
            )

        flash("Profile saved.")
        return redirect(url_for("profile"), code=303)

    return render_template("profile.html", values=values)









