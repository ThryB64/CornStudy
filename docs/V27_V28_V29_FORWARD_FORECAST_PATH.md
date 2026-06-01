# V27 / V28 / V29 — Forward officiel, météo prévue, premium × risque & chemin

Session 2026-05-31. Suite directe de V26 (déblocage EMA officiel). Baseline figée
`MaizePremiumIndicator_RESEARCH_V1` **inchangée**. Statut `RESEARCH_ONLY_NOT_TRADING`. Holdout 2024 verrouillé.

## V27 — Suivi forward officiel + journal append-only

**Module** : `src/mais/research/v27_official_forward.py`. **Branché dans le pipeline daily** (`ops/daily.py`,
step `official_forward`, non bloquant).

- `compute_official_signal()` : à partir de la donnée OFFICIELLE live (EMA settlement Euronext + CBOT/FX
  Yahoo) → basis officiel, `basis_z_official_implied` (distribution proxy trailing 260), tier de la
  baseline figée, warnings (ROLL_RISK, NON_REVERSION_RISK_HIGH).
- `basis_z_official_rolling` : calculé **en plus** dès que l'historique officiel ≥ 40 jours (sinon `None`,
  on retombe sur l'implied). `z_source` indique lequel est utilisé.
- `append_forward_journal()` : **append-only** (`data/forward_journal/official_forward_journal.{parquet,jsonl}`).
  Une date déjà journalisée n'est **jamais** réécrite (test dédié).
- Premier point live (2026-05-29) : basis officiel **+76.15 €/t**, z implied **2.06**, tier
  **SHORT_PREMIUM_EXTREME**, journal initialisé (1 jour).

**Suite** : cron quotidien (`mais daily-run --collect`) accumule le journal. Bilan forward sérieux à ≥ 6 mois ;
bascule automatique sur `basis_z_official_rolling` à ≥ 40 jours. Le passé n'est jamais réécrit.

## V28 — Étude météo PRÉVUE (forecast) vs CBOT/basis, anti-leakage

**Module** : `src/mais/research/v28_forecast_weather_study.py`.

- Anti-leakage strict : features = run de prévision connu à `forecast_issue_date` ; cible = rendement/
  drawdown CBOT forward ; garde `assert_forecast_no_leakage` ; holdout 2024 retiré.
- `run_forecast_cbot_study` : OOF logistique, anomalies/révisions de prévision → direction & drawdown CBOT.
- `run_forecast_basis_study` : un basis élevé se compresse-t-il **moins** sous stress météo US prévu ?
- `collect_real_archive` : récupère l'archive Historical-Forecast (réseau).

**État** : le host `historical-forecast-api.open-meteo.com` **time out** dans cet environnement (l'API
forward `forecast` marchait en V23, pas l'archive). Le module retombe proprement sur une archive
synthétique, **honnêtement étiquetée `METHODOLOGY_DEMO_SYNTHETIC`** (pas un résultat publiable). Le
pipeline anti-leakage est validé end-to-end. **Suite** : accumuler l'archive forward (`save_forecast`
quotidien, qui lui fonctionne) puis re-tester sur données réelles.

## V29 — Exploration C (premium × drawdown CBOT) + D (chemin de compression)

**Module** : `src/mais/research/v29_premium_risk_path.py`. Sur le master réel (hors holdout).

### Exploration C — short premium × risque de drawdown CBOT
Trades short basis-haut segmentés par tier de `drawdown_risk` (proba OOF de drawdown CBOT 8 %/40j) :

| drawdown_risk | n | win | PnL moyen | stopped |
|---|---:|---:|---:|---:|
| low | 10 | 0.80 | 9.92 | 0.00 |
| medium | 16 | 0.75 | 4.63 | 0.25 |
| high | 16 | **0.875** | **22.85** | 0.00 |

**Verdict : NON CONFIRMÉ.** Aucune dégradation sous drawdown_risk élevé (le tier high fait même mieux).
→ `drawdown_risk` reste un **contexte informatif, pas un veto**. Cohérent avec la discipline anti
sur-filtrage (V15, V23, V11).

### Exploration D — chemin de compression (d(basis) = d(EMA) − d(CBOT_eur_t))

| chemin | n | win | PnL moyen |
|---|---:|---:|---:|
| CBOT_DRIVEN | 19 | **1.00** | **22.70** |
| EMA_DRIVEN | 13 | 0.92 | 14.01 |
| BOTH | 3 | 1.00 | 16.79 |
| ADVERSE | 7 | **0.00** | **−17.83** |

Part CBOT_DRIVEN parmi les compressions = **54 %**. **Découverte nette** : les pertes du short premium
sont **exactement** le chemin `ADVERSE` (le basis s'écarte au lieu de se comprimer, win 0.00). Confirme et
affine V21 : la compression profitable vient surtout du rattrapage CBOT (short premium ≈ long CBOT
relatif), mais les compressions EMA-driven sont aussi profitables. Le vrai risque n'est pas « par quelle
jambe ça compresse » mais « est-ce que ça compresse tout court ».

## V30 — Structure de courbe EMA OFFICIELLE (contango / backwardation), données réelles

**Module** : `src/mais/research/v30_official_curve_structure.py`. Débloque l'Exploration B (jusqu'ici
bloquée faute de données multi-échéances) grâce à la source officielle V26.

Sur le snapshot officiel 2026-05-29 (échéances liquides OI>0) :

| contrat | settlement | OI |
|---|---:|---:|
| EMA_M2026 (Jun) | 236.00 | 1 137 |
| EMA_Q2026 (Aug, **le + liquide**) | 227.00 | 14 447 |
| EMA_X2026 (Nov) | 211.75 | 12 253 |
| EMA_H2027 (Mar) | 215.50 | 2 049 |
| EMA_M2027 (Jun) | 217.75 | 100 |

- **nearby = BACKWARDATION** (front−second **+9.00 €/t** ; Q2026−X2026 +15.25) → **tension physique old-crop**.
- structure globale **MOSTLY_CONTANGO** (portage new-crop X2026→H2027→M2027 qui remonte).

**Combinaison avec V27 (le jour même)** : signal **SHORT_PREMIUM_EXTREME** (z 2.06) **+ backwardation nearby**
→ warning **`BACKWARDATION_SLOWER_COMPRESSION`** ajouté au signal/journal. Cohérent avec l'hypothèse de la
baseline (V16) : un basis haut sous backwardation se normalise plus lentement (compression prudente). Le
contexte de courbe (`curve_shape`, `curve_overall`, `most_liquid_contract`) est désormais journalisé en
forward et s'enrichira jour après jour. Tests `tests/test_v30_official_curve.py` (3 PASS).

## Ce qui ne change pas
Baseline figée inchangée (aucune idée n'a battu la règle). `drawdown_risk`, chemin de compression et météo
prévue restent **contexte/warnings**, pas vetoes. Réserves permanentes maintenues (EMA historique proxy,
mur de coûts ~3-4 €/t/leg, pas de validation forward longue, pas de bot réel).
