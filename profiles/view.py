"""\"Socio-professional profile\" page: the clustering dashboard (7 pages in the left-hand menu).

Reuses the results of the notebook `profiles/notebook/projet_ml_clustering.ipynb` without changing it.
Entry point: `render(t)` (called by app.py).
(Internal names such as `profil`, `taux`, `famille` are French identifiers; everything shown on screen is English.)
"""
from __future__ import annotations

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import pipeline as P
from . import reco as R

COULEURS = ['#2a78d6', '#eb6834', '#1baf7a']
COULEURS_FAMILLE = {'Married': '#6250d6', 'Single': '#e87ba4', 'Divorced or separated': '#eda100', 'Widowed': '#8a8f98'}
GRIS = '#8a8f98'

# ----------------------------------------------------------------------------------------------
# Plain-English labels for the values of the data
# ----------------------------------------------------------------------------------------------
SITUATIONS_FR = {
    'Married-civ-spouse': "Married", 'Married-AF-spouse': "Married", 'Married-spouse-absent': "Married, spouse absent",
    'Never-married': "Single", 'Divorced': "Divorced", 'Separated': "Separated", 'Widowed': "Widowed",
}
FAMILLE4 = {
    'Married-civ-spouse': 'Married', 'Married-AF-spouse': 'Married', 'Married-spouse-absent': 'Married',
    'Never-married': 'Single', 'Divorced': 'Divorced or separated', 'Separated': 'Divorced or separated',
    'Widowed': 'Widowed',
}
EMPLOYEUR_FR = {
    'Private': "Private company", 'Self-emp-not-inc': "Self-employed", 'Self-emp-inc': "Self-employed (incorporated)",
    'Federal-gov': "Federal government", 'State-gov': "State government", 'Local-gov': "Local government",
    'Without-pay': "Volunteer / unpaid", 'Never-worked': "Has never worked", 'Unknown': "Not specified",
}
METIER_FR = {
    'Adm-clerical': "Administrative clerk", 'Exec-managerial': "Management", 'Handlers-cleaners': "Handling / cleaning",
    'Prof-specialty': "Specialised profession (engineer, teacher...)", 'Other-service': "Other services", 'Sales': "Sales",
    'Craft-repair': "Crafts / repair", 'Transport-moving': "Transport", 'Farming-fishing': "Farming / fishing",
    'Machine-op-inspct': "Machine operator", 'Tech-support': "Technical support", 'Protective-serv': "Security / protection",
    'Armed-Forces': "Armed forces", 'Priv-house-serv': "Household worker", 'Unknown': "Not specified",
}
ETUDES_FR = {
    1: "Preschool", 2: "Primary (grades 1 to 4)", 3: "Primary (grades 5 and 6)", 4: "Early middle school (grades 7-8)",
    5: "Middle school (grade 9)", 6: "High school, grade 10", 7: "High school, grade 11", 8: "High school, grade 12, no diploma",
    9: "High-school diploma", 10: "Some college", 11: "Short vocational diploma",
    12: "Associate degree", 13: "Bachelor's degree", 14: "Master's degree",
    15: "Professional school (medicine, law...)", 16: "Doctorate",
}
ORDRE_AGE = ['Under 30', '30-39', '40-49', '50-59', '60 and over']
ORDRE_HEURES = ['Under 35 h', '35 to 45 h', 'Over 45 h']
ORDRE_ETUDES = ['Before high school', 'High-school diploma', 'Short studies (1-2 years)', 'Bachelor', 'Master and above']
REV_BAS, REV_HAUT = "$50,000 or less", "Over $50,000"


def niveau_etudes(m):
    if m < 8.5:
        return "before high school"
    if m < 9.5:
        return "high-school diploma"
    if m < 12.5:
        return "short studies"
    if m < 13.5:
        return "bachelor"
    return "master or above"


# ----------------------------------------------------------------------------------------------
# Loading (done once)
# ----------------------------------------------------------------------------------------------
@st.cache_resource(show_spinner="Preparing the data, one moment...")
def load():
    art = P.build_artifacts()
    seg_map = R.assign_segments(art.profile)                      # {group number: key}
    noms = {c: R.SEGMENTS[k]['nom'] for c, k in seg_map.items()}
    cle_couleur = {'jeunes': COULEURS[0], 'cadres': COULEURS[1], 'seniors': COULEURS[2]}
    couleurs = {noms[c]: cle_couleur[k] for c, k in seg_map.items()}

    v = art.df.copy()
    v['profil'] = v['cluster'].map(noms)
    v['seg_key'] = v['cluster'].map(seg_map)
    v['Sexe'] = v['sex'].map({'Male': 'Male', 'Female': 'Female'})
    v['tranche_age'] = pd.cut(v['age'], [0, 29, 39, 49, 59, 200], labels=ORDRE_AGE).astype(str)
    v['tranche_heures'] = pd.cut(v['hours-per-week'], [0, 34, 45, 200], labels=ORDRE_HEURES).astype(str)
    v['tranche_etudes'] = pd.cut(v['education-num'], [0, 8, 9, 12, 13, 16], labels=ORDRE_ETUDES).astype(str)
    v['employeur'] = v['workclass'].map(EMPLOYEUR_FR).fillna(v['workclass'])
    v['metier'] = v['occupation'].map(METIER_FR).fillna(v['occupation'])
    v['revenu'] = v['income'].map({'<=50K': REV_BAS, '>50K': REV_HAUT})
    v['situation'] = v['marital-status'].map(SITUATIONS_FR)
    v['famille'] = v['marital-status'].map(FAMILLE4)
    return art, seg_map, noms, couleurs, v


art = SEG_MAP = NOMS = COUL = VIEW = N = ORDRE_PROFILS = KEY_PAR_NOM = None


def _init_base():
    global art, SEG_MAP, NOMS, COUL, VIEW, N, ORDRE_PROFILS, KEY_PAR_NOM
    art, SEG_MAP, NOMS, COUL, VIEW = load()
    N = len(VIEW)
    ORDRE_PROFILS = [NOMS[c] for c in sorted(NOMS, key=lambda c: ['jeunes', 'cadres', 'seniors'].index(SEG_MAP[c]))]
    KEY_PAR_NOM = {NOMS[c]: SEG_MAP[c] for c in NOMS}


def style(fig, height=380, legend=True):
    fig.update_layout(template=None, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=height, margin=dict(l=10, r=10, t=30, b=10),
                      showlegend=legend, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""))
    return fig


def nf(x):
    return f"{int(x):,}"


def pct(x, d=0):
    return f"{x * 100:.{d}f}%"


# ----------------------------------------------------------------------------------------------
# Indicators per profile
# ----------------------------------------------------------------------------------------------
def indicateurs(d: pd.DataFrame) -> dict:
    return {
        'age': d['age'].mean(), 'heures': d['hours-per-week'].mean(), 'etudes': d['education-num'].mean(),
        'riches': (d['income'] == '>50K').mean(), 'maries': (d['famille'] == 'Married').mean(),
        'celib': (d['famille'] == 'Single').mean(), 'divorces': (d['famille'] == 'Divorced or separated').mean(),
        'placements': d['has-capital-gain'].mean(),
    }


IND_POP = IND_PROFIL = STD_POP = None


def _init_stats():
    global IND_POP, IND_PROFIL, STD_POP
    IND_POP = indicateurs(VIEW)
    IND_PROFIL = {nom: indicateurs(VIEW[VIEW['profil'] == nom]) for nom in ORDRE_PROFILS}
    STD_POP = {'age': VIEW['age'].std(), 'heures': VIEW['hours-per-week'].std(), 'etudes': VIEW['education-num'].std()}


def traits_distinctifs(nom: str, n: int = 4) -> list[str]:
    ind, pop = IND_PROFIL[nom], IND_POP
    ecart = {}
    for k in ind:
        s = STD_POP[k] if k in STD_POP else (pop[k] * (1 - pop[k])) ** 0.5
        ecart[k] = abs(ind[k] - pop[k]) / s if s else 0
    phrases = {
        'age': lambda: f"{ind['age']:.0f} years old on average (whole population: {pop['age']:.0f})",
        'heures': lambda: f"{ind['heures']:.0f} working hours per week (whole population: {pop['heures']:.0f} h)",
        'etudes': lambda: f"Average education level: {niveau_etudes(ind['etudes'])} (whole population: {niveau_etudes(pop['etudes'])})",
        'riches': lambda: f"{pct(ind['riches'])} earn more than $50,000 a year (whole population: {pct(pop['riches'])})",
        'maries': lambda: f"{pct(ind['maries'])} are married (whole population: {pct(pop['maries'])})",
        'celib': lambda: f"{pct(ind['celib'])} are single (whole population: {pct(pop['celib'])})",
        'divorces': lambda: f"{pct(ind['divorces'])} are divorced or separated (whole population: {pct(pop['divorces'])})",
        'placements': lambda: f"{pct(ind['placements'])} have investment income (whole population: {pct(pop['placements'])})",
    }
    haut = sorted(ecart, key=ecart.get, reverse=True)[:n]
    out = [phrases[k]() for k in haut]
    d = VIEW[VIEW['profil'] == nom]
    out.append(f"Most common occupation: {d['metier'].mode().iloc[0].lower()}")
    return out


# ----------------------------------------------------------------------------------------------
# Outcomes to study and factors (for "Why?" and "Family")
# ----------------------------------------------------------------------------------------------
def deja_maries(d):
    return d['marital-status'] != 'Never-married'


RESULTATS = {
    "Earns more than $50,000 a year": (None, lambda d: d['income'] == '>50K'),
    "Is married": (None, lambda d: d['famille'] == 'Married'),
    "Is single": (None, lambda d: d['famille'] == 'Single'),
    "Is divorced or separated (among people who have ever been married)":
        (deja_maries, lambda d: d['famille'] == 'Divorced or separated'),
    "Is widowed (among people who have ever been married)":
        (deja_maries, lambda d: d['famille'] == 'Widowed'),
    "Has investment income": (None, lambda d: d['has-capital-gain'] == 1),
}
FACTEURS = {
    "Profile": ('profil', ORDRE_PROFILS), "Age": ('tranche_age', ORDRE_AGE),
    "Education level": ('tranche_etudes', ORDRE_ETUDES), "Working hours": ('tranche_heures', ORDRE_HEURES),
    "Income": ('revenu', [REV_BAS, REV_HAUT]), "Occupation": ('metier', None), "Employer type": ('employeur', None),
}


def taux_par_groupe(resultat: str, facteur: str, min_n: int = 200):
    sel, cible = RESULTATS[resultat]
    d = VIEW if sel is None else VIEW[sel(VIEW)]
    d = d.assign(_y=cible(d).astype(int))
    col, ordre = FACTEURS[facteur]
    t = d.groupby(col).agg(taux=('_y', 'mean'), n=('_y', 'size')).reset_index()
    t = t[t['n'] >= min_n]
    return d, t, col, ordre


def classement_facteurs(resultat: str, min_n: int = 200) -> pd.DataFrame:
    """Factors sorted by the gap between the most and the least affected group."""
    lignes = []
    for fac in FACTEURS:
        if fac == "Income" and resultat.startswith("Earns"):
            continue
        d, t, col, _ = taux_par_groupe(resultat, fac, min_n)
        if len(t) < 2:
            continue
        lo, hi = t.loc[t['taux'].idxmin()], t.loc[t['taux'].idxmax()]
        lignes.append({'Factor': fac, 'Gap (points)': (hi['taux'] - lo['taux']) * 100,
                       'bas': lo['taux'], 'bas_nom': lo[col], 'haut': hi['taux'], 'haut_nom': hi[col]})
    return pd.DataFrame(lignes).sort_values('Gap (points)', ascending=False).reset_index(drop=True)


def graphique_taux(resultat: str, facteur: str, min_n: int = 200, hauteur=None):
    d, t, col, ordre = taux_par_groupe(resultat, facteur, min_n)
    moyenne = d['_y'].mean()
    if ordre:
        t[col] = pd.Categorical(t[col], categories=ordre, ordered=True)
        t = t.sort_values(col)
    else:
        t = t.sort_values('taux', ascending=True)
    fig = px.bar(t, x='taux', y=col, orientation='h', text=t['taux'].map(lambda v: f"{v:.0%}"),
                 hover_data={'n': True, 'taux': ':.1%'}, color_discrete_sequence=[COULEURS[0]])
    fig.add_vline(x=moyenne, line_dash="dash", line_color=GRIS, annotation_text=f"Average: {moyenne:.0%}", annotation_position="top")
    fig.update_xaxes(tickformat=".0%", title=None, range=[0, max(t['taux'].max(), moyenne) * 1.2])
    fig.update_yaxes(title=None, autorange="reversed" if ordre else True)
    fig.update_traces(textposition="outside", cliponaxis=False)
    return style(fig, hauteur or max(260, 70 + 38 * len(t)), legend=False), moyenne, t, col


def phrase_classement(r) -> str:
    return (f"**{r['Factor']}**: from {r['bas']:.0%} ({str(r['bas_nom']).lower()}) "
            f"to {r['haut']:.0%} ({str(r['haut_nom']).lower()})")


# ----------------------------------------------------------------------------------------------
# User's choice (left sidebar)
# ----------------------------------------------------------------------------------------------
def audience_choisie() -> str:
    return st.session_state.get('audience', 'banque')


# ----------------------------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------------------------
def page_accueil():
    aud = audience_choisie()
    st.title("Know the population better to act better")
    st.markdown(f"**{R.AUDIENCES[aud]}**: {R.AUDIENCE_INTRO[aud]}")
    st.caption(f"{nf(N)} people analysed (1994 US census). "
               "They were automatically grouped into 3 profiles of similar people.")

    a, b, c, d = st.columns(4)
    a.metric("People analysed", nf(N))
    b.metric("Profiles identified", len(ORDRE_PROFILS))
    c.metric("Earn more than $50,000 a year", pct(IND_POP['riches']))
    d.metric("Are married", pct(IND_POP['maries']))

    st.subheader("The 3 profiles at a glance")
    cols = st.columns(3)
    for col, nom in zip(cols, ORDRE_PROFILS):
        ind = IND_PROFIL[nom]
        with col.container(border=True):
            st.markdown(f"### {nom}")
            st.markdown(f"**{pct(len(VIEW[VIEW['profil'] == nom]) / N)} of the population** ({nf((VIEW['profil'] == nom).sum())} people)")
            st.markdown(R.SEGMENTS[KEY_PAR_NOM[nom]]['resume'])
            st.markdown(f"- Average age: **{ind['age']:.0f}**\n"
                        f"- Earn more than $50,000: **{pct(ind['riches'])}**\n"
                        f"- Married: **{pct(ind['maries'])}**")

    st.subheader("What can you do here?")
    st.markdown(
        "- **Who are our audiences?** Understand each profile in a few figures.\n"
        "- **Family and marriage**: where are the most divorced, single or married people?\n"
        "- **Why? The factors**: which factors (age, education, occupation...) make a result vary the most.\n"
        "- **What to offer?** An action plan per profile, or advice for one specific person.\n"
        "- **Find a specific audience**: filter, count, download the list.\n"
        "- **Reliability and method**: how far the results can be trusted.")
    st.info("Choose your type of organisation in the left sidebar: the advice adapts to it.")


def page_publics():
    st.title("Who are our audiences?")
    st.markdown("Each profile is a group of people who are alike in age, education, work and income.")

    indic = [('age', "Average age (years)", ".0f"), ('heures', "Working hours per week", ".0f"),
             ('riches', "Earn more than $50,000", ".0%"), ('maries', "Are married", ".0%")]
    cols = st.columns(4)
    for col, (k, titre, fmt) in zip(cols, indic):
        t = pd.DataFrame({'profil': ORDRE_PROFILS, 'v': [IND_PROFIL[n][k] for n in ORDRE_PROFILS]})
        fig = px.bar(t, x='profil', y='v', color='profil', color_discrete_map=COUL, text=t['v'].map(lambda x, f=fmt: format(x, f)),
                     category_orders={'profil': ORDRE_PROFILS}, title=titre)
        fig.update_xaxes(title=None, showticklabels=False)
        fig.update_yaxes(title=None, visible=False, range=[0, t['v'].max() * 1.25])
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(title_font_size=14)
        col.plotly_chart(style(fig, 280, legend=False), width="stretch")
    legend = " · ".join(f":blue[■] {n}" if i == 0 else (f":orange[■] {n}" if i == 1 else f":green[■] {n}")
                        for i, n in enumerate(ORDRE_PROFILS))
    st.caption(legend)

    for nom in ORDRE_PROFILS:
        d = VIEW[VIEW['profil'] == nom]
        with st.container(border=True):
            st.markdown(f"### {nom}  \n:gray[{pct(len(d) / N)} of the population · {nf(len(d))} people]")
            a, b = st.columns([2, 3])
            with a:
                st.markdown(f"**In short**  \n{R.SEGMENTS[KEY_PAR_NOM[nom]]['resume']}")
                st.markdown(f"**Most common employer type:** {d['employeur'].mode().iloc[0].lower()}")
            with b:
                st.markdown("**What sets it apart**")
                for s in traits_distinctifs(nom):
                    st.markdown(f"- {s}")
    st.info(R.NOTE_CAUSALITE_SIMPLE)


def page_famille():
    st.title("Family and marriage")
    st.markdown("Marital status was **not** used to form the profiles. Here is how it is spread within each one.")

    ordre_f = list(COULEURS_FAMILLE)
    pop = VIEW['famille'].value_counts(normalize=True)
    cols = st.columns(4)
    for col, f in zip(cols, ordre_f):
        col.metric(f, pct(pop.get(f, 0)))

    t = pd.crosstab(VIEW['profil'], VIEW['famille'], normalize='index')[ordre_f].reindex(ORDRE_PROFILS)
    t.loc['Whole population'] = pop.reindex(ordre_f)
    long = t.reset_index().melt(id_vars='profil', var_name='Status', value_name='part')
    fig = px.bar(long, x='part', y='profil', color='Status', orientation='h', color_discrete_map=COULEURS_FAMILLE,
                 category_orders={'profil': list(t.index), 'Status': ordre_f},
                 text=long['part'].map(lambda v: f"{v:.0%}" if v >= 0.04 else ""))
    fig.update_xaxes(tickformat=".0%", title=None)
    fig.update_yaxes(title=None, autorange="reversed")
    fig.update_traces(textposition="inside")
    st.plotly_chart(style(fig, 330), width="stretch")

    st.subheader("What we observe")
    for nom in ORDRE_PROFILS:
        d = VIEW[VIEW['profil'] == nom]
        part = d['famille'].value_counts(normalize=True)
        meilleur = max(ordre_f, key=lambda f: part.get(f, 0) / pop[f])
        st.markdown(f"- **{nom}**: {pct(part.get(meilleur, 0))} are \"{meilleur.lower()}\" "
                    f"versus {pct(pop[meilleur])} in the whole population.")
    pur = art.metrics['purete']
    base = art.metrics['purete_base']
    st.caption(f"Limit: if we guessed marital status from the profile alone, we would be wrong for about "
               f"{round((1 - pur) * 10)} people out of 10 (versus {round((1 - base) * 10)} out of 10 by saying everyone is married). "
               "The profile helps, but it does not replace the real information.")

    st.divider()
    st.subheader("Focus: divorce and separation")
    res = "Is divorced or separated (among people who have ever been married)"
    d_ref = VIEW[deja_maries(VIEW)]
    taux = (d_ref['famille'] == 'Divorced or separated').mean()
    st.markdown(f"Among people who have ever been married, **{pct(taux)}** are now divorced or separated. "
                "Here is where this rate is highest, and the factors that go with it.")
    fig, moyenne, tt, col = graphique_taux(res, "Profile")
    classement = classement_facteurs(res)
    a, b = st.columns(2)
    with a:
        st.markdown("**By profile**")
        st.plotly_chart(fig, width="stretch")
    with b:
        st.markdown("**By age**")
        fig2, *_ = graphique_taux(res, "Age")
        st.plotly_chart(fig2, width="stretch")
    st.markdown("**The factors that make this rate vary the most:**")
    for _, r in classement.head(3).iterrows():
        st.markdown(f"- {phrase_classement(r)}")
    aud = audience_choisie()
    conseil = {
        'banque': "Offer a review of contracts (beneficiaries, life insurance) and budget to customers whose family situation changes.",
        'rh': "Offer a listening ear, social support and more flexible hours to employees going through a separation.",
        'public': "Strengthen social and legal support, and help for single-parent families.",
    }[aud]
    st.success(f"**For a {R.AUDIENCES[aud].lower()}:** {conseil}")
    st.info(R.NOTE_CAUSALITE_SIMPLE)


def page_pourquoi():
    st.title("Why? The factors that matter")
    st.markdown("Choose an outcome: the chart ranks the factors (age, education, occupation...) by their effect on that outcome.")
    res = st.selectbox("Outcome to study", list(RESULTATS))
    classement = classement_facteurs(res)

    st.subheader("The factors that make this outcome vary the most")
    fig = px.bar(classement, x='Gap (points)', y='Factor', orientation='h', color_discrete_sequence=[COULEURS[0]],
                 text=classement['Gap (points)'].map(lambda v: f"{v:.0f} points"))
    fig.update_yaxes(title=None, autorange="reversed", categoryorder="array", categoryarray=list(classement['Factor']))
    fig.update_xaxes(title="Gap between the most and the least affected group (in percentage points)",
                     range=[0, classement['Gap (points)'].max() * 1.2])
    fig.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(style(fig, 60 + 42 * len(classement), legend=False), width="stretch")
    st.markdown("**Key points:**")
    for _, r in classement.head(3).iterrows():
        st.markdown(f"- {phrase_classement(r)}")

    st.subheader("See the detail of one factor")
    fac = st.selectbox("Factor", list(classement['Factor']))
    fig, moyenne, t, col = graphique_taux(res, fac)
    st.plotly_chart(fig, width="stretch")
    top, bas = t.sort_values('taux').iloc[-1], t.sort_values('taux').iloc[0]
    st.markdown(f"**Reading:** on average {moyenne:.0%} of people are concerned. It is most frequent for "
                f"**{str(top[col]).lower()}** ({top['taux']:.0%}) and least frequent for **{str(bas[col]).lower()}** ({bas['taux']:.0%}).")
    st.caption("Groups of fewer than 200 people are not shown, because their figures would be unreliable.")
    st.info(R.NOTE_CAUSALITE_SIMPLE)


PRESETS = {
    "Custom": dict(age=35, workclass='Private', edu=9, occupation='Sales', sex='Male', hours=40,
                         income='<=50K', gain=False, loss=False),
    "Young employee": dict(age=25, workclass='Private', edu=9, occupation='Adm-clerical', sex='Female', hours=35,
                          income='<=50K', gain=False, loss=False),
    "Graduate executive": dict(age=42, workclass='Private', edu=14, occupation='Prof-specialty', sex='Male', hours=50,
                          income='>50K', gain=True, loss=False),
    "Employee close to retirement": dict(age=58, workclass='Private', edu=8, occupation='Craft-repair', sex='Male', hours=38,
                                          income='<=50K', gain=False, loss=False),
}
FIABILITE = {"nette": "Very sure", "moyenne": "Fairly sure", "ambiguë": "To check: close to another profile"}


def plan_en_tableau(aud: str) -> pd.DataFrame:
    lignes = []
    for nom in ORDRE_PROFILS:
        besoin, actions = R.plan_for(aud, KEY_PAR_NOM[nom])
        n = int((VIEW['profil'] == nom).sum())
        for a, w in actions:
            lignes.append({'Profile': nom, 'People': n, 'Main need': besoin, 'Recommended action': a, 'Why': w})
    return pd.DataFrame(lignes)


def onglet_plan(aud: str):
    st.markdown(f"Action plan for a **{R.AUDIENCES[aud].lower()}**: a list of actions for each of the 3 profiles.")
    for nom in ORDRE_PROFILS:
        besoin, actions = R.plan_for(aud, KEY_PAR_NOM[nom])
        n = int((VIEW['profil'] == nom).sum())
        with st.container(border=True):
            st.markdown(f"### {nom}  \n:gray[{nf(n)} people · {pct(n / N)} of the population]")
            st.markdown(f"**Main need:** {besoin}")
            for a, w in actions:
                st.markdown(f"- **{a}**  \n  :gray[{w}]")
    st.download_button("Download the action plan (Excel / CSV)", plan_en_tableau(aud).to_csv(index=False, sep=';').encode('utf-8-sig'),
                       file_name="action_plan.csv", mime="text/csv")
    st.caption(R.NOTE_EQUITE_SIMPLE)


def onglet_personne(aud: str):
    st.markdown("Describe a person: the dashboard finds the profile they are closest to and suggests suitable actions.")
    ex = st.selectbox("Start from an example", list(PRESETS))
    p0 = PRESETS[ex]
    col_in, col_out = st.columns([1, 2])
    with col_in:
        st.subheader("The person")
        age = st.slider("Age", 17, 90, p0['age'], key=f"age-{ex}")
        edu = st.selectbox("Education level", list(ETUDES_FR), index=list(ETUDES_FR).index(p0['edu']),
                           format_func=lambda n: ETUDES_FR[n], key=f"edu-{ex}")
        wcs = sorted(art.df['workclass'].unique(), key=lambda w: EMPLOYEUR_FR.get(w, w))
        wc = st.selectbox("Employer type", wcs, index=wcs.index(p0['workclass']),
                          format_func=lambda w: EMPLOYEUR_FR.get(w, w), key=f"wc-{ex}")
        occs = sorted(art.df['occupation'].unique(), key=lambda o: METIER_FR.get(o, o))
        occ = st.selectbox("Occupation", occs, index=occs.index(p0['occupation']),
                           format_func=lambda o: METIER_FR.get(o, o), key=f"occ-{ex}")
        hours = st.slider("Working hours per week", 1, 99, p0['hours'], key=f"h-{ex}")
        inc = st.radio("Income per year", ['<=50K', '>50K'], index=['<=50K', '>50K'].index(p0['income']), horizontal=True,
                       format_func=lambda s: REV_BAS if s == '<=50K' else REV_HAUT, key=f"inc-{ex}")
        gain = st.checkbox("Has investment income (shares, property...)", p0['gain'], key=f"g-{ex}")
        loss = st.checkbox("Has had investment losses", p0['loss'], key=f"l-{ex}")
        sex = st.radio("Sex", ['Male', 'Female'], index=['Male', 'Female'].index(p0['sex']), horizontal=True,
                       format_func=lambda s: {'Male': 'Male', 'Female': 'Female'}[s], key=f"sex-{ex}",
                       help="Only used to find the closest profile. It never influences the proposed actions.")
        sit = st.selectbox("Marital status (if known)", ['Unknown'] + list(SITUATIONS_FR),
                           format_func=lambda s: s if s == 'Unknown' else SITUATIONS_FR[s], key=f"sit-{ex}")

    person = {'age': age, 'workclass': wc, 'education-num': int(edu), 'occupation': occ, 'sex': sex,
              'hours-per-week': hours, 'income': inc, 'has_gain': gain, 'has_loss': loss}
    res = P.predict_person(art, person)
    c = res['cluster']
    key = SEG_MAP[c]

    with col_out:
        st.subheader("Result")
        a, b = st.columns(2)
        a.metric("This person's profile", NOMS[c])
        b.metric("Reliability of this match", FIABILITE[res['confiance']].split(":")[0],
                 help="\"To check\": the person is almost as close to another profile.")
        if res['confiance'] == 'ambiguë':
            st.warning("This person is almost as close to another profile: check before acting.")
        st.markdown(f"> {R.SEGMENTS[key]['resume']}")

        st.subheader("Recommended actions")
        sit_val = None if sit == 'Unknown' else sit
        for r in R.advice_for(aud, person, key, sit_val):
            st.markdown(f"**{r['action']}**  \n:gray[{r['pourquoi']}  ·  {r['origine']}]")
        st.caption(R.NOTE_EQUITE_SIMPLE)

        with st.expander("See people who are similar"):
            v = art.df.iloc[res['voisins']][['age', 'workclass', 'education-num', 'occupation', 'hours-per-week', 'income']].copy()
            v['workclass'] = v['workclass'].map(EMPLOYEUR_FR)
            v['occupation'] = v['occupation'].map(METIER_FR)
            v['education-num'] = v['education-num'].map(ETUDES_FR)
            v['income'] = v['income'].map({'<=50K': REV_BAS, '>50K': REV_HAUT})
            v.columns = ['Age', 'Employer', 'Education', 'Occupation', 'Hours per week', 'Income per year']
            st.dataframe(v, width="stretch", hide_index=True)


def page_recommandations():
    aud = audience_choisie()
    st.title("What to offer? Recommendations")
    st.caption(f"Type of organisation chosen: {R.AUDIENCES[aud]} (change it in the left sidebar).")
    t1, t2 = st.tabs(["Action plan per profile", "Advice for one person"])
    with t1:
        onglet_plan(aud)
    with t2:
        onglet_personne(aud)


def page_chercher():
    aud = audience_choisie()
    st.title("Find a specific audience")
    st.markdown("Filter the population, see how many people are concerned and what can be offered to them.")
    ages = (int(VIEW['age'].min()), int(VIEW['age'].max()))
    hs = (int(VIEW['hours-per-week'].min()), int(VIEW['hours-per-week'].max()))
    with st.expander("Filters", expanded=True):
        a, b, c = st.columns(3)
        age = a.slider("Age", ages[0], ages[1], ages)
        heures = a.slider("Working hours per week", hs[0], hs[1], hs)
        revenu = b.multiselect("Income per year", [REV_BAS, REV_HAUT], default=[REV_BAS, REV_HAUT])
        fam = b.multiselect("Marital status", list(COULEURS_FAMILLE), placeholder="All")
        emp = c.multiselect("Employer type", sorted(VIEW['employeur'].unique()), placeholder="All")
        met = c.multiselect("Occupation", sorted(VIEW['metier'].unique()), placeholder="All")
    sel = VIEW[VIEW['age'].between(*age) & VIEW['hours-per-week'].between(*heures) & VIEW['revenu'].isin(revenu)]
    if fam:
        sel = sel[sel['famille'].isin(fam)]
    if emp:
        sel = sel[sel['employeur'].isin(emp)]
    if met:
        sel = sel[sel['metier'].isin(met)]
    if sel.empty:
        st.warning("No one matches these filters.")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("People concerned", nf(len(sel)))
    k2.metric("Share of the population", pct(len(sel) / N, 1))
    k3.metric("Average age", f"{sel['age'].mean():.0f}", delta=f"{sel['age'].mean() - IND_POP['age']:+.0f} years vs whole population")
    k4.metric("Earn more than $50,000", pct((sel['income'] == '>50K').mean()),
              delta=f"{((sel['income'] == '>50K').mean() - IND_POP['riches']) * 100:+.0f} points vs whole population")

    g, d = st.columns(2)
    with g:
        st.subheader("Split by profile")
        t = pd.concat([sel['profil'].value_counts(normalize=True).rename('This audience'),
                       VIEW['profil'].value_counts(normalize=True).rename('Whole population')], axis=1).reset_index()
        t = t.melt(id_vars='profil', var_name='Group', value_name='part')
        fig = px.bar(t, x='profil', y='part', color='Group', barmode='group',
                     color_discrete_map={'This audience': COULEURS[0], 'Whole population': '#c9ccd1'},
                     category_orders={'profil': ORDRE_PROFILS}, text=t['part'].map(lambda v: f"{v:.0%}"))
        fig.update_yaxes(tickformat=".0%", title=None, range=[0, 1.1])
        fig.update_xaxes(title=None)
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(style(fig, 360), width="stretch")
    with d:
        st.subheader("Marital status")
        t = pd.concat([sel['famille'].value_counts(normalize=True).rename('This audience'),
                       VIEW['famille'].value_counts(normalize=True).rename('Whole population')], axis=1).fillna(0)
        t = t.reindex(list(COULEURS_FAMILLE)).reset_index().rename(columns={'famille': 'Status'})
        t = t.melt(id_vars='Status', var_name='Group', value_name='part')
        fig = px.bar(t, x='Status', y='part', color='Group', barmode='group',
                     color_discrete_map={'This audience': COULEURS[0], 'Whole population': '#c9ccd1'},
                     text=t['part'].map(lambda v: f"{v:.0%}"))
        fig.update_yaxes(tickformat=".0%", title=None, range=[0, 1.1])
        fig.update_xaxes(title=None)
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(style(fig, 360), width="stretch")

    dominant = sel['profil'].value_counts().index[0]
    part_dom = sel['profil'].value_counts(normalize=True).iloc[0]
    besoin, actions = R.plan_for(aud, KEY_PAR_NOM[dominant])
    st.subheader("What to offer this audience?")
    st.markdown(f"This audience mostly belongs to the **{dominant}** profile ({pct(part_dom)}). "
                f"Main need: {besoin}")
    for a, w in actions[:3]:
        st.markdown(f"- **{a}**  \n  :gray[{w}]")

    table = sel[['age', 'employeur', 'tranche_etudes', 'metier', 'hours-per-week', 'revenu', 'situation', 'profil']].rename(columns={
        'age': 'Age', 'employeur': 'Employer', 'tranche_etudes': 'Education', 'metier': 'Occupation',
        'hours-per-week': 'Hours per week', 'revenu': 'Income per year', 'situation': 'Marital status', 'profil': 'Profile'})
    st.subheader("The list")
    st.dataframe(table.head(500), width="stretch", hide_index=True)
    st.caption("The first 500 rows are shown; the downloaded file contains the whole selection.")
    st.download_button("Download the list (Excel / CSV)", table.to_csv(index=False, sep=';').encode('utf-8-sig'),
                       file_name="selected_audience.csv", mime="text/csv")


def page_methode():
    st.title("Reliability and method")
    st.subheader("Where do the figures come from?")
    st.markdown(
        f"- The data comes from a 1994 US census ({nf(N)} adults). Amounts are in dollars of that time.\n"
        "- A program automatically grouped similar people (age, education, work, income, investments) "
        "into **3 profiles**. Nobody decided by hand who goes into which group.\n"
        "- Marital status was not used to form the groups: it is only used to describe them.")

    st.subheader("Can it be trusted?")
    stab = None
    try:
        s = pd.read_csv(P.CACHE / 'stabilite_k.csv')
        stab = float(s.loc[s['k'] == P.K, 'ARI min'].iloc[0])
    except Exception:
        pass
    if stab is not None:
        st.success(f"**Yes for the profiles.** When the grouping is redone several times from different starting points, "
                   f"the same groups are found {stab * 100:.1f}% of the time.")
    pur, base = art.metrics['purete'], art.metrics['purete_base']
    st.warning(f"**With caution for marital status.** The profiles look more like life stages (young, executive, senior) "
               f"than family situations. Guessing marital status from the profile gives the right answer {round(pur * 10)} times out of 10 "
               f"(versus {round(base * 10)} out of 10 with no information at all).")

    st.subheader("Limits to know")
    st.markdown(
        "- **Association is not causation**: we see what goes together, not what causes what.\n"
        "- **Old, US data**: confirm with recent data from your own country before deciding.\n"
        "- **The proposed actions are starting ideas**: they come from business reasoning, not from a history of purchases or results. "
        "They must be tested and their effect measured.\n"
        f"- **Fairness**: {R.NOTE_EQUITE_SIMPLE}")

    st.subheader("Link with the notebook")
    st.markdown("This dashboard reuses the results of the project notebook, **without changing it**.")
    cmp = P.compare_with_notebook(art)
    if cmp is not None:
        if bool(cmp['Identical'].all()):
            st.success(f"The {len(cmp)} figures checked are identical to those of the notebook.")
        else:
            st.error("Some figures differ from the notebook: it may have been modified or rerun with other data.")
        with st.expander("Technical details (optional)"):
            show = cmp.copy()
            show['Identical'] = show['Identical'].map({True: "Yes", False: "No"})
            st.dataframe(show, width="stretch", hide_index=True)
            concl = P.notebook_conclusion(P.read_notebook())
            if concl:
                st.markdown("**Conclusion written in the notebook**")
                st.markdown(concl)
            st.download_button("Download the notebook", P.NOTEBOOK_PATH.read_bytes(), file_name="projet_ml_clustering.ipynb")
    else:
        st.warning("Notebook not found: put `projet_ml_clustering.ipynb` in the `notebook/` folder.")


PAGES = {
    "Home": page_accueil,
    "Who are our audiences?": page_publics,
    "Family and marriage": page_famille,
    "Why? The factors": page_pourquoi,
    "What to offer?": page_recommandations,
    "Find a specific audience": page_chercher,
    "Reliability and method": page_methode,
}

MENU_ICONS = {
    "Home": ":material/home:",
    "Who are our audiences?": ":material/groups:",
    "Family and marriage": ":material/family_restroom:",
    "Why? The factors": ":material/query_stats:",
    "What to offer?": ":material/lightbulb:",
    "Find a specific audience": ":material/person_search:",
    "Reliability and method": ":material/verified:",
}


def render(t=None):
    """Shows the dashboard: menu in the left sidebar, chosen page in the main area."""
    _init_base()
    _init_stats()
    with st.sidebar:
        with st.container(key="profilenav"):
            st.markdown('<div class="side-title">Know the population</div>', unsafe_allow_html=True)
            st.markdown('<div class="side-label">I am...</div>', unsafe_allow_html=True)
            st.radio("I am...", list(R.AUDIENCES), format_func=R.AUDIENCES.get, key='audience',
                     label_visibility="collapsed",
                     help="The advice and recommendations adapt to your type of organisation.")
            st.markdown('<div class="side-label">Menu</div>', unsafe_allow_html=True)
            page = st.radio("Menu", list(PAGES), key="profiles_menu", label_visibility="collapsed",
                            format_func=lambda p: f"{MENU_ICONS[p]} {p}")
            st.markdown('<div class="side-note">Based on the project notebook, without changing it.</div>',
                        unsafe_allow_html=True)
    PAGES[page]()
    st.caption("Educational project on a 1994 US census. Profiles are statistical tendencies "
               "and reflect the biases in the data: they must not be used to make real decisions.")
