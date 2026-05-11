
from __future__ import annotations
import hashlib
import sqlite3
from pathlib import Path
from functools import wraps
from flask import session, redirect, url_for, abort

BASE_DIR = Path(__file__).resolve().parents[2]
AUTH_DB = BASE_DIR / "data" / "warehouse" / "auth.db"

def _conn():
    return sqlite3.connect(AUTH_DB)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username: str, password: str):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("select username, role, full_name from users where username=? and password_hash=?", (username, hash_password(password)))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "role": row[1], "full_name": row[2]}
    return None

def audit(username: str, action: str, detail: str = ""):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("insert into audit_logs (ts, username, action, detail) values (datetime('now'), ?, ?, ?)", (username, action, detail))
    conn.commit()
    conn.close()

def recent_audit(limit: int = 100):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("select ts, username, action, detail from audit_logs order by id desc limit ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("login"))
            if user.get("role") not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
