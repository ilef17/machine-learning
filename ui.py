"""Streamlit page shared by the five prediction targets: form on the left, result and insights on the right."""
from html import escape

import streamlit as st

from core import FIELD_SPECS, options_for
from insights import INSIGHTS
from targets import BY_SLUG


@st.cache_resource(show_spinner=False)
def _bundle(slug):
    return BY_SLUG[slug].load()


def _widget(slug, name, unknown_ok):
    spec, key = FIELD_SPECS[name], f"{slug}_{name}"
    if spec["kind"] == "slider":
        return st.slider(spec["label"], spec["min"], spec["max"], spec["default"], key=key)
    if spec["kind"] == "number":
        return st.number_input(spec["label"], min_value=0, max_value=spec["max"], value=0, step=spec["step"], key=key)
    opts = options_for(name, unknown_ok)
    values = [v for v, _ in opts]
    return st.selectbox(spec["label"], values, index=values.index(spec["default"]),
                        format_func=dict(opts).get, key=key)


# Form fields are grouped in labelled sections (order of the fields inside a section follows this list)
SECTIONS = [("Personal", ["age", "sex", "race", "native-country", "marital-status", "relationship"]),
            ("Education and work", ["education", "workclass", "occupation", "hours-per-week"]),
            ("Income and capital", ["income", "capital-gain", "capital-loss"])]


def _show(entry, res, with_name):
    """The predicted class, its description and the model's confidence in it."""
    meter = ""
    if "confidence" in res:  # clustering has no probability, only a segment
        pct = res["confidence"] * 100
        meter = (f'<div class="meter-top"><span>Model confidence</span><b>{pct:.0f}%</b></div>'
                 f'<div class="meter-track"><div class="meter-fill" style="width:{pct:.0f}%"></div></div>')
    model = f'<span class="result-model">{escape(with_name)}</span>' if with_name else ""
    st.markdown(f'''<div class="result-card"><div class="result-top"><span class="badge">Prediction</span>{model}</div>
<p class="result-label">{escape(res["label"])}</p><p class="result-desc">{escape(res["description"])}</p>{meter}</div>''',
                unsafe_allow_html=True)


def render_target(t):
    st.markdown(f'<p class="crumb">Predictions  /  {escape(t.title)}</p>', unsafe_allow_html=True)
    st.title(f"{t.icon} {t.title}")
    st.markdown(f'<p class="lede">{escape(t.question)} {escape(t.detail)}</p>', unsafe_allow_html=True)
    with st.spinner("Loading the model (on the very first launch, training can take up to a minute)…"):
        bundle = _bundle(t.slug)
    models = bundle["models"]
    state = f"{t.slug}_last"

    left, right = st.columns([5, 7], gap="large")
    with left, st.form(f"form_{t.slug}"):
        choice = next(iter(models))  # one model per page: pages with several keep the first (no selector shown)
        values, first = {}, True
        for title, names in SECTIONS:
            fields = [n for n in names if n in t.fields]
            if not fields:
                continue
            st.markdown(f'<p class="form-section{" first" if first else ""}">{title}</p>', unsafe_allow_html=True)
            first = False
            for k in range(0, len(fields), 2):  # fields laid out in pairs: left / right
                for col, name in zip(st.columns(2), fields[k:k + 2]):
                    with col:
                        values[name] = _widget(t.slug, name, t.unknown_ok)
        if st.form_submit_button("Predict", type="primary", width="stretch"):
            st.session_state[state] = {"choice": choice, "values": values,
                                       "res": t.predict(bundle, choice, values)}

    with right:
        last = st.session_state.get(state)
        if not last:
            st.markdown('<div class="placeholder"><b>No prediction yet</b>Fill in the profile and select Predict. '
                        'The result and the insights behind it appear here.</div>', unsafe_allow_html=True)
        else:
            _show(models[last["choice"]], last["res"], with_name="")
            if t.slug in INSIGHTS:
                title, _, sub = t.extra.partition(": ")
                st.markdown(f'<p class="section-head">{escape(title)}</p><p class="section-sub">{escape(sub.capitalize())}</p>',
                            unsafe_allow_html=True)
                INSIGHTS[t.slug](t, bundle, last["choice"], last["values"], last["res"])

    st.caption("Educational project on a 1994 US census. Predictions are statistical and reflect "
               "the biases in the data (sex, ethnic origin…): they must not be used to make real decisions.")
