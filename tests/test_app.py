"""Tests every page: the page opens, the form is submitted, results are consistent."""
import pytest
from streamlit.testing.v1 import AppTest

from targets import BY_SLUG, TARGETS

SCRIPT = """
import sys; sys.path.insert(0, {root!r})
from targets import BY_SLUG
from ui import render_target
render_target(BY_SLUG[{slug!r}])
"""
ROOT = str(__import__("pathlib").Path(__file__).resolve().parent.parent)


def run(slug):
    at = AppTest.from_string(SCRIPT.format(root=ROOT, slug=slug), default_timeout=300).run()
    assert not at.exception, at.exception
    return at


def submit(at):
    next(b for b in at.button if b.label == "Predict").click()
    at.run()
    assert not at.exception, at.exception
    return at


def results(at):
    """Result cards displayed (only one expected per prediction)."""
    return [m.value for m in at.markdown if "class=\"result-card\"" in m.value]


@pytest.mark.parametrize("slug", [t.slug for t in TARGETS if t.slug != "marital"])  # marital = dashboard (tests/test_profiles.py)
def test_page_and_prediction(slug):
    at = submit(run(slug))
    assert len(results(at)) == 1, "exactly one result expected"
    assert not list(at.get("progress")), "no probability bars any more"
    assert not any("performance" in e.label.lower() for e in at.expander), "model performance is not shown"


EXTRAS = {"income": "Recommendations", "education": "Key factors", "occupation": "Career matches",
          "relationship": "What-if", "workclass": "Similar profiles"}


@pytest.mark.parametrize("slug", list(EXTRAS))
def test_each_page_adds_something_more_than_the_prediction(slug):
    at = submit(run(slug))
    heads = [m.value for m in at.markdown if "section-head" in m.value]
    assert len(heads) == 1 and EXTRAS[slug] in heads[0]


def test_income_recommendations_raise_the_estimate():
    at = run("income")
    at.slider(key="income_age").set_value(30)
    at.selectbox(key="income_education").set_value("HS-grad")
    at.selectbox(key="income_occupation").set_value("Other-service")
    at.slider(key="income_hours-per-week").set_value(35)
    submit(at)
    now = next(m for m in at.metric if m.label == "Chance today").value
    full = next(m for m in at.metric if m.label == "With the full plan").value
    assert int(full.rstrip("%")) > int(now.rstrip("%"))


def test_income_recommendations_never_use_protected_traits():
    from insights import _income_actions
    base = {"age": 30, "workclass": "Private", "education": "HS-grad", "occupation": "Sales", "hours-per-week": 40,
            "capital-gain": 0}
    touched = {k for _, _, chg in _income_actions(base) for k in chg}
    assert touched <= {"education", "hours-per-week", "occupation", "workclass", "capital-gain"}


def test_occupation_matches_returns_five_rows():
    at = submit(run("occupation"))
    assert len(at.dataframe[0].value) == 5


def test_income_has_no_model_selector():
    at = run("income")
    assert not any(sb.label == "Model" for sb in at.selectbox)
    submit(at)
    assert len(results(at)) == 1


def test_relationship_husband_profile():
    at = run("relationship")  # default profile: married man, 30 years old
    submit(at)
    assert "Husband<" in results(at)[0]


def test_relationship_wife_profile():
    at = run("relationship")
    at.selectbox(key="relationship_sex").set_value("Female")
    submit(at)
    assert "Wife<" in results(at)[0]


def test_education_high_profile():
    at = run("education")
    at.selectbox(key="education_occupation").set_value("Prof-specialty")
    at.selectbox(key="education_income").set_value(">50K")
    submit(at)
    assert "Higher education<" in results(at)[0]


def test_unknown_option_only_where_trained():
    from core import options_for
    assert ("Unknown", "Not specified") in options_for("workclass", BY_SLUG["income"].unknown_ok)
    assert ("Unknown", "Not specified") not in options_for("workclass", BY_SLUG["relationship"].unknown_ok)


def test_workclass_has_all_classes_and_one_result():
    from core import OPTIONS
    at = run("workclass")
    assert not any(s.key == "workclass_workclass" for s in at.selectbox), "workclass is the target, not a field"
    submit(at)
    assert len(results(at)) == 1
    bundle = BY_SLUG["workclass"].load()
    assert set(bundle["models"]["rf"]["pipeline"].classes_) == {v for v, _ in OPTIONS["workclass"]}


def test_workclass_unknown_occupation_ok():
    at = run("workclass")
    at.selectbox(key="workclass_occupation").set_value("Unknown")
    at.selectbox(key="workclass_native-country").set_value("Unknown")
    submit(at)
    assert len(results(at)) == 1
