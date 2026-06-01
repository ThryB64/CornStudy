# Tickets — V25 (data clean) + V26 (EMA officiel débloqué)

Demande utilisateur : chercher/obtenir les vraies données Euronext officielles, finaliser la data propre,
figer la baseline. Docs `docs/V26_OFFICIAL_EMA_UNBLOCK.md`, `docs/FROZEN_BASELINE.md`.

## V25 — Data clean (audit V24)

- **V25-01** — `DONE` — Relabel eurusd : `load_master_dataset` charge le vrai `eurusd_rate` (médiane 1.219)
  au lieu de la dérivation ×36.744. Invariance vérifiée (modèle 2-var inchangé AUC 0.694). Fallback dérivé
  étiqueté `eurusd_is_derived`.
- **V25-BASELINE** — `DONE` — Baseline figée `MaizePremiumIndicator_RESEARCH_V1` (`docs/FROZEN_BASELINE.md`).

## V26 — Source EMA officielle (DÉBLOCAGE RÉEL)

- **V26-01** — `DONE` — Collecteur officiel `src/mais/collect/euronext_official_live.py` : parser robuste de
  l'endpoint AJAX Euronext → settlements réels. Snapshot 2026-05-29 collecté (10 contrats M/Q/X/H, front Aug
  OI 14 447), append-only `data/raw/euronext_ema_official/official_daily.parquet`.
- **V26-02** — `DONE` — Basis officiel du jour : CBOT live 446.75 cents + EUR/USD 1.166 → cbot_eur_t 150.85 ;
  basis officiel front = **+76.2 €/t**.
- **V26-03** — `DONE` — Proxy vs officiel (niveaux) : basis officiel au **99ᵉ pctl** du proxy (z≈2.51) →
  niveaux proxy **réalistes** ; marché réel en régime prime EXTRÊME. Validation date-par-date en attente.
- Tests `tests/test_v26_official_ema.py` (3 PASS), runner `run_v26.py`, artefacts `artefacts/v26/`.

## Reste

- **V27** — cron quotidien du collecteur officiel → accumuler l'historique officiel ; journal forward.
- **V26-OVERLAP** — quand historique officiel ≥ quelques mois : validation date-par-date proxy vs officiel
  (basis, signaux, PnL).
- Indicateur figé. Statut `RESEARCH_ONLY_NOT_TRADING` (historique encore proxy).
