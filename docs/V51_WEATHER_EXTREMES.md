# V51 — Weather Extremes Lab (développement de la météo future)

Session 2026-06-01. Développement rigoureux de la piste « météo future » après V45 (réalisé moyen négatif)
et V48 (oracle moyen négatif, mais signal dans les EXTRÊMES). Baseline figée inchangée, anti-leakage
(`shift(1)`, z causaux expandants), `RESEARCH_ONLY_NOT_TRADING`, holdout verrouillé.

Module `src/mais/research/v51_weather_extremes.py`, tests `test_v51` (3 PASS), runner `run_v52_v57`.

## Indicateurs d'extrêmes construits (US Corn Belt, causaux, pondérés phénologie juillet=1.0)
- `heat_anom_z` (anomalie tmax, déjà en z) ; seuils `hot>1σ`, `hot>1.5σ`
- `consecutive_hot_days` : run-length de jours chauds (persistance)
- `dry_z` : déficit pluie 14j + anomalie pluie 30j
- `heat_dome_flag` : chaleur extrême **et** sécheresse simultanées
- `heat_extreme_crit` : chaleur extrême × poids phénologique (fenêtre critique)
- ⚠️ `wx_belt_heat_days_30/38c` et `drought_extreme_flag` du master sont **dégénérés** (≈constants) → non
  utilisés ; on reconstruit les extrêmes depuis `tmax_anom_z` / pluie (propres, n≈4400).

## Résultats (réalisé = borne explicative, non-tradeable)

**E1 — Structure lead-lag (la découverte centrale).** Corrélation de l'extrême connu à J avec le rendement
CBOT à divers horizons, en fenêtre critique :

| horizon | −20 | −10 | −5 | +5 | +10 | +20 |
|---|---:|---:|---:|---:|---:|---:|
| corr | 0.282 | **0.341** | 0.235 | 0.054 | 0.147 | 0.077 |

→ La corrélation avec le **passé** (backward 0.34) est **bien plus forte** qu'avec le **futur**
(forward 0.15). **Le marché ANTICIPE la chaleur** : quand l'extrême est réalisé, le CBOT a déjà bougé.
`predictive_beyond_anticipation = false`.

**E2 — Queue vs corps (la queue existe).** Décile haut de chaleur (z≥1.57) → CBOT **+1.0 %** vs corps
**−1.4 %** sur 10 j (écart **+2.4 %**, n_tail=83 sur 825 jours critiques). Le signal de queue est réel et va
dans le sens agronomique, mais cf. E1 il est en partie déjà incorporé.

**E3 — Quel extrême porte le signal ?** Corrélation au rendement CBOT forward (10 j, critique) :
`consecutive_hot_days` **0.098** > `heat_extreme_crit` 0.086 > `heat_anom_z` 0.071 > `dry_z` −0.018 >
`heat_dome_flag` 0.014. → **La PERSISTANCE de la chaleur (jours consécutifs) porte plus de signal que
l'intensité d'un seul jour ou la sécheresse.** Découverte actionnable pour ce qu'il faut PRÉVOIR.

**E4 — Lien compression (négatif honnête).** Quand le basis est haut, un extrême US élevé n'AIDE PAS la
compression (4.7 vs 6.21 €/t). La chaîne naïve « chaleur → CBOT monte → compression » ne tient pas
mécaniquement (la chaleur soutient peut-être aussi les prix EU / relation bruitée).

## Verdict
`EXTREME_HEAT_TAIL_REAL_BUT_ANTICIPATED_FORECAST_LEADTIME_REQUIRED`.

Le signal météo n'est NI dans la moyenne (V45/V48) NI capturable a posteriori sur le réalisé : il est dans
la **queue ET en amont du prix**. Le seul edge exploitable est un **avantage de PRÉVISION** — devancer le
dôme de chaleur de juillet, en suivant en priorité la **persistance** prévue (jours consécutifs >seuil),
pas la météo moyenne. C'est précisément ce que le journal forward V45/V48 accumule (pics tmax prévus) ; V51
dit quoi y privilégier : la durée de l'épisode chaud.

## Suite
- Enrichir le journal forward (V45) avec `forecast_consecutive_hot_days` (persistance prévue), pas seulement
  le pic.
- Valider en forward quand l'historique de prévisions s'accumule (les prévisions historiques ne sont pas
  re-téléchargeables — l'API historical-forecast time-out, cf. V45).
