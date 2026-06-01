# DÉCISION RECHERCHE MAIS — V8 (PRÉ-EXPÉRIENCES)

**Date** : 2026-05-30.
**Statut** : pré-expérience V8. Ce document est mis à jour à la fin de chaque sprint V8.
**Verdict global actuel** : `RESEARCH_ONLY_NOT_TRADING`.

---

## Cadre

Ce document répond aux 15 questions de cadrage de V8, **avec l'état actuel de connaissance V7 et les caveats**. Toute conclusion non encore prouvée par V8 est marquée `[À VÉRIFIER V8]`. Aucune décision de bot ou d'indicateur n'est prise dans ce document — il prépare la décision.

---

## 1. Qu'est-ce qui explique le mieux CBOT ?

**Connu (V0–V7) :**

- **Bilans mondiaux WASDE** (ending_stocks / use mondial) — driver fondamental.
- **Surprises WASDE z-score** : signal de mouvement court terme.
- **COT non-commercial positioning** : signal cyclique (extremes percentile90 corrélés aux reversements).
- **Météo US** (GDD, heat stress, rain deficit, Drought Monitor) : driver saisonnier juin-août dominant.
- **Crop Progress / Crop Condition** : signal de révision rendement US.
- **Parité éthanol** : ancre demande.
- **Soja/maïs ratio** : substitution rotation futures.
- **EUR/USD** : indirect via demande export.
- **Brazil safrinha** : driver lié à la production secondaire qui pèse sur Q2-Q3.

**Résultats quantitatifs V7 :**

- CBOT J+60 direction (HistGB) : DA 62.4%, AUC 67.5%.
- CBOT drawdown 5pct H20 : AUC ≈ 0.75, top20 ≈ 0.89.
- CBOT large_down 3pct H60/H90 : AUC ≈ 0.71/0.70.

**Verdict provisoire** : CBOT est expliqué par un mix S&D mondial + positionnement spéculatif + météo Corn Belt. La cible la plus prédictible n'est pas la direction brute mais le **risque de drawdown** à H20.

**À vérifier V8 (`V8-CBOT-LAB-PLUS`)** :
- Triple barrier ±3/±5 % bat-il drawdown ?
- Conditionnels (stocks tendus, COT extreme, weather stress) sont-ils stables LOYO ?

---

## 2. Qu'est-ce qui explique le mieux EMA ?

**Connu :**

- EMA brut absolu = quasi non explicable (DA ≈ 0.50, AUC ≈ 0.50).
- EMA contient ≈ 94% de l'information de niveau CBOT_EUR (corr 0.94) + un résidu structurel.
- Cointégration EMA/CBOT_EUR confirmée (Engle-Granger p ≈ 7e-7, demi-vie 22.8j).
- Causalité contemporaine dominante (corr returns 1j ≈ 0.34) ; lead-lag mostly_contemporaneous.

**Verdict provisoire** : EMA s'explique structurellement par `P_CBOT × FX + basis_EU`. Le prix EMA pur n'est pas le bon objet d'étude. La **prime européenne (basis)** est le résidu informatif.

**À vérifier V8** : confirmer que le basis seul (z-score + régime) capte la plupart du signal vs un modèle complet.

---

## 3. Qu'est-ce qui explique le mieux le premium EMA/CBOT ?

**Connu :**

- **Basis_z** : driver direct.
- **Saison** (nov-jan = pression récolte EU, jul-aug = stress yield).
- **EU stocks / utilisation** (théorie du storage).
- **Flux import Ukraine** (parité d'export).
- **TTF gas** (coût séchage).
- **EUR/USD** (modificateur indirect).
- **Roll mechanics** (artefact prix EMA).
- **Liquidité EMA** (OI faible = basis bruité).

**Résultats V6 sur `y_rel_outperform_h90`** :
- classic seul : AUC 0.928
- meta seul : AUC 0.902
- classic + meta : AUC 0.937 (+0.010)

**Fragilité (V8 §4)** : protocole walk-forward classique, pas nested. **REVALIDATION V8 REQUISE**.

**À vérifier V8 (`V8-META-REVALIDATION`)** : si AUC chute > 0.20 sous protocole nested → l'explication "meta-features améliorent l'explication" est invalide.

---

## 4. Quelles cibles sont les meilleures ?

**Connu V7** :

| Cible | n | AUC | Verdict |
|---|---:|---:|---|
| `y_rel_outperform_h40` classic | 503 | 0.768 | GO_RESEARCH |
| `y_rel_outperform_h90` classic + meta | 503 | 0.937 | PROMISING [À REVALIDER] |
| `y_cbot_drawdown_5pct_h20` | n/a | 0.750 | GO_RESEARCH |
| `y_cbot_large_down_3pct_h90` | n/a | 0.716 | GO_RESEARCH |
| `y_rel_outperform_when_basis_extreme_h40` | 65 | 0.954 | FRAGILE |
| `y_rel_outperform_when_basis_extreme_h90` | 29 | 1.000 | FRAGILE |
| `y_up_h40_ema` (direction absolue) | — | 0.529 | NO_GO |

**Verdict provisoire** :
- **Cœur exploitable** : `y_rel_outperform_h40/h90` (premium relatif).
- **Meilleur risque CBOT** : `y_cbot_drawdown_5pct_h20`.
- **Conditionnel intéressant mais fragile** : `y_rel_outperform_when_basis_extreme_*`.

**À vérifier V8** : ajout des cibles V8 (triple-barrier, conditionnels, basis_compression/expansion/reversion).

---

## 5. Quelles cibles sont rejetées ?

| Cible | Verdict |
|---|---|
| `y_up_h*_ema` (direction absolue EMA) | NO_GO |
| Stockage EMA | NO_GO |
| CQR prix absolu EMA | NO_GO (cover insuffisant) |
| `y_storage_*` | NO_GO |
| Fair value comme prédicteur OOF du premium | NO_GO (V7-32) |
| Distributional forecast premium (V7-35) | POORLY_CALIBRATED |

---

## 6. Quelles features sont vraiment utiles ?

**Connu V7 (V7-37 stabilité)** :
- `corn_dist_to_52w_high` : feature la plus stable.
- Familles `basis_cbot` et `all_ema_curve` : +0.07 et +0.08 delta DA vs CBOT-only.
- Familles `price_levels`, `liquidity` : +0.05 et +0.04 delta DA.
- Famille `continuous_lags` : marginal (+0.01 delta DA, q BH élevé).

**Familles à retirer (EXP-BENCH-03 V5)** :
- adjusted returns
- slope
- spreads
- carry
- flags

**Verdict provisoire** : `basis + curve + price_levels + liquidity` = cœur des features EMA-related. Sur CBOT : COT + WASDE + drought + Crop Progress + ethanol parity + soja ratio.

**À vérifier V8 (`V8-EXPERTS-OOF`, `V8-META-FEATURES-V3`)** : importance OOF + stabilité rolling, comparaison rolling SHAP V8 vs V7-37.

---

## 7. Quelles données manquent encore ?

Voir `docs/DATA_SOURCES_MAIS_CBOT_EURONEXT_V8.md §15` pour priorisation. Principales lacunes :

| Donnée | Priorité | Statut |
|---|---|---|
| EMA settlement officiel Euronext | CRITIQUE | proxy uniquement |
| EC MARS Bulletin EU (yield, NDVI) | CRITIQUE | manquant |
| FAS Export Sales corn (key API) | CRITIQUE | API_KEY absente |
| Eurostat COMEXT import/export | CRITIQUE | manquant |
| FranceAgriMer bilans + cereobs | CRITIQUE | manquant |
| FOB Ukraine + FOB Bordeaux | HAUTE | manquant |
| Météo EU pondérée production | HAUTE | partiel |
| Baltic Dry Index + sub-indices | HAUTE | partiel |
| EU ETS CO2 + Engrais | MOYENNE | manquant |
| CONAB Brazil + Bolsa AR | MOYENNE | manquant |
| Dalian DCE futures | MOYENNE | collector existe, à activer |

---

## 8. Est-ce que le meta-model est robuste ?

**Réponse actuelle** : **INDÉTERMINÉE** [À VÉRIFIER V8 — `V8-META-REVALIDATION`].

- V6 affirme AUC 0.937 sur `y_rel_outperform_h90` (n=503) avec walk-forward classique.
- V7-03 nested AUC 0.5454 — mais sur la mauvaise cible (fallback `y_up_h20`).
- Aucune comparaison directe V6 sur protocole V7 strict n'existe.

**Décision** : V8-META-REVALIDATION doit conclure. Trois scénarios possibles :

| Verdict | Action V8 |
|---|---|
| `META_PREMIUM_ROBUST` | indicateur design lancé, paper en design |
| `META_PREMIUM_USEFUL_BUT_OVERSTATED` | indicateur hybride règle + meta, poids modeste |
| `META_PREMIUM_FRAGILE / OVERFIT / NO_GO` | retour aux règles simples + V9 cadrage |

---

## 9. Est-ce que les règles simples battent le ML ?

**Réponse actuelle** : **INDÉTERMINÉE** [À VÉRIFIER V8 — `V8-BACKTEST-V3` comparaison directe].

- Hypothèse H28 : règle `basis_z > 1.5` bat le meta-model en backtest coût 5 €/t.
- Hypothèse H38 : règle combinée `basis_z > 1.5 × season ∈ {nov, dec, jan}` est plus stable.

**Décision V8** : tester explicitement règle pure vs meta-model en backtest, sur les mêmes folds, avec les mêmes coûts. Si la règle bat le meta après coûts → privilégier la règle dans l'indicateur final (plus simple, plus explicable).

---

## 10. Est-ce que les backtests research-only sont encore positifs avec coûts réalistes ?

**Connu V7-13** :
- Best `full_signal` : 59 trades, hit 33.9%, PnL +47.57 €/t, profit factor 3.44, max DD -3.5.
- `top10` : PnL -17.515 €/t (négatif) → instabilité au seuil sélectif.
- Stress test 5/8 €/t **non publié**.

**Réponse actuelle** : positif sans stress, **incertain avec stress**.

**Décision V8** : V8-BACKTEST-V3 publie obligatoirement le PnL à coût 5 €/t et 8 €/t, avec slippage 1–2 €/t et leave-one-year-out. Si PnL devient négatif à 5 €/t → **backtest non utilisable comme preuve indicateur**.

---

## 11. Est-ce qu'un indicateur est envisageable ?

**Réponse actuelle** : **CONDITIONNEL**. L'architecture est claire (cf §7 réflexion V8) mais les conditions ne sont pas remplies :

| Condition | Statut |
|---|---|
| Source EMA officielle | NON (proxy uniquement) |
| Meta-model verdict ∈ {ROBUST, USEFUL_BUT_OVERSTATED} | INDÉTERMINÉ |
| BH global publié | NON |
| Red team passée | NON |
| Backtest stable rolling 12m + PF > 1.3 @ 5 €/t | INDÉTERMINÉ |
| P(correct) calibrée ECE < 0.05 | NON (ECE 0.12+) |

**Décision V8** : V8 doit dégager si les 6 conditions sont remplissables. Si oui → INDICATOR_DESIGN_READY. Si non → publier les gaps et revoir le périmètre.

---

## 12. Quel type d'indicateur ?

**Architecture future (V7-28 raffinée)** :

```
INDICATOR_V8 = CBOT_module       (direction + drawdown + rally + vol)
            ⊕ EMA_premium_module (H40, H90)
            ⊕ Basis_regime
            ⊕ Seasonal
            ⊕ Roll_risk_filter
            ⊕ Data_quality_filter
            ⊕ Event_risk_filter
            ⊕ P(correct)
            ⊕ Abstention_logic
```

Sortie :
- `global_cbot_signal` ∈ {BULLISH, BEARISH, UNCERTAIN}
- `eu_premium_signal` ∈ {BULLISH, BEARISH, UNCERTAIN}
- `final_research_signal`
- `confidence` ∈ [0, 1]
- `drivers_haussiers`, `drivers_baissiers`
- `abstention_reasons`
- `horizon_recommandé`
- `statut: RESEARCH_ONLY_NOT_TRADING`

**Décision V8** : V8-INDICATOR-DESIGN-V2 livre le design détaillé (interfaces, schémas, logique abstention), **sans coder**.

---

## 13. Qu'est-ce qui manque avant un paper trading ?

1. **V8-META-REVALIDATION** verdict ∈ {ROBUST, USEFUL_BUT_OVERSTATED}.
2. **V8-RED-TEAM-PREMIUM** PASS sur tous les pics utilisés.
3. **V8-BACKTEST-V3** PF > 1.3 à coût 5 €/t avec slippage 1 €/t, rolling 12m positif.
4. **V8-PCORRECT-V3** ECE < 0.05.
5. **V8-BASIS-REGIME-V3** régimes interprétables, stables walk-forward.
6. **V8-DQ-V3** filtre DQ < 0.4 actif.
7. **V8-INDICATOR-DESIGN-V2** livré.
8. **V8-BOT-PAPER-DESIGN** livré.

---

## 14. Qu'est-ce qui manque avant un bot réel ?

1. Tout ce qui manque pour paper (cf §13).
2. **Source EMA officielle obtenue** (V7-01B).
3. **Paper trading 6–12 mois** avec PnL net stable > +25 €/t/an et drawdown max < -20 €/t.
4. **Hit rate stable > 60%** en live.
5. **P(correct) ECE < 0.05 en live**, pas seulement en backtest.
6. **Validation humaine** (revue mensuelle minimum).
7. **Conformité légale** : statut (publication / recommandation / produit financier) clair.
8. **Infrastructure** : monitoring drift, arrêt automatique sur DQ_score < seuil, logs erreurs taxonomy V7-14.

**Décision V8** : pas de bot réel avant **fin 2027** au plus tôt, et seulement si toutes les conditions ci-dessus sont remplies.

---

## 15. Quelles sont les prochaines étapes ?

**Sprint 1 (semaine actuelle)** : Phase A
- V8-INFRA-HOLDOUT
- V8-INFRA-REGISTRY
- V8-INFRA-LEAKAGE
- V8-FRAGILE-FLAGS-AUDIT
- V8-RULE-TRAIN-ONLY-AUDIT
- V8-CALIBRATION-PLATT-ISO
- V8-EMBARGO-ROBUSTNESS

**Sprint 2** : V8-MT-BH-GLOBAL + V8-RED-TEAM-PREMIUM (en parallèle).

**Sprint 3** : V8-META-REVALIDATION (critique).
- Si verdict positif → Sprint 4+.
- Si verdict négatif → V8 PIVOT vers règles simples uniquement.

**Sprint 4-6** : extension labs, experts, basis regime, seasonal, roll, DQ, fair value, cross-market, causality.

**Sprint 7** : distributional, event study, P(correct), backtests.

**Sprint 8** : synthèse + indicator design + bot paper design + DECISION update.

---

## VERDICT V8 POST-EXÉCUTION (MAJ 2026-05-30)

**FRAGILE — INDICATEUR NON PRÊT, BOT NON PRÊT, PAPER NON PRÊT.**

### Résumé exécutif post-exécution

V8 a tourné 8 expériences scientifiques + V8-META-REVALIDATION + Phase A. Les résultats publiés dans `docs/V8_SYNTHESE_RESULTATS.md` :

1. **V8-META-REVALIDATION** : meta-model V6 H90 AUC 0.937 → AUC médiane V8 nested = 0.598. Verdict `META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE`. Sur H40 : 0.768 → 0.615 (FRAGILE).
2. **V8-BACKTEST-V3** : top20 cost-0 PnL +172 €/t, mais NÉGATIF dès cost 1 €/t. Règle simple `basis_z > 1.5` catastrophique en backtest (hit 24%).
3. **V8-RED-TEAM-PREMIUM** : `y_rel_outperform_h40` FAIL (p=0.06), H90 PASS marginal (p=0.01), basis_extreme PASS marginal (p=0.04).
4. **V8-CBOT-LAB-PLUS** : best `y_down_gt_5pct_h20` AUC 0.62, n=4625, PROMISING.
5. **V8-EMA-PREMIUM-LAB-PLUS** : best `y_basis_compression_h20` AUC 0.65, n=139, GO_RESEARCH (nouvelle cible V8).
6. **V8-SEASONAL-V3** : `jul_aug` AUC 0.62 (n=237, vraie poche), `jan_mar`/`apr_jun` AUC 0.35/0.40 (signal inversé exploitable), `dec` AUC 0.92 (n=65, FRAGILE).
7. **V8-CROSS-MARKET-V3** : EMA_ADDS_TO_CBOT confirmé.
8. **V8-PCORRECT-V3** : Isotonic bien calibrée (ECE 0.025), mais base classifier trop faible.
9. **V8-EMBARGO-ROBUSTNESS** : EMBARGO_NEUTRAL. Le delta V6/V8 n'est pas un effet embargo.

### VERDICT V8

**`RESEARCH_HYBRID_RULES_PREFERRED` avec contrainte forte : INDICATEUR NON PRÊT — étude en `RESEARCH_DEEPER` pour V9.**

L'étude doit progresser sur :
- (a) Acquisition données officielles (Euronext NextHistory, EC MARS, FAS Export Sales, FOB, Ukraine).
- (b) Approfondissement saisonnalité jul_aug + signaux inversés jan_mar/apr_jun.
- (c) Validation `y_basis_compression_h20` (nouvelle cible V8, AUC 0.65) sur plus de données.
- (d) Module structurel `P_EMA = f(CBOT, FX, basis_z, season, roll, DQ)` au lieu de meta-stacking.
- (e) Test contrastive learning sur cibles déséquilibrées (`y_down_gt_5pct_h20`).

---

## VERDICT V8 PRÉ-EXPÉRIENCE (archive)

**INDÉTERMINÉ — CADRE PRÊT, EXPÉRIENCES À LANCER.**

L'étude est **techniquement préparée** pour V8 :
- Réflexion V8 livrée (`RECHERCHE_MAIS_REFLEXION_PRO_V8.md`).
- Sources de données documentées (`DATA_SOURCES_MAIS_CBOT_EURONEXT_V8.md`).
- Roadmap V8 livrée (`ROADMAP_EXPERIENCES_MAIS_V8.md`).
- Tickets V8 ouverts (30 tickets, `.ai/TICKETS_RD_V8.md`).
- Décision V8 pré-expérience livrée (ce document).

**Aucune décision d'indicateur ou de bot n'est prise avant la fin du Sprint 8.** Le statut reste `RESEARCH_ONLY_NOT_TRADING`.

**Trois verdicts V8 possibles à terme** :

| Verdict V8 final | Suite |
|---|---|
| `RESEARCH_COMPLETE_INDICATOR_DESIGN_READY` | Design indicateur + bot paper, pas d'exécution |
| `RESEARCH_HYBRID_RULES_PREFERRED` | Indicateur à base de règles, meta poids modeste |
| `RESEARCH_DEEPER_V9_REQUIRED` | Étude V9 cadrée, pas d'indicateur encore |

---

*Document V8 — décision pré-expérience — 2026-05-30. À mettre à jour après chaque sprint.*
