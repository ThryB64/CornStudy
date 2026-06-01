# V8 — SYNTHÈSE DES RÉSULTATS SCIENTIFIQUES

**Date** : 2026-05-30.
**Statut** : DONE pour Sprint Phase A + 8 expériences scientifiques.
**Statut global** : `RESEARCH_ONLY_NOT_TRADING` — confirmé et renforcé par V8.

---

## 1. Vue d'ensemble

V8 a tourné les expériences suivantes après audit V0–V7 :

| Ticket | Verdict V8 | Artefact |
|---|---|---|
| V8-INFRA-HOLDOUT | DONE | `artefacts/v8/holdout_lock.json` |
| V8-INFRA-REGISTRY | DONE — 55 entrées unifiées | `artefacts/registry/experiments_unified.jsonl` |
| V8-FRAGILE-FLAGS-AUDIT | DONE — 32 entrées FRAGILE identifiées | `artefacts/v8/fragile_flags_audit.json` |
| V8-META-REVALIDATION | **META_PREMIUM_FRAGILE** (H90 = LIKELY_OVERFIT_OR_LEAKAGE) | `artefacts/v8/meta_revalidation.json` |
| V8-EMBARGO-ROBUSTNESS | EMBARGO_NEUTRAL | `artefacts/v8/embargo_robustness.json` |
| V8-CBOT-LAB-PLUS | best `y_down_gt_5pct_h20` AUC 0.6229 | `artefacts/v8/cbot_lab_plus.json` |
| V8-EMA-PREMIUM-LAB-PLUS | best `y_basis_compression_h20` AUC 0.6548 | `artefacts/v8/ema_premium_lab_plus.json` |
| V8-BASIS-REGIME-V3 | 4 régimes KMeans (silhouette 0.30) / 5 GMM | `artefacts/v8/basis_regime_v3.json` |
| V8-SEASONAL-V3 | best `dec` AUC 0.9209 (n=65 FRAGILE), `jul_aug` AUC 0.618 (n=237) | `artefacts/v8/seasonal_v3.json` |
| V8-CROSS-MARKET-V3 | EMA_ADDS_TO_CBOT confirmé | `artefacts/v8/cross_market_v3.json` |
| V8-PCORRECT-V3 | Isotonic > Platt, ECE 0.025 well_calibrated | `artefacts/v8/pcorrect_v3.json` |
| V8-BACKTEST-V3 | top20 cost-0 +172 €/t, négatif dès cost 1 €/t | `artefacts/v8/backtests_v3.json` |
| V8-RED-TEAM-PREMIUM | RED_TEAM_PARTIAL (H40 FAIL, H90 PASS marginal, basis_extreme PASS marginal) | `artefacts/v8/red_team_premium.json` |

---

## 2. Découverte critique — META-REVALIDATION

| Cible | V6 walk-forward classique | V8 nested strict (médiane) | Delta |
|---|---:|---:|---:|
| `y_rel_outperform_h40` | 0.768 | **0.6151** | **-0.153** |
| `y_rel_outperform_h90` | **0.937** | **0.5982** | **-0.339** |
| `y_rel_outperform_when_basis_extreme_h40` | 0.954 (n=65) | 0.641 | -0.31 |
| `y_rel_outperform_when_basis_extreme_h90` | 1.000 (n=29) | 0.640 | -0.36 |

**Verdict** : `META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE` pour H90, `FRAGILE` ailleurs.

**Conclusion** : Le V6 AUC 0.937 était optimiste. Sous protocole strict, le meta-model converge vers ~0.60 AUC. Les meta-features OOF apportent +0.05 AUC sur walk-forward classique mais seulement +0.02 sur LOCY.

---

## 3. Découvertes sur les cibles

### 3.1 CBOT
Toutes les cibles testées (25) sont PROMISING (aucune GO_RESEARCH), AUC dans [0.55, 0.62].

| Rang | Cible | AUC | top20 | n_oof |
|---|---|---:|---:|---:|
| 1 | `y_down_gt_5pct_h20` | 0.623 | 0.34 | 4625 |
| 2 | `y_down_gt_5pct_h10` | 0.618 | 0.24 | 4635 |
| 3 | `y_down_gt_3pct_h20` | 0.597 | 0.43 | 4625 |
| 4 | `y_down_gt_3pct_h5` | 0.593 | 0.25 | 4640 |
| 5 | `y_down_gt_3pct_h10` | 0.583 | 0.33 | 4635 |

**Observation** : le CBOT est plus prédictible côté **risque de drawdown** que côté direction haussière. AUC ~0.62 sur n=4625 est statistiquement solide mais modeste économiquement.

### 3.2 EMA premium

| Rang | Cible | AUC | top20 | n_oof | Verdict |
|---|---|---:|---:|---:|---|
| 1 | `y_basis_compression_h20` | **0.655** | 0.41 | 139 | GO_RESEARCH (n petit, à confirmer) |
| 2 | `y_basis_expansion_h20` | 0.630 | 0.63 | 139 | PROMISING |
| 3 | `y_up_h60_ema` | 0.600 | 0.52 | **2217** | PROMISING — meilleure cible large échantillon |
| 4 | `y_up_h60_ema_raw` | 0.600 | 0.52 | 2217 | PROMISING |
| 5 | `y_rel_outperform_h120` | 0.579 | 0.64 | 1465 | PROMISING |

**Observation majeure** : `y_basis_compression_h20` est la cible EMA la plus prédictible OOF (AUC 0.65). C'est une cible nouvelle V8 — elle prédit si le basis va se compresser de plus d'un σ à H20. Économiquement plausible : la prime EU mean-reverts quand elle est haute.

### 3.3 Saisonnalité

| Saison | AUC | top20_train_only_DA | n_obs | n_oof |
|---|---:|---:|---:|---:|
| `jan_mar` | **0.350** | None | 1460 | 464 |
| `apr_jun` | **0.402** | 0.787 | 1513 | 545 |
| `jul_aug` | **0.618** | None | 1014 | 237 |
| `sep_nov` | 0.528 | None | 1464 | 60 |
| `dec` | **0.921** | None | 489 | 65 |

**Découvertes** :
- `jan_mar` et `apr_jun` ont des AUC **inversées** (0.35, 0.40). Un signal **inversé** sur ces saisons donnerait AUC 0.65 et 0.60 — l'information existe, mais le signe est opposé à la direction par défaut. C'est cohérent économiquement (jan-mar = stocks, apr-jun = semis EU).
- `jul_aug` (stress yield US/EU) AUC 0.62 sur n=237 — **vraie** poche de signal.
- `dec` AUC 0.92 sur n=65 — **FRAGILE**, à marquer attentivement, ne pas citer comme preuve.
- `sep_nov` quasi-aléatoire (AUC 0.53), n=60 trop faible pour conclure.

### 3.4 Cross-market

EMA → CBOT : `1` cible voit son AUC augmenter de plus de +0.01 quand on ajoute les features EMA. CBOT → EMA : `0` cible.

Confirme partiellement V7-05 : EMA contient un peu d'information pour CBOT, l'inverse n'est pas observé sous V8 protocole.

### 3.5 Régimes de basis

KMeans best k=4 (silhouette 0.296), GMM best k=5 (BIC -800).
Distribution KMeans k=4 : {0: 51, 1: 142, 2: 162, 3: 56}.

**Limitation V8** : `auc_premium_h40_by_regime` est vide (problème de filtrage taille minimale). À corriger en V9 ou nouveau ticket V8-BASIS-REGIME-V3-PATCH.

---

## 4. Découverte critique — BACKTESTS

### 4.1 PnL par politique (cost 0)

| Politique | n_trades long | hit long | n_trades short | hit short | PnL combined (€/t) |
|---|---:|---:|---:|---:|---:|
| `full_signal_long_short` | 71 | 0.51 | 54 | 0.52 | **+1.76** |
| `top20` | 42 | 0.52 | 32 | 0.53 | **+172.46** |
| `basis_rule_only` (z > 1.5) | 21 | **0.24** | 18 | **0.28** | **-382.29** |

### 4.2 Stress coûts sur full_signal

| Coût (€/t/leg) | PnL net combined (€/t) | Profitable |
|---:|---:|---|
| 1 | **-248** | NON |
| 2 | -498 | NON |
| 3 | -748 | NON |
| 5 | -1248 | NON |
| 8 | -1998 | NON |

### 4.3 Conclusions backtest

1. **La règle simple `basis_z > 1.5` seule est catastrophique** (hit ~25% au lieu de 50%+). Le z-score nu n'est PAS un signal directionnel utilisable. C'est un résultat **inattendu et important** : V7 affichait des AUC 0.95–1.00 sur basis_extreme conditionnel — ces pics étaient des fragiles n<100, pas un signal exploitable réellement.
2. **top20 cost-0 est positif (+172 €/t)** mais s'effondre à cost 1 €/t. Le signal a du contenu, mais pas assez de marge pour absorber les coûts de transaction réalistes.
3. **full_signal cost-0 est neutre** (+1.76 €/t sur 125 trades) — pas exploitable.
4. **À cost 5/8 €/t, toutes les stratégies sont massivement négatives**. C'est cohérent : si AUC ~0.60 et hit ~50%, la marge nette ne couvre pas le slippage + frais.

---

## 5. Red team

| Cible | AUC obs | AUC perm p95 | p-value | Verdict |
|---|---:|---:|---:|---|
| `y_rel_outperform_h40` | 0.519 | 0.521 | 0.06 | **RED_TEAM_FAIL** |
| `y_rel_outperform_h90` | 0.530 | 0.520 | 0.01 | RED_TEAM_PASS (marginal) |
| `y_rel_outperform_when_basis_extreme_h40` | 0.556 | 0.554 | 0.04 | RED_TEAM_PASS (marginal) |

**Conclusion** : sous permutation des labels (100 perms), le signal H40 brut **n'est pas statistiquement distinct du bruit** (p=0.06 > 0.05). H90 et basis_extreme passent mais à p marginal (0.01–0.04). Verdict global RED_TEAM_PARTIAL.

---

## 6. P(correct) calibration

- Sigmoid (Platt) : AUC 0.43, ECE 0.026, well_calibrated=True.
- Isotonic : AUC 0.54, ECE 0.025, well_calibrated=True.

**Conclusion** : la calibration isotonique est meilleure en AUC (mais reste basse). Les deux sont bien calibrées (ECE < 0.05). À retenir : pour V9, utiliser Isotonic. Mais le modèle de base est trop faible pour que P(correct) soit utile.

---

## 7. Embargo robustness

Embargo {0, 5, 20, 40, 60, 90, 180} jours testé sur 4 cibles :

| Cible | max AUC | min AUC | delta |
|---|---:|---:|---:|
| `y_rel_outperform_h40` | 0.551 | 0.544 | 0.008 |
| `y_rel_outperform_h90` | 0.537 | 0.507 | 0.030 |
| `y_up_h20` | 0.531 | 0.518 | 0.013 |

**Verdict** : EMBARGO_NEUTRAL. Le choix d'embargo (0 à 180j) ne change pas significativement l'AUC OOF. Cela suggère que :
- Le signal est faible et stable
- Ou les fenêtres test sont déjà non-corrélées au train

C'est rassurant méthodologiquement : les écarts V6/V8 ne viennent **pas** de l'embargo seul.

---

## 8. Synthèse économique V8

### Ce qui marche (modestement, OOF strict)
- CBOT `y_down_gt_5pct_h20` AUC 0.62 (n=4625) — risque de drawdown CBOT.
- EMA `y_up_h60_ema` AUC 0.60 (n=2217) — la direction EMA H60 est légèrement prédictible.
- EMA `y_basis_compression_h20` AUC 0.65 (n=139) — la compression de basis H20 (cible nouvelle V8).
- Saisonnalité `jul_aug` AUC 0.62 (n=237) — stress yield été.
- Saisonnalités inversées `jan_mar` et `apr_jun` — signal contraire au défaut, exploitable.

### Ce qui ne marche pas
- Meta-model V6 H90 (V8-META-REVALIDATION).
- Règle simple `basis_z > 1.5` en backtest (hit 25%).
- Direction EMA H20 brute (V7 NO_GO confirmé).
- Stockage économique.
- CQR prix absolu.
- Fair value comme prédicteur.

### Ce qui est suspect / à protéger
- `dec` saisonnier AUC 0.92 (n=65) — FRAGILE.
- `basis_extreme_h40/h90` (n=29–65) — FRAGILE.
- V7 seasonal_expert top20 AUC 0.98 (n=68) — protocole train-only non vérifié.

---

## 9. Implications pour l'indicateur

### A. L'indicateur **ne peut pas** s'appuyer sur le meta-model V6
Sa performance V6 était un artefact de protocole. Sous protocole strict, AUC ~0.60.

### B. L'indicateur ne peut pas s'appuyer sur les pics basis_extreme/seasonal_expert V7
Trop fragiles, n trop petit.

### C. L'indicateur **peut** s'appuyer sur :
- CBOT downside risk module (y_down_gt_5pct_h20).
- EMA basis compression module (y_basis_compression_h20).
- EMA direction H60 module (y_up_h60_ema).
- Filtre saisonnier (jul_aug + signaux inversés jan_mar / apr_jun).
- Confidence isotonic.
- Abstention systématique en dehors des saisons / régimes.

### D. Profitabilité en backtest research-only
**Aucune stratégie n'est rentable au-delà de cost 1 €/t.** Pas de paper trading possible en l'état. Conditions sine qua non avant paper :
1. Soit acquérir des données meilleures (EMA officiel, EC MARS, FOB, Ukraine flux) pour pousser AUC > 0.65.
2. Soit identifier des poches saisonnières/régimes plus profondes (jul_aug a déjà n=237).
3. Soit baisser drastiquement les coûts (impossible sur EMA peu liquide).

---

## 10. Verdict V8 global

**`META_PREMIUM_FRAGILE`** — confirmé.
**`INDICATOR_NOT_READY`** — confirmé.
**`PAPER_TRADING_NOT_READY`** — confirmé.
**`BOT_REAL_NOT_READY`** — confirmé.
**`RESEARCH_ONLY_NOT_TRADING`** — statut maintenu.

V8 a transformé une étude apparemment riche (V6 AUC 0.937) en une étude rigoureuse mais beaucoup plus humble (AUC réelle ~0.55–0.62). C'est un **progrès scientifique**, pas une régression : on sait maintenant **où on en est vraiment**.

---

## 11. Prochaines étapes (V9 cadrage initial)

| # | Action | Justification |
|---|---|---|
| 1 | Acquisition EMA officiel Euronext (V7-01B) | Tout le signal EMA est sur proxy ; un protocole sur source officielle peut révéler ou invalider définitivement les signaux. |
| 2 | EC MARS + FAS + Eurostat COMEXT (V7-11A/B/C) | Apport de drivers fondamentaux EU manquants. |
| 3 | V8-BASIS-REGIME-V3-PATCH (corriger le filtre AUC par régime) | Le résultat par régime est vide, à corriger. |
| 4 | V8-SEASONAL-V3-DEEP (poches profondes jul_aug, déc avec n>=100) | Le seul vrai signal saisonnier exploitable identifié. |
| 5 | V8-CBOT-DOWNSIDE-DEEP (y_down_gt_5pct H10/H20 avec filtres avancés) | La cible la plus prédictible CBOT. |
| 6 | V8-BASIS-COMPRESSION-DEEP (validation cible V8 sur plus de données) | Nouvelle découverte V8. |
| 7 | V9-STRUCTURAL-MODEL (modèle structurel `P_EMA = f(CBOT, FX, basis_z, season, roll, DQ)`) | Alternative au stacking lourd. |
| 8 | V9-CONTRASTIVE-LEARNING (supervised contrastive sur cibles déséquilibrées) | Pour les cibles drawdown rare. |

Tant que (1)+(3)+(4)+(5)+(6) ne sont pas livrés, l'étude reste en `RESEARCH_ONLY_NOT_TRADING`.

---

## 12. Liste des artefacts V8 produits

```
artefacts/v8/
├── backtests_v3.json
├── basis_regime_v3.json
├── cbot_lab_plus.json
├── cross_market_v3.json
├── ema_premium_lab_plus.json
├── embargo_robustness.json
├── fragile_flags_audit.json
├── holdout_lock.json
├── infra_registry_merge.json
├── meta_revalidation.json
├── pcorrect_v3.json
├── red_team_premium.json
└── seasonal_v3.json
```

Plus :
- `artefacts/registry/experiments_unified.jsonl` (55 entrées)

Et docs :
- `docs/RECHERCHE_MAIS_REFLEXION_PRO_V8.md`
- `docs/DATA_SOURCES_MAIS_CBOT_EURONEXT_V8.md`
- `docs/ROADMAP_EXPERIENCES_MAIS_V8.md`
- `docs/DECISION_RECHERCHE_MAIS_V8.md`
- `docs/V8_META_REVALIDATION.md`
- `docs/V8_SYNTHESE_RESULTATS.md` (ce document)
- `.ai/TICKETS_RD_V8.md`

---

*V8 — synthèse des résultats — 2026-05-30. Étude scientifique mature, statut `RESEARCH_ONLY_NOT_TRADING` confirmé.*
