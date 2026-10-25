"""The home page opens for a signed-in user and shows the hero, one card per model and the data charts."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from targets import TARGETS

ROOT = Path(__file__).resolve().parent.parent


def test_home_renders():
    at = AppTest.from_file(f"{ROOT}/app.py", default_timeout=120)
    at.session_state["user"] = {"id": 1, "name": "Ilef Zayed", "email": "ilef@test.com"}
    at.run()
    assert not at.exception, at.exception
    html = " ".join(m.value for m in at.markdown)
    assert "hero-title" in html and "Welcome back, Ilef" in html
    assert html.count('class="home-card"') == len(TARGETS)
    assert len(at.get("arrow_chart")) + len(at.get("vega_lite_chart")) >= 2
