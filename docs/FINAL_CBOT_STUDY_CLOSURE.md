# Clôture de l'étude du cours du maïs CBOT

Date : 2026-06-13. Ce document clôt l'étude (étapes 1-7). **Pas d'étape 8.**

## 1. Ce qui a été exploré
- **Étapes 1-2** : audit + analyse de 12 repos GitHub, 131 fiches sources (études, mémoires,
  rapports, brevets), 46 idées testables.
- **Étape 3 (P0)** : benchmarks random walk (EXT025), roll volume-based (EXT006), pipeline
  WASDE vintage (EXT026).
- **Étape 4 (P1)** : météo, WASDE, COT, courbe futures, éthanol/DDG, basis, Crop Condition,
  prime météo, météo extrême (11 expériences).
- **Étape 5 (P2)** : modèles directionnels, volatilité, régimes, SHAP, HAR/GARCH,
  trend-following, combinaison de modèles (10 expériences).
- **Étape 5 bis** : correction d'une fuite `target_date` (jours calendaires → lignes de
  marché) ; tous les verdicts ont survécu.
- **Étape 6** : synthèse finale + décision stratégique (Option B).
- **Étape 7** : intégration du **score de vente** + validation holdout 2024+ + backtest.

## 2. Ce qui est GARDÉ (intégré au score)
- **Crop Condition @ H90** (cœur directionnel) — `cond_gd_ex_anom`, `cond_dev5y`, `cond_poor_vp`.
- **WASDE stocks-to-use @ H40** — `s2u_z`, `s2u_pctile`, `s2u_slow_chg`.
- **Saisonnalité** — `base_sin`, `base_cos`.
- **Volatilité HAR** + **gate de risque** (décile haut).
- **Régimes** (confiance seulement).
- **Infra** : vintage WASDE anti-fuite (EXT026), hygiène de roll (EXT006).

## 3. Ce qui est REJETÉ
Météo réalisée (EXT001/002/020), surprise WASDE (EXT008), COT (EXT003), proxys éthanol
(EXT004), trend-following (EXT011), stacking (EXT050), deep learning (EXT016). → dégradent le
signal ou sur-apprennent ; la **parcimonie gagne**.

## 4. Ce qui est BLOQUÉ (DATA_BLOCKED / FUTURE_DATA_REQUIRED)
Courbe futures (EXT005), basis/VECM (EXT013), OU mean-reversion (EXT012), vraie surprise WASDE,
prime new-crop prédictive (EXT018), météo prévue (EXT033), satellite, options. Manque :
EUR/USD quotidien, contrats CBOT par maturité, consensus WASDE, options (vol implicite),
archive de prévisions météo forward. Détail : `external_research/matrices/data_blocked_ideas.csv`.

## 5. Conclusion finale (honnête)
1. **La prédiction pure du prix n'est pas validée** avec les données publiques gratuites : la
   random walk reste imbattable en RMSE.
2. Il existe un **signal directionnel modeste** (Crop Condition + WASDE stocks-to-use) et un
   **signal de volatilité solide** (HAR/EGARCH), exploités dans un **score de vente H40-H90**.
3. Sur le **holdout 2024+** (jamais touché avant), le score **bat la random walk** et est
   économiquement cohérent, **mais ne bat pas une simple saisonnalité** ; la fenêtre est courte
   (~1,5 an). Le backtest décisionnel (avec cooldown + campagnes Sep-Aug/Oct-Sep) est **mitigé
   et dépend du cadrage** (bat les baselines en Sep-Aug, perd en année civile) — non conclusif
   sur 2 campagnes.
4. **Verdict du livrable : FRAGILE.** Indicateur d'aide à la décision à reconfirmer en forward,
   **pas un système de trading**.

## 6. Le livrable final
Un **score de vente / direction / risque CBOT** (`mais.indicator.cbot_sale_score`), documenté,
testé (13 tests), reproductible, lançable par `python -m mais.cli sale-score --holdout`. Voir
`FINAL_CBOT_SALE_SCORE_STUDY.md`, `..._PROTOCOL.md`, `..._LIMITS.md`, `..._USER_GUIDE.md`,
`..._TECHNICAL_SUMMARY.md`, `FINAL_HOLDOUT_2024_VALIDATION.md`, `FINAL_FARMER_DECISION_BACKTEST.md`.

## 6bis. Couche de visualisation Euronext
Le score de vente CBOT est en outre **appliqué et visualisé sur l'historique de prix Euronext**
(EMA, €/t) via un dashboard HTML interactif (`mais euronext-indicator`). Les recommandations y
ordonnent correctement les retours futurs (SELL_PARTIAL → baisse, WAIT → hausse), mais le prix
Euronext disponible est à **~97 % un proxy** et la discrimination hors échantillon est faible →
verdict **RESEARCH_ONLY**. Détail : `docs/FINAL_EURONEXT_INDICATOR_REPORT.md`,
`docs/EURONEXT_DATA_AUDIT.md`. Vue d'ensemble de toute l'étude : `docs/FINAL_STUDY_OVERVIEW.md`.

## 7. Pour aller plus loin
Acquérir les données débloquantes (EUR/USD gratuit, prévisions météo forward, exports ; puis
consensus WASDE et options payants) et **reconfirmer le score en forward** sur plusieurs
campagnes. C'est la seule voie crédible de progrès — pas un modèle plus complexe sur les
données actuelles. **L'étude est close ici.**
