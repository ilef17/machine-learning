"""Family role (6 classes): Random Forest (notebook \"relationship\")."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from core import EDUCATION_NUM, Target, build_result, load_or_train, read_adult

NUM = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
CAT = ["workclass", "education", "marital-status", "occupation", "race", "sex", "native-country"]
FEATURES = ["age", "workclass", "education", "education-num", "marital-status", "occupation", "race", "sex",
            "capital-gain", "capital-loss", "hours-per-week", "native-country"]

LABELS = {k: k for k in ("Husband", "Wife", "Own-child", "Not-in-family", "Unmarried", "Other-relative")}
DESCR = {"Husband": "Male spouse, married.", "Wife": "Female spouse, married.",
         "Own-child": "Child of the head of household.", "Not-in-family": "Lives alone or outside a family unit.",
         "Unmarried": "Not married, lives in a household with a partner or family.",
         "Other-relative": "Other family tie. Rare class: the least well predicted."}


def _train():
    df = read_adult("adult.data").drop_duplicates().dropna().reset_index(drop=True)  # rows with "?" dropped
    y, X = df["relationship"], df[FEATURES]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    prep = ColumnTransformer([("num", StandardScaler(), NUM),
                              ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])
    rf = RandomForestClassifier(n_estimators=100, max_depth=20, class_weight="balanced", random_state=42, n_jobs=-1)
    pipe = Pipeline([("prep", prep), ("model", rf)]).fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    metrics = {"accuracy": round(float(accuracy_score(y_te, pred)), 4),
               "precision": round(float(precision_score(y_te, pred, average="weighted")), 4),
               "recall": round(float(recall_score(y_te, pred, average="weighted")), 4),
               "f1": round(float(f1_score(y_te, pred, average="weighted")), 4),
               "f1_macro": round(float(f1_score(y_te, pred, average="macro")), 4)}
    return {"models": {"rf": {
        "name": "Random Forest", "description": "100 trees (max depth 20), class_weight='balanced'.",
        "pipeline": pipe, "metrics": metrics, "note": f"20% test set, {len(y_te)} rows (weighted averages)."}}}


def load():
    return load_or_train("relationship", _train)


def proba(bundle, model_id, rows):
    df = pd.DataFrame([{**v, "education-num": EDUCATION_NUM[v["education"]]} for v in rows])[FEATURES]
    pipe = bundle["models"][model_id]["pipeline"]
    return list(pipe.classes_), pipe.predict_proba(df)


def predict(bundle, model_id, values):
    labels, P = proba(bundle, model_id, [values])
    return build_result(labels, P[0], DESCR)


TARGET = Target(
    slug="relationship", title="Relationship", icon=":material/family_restroom:",
    question="What is this person's family role in the household?",
    detail="Husband, Wife, Own-child, Not-in-family, Unmarried or Other-relative.",
    fields=("age", "race", "workclass", "sex", "education", "capital-gain", "marital-status", "capital-loss",
            "occupation", "hours-per-week", "native-country"),
    unknown_ok=(), load=load, predict=predict, proba=proba,
    extra="What-if: what would change the answer")
