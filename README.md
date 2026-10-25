# Census Insight: Streamlit platform on the Adult dataset

One application, six pages (one per variable to predict):

| Page | Target | Model(s) |
|---|---|---|
| Income | > $50,000 or ≤ $50,000 per year | Logistic Regression + Random Forest (pick one, or compare) |
| Education | secondary or less / short post-secondary / higher education | XGBoost |
| Occupation | executives and professionals / clerical and service / blue-collar | Random Forest |
| Relationship | Husband, Wife, Own-child, Not-in-family, Unmarried, Other-relative | Random Forest |
| Workclass | Private / Self-emp (2 types) / Government (3 levels) / Without-pay / Never-worked | Random Forest (softened class weights) |
| Socio-professional profile | young professionals / graduate executives / experienced seniors (clustering) | K-Means (k = 3), full dashboard in `profiles/` |

Access is protected by an account (sign in / create account). Each page has the profile form on the left and, on the
right, the prediction with the model's confidence, then **one extra feature built on top of the model**:

| Page | What it adds |
|---|---|
| Income | **Recommendations**: ranks the actions (education, hours, occupation, employer type, investments) that raise the chance of > $50,000, then a combined plan |
| Education | **Key factors**: which inputs pushed the prediction, compared with typical census people |
| Occupation | **Career matches**: the 5 closest detailed occupations, with typical hours, education and income |
| Relationship | **What-if**: which single changes would flip the predicted family role |
| Workclass | **Similar profiles**: how the 250 most comparable census records actually work, versus the whole census |
| Socio-professional profile | Full dashboard, personal advice and recommended offers (below) |

Recommendations never use age, sex, race, marital status or country as levers. Model performance figures are not shown in the app.

## Light / dark mode

The `⋮` menu (top right, also on the sign-in screen) offers **System / Light / Dark**; the browser remembers the choice. Both themes are defined in `.streamlit/config.toml`;
charts use colours that stay readable on either background.

## Clustering dashboard (Socio-professional profile page)

This page opens a dashboard of its own (in English), kept in the `profiles/` folder. It rebuilds the notebook
`profiles/notebook/projet_ml_clustering.ipynb` (K-Means, k = 3, seed 42) without changing it (the notebook itself stays in French). Its menu is in the sidebar,
below the platform menu, and the advice adapts to the type of organisation chosen ("I am...").

| Page of the dashboard | What it shows |
|---|---|
| Home | key figures and the 3 profiles at a glance |
| Who are our audiences? | card for each profile, in plain words |
| Family and marriage | married / single / divorced: where and with which factors |
| Why? The factors | which factors make a result vary the most |
| What to offer? | action plan per profile (downloadable) and advice for one person |
| Find a specific audience | filters, number of people, suggested actions, downloadable list |
| Reliability and method | how far to trust the results, limits, link with the notebook |

Code: `profiles/view.py` (pages), `profiles/pipeline.py` (cleaning, K-Means, measures), `profiles/reco.py` (segment names,
offer catalogue, rules), `profiles/data/adult.data` (its own copy of the data), `profiles/cache/` (small precomputed table;
rebuild with `python -m profiles.build_cache`). Tests: `tests/test_profiles.py`.

## Accounts

- Sign-up needs a name, an email and a password (8+ characters, one letter and one digit).
- Passwords are hashed with scrypt and a random salt; accounts live in a SQLite file, `storage/users.db`
  (change the location with the `AUTH_DB` environment variable).
- 5 wrong passwords lock the account for 5 minutes.
- The session is kept in the browser tab: reloading the page signs you out.
- On hosts with a temporary disk (Streamlit Community Cloud, Docker without a volume) accounts are lost on restart:
  mount a volume on `storage/` or point `AUTH_DB` to a persistent path.

## Run

- **Windows**: double-click `run.bat`
- **Mac / Linux**: `./run.sh`
- **By hand**: `pip install -r requirements.txt` then `streamlit run app.py` (http://localhost:8501)

Models train automatically the first time each page is opened, then are saved in `artifacts/`
(up to ≈ 1 minute for income). `python train_all.py` trains all six at once.
They retrain by themselves if the scikit-learn or XGBoost version changes (or if `SCHEMA` in `core.py` is bumped).

## Structure

```
app.py               sign-in gate, navigation
home.py              home page: hero banner, illustrated model cards, data charts, how it works
auth.py              accounts (SQLite + scrypt), sign-in / create-account screen
style.py             global stylesheet; theme colours and fonts are in .streamlit/config.toml
ui.py                form, prediction and insights layout (shared by the 5 prediction pages)
insights.py          the extra feature of each page (recommendations, key factors, career matches, ...)
profiles/             clustering dashboard (view.py, pipeline.py, reco.py, data, notebook)
core.py              data, choice lists, model saving
targets/
  income.py  education.py  occupation.py  relationship.py  workclass.py  marital.py   one file per target
train_all.py         trains all models
data/                adult.data, adult.test, adult.names (a single copy)
storage/             users.db (created at first sign-up)
assets/              logo
tests/               pytest: pages, predictions, insights, authentication
```

## Add a page

1. Copy `targets/relationship.py` to `targets/<name>.py`, then adapt: columns, training, class labels,
   and the form's `fields` list (available fields are in `FIELD_SPECS`, `core.py`).
2. Add `<name>.TARGET` to `targets/__init__.py`. The page and its home card appear on their own.

## Deploy

- **Streamlit Community Cloud** (free): push the folder to GitHub, then New app, choose `app.py`.
- **ngrok**: `streamlit run app.py` then `ngrok http 8501` to share a temporary link.
- **Docker**: `docker build -t adult-app . && docker run -p 8501:8501 adult-app` (trains the models at build time).

## Notes

- Training recipes are those of the original projects (same preprocessing and same hyperparameters). Metrics are still
  computed at training time and printed by `python train_all.py`, but the app does not display them.
- The occupation page trains a second Random Forest on the 14 detailed occupations for its "Career matches".
- The numeric education level (`education-num`) is derived from the "Education" list, to avoid
  inconsistent combinations.
- "Not specified" is only offered where the model was trained with missing values.
- The data dates from 1994 (United States) and contains biases: educational project, not for real decisions.
