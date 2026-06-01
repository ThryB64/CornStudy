# Tickets — V19 CBOT + météo prévisionnelle

Demande utilisateur : pousser le CBOT plus loin (régimes/risques, pas up/down brut) et intégrer la météo
PRÉVUE (révisions de prévisions en phases sensibles). Plan : `docs/PLAN_V19_CBOT_WEATHER.md`.

## Exécuté (données existantes)

- **V19-CBOT-02** — `DONE` — CBOT risk lab. **Asymétrie : drawdown prévisible (8% h40 AUC 0.725), rally non
  (~0.58), direction 0.53.** Module risque = la bonne sortie CBOT. Artefact `cbot_risk_lab.json`.
- **V19-CBOT-WEATHER** — `DONE` — Météo réalisée → **direction CBOT up_h20 +0.071 (ADD_TO_CBOT_MODEL)** ;
  drawdown +0.013 (WATCHLIST) ; rallyes dégradés (NO_GO).
- **V19-CBOT-03** — `DONE` — COT × météo (short-covering). `NO_GO` (delta −0.006 à −0.007 sur rallyes).
- **V19-CBOT-04** — `DONE` (via lab) — WASDE × cibles : NO_GO (confirme V18-LIT).
- **V19-WX-INFRA** — `DONE` — `src/mais/features/weather_forecast.py` : anomalies/révisions/incertitude/
  phénologie + `assert_forecast_no_leakage` + 4 tests anti-leakage. Archive réelle = WAITING_DATA.

## WAITING_DATA (archive externe requise)

- **V19-WX-01..05** — collecte archive prévisions US (Open-Meteo Historical Forecast / GFS / GEFS) →
  anomalies, révisions, incertitude ensemble, stress phénologique réels.
- **V19-CBOT-05** — futures curve CBOT old/new crop, carry (données complètes).
- **V20-WX-EU-01..02** — météo prévue Europe (France/Roumanie/Hongrie/Ukraine ouest...).

## V21-IND (exécuté)

- **V21-IND-01** — `DONE` — Contexte CBOT causal (UPTREND/NEUTRAL/BULLISH_WEATHER/RISK_OFF + drawdown_risk).
- **V21-IND-02** — `DONE` — **Décomposition du chemin de compression** : DÉCOUVERTE — la prime se compresse
  surtout par **hausse CBOT** (69% CBOT_DRIVEN+BOTH ; jambe CBOT +0.064 vs jambe EMA +0.011, 6×). Le « short
  premium » est surtout un « long CBOT relatif ». Artefact `artefacts/v21/compression_path.json`.
- **V21-IND-04** — `DONE` — Indicateur intégré (prime V17 + contexte CBOT + path hint), règle basis inchangée.
  Module `src/mais/research/v21_indicator_integration.py`, doc `docs/V21_INTEGRATION_RESULTS.md`.
- **V19-WX-COLLECTOR** — `DONE` (code) — `src/mais/collect/openmeteo_forecast_collector.py` prêt (Forecast +
  Historical Forecast API, format long anti-leakage) ; réseau requis → archive `WAITING_DATA`.
- **RAPPORT FINAL** — `DONE` — `docs/FINAL_STUDY_REPORT_CORN_PREMIUM.md` (capstone V9→V21).

## Suite (données externes)

- **V20-PREMIUM** — compression du basis avec météo **prévue** (US+EU) une fois l'archive collectée.
- **V22** — paper trading forward (journal prêt) ; backtest vs forward.

## Découverte clé à retenir

Le CBOT prédit ses **baisses** (risk-off), pas ses hausses. La météo (réalisée) améliore sa **direction**
(+0.07) → la météo **prévue** est la prochaine priorité data (devrait faire mieux, et est exploitable car
connue à l'avance).
