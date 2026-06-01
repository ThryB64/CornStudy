# V9 — Indicateur structurel hybride de la prime EMA/CBOT

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING` — prototype validé en recherche, non promu en production.
**Modules** : `src/mais/indicator/structural_indicator_v9.py`, runner `src/mais/scripts/run_v9.py`.
**Artefacts** : `artefacts/v9/structural_indicator_v9.json`, `loyo_v9.json`, `backtest_v4.json`, `red_team_v2.json`.
**Holdout 2024** : verrouillé, jamais touché (`artefacts/v9/` n'utilise que le dataset filtré).

---

## 1. Objectif

V8 a démontré (`docs/V8_DEEP_DIVE_RESULTATS.md`) que le meta-stacking lourd V6 (AUC affichée 0.937)
était un artefact de protocole : revalidé en nested strict, il tombe à 0.60. À l'inverse, **un modèle
structurel à 6 variables atteint AUC 0.66** sur la direction de la prime. V9 transforme ce constat en
**indicateur explicite, calibré, avec abstention et vetoes**, puis le valide honnêtement.

## 2. Architecture

### A. Cœur structurel (6 variables)
Régression logistique sur :
`cbot_eur`, `basis_z` (`ema_cbot_basis_zscore_52w`), `eurusd`, `month_sin`, `month_cos`, `oi_proxy`.
- OOF walk-forward, **purged embargo 40 jours**.
- **Calibration Isotonic apprise sur le train uniquement** (anti-leakage).
- Cible : `y_rel_outperform_h40` (EMA surperforme CBOT sur 40 jours).

### B. Règles tactiques mean-reversion (rares, prioritaires)
- **R2** : `basis_z < -1.5` → `LONG_PREMIUM` (mean-reversion, hit ~72% V8).
- **R5** : `basis_z > 1.5` et mois ∈ {jan, fév, mars} → `SHORT_PREMIUM`.

### C. Vetoes (depuis colonnes réelles)
- `ema_data_availability_score < 0.4` → veto data quality.
- `ema_oi_total` sous le 10ᵉ percentile → veto liquidité.
- `days_to_next_wasde ≤ 2` → veto proximité événement.
- mois ∈ {fév, mai, juil, oct} → veto roll-risk proxy (mois précédant les échéances H/M/Q/X).

### D. Décision et calibration
- Vetoes → `ABSTAIN`.
- Règle déclenchée → signal tactique (confiance 0.80).
- Sinon cœur : `p > 0.56` → LONG, `p < 0.44` → SHORT, sinon `ABSTAIN` (bande morte ±0.06).
- `confidence = |p − 0.5| × 2` (calibrée Isotonic).

### Sortie
`{signal ∈ {LONG_PREMIUM, SHORT_PREMIUM, ABSTAIN}, confidence, drivers, veto_reasons, horizon=40, statut}`.

---

## 3. Correction scientifique majeure : rejet de l'inversion saisonnière

Le deep-dive V8 recommandait une **inversion du signal en avril-juin** (AUC 0.35 → 0.65 supposé) et une
**abstention en sept-déc** (n faible). V9 a testé ces hypothèses sur l'OOF structurel réel et les **falsifie** :

| Couche de signal | DA directionnelle | n actifs |
|---|---:|---:|
| Cœur structurel direct + deadband | **0.646** | 1450 |
| Cœur + abstention sep-déc, sans inversion | 0.641 | 1235 |
| Cœur + inversion apr-juin (hypothèse V8) | **0.476** | 1235 |

DA du cœur par saison (direct, seuil 0.5) : jan-mars 0.61, **apr-juin 0.71** (meilleure, NON inversée),
juil-août 0.55, sep-nov 0.63, déc 0.71.

**Conclusion** : l'inversion apr-juin détruit le signal ; l'abstention sep-déc n'est pas justifiée (le cœur
y est performant). V9 garde donc le **cœur direct sur toutes les saisons**. La saison ne sert plus que de
label de driver (jul-août = poche connue). C'est une application directe de la leçon V8 §7 : *la
simplicité structurelle gagne ; les couches d'overlay ajoutées dégradent le cœur.*

---

## 4. Résultats mesurés (dataset hors holdout 2024)

### Cœur structurel (OOF forward, purged embargo 40j)
| Métrique | Valeur |
|---|---:|
| AUC (calibré) | **0.656** |
| AUC (brut) | 0.659 |
| Balanced accuracy | 0.619 |
| top20 DA | 0.735 |
| Brier (raw / cal) | 0.256 / 0.257 |
| ECE (raw / cal) | 0.141 / 0.154 |
| n OOF | 1546 |

> Note calibration : l'Isotonic n'améliore pas l'ECE ici (folds courts) ; le signal reste honnête mais la
> calibration fine est à reprendre avec plus de données officielles (V9-DATA-01).

### Signaux déployés
- Coverage **14.4%** (853 signaux actifs / 5940), 619 LONG / 234 SHORT, 5034 ABSTAIN.
- **Accuracy directionnelle 0.627**. Par tier de confiance : low 0.59, mid 0.59, **high (≥0.6) 0.67**.
- Snapshot le plus récent (2025-04-30) : `LONG_PREMIUM`, confiance 0.32.

### V9-IND-02 — Leave-One-Year-Out
- 15 années testées, **mean AUC 0.77**, std 0.14, min 0.36, max 0.96, **14/15 années AUC > 0.55**.
- Verdict `LOYO_STABLE`.
- **Caveat honnête** : la LOYO entraîne sur les autres années **y compris futures** → elle mesure la
  *consistance* du signal, pas la performance forward. L'estimation forward honnête reste l'OOF (0.656),
  pas la LOYO. L'écart 0.77 vs 0.656 reflète exactement ce biais non-causal de la LOYO.

### V9-IND-03 — Backtest V4 stressé (spread EMA/CBOT H40, non-overlap, 74 trades)
| Coût €/t/leg | PnL total €/t | hit rate | profit factor | max DD €/t | années + |
|---:|---:|---:|---:|---:|---:|
| 0 | **+381** | 0.69 | 2.14 | −70 | 80% |
| 1 | **+233** | 0.64 | 1.61 | −105 | 67% |
| 2 | **+85** | 0.53 | 1.19 | −155 | 53% |
| 3 | −63 | 0.49 | 0.88 | −230 | 40% |
| 5 | −359 | 0.43 | 0.47 | −406 | 20% |
| 8 | −803 | 0.22 | 0.10 | −798 | 13% |

**Seuil de rentabilité ≈ 2.5 €/t par leg.** C'est une amélioration nette sur V8 (où les règles nues
cassaient dès 1 €/t). Mais à coûts réalistes (5 €/t) le prototype reste perdant.

### V9-IND-04 — Red team V2 (permutation, 100 perms)
- AUC observée 0.656 vs perm 95ᵉ pct ; **p-value = 0.0099** → `SIGNAL_PASS`.
- Le signal du cœur structurel n'est pas du bruit.

---

## 5. Verdict V9

| Composant | Verdict |
|---|---|
| Cœur structurel 6 vars | **SIGNAL RÉEL** (AUC 0.656, red team p=0.0099) |
| Inversion saisonnière apr-juin (hypothèse V8) | **REJETÉE** (DA 0.476) |
| Abstention sep-déc en bloc | **REJETÉE** (non justifiée OOF) |
| Indicateur déployé (cœur + règles + vetoes) | DA 0.627, coverage 14%, **rentable jusqu'à ~2.5 €/t/leg** |
| LOYO | STABLE mais biais non-causal — lecture prudente |
| Promotion production / trading | **NON** — `RESEARCH_ONLY_NOT_TRADING` |

**Verdict global : `STRUCTURAL_INDICATOR_RESEARCH_GO` / `PRODUCTION_NO_GO`.**

Le prototype V9 est le meilleur indicateur honnête de l'étude à ce jour : signal statistiquement
significatif, simple, explicable, calibré, avec abstention. Il bat les règles V8 en robustesse aux coûts.
Mais il ne survit pas aux coûts de transaction réalistes (5 €/t) et repose encore sur des prix EMA proxy
(`barchart_proxy_exploratory`). Il n'est pas prêt pour la production.

---

## 6. Limites

1. **Prix EMA proxy** (`barchart_proxy_exploratory`, MAE ~37 €/t vs proxy CBOT→EUR). Le settlement
   officiel Euronext (V9-DATA-01) reste requis avant tout claim.
2. **Rentabilité fragile** : seuil de coût ≈ 2.5 €/t/leg, sous le coût réaliste (5 €/t).
3. **Calibration imparfaite** (ECE cal ≥ raw sur folds courts).
4. **LOYO non-causale** : ne pas la lire comme une performance forward.
5. **Coverage faible** (14%) : l'indicateur est très sélectif, donc peu de signaux par an.

---

## 7. Suite (V9 → V10)

- **V9-DATA-01..03** (`WAITING_DATA`) : EMA officiel Euronext NextHistory, EC MARS, FranceAgriMer/Eurostat.
- **V9-HOLDOUT-2024** (`BLOCKED`) : usage UNIQUE du holdout 2024 — autorisé seulement si V9-IND-02 et
  V9-IND-04 restent PASS sur données officielles ET sous signature humaine explicite.
- Reprise de la calibration sur historique plus long, et test d'une couche d'abstention par incertitude
  (largeur d'intervalle CQR) plutôt que par bande morte fixe.

---

*V9 — 2026-05-31. Indicateur structurel honnête. La complexité reste inutile ; la rentabilité réelle reste*
*non démontrée à coûts réalistes. Statut `RESEARCH_ONLY_NOT_TRADING` confirmé.*
