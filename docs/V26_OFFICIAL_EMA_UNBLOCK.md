# V26 — Déblocage de la source EMA officielle Euronext + V25 corrections data

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING` (mais source officielle désormais opérationnelle)
**Modules** : `src/mais/collect/euronext_official_live.py`, `src/mais/research/v26_official_ema_validation.py`
**Runner** : `run_v26.py` · tests (3 PASS) · artefacts `artefacts/v26/` + `data/raw/euronext_ema_official/official_daily.parquet`

Le plus gros blocage de l'étude — la donnée EMA officielle — est **débloqué** : l'endpoint AJAX officiel
Euronext répond et fournit les **vrais settlements**. Le collecteur est opérationnel.

---

## V26 — Données officielles Euronext EMA (déblocage réel)

L'endpoint `https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/EMA/DPAR` renvoie le
tableau officiel des prix. Le parser V26 (`parse_official_prices`) extrait bid/ask/last/open/high/low/
**settlement**/volume/open_interest par échéance.

**Snapshot officiel réel collecté (2026-05-29)** :

| Contrat | mois | settlement | volume | open interest |
|---|---|---:|---:|---:|
| EMA_M2026 (Jun) | M | 236.00 | 681 | 1 137 |
| **EMA_Q2026 (Aug)** | Q | **227.00** | 2 001 | **14 447** (front liquide) |
| EMA_X2026 (Nov) | X | 211.75 | 1 465 | 12 253 |
| EMA_H2027 (Mar) | H | 215.50 | 55 | 2 049 |
| … 2027-2028 | | settlements | — | faible |

Mois = **M/Q/X/H** (Jun/Aug/Nov/Mar) → **confirme H/M/Q/X, pas de Janvier** (cohérent V24). Données
sauvegardées **append-only** dans `data/raw/euronext_ema_official/official_daily.parquet`.

### Premier basis OFFICIEL réel (2026-05-29)
Live : CBOT ZC=F **446.75 cents/bu**, EUR/USD **1.1659** → `cbot_eur_t = 150.85 €/t`.
- **Basis officiel (front Aug) = 227.00 − 150.85 = +76.15 €/t.**

### Proxy vs officiel (niveaux)
Distribution du basis **proxy** historique : moyenne 37.2, std 15.5, p90 56.0, p95 62.5, max 110.7.
- Le basis officiel **+76.2 €/t** est au **99ᵉ percentile** du proxy (z ≈ **2.51**).

**Deux conclusions importantes** :
1. **Les niveaux proxy sont réalistes** : 76 €/t est dans la plage proxy (jusqu'à 110), pas une aberration.
   La donnée proxy n'est pas grossièrement fausse en niveau de basis.
2. **Le marché réel est aujourd'hui en régime de prime EXTRÊME** (z ≈ 2.5) → l'indicateur signalerait
   `SHORT_PREMIUM_EXTREME`. C'est le premier read réel-monde de l'indicateur (research-only).

**Limite** : pas de chevauchement de dates (proxy s'arrête 2025-07-25, officiel = 2026-05-29) → la
validation **date-par-date** proxy vs officiel n'est pas encore possible. Solution : **accumuler l'officiel
forward** (le collecteur tourne désormais) jusqu'à constituer un historique officiel comparable.

---

## V25 — Corrections data (audit V24)

- **V25-01 relabel eurusd** : `load_master_dataset` charge désormais le **vrai** `eurusd_rate`
  (eu_cross_assets, médiane 1.219) au lieu de la dérivation ×36.744 (~114). **Invariance vérifiée** :
  modèle 2-var promu **inchangé (AUC 0.694)** ; 6-var 0.652 vs 0.656 (bruit de couverture). Confirme l'audit :
  la correction est cosmétique, les résultats tiennent.
- Fallback dérivé conservé (étiqueté `eurusd_is_derived=True`) si eu_cross_assets absent.

---

## Synthèse

| Élément | Statut |
|---|---|
| Source EMA officielle | **DÉBLOQUÉE** (collecteur opérationnel, settlement réel) |
| Snapshot officiel 2026-05-29 | collecté (10 contrats, front Aug OI 14 447) |
| Basis officiel du jour | +76.2 €/t = 99ᵉ pctl proxy (régime prime extrême) |
| Niveaux proxy | **confirmés réalistes** par l'officiel |
| Validation date-par-date | en attente (accumuler l'officiel forward) |
| eurusd relabel | fait, invariant |

## Ce que ça change

L'étude n'est plus **entièrement** dépendante du proxy : on a maintenant un **collecteur officiel
opérationnel** et un premier point de validation des niveaux. Le statut reste `RESEARCH_ONLY_NOT_TRADING`
car l'**historique** reste proxy (l'officiel ne fournit que le snapshot du jour, à accumuler), mais le
chemin vers une validation officielle complète est **ouvert et fonctionnel**.

## Suite

- **V27** : cron quotidien du collecteur officiel → accumuler l'historique officiel ; journal forward.
- Quand l'historique officiel ≥ quelques mois : validation date-par-date proxy vs officiel (basis, signaux, PnL).
- Indicateur figé (baseline `MaizePremiumIndicator_RESEARCH_V1`, cf. `docs/FROZEN_BASELINE.md`).

---

*V26 — 2026-05-31. Source EMA officielle Euronext débloquée et opérationnelle ; basis officiel +76 €/t*
*(prime extrême, 99ᵉ pctl) ; niveaux proxy validés réalistes. eurusd relabélisé (invariant). Research-only.*
