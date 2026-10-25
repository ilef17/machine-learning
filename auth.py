"""Authentication: accounts stored in SQLite, passwords hashed with scrypt (standard library only).

- `register` / `authenticate` are plain functions (no Streamlit), so they can be tested on their own.
- `login_page` is the sign-in / create-account screen, `current_user` / `logout` manage the session.
- The database path can be changed with the AUTH_DB environment variable (default: storage/users.db).
"""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
MAX_ATTEMPTS, LOCK_SECONDS = 5, 300  # 5 wrong passwords -> the account is locked for 5 minutes
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)


# ----------------------------------------------------------------------------- storage
def _db():
    path = Path(os.environ.get("AUTH_DB", ROOT / "storage" / "users.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        pw_hash TEXT NOT NULL, created_at REAL NOT NULL, failed INTEGER NOT NULL DEFAULT 0,
        locked_until REAL NOT NULL DEFAULT 0)""")
    return con


def _hash(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def _verify(password, stored):
    try:
        _, salt, digest = stored.split("$")
        expected = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT)
    except ValueError:
        return False
    return hmac.compare_digest(expected, bytes.fromhex(digest))


# ----------------------------------------------------------------------------- accounts
def check_password(password):
    """Returns an error message, or None if the password is acceptable."""
    if len(password) < 8:
        return "The password must contain at least 8 characters."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        return "The password must contain at least one letter and one digit."
    return None


def register(name, email, password):
    """Creates an account. Returns (user dict, None) or (None, error message)."""
    name, email = name.strip(), email.strip().lower()
    if len(name) < 2:
        return None, "Enter your name."
    if not _EMAIL.match(email):
        return None, "Enter a valid email address."
    if (err := check_password(password)):
        return None, err
    with _db() as con:
        try:
            cur = con.execute("INSERT INTO users (email, name, pw_hash, created_at) VALUES (?, ?, ?, ?)",
                              (email, name, _hash(password), time.time()))
        except sqlite3.IntegrityError:
            return None, "An account already exists with this email. Sign in instead."
    return {"id": cur.lastrowid, "name": name, "email": email}, None


def authenticate(email, password):
    """Checks credentials. Returns (user dict, None) or (None, error message)."""
    email = email.strip().lower()
    bad = "Incorrect email or password."
    with _db() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            _hash(password)  # same cost whether or not the account exists
            return None, bad
        if row["locked_until"] > time.time():
            minutes = int((row["locked_until"] - time.time()) // 60) + 1
            return None, f"Too many attempts. Try again in {minutes} min."
        if not _verify(password, row["pw_hash"]):
            failed = row["failed"] + 1
            locked = time.time() + LOCK_SECONDS if failed >= MAX_ATTEMPTS else 0
            con.execute("UPDATE users SET failed = ?, locked_until = ? WHERE id = ?",
                        (0 if locked else failed, locked, row["id"]))
            return None, bad
        con.execute("UPDATE users SET failed = 0, locked_until = 0 WHERE id = ?", (row["id"],))
    return {"id": row["id"], "name": row["name"], "email": row["email"]}, None


# ----------------------------------------------------------------------------- session
def current_user():
    return st.session_state.get("user")


def logout():
    st.session_state.clear()


PANEL = """<div class="auth-panel">
<div class="brand"><span class="mark"><i style="height:7px"></i><i style="height:12px"></i><i style="height:16px"></i></span>Census Insight</div>
<div class="pitch">Six predictive models, and the reasoning behind every answer.</div>
<ul><li>Predictions with a clear confidence level</li>
<li>Recommendations, key factors and what-if scenarios for each model</li>
<li>A segmentation dashboard with a profile simulator</li></ul>
<div class="foot">UCI Adult census, 1994 · Educational project</div></div>"""


def login_page():
    """Sign-in / create-account screen (the only page visible before login)."""
    st.markdown("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'] {display:none}</style>",
                unsafe_allow_html=True)
    left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")
    with left:
        st.markdown(PANEL, unsafe_allow_html=True)
    with right:
        st.markdown('<p class="auth-title">Welcome</p><p class="auth-sub">Sign in to run predictions, or create '
                    'an account to get started.</p>', unsafe_allow_html=True)
        sign_in, sign_up = st.tabs(["Sign in", "Create account"])
        with sign_in, st.form("login_form", border=False):
            email = st.text_input("Email", key="login_email", autocomplete="email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.form_submit_button("Sign in", type="primary", width="stretch"):
                user, err = authenticate(email, password)
                if err:
                    st.error(err)
                else:
                    st.session_state["user"] = user
                    st.rerun()
        with sign_up, st.form("signup_form", border=False):
            name = st.text_input("Full name", key="signup_name", autocomplete="name")
            email = st.text_input("Email", key="signup_email", autocomplete="email")
            password = st.text_input("Password", type="password", key="signup_password",
                                     help="At least 8 characters, with a letter and a digit.")
            confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            if st.form_submit_button("Create account", type="primary", width="stretch"):
                if password != confirm:
                    st.error("The two passwords do not match.")
                else:
                    user, err = register(name, email, password)
                    if err:
                        st.error(err)
                    else:
                        st.session_state["user"] = user
                        st.rerun()
