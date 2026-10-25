"""Socio-professional profile: card of the clustering dashboard.

This page has no prediction form: it opens the full dashboard in `profiles/` (K-Means with 3 groups, rebuilt from
the notebook `profiles/notebook/projet_ml_clustering.ipynb`). This file only declares the page for the menu and the Home page.
"""
from core import Target


def load():
    return {"models": {}}  # nothing to train here: profiles/pipeline.py builds its own results


def predict(bundle, model_id, values):
    raise NotImplementedError("The dashboard in profiles/ replaces the prediction form of this page.")


TARGET = Target(
    slug="marital", title="Socio-professional profile", icon=":material/hub:",
    question="Which socio-professional profiles make up the census?",
    detail="Three profiles: young professionals, graduate executives, experienced seniors. Full dashboard.",
    fields=(), unknown_ok=(), load=load, predict=predict,
    extra="Full dashboard, personal advice and recommended offers")
