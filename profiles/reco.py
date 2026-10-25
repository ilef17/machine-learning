"""Segment interpretation and recommendation system.

Important: the data contains no purchase or click history. The recommendation system is therefore RULE-BASED:
a catalogue of offers per segment, plus a few individual rules. The catalogue is a business assumption
(bank / insurance), not a result computed from the data.

(Internal keys such as 'jeunes', 'cadres', 'seniors', 'nom', 'offre' are kept as identifiers; only the text is English.)
"""
from __future__ import annotations

import pandas as pd

# ----------------------------------------------------------------------------------------------
# 1) Name each cluster from its profile (not from its number)
# ----------------------------------------------------------------------------------------------
SEGMENTS = {
    'jeunes': {
        'nom': "Young professionals",
        'resume': "Early career, modest income, mostly single. "
                  "Main need: starting simply (low fees, small savings, first loan).",
    },
    'cadres': {
        'nom': "Graduate executives",
        'resume': "Graduates, long working weeks, high income, most often married. "
                  "Main need: long-term projects (property, retirement, wealth).",
    },
    'seniors': {
        'nom': "Experienced seniors",
        'resume': "End of career, mostly manual trades, lower qualifications, average income. "
                  "Main need: security (retirement, health, savings).",
    },
}


def assign_segments(profile: pd.DataFrame) -> dict[int, str]:
    """Returns {cluster number: segment key}. Rules: highest income = cadres,
    youngest of the others = jeunes, the rest = seniors."""
    ids = list(profile.index)
    if len(ids) != 3:
        return {i: f"autre{i}" for i in ids}
    cadres = profile['pct_revenu_sup50k'].idxmax()
    reste = [i for i in ids if i != cadres]
    jeunes = profile.loc[reste, 'age_moyen'].idxmin()
    seniors = [i for i in reste if i != jeunes][0]
    return {int(cadres): 'cadres', int(jeunes): 'jeunes', int(seniors): 'seniors'}


def segment_name(key: str, cluster: int) -> str:
    return SEGMENTS.get(key, {}).get('nom', f"Cluster {cluster}")


# ----------------------------------------------------------------------------------------------
# 2) Automatic interpretation: what sets each segment apart?
# ----------------------------------------------------------------------------------------------
def describe_segments(profile: pd.DataFrame, df: pd.DataFrame) -> dict[int, list[str]]:
    """For each cluster: the 4 characteristics that differ most from the population."""
    pop = {
        'age_moyen': (df['age'].mean(), df['age'].std()),
        'education_moy': (df['education-num'].mean(), df['education-num'].std()),
        'heures_moy': (df['hours-per-week'].mean(), df['hours-per-week'].std()),
        'pct_hommes': ((df['sex'] == 'Male').mean(), None),
        'pct_revenu_sup50k': ((df['income'] == '>50K').mean(), None),
        'pct_gain_capital': (df['has-capital-gain'].mean(), None),
    }

    def z(col, val):
        m, s = pop[col]
        s = s if s is not None else (m * (1 - m)) ** 0.5
        return (val - m) / s

    def phrase(col, val):
        m = pop[col][0]
        if col == 'age_moyen':
            return f"Average age of {val:.1f} years (population: {m:.1f} years)"
        if col == 'education_moy':
            return f"Average education level of {val:.1f} (population: {m:.1f}, on a scale of 1 to 16)"
        if col == 'heures_moy':
            return f"{val:.0f} hours per week (population: {m:.0f} h)"
        if col == 'pct_hommes':
            return f"{val:.0%} men (population: {m:.0%})"
        if col == 'pct_revenu_sup50k':
            return f"{val:.0%} with income above $50,000 (population: {m:.0%})"
        return f"{val:.0%} have a capital gain (population: {m:.0%})"

    out = {}
    for c, row in profile.iterrows():
        scores = sorted(((abs(z(col, row[col])), col) for col in pop), reverse=True)[:4]
        bullets = [phrase(col, row[col]) for _, col in scores]
        bullets.append(f"Most common occupation: {row['metier_dominant']}; "
                       f"most common employer type: {row['workclass_dominant']}")
        out[int(c)] = bullets
    return out


def marital_lifts(df: pd.DataFrame, min_share: float = 0.03) -> list[dict]:
    """For each cluster: the marital status most over-represented compared with the population."""
    pop = df['marital-status'].value_counts(normalize=True)
    cross = pd.crosstab(df['cluster'], df['marital-status'], normalize='index')
    res = []
    for c in cross.index:
        best = None
        for situation, share in cross.loc[c].items():
            if pop[situation] < min_share:
                continue
            lift = share / pop[situation]
            if best is None or lift > best['lift']:
                best = {'cluster': int(c), 'situation': situation, 'part_cluster': share,
                        'part_population': pop[situation], 'lift': lift}
        res.append(best)
    return res


# ----------------------------------------------------------------------------------------------
# 3) Recommendation system (rules): catalogue per segment
# ----------------------------------------------------------------------------------------------
CATALOGUE = {
    'jeunes': [
        ("Fee-free youth account + debit card", "Income still modest: keep banking fees low."),
        ("Automatic savings (round-up on purchases, small monthly transfer)", "Build the habit of saving small amounts."),
        ("Small first loan (equipment, vehicle)", "Early career: first financing needs."),
        ("Tenant home insurance + phone insurance", "Young profile, often renting."),
    ],
    'cadres': [
        ("Mortgage on negotiated terms", "High income and stable situation: a property project is likely."),
        ("Life insurance / retirement savings plan", "Strong saving capacity, long-term horizon."),
        ("Premium card (travel insurance included)", "High income and long working weeks."),
        ("Wealth management with a dedicated adviser", "Assets and income that justify personal follow-up."),
    ],
    'seniors': [
        ("Supplementary pension / annuity", "End of career: prepare retirement income."),
        ("Supplementary health insurance", "Health needs increase with age."),
        ("Secure savings (savings account, term deposit)", "Preference for risk-free investments."),
        ("Home improvement / renovation loan", "Owners who can finance adapting their home."),
    ],
    'autre': [
        ("Personal review with an adviser", "Segment not described in the catalogue."),
    ],
}


def recommend(person: dict, seg_key: str, situation: str | None = None) -> list[dict]:
    """Recommendations for one person: offers of the segment + individual rules.

    Sex is NEVER used in the individual rules (see NOTE_EQUITE).
    """
    recs = [{'offre': o, 'pourquoi': w, 'origine': "Segment"}
            for o, w in CATALOGUE.get(seg_key, CATALOGUE['autre'])]

    if person.get('has_gain'):
        recs.append({'offre': "Investment advice (securities)",
                     'pourquoi': "A declared capital gain shows investment activity.",
                     'origine': "Individual rule"})
    if person['age'] < 35 and person['education-num'] >= 13:
        recs.append({'offre': "First-time buyer mortgage",
                     'pourquoi': "Young higher-education graduate: strong income potential.",
                     'origine': "Individual rule"})
    if person['hours-per-week'] >= 50:
        recs.append({'offre': "Income protection insurance (sick leave, disability)",
                     'pourquoi': "Very high workload: protect income in case of absence.",
                     'origine': "Individual rule"})
    if person['age'] >= 55:
        recs.append({'offre': "Personal retirement review",
                     'pourquoi': "Close to retirement age.",
                     'origine': "Individual rule"})
    if str(person.get('workclass', '')).startswith('Self-emp'):
        recs.append({'offre': "Business account + business insurance",
                     'pourquoi': "Self-employed worker.",
                     'origine': "Individual rule"})

    # Marital status: only if the customer declared it
    if situation in MARIES_LABELS:
        recs.append({'offre': "Family insurance / home protection",
                     'pourquoi': "Declared status: married.", 'origine': "Declared status"})
    elif situation in ('Divorced', 'Separated', 'Widowed'):
        recs.append({'offre': "Review of contracts (beneficiaries, life insurance) and budget",
                     'pourquoi': "Declared status: change in family situation.",
                     'origine': "Declared status"})
    return recs


MARIES_LABELS = ('Married-civ-spouse', 'Married-AF-spouse', 'Married-spouse-absent')

NOTE_EQUITE = (
    "Sex is never used in the rules that choose the offers. However, it is one of the clustering "
    "variables (as in the notebook): it therefore indirectly influences the assigned segment. "
    "Marital status is only used if the customer declared it."
)

NOTE_CAUSALITE = (
    "These are **observed associations** in 1994 US census data. "
    "They show which factors go together, not what **causes** what. "
    "For example, a high rate in a group does not prove that the factor studied is the reason."
)


# ==============================================================================================
# 4) "General public" version: three types of users, one action plan per profile
# ==============================================================================================
AUDIENCES = {
    'banque': "Bank or insurer",
    'rh': "Employer (human resources)",
    'public': "Ministry or public body",
}

AUDIENCE_INTRO = {
    'banque': "Spot the main types of customers to offer them the right products: savings, credit, insurance, retirement.",
    'rh': "Better understand your teams to train them, retain them and adapt working conditions.",
    'public': "Spot who needs which support (jobs, training, health, family) to guide public programmes.",
}

# For each type of user and each profile: the main need + the recommended actions
PLAN = {
    'banque': {
        'jeunes': ("Start simply: low fees, small savings, first loan.", [
            ("Fee-free youth account + debit card", "Income still modest: keep banking fees low."),
            ("Automatic savings (small transfer every month)", "Build the habit of saving small amounts."),
            ("Small first loan (equipment, vehicle)", "Early career: first financing needs."),
            ("Tenant home insurance + phone insurance", "Often renting, little protection at the start."),
        ]),
        'cadres': ("Achieve long-term projects: housing, retirement, wealth.", [
            ("Mortgage on negotiated terms", "High income and stable situation: a housing project is likely."),
            ("Life insurance and retirement savings plan", "Good saving capacity, long horizon."),
            ("Premium card (travel insurance included)", "High income and long working weeks."),
            ("Dedicated adviser to manage wealth", "Income and assets that justify personal follow-up."),
        ]),
        'seniors': ("Secure: retirement, health, risk-free savings.", [
            ("Supplementary pension or annuity", "End of career: prepare retirement income."),
            ("Supplementary health insurance", "Health needs increase with age."),
            ("Secure savings (savings account, term deposit)", "Preference for risk-free investments."),
            ("Home improvement / renovation loan", "Adapt the home to age well."),
        ]),
    },
    'rh': {
        'jeunes': ("Get off to a good start and stay with the company.", [
            ("Welcome programme with a tutor (mentoring)", "The start of a career is when people change employer most easily."),
            ("Work-study or qualifying training", "Large room for progress in qualifications and skills."),
            ("Clear pay scale with raises linked to skills", "Income still modest: visible progression motivates."),
            ("Housing or transport allowance", "Reduces the cost of living early in a career."),
        ]),
        'cadres': ("Progress without burning out.", [
            ("Career development plan (management positions)", "Graduates and highly committed: they expect prospects."),
            ("Remote work and flexible hours", "Long working weeks: risk of burnout."),
            ("Role as trainer or mentor for young people", "Their experience benefits newcomers."),
            ("Company retirement savings / profit sharing", "Long-term retention."),
        ]),
        'seniors': ("Pass on knowledge and end the career in good conditions.", [
            ("Tutoring: pass know-how on to young people", "Long experience, often in manual trades."),
            ("Health prevention and adapted workstation", "Physical jobs: prevent wear and tear."),
            ("Continuing training (digital tools, new jobs)", "Lower qualification level and changing trades."),
            ("End-of-career preparation (gradual part-time)", "A smooth transition to retirement."),
        ]),
    },
    'public': {
        'jeunes': ("Enter employment and become independent.", [
            ("Vocational training and apprenticeships", "Very few already have a high income: training opens access to better-paid jobs."),
            ("First-job support (paid internship, subsidised contract)", "Early career, modest income."),
            ("Housing and transport aid for young people", "Reduce the costs that hold back independence."),
            ("Microcredit and support to start a business", "Support young people who want to start a business."),
        ]),
        'cadres': ("Grow the economy and balance work and family.", [
            ("Support for business creation and growth", "Graduates, high income: strong potential for initiative."),
            ("Information on working time and childcare solutions", "Very long working weeks."),
            ("Partnerships with schools: take part as trainers", "Put their experience at the service of young people."),
            ("Information on retirement savings", "Prepare retirement financing."),
        ]),
        'seniors': ("Stay in work in good health and prepare retirement.", [
            ("Continuing training and career change (recognition of experience)", "Lower qualifications, changing trades."),
            ("Workplace health prevention", "Mostly manual jobs: prevent wear and tear."),
            ("Information on retirement rights", "End of career is near."),
            ("Hiring and job-retention aid for seniors", "Avoid early exits from the labour market."),
        ]),
    },
}


def plan_for(audience: str, seg_key: str) -> tuple[str, list[tuple[str, str]]]:
    return PLAN[audience][seg_key]


def advice_for(audience: str, person: dict, seg_key: str, situation: str | None = None) -> list[dict]:
    """Advice for one person: actions of their profile + a few rules linked to their situation.

    Sex is never used to choose the actions.
    """
    besoin, actions = PLAN[audience][seg_key]
    recs = [{'action': a, 'pourquoi': w, 'origine': "Based on their profile"} for a, w in actions]
    age, edu, heures = person['age'], person['education-num'], person['hours-per-week']
    bas_revenu = person['income'] == '<=50K'
    wc = str(person.get('workclass', ''))
    ind = "Based on the person's situation"

    if audience == 'banque':
        if person.get('has_gain'):
            recs.append({'action': "Investment advice (shares, funds)", 'pourquoi': "They already have investment income.", 'origine': ind})
        if age < 35 and edu >= 13:
            recs.append({'action': "Mortgage for a first purchase", 'pourquoi': "Young higher-education graduate: good income potential.", 'origine': ind})
        if heures >= 50:
            recs.append({'action': "Income protection insurance (sick leave, disability)", 'pourquoi': "Very high workload: protect income.", 'origine': ind})
        if age >= 55:
            recs.append({'action': "Personal retirement review", 'pourquoi': "Close to retirement age.", 'origine': ind})
        if wc.startswith('Self-emp'):
            recs.append({'action': "Business account + business insurance", 'pourquoi': "Self-employed worker.", 'origine': ind})
    elif audience == 'rh':
        if heures >= 50:
            recs.append({'action': "Discussion about workload and working hours", 'pourquoi': "More than 50 hours per week.", 'origine': ind})
        if age < 30 and edu >= 13:
            recs.append({'action': "\"Young talent\" programme (regular job rotations)", 'pourquoi': "Young higher-education graduate.", 'origine': ind})
        if age >= 55:
            recs.append({'action': "Second-half-of-career interview", 'pourquoi': "Close to retirement.", 'origine': ind})
        if edu <= 8:
            recs.append({'action': "Basic skills refresher (reading, maths, digital tools)", 'pourquoi': "Education level before high school.", 'origine': ind})
        if bas_revenu and heures >= 45:
            recs.append({'action': "Review pay or bonuses", 'pourquoi': "Long working hours for a modest income.", 'origine': ind})
    else:
        if edu <= 8:
            recs.append({'action': "Basic skills refresher and recognition of work experience", 'pourquoi': "Education level before high school.", 'origine': ind})
        if heures >= 50:
            recs.append({'action': "Information on working-time rights", 'pourquoi': "More than 50 hours per week.", 'origine': ind})
        if bas_revenu and heures >= 45:
            recs.append({'action': "Review of social aid for low-income workers", 'pourquoi': "Long working hours for a modest income.", 'origine': ind})
        if age >= 55:
            recs.append({'action': "End-of-career review", 'pourquoi': "Close to retirement.", 'origine': ind})
        if wc.startswith('Self-emp'):
            recs.append({'action': "Support for the self-employed (social protection)", 'pourquoi': "Self-employed worker.", 'origine': ind})
        if age < 35 and edu >= 13:
            recs.append({'action': "Help to start an innovative business", 'pourquoi': "Young higher-education graduate.", 'origine': ind})
        if wc in ('Unknown', 'Never-worked', 'Without-pay'):
            recs.append({'action': "Support towards employment", 'pourquoi': "No paid job declared.", 'origine': ind})

    decl = "Based on their family situation (declared)"
    if situation in MARIES_LABELS:
        txt = {'banque': ("Family insurance / home protection", "Married person."),
               'rh': ("Arrangements for parents (hours, leave)", "Married person."),
               'public': ("Family support (childcare, allowances)", "Married person.")}[audience]
        recs.append({'action': txt[0], 'pourquoi': txt[1], 'origine': decl})
    elif situation in ('Divorced', 'Separated', 'Widowed'):
        txt = {'banque': ("Review of contracts (beneficiaries, life insurance) and budget", "Change in family situation."),
               'rh': ("Listening, social support and more flexible hours", "Change in family situation."),
               'public': ("Social and legal support, help for single-parent families", "Change in family situation.")}[audience]
        recs.append({'action': txt[0], 'pourquoi': txt[1], 'origine': decl})
    return recs


NOTE_EQUITE_SIMPLE = (
    "The proposed actions never depend on the person's sex. Family situation is only taken into account if "
    "it is given voluntarily. The lists of actions are **starting ideas**: the final decision stays human."
)

NOTE_CAUSALITE_SIMPLE = (
    "These results show what **goes together** in the population studied. They do not prove what **causes** what: "
    "for example, a high rate in a group does not say why it is high."
)
