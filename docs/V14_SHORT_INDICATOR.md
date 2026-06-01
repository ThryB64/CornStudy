# V14 — Indicateur short-only assemblé, durée de reversion, robustesse proxy

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v14_short_indicator.py` · runners `run_v14.py` + `run_premium_journal.py` · tests (5 PASS)
**Artefacts** : `artefacts/v14/` (short_indicator, reversion_survival, proxy_robustness) + `data/reports/premium_journal.parquet`
**Données** : hors holdout 2024. Holdout verrouillé, jamais touché.

Point d'orgue de la lignée basis : on assemble tout ce qui a été validé (V10-V13) en UN indicateur
discipliné short-only, on modélise la durée de reversion, on teste la robustesse au proxy, et on rend le
journal opérationnel.

---

## V14-01 — Indicateur short-only assemblé : leçon d'over-gating + version utile

Composants : entrée `basis_z > 1`, prédiction conforme de `basis_change_h40` (α=0.10), filtre cost-aware
(`edge attendu > 2·coût + marge`), vetoes (DQ / liquidité / WASDE / roll), sortie `z→0` plafonnée 90j.

| Variante | n signaux | n trades | hit | net coût 5 €/t | coût 5 / trade |
|---|---:|---:|---:|---:|---:|
| **gate strict** (intervalle conforme entièrement < 0) | **0** | 0 | — | — | — |
| **gate relâché** (compression attendue + cost-aware) | 37 | 5 | **1.00** | +56 | **+11.2** |
| baseline short basis_z>1 (sans gate) | — | 42 | 0.86 | +178 | +4.2 |

**Découverte (over-gating)** : le **gate strict émet 0 signal**. La magnitude du basis_change est trop
incertaine (R² < 0) pour que l'intervalle conforme exclue 0 en €/t ; empiler tous les gates à pleine
sévérité **vide l'ensemble**. C'est une illustration directe du principe « ≤ 3 degrés de liberté » : on ne
cumule pas tous les filtres au maximum.

**Indicateur retenu (relâché)** : 5 trades sur ~15 ans, **hit 100%, +11.2 €/t par trade net de coût 5**
contre +4.2 pour la règle brute. Le gate cost-aware **triple l'efficacité par trade au coût 5** — il
« parle rarement, mais mieux ». Verdict `SHORT_INDICATOR_SURVIVES_COST5` (relaxed + leave-all-crises-out
tous deux positifs à coût 5).

**Réserve forte et honnête** : **n=5 trades** → statistiquement fragile. En agrégat, la règle large (42
trades, +178 à coût 5) reste plus exploitable ; le gate cost-aware est une **surcouche haute conviction**,
pas un remplacement. À confirmer en forward réel (journal) et sur données EMA officielles.

## V14-02 — Durée de reversion (Kaplan-Meier)

Temps avant que `basis_z` extrême (|z|>1) revienne croiser 0 (estimateur KM, censure à 160j) :

- **Médiane de reversion : 47 jours**. P(revert ≤ 40j) = 0.47, ≤ 60j = 0.62, **≤ 90j = 0.74**.
- Par saison : **apr-juin rapide (23j)**, jul-août 47j, sep-nov 51j, **jan-mars lent (53j)**.

**Découverte** : la médiane KM (47j) confirme que **H40 sort légèrement trop tôt** et **justifie le plafond
de sortie à 90j** (74% des reversions sont bouclées à 90j). La forte saisonnalité de la vitesse de reversion
(23j au printemps vs 53j en hiver) plaide pour une **sortie saison-aware** : plafond plus court au printemps,
plus long en hiver. Cohérent avec la demi-vie de 17j (V10) et le temps médian de 54j (V12).

## V14-04 — Robustesse au bruit du proxy EMA

On perturbe le prix EMA proxy par un bruit gaussien (0 → 10 €/t) et on remesure l'edge short basis-haut :

| Bruit €/t | hit rate | net coût 3 €/t |
|---|---:|---:|
| 0 | 0.857 | +346 |
| 1 | 0.862 | +349 |
| 2 | 0.862 | +351 |
| 5 | 0.810 | +358 |
| 10 | 0.762 | +371 |

**Découverte** : `PROXY_ROBUST` — même avec un bruit de **10 €/t** sur le prix EMA, l'edge reste largement
positif et le **hit rate ne dégrade que doucement** (0.857 → 0.762). Les conclusions sur la règle short
basis-haut sont donc **peu sensibles à l'erreur de prix du proxy**. *Réserve : `basis_z` (issu de
fondamentaux laggés) est conservé ; seul le prix de sortie est perturbé — test indicatif, pas un substitut à
la donnée officielle.*

## V14-03 — Journal paper-trading opérationnel

`mais.scripts.run_premium_journal` (cron-ready) : append-only des signaux short-only du jour, évaluation des
trades arrivés à maturité (sortie z→0 max90), rapport. Premier run : 37 signaux écrits, 5 trades mûrs
(hit 1.0, +56 €/t net coût 5). Aucune exécution réelle. Cron suggéré :
`15 7 * * 1-5 cd "$PROJET" && venv/bin/python -m mais.scripts.run_premium_journal >> logs/journal.log 2>&1`.

---

## Synthèse V14

| Question | Réponse |
|---|---|
| Peut-on tout empiler (basis + conforme strict + cost) ? | **Non** — over-gating, 0 signal. Garder le gate relâché. |
| Le gate cost-aware améliore-t-il la qualité ? | **Oui** — +11.2 vs +4.2 €/t/trade à coût 5, mais seulement 5 trades. |
| Quel horizon de sortie ? | Plafond **90j** (74% revert ≤90j), médiane 47j, **saison-aware** (23j printemps / 53j hiver). |
| Les résultats tiennent-ils si le proxy est bruité ? | **Oui** jusqu'à 10 €/t (hit 0.86→0.76). |
| Journal forward ? | Opérationnel, cron-ready, append-only. |

## Limites et suite V15

- Indicateur cost-aware **trop rare (n=5)** → la règle large reste le cœur ; gate = surcouche conviction.
- Données EMA proxy → **acquisition officielle = déblocage n°1** (V15-DATA, `WAITING_DATA`).
- exit z→0 optimiste, trades clusterisés → forward réel via le journal (≥ 12 mois) requis.
- **V15** : sortie **saison-aware** (plafond court printemps / long hiver), accumulation du journal forward,
  comparaison proxy vs EMA officiel dès qu'un échantillon est disponible, modèle de hazard saison × régime.

---

*V14 — 2026-05-31. On a assemblé l'indicateur, appris que sur-filtrer le tue, chiffré la durée de reversion*
*(47j, plafond 90j), et montré la robustesse au proxy. Recherche honnête, statut research-only maintenu.*
