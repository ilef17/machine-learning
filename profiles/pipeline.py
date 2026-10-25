"""Dashboard engine.

This file redoes EXACTLY the same steps as the notebook `projet_ml_clustering.ipynb`
(same cleaning, same variables, K-Means with k = 3 and seed 42).
The notebook is never modified: the dashboard only reads it to check that it finds the same figures.
(The notebook itself is in French, so the patterns that read its outputs below stay in French.)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, davies_bouldin_score,
                             normalized_mutual_info_score, silhouette_score)
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "data" / "adult.data"
NOTEBOOK_PATH = BASE / "notebook" / "projet_ml_clustering.ipynb"
CACHE = BASE / "cache"

RS = 42   # graine du hasard (la même que dans le notebook)
K = 3     # nombre de clusters choisi dans le notebook

COLUMNS = ['age', 'workclass', 'fnlwgt', 'education', 'education-num',
           'marital-status', 'occupation', 'relationship', 'race', 'sex',
           'capital-gain', 'capital-loss', 'hours-per-week', 'native-country',
           'income']

# Variables utilisées pour former les clusters (marital-status n'en fait pas partie)
POOL = ['age', 'workclass', 'education-num', 'occupation', 'sex',
        'hours-per-week', 'income', 'has-capital-gain', 'has-capital-loss']
BINAIRES = ['has-capital-gain', 'has-capital-loss']

MARIES = ['Married-civ-spouse', 'Married-AF-spouse', 'Married-spouse-absent']


# ----------------------------------------------------------------------------------------------
# 1) Chargement et nettoyage (comme la Partie 1 du notebook)
# ----------------------------------------------------------------------------------------------
def load_clean(path: Path = DATA_PATH):
    df = pd.read_csv(path, names=COLUMNS, na_values='?', skipinitialspace=True)
    df = df.drop_duplicates().reset_index(drop=True)
    for col in ['workclass', 'occupation', 'native-country']:
        df[col] = df[col].fillna('Unknown')

    df['has-capital-gain'] = (df['capital-gain'] > 0).astype(int)
    df['has-capital-loss'] = (df['capital-loss'] > 0).astype(int)

    bounds = {}
    for col in ['age', 'hours-per-week']:
        bas, haut = df[col].quantile([0.01, 0.99])
        bounds[col] = (float(bas), float(haut))
        df[col] = df[col].clip(lower=bas, upper=haut)
    return df, bounds


# ----------------------------------------------------------------------------------------------
# 2) Préparation des données (comme la Partie 2 / 3 du notebook)
# ----------------------------------------------------------------------------------------------
def build_matrix(df: pd.DataFrame, features: list[str]):
    sub = df[features]
    bin_c = [c for c in features if c in BINAIRES]
    num_c = [c for c in sub.select_dtypes(include=[np.number]).columns if c not in bin_c]
    cat_c = sub.select_dtypes(exclude=[np.number]).columns.tolist()
    prep = ColumnTransformer([
        ('num', StandardScaler(), num_c),
        ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), cat_c),
        ('bin', 'passthrough', bin_c),
    ], verbose_feature_names_out=False)
    M = prep.fit_transform(sub)
    return M, prep.get_feature_names_out(), prep


def _mode(s: pd.Series):
    return s.value_counts().index[0]


def compute_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Tableau de profil de chaque cluster (comme la Partie 7 du notebook)."""
    profil = df.groupby('cluster').agg(
        effectif=('age', 'size'),
        age_moyen=('age', 'mean'),
        education_moy=('education-num', 'mean'),
        heures_moy=('hours-per-week', 'mean'),
        pct_hommes=('sex', lambda s: (s == 'Male').mean()),
        pct_revenu_sup50k=('income', lambda s: (s == '>50K').mean()),
        pct_gain_capital=('has-capital-gain', 'mean'),
        workclass_dominant=('workclass', _mode),
        metier_dominant=('occupation', _mode),
        situation_dominante=('marital-status', _mode),
    )
    profil['effectif'] = (profil['effectif'] / len(df))
    return profil.rename(columns={'effectif': 'part_population'})


def compute_metrics(df: pd.DataFrame, X: np.ndarray, labels: np.ndarray) -> dict:
    """Mesures de qualité (comme les Parties 5 et 6 du notebook)."""
    ms = df['marital-status']
    purete = pd.crosstab(df['cluster'], ms).max(axis=1).sum() / len(df)
    return {
        'silhouette': float(silhouette_score(X, labels, sample_size=5000, random_state=RS)),
        'davies_bouldin': float(davies_bouldin_score(X, labels)),
        'nmi': float(normalized_mutual_info_score(ms, labels)),
        'ari': float(adjusted_rand_score(ms, labels)),
        'purete': float(purete),
        'purete_base': float(ms.value_counts(normalize=True).max()),
        'tailles': df['cluster'].value_counts(normalize=True).sort_index(),
    }


@dataclass
class Artifacts:
    df: pd.DataFrame
    X: np.ndarray
    names: np.ndarray
    prep: ColumnTransformer
    km: KMeans
    pca: PCA
    Z: np.ndarray
    nn: NearestNeighbors
    bounds: dict
    profile: pd.DataFrame
    metrics: dict
    ratio_q: tuple   # seuils (33 % et 67 %) du rapport distance1/distance2, pour la confiance d'affectation


def build_artifacts(path: Path = DATA_PATH, k: int = K) -> Artifacts:
    df, bounds = load_clean(path)
    X, names, prep = build_matrix(df, POOL)
    km = KMeans(n_clusters=k, n_init=20, random_state=RS).fit(X)
    df['cluster'] = km.labels_
    pca = PCA(n_components=2, random_state=RS)
    Z = pca.fit_transform(X)
    nn = NearestNeighbors(n_neighbors=5).fit(X)

    d = np.sort(km.transform(X), axis=1)
    ratio = d[:, 0] / d[:, 1]
    ratio_q = (float(np.quantile(ratio, 0.33)), float(np.quantile(ratio, 0.67)))

    return Artifacts(df=df, X=X, names=names, prep=prep, km=km, pca=pca, Z=Z, nn=nn,
                     bounds=bounds, profile=compute_profile(df),
                     metrics=compute_metrics(df, X, km.labels_), ratio_q=ratio_q)


# ----------------------------------------------------------------------------------------------
# 3) Choix de k (comme la Partie 4 du notebook) : calcul lourd, gardé dans cache/
# ----------------------------------------------------------------------------------------------
def k_tables(X: np.ndarray, force: bool = False):
    f1, f2 = CACHE / "choix_k.csv", CACHE / "stabilite_k.csv"
    if f1.exists() and f2.exists() and not force:
        return pd.read_csv(f1), pd.read_csv(f2)

    rows = []
    for k in range(2, 11):
        km = KMeans(n_clusters=k, n_init=10, random_state=RS).fit(X)
        rows.append({'k': k, 'Inertie': km.inertia_,
                     'Silhouette': silhouette_score(X, km.labels_, sample_size=5000, random_state=RS),
                     'Davies-Bouldin': davies_bouldin_score(X, km.labels_)})
    choix = pd.DataFrame(rows)

    stab = []
    for k in range(2, 8):
        ref = KMeans(n_clusters=k, n_init=20, random_state=RS).fit_predict(X)
        aris = [adjusted_rand_score(ref, KMeans(n_clusters=k, n_init=5, random_state=s).fit_predict(X))
                for s in range(1, 6)]
        stab.append({'k': k, 'ARI min': min(aris), 'ARI moyen': float(np.mean(aris))})
    stab = pd.DataFrame(stab)

    CACHE.mkdir(exist_ok=True)
    choix.to_csv(f1, index=False)
    stab.to_csv(f2, index=False)
    return choix, stab


# ----------------------------------------------------------------------------------------------
# 4) Simulateur : où se place une nouvelle personne ?
# ----------------------------------------------------------------------------------------------
def predict_person(art: Artifacts, p: dict) -> dict:
    row = pd.DataFrame([{
        'age': float(np.clip(p['age'], *art.bounds['age'])),
        'workclass': p['workclass'],
        'education-num': p['education-num'],
        'occupation': p['occupation'],
        'sex': p['sex'],
        'hours-per-week': float(np.clip(p['hours-per-week'], *art.bounds['hours-per-week'])),
        'income': p['income'],
        'has-capital-gain': int(p['has_gain']),
        'has-capital-loss': int(p['has_loss']),
    }])[POOL]
    x = art.prep.transform(row)
    dists = art.km.transform(x)[0]
    order = np.argsort(dists)
    ratio = float(dists[order[0]] / dists[order[1]])
    if ratio <= art.ratio_q[0]:
        confiance = "nette"
    elif ratio <= art.ratio_q[1]:
        confiance = "moyenne"
    else:
        confiance = "ambiguë"
    nd, ni = art.nn.kneighbors(x, n_neighbors=5)
    return {'cluster': int(order[0]), 'dists': dists, 'ratio': ratio, 'confiance': confiance,
            'z': art.pca.transform(x)[0], 'voisins': ni[0]}


# ----------------------------------------------------------------------------------------------
# 5) Lien avec le notebook : lecture seule + comparaison des chiffres
# ----------------------------------------------------------------------------------------------
def read_notebook(path: Path = NOTEBOOK_PATH):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _stream_text(nb: dict) -> str:
    out = []
    for c in nb.get("cells", []):
        if c.get("cell_type") != "code":
            continue
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                out.append("".join(o.get("text", [])))
    return "\n".join(out)


def notebook_numbers(nb: dict) -> dict:
    """Reads the figures to compare from the notebook outputs."""
    txt = _stream_text(nb)
    num = lambda pat: (float(m.group(1)) if (m := re.search(pat, txt, re.M)) else None)
    res = {
        'silhouette': num(r"^Silhouette\s*:\s*([0-9.]+)"),
        'davies_bouldin': num(r"^Davies-Bouldin\s*:\s*([0-9.]+)"),
        'nmi': num(r"^NMI\s+:\s*([0-9.]+)"),
        'ari': num(r"^ARI\s+:\s*([0-9.]+)"),
        'purete': num(r"^Pureté des clusters\s*:\s*([0-9.]+)"),
        'purete_base': num(r"^Pureté sans clustering\s*:\s*([0-9.]+)"),
    }
    m = re.search(r"Taille des clusters :(.*?)Name:", txt, re.S)
    res['tailles'] = ({int(a): float(b) for a, b in re.findall(r"^\s*(\d+)\s+([0-9.]+)\s*$", m.group(1), re.M)}
                      if m else {})
    return res


def compare_with_notebook(art: Artifacts) -> pd.DataFrame | None:
    nb = read_notebook()
    if nb is None:
        return None
    nbn = notebook_numbers(nb)
    rows = []
    labels = {'silhouette': 'Silhouette', 'davies_bouldin': 'Davies-Bouldin', 'nmi': 'NMI with marital-status',
              'ari': 'ARI with marital-status', 'purete': 'Cluster purity', 'purete_base': 'Purity without clustering'}
    for key, lab in labels.items():
        a, b = nbn.get(key), art.metrics[key]
        rows.append({'Measure': lab, 'Notebook': a, 'Dashboard': round(b, 3),
                     'Identical': (a is not None) and abs(a - round(b, 3)) < 0.0011})
    for c, part in sorted(nbn['tailles'].items()):
        b = float(art.metrics['tailles'].get(c, np.nan))
        rows.append({'Measure': f'Share of cluster {c}', 'Notebook': part, 'Dashboard': round(b, 3),
                     'Identical': abs(part - round(b, 3)) < 0.0011})
    return pd.DataFrame(rows)


def notebook_conclusion(nb: dict) -> str | None:
    """Last text cell of the notebook (the conclusion)."""
    for c in reversed(nb.get("cells", [])):
        if c.get("cell_type") == "markdown":
            return "".join(c.get("source", []))
    return None
