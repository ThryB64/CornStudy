# Plan V19 — Pousser le CBOT + météo prévisionnelle

**Date** : 2026-05-31 · **Statut** : plan directeur (research-only).

Deux directions, sans casser la règle EMA/CBOT (basis mean-reversion) :
1. **Pousser le CBOT** comme moteur mondial — pas du « up/down » brut, mais **régimes, risques, grandes
   baisses/hausses, volatilité, changements de structure**.
2. **Intégrer la météo PRÉVUE** (forecasts, révisions, incertitude) pendant les **phases agronomiques
   sensibles** — le marché price l'anticipé, pas seulement le réalisé.

Hypothèse forte : *le CBOT est plus prédictible quand on modélise les **révisions de prévisions météo**
pendant les fenêtres sensibles (pollinisation, remplissage)* ; et *un basis EMA/CBOT haut se compresse
différemment selon que la météo US/EU **prévue** justifie ou non une tension physique.*

---

## 0. Principe anti-leakage météo prévue (CRITIQUE)

On NE backteste PAS avec la météo réalisée pour simuler une décision passée. On utilise les **prévisions
archivées telles que connues le jour J**. Schéma de stockage obligatoire :

```
forecast_issue_date | forecast_run | forecast_valid_date | lead_time_days | zone | variable | value
```

Règle : une feature au jour `J` ne peut utiliser que des prévisions avec `forecast_issue_date <= J`.
Interdits : météo réalisée future, réanalyse postérieure, moyenne de runs incluant le futur.
Tests obligatoires : `forecast_issue_date <= signal_date`, `valid_date = issue_date + lead_time`,
aucune valeur réalisée future dans les features forecast.

## 1. Zones suivies (pondérées par production)

**US Corn Belt** (poids ~ production maïs) : Iowa, Illinois, Nebraska, Minnesota, Indiana, Ohio,
South Dakota, Kansas, Missouri, Wisconsin.
**Europe** (pour EMA/basis) : France, Roumanie, Hongrie, Italie du Nord, Pologne, Ukraine ouest, Serbie.

## 2. Sources météo

- **Open-Meteo Forecast API** (jusqu'à 16 j) + **Historical Forecast API / Previous-Runs API** → permet de
  reconstruire « la prévision telle que connue le jour J » (clé pour le backtest honnête).
- **NOAA NOMADS / GFS / GEFS** (runs 4×/jour, horizons +192h à +384h) pour la production future.
- Ensemble (**GEFS / ECMWF ens / Open-Meteo ensemble**) pour l'incertitude.

> Statut data : l'archive de prévisions n'est pas dans le dataset courant → **`WAITING_DATA`**. On construit
> dès maintenant l'infrastructure de features + tests anti-leakage (testée sur données synthétiques).

## 3. Variables météo forecast

Par zone et lead time (J+1..J+16) : tmax, tmin, précip, proba précip, vent, humidité, ET0, soil moisture
(si dispo), GDD prévus, jours >32/35°C, jours secs.

## 4. Features dérivées (le cœur)

### 4.1 Anomalies (vs normale 30 ans)
`temp_forecast_anomaly`, `precip_forecast_anomaly`, `gdd_forecast_anomaly`, `heat_days_forecast_anomaly`,
`dryness_forecast_anomaly`.

### 4.2 Révisions de prévision (probablement le signal le plus fort)
`revision_temp_7d = forecast_7d_today − forecast_7d_yesterday`, idem precip/gdd/heat/dryness sur 7-14j.
Exemple : hier +12 mm de pluie attendus, aujourd'hui +2 mm → révision sèche −10 mm → potentiellement
bullish CBOT en période sensible.

### 4.3 Incertitude ensemble
dispersion pluie/temp, proba chaleur extrême, proba sécheresse, désaccord GFS vs ECMWF.
Hypothèse : ↑ incertitude → ↑ volatilité CBOT.

### 4.4 Stress par phénologie (météo au bon moment agronomique)
Calendrier US : avril-mai planting, juin végétatif, **juillet pollinisation (critique)**, août remplissage,
sept-oct récolte. Index : `us_pollination_heat_risk`, `us_drought_forecast_risk`, `us_planting_delay_risk`,
`us_harvest_delay_risk`, `us_weather_forecast_stress_index`. Idem EU (floraison/remplissage/récolte).

## 5. Cibles CBOT (pas seulement up/down)

- **Direction** : y_cbot_up_h5/h10/h20/h40.
- **Grandes hausses** : rally_3pct_h10, 5pct_h20, 8pct_h40.
- **Grandes baisses** : drawdown_3pct_h10, 5pct_h20, 8pct_h40.
- **Triple barrier** : first_hit_up/down ±3% h20, ±5% h40.
- **Volatilité** : vol_spike_h10, range_expansion_h10, gap_risk_next_session.
- **Météo-spécifiques** : up_after_hot_dry_revision_h10, up_during_pollination_h20,
  down_after_rain_relief_h10.

## 6. Cibles EMA/CBOT (lien avec l'indicateur)

basis_change_h40, compression probable, time-to-reversion **selon météo prévue US/EU**, chemin de
compression (baisse EMA vs hausse CBOT).

## 7. Expériences

### Phase V19 — CBOT + météo prévue
- **V19-WX-01..05** : collecteur forecast US, anomalies, révisions, stress phénologique, incertitude ensemble.
- **V19-CBOT-01** baseline CBOT moderne (réalisé + prévu + révisions + saison) vs baselines simples.
- **V19-CBOT-02** CBOT **risk model** (drawdown/rally/vol risk) — plus utile que up/down.
- **V19-CBOT-03** **COT × météo** (météo bullish + fonds très short → short covering).
- **V19-CBOT-04** **WASDE × météo** (choc fondamental combiné).
- **V19-CBOT-05** futures curve CBOT (front-next, old/new crop, carry, contango).
- **V19-CBOT-06** event study des **révisions météo** fortes.

### Phase V20 — Europe météo + premium
- **V20-WX-EU-01..02** collecteur forecast EU + stress phénologique EU.
- **V20-PREMIUM-01** compression du basis avec météo **prévue** (US + EU).
- **V20-PREMIUM-02** time-to-reversion selon météo prévue.
- **V20-PREMIUM-03** weather warning (prévu) dans l'indicateur.

### Phase V21 — Intégration indicateur
- **V21-IND-01** CBOT context warning (bullish weather risk / drawdown risk / rally risk / vol risk / COT).
- **V21-IND-02** **décomposition du chemin de compression** : baisse EMA vs hausse CBOT vs mixte vs lente
  vs non-reversion. (Un short premium gagne si EMA baisse OU si CBOT monte plus vite qu'EMA.)
- **V21-IND-03** météo forecast dans le rapport quotidien.
- **V21-IND-04** signal premium + contexte mondial.

## 8. Tests anti-leakage obligatoires

`test_weather_forecast_no_future_run`, `test_forecast_issue_date_before_signal_date`,
`test_forecast_valid_date_lead_time_correct`, `test_no_realized_weather_leakage_in_forecast_features`.

## 9. Artefacts attendus

`data/processed/weather_forecast/us_corn_belt_forecast_daily.parquet`,
`weather_forecast_anomalies.parquet`, `artefacts/v19/cbot_*.json`, `artefacts/v20/premium_weather_*.json`.

## 10. Critères GO / NO_GO

- Une famille (révisions météo, COT×météo, WASDE×météo, curve) est intégrée **seulement si** elle améliore
  l'OOF d'une **cible CBOT risque** au-delà des baselines, ou améliore la prédiction de compression du basis
  au-delà de `basis_z + saison` (delta AUC > +0.02 robuste). Sinon `KEEP_AS_EXPLANATION` / `WATCHLIST`.
- La baseline indicateur (short basis-haut) reste **figée** tant qu'aucun `ADD_TO_INDICATOR` robuste.

## 11. Ce qui est constructible MAINTENANT vs WAITING_DATA

| Bloc | Maintenant | WAITING_DATA |
|---|---|---|
| CBOT risk targets + COT×météo + WASDE×météo (météo **réalisée**) | ✅ V19-CBOT-LAB | — |
| Futures curve CBOT | partiel (données dispo limitées) | courbe complète |
| Météo **prévue** (anomalies/révisions/incertitude) | infra + tests anti-leakage (synthétique) | archive Open-Meteo/GFS |
| Météo EU prévue | infra | archive |
| Décomposition chemin de compression | ✅ (avec données actuelles) | affinement |

---

*Plan V19 — 2026-05-31. Pousser le CBOT par les risques et les révisions de prévisions météo en phases*
*sensibles ; relier au basis EMA/CBOT. Anti-leakage strict sur les forecasts. Research-only.*
