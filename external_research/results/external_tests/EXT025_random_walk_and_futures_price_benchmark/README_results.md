# EXT025 — Résultats : benchmarks RW / drift / naïfs

Date : 2026-06-12. Scripts : `external_research/experiments/external_tests/EXT025_.../{run,evaluate}_ext025.py` (reproductibles, données internes en lecture seule).

## Verdict : **KEEP**

Le tableau de référence est produit, stable, reproductible et sans fuite. Il devient la base de comparaison obligatoire de tous les EXT futurs.

## Ce qui a été produit

- `predictions_ext025.csv` — 216 000 prédictions (2 séries × 6 horizons × 4 benchmarks), datées, avec segment `eval_pre2024` vs `holdout_2024plus` (holdout verrouillé, jamais comparé).
- `metrics_ext025.csv` — RMSE/MAE/R²/DA par série × segment × horizon × modèle.
- `comparison_ext025.csv` — mêmes métriques par sous-période (2000-2009 / 2010-2015 / 2016-2019 / 2020+).
- `dm_tests_ext025.csv` — Diebold-Mariano (HAC Bartlett lag h-1, ajustement Harvey) de chaque benchmark vs RW.
- `NOTE_basis_skipped.md` — le basis n'a pas de tableau (pas de série eurusd quotidienne dans `data/interim` ; seul usd_index existe). DATA_BLOCKED partiel sans impact sur CBOT/EMA.

## Résultats clés (segment éval ≤ 2023)

RMSE (niveau de prix) :

| Série | H | MA20 | NaiveRet | **RW** | RW+drift |
|---|---|---|---|---|---|
| CBOT (¢/bu) | 5 | 30.7 | 48.3 | **20.4** | 20.4 |
| CBOT | 20 | 46.2 | 216 | **41.3** | 41.6 |
| CBOT | 40 | 61.7 | 1036 | **56.6** | 57.5 |
| CBOT | 90 | 92.5 | (explose) | **89.1** | 92.4 |
| EMA (€/t) | 5 | 11.9 | 32.8 | **8.3** | 8.3 |
| EMA | 20 | 17.8 | 4601 | **15.8** | 16.2 |
| EMA | 40 | 23.5 | (explose) | **22.2** | 23.5 |
| EMA | 90 | 33.8 | (explose) | **32.6** | 37.1 |

1. **La RW est la baseline la plus difficile à battre à TOUS les horizons, sur les deux marchés** — réplication propre de Reeve & Vigfusson sur nos données. Aucun des 36 couples benchmark×horizon ne bat la RW avec p<0.10 (DM).
2. RW+drift ≈ RW à court horizon, se dégrade à H90 (le drift expandant n'aide jamais) — confirmer un edge contre la RW suffit donc.
3. Naive-last-return est inutilisable au-delà de H5 (capitalisation du dernier rendement = explosion) — gardé comme borne basse pédagogique.
4. MA20 est systématiquement pire que la RW : « prévoir le retour vers la moyenne mobile » détruit de l'information au niveau prix.

## Implications pour le programme

- Tout EXT directionnel doit battre **DA ≈ 0.5 vs la RW** (la RW ne prédit pas de direction : l'asymétrie haussière légère du corn donne ~0.51-0.53 aux benchmarks à drift, voir `metrics_ext025.csv`).
- Tout EXT en niveau doit battre la **RMSE RW** du tableau ci-dessus, DM à l'appui.
- Le benchmark « futures-as-forecast » (prix du déféré comme prévision) est **DATA_BLOCKED** historiquement (pas de courbe profonde avant 2025) — à ajouter quand la courbe accumulée le permettra.

## Limites

- Série CBOT = continu vendeur (artefacts de roll possibles — voir EXT006) ; série EMA = proxy barchart 2010-2024 + officiel 2025+ (niveaux validés V26).
- R² au niveau prix est mécaniquement élevé pour tous les benchmarks (persistance) : ne JAMAIS citer un R² de niveau comme preuve de compétence — utiliser RMSE relative à la RW et la DA.
- Holdout 2024+ : segment calculé mais non comparé (règle 12), réservé à une ouverture humaine explicite.
