"""Home page: hero banner, model cards with illustrations, data snapshot and a short "how it works".

`render(user, pages, census_size)` is called by app.py. Styles live in style.py (classes starting with `hero-`,
`home-`, `how-`). Every illustration is generated here as inline SVG / CSS: no image file, no network access.
"""
import random
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from core import read_adult
from targets import TARGETS

# (gradient start, gradient end) of each model card banner
HUES = {"income": ("#2563eb", "#1e3a8a"), "education": ("#8b5cf6", "#4c1d95"), "occupation": ("#f59e0b", "#9a3412"),
        "relationship": ("#f43f5e", "#881337"), "workclass": ("#14b8a6", "#134e4a"), "marital": ("#0ea5e9", "#312e81")}
BLUE, SOFT = "#3b82f6", "#93c5fd"


# ----------------------------------------------------------------------------- illustrations
def _motif(slug):
    """A small abstract drawing (white, translucent) that hints at what the model does."""
    rnd, w = random.Random(slug), "#fff"
    s = []
    if slug == "income":  # rising bars + coins
        for i, h in enumerate([22, 34, 30, 52, 66, 84]):
            s.append(f'<rect x="{150 + i * 24}" y="{112 - h}" width="15" height="{h}" rx="3" fill="{w}" opacity="{.18 + i * .07:.2f}"/>')
        s += [f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{w}" stroke-width="2.5" opacity=".55"/>'
              for x, y, r in [(228, 24, 13), (262, 40, 9), (196, 36, 7)]]
    elif slug == "education":  # steps + cap
        for i in range(5):
            s.append(f'<rect x="{150 + i * 28}" y="{100 - i * 17}" width="28" height="{16 + i * 17 + 12}" fill="{w}" opacity="{.14 + i * .08:.2f}"/>')
        s.append(f'<path d="M210 26 L250 10 L290 26 L250 42 Z M228 34 V50 Q250 62 272 50 V34" fill="none" stroke="{w}" stroke-width="2.5" opacity=".6" stroke-linejoin="round"/>')
    elif slug == "occupation":  # three groups of bars
        for r, (n, o) in enumerate([(7, .55), (5, .35), (9, .22)]):
            for i in range(n):
                s.append(f'<rect x="{160 + i * 17}" y="{24 + r * 30}" width="12" height="20" rx="3" fill="{w}" opacity="{o}"/>')
    elif slug == "relationship":  # family tree
        pts = {"a": (225, 22), "b": (270, 22), "c": (200, 66), "d": (248, 66), "e": (296, 66), "f": (224, 104), "g": (272, 104)}
        for p, q in [("a", "b"), ("a", "c"), ("a", "d"), ("b", "d"), ("b", "e"), ("c", "f"), ("d", "f"), ("d", "g")]:
            s.append(f'<line x1="{pts[p][0]}" y1="{pts[p][1]}" x2="{pts[q][0]}" y2="{pts[q][1]}" stroke="{w}" stroke-width="2" opacity=".35"/>')
        s += [f'<circle cx="{x}" cy="{y}" r="9" fill="{w}" opacity=".6"/>' for x, y in pts.values()]
    elif slug == "workclass":  # concentric arcs
        for i, (r, o) in enumerate([(78, .16), (58, .26), (38, .38), (18, .55)]):
            s.append(f'<circle cx="262" cy="70" r="{r}" fill="none" stroke="{w}" stroke-width="9" opacity="{o}" '
                     f'stroke-dasharray="{r * 4.4:.0f} {r * 6.3:.0f}" stroke-linecap="round" transform="rotate({-60 + i * 25} 262 70)"/>')
    else:  # clusters of dots
        for cx, cy, o in [(205, 36, .85), (262, 78, .55), (300, 32, .35)]:
            s += [f'<circle cx="{cx + rnd.gauss(0, 15):.0f}" cy="{cy + rnd.gauss(0, 13):.0f}" r="{rnd.choice([3, 4, 5])}" fill="{w}" opacity="{o}"/>'
                  for _ in range(16)]
    return f'<svg class="home-motif" viewBox="0 0 330 120" preserveAspectRatio="xMaxYMid slice" aria-hidden="true">{"".join(s)}</svg>'


def _banner(t):
    a, b = HUES[t.slug]
    return (f'<div class="home-banner" style="background:linear-gradient(135deg,{a},{b})">{_motif(t.slug)}'
            f'<div class="home-icon">{t.icon}</div></div>')


def _hero_visual():
    """Floating 'app window' made of three cards: prediction, key factors, segment."""
    bars = "".join(f'<div class="fx-row"><span>{n}</span><i style="width:{w}%"></i></div>'
                   for n, w in [("Education", 92), ("Occupation", 74), ("Hours / week", 58), ("Capital gain", 36)])
    people = "".join(f'<b style="background:{c}">{l}</b>' for c, l in
                     [("#60a5fa", "A"), ("#f59e0b", "M"), ("#34d399", "S"), ("#f472b6", "L")])
    return f'''<div class="hero-visual" aria-hidden="true">
<div class="fx fx-a"><div class="fx-top"><em>Prediction</em><span>Census model</span></div>
<p class="fx-big">&gt; $50,000</p><div class="fx-meter"><div style="width:87%"></div></div>
<div class="fx-meta"><span>Model confidence</span><b>87%</b></div></div>
<div class="fx fx-b"><div class="fx-top"><em>Key factors</em></div>{bars}</div>
<div class="fx fx-c"><div class="fx-top"><em>Similar profiles</em></div><div class="fx-people">{people}<span>+246</span></div></div>
<span class="orb o1"></span><span class="orb o2"></span></div>'''


# ----------------------------------------------------------------------------- data snapshot
@st.cache_data(show_spinner=False)
def _snapshot():
    df = read_adult("adult.data").drop_duplicates()
    df["high"] = df["income"].str.strip().eq(">50K")
    edu = (df.groupby(["education", "education-num"])["high"].mean().reset_index()
           .rename(columns={"high": "share", "education": "Education"}).sort_values("education-num"))
    df["Age"] = (df["age"] // 5 * 5).clip(upper=80)
    age = (df.groupby(["Age", "high"]).size().reset_index(name="People"))
    age["Income"] = age["high"].map({True: "> $50K", False: "≤ $50K"})
    return edu, age[["Age", "Income", "People"]]


def _charts():
    edu, age = _snapshot()
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        st.markdown('<p class="home-chart-title">Who earns more than $50K</p>'
                    '<p class="home-chart-sub">Share of people above $50K, by education level</p>', unsafe_allow_html=True)
        st.altair_chart(alt.Chart(edu).mark_bar(color=BLUE, cornerRadiusEnd=4, size=11).encode(
            y=alt.Y("Education:N", sort=list(edu["Education"]), title=None, axis=alt.Axis(labelLimit=120, labelOverlap=False)),
            x=alt.X("share:Q", title=None, axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            tooltip=["Education", alt.Tooltip("share:Q", format=".0%", title="Above $50K")]).properties(height=340))
    with right, st.container(border=True):
        st.markdown('<p class="home-chart-title">Age profile of the census</p>'
                    '<p class="home-chart-sub">Number of people by 5-year age band and income class</p>', unsafe_allow_html=True)
        st.altair_chart(alt.Chart(age).mark_area(opacity=.85, line=True, interpolate="monotone").encode(
            x=alt.X("Age:Q", title="Age", axis=alt.Axis(tickMinStep=10)),
            y=alt.Y("People:Q", stack=True, title=None),
            color=alt.Color("Income:N", scale=alt.Scale(domain=["≤ $50K", "> $50K"], range=[SOFT, "#1d4ed8"]),
                            legend=alt.Legend(title=None, orient="top-right")),
            tooltip=["Age", "Income", "People"]).properties(height=340))


# ----------------------------------------------------------------------------- page
def _session_strip():
    """Predictions already made in this browser session (shown only when there are some)."""
    chips = []
    for t in TARGETS:
        last = st.session_state.get(f"{t.slug}_last")
        if last:
            chips.append(f'<span class="home-chip"><small>{escape(t.title)}</small><b>{escape(last["res"]["label"])}</b></span>')
    if chips:
        st.markdown(f'<div class="home-session"><span class="home-session-title">Your session</span>{"".join(chips)}</div>',
                    unsafe_allow_html=True)


ICONS = {  # small stroke icons for the "How it works" steps (Material shortcodes do not render inside raw HTML blocks)
    "form": '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13 7l4 4"/>',
    "brain": '<path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/><circle cx="16" cy="7" r="2.5"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
}


def _icon(name):
    return (f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def _step(n, icon, title, text):
    return (f'<div class="how-step"><span class="how-n">{n}</span><div class="how-icon">{_icon(icon)}</div>'
            f'<p class="how-title">{title}</p><p class="how-text">{text}</p></div>')


def render(user, pages, census_size):
    first = user["name"].split()[0]
    stats = [(f"{census_size:,}", "census records"), (str(len(TARGETS)), "predictive models"),
             ("14", "variables per person"), ("1994", "US census data")]
    with st.container(key="hero"):
        text, visual = st.columns([6, 5], gap="large", vertical_alignment="center")
        with text:
            st.markdown(f'''<span class="hero-pill"><i></i>Welcome back, {escape(first)}</span>
<h1 class="hero-title">What does a census profile say about a person's <span>income, work and family</span>?</h1>
<p class="hero-sub">Describe someone, get a machine-learning prediction with its confidence, then see what sits behind it:
key factors, recommendations and comparable profiles.</p>''', unsafe_allow_html=True)
            a, b = st.columns(2, gap="small")
            with a, st.container(key="hero-cta"):
                st.page_link(pages["income"], label="Try the income model", icon=":material/rocket_launch:")
            with b, st.container(key="hero-ghost"):
                st.page_link(pages["marital"], label="Open the dashboard", icon=":material/dashboard:")
        with visual:
            st.markdown(_hero_visual(), unsafe_allow_html=True)
        st.markdown('<div class="hero-stats">' + "".join(f"<div><b>{v}</b><span>{k}</span></div>" for v, k in stats) + "</div>",
                    unsafe_allow_html=True)

    _session_strip()

    st.markdown('<p class="section-head">Models</p><p class="section-sub">Six pages, one dataset. Pick what you want to estimate.</p>',
                unsafe_allow_html=True)
    for i in range(0, len(TARGETS), 3):
        for col, t in zip(st.columns(3, gap="medium"), TARGETS[i:i + 3]):
            with col, st.container(border=True, key=f"card-{t.slug}"):
                st.markdown(f'<span class="home-card"></span>{_banner(t)}<p class="home-card-title">{escape(t.title)}</p>',
                            unsafe_allow_html=True)
                st.write(t.question)
                st.markdown(f'<p class="home-card-model">{escape(t.detail)}</p><span class="home-card-extra">{escape(t.extra)}</span>',
                            unsafe_allow_html=True)
                st.page_link(pages[t.slug], label=f"Open {t.title.lower()}", icon=":material/arrow_forward:")

    st.markdown('<p class="section-head">Inside the data</p><p class="section-sub">A first look at the census behind every model.</p>',
                unsafe_allow_html=True)
    _charts()

    st.markdown('<p class="section-head">How it works</p><p class="section-sub">Three steps, the same on every page.</p>',
                unsafe_allow_html=True)
    st.markdown('<div class="how-grid">' + _step(1, "form", "Describe a profile", "Age, education, job, hours worked: fill in the form on any page.")
                + _step(2, "brain", "Get a prediction", "The model gives its answer along with how confident it is.")
                + _step(3, "search", "Explore the why", "Key factors, what-if changes, recommendations and similar people.")
                + "</div>", unsafe_allow_html=True)
    st.caption("The data dates from 1994 and contains biases: educational project, not for real decisions.")
