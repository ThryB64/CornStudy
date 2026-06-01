# V48 — Météo PRÉVUE favorable/défavorable au maïs : apporte-t-elle du signal ?

Session 2026-06-01. Réponse à la question : *les prévisions météo futures (favorables/défavorables au
maïs) portent-elles du signal sur le cours ?* V45 a montré que la météo RÉALISÉE arrive trop tard. Ici on
mesure la **valeur d'une prévision PARFAITE** (oracle), borne supérieure honnête, NON-TRADEABLE (utilise le
futur). `RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé. Règle figée inchangée. Module
`src/mais/research/v48_weather_forecast_signal.py`, tests (2 PASS), artefacts `artefacts/v48/`.

## Méthode : valeur d'une prévision parfaite (oracle)
À J, `oracle_forecast = météo réalisée sur [J+1, J+lead]` = ce qu'une prévision parfaite aurait annoncé.
On mesure le signal qu'elle donnerait sur le CBOT. Borne SUPÉRIEURE : si même elle n'aide pas, l'idée est
morte ; si elle aide alors que le réalisé-connu (V45) ≈ hasard, tout le signal est dans l'anticipation.

## Résultat 1 : la météo MOYENNE prévue n'apporte (presque) rien, même parfaite
| lead | corr(oracle stress moyen, rendement CBOT) | OOF AUC CBOT up |
|---|---:|---:|
| 3 j | 0.037 | 0.473 |
| 7 j | 0.056 | 0.457 |
| 14 j | 0.060 | **0.488** |

→ Oracle AUC ≈ 0.49 ≈ hasard ; gain vs réalisé-connu V45 (0.507) = **−0.019**. **Même une prévision
parfaite de la météo MOYENNE n'a pas d'edge directionnel** : le marché price la météo de base en continu.
Le SIGNE est agronomiquement correct (prévision défavorable → rendement CBOT moins négatif, −1.4 % vs
−2.2 %) mais négligeable.

## DÉCOUVERTE : le signal est dans les ÉVÉNEMENTS EXTRÊMES, pas dans la moyenne
Oracle d'un **pic de chaleur** prévu (top 20 % du max de `tmax_anom_z` sur la fenêtre critique) :

- `corr(pic de chaleur prévu, rendement CBOT) = **0.311**` (vs 0.06 pour la moyenne)
- pic extrême prévu → CBOT **+1.6 %** ; reste → **−2.3 %** → **écart ~3.9 %**, `extreme_heat_bullish=True`.

→ **Le rendement du maïs chute NON-LINÉAIREMENT au-delà de ~30-32 °C en pollinisation** : c'est l'extrême
(dôme de chaleur), pas la météo moyenne, qui fait bouger le prix. Une prévision parfaite d'un **extrême**
porterait un vrai signal haussier. Verdict : `SIGNAL_IN_EXTREME_FORECAST_NOT_MEAN_COLLECT_FORWARD_EXTREMES`.

## Conséquence opérationnelle (anti-leakage)
- Le signal exploitable n'est PAS la météo réalisée ni la prévision moyenne : c'est la **probabilité d'un
  EXTRÊME prévu** (heat dome) sur la fenêtre critique. Les dômes de chaleur sont partiellement prévisibles à
  1-2 semaines → piste réelle.
- Le **journal de prévisions forward (V45)** enregistre désormais, en plus du stress moyen, le **pic de
  température prévu** (`forecast_peak_tmax_us/eu`) — daté à l'émission, append-only. C'est la version
  tradeable, anti-leakage, qui s'accumule pour valider en réel.
- **Côté EU / basis** : un extrême météo EU prévu justifierait un basis haut (→ ADVERSE_RISK). La météo EU
  réalisée est absente du master (data-gated) ; seul le forward EU l'apporte → à mesurer en accumulant.

## Verdict global
Question « la météo prévue apporte-t-elle du signal ? » → **Oui, mais uniquement via les EXTRÊMES**
(pas la météo moyenne, déjà price-in). C'est une découverte importante qui oriente précisément la suite :
suivre en forward la **probabilité de dôme de chaleur** (US pour le CBOT, EU pour la justification du basis),
pas la météo moyenne. Borne oracle = non-tradeable ; le tradeable = journal forward V45 (extrêmes inclus).
Aucune touche à la règle figée.
