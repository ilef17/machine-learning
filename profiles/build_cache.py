"""Calcule une fois le tableau « choix de k » (la partie lente) et le garde dans cache/.

Optionnel : sans ce fichier, le dashboard le calcule tout seul à la première ouverture de la page « Choix de k ».
Usage :  python -m profiles.build_cache
"""
from profiles import pipeline as P

art = P.build_artifacts()
choix, stab = P.k_tables(art.X, force=True)
print(choix.round(3).to_string(index=False))
print(stab.round(3).to_string(index=False))
print("Cache enregistré dans", P.CACHE)
