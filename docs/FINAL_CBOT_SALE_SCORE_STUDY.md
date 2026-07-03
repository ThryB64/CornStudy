# Étude finale — Score de vente / direction / risque CBOT

Version : `cbot_sale_score_v1`. Date : 2026-06-13. **Livrable final de l'étude.** Aide à la
décision de commercialisation, **pas une prévision de prix ni un bot de trading.**

## 1. Objectif
Fournir à un agriculteur un **score H40-H90** indiquant le risque directionnel (baisse/hausse)
et le risque de volatilité du maïs CBOT, pour **doser ses ventes** (vendre partiellement /
attendre / surveiller). On **ne prédit pas le prix exact**.

## 2. Pourquoi l'abandon de la prédiction du prix
L'étape 6 a établi (sur données publiques gratuites) que **la random walk est imbattable en
RMSE** (EXT025 : 0/36 couples benchmark×horizon, Diebold-Mariano p<0.10) ; tous les
fondamentaux **dégradent** le RMSE hors échantillon. La seule information exploitable est
**directionnelle long-horizon** (Crop Condition, WASDE stocks-to-use) et de **volatilité**
(HAR/EGARCH). D'où le pivot vers un **score**.

## 3. Signaux retenus (uniquement les briques validées)
| Bloc | Variables | Horizon | Source/verdict |
|---|---|---|---|
| Crop Condition (cœur) | `cond_gd_ex_anom`, `cond_dev5y`, `cond_poor_vp` | H90 | EXT019/EXT024 IMPROVE |
| WASDE stocks-to-use | `s2u_z`, `s2u_pctile`, `s2u_slow_chg` | H40 | EXT007/EXT024 IMPROVE |
| Saison | `base_sin`, `base_cos` | H40/H90 | porte une part de l'edge |
| Volatilité (HAR) | `rv_w`, `rv_m`, `rv_q` + HAR forecast | H20-H90 | EXT010 KEEP |
| Gate vol | décile haut de vol prévue | H90 | EXT009 KEEP |
| Régimes | `regime_uptrend`, `regime_low_vol`, `regime_bilan_extreme` | H90 | EXT017 (confiance seulement) |

## 4. Modèles
- **Logit L2 parcimonieux** par horizon (3-6 variables) : H40 = WASDE+saison, H90 = Crop+saison.
- **HAR** (OLS sur vol réalisée 5/22/66 j) pour la prévision de volatilité H90 ; gate = décile
  90 gelé sur ≤2023.
- **Régimes** passé-only → modulent la **confiance** uniquement (pas la direction).
- Aucun stacking, RF, ni DL. **Parcimonie**.

## 5. Score → recommandation
À chaque date : `p_down_h90 = 1 − P(hausse H90)`, `p_down_h40`, `pred_vol_h90`, `confidence`.
- **NO_SIGNAL** si features manquantes.
- **RISK_HIGH** si vol prévue dans le décile haut (le signal s'y inverse, EXT009).
- **SELL_PARTIAL** si `p_down_h90 ≥ 0.58` et confiance ≥ 0.50.
- **WAIT** si `P(hausse H90) ≥ 0.55` (pas de risque baissier).
- **WATCH** sinon (signal faible/contradictoire). **Jamais BUY, jamais short.**

## 6. Résultats holdout 2024+ (une seule fois)
| modèle | h | n | DA | AUC | vs majorité |
|---|---|---|---|---|---|
| score crop@H90 | 90 | 303 | 0.686 | 0.816 | +0.182 |
| score wasde@H40 | 40 | 353 | 0.705 | 0.709 | +0.184 |
| saison seule | 90 | 303 | **0.752** | **0.840** | +0.248 |
| marché seul | 90 | 303 | **0.752** | **0.878** | +0.248 |
| random walk | 90 | 303 | 0.495 | 0.500 | −0.010 |

Le score **bat la random walk** (+18 pts) et est cohérent, **mais ne bat pas la saisonnalité /
le marché seul** sur ce holdout court (~1,5 an, cycle baissier 2024). Détail :
`FINAL_HOLDOUT_2024_VALIDATION.md`.

## 7. Backtest décisionnel (2024+)
Avec **cooldown** (20 séances entre ventes) et plusieurs **découpages de campagne** : le
résultat **dépend du cadrage** — en année civile le score perd contre la vente précoce (−14 à
−19), en campagne Sep-Aug il bat toutes les baselines (jusqu'à +49 vs attente). Le cooldown
rend la simulation réaliste mais ne crée pas d'avantage. **2 campagnes seulement** → mitigé et
non conclusif. Détail : `FINAL_FARMER_DECISION_BACKTEST.md`.

## 8. Limites
Edge modeste (DM non significatif), pas de gain démontré vs saisonnalité sur le holdout,
fenêtre courte, régimes post-hoc. Détail : `FINAL_CBOT_SALE_SCORE_LIMITS.md`.

## 9. Conclusion — verdict : **FRAGILE**
Le score reproduit la conclusion de recherche (direction H90 cohérente, vol prévisible) et
survit au holdout face à la random walk, **mais n'apporte pas de valeur démontrable au-dessus
d'une simple saisonnalité** sur 2024+, et la fenêtre est trop courte. C'est un **indicateur
d'aide à la décision FRAGILE** : utilisable comme repère prudent, **à reconfirmer en forward**
sur plusieurs campagnes avant tout usage opérationnel. **Ce n'est pas un système de trading.**
