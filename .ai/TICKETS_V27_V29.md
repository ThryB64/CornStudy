# Tickets — V27 (forward officiel) · V28 (météo prévue) · V29 (premium × risque/chemin)

Suite de V26. Baseline figée inchangée. Statut `RESEARCH_ONLY_NOT_TRADING`. Holdout 2024 verrouillé.
Doc : `docs/V27_V28_V29_FORWARD_FORECAST_PATH.md`.

## V27 — Suivi forward officiel
- **V27-01** — `DONE` — `v27_official_forward.py` : signal officiel du jour (basis officiel, z implied/rolling,
  tier baseline, warnings). Premier point live 2026-05-29 : basis +76.15, z 2.06, SHORT_PREMIUM_EXTREME.
- **V27-02** — `DONE` — Journal **append-only** `data/forward_journal/official_forward_journal.{parquet,jsonl}`.
  Dédup par date, passé jamais réécrit (test). `summarize_forward_journal` (bilan ≥6 mois).
- **V27-03** — `DONE` — Branché dans `ops/daily.py` (step `official_forward`, non bloquant, SKIP propre offline).
- Tests `tests/test_v27_official_forward.py` (5 PASS). Artefacts `artefacts/v27/`.

## V28 — Étude météo prévue (anti-leakage)
- **V28-01** — `DONE` — `v28_forecast_weather_study.py` : features prévision (issue_date) → CBOT forward
  (OOF) + basis compression sous stress, garde anti-leakage, holdout retiré.
- **V28-02** — `BLOCKED_DATA` — archive Historical-Forecast indisponible (host time out dans cet env).
  Fallback synthétique étiqueté `METHODOLOGY_DEMO_SYNTHETIC`. Pipeline validé ; à relancer quand l'archive
  forward (`save_forecast` quotidien) est accumulée ou l'API archive joignable.
- Tests `tests/test_v28_forecast_weather.py` (4 PASS). Artefacts `artefacts/v28/`.

## V29 — Exploration C/D
- **V29-C** — `DONE` — premium × drawdown_risk CBOT : NON CONFIRMÉ (pas de dégradation, high tier meilleur)
  → drawdown_risk reste contexte, pas veto.
- **V29-D** — `DONE` — chemin de compression CBOT_DRIVEN/EMA_DRIVEN/BOTH/ADVERSE : pertes = chemin ADVERSE
  (win 0.00), CBOT_DRIVEN domine (54%, win 1.00). Confirme/affine V21.
- Tests `tests/test_v29_premium_risk_path.py` (3 PASS). Artefacts `artefacts/v29/`.

## V30 — Structure de courbe officielle (Exploration B débloquée)
- **V30-01** — `DONE` — `v30_official_curve_structure.py` : courbe officielle multi-échéances (filtre OI>0),
  spreads, nearby contango/backwardation, contrat le plus liquide. Snapshot 2026-05-29 : nearby
  BACKWARDATION (front−second +9 €/t), globale MOSTLY_CONTANGO, le + liquide Q2026.
- **V30-02** — `DONE` — Contexte de courbe (`curve_shape`/`curve_overall`/`most_liquid_contract`) câblé dans
  le signal/journal V27 ; warning `BACKWARDATION_SLOWER_COMPRESSION` si basis haut + backwardation.
- Tests `tests/test_v30_official_curve.py` (3 PASS). Artefacts `artefacts/v30/`.

## Reste
- **V27-FWD** — cron quotidien → accumuler le journal officiel ; bascule auto sur z rolling à ≥40j ;
  bilan forward à 3/6/12 mois.
- **V28-ARCHIVE** — accumuler l'archive de prévisions forward pour un vrai backtest des révisions.
- **V26-OVERLAP** — validation date-par-date proxy vs officiel quand historique officiel suffisant.
