import csv
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


DATABASE = os.environ.get("DATABASE", "/data/timesheet.sqlite3")
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
SESSION_SECRET = os.environ["SESSION_SECRET"]
ALLOWED_DOMAIN = os.environ.get("ALLOWED_DOMAIN", "developyn.com")

app = Flask(__name__)
app.secret_key = SESSION_SECRET


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            picture TEXT,
            is_admin INTEGER NOT NULL DEFAULT 0,
            has_email_reminders INTEGER NOT NULL DEFAULT 1,
            last_login_at TEXT
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            client TEXT NOT NULL DEFAULT '',
            currency TEXT NOT NULL DEFAULT 'GBP',
            maximum_hours REAL,
            end_date TEXT,
            is_maintenance INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS project_developers (
            id INTEGER PRIMARY KEY,
            hourly_rate REAL NOT NULL DEFAULT 0,
            developer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            max_hours INTEGER,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS timesheet_entries (
            id INTEGER PRIMARY KEY,
            entry_date TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            hours REAL NOT NULL,
            hourly_rate REAL,
            description TEXT,
            paid_work INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    db.commit()


@app.before_request
def ensure_db():
    init_db()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if not user["is_admin"]:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    return {"user": current_user(), "google_client_id": GOOGLE_CLIENT_ID}


@app.get("/health")
def health():
    return "ok"


@app.get("/login")
def login():
    return render_template("login.html")


@app.post("/auth/google")
def auth_google():
    token = request.form.get("credential")
    if not token:
        abort(400)

    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
    except ValueError:
        abort(401)

    email = info.get("email", "").lower()
    if not info.get("email_verified") or not email.endswith(f"@{ALLOWED_DOMAIN}"):
        abort(403)

    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    now = datetime.now(timezone.utc).isoformat()
    if existing:
        db.execute(
            "UPDATE users SET name = ?, picture = ?, last_login_at = ? WHERE id = ?",
            (info.get("name"), info.get("picture"), now, existing["id"]),
        )
        user_id = existing["id"]
    else:
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        cursor = db.execute(
            "INSERT INTO users (email, name, picture, is_admin, last_login_at) VALUES (?, ?, ?, ?, ?)",
            (email, info.get("name"), info.get("picture"), 1 if count == 0 else 0, now),
        )
        user_id = cursor.lastrowid
    db.commit()
    session["user_id"] = user_id
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    user = current_user()
    start = request.args.get("start") or (date.today() - timedelta(days=30)).isoformat()
    end = request.args.get("end") or date.today().isoformat()
    params = [start, end]
    where = "WHERE date(entry_date) BETWEEN date(?) AND date(?)"
    if not user["is_admin"]:
        where += " AND t.user_id = ?"
        params.append(user["id"])

    entries = get_db().execute(
        f"""
        SELECT t.*, u.email, COALESCE(u.name, u.email) AS user_name, p.name AS project_name, p.client
        FROM timesheet_entries t
        JOIN users u ON u.id = t.user_id
        JOIN projects p ON p.id = t.project_id
        {where}
        ORDER BY date(t.entry_date) DESC, t.id DESC
        """,
        params,
    ).fetchall()
    totals = get_db().execute(
        f"""
        SELECT p.name AS project_name, COALESCE(u.name, u.email) AS user_name, SUM(t.hours) AS hours
        FROM timesheet_entries t
        JOIN users u ON u.id = t.user_id
        JOIN projects p ON p.id = t.project_id
        {where}
        GROUP BY p.name, user_name
        ORDER BY p.name, user_name
        """,
        params,
    ).fetchall()
    return render_template("index.html", entries=entries, totals=totals, start=start, end=end)


@app.route("/entries/new", methods=["GET", "POST"])
@login_required
def new_entry():
    user = current_user()
    db = get_db()
    projects = db.execute("SELECT * FROM projects WHERE active = 1 ORDER BY client, name").fetchall()
    if request.method == "POST":
        project_id = int(request.form["project_id"])
        hours = float(request.form["hours"])
        if hours <= 0:
            abort(400)
        rate = db.execute(
            "SELECT hourly_rate FROM project_developers WHERE developer_id = ? AND project_id = ? AND active = 1",
            (user["id"], project_id),
        ).fetchone()
        db.execute(
            """
            INSERT INTO timesheet_entries (entry_date, user_id, project_id, hours, hourly_rate, description, paid_work)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.form["entry_date"],
                user["id"],
                project_id,
                hours,
                rate["hourly_rate"] if rate else None,
                request.form.get("description", "").strip(),
                1 if request.form.get("paid_work") else 0,
            ),
        )
        db.commit()
        flash("Entry saved")
        return redirect(url_for("index"))
    return render_template("entry_form.html", projects=projects, entry=None)


@app.post("/entries/<int:entry_id>/delete")
@login_required
def delete_entry(entry_id):
    user = current_user()
    db = get_db()
    entry = db.execute("SELECT * FROM timesheet_entries WHERE id = ?", (entry_id,)).fetchone()
    if not entry:
        abort(404)
    if not user["is_admin"] and entry["user_id"] != user["id"]:
        abort(403)
    db.execute("DELETE FROM timesheet_entries WHERE id = ?", (entry_id,))
    db.commit()
    flash("Entry deleted")
    return redirect(url_for("index"))


@app.get("/projects")
@login_required
def projects():
    projects = get_db().execute(
        "SELECT p.*, COALESCE(SUM(t.hours), 0) AS tracked_hours FROM projects p LEFT JOIN timesheet_entries t ON t.project_id = p.id GROUP BY p.id ORDER BY p.active DESC, p.client, p.name"
    ).fetchall()
    return render_template("projects.html", projects=projects)


@app.route("/projects/new", methods=["GET", "POST"])
@admin_required
def new_project():
    if request.method == "POST":
        get_db().execute(
            "INSERT INTO projects (name, client, currency, maximum_hours, active) VALUES (?, ?, ?, ?, 1)",
            (request.form["name"], request.form.get("client", ""), request.form.get("currency", "GBP"), request.form.get("maximum_hours") or None),
        )
        get_db().commit()
        return redirect(url_for("projects"))
    return render_template("project_form.html")


@app.get("/users")
@admin_required
def users():
    users = get_db().execute("SELECT * FROM users ORDER BY email").fetchall()
    return render_template("users.html", users=users)


@app.get("/export.csv")
@login_required
def export_csv():
    rows = get_db().execute(
        """
        SELECT t.entry_date, u.email, p.client, p.name AS project, t.hours, t.hourly_rate, t.description, t.paid_work
        FROM timesheet_entries t
        JOIN users u ON u.id = t.user_id
        JOIN projects p ON p.id = t.project_id
        ORDER BY date(t.entry_date), t.id
        """
    ).fetchall()
    lines = []
    writer = csv.writer(_CsvBuffer(lines))
    writer.writerow(["date", "user", "client", "project", "hours", "hourly_rate", "description", "paid_work"])
    for row in rows:
        writer.writerow([row[key] for key in row.keys()])
    return "".join(lines), {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=timesheet.csv"}


class _CsvBuffer:
    def __init__(self, lines):
        self.lines = lines

    def write(self, value):
        self.lines.append(value)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
