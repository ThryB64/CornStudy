# Indicateur Euronext de vente / risque — rapport final

Version : `euronext_indicator_v1`. Date : 2026-06-13. **Aide à la décision de vente, pas une prévision de prix ni un bot.**

## 1. Résumé exécutif — verdict : **RESEARCH_ONLY**

Les recommandations séparent les retours futurs Euronext dans le bon sens (SELL_PARTIAL -0.058 < WAIT +0.051 à H90), mais la discrimination OOS 2024+ est faible (AUC 0.561) et le prix Euronext est à ~97 % un proxy. Données et signal trop fragiles pour valider.

L'indicateur applique le **score de vente CBOT** (étude finale, FRAGILE) à l'historique **Euronext** (€/t) et le visualise (dashboard HTML interactif). Il ne prédit pas le prix ; il signale direction/risque pour **aider à étaler les ventes**.

## 2. Données

- Prix Euronext : `data/processed/euronext/ema_liquid_continuous_adjusted.parquet` (2010-01-04 → 2026-05-20, 3377 j, €/t). **~97 % proxy** (cf. `EURONEXT_DATA_AUDIT.md`).
- Score : Crop Condition (H90), WASDE stocks-to-use (H40), saison, volatilité HAR, régimes — tous **CBOT/US**, alignés sur Euronext par `merge_asof` backward.

## 3. Méthode

- Cible directionnelle Euronext = signe du retour t→t+h, `target_date=index[i+h]` (vraie ligne de marché). **Anti-fuite** : les retours futurs ne servent qu'à l'évaluation, jamais au score ; le dernier signal n'utilise pas le futur.
- Recommandation : SELL_PARTIAL / WAIT / WATCH / RISK_HIGH / NO_SIGNAL (jamais BUY/SHORT).
- Coefficients CBOT (≤2023) : {"h90_crop": {"cond_gd_ex_anom": 1.4274, "cond_dev5y": -1.1944, "cond_poor_vp": -0.519, "base_sin": -0.3642, "base_cos": 0.3915}, "h40_wasde": {"s2u_z": -0.0719, "s2u_pctile": 0.4088, "s2u_slow_chg": 0.0045, "base_sin": -0.1272, "base_cos": 0.5518}}

## 4. Visualisation

Dashboard : `artefacts/final_euronext_indicator/euronext_indicator_dashboard.html` (Plotly, JS inline, **aucune image**). Ouvrir dans un navigateur. 10 graphiques : prix + recommandations, score global, risque de baisse, composantes, retours futurs par recommandation, matrice de confusion H90, table des derniers signaux, backtest agricole, résultat par campagne.

## 5. Résultats historiques

Métriques directionnelles (CBOT → Euronext) :

| horizon | period | prob_source | n | da | base_rate | majority_acc | da_vs_majority | balanced_acc | roc_auc | brier | precision_up | recall_up | precision_down | recall_down | tp | fp | tn | fn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | full_2010+ | h40 | 3357 | 0.540 | 0.498 | 0.502 | 0.038 | 0.540 | 0.553 | 0.258 | 0.541 | 0.502 | 0.539 | 0.577 | 840 | 713 | 972 | 832 |
| 20 | oos_2024+ | h40 | 522 | 0.554 | 0.510 | 0.510 | 0.044 | 0.557 | 0.505 | 0.263 | 0.593 | 0.395 | 0.533 | 0.719 | 105 | 72 | 184 | 161 |
| 40 | full_2010+ | h40 | 3337 | 0.560 | 0.538 | 0.538 | 0.022 | 0.563 | 0.582 | 0.252 | 0.605 | 0.523 | 0.521 | 0.602 | 939 | 614 | 929 | 855 |
| 40 | oos_2024+ | h40 | 502 | 0.554 | 0.592 | 0.592 | -0.038 | 0.584 | 0.557 | 0.254 | 0.706 | 0.421 | 0.471 | 0.746 | 125 | 52 | 153 | 172 |
| 90 | full_2010+ | h90 | 3287 | 0.633 | 0.508 | 0.508 | 0.125 | 0.633 | 0.678 | 0.228 | 0.636 | 0.652 | 0.631 | 0.614 | 1089 | 624 | 993 | 581 |
| 90 | oos_2024+ | h90 | 452 | 0.637 | 0.487 | 0.513 | 0.124 | 0.638 | 0.561 | 0.262 | 0.614 | 0.686 | 0.665 | 0.591 | 151 | 95 | 137 | 69 |

Retours Euronext futurs moyens par recommandation :

| recommendation | n | mean_ret_h20 | mean_ret_h40 | mean_ret_h90 | down_rate_h90 | up_rate_h90 |
|---|---|---|---|---|---|---|
| RISK_HIGH | 239 | -0.014 | -0.012 | -0.041 | 0.615 | 0.385 |
| SELL_PARTIAL | 875 | -0.010 | -0.028 | -0.058 | 0.726 | 0.273 |
| WAIT | 1315 | 0.009 | 0.021 | 0.051 | 0.352 | 0.643 |
| WATCH | 948 | 0.010 | 0.019 | 0.033 | 0.413 | 0.575 |

## 6. Interprétation

- **Juste** : les recommandations ordonnent correctement les retours futurs (SELL_PARTIAL → baisse, WAIT → hausse) sur tout l'historique.
- **Limite** : en **OOS 2024+**, l'AUC chute (faible discrimination) ; le signal H90 n'est pas robuste hors échantillon. WATCH/RISK_HIGH sont moins nets.

## 7. Limites

- Score issu du **CBOT** appliqué à **Euronext** : pas de basis ni d'EUR/USD intégrés.
- Prix Euronext **~97 % proxy** : résultats **illustratifs**, pas une validation.
- Données publiques gratuites ; **pas de prévision de prix** ; pas de garantie de vente optimale ; **validation forward nécessaire**.

## 8. Conclusion : **RESEARCH_ONLY**

Indicateur **visuel exploitable** pour regarder l'historique, mais **non validé** : données proxy + signal OOS faible. À traiter comme outil de recherche/visualisation, pas comme conseil de vente opérationnel.

Dernier signal : **WATCH** au 2026-05-20 (prix 214.0 €/t, P baisse H90 0.4858).