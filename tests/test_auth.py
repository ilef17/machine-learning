"""Authentication: account creation, sign-in, lock-out, and the login gate of the app."""
import pytest
from streamlit.testing.v1 import AppTest

import auth

ROOT = str(__import__("pathlib").Path(__file__).resolve().parent.parent)


@pytest.fixture(autouse=True)
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB", str(tmp_path / "users.db"))


def test_register_then_authenticate():
    user, err = auth.register("Ilef Zayed", "Ilef@Example.com ", "secret123")
    assert err is None and user["email"] == "ilef@example.com"
    ok, err = auth.authenticate("ILEF@example.com", "secret123")
    assert err is None and ok["name"] == "Ilef Zayed"


@pytest.mark.parametrize("name,email,pw,msg", [
    ("I", "a@b.co", "secret123", "name"),
    ("Ilef", "not-an-email", "secret123", "email"),
    ("Ilef", "a@b.co", "short1", "8 characters"),
    ("Ilef", "a@b.co", "onlyletters", "digit")])
def test_register_validation(name, email, pw, msg):
    user, err = auth.register(name, email, pw)
    assert user is None and msg in err


def test_duplicate_email_refused():
    auth.register("Ilef", "a@b.co", "secret123")
    user, err = auth.register("Other", "A@B.co", "secret456")
    assert user is None and "already exists" in err


def test_password_is_not_stored_in_clear():
    auth.register("Ilef", "a@b.co", "secret123")
    stored = auth._db().execute("SELECT pw_hash FROM users").fetchone()[0]
    assert stored.startswith("scrypt$") and "secret123" not in stored


def test_wrong_password_and_lockout():
    auth.register("Ilef", "a@b.co", "secret123")
    for _ in range(auth.MAX_ATTEMPTS):
        user, err = auth.authenticate("a@b.co", "wrong")
        assert user is None and err == "Incorrect email or password."
    user, err = auth.authenticate("a@b.co", "secret123")  # right password, but locked
    assert user is None and "Too many attempts" in err


def test_unknown_account_gives_same_message():
    assert auth.authenticate("nobody@b.co", "whatever1") == (None, "Incorrect email or password.")


def test_app_shows_only_sign_in_until_logged_in():
    at = AppTest.from_file(f"{ROOT}/app.py", default_timeout=120).run()
    assert not at.exception, at.exception
    assert any(b.label == "Sign in" for b in at.button)
    assert not any("Welcome back" in t.value for t in at.title)


def test_signup_opens_the_home_page_and_sign_out_returns():
    at = AppTest.from_file(f"{ROOT}/app.py", default_timeout=120).run()
    at.text_input(key="signup_name").input("Ilef Zayed")
    at.text_input(key="signup_email").input("ilef@example.com")
    at.text_input(key="signup_password").input("secret123")
    at.text_input(key="signup_confirm").input("secret123")
    next(b for b in at.button if b.label == "Create account").click()
    at.run()
    assert not at.exception, at.exception
    assert any("Welcome back, Ilef" in m.value for m in at.markdown)
    next(b for b in at.button if b.key == "signout").click()
    at.run()
    assert any(b.label == "Sign in" for b in at.button)
