# V8-META-REVALIDATION — RAPPORT

**Date** : 2026-05-30.
**Statut** : DONE.
**Artefact** : `artefacts/v8/meta_revalidation.json`.
**Verdict global** : `META_PREMIUM_FRAGILE` (avec `META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE` sur H90).

---

## 1. Question scientifique

Le meta-model V6 affichait `AUC = 0.937` sur `y_rel_outperform_h90` (n=503, walk-forward classique). Cette performance survit-elle à des protocoles plus stricts (purged embargo, leave-one-crop-year, non-overlap, no-crisis) ?

## 2. Protocole

Dataset : `data/processed/features.parquet` + market + EMA continuous, **holdout 2024 retiré** (5940 lignes utilisables).

Cibles testées :
- `y_rel_outperform_h40`
- `y_rel_outperform_h90`
- `y_rel_outperform_when_basis_extreme_h40`
- `y_rel_outperform_when_basis_extreme_h90`

Cibles construites dans `ensure_rel_targets()` :
```
y_rel_outperform_hH = 1 si pct_change(EMA, H).shift(-H) > pct_change(CBOT_eur, H).shift(-H)
when_basis_extreme  = y_rel_outperform | (|basis_z_52w| > 1.5)
```

Combinaisons testées (8) :
1. classic_only (60 features quantitatives non-target)
2. meta_only (3 OOF auxiliaires : `oof_y_up_h20`, `oof_y_up_h20_ema`, `oof_y_up_h40_ema`)
3. classic_plus_meta
4. basis_rule_only (`basis_z > 1.5` long / `< -1.5` short)
5. season_rule_only (one-hot mois nov-jan, jul-août, avr-juin)
6. classic_plus_basis
7. classic_plus_season
8. full_stack

Protocoles testés (5 actifs) :
- A. Walk-forward V6 classique (5 splits, sans embargo)
- B. Purged embargo H=90j
- C. Purged embargo 2H=180j
- D. Leave-one-crop-year nested
- E. Non-overlap strict H=90j
- F. No-crisis (exclure 2020 + 2022)

Total : jusqu'à 8 × 6 = 48 expériences par cible. 40 ont produit des résultats valides par cible.

## 3. Résultats agrégés

| Cible | Verdict | median_AUC | min_AUC | max_AUC | delta_vs_V6 | n_combos×proto |
|---|---|---:|---:|---:|---:|---:|
| `y_rel_outperform_h40` | `META_PREMIUM_FRAGILE` | **0.6151** | 0.2925 | 0.7170 | **-0.1529** | 40 |
| `y_rel_outperform_h90` | `META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE` | **0.5982** | 0.3203 | 0.7140 | **-0.3388** | 40 |
| `y_rel_outperform_when_basis_extreme_h40` | `META_PREMIUM_FRAGILE` | 0.6410 | 0.3148 | 0.7547 | — | 40 |
| `y_rel_outperform_when_basis_extreme_h90` | `META_PREMIUM_FRAGILE` | 0.6403 | 0.3247 | 0.7559 | — | 40 |

**Lecture** :
- Pour `y_rel_outperform_h90`, le pic V6 (AUC 0.937) s'effondre à AUC médiane 0.598. Delta -0.34. C'est l'archétype d'un overfit ou d'un leakage de protocole (walk-forward classique avec meta-features OOF qui peuvent fuiter par chevauchement de fenêtres).
- Pour H40, la chute est moins violente (0.768 → 0.615, delta -0.15) mais le résultat passe en zone FRAGILE.
- Les cibles `basis_extreme` qui affichaient AUC 0.95–1.00 (n=29–65) s'effondrent autour de 0.64. Comme attendu pour des n < 100.

## 4. Détail par combinaison (cible `y_rel_outperform_h90`)

| Combinaison | Walk-forward A | Embargo H | Embargo 2H | LOCY | Non-overlap | No-crisis |
|---|---:|---:|---:|---:|---:|---:|
| classic_only | 0.62 | 0.61 | 0.61 | 0.59 | 0.59 | 0.60 |
| meta_only | 0.71 | 0.70 | 0.69 | 0.63 | 0.66 | 0.63 |
| classic_plus_meta | 0.68 | 0.67 | 0.67 | 0.61 | 0.63 | 0.63 |
| basis_rule_only | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| season_rule_only | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| classic_plus_basis | 0.62 | 0.61 | 0.61 | 0.59 | 0.59 | 0.60 |
| classic_plus_season | 0.62 | 0.61 | 0.61 | 0.59 | 0.59 | 0.60 |
| full_stack | 0.68 | 0.67 | 0.67 | 0.61 | 0.63 | 0.63 |

(Valeurs approximatives, voir artefact JSON pour précision.)

**Observations** :
- `meta_only` est le plus performant (AUC ~0.70 en walk-forward, mais dégrade à 0.63 en LOCY et no-crisis).
- Le gain `classic + meta` vs `classic` seul est positif mais modeste (+0.05 AUC walk-forward, +0.02 nested).
- Les règles basis/season nues sont neutres (AUC ~0.50) — elles ne battent pas le hasard sur cette cible.
- Le V6 AUC 0.937 ne s'est jamais reproduit sur n'importe quel protocole testé V8.

## 5. Explication probable du gap V6 → V8

1. **Protocole V6 walk-forward classique** : pas d'embargo, fenêtres H90 chevauchent à 89% entre obs consécutives. Avec target H90, les labels sont fortement corrélés temporellement → le modèle "voit" implicitement le futur.
2. **Meta-features V6 `pred_*_oof`** : pour entraîner le meta sur 503 obs, les OOF étaient calculées sur des fenêtres internes qui pouvaient déborder sur la fenêtre de test externe. L'isolation outer/inner n'était pas strictement appliquée.
3. **n=503 dans V6** : population sélectionnée après filtres, ce qui réduit la taille effective et peut introduire un biais d'échantillonnage.
4. **Pas d'embargo explicite dans V6** : confirmé par lecture du code V6 historique.

## 6. Implications V8

### A. Pour le rapport global de l'étude
- Toute mention "meta-model V6 AUC 0.937" doit être **immédiatement requalifiée** comme `FRAGILE_V6_NOT_REPLICATED_UNDER_V7_PROTOCOL`.
- La table d'implémentation `docs/PROFESSIONAL_STUDY_REPORT.md` doit refléter le verdict V8.
- Le rapport V7 final (`docs/FINAL_CORN_STUDY_V7.md`) doit recevoir une note V8 en tête.

### B. Pour la roadmap V8
- V8 doit pivoter : moins de meta-model lourd, plus de signaux simples + filtres.
- Les cibles H40 sont récupérables avec AUC ~0.62 — modeste mais réel.
- Les cibles H90 deviennent suspectes systémiquement.
- Les conditionnels basis_extreme à n < 100 sont rejetés.

### C. Pour l'indicateur futur
- L'indicateur ne peut plus s'appuyer sur le meta-model H90 V6 comme source forte.
- Il doit reposer sur :
  - CBOT direction H60 (modeste mais robuste)
  - CBOT drawdown / large_move (à revalider V8)
  - règles économiques simples (basis_z + saison + roll filter)
  - data quality + abstention
- Pas de "BULLISH/BEARISH" sortant d'un meta-model gonflé.

### D. Pour le bot futur
- Recul de 6+ mois. Le seuil "indicator ready" devient `règles simples + filtres robustes + paper trading 12 mois` plutôt que `meta-model fort`.

## 7. Statut

`RESEARCH_ONLY_NOT_TRADING` — confirmé.
**V6 meta verdict** : `META_PREMIUM_FRAGILE / LIKELY_OVERFIT_OR_LEAKAGE` — confirmé.
**Prochaine étape** : V8-CBOT-LAB-PLUS et V8-EMA-PREMIUM-LAB-PLUS pour identifier les cibles réellement prédictibles sous protocole strict.

## 8. Note méthodologique

V8 n'invalide pas l'utilité scientifique de V6 — il **précise** : la performance walk-forward classique V6 était optimiste. Les meta-features OOF ajoutent un peu de valeur (+0.02 AUC nested vs classic seul), mais beaucoup moins que les +0.17 AUC apparents V6. La conclusion économique reste : la prime EMA/CBOT contient de l'information exploitable, mais à un niveau bien plus modeste (~0.62 AUC nested) que prétendu V6 (0.937 walk-forward).

---

*V8-META-REVALIDATION — rapport produit après exécution complète 2026-05-30.*
