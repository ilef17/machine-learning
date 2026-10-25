"""Income (> $50K / ≤ $50K): Logistic Regression + Random Forest (full sklearn pipelines)."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from core import COLS, EDUCATION_NUM, Target, build_result, clean_income, load_or_train, read_adult

NUM = ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
CAT = ["workclass", "education", "marital-status", "occupation", "relationship", "race", "sex", "native-country"]
INPUT_COLS = [c for c in COLS if c != "income"]
FNLWGT_DEFAULT = 178356  # dataset median, not entered by the user


def _load(name, skiprows=0, dedupe=False):
    df = read_adult(name, skiprows)
    if dedupe:
        df = df.drop_duplicates()
    for c in ("workclass", "occupation", "native-country"):
        df[c] = df[c].fillna("Unknown")
    df["income"] = clean_income(df["income"]).map({"<=50K": 0, ">50K": 1})
    return df.dropna(subset=["income"]).astype({"income": int})


def _metrics(y, pred):
    return {"accuracy": round(float(accuracy_score(y, pred)), 4), "precision": round(float(precision_score(y, pred)), 4),
            "recall": round(float(recall_score(y, pred)), 4), "f1": round(float(f1_score(y, pred)), 4)}


def _train():
    df = _load("adult.data", dedupe=True)
    X, y = df.drop(columns="income"), df["income"]
    X_tr, _, y_tr, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    test = _load("adult.test", skiprows=1)
    X_te, y_te = test.drop(columns="income"), test["income"]
    specs = {
        "logreg": ("Logistic Regression", "StandardScaler + OneHotEncoder, class_weight='balanced'.",
                   LogisticRegression(max_iter=1000, class_weight="balanced")),
        "rf": ("Random Forest", "200 trees, class_weight='balanced'.",
               RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)),
    }
    models = {}
    for key, (name, desc, clf) in specs.items():
        prep = ColumnTransformer([("num", StandardScaler(), NUM), ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
        pipe = Pipeline([("preprocessor", prep), ("classifier", clf)]).fit(X_tr, y_tr)
        models[key] = {"name": name, "description": desc, "pipeline": pipe,
                       "metrics": _metrics(y_te, pipe.predict(X_te)), "note": f"official adult.test, {len(y_te)} lignes"}
    return {"models": models}


def load():
    return load_or_train("income", _train)


HIGH, LOW = "Income > $50,000 per year", "Income ≤ $50,000 per year"
DESCR = {HIGH: "The model estimates a better than even chance of earning above $50,000 a year.",
         LOW: "The model estimates the chance of earning above $50,000 a year is below 50%."}


def proba(bundle, model_id, rows):
    """Batch scoring: columns = [HIGH, LOW]."""
    df = pd.DataFrame([{**v, "fnlwgt": FNLWGT_DEFAULT, "education-num": EDUCATION_NUM[v["education"]]}
                       for v in rows])[INPUT_COLS]
    p = bundle["models"][model_id]["pipeline"].predict_proba(df)[:, 1]
    return [HIGH, LOW], np.column_stack([p, 1 - p])


def predict(bundle, model_id, values):
    labels, P = proba(bundle, model_id, [values])
    return build_result(labels, P[0], DESCR)


TARGET = Target(
    slug="income", title="Income", icon=":material/payments:",
    question="Does this profile earn more than $50,000 per year?",
    detail="Above or below $50,000 a year.",
    fields=("age", "race", "workclass", "sex", "education", "capital-gain", "marital-status", "capital-loss",
            "occupation", "hours-per-week", "relationship", "native-country"),
    unknown_ok=("workclass", "occupation", "native-country"), load=load, predict=predict, proba=proba,
    extra="Recommendations: the shortest path to > $50,000")
