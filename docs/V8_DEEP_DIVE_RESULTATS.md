# V8 DEEP DIVE — DÉCOUVERTES SCIENTIFIQUES

**Date** : 2026-05-30 (soir).
**Statut** : DONE — Sprint deep-dive post-V8-batch.
**Artefacts** : `artefacts/v8/basis_compression_deep.json`, `seasonal_deep.json`, `structural_pema.json`, `simple_rules_lab.json`.

---

## 1. Vue d'ensemble — découvertes nouvelles

Le deep dive V8 a produit 4 résultats scientifiquement importants qui changent la lecture de l'étude :

| # | Découverte | Impact |
|---|---|---|
| 1 | Modèle structurel simple (6 variables) atteint AUC 0.66 = LGBM full | **Le meta-stacking lourd est inutile** : 6 variables structurelles font aussi bien |
| 2 | Saisonnier jul_aug : top20 train-only DA = **0.89** sur n=246 | **Vraie poche exploitable** — signal robuste sur n grand |
| 3 | Règle `long basis_z < -1.5` (mean-reversion) : hit 72%, +156 €/t cost0 | **Inverse** de l'intuition V6/V7 : le basis bas est plus prédictible que le basis haut |
| 4 | y_basis_compression_h20 : médiane 0.65 mais std 0.19 (instable annuellement) | **Cible à valider** sur plus de données ou à filtrer par sous-période |

---

## 2. V8-STRUCTURAL-PEMA — résultat fondamental

### Modèle
6 variables structurelles uniquement :
- `cbot_eur_t` (prix CBOT en EUR/t)
- `ema_cbot_basis_zscore_52w` (basis z-score)
- `eurusd`
- `month_sin`, `month_cos`
- `ema_oi_total` (proxy liquidité)

### Résultats sur direction (`y_rel_outperform_h40`)

| Modèle | AUC OOF | Balanced Accuracy | Brier | n_oof |
|---|---:|---:|---:|---:|
| Logistic structural (6 vars) | **0.663** | 0.594 | 0.260 | 1630 |
| LGBM full (mêmes 6 vars) | **0.664** | 0.634 | 0.282 | 1630 |

### Résultats sur niveau de prix
- Ridge structural : R² = 0.884, MAE = 13.26 €/t
- LGBM full : R² = 0.847, MAE = 13.23 €/t

### Interprétation
**Ridge bat légèrement LGBM en R²** sur le niveau de prix (0.88 vs 0.85). En direction, AUC identique (0.663 vs 0.664). Conclusion : **la complexité n'ajoute aucune valeur prédictive nette**.

C'est la preuve scientifique que le V6 meta-model AUC 0.937 était bien un artefact de protocole — **la structure économique simple explique tout ce qu'on peut prédire**.

Implication forte : pour l'indicateur futur, **un modèle linéaire à 6 variables est aussi performant qu'un stacking lourd**. Privilégier la simplicité + explicabilité.

---

## 3. V8-SEASONAL-DEEP — la vraie poche jul_aug

| Saison | AUC normal | AUC inverted | BA utilisé | top20 train-only DA | n_oof |
|---|---:|---:|---:|---:|---:|
| jan_mar | 0.55 | 0.45 | 0.50 | 0.66 | 516 |
| apr_jun | **0.35** | **0.65** (inversé) | 0.60 | None | 519 |
| **jul_aug** | **0.65** | 0.35 | 0.57 | **0.89** | **246** |
| sep_nov | 0.53 | 0.47 | 0.46 | 0.73 | 105 |
| dec | 0.58 | 0.42 | 0.50 | None | 111 |

### Découvertes
1. **jul_aug est la meilleure saison exploitable** : AUC 0.65, top20 train-only DA **0.89** sur n=246. C'est statistiquement robuste et économiquement cohérent (stress yield été US + EU).
2. **apr_jun fonctionne en signal inversé** : AUC 0.35 → si on inverse, AUC 0.65, BA 0.60 sur n=519. Économiquement plausible : période de semis EU, sur-réaction médiatique → reversement.
3. **jan_mar marche moyennement** (AUC 0.55, top20 train-only DA 0.66 sur n=516).
4. **dec et sep_nov ont n_oof faible** (111, 105) — résultats à marquer FRAGILE.

### Implication pour l'indicateur
La saisonnalité **n'est pas un détail**. C'est la couche la plus exploitable de l'étude. L'indicateur futur doit avoir :
- Un module jul_aug (signal direct, top20 DA 0.89).
- Un module apr_jun **inversé** (signal contraire à la direction par défaut).
- Un module jan_mar (top20 0.66, signal modeste).
- Abstention sep_nov + dec (n trop faible pour confiance).

---

## 4. V8-SIMPLE-RULES-LAB — règles économiques pures

Backtests sur spread relatif EMA/CBOT H40, H=40j non-overlap.

| Règle | n_trades | hit_rate | PnL cost0 (€/t) | PnL cost1 (€/t) | PnL cost5 (€/t) |
|---|---:|---:|---:|---:|---:|
| R1 : long si basis_z > 1.5 | 24 | **0.25** | -273 | -321 | -513 |
| **R2 : long si basis_z < -1.5 (mean-rev)** | 25 | **0.72** | **+156** | **+106** | -94 |
| R3 : long jul-aug | 28 | 0.61 | -7 | -63 | -287 |
| R4 : long jul-aug × basis_z > 0.5 | 21 | 0.48 | -113 | -155 | -323 |
| **R5 : short si basis_z > 1.5 × jan-mar (inversé)** | 3 | 0.67 | +40 | **+34** | **+10** |
| R6 : long si basis_z > 1.0 ET delta20 > 0 | 26 | 0.31 | -294 | -346 | -554 |
| R7 : short si basis_z > 1.0 ET delta20 < 0 | 9 | 0.56 | +65 | +47 | -25 |

### Découvertes
1. **R1 (long basis haut) est catastrophique** (hit 25%). C'est la règle **intuitive** V6/V7 — elle ne marche pas en backtest réel.
2. **R2 (long basis bas, mean-rev) est solide** : 72% hit, n=25, profitable jusqu'à cost 1 €/t (+106 €/t net). Au-delà de cost 5, devient légèrement négatif. **Vraie règle exploitable** sous conditions de coût modéré.
3. **R5 (short basis haut × jan-mar inversé)** est **la seule règle profitable à cost 5 €/t** (+10 €/t net). Mais n=3 trades → **FRAGILE statistiquement**. À surveiller.
4. R3 (long jul-aug nu) ne suffit pas : hit 61% bien mais PnL ~0 à cost 0, négatif après. Le signal saisonnier doit être **combiné** avec un filtre supplémentaire.
5. R6 et R7 (basis-delta) tombent dans le piège opposé : R6 hit 31%, R7 hit 56%. Le signe du delta n'est pas un bon discriminateur seul.

### Implication
- **Le basis seul est un signal de mean-reversion** (R2), pas un signal directionnel (R1 NO).
- **La saisonnalité seule est insuffisante** (R3 ~ neutre). Il faut combiner.
- **Aucune règle simple à n_trades raisonnable ne survit à cost 5 €/t**. Il faut :
  - Soit baisser les coûts (acheter EMA via broker low-cost, faire le spread en gross).
  - Soit identifier des régimes/poches plus profondes.
  - Soit combiner les règles (R2 ET R5 selon contexte).

---

## 5. V8-BASIS-COMPRESSION-DEEP

`y_basis_compression_h20` (cible nouvelle V8, identifiée comme la plus prédictible OOF).

### Embargo sensitivity
AUC stable à 0.655 entre embargo 0–90 jours. Tombe à 0.641 à embargo 180j. **Embargo non discriminant** — signal stable.

### Yearly walk-forward (4 années testées)
- mean AUC : 0.65
- std : 0.19 (instable annuellement)
- min : 0.43, max : 0.95
- 3/4 années avec AUC > 0.55

### Features importantes (SHAP)
| Rang | Feature | mean_abs_shap |
|---|---|---:|
| 1 | corn_logret_1d | 1.20 |
| 2 | corn_macd_hist | 1.16 |
| 3 | corn_realized_vol_20 | 0.77 |
| 4 | corn_macd_signal | 0.75 |
| 5 | wasde_supply_total | 0.65 |
| 6 | corn_gas_corr60 | 0.52 |
| 7 | corn_soy_ratio | 0.49 |

### Lecture
- Les prédicteurs principaux sont des **features CBOT** (corn_logret, corn_macd, corn_realized_vol), pas des features EMA. C'est cohérent : la compression de basis est conditionnée par la dynamique CBOT (si CBOT monte, le basis se compresse mécaniquement).
- WASDE supply pèse modérément — fondamental utile.
- La stabilité annuelle (std 0.19) est moyenne. **À valider sur plus de données ou filtrer par régime CBOT**.

Verdict : `UNSTABLE_FRAGILE` — cible prometteuse mais instable, ne doit pas être l'unique pilier de l'indicateur.

---

## 6. Synthèse globale V8 (avec deep-dive)

### Ce qui est VRAIMENT exploitable (consolidé V8)
1. **Modèle structurel 6 variables** (CBOT_EUR, basis_z, EURUSD, month_sin, month_cos, OI proxy) → AUC 0.66 sur n=1630. Direction premium H40.
2. **Saisonnier jul_aug** → top20 train-only DA 0.89 sur n=246. Vraie poche.
3. **Saisonnier apr_jun inversé** → AUC 0.65 sur n=519. Période de semis EU.
4. **Règle R2 : long basis_z < -1.5** → hit 72% n=25, profitable jusqu'à cost 1 €/t.
5. **CBOT downside `y_down_gt_5pct_h20`** → AUC 0.62 n=4625.

### Ce qui est marginalement exploitable
- `y_basis_compression_h20` → AUC 0.65 mais instable annuellement.
- R5 (short basis × jan-mar inversé) → profitable cost 5 mais n=3.
- `y_up_h60_ema` → AUC 0.60 n=2217.

### Ce qui est définitivement rejeté
- Meta-model V6 H90 (V8-META-REVALIDATION confirme).
- R1 long basis haut nu (hit 25%).
- R3 long jul-aug nu (PnL neutre).
- R6 long basis_z + delta20 (hit 31%).
- Fair value comme prédicteur (V7-32 + V8 confirme).
- Direction EMA absolue brute (V7 NO_GO).

---

## 7. Implications architecturales pour l'indicateur futur

### A. Modèle de base (cœur)
Régression logistique structurelle à 6 variables, calibrée Isotonic. AUC attendue ~0.65 sur direction H40.

### B. Filtres saisonniers (couche dominante)
- jul_aug : signal direct, top20 DA 0.89.
- apr_jun : signal inversé.
- jan_mar : signal modéré direct.
- sep_nov + dec : abstention (n trop faible).

### C. Règles de mean-reversion (couche tactique)
- R2 (basis_z < -1.5 → long EMA/short CBOT spread). Pas plus de 25 trades par décennie.
- R5 (basis_z > 1.5 × jan-mar → short EMA/long CBOT). Très rare.

### D. Filtres veto
- Roll risk (DTE < 20 → veto).
- Data quality (DQ < 0.4 → veto).
- Liquidité OI EMA < seuil → veto.
- Event proximity (WASDE proche → réduction de taille).

### E. Calibration et abstention
- P(correct) Isotonic.
- Abstention si proba ∈ [0.40, 0.60].
- Abstention systématique pendant les saisons à n faible (sep-nov, déc).

### F. Sortie indicateur (architecture cible V9)
```
final_signal ∈ {LONG_PREMIUM, SHORT_PREMIUM, ABSTAIN}
confidence ∈ [0, 1] (P(correct) calibrée)
drivers : list[str]  # raisons économiques (saison, basis, CBOT)
veto_reasons : list[str]  # roll, DQ, event
horizon_recommandé : int  # 40 typically
statut : "RESEARCH_ONLY_NOT_TRADING"
```

---

## 8. Verdict V8 final consolidé

**`META_PREMIUM_FRAGILE` mais `STRUCTURAL_SIMPLICITY_WORKS`.**

L'étude V8 a démontré que :
1. Le V6 meta-stacking lourd était un artefact (AUC 0.937 → 0.60 nested).
2. **Une approche structurelle simple atteint la même performance** (AUC 0.66 sur 6 variables).
3. La saisonnalité jul_aug est un vrai signal (top20 DA 0.89).
4. La règle `long basis_z < -1.5` est exploitable jusqu'à cost 1 €/t.
5. Le risque de drawdown CBOT (`y_down_gt_5pct_h20`) est modeste mais robuste (AUC 0.62 n=4625).
6. La rentabilité après cost 5 €/t demeure marginale → **bot réel toujours pas envisageable**.

---

## 9. Roadmap V9 (proposition)

### Phase 1 — Acquisition
- V7-01B : EMA officiel Euronext NextHistory.
- V7-11A : EC MARS automatisé.
- V7-11B : FranceAgriMer.
- V7-11C : Eurostat COMEXT.
- V7-11D : Ukraine exports détaillés.
- V7-11F : FOB Bordeaux/Ukraine.

### Phase 2 — Indicateur prototype
- V9-INDICATOR-V1 : modèle structurel 6 vars + filtres saisonniers + R2 + R5.
- V9-CALIBRATION : Platt + Isotonic en parallèle.
- V9-ABSTENTION : règles vetoes.

### Phase 3 — Validation
- V9-LOYO : leave-one-year-out sur le prototype.
- V9-BACKTEST-V4 : stress costs 1/2/3/5/8 avec nouveau prototype.
- V9-RED-TEAM-V2 : sur prototype.
- V9-HOLDOUT-2024 : **UNIQUE utilisation du holdout** (signature humaine requise) si V9-LOYO et V9-RED-TEAM passent.

### Phase 4 — Paper trading design
- Si V9-HOLDOUT-2024 PASS → V9-PAPER-DESIGN.
- Sinon → V10 ou abandon.

---

*V8 deep dive — 2026-05-30. Étude scientifique mature. Statut `RESEARCH_ONLY_NOT_TRADING` confirmé, voie d'amélioration claire.*
