"""Streamlit platform: sign-in, then 6 pages on the Adult dataset (income, education, occupation, relationship,
workclass, profile).

Run:  streamlit run app.py
Add a page: create targets/<name>.py (see targets/relationship.py) and add it to targets/__init__.py.
"""
from html import escape
from pathlib import Path

import streamlit as st

import auth
import home as home_ui
from profiles.view import render as render_profiles
from style import inject
from targets import TARGETS
from ui import render_target

RENDERERS = {"marital": render_profiles}  # pages with their own layout (otherwise: shared form)
LOGO = str(Path(__file__).resolve().parent / "assets" / "logo.svg")

st.set_page_config(page_title="Census Insight", page_icon=":material/bar_chart:", layout="wide")
inject()


@st.cache_data(show_spinner=False)
def _census_size():
    from core import read_adult
    return len(read_adult("adult.data").drop_duplicates())


def home():
    home_ui.render(auth.current_user(), PAGES, _census_size())


def _make_page(t):
    def page():
        RENDERERS.get(t.slug, render_target)(t)
    page.__name__ = f"page_{t.slug}"
    return page


PAGES = {t.slug: st.Page(_make_page(t), title=t.title, icon=t.icon, url_path=t.slug) for t in TARGETS}
home_page = st.Page(home, title="Home", icon=":material/home:", default=True, url_path="home")

if auth.current_user() is None:
    st.navigation([st.Page(auth.login_page, title="Sign in", url_path="sign-in")], position="hidden").run()
else:
    st.logo(LOGO, size="large")
    nav = st.navigation({"": [home_page], "Predictions": list(PAGES.values())})
    nav.run()  # the page fills the sidebar first (e.g. the profile menu) ...
    user = auth.current_user()
    with st.sidebar:  # ... so the account block always comes last, at the bottom
        with st.container(key="usercard"):
            st.markdown(f'<div class="user-chip"><div class="user-avatar">{escape(user["name"][:1].upper())}</div>'
                        f'<div class="user-info"><div class="user-name">{escape(user["name"])}</div>'
                        f'<div class="user-mail">{escape(user["email"])}</div></div></div>', unsafe_allow_html=True)
            if st.button("Sign out", icon=":material/logout:", width="stretch", key="signout"):
                auth.logout()
                st.rerun()
