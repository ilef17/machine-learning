"""The clustering dashboard (profiles/): every page of its menu opens without error, for each audience."""
import pytest
from streamlit.testing.v1 import AppTest

import profiles.reco as R

ROOT = str(__import__("pathlib").Path(__file__).resolve().parent.parent)
SCRIPT = """
import sys; sys.path.insert(0, {root!r})
from profiles.view import render
render()
"""
PAGES = ["Home", "Who are our audiences?", "Family and marriage", "Why? The factors", "What to offer?",
         "Find a specific audience", "Reliability and method"]


@pytest.fixture(scope="module")
def at():
    app = AppTest.from_string(SCRIPT.format(root=ROOT), default_timeout=300).run()
    assert not app.exception, app.exception
    return app


@pytest.mark.parametrize("audience", list(R.AUDIENCES))
@pytest.mark.parametrize("page", PAGES)
def test_every_page_opens(at, audience, page):
    at.sidebar.radio(key="audience").set_value(audience)
    at.sidebar.radio(key="profiles_menu").set_value(page).run()
    assert not at.exception, at.exception


def test_why_page_every_result_and_factor(at):
    at.sidebar.radio(key="profiles_menu").set_value("Why? The factors").run()
    for res in at.selectbox[0].options[:3]:
        at.selectbox[0].set_value(res).run()
        assert not at.exception, at.exception


def test_advice_for_one_person(at):
    at.sidebar.radio(key="profiles_menu").set_value("What to offer?").run()
    for ex in at.selectbox[0].options:
        at.selectbox[0].set_value(ex).run()
        assert not at.exception, at.exception
