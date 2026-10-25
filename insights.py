"""What each page adds on top of the prediction itself.

    income        recommendations: which actions raise the chance of earning more than $50,000
    education     key factors: which inputs drove the predicted level
    occupation    career matches: the 5 closest detailed occupations, with typical hours and income
    relationship  what-if: which single changes would flip the predicted role
    workclass     similar profiles: how comparable people in the census actually work

Every function receives (target, bundle, model_id, values, result) and draws into the current container.
"""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from core import EDUCATION_NUM, FIELD_SPECS, OPTIONS, read_adult
from targets import occupation

ACCENT, WARM, MUTED = "#3b82f6", "#f59e0b", "#8b93a1"


# ----------------------------------------------------------------------------- shared data
@st.cache_data(show_spinner=False)
def _census():
    """adult.data without duplicates; '?' -> 'Unknown'; education-num added."""
    df = read_adult("adult.data").drop_duplicates().reset_index(drop=True)
    for c in ("workclass", "occupation", "native-country"):
        df[c] = df[c].fillna("Unknown")
    df["education-num"] = df["education"].map(EDUCATION_NUM)
    return df


@st.cache_data(show_spinner=False)
def _typical_people(n=25):
    """A fixed random sample of real census records, used as the 'typical person' of the key-factors analysis."""
    return _census().sample(n, random_state=0).to_dict("records")


def _label(field, value):
    if field == "education":
        return value
    return "Not specified" if value == "Unknown" else str(value)


def _show_value(field, value):
    if field in ("capital-gain", "capital-loss"):
        return f"${value:,.0f}"
    return _label(field, value)


def _hbar(df, y, x, order, color=ACCENT, title=None, fmt="%", height=None, scale=alt.Undefined, **enc):
    base = alt.Chart(df).encode(y=alt.Y(f"{y}:N", sort=order, title=None, axis=alt.Axis(labelLimit=320)))
    bars = base.mark_bar(color=color, cornerRadiusEnd=3, height=18).encode(
        x=alt.X(f"{x}:Q", title=title, scale=scale, axis=alt.Axis(format=fmt)), **enc)
    return bars.properties(height=height or 38 * len(df) + 24, width="container")


# ----------------------------------------------------------------------------- income: recommendations
EDU_TEXT = {"Some-college": "Complete some college", "Bachelors": "Earn a Bachelor's degree",
            "Masters": "Earn a Master's degree", "Prof-school": "Earn a professional degree"}


def _income_actions(v):
    """(lever, action, changes): only things a person can act on. Age, sex, race, marital status and
    country are never suggested."""
    acts = []
    for e, text in EDU_TEXT.items():
        if EDUCATION_NUM[e] > EDUCATION_NUM[v["education"]]:
            acts.append(("Education", text, {"education": e}))
    for extra in (5, 10):
        h = v["hours-per-week"] + extra
        if h <= 70:
            acts.append(("Working hours", f"Work {h} hours a week", {"hours-per-week": h}))
    for job in ("Exec-managerial", "Prof-specialty", "Tech-support", "Sales"):
        if job != v["occupation"]:
            acts.append(("Occupation", f"Move into {job}", {"occupation": job}))
    for wc in ("Self-emp-inc", "Federal-gov"):
        if wc != v["workclass"]:
            acts.append(("Employer type", f"Work as {wc}", {"workclass": wc}))
    if v["capital-gain"] < 5000:
        acts.append(("Investments", "Build investment income ($5,000 capital gain)", {"capital-gain": 5000}))
    return acts


def income_recommendations(t, bundle, model_id, v, res):
    acts = _income_actions(v)
    rows = [v] + [{**v, **c} for _, _, c in acts]
    _, P = t.proba(bundle, model_id, rows)
    now, after = P[0][0], P[1:, 0]
    best = {}  # best action of each lever
    for (lever, text, chg), p in zip(acts, after):
        if p - now > 0.005 and (lever not in best or p > best[lever][2]):
            best[lever] = (text, chg, p)
    ranked = sorted(best.values(), key=lambda b: -b[2])

    # Combined plan: apply the levers one after the other, best first
    plan, cur = [], dict(v)
    if ranked:
        steps = []
        for text, chg, _ in ranked:
            cur = {**cur, **chg}
            steps.append((text, dict(cur)))
        _, PP = t.proba(bundle, model_id, [s for _, s in steps])
        plan = [(text, float(p[0])) for (text, _), p in zip(steps, PP)]

    a, b, c = st.columns(3)
    a.metric("Chance today", f"{now:.0%}")
    b.metric("Best single action", f"+{(ranked[0][2] - now) * 100:.0f} pts" if ranked else "None")
    c.metric("With the full plan", f"{plan[-1][1]:.0%}" if plan else f"{now:.0%}")

    if not ranked:
        st.info("None of the actions tested raises the estimate for this profile.")
        return
    st.markdown("**Recommended actions, ranked by impact**")
    df = pd.DataFrame({"Action": [r[0] for r in ranked], "Gain": [r[2] - now for r in ranked],
                       "After": [r[2] for r in ranked]})
    bars = _hbar(df, "Action", "Gain", list(df["Action"]), title="Change in probability (points)", fmt="+.0%",
                 scale=alt.Scale(domain=[0, float(df["Gain"].max()) * 1.25]),
                 tooltip=["Action", alt.Tooltip("Gain:Q", format="+.1%"), alt.Tooltip("After:Q", format=".0%")])
    labels = alt.Chart(df).mark_text(align="left", dx=5, color=MUTED).encode(
        y=alt.Y("Action:N", sort=list(df["Action"])), x=alt.X("Gain:Q", scale=alt.Scale(domain=[0, float(df["Gain"].max()) * 1.25])), text=alt.Text("After:Q", format=".0%"))
    st.altair_chart(bars + labels, width="stretch")

    st.markdown("**A realistic plan: combine them in this order**")
    lines = [f"{i}. {text} → **{p:.0%}**" for i, (text, p) in enumerate(plan, 1)]
    st.markdown("\n".join(lines))
    st.caption("Each line adds one action to the previous ones. Only things a person can act on are suggested: "
               "age, sex, race, marital status and country are never used as recommendations. "
               "Associations in a 1994 census are not guarantees.")


# ----------------------------------------------------------------------------- education: key factors
def education_factors(t, bundle, model_id, v, res):
    people = _typical_people()
    rows = [v] + [{**v, f: p[f]} for f in t.fields for p in people]
    labels, P = t.proba(bundle, model_id, rows)
    k = labels.index(res["label"])
    avg = P[1:, k].reshape(len(t.fields), len(people)).mean(axis=1)  # same profile, one input swapped for a typical one
    impact = P[0][k] - avg  # > 0: this input pushes toward the predicted level
    df = pd.DataFrame({"Factor": [f"{FIELD_SPECS[f]['label']}: {_show_value(f, v[f])}" for f in t.fields],
                       "Impact": impact}).sort_values("Impact", key=abs, ascending=False).head(8)
    df["Direction"] = np.where(df["Impact"] >= 0, "Pushes toward this level", "Pushes away from it")
    order = list(df["Factor"])
    lim = max(float(df["Impact"].abs().max()) * 1.15, 0.02)
    chart = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=18).encode(
        y=alt.Y("Factor:N", sort=order, title=None, axis=alt.Axis(labelLimit=320)),
        x=alt.X("Impact:Q", scale=alt.Scale(domain=[-lim, lim]), axis=alt.Axis(format="+.0%"),
                title=f"Effect on the probability of “{res['label']}”"),
        color=alt.Color("Direction:N", legend=alt.Legend(title=None, orient="top"),
                        scale=alt.Scale(domain=["Pushes toward this level", "Pushes away from it"],
                                        range=[ACCENT, WARM])),
        tooltip=["Factor", alt.Tooltip("Impact:Q", format="+.1%")]).properties(height=38 * len(df) + 40, width="container")
    st.altair_chart(chart, width="stretch")
    top = df.iloc[0]
    st.markdown(f"The strongest signal is **{top['Factor']}**: compared with a typical person, it "
                f"{'raises' if top['Impact'] > 0 else 'lowers'} the probability of this level by "
                f"{abs(top['Impact']) * 100:.0f} points.")
    st.caption(f"Each bar swaps one input for the value of {len(people)} randomly drawn census people and measures how "
               "the probability of the predicted level changes on average. It describes this model's behaviour, not a cause.")


# ----------------------------------------------------------------------------- occupation: career matches
@st.cache_data(show_spinner=False)
def _occupation_stats():
    d = _census()
    g = d.groupby("occupation")
    return pd.DataFrame({"hours": g["hours-per-week"].median(), "edu": g["education-num"].mean(),
                         "high": g["income"].apply(lambda s: (s == ">50K").mean())})


def occupation_matches(t, bundle, model_id, v, res):
    names, P = occupation.detail_proba(bundle, [v])
    top = np.argsort(-P[0])[:5]
    stats = _occupation_stats()
    df = pd.DataFrame({
        "Occupation": [names[i] for i in top],
        "Match": [float(P[0][i]) * 100 for i in top],
        "Hours / week": [float(stats.loc[names[i], "hours"]) for i in top],
        "Education": [float(stats.loc[names[i], "edu"]) for i in top],
        "> $50K": [float(stats.loc[names[i], "high"]) * 100 for i in top]})
    best = df.iloc[0]
    st.markdown(f"The closest occupation is **{best['Occupation']}** (match {best['Match']:.0f}%). "
                "Here are the five best fits and what each looks like in the census.")
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        "Match": st.column_config.ProgressColumn("Match", min_value=0, max_value=float(df["Match"].max()) * 1.15,
                                                 format="%.0f%%"),
        "Hours / week": st.column_config.NumberColumn(format="%.0f h", help="Typical (median) working hours."),
        "Education": st.column_config.NumberColumn(format="%.1f", help="Average education level, from 1 to 16."),
        "> $50K": st.column_config.NumberColumn(format="%.0f%%", help="Share of people earning more than $50,000.")})
    st.caption("The match score comes from a second model trained on the 14 detailed occupations with the same "
               "inputs. It ranks fits, it does not predict a job: the 14 classes overlap a lot. "
               "Typical figures are census averages for each occupation.")


# ----------------------------------------------------------------------------- relationship: what-if
def _whatif_variants(v):
    out = []
    for a in (20, 30, 40, 50, 60, 70):
        if abs(a - v["age"]) >= 5:
            out.append(("Age", f"Age {a}", {"age": a}))
    out += [("Sex", s, {"sex": s}) for s in ("Male", "Female") if s != v["sex"]]
    out += [("Marital status", m, {"marital-status": m}) for m, _ in OPTIONS["marital-status"]
            if m != v["marital-status"]]
    out += [("Education", e, {"education": e}) for e in ("HS-grad", "Bachelors", "Masters") if e != v["education"]]
    out += [("Hours per week", f"{h} h", {"hours-per-week": h}) for h in (20, 40, 60) if abs(h - v["hours-per-week"]) >= 10]
    return out


def relationship_whatif(t, bundle, model_id, v, res):
    variants = _whatif_variants(v)
    labels, P = t.proba(bundle, model_id, [{**v, **c} for _, _, c in variants])
    rows = []
    for (field, what, _), p in zip(variants, P):
        k = int(p.argmax())
        if labels[k] != res["label"]:
            rows.append({"If this changed…": f"{field}: {what}", "New prediction": labels[k],
                         "Confidence": float(p[k]) * 100})
    flips = len(rows)
    a, b = st.columns(2)
    a.metric("Single changes tested", len(variants))
    b.metric("Changes that flip the answer", flips)
    if not rows:
        st.success(f"The prediction “{res['label']}” is stable: none of the changes tested alters it.")
        return
    df = pd.DataFrame(rows).sort_values("Confidence", ascending=False).head(8)
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%.0f%%")})
    st.caption("One input is changed at a time while the others stay as entered. Race and country are left out of "
               "this analysis on purpose.")


# ----------------------------------------------------------------------------- workclass: similar profiles
PEERS = 250


def workclass_peers(t, bundle, model_id, v, res):
    d = _census()
    d = d[d["workclass"] != "Unknown"]
    dist = (d["age"].sub(v["age"]).abs() / 73 + d["education-num"].sub(EDUCATION_NUM[v["education"]]).abs() / 15
            + d["hours-per-week"].sub(v["hours-per-week"]).abs() / 98
            + (d["sex"] != v["sex"]) + 0.75 * (d["marital-status"] != v["marital-status"])
            + 0.75 * (d["relationship"] != v["relationship"]) + 0.5 * ((d["capital-gain"] > 0) != (v["capital-gain"] > 0)))
    if v["occupation"] != "Unknown":
        dist = dist + (d["occupation"] != v["occupation"])
    peers = d.loc[dist.nsmallest(PEERS).index]
    share, pop = peers["workclass"].value_counts(normalize=True), d["workclass"].value_counts(normalize=True)
    order = [w for w, _ in OPTIONS["workclass"] if w in pop.index]
    top = share.index[0]

    a, b, c = st.columns(3)
    a.metric("Similar people found", f"{PEERS:,}", help=f"The {PEERS} closest profiles among {len(d):,} census records.")
    b.metric("Most common among them", top, delta=f"{share.iloc[0]:.0%} of the group", delta_color="off")
    c.metric("Model prediction", res["label"])
    t_ = pd.DataFrame({"Workclass": order * 2, "Group": ["Similar profiles"] * len(order) + ["Whole census"] * len(order),
                       "Share": [float(share.get(w, 0)) for w in order] + [float(pop[w]) for w in order]})
    chart = alt.Chart(t_).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Workclass:N", sort=order, title=None, axis=alt.Axis(labelAngle=-25, labelOverlap=False)), xOffset="Group:N",
        y=alt.Y("Share:Q", axis=alt.Axis(format="%"), title=None),
        color=alt.Color("Group:N", legend=alt.Legend(title=None, orient="top"),
                        scale=alt.Scale(domain=["Similar profiles", "Whole census"], range=[ACCENT, "#b0b7c3"])),
        tooltip=["Workclass", "Group", alt.Tooltip("Share:Q", format=".1%")]).properties(height=260, width="container")
    st.altair_chart(chart, width="stretch")
    lift = (share / pop.reindex(share.index)).where(pop.reindex(share.index) >= 0.01).dropna().sort_values(ascending=False)
    if len(lift) and lift.index[0] != "Private":
        st.markdown(f"Compared with the whole census, people like this are **{lift.iloc[0]:.1f}× more likely** to be "
                    f"**{lift.index[0]}** ({share[lift.index[0]]:.0%} against {pop[lift.index[0]]:.0%}).")
    st.caption("Peers are the census records closest in age, education, hours, sex, marital status, relationship, "
               "occupation and capital gain. Most people work in the private sector, so this comparison shows "
               "what sets a profile apart better than a single predicted class.")


INSIGHTS = {"income": income_recommendations, "education": education_factors, "occupation": occupation_matches,
            "relationship": relationship_whatif, "workclass": workclass_peers}
