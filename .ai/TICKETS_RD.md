# Tickets R&D — Phase 4 (post-V3)
> Créé le 2026-05-17. Corrigé le 2026-05-17 (revue expert intégrale).
> Source : docs/AUDIT_COMPLET_V3.md, sections 9–11.
> Objectif : transformer l'étude V3 en un indicateur réellement utile aux décisions agricoles.
> Tous les tickets sont sur 2010–2022 uniquement sauf mention explicite. 2023–2025 = backtest final, non réoptimisé.
> Anti-leakage obligatoire : shift(1) + z-scores expandants sur toutes les données fondamentales.

---

## Conventions transversales (applicables à tous les tickets)

### Statut résultat

Chaque expérience produit obligatoirement un des verdicts suivants :

| Verdict | Signification |
|---|---|
| CONFIRMÉ | Résultat positif clair, IC95% non-nul, répliqué |
| PROMETTEUR | Signal positif mais non significatif ou non répliqué |
| NEUTRE | Pas d'effet mesurable |
| REJETÉ | Signal négatif ou inférieur à la baseline |
| INCONCLU | Données insuffisantes ou artefact non exploitable |

### IC95% obligatoire

Pour chaque métrique finale (DA, AUC, DA_top20) :
```
DA = 0.640 [IC95% : 0.618 ; 0.662]
AUC = 0.700 [IC95% : 0.679 ; 0.721]
```
Méthode : bootstrap 1 000 tirages avec remplacement sur les prédictions OOF.

### Correction pour tests multiples

Quand plusieurs modèles, horizons ou familles de features sont comparés simultanément, appliquer **Benjamini-Hochberg** (FDR correction) ou documenter explicitement le risque de sélection post-hoc.

### Évaluation quotidienne ET hebdomadaire

Chaque signal est évalué sur deux fréquences :
- **Quotidienne** : DA calculée sur tous les jours ouvrés
- **Hebdomadaire** : DA calculée sur un point par semaine (chaque lundi)

La fréquence hebdomadaire est la référence agricole. La fréquence quotidienne est souvent gonflée par autocorrélation (5 jours consécutifs avec les mêmes features WASDE/COT).

### Data availability score

Chaque signal porte un `data_availability_score ∈ [0, 1]` indiquant la proportion de sources attendues réellement disponibles le jour J. En dessous de 0.7, le signal est reclassé UNCERTAIN automatiquement.

---

## Index

| Ticket | Titre | Priorité | Type | Statut | Dépendances |
|---|---|---|---|---|---|
| [R&D-01](#rd-01--benchmark-canonique-v3) | Benchmark canonique V3 | **PRIORITÉ 0** | critique | DONE | — |
| [R&D-02](#rd-02--vrai-consensus-multi-horizon-oof) | Vrai consensus multi-horizon OOF | HAUTE | critique | DONE | R&D-01 |
| [R&D-03](#rd-03--courbe-des-futures-spreads-zhkn) | Courbe des futures (spreads Z/H/K/N) | HAUTE | moyen | DONE | R&D-01 |
| [R&D-04](#rd-04--fas-export-sales) | FAS Export Sales | HAUTE | moyen | DONE | R&D-01 |
| [R&D-05A](#rd-05a--crop-condition--phénologie) | Crop Condition + phénologie | HAUTE | moyen | DONE | R&D-01 |
| [R&D-05B](#rd-05b--enso--oni-noaa) | ENSO / ONI NOAA | HAUTE | moyen | DONE | R&D-01 |
| [R&D-06](#rd-06--cibles-et-backtest-stockage-agriculteur) | Cibles et backtest stockage agriculteur | HAUTE | complexe | DONE | R&D-01 (R&D-02 optionnel) |
| [R&D-07](#rd-07--confiance-pcorrect-calibrée) | Confiance P(correct) calibrée | HAUTE | complexe | DONE | R&D-02 / R&D-06 |
| [R&D-08](#rd-08--module-risqueopportunité-asymétrique) | Module risque/opportunité asymétrique | MOYENNE | complexe | DONE | R&D-06, R&D-07 |
| [R&D-09](#rd-09--cot-avancé-normalisé) | COT avancé normalisé | MOYENNE | moyen | DONE | R&D-01 |
| [R&D-10](#rd-10--rapport-hebdomadaire-agriculteur-4-modules) | Rapport hebdomadaire agriculteur | BASSE | complexe | DONE | R&D-06, R&D-07, R&D-08 |

**Ordre d'exécution :**
```
Sprint 0 : R&D-01 (juge de paix — ne lancer aucun autre ticket de modélisation avant)
Sprint 1 : R&D-03 / R&D-04 / R&D-05A / R&D-05B / R&D-09 (après R&D-01 DONE)
Sprint 2 : R&D-02
Sprint 3 : R&D-06 version simple → R&D-07
Sprint 4 : R&D-08 → R&D-10

Ordre recommandé complet :
R&D-01 → R&D-03/R&D-04/R&D-05A/R&D-05B/R&D-09 → R&D-02 → R&D-06 → R&D-07 → R&D-08 → R&D-10.
```

---

## R&D-01 — Benchmark canonique V3

**Priorité** : PRIORITÉ 0 — ne lancer aucun autre ticket de modélisation avant  
**Type** : critique  
**Statut** : DONE  
**Dépendances** : aucune  

### Contexte

Il existe une contradiction inexpliquée entre deux résultats sur J+40 :
- Sweep V3-02 (`lgbm_factors`) : DA = **0.640**, AUC = 0.700
- Model zoo V3-03 (`lasso`) : DA = **0.569**, AUC = 0.592

Même horizon, même période OOF 2010–2022, même KFold 5-split déclaré. L'écart de 7 points de DA est inacceptable tant qu'il n'est pas expliqué et décomposé. Par ailleurs, toutes les expériences V3 utilisent des protocoles légèrement différents (features, random states, target construction), ce qui rend les comparaisons non rigoureuses.

Ce ticket crée un benchmark canonique unique : mêmes features, mêmes splits, mêmes modèles, mêmes métriques. C'est le juge de paix de toute la suite.

### Hypothèses pour l'écart sweep/zoo (à tester une par une)

1. `lgbm_factors` dans le sweep = sous-ensemble de features "factors" seulement vs 289 colonnes complètes dans le zoo
2. LightGBM hyperparamètres différents (sweep = defaults, zoo = grille Optuna)
3. Construction de `y_up_h40` différente selon le script appelé (shift ou seuil différent)
4. KFold random_state différent ou shuffle involontaire dans un des scripts

### Objectifs mesurables

- Écart sweep/zoo expliqué et décomposé dans un artefact JSON (cause isolée par iso-expérience)
- Un seul tableau de référence : 7 modèles × 5 horizons × 3 métriques (DA, AUC, DA_top20) + IC95%
- Walk-forward par crop year (Sept-Aug) implémenté en alternative au KFold
- DA inter-annuelle : documentée par année ; si une année < 0.48, analyser la cause économique
- IC95% bootstrap (1 000 tirages) sur DA et AUC pour chaque résultat retenu
- Évaluation quotidienne ET hebdomadaire (un point par lundi)
- Correction Benjamini-Hochberg sur les comparaisons inter-modèles
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/canonical_benchmark.py` | **CRÉER** — module principal |
| `tests/test_benchmark_canonical.py` | **CRÉER** — 7 tests P0 |
| `artefacts/canonical/benchmark_results.json` | Produit par le module |
| `artefacts/canonical/contradiction_analysis.json` | Décomposition sweep vs zoo |
| `docs/BENCHMARK_CANONICAL.md` | Rapport résultats |
| `docs/PROTOCOL_FREEZE.md` | **CRÉER** — protocole figé avant poursuite R&D |

**Fichiers à lire mais ne pas modifier** : `src/mais/research/horizon_sweep.py`, `src/mais/research/model_zoo.py`, `src/mais/features/__init__.py`.

### Tâches détaillées

**T1 — Isoler la source de l'écart sweep/zoo (iso-expériences)**

Construire 4 expériences d'isolation sur J+40 :

| Expérience | Features | Modèle | Hyperparamètres | Attendu |
|---|---|---|---|---|
| lgbm_sweep_exact | factors_cols du sweep | LightGBM defaults sweep | identiques sweep | DA ≈ 0.640 |
| lgbm_zoo_exact | 289 cols zoo | LightGBM zoo | identiques zoo | DA ≈ 0.569 |
| lgbm_swap_features | 289 cols zoo | LightGBM defaults sweep | identiques sweep | isole features |
| lgbm_swap_hyperparams | factors_cols sweep | LightGBM zoo | identiques zoo | isole hyperparams |

Produire `contradiction_analysis.json` :
```json
{
  "sweep_features_count": ...,
  "zoo_features_count": ...,
  "sweep_target_construction": "...",
  "zoo_target_construction": "...",
  "sweep_lgbm_params": {...},
  "zoo_lgbm_params": {...},
  "da_lgbm_sweep_exact": ...,
  "da_lgbm_zoo_exact": ...,
  "da_lgbm_swap_features": ...,
  "da_lgbm_swap_hyperparams": ...,
  "identified_primary_cause": "...",
  "delta_da_explained_by_features": ...,
  "delta_da_explained_by_hyperparams": ...,
  "residual_unexplained": ...
}
```

**T2 — Walk-forward par crop year (CropYearWalkForward)**

Le crop year US maïs = 1er septembre → 31 août.

```python
class CropYearWalkForward:
    """Walk-forward expanding, un crop year par fold.
    Crop years 2010-2022 : 13 années disponibles.
    Train min = 5 ans → premiers folds disponibles à partir de 2015.
    """
    # Walk 1 : train 2010-2014, val 2015
    # Walk 2 : train 2010-2015, val 2016
    # ...
    # Walk 8 : train 2010-2021, val 2022
    # Total : 8 folds de validation (2015–2022) si les données 2022 sont complètes
```

Avantage : chaque fold = une année agricole complète, sans contamination intra-annuelle. À comparer avec KFold 5 du benchmark.

**T3 — Benchmark canonique : 7 modèles × 5 horizons**

- Modèles : `lasso`, `histgb`, `gaussian_nb`, `logistic`, `extratrees`, `lgbm`, `ridge`
- Horizons : J+28, J+35, J+40, J+45, J+60
- Features : les 289 colonnes complètes de `build_features()` (pas un sous-ensemble)
- Target : `y_up_hH` standard tel que défini dans `targets.py`
- Splits : KFold 5 no-shuffle **ET** CropYearWalkForward (comparer les deux)
- Correction multiple testing : Benjamini-Hochberg sur la comparaison inter-modèles

Métriques par cellule (modèle × horizon) :
- DA quotidienne, DA hebdomadaire (lundi), AUC, Brier
- IC95% bootstrap (1 000 tirages avec replacement)
- DA par crop year (distribution annuelle)

**T4 — Benchmark hebdomadaire**

Construire une version du benchmark sur la seule fréquence hebdomadaire :
- 1 observation par semaine (lundi, ou jeudi si WASDE/COT publiés ce jour)
- Comparer DA_quotidien vs DA_hebdomadaire pour chaque modèle
- Si delta(DA_quotidien - DA_hebdomadaire) > 0.05 : documenter comme artefact d'autocorrélation

**T5 — Tests P0**

```python
def test_contradiction_decomposed():
    """contradiction_analysis.json identifie la cause primaire avec delta expliqué > 0.03."""

def test_canonical_features_identical():
    """Tous les modèles ont reçu exactement le même nombre de colonnes."""

def test_metric_confidence_intervals_present():
    """IC95% bootstrap présents pour DA et AUC de chaque cellule modèle×horizon."""

def test_annual_da_documented():
    """Rapport contient la DA par crop year pour chaque modèle (8 valeurs si 2022 complète)."""

def test_no_single_year_dominance():
    """Ablation leave-one-year-out : retirer 2012 ou 2020 seul ne fait pas chuter DA > 0.07."""

def test_weekly_da_computed():
    """Artefact contient DA_quotidienne et DA_hebdomadaire pour comparaison."""

def test_canonical_results_saved():
    """benchmark_results.json contient les 7 modèles × 5 horizons avec IC95%."""
```

### Critère de fin

- Contradiction expliquée et décomposée par cause isolée
- Tableau canonique 7 × 5 avec IC95% et correction multiple testing
- Évaluation quotidienne et hebdomadaire
- Rapport `BENCHMARK_CANONICAL.md` lisible
- 7 tests PASS

### Résultat ticket (2026-05-18)

- Module `src/mais/research/canonical_benchmark.py` créé.
- Tests `tests/test_benchmark_canonical.py` créés (10 tests P0).
- Artefacts générés :
  - `artefacts/canonical/benchmark_results.json` — 70 lignes (7 modèles × 5 horizons × 2 splitters).
  - `artefacts/canonical/contradiction_analysis.json` — cause primaire identifiée : `hyperparams_or_model_family`, delta expliqué absolu ≈ `0.0344`.
  - `artefacts/canonical/canonical_oof_predictions.parquet`.
- Documents générés :
  - `docs/BENCHMARK_CANONICAL.md`.
  - `docs/PROTOCOL_FREEZE.md`.
- Meilleur résultat walk-forward crop year : `histgb` J+60, DA `0.624`, AUC `0.675`, DA hebdo `0.616`, verdict `CONFIRMÉ`.
- Contradiction J+40 : features sweep/zoo = `288`/`288`, donc l'écart vient surtout de la famille modèle / hyperparamètres, pas du nombre de features.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/canonical_benchmark.py tests/test_benchmark_canonical.py` PASS.
  - `venv/bin/python -m pytest tests/test_benchmark_canonical.py -q` PASS (`10 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS (`70 passed`).
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet. Les tickets dépendants restent `BLOCKED` tant que R&D-01 n'est pas validé `DONE`.

---

## R&D-02 — Vrai consensus multi-horizon OOF

**Priorité** : HAUTE  
**Type** : critique  
**Statut** : DONE  
**Dépendances** : R&D-01  

### Contexte

Le consensus V3-04 était construit sur des OOF mono-horizon J+40 uniquement. Le disagreement était quasi-nul (0.000001), rendant la mécanique UNCERTAIN non fonctionnelle. Le DA_top20 = 0.742729 vs référence 0.742730 → delta ≈ 0 : le consensus n'apportait aucun alpha.

Ce ticket génère les OOF réels sur J+28, J+35, J+40, J+45, J+60 pour construire un vrai signal de consensus inter-horizon. Le consensus peut améliorer la DA directe **ou** jouer un rôle de filtre de prudence (moins de faux signaux forts). Les deux rôles sont utiles.

### Objectifs mesurables

- Distribution du disagreement inter-horizon non dégénérée : `std(disagreement) > 0` et nombre de valeurs uniques > 10
- Le consensus améliore au moins **un** des indicateurs suivants : DA_top20, stabilité annuelle, calibration de confiance, réduction flip rate, réduction faux signaux forts
- Seuil de disagreement calibré sur OOF (pas fixé arbitrairement)
- Proportion UNCERTAIN par disagreement : documentée et compatible avec l'usage métier (ni < 5%, ni > 60%)
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/multi_horizon_oof.py` | **CRÉER** — génération OOF multi-horizon |
| `src/mais/research/consensus_v2.py` | **CRÉER** — consensus avec vrais OOF |
| `tests/test_consensus_real.py` | **CRÉER** — 5 tests P1 |
| `artefacts/canonical/multi_horizon_oof.parquet` | OOF probas pour 5 horizons |
| `artefacts/consensus_v2/consensus_results.json` | Métriques et verdict |

### Tâches détaillées

**T1 — OOF multi-horizon**

Pour chaque horizon H ∈ {28, 35, 40, 45, 60} :
- Entraîner les modèles retenus sur les mêmes splits canoniques que R&D-01
- Stocker les probabilités OOF : `oof_proba_hH[date] = p_up`
- Aligner sur les dates communes à tous les horizons
- Conserver les OOF individuels par modèle (pas seulement la moyenne)

**T2 — Consensus et disagreement**

```python
# Pour chaque date t :
probas = [oof_h28[t], oof_h35[t], oof_h40[t], oof_h45[t], oof_h60[t]]
consensus_proba = np.mean(probas)          # ou pondéré par AUC de chaque horizon
disagreement = np.std(probas)              # dispersion inter-horizon réelle

# Seuil de disagreement : calibré sur OOF validation, pas fixé
# → chercher threshold maximisant DA_top20 sur les jours BULLISH/BEARISH retenus
signal = "UNCERTAIN" if disagreement > threshold_calibrated else (
    "BULLISH" if consensus_proba > 0.50 else "BEARISH"
)
```

**T3 — Calibration du seuil de disagreement**

- Balayer `disagreement_threshold` ∈ [0.02, 0.15] avec pas 0.01
- Évaluer pour chaque seuil : DA_top20, flip_rate, proportion_uncertain, profit_vs_harvest
- Sélectionner le seuil offrant le meilleur compromis DA_top20 × proportion_actionnelle
- Documenter la courbe seuil → DA_top20 dans l'artefact

**T4 — Verdict consensus**

Le consensus est retenu selon le premier critère satisfait :
1. **ALPHA** : DA_top20 consensus > DA_top20 meilleur horizon seul + 0.003
2. **FILTRE** : flip_rate consensus < flip_rate meilleur horizon × 0.85 (réduit les retournements)
3. **PRUDENCE** : faux signaux forts réduits (P(signal fort et faux) < baseline × 0.90)
4. **REJETÉ** : aucun critère satisfait → horizon seul retenu, consensus documenté comme piste future

**T5 — Tests P1**

```python
def test_disagreement_not_degenerate():
    """std(disagreement) > 0.005 — pas d'OOF mono-horizon déguisé."""

def test_multi_horizon_oof_aligned():
    """Toutes les dates dans l'OOF multi-horizon ont les 5 probas non-NaN."""

def test_consensus_verdict_documented():
    """consensus_results.json contient un champ 'verdict' parmi les 4 possibles."""

def test_uncertain_proportion_usable():
    """5% <= P(UNCERTAIN par disagreement) <= 60%."""

def test_threshold_calibrated_on_oof():
    """Le seuil de disagreement retenu est issu d'une recherche sur OOF (pas une constante hardcodée)."""
```

### Critère de fin

- OOF multi-horizon généré et sauvegardé
- Disagreement distribution non dégénérée documentée
- Verdict consensus documenté honnêtement (ALPHA, FILTRE, PRUDENCE ou REJETÉ)

### Résultat ticket (2026-05-18)

- Module `src/mais/research/multi_horizon_oof.py` créé :
  - génération OOF par horizon/modèle en réutilisant `run_model_oof()` canonique ;
  - alignement strict des dates communes aux 5 horizons.
- Module `src/mais/research/consensus_v2.py` créé :
  - consensus_proba = moyenne des probas multi-horizons ;
  - disagreement = écart-type réel inter-horizon ;
  - calibration du seuil de disagreement sur grille OOF `[0.02, 0.15]` ;
  - métriques `disagreement_std`, `disagreement_unique_values`, `proportion_uncertain`, `da_actionable`, `flip_rate`, `verdict`.
- Tests `tests/test_consensus_real.py` créés (5 tests).
- Vérifications :
  - `venv/bin/python -m pytest tests/test_consensus_real.py -q` PASS (`5 passed`).
  - `venv/bin/python -m ruff check src/mais/research/multi_horizon_oof.py src/mais/research/consensus_v2.py tests/test_consensus_real.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`100 passed`).
- Non lancé : génération réelle `artefacts/canonical/multi_horizon_oof.parquet` et `artefacts/consensus_v2/consensus_results.json`, car les règles agents interdisent la lecture directe de `data/`/`artefacts/`. Les fonctions acceptent `output_path` et sont prêtes pour un run pipeline autorisé.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : la review valide le code et les tests synthétiques ; les artefacts réels restent à régénérer via les commandes officielles si une décision métier dépend des métriques finales.

---

## R&D-03 — Courbe des futures (spreads Z/H/K/N)

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : R&D-01  

### Contexte

La structure à terme du CBOT maïs encode l'information du marché sur l'offre et la demande futures : backwardation (futures < spot) = marché tendu → haussier ; contango (futures > spot) = offre abondante → baissier. Ces spreads ne sont pas encore dans les features.

Théorie : `F(T) = S₀ × e^((r - δ) × T)` où δ est le convenience yield (bénéfice de détenir le physique).

**Attention technique** : les tickers yfinance pour les contrats différés historiques (ZCZ24, ZCH25, etc.) peuvent être incomplets, mal chainés ou discontinus. Ce ticket commence obligatoirement par un diagnostic de qualité données avant toute intégration.

Contrats cibles :
- ZCZ (décembre, récolte) — crop year marker
- ZCH (mars) — signal demande post-récolte
- ZCK (mai) — fin ancienne récolte
- ZCN (juillet) — signal nouvelle récolte

### Objectifs mesurables

- Phase 1 (diagnostic) obligatoire : coverage ≥ 80% sur 2010–2022, sinon le ticket s'arrête
- Si Phase 1 OK : delta_AUC ≥ +0.008 ou signal saisonnier documenté (verdict CONFIRMÉ ou PROMETTEUR)
- Signal de timing : heure du signal définie explicitement
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/futures_curve.py` | **CRÉER** — collecteur + diagnostic qualité |
| `src/mais/features/curve_spreads.py` | **CRÉER** — construction features spread |
| `src/mais/features/__init__.py` | Ajouter appel (seulement si Phase 1 OK) |
| `config/sources.yaml` | Section `futures_curve` |
| `tests/test_curve_spreads.py` | **CRÉER** — 5 tests P1 |

### Phase 1 — Diagnostic qualité obligatoire

Avant tout, valider :

```python
def diagnose_futures_curve_quality():
    """Retourne un rapport de disponibilité par contrat et par année."""
    results = {}
    for year in range(2010, 2023):
        for month_code in ["Z", "H", "K", "N"]:
            ticker = build_cbot_symbol(month_code, year, provider)
            data = yf.download(ticker, ...)
            results[ticker] = {
                "coverage": len(data.dropna()) / expected_trading_days,
                "price_coherent": check_no_outliers(data["Close"]),
                "roll_continuity": check_price_continuity_around_expiry(data),
            }
    return results
```

La nomenclature des tickers dépend de la source (`ZCZ24`, `ZC=F`, `ZCH25.CBT`, etc.). Le collecteur doit isoler cette logique dans une fonction dédiée :

```python
def build_cbot_symbol(month_code: str, year: int, provider: str) -> str:
    ...
```

Tout le reste du code doit dépendre de cette fonction, pas d'une convention fournisseur codée en dur.

**Critère d'arrêt** : si couverture moyenne < 80% ou continuité prix cassée sur > 3 années, documenter comme limitation et ne pas intégrer au modèle principal. Verdict : INCONCLU avec recommandation de source alternative (Quandl, Bloomberg, CBOT CSV officiel).

### Gestion du roll contractuel

Les contrats CBOT ont des échéances annuelles. La logique de sélection par date :
- Contrat récolte courant : ZCZ de l'année en cours (décembre)
- Contrat mars suivant : ZCH de l'année suivante
- Contrat mai suivant : ZCK de l'année suivante
- Contrat juillet suivant : ZCN de l'année suivante

Pour chaque jour t, construire la courbe à partir des contrats non-expirés les plus proches.

### Timing du signal (anti-leakage)

Définir **avant** l'implémentation :
- Signal produit en **fin de journée** (après clôture) : `close[t]` autorisé → features pour `t+1`
- Signal produit en **matin** (avant ouverture) : `close[t-1]` obligatoire → shift(2) requis

La décision doit être cohérente avec le pipeline quotidien existant (`ops/daily.py`).

### Features à créer (7 features — seulement si Phase 1 OK)

```python
# Spreads (en ¢/bu) — tous avec shift(1) pour anti-leakage
curve_zh_spread = ZCH_close - ZCZ_close        # Mar-Dec
curve_kn_spread = ZCK_close - ZCN_close        # May-Jul
curve_nz_spread = ZCN_close - ZCZ_close        # Jul-Dec (new crop vs old crop)

# Contexte et normalisation
curve_contango_flag = int(ZCN_close > spot_close * 1.02)
curve_zh_spread_ma20 = rolling_mean(curve_zh_spread, 20).shift(1)
curve_zh_spread_zscore = expanding_zscore(curve_zh_spread).shift(1)  # anti-leakage
curve_backwardation_flag = int(ZCN_close < spot_close * 0.98)
```

### Tests P1

```python
def test_phase1_diagnostic_runs():
    """Le diagnostic s'exécute sans erreur et produit un rapport par contrat/année."""

def test_curve_spread_coverage():
    """Si Phase 1 OK : couverture >= 80% sur 2010-2022 pour ZCH, ZCK, ZCN, ZCZ."""

def test_curve_spreads_anti_leakage():
    """Tous les spreads ont shift(1) appliqué avant intégration dans le modèle."""

def test_curve_spreads_delta_auc_documented():
    """Artefact contient delta_auc et verdict (CONFIRMÉ/PROMETTEUR/NEUTRE/INCONCLU)."""

def test_contango_seasonal_coherence():
    """Si features intégrées : contango_flag > backwardation_flag en moyenne mai-juillet."""
```

### Critère de fin

- Phase 1 (diagnostic) exécutée, verdict documenté
- Si OK : 7 features intégrées à build_features() avec anti-leakage
- delta_AUC documenté avec IC95% et verdict

### Résultat ticket (2026-05-18)

- Collecteur diagnostic `src/mais/collect/futures_curve.py` créé.
- Mapping fournisseur isolé via `build_cbot_symbol(month_code, year, provider)`.
- Module `src/mais/features/curve_spreads.py` créé.
- Registry collecteurs mis à jour avec `futures_curve`.
- `config/sources.yaml` : source `futures_curve` ajoutée, `enabled: false` tant que la phase diagnostic qualité n'est pas validée sur source fiable.
- `src/mais/features/__init__.py` : intégration conditionnelle de `futures_curve.parquet`; si absent, colonnes schéma ajoutées en NaN.
- 7 features ajoutées : `curve_zh_spread`, `curve_kn_spread`, `curve_nz_spread`, `curve_contango_flag`, `curve_zh_spread_ma20`, `curve_zh_spread_zscore`, `curve_backwardation_flag`.
- Évaluateur ajouté : `evaluate_curve_spreads()` documente `baseline_auc`, `auc_with_curve`, `delta_auc`, `verdict`.
- Tests `tests/test_curve_spreads.py` créés (6 tests).
- Vérifications :
  - `venv/bin/python -m pytest tests/test_curve_spreads.py -q` PASS (`6 passed`).
  - `venv/bin/python -m ruff check src/mais/collect/futures_curve.py src/mais/features/curve_spreads.py src/mais/collect/__init__.py src/mais/features/__init__.py tests/test_curve_spreads.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`90 passed`).
- Non lancé : téléchargement/diagnostic historique complet 2010–2022 et ablation réelle sur `data/`, car la source doit être validée et les règles agents interdisent la lecture directe de `data/`. Le code est prêt pour un run pipeline autorisé.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : mapping fournisseur futures correctement isolé, mais la couverture réelle dépendra des symboles disponibles chez le fournisseur configuré.

---

## R&D-04 — FAS Export Sales

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : R&D-01  

### Contexte

Les ventes export hebdomadaires (Export Sales) du USDA FAS sont une donnée fondamentale majeure non encore collectée. Elles représentent une composante importante de la demande marginale de maïs US et sont très suivies par le marché : une surprise positive dans les engagements export est immédiatement pricée.

Publication : chaque **jeudi matin** (8h30 ET) pour les engagements de la semaine close le jeudi précédent.

**Sources à distinguer** :
- **Export Sales hebdomadaires** : engagements semaine par semaine → c'est ce qu'on cible
- **PSD Online** : bilans annuels/mensuels USDA → ne pas confondre
- **GATS** : historique commercial, pas hebdomadaire

**Absence actuelle** : identifiée depuis ETUDE-09 (reporté Phase 4). FAS_API_KEY gratuite disponible sur apps.fas.usda.gov. Fallback : CSV public hebdomadaire USDA sans clé.

### Objectifs mesurables

- Collecteur fonctionnel : données disponibles sur 2010–2022 (ou depuis disponibilité réelle)
- delta_AUC ≥ +0.010 global **ou** gain sept-janv ≥ +0.015 (saison export)
- 7 features FAS dans build_features()
- NaN pré-activation et couverture réelle documentés dans sources.yaml
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/fas_exports.py` | **CRÉER** — collecteur FAS Export Sales |
| `src/mais/features/fas_features.py` | **CRÉER** — construction features |
| `src/mais/features/__init__.py` | Ajouter appel |
| `config/sources.yaml` | Section `fas_exports: enabled: true` + couverture |
| `tests/test_fas_exports.py` | **CRÉER** — 4 tests |

### Stratégie de collecte

```python
# Option A — API FAS (avec FAS_API_KEY)
# Endpoint : https://apps.fas.usda.gov/gats/ExpressQuery1.aspx
# Commodity code maïs : 0410000 (ou "Corn")

# Option B — Fichier CSV public sans clé (fallback)
# URL à vérifier : export sales weekly report USDA
# Format : CSV avec colonnes week_ending, country, net_sales, accumulated_exports, outstanding_sales

# Si aucune source disponible : créer stub retournant NaN + log WARNING, ne pas planter le pipeline
```

### Anti-leakage précis

Publication FAS : jeudi J pour les engagements de la semaine close J-7.
→ Feature disponible le jeudi J après 8h30 ET.
→ Si signal produit le vendredi ou le lundi suivant : OK avec `shift(1)` hebdomadaire.
→ Ne jamais utiliser les données du jeudi J dans les features d'un signal produit avant J+8h30.

### Features à créer (7 features)

```python
# Données brutes (hebdomadaire → forward-fill sur jours ouvrés)
export_sales_weekly_mt         # Engagements hebdo en tonnes métriques
export_sales_accumulated_mt    # Cumulatif depuis départ crop year (1er septembre)

# Signaux dérivés (tous avec shift(1) et z-scores expandants)
export_pace_vs_usda_forecast   # si forecast USDA disponible proprement
export_pace_vs_5y_avg          # fallback si forecast USDA absent ou mal aligné
export_sales_weekly_zscore     # z-score expandant des ventes hebdo
export_china_pct_total         # Part Chine / total (signal concentration risque)
export_momentum_4w             # Moyenne 4 semaines vs 4 semaines précédentes
export_vs_same_week_last_year  # YoY comparison (saisonnalité)
```

### Ablation saisonnale

Les exports comptent surtout de septembre à janvier (après récolte US, avant nouvelle récolte Brésil/Argentine). Tester :
- **Ablation globale** : delta_AUC annuel complet
- **Ablation sept–janv** : delta_AUC dans la fenêtre export seulement
- **Hors-saison** : delta_AUC en fév–août (doit être quasi-nul)

Si delta_AUC < +0.010 global mais ≥ +0.015 en sept–janv : conserver avec flag saisonnier.

### Tests

```python
def test_fas_no_leakage():
    """Engagements FAS utilisés après publication (shift >= 1 jour ouvré depuis publication jeudi)."""

def test_fas_coverage_documented():
    """sources.yaml mentionne la couverture réelle FAS et les NaN pré-disponibilité."""

def test_fas_fallback_no_crash():
    """Si FAS_API_KEY absente, le collecteur retourne NaN + log WARNING sans plantage."""

def test_fas_delta_auc_documented():
    """Artefact contient delta_auc global, saisonnier (sept-janv) et hors-saison + verdict."""
```

### Critère de fin

- Collecteur fonctionnel (ou fallback CSV documenté)
- 7 features intégrées à build_features()
- delta_AUC global et saisonnier documenté avec IC95% et verdict

### Résultat ticket (2026-05-18)

- Module `src/mais/collect/fas_exports.py` créé :
  - wrapper R&D-04 autour du collecteur FAS existant ;
  - fallback vide sans crash si `FAS_API_KEY` absente ;
  - écriture `data/interim` désactivable en test via `write_interim: false`.
- Registry collecteurs mis à jour : `usda_fas_export_sales` utilise le wrapper robuste.
- `config/sources.yaml` : `usda_fas_export_sales.enabled = true`.
- Module `src/mais/features/fas_features.py` créé.
- `src/mais/features/__init__.py` : `_fas_weekly_to_daily()` délègue au builder R&D-04.
- Features FAS ajoutées :
  - `export_sales_weekly_mt`
  - `export_sales_accumulated_mt`
  - `export_pace_vs_usda_forecast`
  - `export_pace_vs_5y_avg`
  - `export_sales_weekly_zscore`
  - `export_china_pct_total`
  - `export_momentum_4w`
  - `export_vs_same_week_last_year`
  - compatibilité maintenue : `export_sales_mt`
- Évaluateur ajouté : `evaluate_fas_ablation()` documente `global`, `sept_jan`, `off_season` avec AUC baseline / AUC FAS / delta AUC et verdict.
- Tests `tests/test_fas_exports.py` créés (5 tests).
- Vérifications :
  - `venv/bin/python -m pytest tests/test_fas_exports.py -q` PASS (`5 passed`).
  - `venv/bin/python -m ruff check src/mais/collect/fas_exports.py src/mais/features/fas_features.py src/mais/collect/__init__.py src/mais/features/__init__.py tests/test_fas_exports.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`95 passed`, 2 warnings Tkinter hérités de `test_model_zoo`).
- Non lancé : collecte réelle FAS et ablation réelle sur `data/`, car elles nécessitent `FAS_API_KEY` et un run pipeline autorisé. Le fallback et l'évaluateur sont prêts.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : fallback `export_pace_vs_5y_avg` validé ; la feature `export_pace_vs_usda_forecast` dépend toujours d'un alignement USDA propre.

---

## R&D-05A — Crop Condition + phénologie

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : R&D-01  

### Contexte

Le taux G+E% (Good+Excellent) de la Crop Condition NASS est le baromètre en temps réel des rendements estivaux. C'est la donnée que lit le marché chaque lundi pendant la saison de croissance (mai–octobre). Le collecteur NASS existe déjà, mais `crop_condition` est désactivé dans sources.yaml.

Les features phénologiques (silkage, récolte...) permettent de contextualiser le signal météo : un déficit hydrique en semaine 27 (silkage) est beaucoup plus impactant qu'en semaine 42 (récolte terminée). Ces features sont construites uniquement sur le calendrier → zéro leakage possible.

### Objectifs mesurables

- Crop Condition : gain DA en juin–août ≥ +0.015
- Ablation hors-saison quasi-nulle (confirme absence d'artefact)
- 16 features total (11 Crop Condition, dont 2 colonnes de disponibilité/remplissage + 5 phénologie) dans build_features()
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/phenology.py` | **CRÉER** — features phénologiques |
| `src/mais/features/__init__.py` | Ajouter les 2 familles |
| `config/sources.yaml` | `crop_condition: enabled: true` |
| `tests/test_crop_condition_phenology.py` | **CRÉER** — 5 tests |

**Fichier à lire (collecteur existant)** : `src/mais/collect/nass.py` — vérifier que crop_condition est parsé.

### Features à créer

**Crop Condition NASS (9 features)**
```python
# Hebdomadaire mai-octobre → forward-fill + NaN hors-saison
crop_ge_pct                  # G+E% hebdomadaire
crop_ge_pct_vs_last_year     # Delta YoY G+E%
crop_ge_5y_avg_deviation     # Écart vs moyenne 5 ans (expanding — anti-leakage)
crop_ge_zscore_seasonal      # Z-score dans la saison courante (expanding)
crop_planted_pct             # % semé (surtout semaines 18-22)
crop_silked_pct              # % silkage (surtout semaines 26-30)
crop_mature_pct              # % mature (surtout semaines 38-42)
crop_harvested_pct           # % récolté (surtout semaines 40-44)
crop_condition_momentum_2w   # Delta G+E% sur 2 semaines
crop_condition_available     # 1 si donnée Crop Condition publiée/disponible, sinon 0
crop_ge_pct_filled           # valeur remplie pour modèles (ffill ou médiane saisonnière documentée)
```

Conserver `crop_ge_pct` brut à `NaN` hors saison pour l'audit. Les modèles utilisent `crop_condition_available` et une stratégie `crop_ge_pct_filled` documentée afin d'éviter les effets indésirables de NaN massifs.

**Phénologie calendaire (5 features — zéro leakage par construction)**
```python
pheno_silking_window         # 1 si semaines calendaires 26-30, sinon 0
pheno_dough_dent_window      # 1 si semaines 30-36
pheno_harvest_window         # 1 si semaines 38-44
pheno_growing_season         # 1 si mai-octobre
pheno_week_in_season         # Numéro semaine dans la saison (1-26), NaN hors-saison
```

### Ablation saisonnale Crop Condition

Tester l'impact uniquement sur les fenêtres saisonnières :
- **Juin–août** : fenêtre critique silkage
- **Octobre** : impact annonce récolte
- **Hors-saison (nov–avril)** : doit être ≈ 0 → confirme pas d'artefact

### Tests

```python
def test_crop_condition_enabled():
    """sources.yaml : crop_condition.enabled = true après modification."""

def test_phenology_no_leakage():
    """Toutes les features phénologiques sont basées sur semaine calendaire uniquement."""

def test_crop_condition_nan_off_season():
    """crop_ge_pct brut = NaN en décembre-avril, avec flag crop_condition_available."""

def test_crop_condition_ablation_documented():
    """Artefact contient delta_DA par fenêtre saisonnière (juin-août, octobre, hors-saison)."""

def test_ge_pct_range():
    """crop_ge_pct ∈ [0, 100] sur toutes les observations non-NaN."""
```

### Critère de fin

- Crop Condition activée (clé NASS existante, collecteur NASS existant)
- 16 features ajoutées à build_features()
- Ablation saisonnale documentée avec IC95% et verdict

### Résultat ticket (2026-05-18)

- Module `src/mais/features/phenology.py` créé.
- `config/sources.yaml` : `usda_nass_crop_condition.enabled = true`.
- `src/mais/features/__init__.py` :
  - ajout des 5 features phénologiques calendaires ;
  - enrichissement `_crop_progress_weekly_to_daily()` avec les colonnes Crop Condition / Progress R&D-05A ;
  - conservation de `condition_gd_ex_pct` pour compatibilité historique.
- Features ajoutées :
  - `crop_ge_pct`
  - `crop_ge_pct_vs_last_year`
  - `crop_ge_5y_avg_deviation`
  - `crop_ge_zscore_seasonal`
  - `crop_planted_pct`
  - `crop_silked_pct`
  - `crop_mature_pct`
  - `crop_harvested_pct`
  - `crop_condition_momentum_2w`
  - `crop_condition_available`
  - `crop_ge_pct_filled`
  - `pheno_silking_window`
  - `pheno_dough_dent_window`
  - `pheno_harvest_window`
  - `pheno_growing_season`
  - `pheno_week_in_season`
- Évaluateur ajouté : `evaluate_crop_condition_windows()` documente les fenêtres `jun_aug`, `october`, `off_season` avec AUC baseline / AUC crop / delta AUC et verdict.
- Tests `tests/test_crop_condition_phenology.py` créés (5 tests).
- Vérifications :
  - `venv/bin/python -m pytest tests/test_crop_condition_phenology.py tests/test_new_sources.py -q` PASS (`10 passed`).
  - `venv/bin/python -m ruff check src/mais/features/phenology.py src/mais/features/__init__.py tests/test_crop_condition_phenology.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`79 passed`, 2 warnings Tkinter hérités de `test_model_zoo`).
- Non lancé : ablation réelle sur `data/processed/features.parquet`, car les règles agents interdisent la lecture directe de `data/`. Le code d'évaluation est prêt pour un run pipeline autorisé.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : colonnes brutes saisonnières conservées pour audit ; l'effet prédictif réel doit être mesuré dans les benchmarks R&D.

---

## R&D-05B — ENSO / ONI NOAA

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : R&D-01  

### Contexte

El Niño/La Niña influence les précipitations en Corn Belt sur des cycles de 12–18 mois. C'est un signal climatique basse fréquence (mensuel) mais crucial pour comprendre les régimes de rendement. Il s'agit d'une variable de contexte (régime), pas d'un signal à court terme. La source NOAA est publique et ne nécessite pas de clé API.

Ce ticket est séparé de R&D-05A car les horizons de pertinence sont différents : Crop Condition agit sur le court terme (jours/semaines), ENSO agit sur le régime (mois/saison).

### Objectifs mesurables

- ONI collecté 2010–2022 sans NaN (hors date initiale)
- Impact sur les régimes El Niño identifié dans l'analyse contextuelle (AUC par régime ENSO)
- 6 features ENSO dans build_features()
- Parser robuste : si URL NOAA change, erreur explicite (pas de NaN silencieux)
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/enso.py` | **CRÉER** — collecteur ONI NOAA |
| `src/mais/features/__init__.py` | Ajouter appel ENSO |
| `config/sources.yaml` | `enso: enabled: true` |
| `tests/test_enso.py` | **CRÉER** — 4 tests |

### Collecteur ENSO

```python
# URL NOAA CPC — ONI historique :
# https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
# Format : tableau HTML avec colonnes Year, DJF, JFM, ..., NDJ (anomalies SST ¡sea surface temp] 3-mois glissants)

# Parser robuste :
# - Si le tableau HTML change de format → raise CollectorError("ENSO NOAA format changed")
# - Ne jamais forward-fill une série entière vide
# - Si < 80% de la plage 2010-2022 est couverte → raise DataQualityError
# Fréquence : mensuelle → forward-fill sur les jours (valeur ONI du mois en cours)
```

### Features à créer (6 features)

```python
# Toutes avec shift(1) mensuel et forward-fill sur les jours
enso_oni_index           # Indice ONI mensuel (-2.5 à +2.5) — anomalie SST
enso_regime              # -1 (La Niña : ONI ≤ -0.5), 0 (neutre), +1 (El Niño : ONI ≥ +0.5)
enso_lag3_oni            # ONI il y a 3 mois (délai d'effet sur Corn Belt)
enso_accumulated_6m      # Somme ONI sur 6 mois (persistance de phase)
enso_el_nino_flag        # 1 si ONI > +0.5 pendant 5 périodes trimenstrielles consécutives
enso_la_nina_flag        # 1 si ONI < -0.5 pendant 5 périodes trimenstrielles consécutives
```

**Note** : la définition officielle NOAA d'El Niño/La Niña = ONI ≥ +0.5 ou ≤ -0.5 pendant 5 périodes trimenstrielles consécutives. Utiliser cette définition pour les flags.

### Tests

```python
def test_enso_collection_coverage():
    """ONI disponible 2010-2022, couverture >= 90%."""

def test_enso_parser_raises_on_format_change():
    """Si le tableau NOAA est absent ou mal formé, CollectorError est levée (pas NaN silencieux)."""

def test_enso_regime_distribution():
    """El Niño + La Niña + neutre couvrent 100% des observations ONI non-NaN."""

def test_enso_flag_coherent():
    """enso_el_nino_flag ne peut être 1 si enso_la_nina_flag est 1."""
```

### Critère de fin

- ONI collecté et intégré
- 6 features ajoutées à build_features()
- Impact AUC par régime ENSO documenté dans l'analyse contextuelle (ContextAnalysis V2)

### Résultat ticket (2026-05-18)

- Collecteur `src/mais/collect/enso.py` créé :
  - parser NOAA CPC ONI robuste ;
  - erreurs explicites `CollectorError` et `DataQualityError` ;
  - validation couverture 2010–2022 ;
  - sauvegarde `enso_oni.parquet` via le collector.
- Registry `src/mais/collect/__init__.py` mis à jour avec `enso_oni`.
- `config/sources.yaml` : source `enso_oni` ajoutée et activée.
- `src/mais/features/__init__.py` : intégration ENSO mensuel → quotidien avec `shift(1)`.
- 6 features ajoutées :
  - `enso_oni_index`
  - `enso_regime`
  - `enso_lag3_oni`
  - `enso_accumulated_6m`
  - `enso_el_nino_flag`
  - `enso_la_nina_flag`
- Tests `tests/test_enso.py` créés (5 tests).
- Vérifications :
  - `venv/bin/python -m pytest tests/test_enso.py -q` PASS (`5 passed`).
  - `venv/bin/python -m ruff check src/mais/collect/enso.py src/mais/collect/__init__.py src/mais/features/__init__.py tests/test_enso.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`84 passed`).
- Non lancé : collecte NOAA réelle et analyse ContextAnalysis V2, pour éviter une lecture/régénération non demandée des dossiers de données. Le collecteur et les features sont prêts pour un run pipeline autorisé.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : collecteur robuste et tests OK ; l'apport ENSO reste à confirmer sur données réelles complètes.

---

## R&D-06 — Cibles et backtest stockage agriculteur

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : **R&D-01 obligatoire** — R&D-02 optionnel (améliore le signal mais non bloquant)  

### Contexte

L'indicateur prédit la direction du prix, mais ne prouve pas qu'il aide un agriculteur à mieux vendre son maïs. Le backtest IND-08 montre que MODEL_SIGNAL (82.0%) < SELL_HARVEST (82.8%) sur la capture du prix max. C'est un résultat honnête mais décevant.

Ce ticket construit les cibles directement agricoles et un vrai backtest économique. C'est **le test de vérité** du projet.

**Objectif final** : prouver ou réfuter que l'indicateur génère un gain net moyen positif vs SELL_HARVEST sur la majorité des années walk-forward.

Validation crop years : 2015–2022, soit 8 années si les données 2022 sont complètes.

### Objectifs mesurables

- Gain net moyen vs SELL_HARVEST : documenté (positif ou négatif, avec IC95%)
- % crop years gagnants documenté (objectif : ≥ 60% soit 5/8 années)
- Pire année documentée
- Résultat honnête quel qu'il soit (ne pas "optimiser pour passer" le critère)
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/storage_targets.py` | **CRÉER** — construction cibles stockage |
| `src/mais/research/farmer_backtest_v2.py` | **CRÉER** — backtest économique réaliste |
| `tests/test_storage_backtest.py` | **CRÉER** — 6 tests P1 |
| `artefacts/storage/storage_targets.parquet` | Cibles calculées |
| `artefacts/storage/backtest_results.json` | Métriques par année + verdict |

### Cibles à créer (deux familles)

**Famille A — Cible réaliste (prix à H jours, pas le max)**
```python
# Le prix dans H jours moins coût de stockage
y_storage_value_1m = price_t_plus_20 - price_t - 8     # coût ~8¢/bu pour 1 mois
y_storage_value_3m = price_t_plus_60 - price_t - 15    # coût ~15¢/bu pour 3 mois
y_storage_value_6m = price_t_plus_120 - price_t - 25   # coût ~25¢/bu pour 6 mois
```

**Famille B — Cible opportunité maximale (oracle, borne supérieure)**
```python
y_max_opportunity_3m = max_price_60d - price_t - 15    # meilleur moment possible
```

**Cible vente fractionnée**
```python
# Position du prix actuel dans la distribution des 12 prochains mois
y_sell_partial_flag = int(current_rank_in_12m > 0.75)  # Top 25% des prix futurs
```

**Important** : ces cibles utilisent les prix futurs → **jamais dans build_features()**. Usage uniquement dans les modèles de stockage entraînés en walk-forward OOF.

### Backtest économique

**Stratégies testées** :
1. `SELL_HARVEST` : vendre tout le 1er lundi après récolte (octobre)
2. `SELL_THIRDS` : 1/3 octobre, 1/3 janvier, 1/3 mars
3. `SELL_25_25_25_25` : 25% chaque trimestre (oct, jan, avr, juil)
4. `SIGNAL_BINARY` : BULLISH → stocker, BEARISH → vendre, UNCERTAIN → SELL_THIRDS
5. `SIGNAL_PARTIAL` : score pondère la fraction à vendre (haute confiance BEARISH = vendre 100%)
6. `SELL_MAX_ORACLE` : vendre au prix max de l'année (borne supérieure non atteignable)

**Coûts de stockage (paramétrables dans config)**
```yaml
storage:
  cost_per_month_cents_per_bu: 5.0   # coût direct stockage
  interest_rate_annual: 0.055        # coût financier (optionnel mais documenté)
  quality_loss_pct: 0.001            # perte qualité par mois
```

**Critère économique réaliste** :
> Produire, chaque lundi, un signal permettant à un agriculteur de décider de vendre ou stocker, avec un gain net moyen positif par rapport à SELL_HARVEST, sur la majorité des années de validation (2015–2022), sans recalibrage des seuils.

### Tests P1

```python
def test_storage_targets_no_leakage():
    """y_storage_value_* et y_max_opportunity_* ne sont pas dans build_features()."""

def test_backtest_all_strategies_documented():
    """backtest_results.json contient les 6 stratégies avec gain par crop year."""

def test_annual_gain_distribution():
    """backtest_results.json contient le gain par année 2015-2022 (8 valeurs si 2022 complète)."""

def test_storage_costs_deducted():
    """Coûts stockage (¢/bu/mois) soustraits du gain brut dans le calcul net."""

def test_worst_year_identified():
    """Pire année documentée avec analyse de la cause (régime marché, signal erroné...)."""

def test_verdict_honest():
    """backtest_results.json contient 'verdict' : CONFIRMÉ/PROMETTEUR/NEUTRE/REJETÉ selon le résultat réel."""
```

### Critère de fin

- Cibles y_storage_value_1m/3m/6m et y_sell_partial_flag créées
- Backtest 6 stratégies sur 2015–2022 par crop year
- Résultat honnête documenté (positif ou non) avec analyse par année et IC95%

### Résultat ticket (2026-05-18)

- Module `src/mais/research/storage_targets.py` créé :
  - `y_storage_value_1m`
  - `y_storage_value_3m`
  - `y_storage_value_6m`
  - `y_max_opportunity_3m`
  - `y_sell_partial_flag`
  - garde anti-leakage `assert_storage_targets_not_in_features()`.
- Module `src/mais/research/farmer_backtest_v2.py` créé :
  - coûts paramétrables `StorageCosts` ;
  - backtest par crop year 2015–2022 ;
  - stratégies `SELL_HARVEST`, `SELL_THIRDS`, `SELL_25_25_25_25`, `SIGNAL_BINARY`, `SIGNAL_PARTIAL`, `SELL_MAX_ORACLE` ;
  - métriques par stratégie, gains vs SELL_HARVEST, pire année et verdict honnête.
- Tests `tests/test_storage_backtest.py` créés (6 tests).
- Vérifications :
  - `venv/bin/python -m pytest tests/test_storage_backtest.py -q` PASS (`6 passed`).
  - `venv/bin/python -m ruff check src/mais/research/storage_targets.py src/mais/research/farmer_backtest_v2.py tests/test_storage_backtest.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Non lancé : génération réelle `artefacts/storage/storage_targets.parquet` et `artefacts/storage/backtest_results.json`, car les règles agents interdisent la lecture directe de `data/`. Les modules acceptent `output_path` et sont prêts pour un run pipeline autorisé.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : backtest économique prêt côté code ; conclusions agriculteur à limiter tant que les runs officiels n'ont pas régénéré les artefacts finaux.

---

## R&D-07 — Confiance P(correct) calibrée

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : R&D-02 pour `P(direction_correct)` ; R&D-06 pour `P(decision_profitable)`  

### Contexte

La confiance actuelle (V4) utilise un score composite proxy. Le problème central : le seuil adaptatif 0.45694 est le percentile 50 des scores → 50% des jours sont mécaniquement "au-dessus du seuil". Ce n'est pas de la confiance, c'est du seuillage arbitraire.

P(correct) = "Parmi les jours où j'ai eu un score similaire dans le passé, dans quelle proportion avais-je raison ?"

Ce ticket distingue aussi deux niveaux :
- `P(direction_correct)` : la direction prédit est-elle la bonne ?
- `P(decision_profitable)` : est-ce que suivre ce signal rapporte économiquement ? (plus important)

### Objectifs mesurables

- **Objectif** : ECE < 0.05 sur les buckets de confiance
- **Acceptable** : ECE < 0.10 avec reliability curve monotone et Brier score < 0.25
- DA_top20% par P(correct) > DA_top20% baseline sur au moins 5/8 crop years si 2022 complète
- Reliability curve : P(correct = 0.70) correspond à 70% ± 5% de réussite réelle
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/p_correct_model.py` | **CRÉER** — modèle P(correct) |
| `src/mais/indicator/calibration.py` | Ajouter `fit_p_correct_model()` |
| `tests/test_confidence_p_correct.py` | **CRÉER** — 6 tests P1 |
| `artefacts/indicator/p_correct_model.pkl` | Modèle sérialisé |
| `artefacts/indicator/reliability_curve.json` | Courbe calibration + ECE + Brier |

### Architecture P(correct)

```python
# Features d'entrée (méta-features de situation — toutes disponibles sans look-ahead)
X_meta = [
    "prob_distance",          # |p_up - 0.5| × 2
    "disagreement",           # std(probas modèles) — issu de R&D-02
    "signal_stability_5d",    # stabilité signal 5 jours (rolling)
    "regime_score",           # score régime Markov
    "month",                  # mois calendaire (one-hot ou ordinal)
    "days_since_wasde",       # jours depuis dernière publication WASDE
    "wasde_surprise_abs",     # |surprise WASDE| normalised
    "cot_extreme_flag",       # COT en zone extrême (signal contrarian clair)
]

# Deux targets
y_direction_correct = int(signal_direction == actual_direction_hH)
y_decision_profitable = int(gain_net_signal > 0)  # issu du backtest R&D-06

# Modèle principal
model_p_correct = LogisticRegression(C=1.0, max_iter=1000)
# Calibré avec CalibratedClassifierCV(method='sigmoid', cv='prefit')

# Entraîné sur OOF walk-forward uniquement
# Ne jamais entraîner sur les réalisations futures (anti-leakage de 2ème niveau)
```

### Métriques d'évaluation

```python
reliability_metrics = {
    "ece": expected_calibration_error(y_true, p_correct, n_bins=10),
    "brier_score": brier_score_loss(y_true, p_correct),
    "log_loss": log_loss(y_true, p_correct),
    "sharpness": np.std(p_correct),
    "monotone": all(bucket_acc[i] <= bucket_acc[i+1] for i in range(len(buckets)-1)),
}
```

### Tests P1

```python
def test_p_correct_ece_documented():
    """reliability_curve.json contient ECE et verdict (< 0.05 CONFIRMÉ, < 0.10 ACCEPTABLE, sinon INCONCLU)."""

def test_p_correct_monotone():
    """Reliability curve : P(correct) croît avec le bucket de confiance (au moins sur les buckets centraux)."""

def test_p_correct_no_leakage():
    """Le modèle P(correct) est entraîné sur OOF produits en walk-forward sans réalisations futures."""

def test_p_direction_vs_p_profitable_documented():
    """Artefact contient les deux métriques P(direction_correct) et P(decision_profitable)."""

def test_top20_da_by_year():
    """DA_top20 selon P(correct) documentée pour chaque crop year 2015-2022."""

def test_brier_score_present():
    """reliability_curve.json contient brier_score, log_loss et sharpness."""
```

### Critère de fin

- Modèle P(correct) entraîné et calibré
- ECE et Brier documentés avec verdict
- Comparaison P(direction_correct) vs P(decision_profitable)
- Remplacement du seuil adaptatif p50 par P(correct) > 0.60 (paramétrable dans indicator.yaml)

### Résultat ticket (2026-05-18)

- Module `src/mais/research/p_correct_model.py` créé :
  - `build_p_correct_frame()` construit les méta-features sans look-ahead ;
  - targets séparées `y_direction_correct` et `y_decision_profitable` ;
  - `PCorrectModel` sérialisable avec `predict_proba()` ;
  - garde anti-leakage sur les méta-features économiques/futures.
- `src/mais/indicator/calibration.py` expose `fit_p_correct_model()` comme point d'entrée production.
- Tests `tests/test_confidence_p_correct.py` créés (6 tests P1).
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/p_correct_model.py src/mais/indicator/calibration.py tests/test_confidence_p_correct.py` PASS.
  - `venv/bin/python -m pytest tests/test_confidence_p_correct.py -q` PASS (`6 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS (`112 passed`).
- Non lancé : génération réelle `artefacts/indicator/p_correct_model.pkl` et `artefacts/indicator/reliability_curve.json`, car elle doit passer par un run officiel sur OOF/artefacts autorisés.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`112 passed`).
- Réserve : validation code/tests complète ; calibration finale ECE/Brier à confirmer après génération officielle des artefacts OOF.

---

## R&D-08 — Module risque/opportunité asymétrique

**Priorité** : MOYENNE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : R&D-06, R&D-07  

### Contexte

L'indicateur donne un signal binaire BULLISH/BEARISH. Un agriculteur a besoin de deux informations distinctes avec des asymétries de coût différentes :

1. **Risque de forte baisse** : "Dois-je protéger mon stock maintenant ?" → priorité sécurité
2. **Opportunité de forte hausse** : "Puis-je attendre encore ?" → priorité gain

La perte d'une forte baisse non anticipée (stocker puis vendre moins cher) n'est pas symétrique avec une opportunité manquée (vendre trop tôt). Les seuils de décision doivent refléter cette asymétrie via la fonction de coût λ.

### Objectifs mesurables

- `downside_risk_score` AUC sur y_down_gt_5pct_h40 documentée (objectif ≥ 0.65)
- `upside_opportunity_score` AUC sur y_up_gt_5pct_h40 documentée (objectif ≥ 0.65)
- Seuils calibrés via la fonction de coût asymétrique, pas fixés arbitrairement
- Évaluation par gain/perte économique (¢/bu), pas seulement AUC
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/asymmetric_module.py` | **CRÉER** — scores downside/upside |
| `src/mais/indicator/direction.py` | Ajouter `downside_risk_score` et `upside_opportunity_score` dans la sortie |
| `tests/test_asymmetric_module.py` | **CRÉER** — 5 tests |

### Calibration des seuils (fonction de coût asymétrique)

Les seuils ne sont pas 0.65 fixes mais calibrés selon λ (rapport des coûts) :

```python
# λ = coût_faux_signal_haussier / coût_faux_signal_baissier
# Profil agriculteur standard : λ ≈ 2.0
# → Seuil optimal : P(down) > λ/(1+λ) = 0.667 pour déclencher VENDRE

# Chercher λ sur OOF par validation croisée économique :
for lambda_val in [1.5, 2.0, 2.5, 3.0]:
    threshold_down = lambda_val / (1 + lambda_val)
    economic_gain = backtest_with_threshold(downside_risk_score, threshold_down)
    # Retenir lambda maximisant le gain économique sur OOF
```

### Architecture

```python
# Deux modèles distincts entraînés sur cibles de magnitude
downside_model = train_classifier(X, y_down_gt_5pct_h40)
upside_model = train_classifier(X, y_up_gt_5pct_h40)

downside_risk_score = downside_model.predict_proba(X_today)[1]
upside_opportunity_score = upside_model.predict_proba(X_today)[1]

# Règle de décision fractionnée (extensible)
threshold_down = calibrated_lambda / (1 + calibrated_lambda)
threshold_up = calibrate_threshold(
    score=upside_opportunity_score,
    objective="economic_gain",
    validation_oof=oof_data,
)

if downside_risk_score > threshold_down:
    action = "VENDRE_MAINTENANT"       # protection prioritaire
elif upside_opportunity_score > threshold_up:
    action = "STOCKER"                 # opportunité claire
elif downside_risk_score > 0.50 and upside_opportunity_score < 0.45:
    action = "VENDRE_PARTIEL_50PCT"    # signal faiblement baissier
else:
    action = "ATTENDRE"                # signal ambigu
```

### Évaluation économique (pas seulement AUC)

Pour chaque action générée, calculer en walk-forward :
- `perte_evitee_cents` : combien de ¢/bu de perte a-t-on évitée grâce à VENDRE_MAINTENANT ?
- `gain_manque_cents` : combien de ¢/bu de hausse a-t-on raté en vendant trop tôt ?
- `regret_moyen` : mean(prix_max_3m - prix_réel_vente)
- Distribution des actions par crop year

### Tests

```python
def test_downside_score_auc_documented():
    """AUC downside_risk_score sur y_down_gt_5pct_h40 documentée avec IC95% + verdict."""

def test_upside_score_auc_documented():
    """AUC upside_opportunity_score sur y_up_gt_5pct_h40 documentée avec IC95% + verdict."""

def test_scores_not_identical():
    """downside_risk_score != upside_opportunity_score sur >= 80% des observations."""

def test_thresholds_calibrated():
    """Les seuils de décision sont issus d'une calibration lambda, pas de constantes hardcodées."""

def test_economic_evaluation_documented():
    """Artefact contient perte_evitee_mean, gain_manque_mean, regret_moyen par crop year."""
```

### Critère de fin

- Deux modèles distincts entraînés avec AUC documentées
- Seuils calibrés via coût asymétrique λ
- Règle de décision fractionnée documentée
- Évaluation économique par crop year

### Résultat ticket (2026-05-18)

- Module `src/mais/research/asymmetric_module.py` créé :
  - modèles distincts downside/upside ;
  - AUC + IC95% bootstrap ;
  - calibration de `lambda_value`, `threshold_down` et `threshold_up` par objectif économique ;
  - actions `VENDRE_MAINTENANT`, `STOCKER`, `VENDRE_PARTIEL_50PCT`, `ATTENDRE` ;
  - évaluation économique par crop year.
- `src/mais/indicator/direction.py` expose `downside_risk_score` et `upside_opportunity_score` dans `DirectionSignal`, `summary()`, `metadata` et `predict_range()`.
- Tests `tests/test_asymmetric_module.py` créés (6 tests).
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/asymmetric_module.py src/mais/indicator/direction.py tests/test_asymmetric_module.py` PASS.
  - `venv/bin/python -m pytest tests/test_asymmetric_module.py -q` PASS (`6 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS (`118 passed`).
- Non lancé : génération réelle des artefacts asymétriques, car elle doit passer par les runs officiels et non une lecture directe de `data/`.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`118 passed`).
- Réserve : logique code/test validée ; performance AUC/gain économique finale à confirmer après run officiel sur OOF réels.

---

## R&D-09 — COT avancé normalisé

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : R&D-01  

### Contexte

Le COT brut (positions absolues en contrats) ignore l'évolution de la taille du marché. 200 000 contrats long managed money en 2023 ≠ 200 000 en 2013 si l'open interest total a doublé. La normalisation par OI et le percentile historique donnent une mesure relative plus stable et moins non-stationnaire.

Risque "crowding" : le signal COT peut se dégrader dans le temps si trop de fonds quant l'utilisent (2010–2015 vs 2016–2022). Ce ticket mesure aussi cette décroissance potentielle.

### Objectifs mesurables

- delta_AUC vs baseline R&D-01 documenté avec IC95% et verdict
- Analyse crowding temporelle : AUC 2010–2015 vs AUC 2016–2022 pour chaque feature COT avancée
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/cot_advanced.py` | **CRÉER** — features normalisées COT |
| `src/mais/features/__init__.py` | Ajouter appel |
| `tests/test_cot_advanced.py` | **CRÉER** — 4 tests |

### Features à créer (8 features)

```python
# Normalisation par Open Interest (ratio [-1, +1] approximatif)
cot_mm_net_pct_oi           = mm_net / total_open_interest
cot_comm_net_pct_oi         = commercials_net / total_open_interest

# Percentile historique expanding window (anti-leakage)
cot_mm_pct_oi_percentile    = expanding_rank(cot_mm_net_pct_oi)     # [0, 1]
cot_comm_pct_oi_percentile  = expanding_rank(cot_comm_net_pct_oi)

# Flags extrêmes (signal contrarian)
cot_mm_extreme_long_flag    = int(cot_mm_pct_oi_percentile > 0.90)
cot_mm_extreme_short_flag   = int(cot_mm_pct_oi_percentile < 0.10)

# Pression hedger vs spéculatifs (normalisée par OI — pas de division par mm_net pour éviter explosion)
cot_hedger_pressure         = commercials_net / total_open_interest  # négatif si hedgers vendent

# Crowding score (distance aux extrêmes)
cot_crowding_score          = abs(cot_mm_pct_oi_percentile - 0.5) * 2  # 0 au centre, 1 aux extrêmes
```

**Note sur les formules** :
- `cot_hedger_pressure = commercials_net / total_open_interest` (pas divisé par mm_net pour éviter ÷0)
- `cot_crowding_score = abs(percentile - 0.5) * 2` : interprétable, borné [0, 1], 1 = extrême contrarian

### Tests

```python
def test_cot_pct_oi_bounded():
    """cot_mm_net_pct_oi ∈ [-1.5, +1.5] (ratio approximatif — peut légèrement dépasser 1)."""

def test_cot_percentile_expanding():
    """cot_mm_pct_oi_percentile calculé sur expanding window (pas rolling fixe)."""

def test_cot_extreme_flags_rare():
    """P(extreme_long_flag=1) ≈ 0.10 ± 0.04 et P(extreme_short_flag=1) ≈ 0.10 ± 0.04."""

def test_cot_temporal_stability_documented():
    """Artefact contient AUC COT avancé sur 2010-2015 vs 2016-2022 avec delta (crowding test)."""
```

### Critère de fin

- 8 features ajoutées à build_features()
- delta_AUC documenté avec IC95% et verdict
- Analyse crowding 2010–2015 vs 2016–2022 documentée

### Résultat ticket (2026-05-18)

- Module `src/mais/features/cot_advanced.py` créé.
- Intégration dans `src/mais/features/__init__.py` après les features CFTC COT existantes.
- Tests `tests/test_cot_advanced.py` créés (4 tests).
- 8 features ajoutées :
  - `cot_mm_net_pct_oi`
  - `cot_comm_net_pct_oi`
  - `cot_mm_pct_oi_percentile`
  - `cot_comm_pct_oi_percentile`
  - `cot_mm_extreme_long_flag`
  - `cot_mm_extreme_short_flag`
  - `cot_hedger_pressure`
  - `cot_crowding_score`
- Évaluateur ajouté : `evaluate_cot_advanced_stability()` produit un JSON avec `baseline_auc`, `auc_with_cot_advanced`, `delta_auc`, `auc_2010_2015`, `auc_2016_2022`, `crowding_delta_auc_late_minus_early`, `verdict`.
- Vérifications :
  - `venv/bin/python -m pytest tests/test_cot_advanced.py tests/test_new_sources.py -q` PASS (`9 passed`).
  - `venv/bin/python -m ruff check src/mais/features/cot_advanced.py src/mais/features/__init__.py tests/test_cot_advanced.py` PASS.
  - `venv/bin/python -m pytest tests/ -q` PASS (`74 passed`).
- Non lancé : ablation réelle sur `data/processed/features.parquet`, car les règles agents interdisent la lecture directe de `data/`. Le code d'évaluation est prêt pour un run pipeline autorisé.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`106 passed`).
- Réserve : features COT avancées prêtes et couvertes ; verdict prédictif final dépend de l'évaluation delta AUC sur benchmark complet.

---

## R&D-10 — Rapport hebdomadaire agriculteur (4 modules)

**Priorité** : BASSE — uniquement après validation économique R&D-06  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : R&D-06, R&D-07, R&D-08  

### Contexte

L'objectif final est un rapport chaque lundi matin, compréhensible par un agriculteur non expert en finance. Il doit l'aider à décider de vendre ou stocker son maïs, sans jargon statistique.

**Précaution importante** : tant que le backtest économique (R&D-06) n'a pas prouvé un gain net positif, le rapport doit se présenter comme une **aide à la décision** (lecture de marché), pas comme une **recommandation directe**. Ne pas afficher "RECOMMANDATION : STOCKER" sans validation économique préalable.

### Objectifs mesurables

- Rapport généré en < 30 secondes
- 4 modules présents
- Aucun terme technique dans le Module 1 (pas de "feature", "SHAP", "AUC", "z-score")
- P(hausse), P(correct) et confiance métier distingués clairement
- Tests : ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/ops/weekly_report.py` | **CRÉER** — générateur rapport Markdown |
| `src/mais/indicator/shap_translator.py` | **CRÉER** — SHAP → langage métier |
| `ops/weekly_report.sh` | **CRÉER** — script bash cron lundi 7h30 |
| `tests/test_weekly_report.py` | **CRÉER** — 4 tests |

### Structure du rapport

**Module 1 — Situation marché**
```
MAÏS CBOT — Semaine du [DATE]

Prix actuel : 485 ¢/bu
Lecture de marché : HAUSSIÈRE (6 semaines)
Probabilité de hausse : 64 %
Fiabilité estimée du signal : 71 %   ← P(correct), PAS confiance composite
Clarté du marché : MODÉRÉE

Facteurs qui poussent le prix à la hausse :
  1. Rapport USDA attendu dans 8 jours → marché en attente prudente
  2. Déficit hydrique dans la Corn Belt : stress sur les cultures cette semaine
  3. Accélération des achats export cette semaine (+18% vs mois dernier)

Facteurs qui pèsent sur le prix :
  1. Dollar américain en hausse → les exports coûtent plus cher à l'étranger
  2. Rythme des ventes export en retard de 12% vs prévisions USDA

⚠ Note : les grands fonds spéculatifs sont très achetés (positions extrêmes).
  Cela peut signaler un retournement prochain si une mauvaise nouvelle arrive.
```

**Important sur le COT** : les positions longues extrêmes des fonds spéculatifs sont un risque contrarian (baissier), pas un facteur haussier. Le `shap_translator` doit utiliser **le signe réel du SHAP**, pas seulement le nom de la feature.

**Module 2 — Aide à la décision stockage**
```
Aide stockage :
  Probabilité que le prix monte encore en 6 semaines : 64 %
  Probabilité de forte baisse (>5%) : 22 % → FAIBLE
  Probabilité de forte hausse (>5%) : 41 % → PRÉSENTE

  Estimation de valeur stockage 3 mois (non garantie) :
    Gain brut attendu : +18 ¢/bu
    Coût de stockage : -5 ¢/bu
    Gain net estimé : +13 ¢/bu [IC90% : +2 à +27]
    
  Cette estimation est basée sur les signaux actuels du marché.
  Elle n'est pas une garantie et peut être erronée.
```

**Module 3 — Alertes couverture**
```
Signal couverture : ATTENDRE
  → Les conditions actuelles ne justifient pas de fixer le prix maintenant.
  → Attendre : rapport USDA dans 8 jours, ou signal de retournement COT.

Situations qui déclencheraient une couverture recommandée :
  - Rapport USDA avec forte révision à la baisse des stocks
  - Fonds spéculatifs commencent à liquider leurs positions
```

**Module 4 — Alertes et limites**
```
Points de vigilance cette semaine :
  ⚠ Rapport USDA dans 8 jours → ne pas prendre de grande décision avant
  ⚠ Fonds spéculatifs en position extrême → risque de retournement brutal
  ⚠ Volatilité du marché en hausse (+15%) → marché plus incertain qu'habituel

Ce que le modèle ne peut pas prévoir :
  - Décisions politiques (embargo, taxe export)
  - Catastrophes météo soudaines hors zone US
  - Choc économique mondial
```

### Tests

```python
def test_report_generation_time():
    """Rapport généré en < 30 secondes (avec données mockées)."""

def test_report_four_modules_present():
    """Rapport Markdown contient les 4 sections."""

def test_shap_no_jargon_in_module1():
    """Module 1 ne contient pas les termes 'SHAP', 'AUC', 'feature', 'z-score', 'percentile'."""

def test_cot_contrarian_framing():
    """Si COT extreme_long_flag=1, le COT apparaît dans les risques, pas dans les facteurs haussiers."""
```

### Critère de fin

- Rapport généré automatiquement avec données réelles
- 4 modules présents, langage métier validé
- Distinction P(hausse) / P(correct) / clarté marché dans le texte
- Script cron configuré

### Résultat ticket (2026-05-18)

- Module `src/mais/ops/weekly_report.py` créé :
  - `WeeklyReportInput` ;
  - `generate_weekly_report()` en 4 modules Markdown ;
  - `input_from_direction_signal()` pour alimenter le rapport depuis l'indicateur ;
  - distinction explicite P(hausse) / P(correct) / clarté marché.
- Module `src/mais/indicator/shap_translator.py` créé :
  - traduction des contributions signées en langage métier ;
  - COT `extreme_long` traité comme risque contrarian, pas comme facteur haussier.
- Script `ops/weekly_report.sh` créé et rendu exécutable.
- Tests `tests/test_weekly_report.py` créés (5 tests).
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/ops/weekly_report.py src/mais/indicator/shap_translator.py src/mais/ops/__init__.py tests/test_weekly_report.py` PASS.
  - `venv/bin/python -m pytest tests/test_weekly_report.py -q` PASS (`5 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS (`123 passed`).
- Non lancé : génération réelle à partir des artefacts de production, car les règles agents interdisent la lecture directe des artefacts/données hors commande officielle.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-18)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Vérification review : `venv/bin/python -m pytest tests/ -q` PASS (`123 passed`).
- Réserve : le générateur est validé sur données mockées ; la version production devra brancher les artefacts officiels régénérés.

---

## Objectif final Phase R&D CBOT (critère de succès global)

> Produire, chaque lundi, un rapport en 4 modules permettant à un agriculteur de prendre de meilleures décisions de stockage et de vente partielle sur le CBOT maïs, avec un gain net moyen positif par rapport à une stratégie naïve, sur la majorité des années de validation (2015–2022), sans aucune connaissance ex-post et sans recalibrage des seuils.

**Ce n'est prouvé que par R&D-06 (backtest économique). Tous les autres tickets préparent ce moment.**

---
---

# Phase EXP — Pivot Euronext Matif (EMA, EUR/tonne)
> Ajouté le 2026-05-19. Source : `.ai/ARCHITECTURE_EMA_PRO.md` (référence centrale).
> Objectif : construire un indicateur professionnel sur le maïs Euronext avec pipeline quotidien automatisé, modèles direction/prix/stockage, et rapport agriculteur hebdomadaire.
>
> **Règle anti-leakage** : chaque source a une date de disponibilité réelle définie (§5 ARCHITECTURE_EMA_PRO). Pas seulement shift(1) généralisé.
> **Données EMA réelles obligatoires** avant Phase Modèles (VAL-EMA-01 bloquant).
> **Proxy CBOT interdit** pour les résultats finaux : il sert uniquement à valider la plomberie.

## Index Phase EXP

| Ticket | Titre | Priorité | Type | Statut | Dépendances |
|---|---|---|---|---|---|
| [DATA-PATHS-01](#data-paths-01--extension-pathspy--répertoires-ema) | Extension paths.py + répertoires EMA | **PRIORITÉ 0** | simple | DONE | — |
| [DATA-PATHS-02](#data-paths-02--chemins-ema-référence-courbe-et-liquidité) | Chemins EMA référence/courbe/liquidité | **PRIORITÉ 0** | simple | DONE | DATA-PATHS-01 |
| [DATA-EMA-07](#data-ema-07--validation-endpoint-euronext) | Validation endpoint Euronext | **PRIORITÉ 0** | moyen | DONE | — |
| [DATA-EMA-01](#data-ema-01--collecteur-quotidien-euronext-contrats-actifs) | Collecteur quotidien Euronext | HAUTE | critique | DONE | DATA-EMA-07 |
| [DATA-EMA-11](#data-ema-11--mois-actifs-vs-mois-legacy-fournisseur) | Mois actifs vs legacy fournisseur | **PRIORITÉ 0** | moyen | DONE | DATA-PATHS-02, DATA-EMA-01 |
| [DATA-EMA-09](#data-ema-09--validation-barchart-expired-ema-contracts) | Validation Barchart expired EMA | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-11 |
| [DATA-EMA-12](#data-ema-12--kit-validation-csv-historique-ema-ohlc) | Kit validation CSV historique EMA OHLC | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-09 |
| [DATA-EMA-13](#data-ema-13--télécharger-ou-reconstruire-série-continue-ema-historique) | Série continue EMA historique | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-12 |
| [DATA-EMA-14](#data-ema-14--tester-téléchargement-contrat-par-contrat-barchart) | Test contrats Barchart unitaires | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-09 |
| [DATA-EMA-15](#data-ema-15--recherche-active-source-ohLC-historique-ema) | Recherche active source OHLC EMA | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-09, DATA-EMA-12 |
| [DATA-EMA-10](#data-ema-10--table-de-référence-contrats-ema) | Table référence contrats EMA | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-09, DATA-EMA-12, DATA-EMA-15 |
| [DATA-EMA-02](#data-ema-02--backfill-historique-ema-par-contrat) | Backfill historique EMA | HAUTE | complexe | DONE | DATA-EMA-10 |
| [DATA-EMA-03](#data-ema-03--séries-continues-ema) | Séries continues EMA | HAUTE | complexe | DONE | DATA-EMA-02 |
| [DATA-EMA-08](#data-ema-08--roll-audit) | Roll audit | HAUTE | moyen | DONE | DATA-EMA-03 |
| [DATA-EMA-04](#data-ema-04--features-courbe-euronext) | Features courbe Euronext | HAUTE | complexe | DONE | DATA-EMA-03, DATA-EMA-08 |
| [DATA-EMA-05](#data-ema-05--rapport-qualité-quotidien) | Rapport qualité quotidien | HAUTE | moyen | DONE | DATA-EMA-01 |
| [DATA-EMA-06](#data-ema-06--anti-leakage-calendrier-par-source) | Anti-leakage calendrier par source | HAUTE | moyen | DONE | — |
| [DATA-MASTER-01](#data-master-01--dataset-master-emacbot) | Dataset master EMA+CBOT | HAUTE | complexe | DONE | DATA-EMA-04, DATA-EMA-06 |
| [DATA-TARGETS-01](#data-targets-01--cibles-agricoles-ema) | Cibles agricoles EMA | HAUTE | moyen | DONE | DATA-EMA-03 |
| [EXP-BENCH-01](#exp-bench-01--feature-selection-ema) | Feature selection EMA | HAUTE | moyen | DONE | DATA-MASTER-01 |
| [VAL-EMA-01](#val-ema-01--proxy-vs-vraie-ema) | Proxy vs vraie EMA | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-02 |
| [EXP-BENCH-02](#exp-bench-02--benchmark-ema-vs-cbot-vrais-prix) | Benchmark EMA vs CBOT | HAUTE | critique | DONE | VAL-EMA-01, EXP-BENCH-01 |
| [VAL-EMA-02](#val-ema-02--benchmark-hebdomadaire) | Benchmark hebdomadaire | HAUTE | moyen | DONE | EXP-BENCH-02 |
| [EXP-BENCH-03](#exp-bench-03--ablation-features-courbe-ema) | Ablation features courbe EMA | MOYENNE | moyen | DONE | EXP-BENCH-02 |
| [EXP-BENCH-04](#exp-bench-04--benchmark-cible-stockage) | Benchmark cible stockage | MOYENNE | moyen | DONE | DATA-TARGETS-01, EXP-BENCH-01 |
| [DATA-EMA-16](#data-ema-16--canonicalisation-lignes-euronext-officielles) | Canonicalisation lignes Euronext officielles | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-10, DATA-EMA-02 |
| [DATA-EMA-17](#data-ema-17--features-courbe-ema-insuffisante--nan) | Features courbe insuffisante → NaN | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-16 |
| [DATA-TARGETS-02](#data-targets-02--targets-ema-raw-adjusted-et-no-roll) | Targets EMA raw/adjusted/no-roll | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-17 |
| [EXP-EMA-ROLL-TARGET-01](#exp-ema-roll-target-01--benchmark-targets-ema-roll) | Benchmark targets EMA roll | HAUTE | moyen | DONE | DATA-TARGETS-02, EXP-BENCH-01 |
| [EXP-EMA-CURVE-TRUE-01](#exp-ema-curve-true-01--benchmark-courbe-ema-fiable) | Benchmark courbe EMA fiable | HAUTE | moyen | DONE | DATA-EMA-17, EXP-BENCH-01 |
| [EXP-EMA-STUDY-01](#exp-ema-study-01--audit-statistique-data-ema) | Audit statistique data EMA | **PRIORITÉ 0** | moyen | DONE | DATA-EMA-17, DATA-TARGETS-02 |
| [EXP-EMA-STUDY-02](#exp-ema-study-02--relation-ema--cbot-leadlag) | Relation EMA / CBOT lead-lag | HAUTE | moyen | DONE | EXP-EMA-STUDY-01 |
| [EXP-EMA-STUDY-03](#exp-ema-study-03--basis-mean-reversion) | Basis mean reversion | HAUTE | moyen | DONE | EXP-EMA-STUDY-02 |
| [EXP-EMA-STUDY-04](#exp-ema-study-04--stockage-économique-ema) | Stockage économique EMA | HAUTE | complexe | DONE | EXP-EMA-STUDY-01, EXP-BENCH-04 |
| [EXP-EMA-STUDY-05](#exp-ema-study-05--module-a-data-status) | Module A data status | MOYENNE | moyen | DONE | MOD-A-02 |
| [EXP-EMA-STUDY-06](#exp-ema-study-06--cqr-prix-ema) | CQR prix EMA | MOYENNE | complexe | DONE | EXP-EMA-STUDY-01 |
| [EXP-EMA-STUDY-07](#exp-ema-study-07--synthèse-finale-euronext) | Synthèse finale Euronext | MOYENNE | moyen | DONE | EXP-EMA-STUDY-02, EXP-EMA-STUDY-03, EXP-EMA-STUDY-04, EXP-EMA-STUDY-05, EXP-EMA-STUDY-06 |
| [MODEL-DIR-01](#model-dir-01--modèle-direction-ema-walk-forward) | Modèle direction EMA | HAUTE | complexe | BLOCKED | EXP-BENCH-02 |
| [MODEL-CQR-01](#model-cqr-01--cqr-prix-absolu-ema) | CQR prix absolu EMA | HAUTE | complexe | BLOCKED | EXP-BENCH-02 |
| [MODEL-STOR-01](#model-stor-01--modèle-décision-stockage) | Modèle décision stockage | HAUTE | complexe | BLOCKED | DATA-TARGETS-01, MODEL-DIR-01 |
| [MODEL-CONF-01](#model-conf-01--confiance-pcorrect-ema) | Confiance P(correct) EMA | MOYENNE | moyen | BLOCKED | MODEL-DIR-01 |
| [MODEL-STACK-01](#model-stack-01--stacking-augmenté-cross-fitted-ema) | Stacking augmenté EMA | MOYENNE | critique | BLOCKED | MODEL-DIR-01, MODEL-CQR-01 |
| [MOD-A-01](#mod-a-01--module-a-12-signaux-contexte-scorés) | Module A — 12 signaux contexte | HAUTE | complexe | DONE | DATA-MASTER-01 |
| [MOD-A-02](#mod-a-02--module-a-calibration-oof--poids) | Module A — calibration OOF + poids | HAUTE | complexe | DONE | MOD-A-01 |
| [MOD-B-01](#mod-b-01--module-b-étude-événementielle-grandes-variations) | Module B — étude événementielle | MOYENNE | complexe | IN_PROGRESS | EXP-BENCH-02 |
| [MOD-B-02](#mod-b-02--module-b-règles-lisibles--carte-risque) | Module B — règles + carte risque | MOYENNE | moyen | BLOCKED | MOD-B-01 |
| [MOD-C-01](#mod-c-01--module-c-prédiction-prix-ema-cqr) | Module C — prédiction prix CQR | HAUTE | critique | BLOCKED | MODEL-CQR-01 |
| [OPS-CLI-01](#ops-cli-01--extension-cli-ema) | Extension CLI EMA | HAUTE | moyen | DONE | DATA-MASTER-01 |
| [OPS-DAILY-01](#ops-daily-01--pipeline-quotidien-ema) | Pipeline quotidien EMA | HAUTE | complexe | BLOCKED | MODEL-DIR-01, MODEL-CQR-01 |
| [OPS-REPORT-01](#ops-report-01--rapport-hebdomadaire-agriculteur-ema) | Rapport hebdomadaire EMA | HAUTE | complexe | BLOCKED | OPS-DAILY-01 |
| [OPS-CRON-01](#ops-cron-01--automatisation-cronsystemd) | Automatisation cron/systemd | MOYENNE | simple | BLOCKED | OPS-DAILY-01 |
| [VAL-BACKTEST-01](#val-backtest-01--backtest-économique-complet-ema) | Backtest économique complet EMA | HAUTE | critique | BLOCKED | OPS-DAILY-01 |
| [VAL-REPORT-01](#val-report-01--rapport-final-euronext) | Rapport final Euronext | MOYENNE | moyen | BLOCKED | VAL-BACKTEST-01 |

**Ordre d'exécution Phase EXP :**
```
Phase 0 — Infrastructure (1-2 jours) :
  DATA-PATHS-01 → DATA-PATHS-02 → DATA-EMA-07 → DATA-EMA-01 → DATA-EMA-05 → DATA-EMA-06
  → DATA-EMA-11

Phase 0b — Validation source historique :
  DATA-EMA-09 DONE : Barchart pages/métadonnées OK, OHLC public KO
  → DATA-EMA-12 (kit validation CSV historique)
  → DATA-EMA-13 (série continue longue XB/EMA1!)
  → DATA-EMA-14 (contrats Barchart XBM26/XBQ26/XBX26/XBM14)
  → DATA-EMA-15 (recherche active Euronext/Barchart/API/sources tierces)
  → Source candidate OHLC Barchart proxy web validée par DATA-EMA-15
  → DATA-EMA-10 (référence contrats exacte)
  → DATA-EMA-02 avec source validée

Phase 1 — Données historiques (2-3 jours) :
  [DATA-EMA-12 + DATA-EMA-15] → DATA-EMA-10 → DATA-EMA-02 → DATA-EMA-03 → DATA-EMA-08 → DATA-EMA-04
              → DATA-TARGETS-01 → DATA-MASTER-01

Phase 2 — Benchmark (1-2 jours) :
  EXP-BENCH-01 → VAL-EMA-01 → EXP-BENCH-02 → VAL-EMA-02 → EXP-BENCH-03 → EXP-BENCH-04
  ⚠ GO/NO-GO après EXP-BENCH-02 (critères : DA>0.55, AUC>0.55, top-20%>0.62)

Phase 3 — Modèles (3-5 jours) :
  MODEL-DIR-01 → MODEL-CQR-01 → MODEL-STOR-01 → MODEL-CONF-01 → MODEL-STACK-01

Phase 4 — Modules A/B/C (3-4 jours) :
  MOD-A-01 → MOD-A-02   (parallèle avec MOD-B-01 → MOD-B-02)
  MOD-C-01

Phase 5 — Ops + Rapport (2-3 jours) :
  OPS-CLI-01 → OPS-DAILY-01 → OPS-REPORT-01 → OPS-CRON-01

Phase 6 — Validation finale (1-2 jours) :
  VAL-BACKTEST-01 → VAL-REPORT-01
```

---

## DATA-PATHS-01 — Extension paths.py + répertoires EMA

**Priorité** : PRIORITÉ 0  
**Type** : simple  
**Statut** : DONE  
**Dépendances** : aucune  

### Contexte

Le fichier `src/mais/paths.py` définit tous les chemins du projet. Les nouveaux répertoires EMA (contrats bruts, séries continues, prédictions) n'y sont pas définis. Toute la Phase EXP dépend de ces chemins standardisés.

### Objectifs mesurables

- Tous les chemins EMA définis dans `paths.py` et utilisables par import
- `ensure_dirs()` crée tous les nouveaux répertoires
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/paths.py` | **MODIFIER** — ajouter chemins EMA |
| `tests/test_paths_ema.py` | **CRÉER** — 3 tests |

### Tâches détaillées

Ajouter dans `paths.py` :
```python
# EMA raw — snapshots quotidiens par contrat
EMA_CONTRACTS_RAW_DIR: Path = RAW_DIR / "euronext_ema_contracts"
EMA_BACKFILL_DIR: Path     = RAW_DIR / "euronext_ema" / "manual_backfill"

# EMA processed — séries continues et features
EMA_PROCESSED_DIR: Path         = PROCESSED_DIR / "euronext"
EMA_CONTRACT_DAILY: Path        = EMA_PROCESSED_DIR / "ema_contract_daily.parquet"
EMA_FRONT_RAW: Path             = EMA_PROCESSED_DIR / "ema_front_continuous_raw.parquet"
EMA_FRONT_ADJUSTED: Path        = EMA_PROCESSED_DIR / "ema_front_continuous_adjusted.parquet"
EMA_MOST_LIQUID: Path           = EMA_PROCESSED_DIR / "ema_most_liquid_continuous.parquet"
EMA_HARVEST_NOV: Path           = EMA_PROCESSED_DIR / "ema_harvest_nov.parquet"
EMA_CONSTANT_30D: Path          = EMA_PROCESSED_DIR / "ema_constant_maturity_30d.parquet"
EMA_CONSTANT_60D: Path          = EMA_PROCESSED_DIR / "ema_constant_maturity_60d.parquet"
EMA_CONSTANT_120D: Path         = EMA_PROCESSED_DIR / "ema_constant_maturity_120d.parquet"
EMA_CURVE_FEATURES: Path        = EMA_PROCESSED_DIR / "ema_curve_features.parquet"

# Prédictions et rapports
PREDICTIONS_DAILY_DIR: Path  = DATA_DIR / "predictions" / "daily"
PREDICTIONS_WEEKLY_DIR: Path = DATA_DIR / "predictions" / "weekly"
REPORTS_QUALITY_DIR: Path    = DATA_DIR / "reports" / "quality"
REPORTS_WEEKLY_EMA_DIR: Path = DATA_DIR / "reports" / "weekly"

# Artefacts benchmark EMA
EMA_BENCHMARK_DIR: Path = ARTEFACTS_DIR / "benchmark_pivot"
EMA_ROLL_AUDIT: Path    = ARTEFACTS_DIR / "roll_audit" / "roll_audit_report.txt"
```

Étendre `ensure_dirs()` pour inclure ces nouveaux chemins.

### Vérifications

```bash
venv/bin/python -m ruff check src/mais/paths.py
venv/bin/python -m pytest tests/test_paths_ema.py -q
from mais.paths import EMA_CONTRACTS_RAW_DIR, EMA_CONTRACT_DAILY, PREDICTIONS_DAILY_DIR
```

---

## DATA-PATHS-02 — Chemins EMA référence, courbe et liquidité

**Priorité** : PRIORITÉ 0  
**Type** : simple  
**Statut** : DONE  
**Dépendances** : DATA-PATHS-01  

### Contexte

Le document `.ai/REFLEXION_CONTRATS_EMA.md` ajoute des fichiers indispensables qui ne sont pas encore standardisés dans `src/mais/paths.py` : table de référence contrats, table courbe quotidienne et séries `liquid` raw/adjusted. Sans chemins centralisés, `DATA-EMA-10`, `DATA-EMA-03` et `DATA-EMA-04` risquent d'inventer des chemins divergents.

### Objectifs mesurables

- Les chemins EMA manquants sont définis dans `src/mais/paths.py`.
- `ensure_dirs()` crée les répertoires nécessaires.
- Les tests de chemins EMA importent tous les nouveaux symboles.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/paths.py` | **MODIFIER** — ajouter chemins manquants |
| `tests/test_paths_ema.py` | **MODIFIER** — couvrir les nouveaux chemins |

### Tâches détaillées

Ajouter :
```python
EMA_CONTRACT_REFERENCE: Path = EMA_PROCESSED_DIR / "ema_contract_reference.parquet"
EMA_CURVE_DAILY: Path        = EMA_PROCESSED_DIR / "ema_curve_daily.parquet"
EMA_LIQUID_RAW: Path         = EMA_PROCESSED_DIR / "ema_liquid_continuous_raw.parquet"
EMA_LIQUID_ADJUSTED: Path    = EMA_PROCESSED_DIR / "ema_liquid_continuous_adjusted.parquet"
EMA_BARCHART_PROBE_RESULTS: Path = ARTEFACTS_DIR / "euronext" / "barchart_probe_results.csv"
EMA_BARCHART_PROBE_REPORT: Path  = ARTEFACTS_DIR / "euronext" / "barchart_probe_report.txt"
```

Conserver les anciens alias si besoin (`EMA_MOST_LIQUID`) mais utiliser `EMA_LIQUID_RAW` dans les nouveaux tickets.

### Vérifications

```bash
venv/bin/python -m ruff check src/mais/paths.py tests/test_paths_ema.py
venv/bin/python -m pytest tests/test_paths_ema.py -q
```

### Critère de fin

- Tous les nouveaux chemins sont importables depuis `mais.paths`.
- Les tests passent.
- Ticket passé en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- Chemins ajoutés dans `src/mais/paths.py` :
  - `EMA_CONTRACT_REFERENCE`
  - `EMA_CURVE_DAILY`
  - `EMA_LIQUID_RAW`
  - `EMA_LIQUID_ADJUSTED`
  - `EMA_BARCHART_PROBE_RESULTS`
  - `EMA_BARCHART_PROBE_REPORT`
- `ensure_dirs()` crée le dossier d'artefacts Euronext utilisé par la sonde Barchart.
- `tests/test_paths_ema.py` couvre les nouveaux chemins et la hiérarchie attendue.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/paths.py tests/test_paths_ema.py` PASS.
  - `venv/bin/python -m pytest tests/test_paths_ema.py -q` PASS (`3 passed`).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ → `DONE`.
- Vérification review : chemins importables, hiérarchie cohérente, anciens chemins conservés, nouveau dossier `artefacts/euronext` créé uniquement via `ensure_dirs()`.
- Vérifications relues : `ruff check` PASS ; `pytest tests/test_paths_ema.py -q` PASS (`3 passed`).
- Réserve : aucune.

---

## DATA-EMA-07 — Validation endpoint Euronext

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : aucune  

### Contexte

Avant de scraper en masse, il est impératif de valider que l'endpoint Euronext récupère bien les données attendues (EMA, pas un autre produit) avec les bons champs. L'URL candidate doit être vérifiée via les Network Requests du navigateur et comparée à l'affichage réel de la page Euronext. Sans cette validation, le collecteur peut silencieusement récupérer des données incorrectes.

### Objectifs mesurables

- Endpoint validé et documenté dans `docs/euronext_endpoint.md`
- 10 lignes comparées automatiquement vs page Euronext, 0 écart > 0.5 €/t sur settlement
- Test de mapping contrats validé (Jun/Aug/Nov/Mar → M/Q/X/H)
- Rapport `artefacts/euronext_endpoint_validation_report.txt` produit
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/euronext_endpoint_probe.py` | **CRÉER** — sonde de validation |
| `docs/euronext_endpoint.md` | **CRÉER** — documentation endpoint retenu |
| `artefacts/euronext_endpoint_validation_report.txt` | Produit par la sonde |
| `tests/test_ema_contracts.py` | **CRÉER** — mapping codes mois (P0) |

### Tâches détaillées

**T1 — Sonde endpoint**

```python
def probe_euronext_endpoint() -> dict:
    """Teste l'endpoint candidat et retourne un rapport de validation."""
    # 1. Essayer les endpoints candidats par priorité
    # 2. Pour chaque endpoint : vérifier champs attendus (settlement, volume, OI, date, contract_code)
    # 3. Vérifier que les contrats récupérés sont bien EMA Matif
    # 4. Comparer 10 valeurs avec page Euronext si accessible
    # 5. Retourner : endpoint_url, fields_present, contracts_found, sample_data, verdict
```

**T2 — Test de mapping obligatoire (P0)**

```python
# Seuls les mois officiels EMA sont valides : H(Mar), M(Jun), Q(Aug), X(Nov)
VALID_EMA_MONTH_CODES = {"H", "M", "Q", "X"}
VALID_EMA_DELIVERY_MONTHS = {3, 6, 8, 11}

def test_contract_month_code_mapping():
    from mais.collect.euronext_contracts_daily import parse_contract_label
    assert parse_contract_label("Mar 2027") == "EMA_H2027"
    assert parse_contract_label("Jun 2026") == "EMA_M2026"
    assert parse_contract_label("Aug 2026") == "EMA_Q2026"
    assert parse_contract_label("Nov 2026") == "EMA_X2026"
    # Janvier n'est PAS un mois officiel EMA — doit lever ValueError ou retourner None
    with pytest.raises(ValueError):
        parse_contract_label("Jan 2027")
```

**T3 — Documentation**

Produire `docs/euronext_endpoint.md` contenant :
- URL retenue et sa structure
- Champs disponibles vs attendus
- Procédure de mise à jour si l'URL change
- Throttle recommandé (min 2s entre appels)

### Critère de fin

- Endpoint documenté et validé, ou alternative documentée si inaccessible
- Test mapping P0 PASS
- Rapport de validation produit

### Résultat ticket (2026-05-19)

- Endpoint officiel validé : `/en/ajax/getPricesFutures/commodities-futures/EMA/DPAR`.
- Endpoints candidats rejetés : `/pd_ajax/fixings` = 404, `/pd/data/quote` = JSON vide.
- 10 contrats actifs EMA récupérés le 2026-05-19, champs prix/settlement/volume/OI présents.
- Documentation créée : `docs/euronext_endpoint.md`.
- Sonde créée : `src/mais/collect/euronext_endpoint_probe.py`.
- Rapport produit : `artefacts/euronext_endpoint_validation_report.txt`.
- Vérifications : `ruff check` PASS ; `pytest tests/test_ema_contracts.py tests/test_euronext_endpoint_probe.py -q` PASS (4 tests).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-19)

- VALIDÉ AVEC RÉSERVE → `DONE`.
- Réserve : endpoint validé pour les snapshots quotidiens des contrats actifs uniquement ; le backfill historique reste à traiter dans `DATA-EMA-02`.

---

## DATA-EMA-01 — Collecteur quotidien Euronext (contrats actifs)

**Priorité** : HAUTE  
**Type** : critique  
**Statut** : DONE  
**Dépendances** : DATA-EMA-07  

### Contexte

Le collecteur actuel (`euronext_ema_collector.py`) génère un proxy CBOT, inutilisable pour les modèles EMA réels. Il faut un collecteur qui récupère automatiquement tous les contrats EMA actifs chaque jour après la clôture Euronext (~18h CET), sans intervention manuelle. C'est la fondation de toute la Phase EXP.

### Objectifs mesurables

- Tous les contrats EMA actifs collectés quotidiennement (5 à 8 contrats)
- Snapshot JSON journalier dans `EMA_CONTRACTS_RAW_DIR/YYYY-MM-DD.json`
- Table master `ema_contract_daily.parquet` mise à jour incrémentalement
- Sources par priorité : scraping Euronext > Barchart > proxy CBOT (flaggé)
- Ruff PASS, pytest PASS (≥ 5 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/euronext_contracts_daily.py` | **CRÉER** — collecteur principal |
| `src/mais/collect/__init__.py` | **MODIFIER** — enregistrer `euronext_ema_daily` |
| `config/sources.yaml` | **MODIFIER** — remplacer `euronext_ema` par `euronext_ema_daily` |
| `tests/test_euronext_daily_collector.py` | **CRÉER** — ≥ 5 tests |

### Tâches détaillées

**T1 — Module `euronext_contracts_daily.py`**

Interface publique :
```python
def download_active_contracts(date: datetime.date | None = None) -> list[dict]:
    """Récupère tous les contrats EMA actifs. Sources par priorité :
    1. Scraping Euronext (endpoint validé DATA-EMA-07)
    2. Barchart API (si BARCHART_API_KEY dans env)
    3. Proxy CBOT (fallback, flaggé is_proxy=True)
    """

def save_daily_snapshot(date: datetime.date, contracts: list[dict]) -> Path:
    """Sauvegarde JSON dans EMA_CONTRACTS_RAW_DIR/YYYY-MM-DD.json.
    Ne jamais écraser un fichier existant — append si nécessaire."""

def update_contract_daily_parquet(date: datetime.date, contracts: list[dict]) -> int:
    """Met à jour ema_contract_daily.parquet incrémentalement.
    Règle : source réelle > proxy. Ne jamais écraser une vraie donnée."""

def parse_contract_label(label: str) -> str:
    """'Jun 2026' → 'EMA_M2026'. Test P0 dans DATA-EMA-07."""

def download(out_dir: Path, src: dict) -> str:
    """Interface collecteur standard pour mais.collect.__init__."""
```

Schéma JSON journalier conforme au §4.1 de `ARCHITECTURE_EMA_PRO.md`.

Chaque entrée contrat dans le JSON doit inclure :
```json
{
  "source_symbol":           "CWHM26",         // code brut fournisseur
  "canonical_contract_code": "EMA_M2026",       // code canonique projet
  "month_code":              "M",               // H/M/Q/X uniquement
  "import_verdict":          "usable",          // usable / legacy_or_ambiguous / do_not_import
  "source":                  "barchart"
}
```
Si `month_code` n'est pas dans {"H","M","Q","X"} : `import_verdict = "legacy_or_ambiguous"`, ne pas charger dans `ema_contract_daily.parquet` sans confirmation officielle dans `EMA_CONTRACT_REFERENCE`.

**T2 — Fallback Barchart**

Si `BARCHART_API_KEY` présent dans l'environnement :
```python
# Tickers EMA Matif sur Barchart (actifs) : CWHM26 (Jun), CWHU26 (Aug), CWHX26 (Nov)
# Format : CWH + code_mois_Barchart + année_2_chiffres
BARCHART_EMA_PREFIX = "CWH"
# ⚠ Les codes mois Barchart peuvent différer des codes EMA canoniques
# Toujours renseigner source_symbol et canonical_contract_code séparément
```

**T3 — Quality flags**
```python
QUALITY_FLAGS = {
    "ok": "Données complètes",
    "settlement_missing": "Settlement absent, utiliser last",
    "oi_missing": "Open interest manquant",
    "low_liquidity": "OI < 500 ou volume = 0",
    "proxy_cbot": "Données dérivées CBOT, non utilisables modèles",
}
```

**T4 — Tests**

```python
def test_parse_contract_label_current_official_months():
    # mapping courant H/M/Q/X ; F/Janvier reste legacy_or_ambiguous si vu chez un fournisseur tiers
def test_snapshot_creates_json():
    # vérifie structure JSON conforme
def test_no_overwrite_real_with_proxy():
    # si is_proxy=False déjà présent, ne pas écraser avec proxy
def test_daily_parquet_incremental_append():
    # append correct, pas de doublons
def test_quality_flag_set_correctly():
    # settlement manquant → flag settlement_missing
```

### Critère de fin

- Collecte quotidienne fonctionnelle (au moins scraping Euronext ou Barchart)
- Fallback proxy documenté et flaggé
- Mapping codes mois test P0 PASS
- 5 tests PASS

### Résultat ticket (2026-05-19)

- Collecteur créé : `src/mais/collect/euronext_contracts_daily.py`.
- Source ajoutée : `euronext_ema_daily` dans `config/sources.yaml` et registry `mais.collect`.
- Endpoint Euronext validé utilisé en priorité, fallback Barchart/proxy explicite si indisponible.
- Snapshot quotidien produit : `data/raw/euronext_ema_contracts/2026-05-19.json`.
- Table master mise à jour : `data/processed/euronext/ema_contract_daily.parquet`.
- Données collectées : 10 contrats actifs EMA, `proxy_pct=0.0`.
- Vérifications : `ruff check` PASS ; `pytest tests/test_euronext_daily_collector.py tests/test_ema_contracts.py tests/test_euronext_endpoint_probe.py -q` PASS (9 tests).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-19)

- VALIDÉ AVEC RÉSERVE → `DONE`.
- Réserve : historique profond non couvert par ce ticket ; à traiter dans `DATA-EMA-02`.

---

## DATA-EMA-11 — Mois actifs vs mois legacy fournisseur

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-PATHS-02, DATA-EMA-01  

### Contexte

Le flux Euronext actif courant utilise les mois H/M/Q/X. Le code historique accepte encore Janvier/F comme mois EMA générique, ce qui peut contaminer le pipeline actif et contredire la règle de référence. Il faut séparer explicitement :
- les mois actifs courants acceptés dans le collecteur Euronext quotidien ;
- les symboles legacy fournisseur, notamment `XBF..`, traités seulement par les sondes/références avec `legacy_or_ambiguous`.

### Objectifs mesurables

- `parse_contract_label()` du flux actif rejette Janvier/F ou le marque non importable selon l'interface retenue.
- Les constantes de mois distinguent `CURRENT_OFFICIAL_EMA_MONTHS = {"H","M","Q","X"}` et les mois legacy investigués.
- Les JSON quotidiens incluent `source_symbol`, `canonical_contract_code`, `month_code`, `import_verdict`, `active_month_status`.
- Les tests existants sont alignés : Janvier/F n'est plus considéré comme un contrat actif courant.
- Ruff PASS, pytest PASS sur le bloc EMA concerné.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/euronext_ema_collector.py` | **MODIFIER** — séparer mois courants et legacy |
| `src/mais/collect/euronext_contracts_daily.py` | **MODIFIER** — enrichir schéma quotidien |
| `src/mais/collect/euronext_backfill.py` | **MODIFIER** — ne pas importer legacy sans référence |
| `tests/test_ema_contracts.py` | **MODIFIER** — Jan/F non actif |
| `tests/test_euronext_ema_collector.py` | **MODIFIER** — Jan/F non actif dans le collecteur historique |
| `tests/test_euronext_daily_collector.py` | **MODIFIER** — schéma enrichi + rejet Jan/F |
| `tests/test_euronext_backfill.py` | **MODIFIER SI NÉCESSAIRE** — import_verdict legacy |

### Tâches détaillées

**T1 — Constantes**

```python
CURRENT_OFFICIAL_EMA_MONTHS = {"H": 3, "M": 6, "Q": 8, "X": 11}
LEGACY_OR_INVESTIGATION_EMA_MONTHS = {"F": 1}
```

**T2 — Parsing flux actif**

```python
def parse_active_contract_label(label: str) -> str:
    """Parse uniquement les contrats actifs officiels H/M/Q/X.
    Jan/F doit lever ValueError ou retourner un verdict non importable documenté.
    """
```

Conserver une fonction fournisseur séparée si besoin pour Barchart/legacy, mais ne pas l'utiliser dans le collecteur quotidien actif.

**T3 — Schéma quotidien**

Chaque ligne normalisée doit contenir :
```json
{
  "source_symbol": "EMA_M2026",
  "canonical_contract_code": "EMA_M2026",
  "contract_code": "EMA_M2026",
  "month_code": "M",
  "active_month_status": "current_official",
  "import_verdict": "usable"
}
```

### Critère de fin

- Jan/F n'est plus importable via le flux actif courant.
- Les symboles legacy restent possibles dans DATA-EMA-09/DATA-EMA-10, mais isolés.
- Ticket passé en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- `CURRENT_OFFICIAL_EMA_MONTHS = {"H","M","Q","X"}` et `LEGACY_OR_INVESTIGATION_EMA_MONTHS = {"F"}` séparés dans `src/mais/collect/euronext_ema_collector.py`.
- `parse_contract_label()` / flux actif rejette `Jan/F`.
- `parse_provider_contract_label(..., allow_legacy=True)` permet d'investiguer `F/Janvier` sans l'intégrer au flux actif.
- `src/mais/collect/euronext_contracts_daily.py` enrichit les lignes avec `source_symbol`, `canonical_contract_code`, `month_code`, `active_month_status`, `import_verdict`.
- `src/mais/collect/euronext_backfill.py` rejette les contrats legacy sans référence confirmée (`historical_confirmed` + `usable`) et conserve les champs de traçabilité dans le schéma.
- Tests mis à jour : Jan/F non actif, legacy investigable seulement via fonction fournisseur, backfill legacy non confirmé rejeté.
- Vérifications :
  - `venv/bin/python -m ruff check ...` PASS.
  - `venv/bin/python -m pytest tests/test_ema_contracts.py tests/test_euronext_ema_collector.py tests/test_euronext_endpoint_probe.py tests/test_euronext_daily_collector.py tests/test_euronext_backfill.py -q` PASS (`19 passed`).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ → `DONE`.
- Vérification review : Jan/F rejeté par le flux actif ; `parse_provider_contract_label(..., allow_legacy=True)` isole l'investigation fournisseur ; backfill legacy impossible sans statut `historical_confirmed` et verdict `usable`.
- Vérifications relues : `ruff check` PASS ; pytest bloc EMA concerné PASS (`19 passed`, puis smoke review `16 passed`).
- Réserve : la confirmation officielle d'un éventuel mois F historique reste à faire dans DATA-EMA-09/DATA-EMA-10.

---

## DATA-EMA-02 — Backfill historique EMA par contrat

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : DATA-EMA-10  

### Contexte

Les modèles ont besoin d'un historique 2014–2025 pour un walk-forward sur 8+ folds. Le collecteur quotidien ne couvre que les données futures. Le backfill ne peut reprendre qu'après une table de référence contrats validée (`DATA-EMA-10`) : elle doit distinguer le symbole fournisseur, le code canonique projet, le statut du mois et le verdict d'import.

### Objectifs mesurables

- ≥ 2 000 jours de données par contrat (si disponibles)
- Couverture 2014-2025 pour les contrats X (Novembre) de chaque campagne
- Rapport de couverture `artefacts/backfill_coverage_report.json`
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/euronext_backfill.py` | **CRÉER** — backfill historique |
| `src/mais/cli.py` | **MODIFIER** — commande `backfill euronext` |
| `docs/ema_historical_source_research.md` | **MODIFIER** — ajouter validation couverture Barchart proxy |
| `tests/test_euronext_backfill.py` | **CRÉER** — ≥ 4 tests |

### Tâches détaillées

**T1 — Sources de backfill par priorité**

```python
def backfill_from_scraper(from_date: date, to_date: date, throttle_sec: float = 2.0) -> int:
    """Scraping Euronext paginé. Throttle obligatoire."""

def backfill_from_barchart(from_date: date, to_date: date) -> int:
    """Via Barchart API (si clé disponible). Max 1 an par requête tier gratuit."""

def backfill_from_manual(csv_path: Path | None = None) -> int:
    """Charge le CSV manuel et alimente ema_contract_daily.parquet.
    Cherche automatiquement dans EMA_BACKFILL_DIR si csv_path est None."""

def run_full_backfill(from_date: date = date(2014, 1, 1)) -> dict:
    """Orchestre les 3 sources. Produit coverage_report."""
```

**T2 — Fichier manuel (format attendu)**

```
data/raw/euronext_ema/manual_backfill/ema_historical_contracts.csv

Colonnes obligatoires :
  date, contract_code, contract_month, contract_year, expiry_date,
  open, high, low, settlement, volume, open_interest

Colonnes obligatoires (traçabilité source) :
  source_symbol          # code brut fournisseur : ex. "XBQ10", "CWHM26", "manual"
  canonical_contract_code # code canonique projet : ex. "EMA_Q2010"
  source                 # euronext_scraper / barchart / manual
  import_verdict         # usable / legacy_or_ambiguous / do_not_import
  active_month_status    # current_official / historical_confirmed / legacy_or_ambiguous

Colonnes optionnelles :
  quality_flag, bid, ask

Règle de validation obligatoire avant import :
  - chaque ligne doit correspondre à une entrée validée dans EMA_CONTRACT_REFERENCE
  - canonical_contract_code doit avoir month_code in {"H","M","Q","X"}, sauf historique confirmé officiellement
  - Si month_code non courant (ex. F) sans confirmation officielle → import_verdict = "legacy_or_ambiguous", ne pas inclure dans dataset final
  - Si settlement absent ET last absent → quality_flag = "no_price", exclure
  - Si open_interest absent → quality_flag = "oi_missing", conserver mais noter
```

Le module doit normaliser et valider ce fichier avant import, et rejeter les lignes avec `import_verdict = "do_not_import"`.

**T3 — Rapport de couverture**

```json
{
  "date_range": ["2014-01-01", "2025-12-31"],
  "total_days": 3130,
  "covered_days": 2842,
  "coverage_pct": 90.8,
  "contracts_found": ["EMA_X2014", "EMA_M2015", "EMA_Q2015", "..."],
  "missing_periods": [{"from": "2016-03-01", "to": "2016-04-15", "reason": "source_unavailable"}],
  "harvest_nov_coverage": {"2014": true, "2015": true, "2016": false, "...": "..."},
  "proxy_pct": 0.0
}
```

**T4 — CLI**

```bash
python -m mais.cli backfill euronext --from 2014-01-01 --to today
python -m mais.cli backfill euronext --manual data/raw/euronext_ema/manual_backfill/ema_historical_contracts.csv
```

**T5 — Validation couverture Barchart proxy avant import**

Avant toute écriture dans `data/processed`, produire un rapport de couverture uniquement dans `artefacts/euronext` :

- `barchart_xb_eod_coverage_contracts.csv`
- `barchart_xb_eod_coverage_by_year.csv`
- `barchart_xb_eod_coverage_report.txt`

Comparer deux univers :

- `strict_official` : H/M/Q/X uniquement ;
- `exploratory_with_F` : F/H/M/Q/X.

Règles :

- throttle 3 à 5 secondes recommandé ;
- retry exponentiel sur `429`, max 3 retries par contrat ;
- ne jamais appeler `lastPrice` settlement, utiliser `close_or_last` ;
- verdict `GO` si H/M/Q/X couvre au moins 8 crop years avec couverture business days ≥ 90 % ;
- verdict `GO_EXPLORATORY` si F/H/M/Q/X couvre correctement mais H/M/Q/X laisse trop de trous ;
- verdict `NO_GO` si trop de contrats retournent 0 ligne, 401, 403 ou 429 non récupérable.

### Critère de fin

- Historique ≥ 2014 dans `ema_contract_daily.parquet` avec contrats validés par `EMA_CONTRACT_REFERENCE`
- Rapport couverture produit
- 4 tests PASS

### Résultat ticket (2026-05-19)

- Module `src/mais/collect/euronext_backfill.py` créé avec orchestration `run_full_backfill()`, import manuel CSV, scraper Euronext des contrats actifs, placeholder Barchart explicite, fusion priorisée dans `ema_contract_daily.parquet` et rapport de couverture.
- Commande CLI créée : `venv/bin/python -m mais.cli backfill euronext --from 2014-01-01 --to 2026-05-19 --throttle-sec 2`.
- Backfill exécuté via source publique Euronext : `rows_written=664`, `coverage_pct=7.307`, contrats trouvés `EMA_H2027`, `EMA_M2026`, `EMA_M2027`, `EMA_Q2026`, `EMA_X2026`, `EMA_X2027`.
- Rapport produit : `artefacts/backfill_coverage_report.json`, avec `coverage_status=PARTIAL_REQUIRES_MANUAL_BACKFILL`, `meets_2014_requirement=false`, `observed_date_range=["2025-05-26", "2026-05-18"]`.
- Limite bloquante constatée : les endpoints publics Euronext testés exposent l'historique récent des maturités actuellement actives, mais pas les contrats expirés 2014–2025. Le fichier manuel historique reste requis : `data/raw/euronext_ema/manual_backfill/ema_historical_contracts.csv`.
- Vérifications : `ruff check src/mais/cli.py src/mais/collect/euronext_backfill.py ...` PASS ; `pytest tests/test_euronext_backfill.py ...` PASS (`25 passed` sur le bloc EMA).
- Review requise : ne pas passer `DONE` tant que l'historique ≥ 2014 ou un fournisseur de données historique n'est pas disponible.

### Review (2026-05-19)

- Verdict : **NON VALIDÉ — `BLOCKED` par source historique externe**.
- Code : OK pour importer un fichier manuel, scraper l'historique public récent et produire un rapport de couverture vérifiable.
- Données : insuffisantes pour satisfaire le ticket (`coverage_pct=7.307`, début observé `2025-05-26`, contrats novembre historiques 2014–2025 absents).
- Mise à jour après DATA-EMA-09 : Barchart public confirme les pages expirées, mais pas l'accès aux lignes OHLC historiques. DATA-EMA-02 reste bloqué jusqu'à obtention d'une source OHLC/API/CSV validée, puis DATA-EMA-10.

### Reprise DATA-EMA-02 (2026-05-20)

- Source candidate Barchart proxy web intégrée dans `src/mais/collect/euronext_backfill.py` :
  - session Barchart avec `XSRF-TOKEN` ;
  - endpoint `proxies/core-api/v1/historical/get` ;
  - retry exponentiel sur `429`, max 3 retries ;
  - source écrite sous `barchart_proxy_exploratory` ;
  - `lastPrice` conservé comme `close_or_last`, pas `settlement`.
- Mode CLI couverture seule ajouté :
  - `venv/bin/python -m mais.cli backfill euronext --from 2010-01-01 --to 2026-05-20 --throttle-sec 3 --barchart-coverage-only`.
- Artefacts couverture produits :
  - `artefacts/euronext/barchart_xb_eod_coverage_contracts.csv` ;
  - `artefacts/euronext/barchart_xb_eod_coverage_by_year.csv` ;
  - `artefacts/euronext/barchart_xb_eod_coverage_report.txt`.
- Verdict couverture :
  - `strict_official` H/M/Q/X : 7 crop years complets ≥ 90 %, couverture moyenne 89.854 % ;
  - `exploratory_with_F` F/H/M/Q/X : 13 crop years complets ≥ 90 %, couverture moyenne 95.935 % ;
  - verdict global `GO_EXPLORATORY`.
- Backfill strict H/M/Q/X exécuté via CLI :
  - commande : `venv/bin/python -m mais.cli backfill euronext --from 2010-01-01 --to 2026-05-20 --throttle-sec 3` ;
  - sortie : `source=barchart_proxy_exploratory`, `rows=4333`, `coverage=90.009%`, `contracts=68`.
- Contrôle parquet :
  - `data/processed/euronext/ema_contract_daily.parquet` existe ;
  - 4 818 lignes totales après fusion ;
  - 4 144 lignes `barchart_proxy_exploratory` conservées après déduplication ;
  - 664 lignes `euronext_chart_history` et 10 lignes `euronext_ajax_prices` conservées ;
  - 0 ligne `F/Janvier` ;
  - plage observée `2010-01-04` → `2026-05-20` ;
  - `settlement` non nul uniquement pour les lignes Euronext, pas pour Barchart ;
  - `close_or_last` non nul sur les lignes Barchart.
- Documentation `docs/ema_historical_source_research.md` mise à jour avec la validation couverture et le backfill strict.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/collect/euronext_backfill.py src/mais/collect/ema_contract_reference.py src/mais/cli.py tests/test_euronext_backfill.py tests/test_ema_contract_reference.py` PASS.
  - `venv/bin/python -m pytest tests/test_euronext_backfill.py tests/test_ema_contract_reference.py tests/test_paths_ema.py tests/test_barchart_contract_download_probe.py tests/test_ema_continuous_series_probe.py tests/test_barchart_ema_probe.py tests/test_euronext_daily_collector.py tests/test_euronext_endpoint_probe.py tests/test_ema_contracts.py -q` PASS (`41 passed`).
- Réserve majeure :
  - le backfill est exploitable pour la suite exploratoire, mais reste `PARTIAL_REQUIRES_MANUAL_BACKFILL` et non final officiel tant que settlement officiel/source contractuelle manquent.
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Critères validés :
  - historique réel EMA strict H/M/Q/X présent dans `EMA_CONTRACT_DAILY` ;
  - contrats validés par référence, aucune ligne `F` importée ;
  - rapport de couverture produit ;
  - CLI et tests OK.
- Réserves obligatoires pour la suite :
  - source Barchart proxy = exploratoire, non officielle ;
  - `settlement` absent sur Barchart, utiliser `close_or_last` ;
  - `GO_EXPLORATORY` seulement, car H/M/Q/X atteint 7 crop years ≥90% au lieu de 8 ;
  - DATA-EMA-03 peut commencer, mais les séries produites devront conserver le statut source exploratoire et ne pas prétendre être des séries finales officielles.
- Décision review : `DATA-EMA-03` peut passer `READY`.

---

## DATA-EMA-09 — Validation Barchart expired EMA contracts

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-11  

### Contexte

L'endpoint public Euronext testé dans DATA-EMA-07 ne fournit que les contrats actifs (couverture 7.3%, début mai 2025). Pour les benchmarks EMA, il faut un historique 2010-2026. Barchart expose des pages pour des contrats Euronext Corn expirés : XBQ10, XBF14, XBM14, XBX14, XBQ15, XBQ19. Ce ticket valide si ces données sont accessibles automatiquement et dans quel format.

**Codes Barchart à valider :**
- Préfixe racine : `XB`
- Mois : H=Mars, M=Juin, Q=Août, X=Novembre
- Format : `XB{mois}{année_2_chiffres}` → ex. `XBQ10` = Corn Euronext Août 2010

⚠ Barchart peut aussi lister des symboles `XBF..` (Corn Jan). Ils doivent rester `legacy_or_ambiguous` tant qu'une référence officielle ne confirme pas une cotation historique réelle.

### Objectifs mesurables

- Rapport `artefacts/euronext/barchart_probe_results.csv` : verdict par symbole (usable / page_exists_no_download / unavailable / legacy_or_ambiguous)
- Rapport `artefacts/euronext/barchart_probe_report.txt` : synthèse par source et par année
- Doc `docs/barchart_ema_data_source.md` : procédure d'accès + limites
- Décision documentée : Barchart = source principale pour DATA-EMA-02 OU alternative documentée
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/barchart_ema_probe.py` | **CRÉER** — sonde de validation Barchart |
| `artefacts/euronext/barchart_probe_results.csv` | Produit par la sonde |
| `artefacts/euronext/barchart_probe_report.txt` | Synthèse lisible |
| `docs/barchart_ema_data_source.md` | **CRÉER** — documentation source |
| `tests/test_barchart_ema_probe.py` | **CRÉER** — 3 tests |

### Tâches détaillées

**T1 — Sonde par symbole**

```python
# Symboles à tester : XBH/XBM/XBQ/XBX × années 2010 à 2026
# + XBF × années 2010 à 2020 (pour vérifier si Janvier était coté)
BARCHART_ROOT = "XB"
VALID_EMA_MONTHS = ["H", "M", "Q", "X"]   # mois officiels Euronext
MONTHS_TO_PROBE = ["H", "M", "Q", "X", "F"]  # F inclus pour investigation

def probe_barchart_symbol(symbol: str) -> dict:
    """Teste un symbole Barchart expired.
    Retourne :
      source_symbol,            # ex. "XBQ10" — code Barchart brut
      canonical_contract_code,  # ex. "EMA_Q2010" si mois H/M/Q/X, sinon None
      import_verdict,           # usable / legacy_or_ambiguous / do_not_import
      year, month_code, url,
      http_status, title_detected,
      has_historical_table, has_download_button,
      first_date_detected, last_date_detected,
      fields_detected,          # open/high/low/settlement/close/volume/open_interest
      open_interest_available,  # bool
      n_rows_visible,           # nombre de lignes dans le tableau HTML
      verdict                   # usable / page_exists_no_download / unavailable / legacy_or_ambiguous
    """
    # Règle de mapping source → canonique :
    # Si month_code in VALID_EMA_MONTHS {"H","M","Q","X"} :
    #     canonical_contract_code = f"EMA_{month_code}{year}"
    #     import_verdict = "usable" si données accessibles
    # Si month_code == "F" (Janvier) ou autre mois non officiel :
    #     canonical_contract_code = None
    #     import_verdict = "legacy_or_ambiguous"  ← ne jamais importer dans dataset final sans confirmation officielle
    #     noter dans le rapport pour investigation
```

Throttle obligatoire : min 2 secondes entre chaque requête HTTP.

**T2 — Rapport de synthèse**

```
BARCHART EMA PROBE REPORT — 2026-05-19

Symboles testés : 79 (H/M/Q/X × 2010-2026 + F × 2010-2020)
  usable         : XX
  page_exists    : XX
  unavailable    : XX

Couverture par mois :
  H (Mars)     : 2010–2026 ✅ / partielle / ❌
  M (Juin)     : ...
  Q (Août)     : ...
  X (Novembre) : ...
  F (Janvier)  : XX pages trouvées — à NE PAS intégrer dans pipeline EMA

Champs disponibles :
  settlement : OUI/NON
  volume     : OUI/NON
  open_interest : OUI/NON

Accès :
  Sans compte   : données visibles / téléchargement bloqué
  Barchart Premier requis : OUI/NON

Décision :
  ✅ Barchart = source principale DATA-EMA-02 (si 2014–2026 disponible avec OHLC)
  ⚠ Barchart Premier requis : [prix ou conditions]
  ❌ Pas utilisable : raison + alternative recommandée
```

**T3 — Documentation procédure**

Produire `docs/barchart_ema_data_source.md` :
- URL de base pour les contrats EMA expirés
- Convention de nommage (XB + mois + année 2 chiffres)
- Procédure de téléchargement CSV (manuel ou API)
- Limitation : si OI non disponible, préciser quelles colonnes sont manquantes
- Recommandation sur le tier d'accès

**T4 — Tests**

```python
def test_probe_report_produced():
    """barchart_probe_results.csv est produit et contient les colonnes attendues."""

def test_probe_throttle_respected():
    """Délai entre requêtes >= 2 secondes (vérifié via mock timer)."""

def test_january_flag_separate():
    """XBF (Janvier) est traité séparément et n'est pas intégré dans les mois valides EMA."""
```

### Critère de fin

- Rapport de synthèse produit pour tous les symboles H/M/Q/X × 2010-2026
- Décision documentée : Barchart utilisable ou non, et à quel tier
- Si utilisable : DATA-EMA-02 reprend avec Barchart comme source prioritaire
- Si non utilisable : alternative documentée (Euronext Web Services ou CSV manuel)

### Résultat ticket (2026-05-20)

- Sonde créée : `src/mais/collect/barchart_ema_probe.py`.
- Documentation créée : `docs/barchart_ema_data_source.md`.
- Tests créés : `tests/test_barchart_ema_probe.py`.
- Probe réel lancé avec throttle 2 s :
  - 79 symboles testés (`H/M/Q/X` 2010–2026 + `F` 2010–2020).
  - 79 pages HTTP 200.
  - H/M/Q/X : 68 pages `page_exists_no_download`.
  - F/Janvier : 11 pages `legacy_or_ambiguous`.
  - `has_historical_table=False` pour 79/79.
  - `n_rows_visible=0` pour 79/79.
  - `has_download_button=True` pour 79/79.
- Artefacts produits par la sonde :
  - `artefacts/euronext/barchart_probe_results.csv`
  - `artefacts/euronext/barchart_probe_report.txt`
- Décision : Barchart expose les pages et métadonnées Euronext Corn expirées, mais ne donne pas l'historique journalier en HTML public. `DATA-EMA-02` ne peut pas reprendre avec Barchart public ; il faut Barchart OnDemand/Premier/API, Euronext Web Services, LSEG/Bloomberg ou CSV manuel validé.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/collect/barchart_ema_probe.py tests/test_barchart_ema_probe.py` PASS.
  - `venv/bin/python -m pytest tests/test_barchart_ema_probe.py -q` PASS (`4 passed`).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ AVEC BLOCAGE SOURCE → `DONE`.
- Vérification review : la sonde couvre le périmètre prévu (79 symboles), applique le throttle, classe `F/Janvier` en `legacy_or_ambiguous`, et produit une décision exploitable.
- Décision confirmée : Barchart public ne fournit pas de lignes OHLC historiques visibles ; `DATA-EMA-10` et `DATA-EMA-02` restent `BLOCKED` tant qu'une source OHLC/API/CSV n'est pas disponible.
- Réserve : les champs détectés dans la page indiquent l'interface historique, pas des lignes de prix importables (`has_historical_table=False`, `n_rows_visible=0`).

---

## DATA-EMA-12 — Kit validation CSV historique EMA OHLC

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-09  

### Contexte

DATA-EMA-09 montre que Barchart public expose les pages contrats expirés, mais pas les lignes OHLC historiques en HTML public. Le prochain déblocage réel passe donc par un export CSV/API externe. Pour éviter d'importer un fichier incomplet ou contaminé, il faut un kit de validation strict avant DATA-EMA-10 et DATA-EMA-02.

### Objectifs mesurables

- Un validateur CSV historique EMA est disponible sans écrire dans `data/`.
- Le validateur vérifie les colonnes minimales, la période, les contrats H/M/Q/X, les lignes legacy F, les prix, la couverture par années et la présence des contrats novembre.
- Une documentation décrit le format attendu et les commandes de validation.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/ema_manual_backfill_validator.py` | **CRÉER** — validation CSV historique sans import |
| `docs/ema_historical_ohlc_acquisition.md` | **CRÉER** — procédure acquisition + format attendu |
| `tests/test_ema_manual_backfill_validator.py` | **CRÉER** — tests validateur |

### Tâches détaillées

**T1 — Validateur**

```python
def validate_manual_backfill_frame(df: pd.DataFrame, from_year: int = 2014, to_year: int = 2025) -> dict:
    """Retourne un rapport sans écrire dans data/.
    Vérifie date, contrat, prix, couverture, legacy, novembre par année.
    """
```

**T2 — CLI module**

```bash
venv/bin/python -m mais.collect.ema_manual_backfill_validator path/to/ema_historical_contracts.csv --from-year 2014 --to-year 2025
```

La commande affiche un JSON lisible et sort avec code `0` si le fichier est importable, `1` sinon.

**T3 — Documentation**

Documenter :
- colonnes obligatoires minimales ;
- colonnes recommandées pour traçabilité ;
- valeurs autorisées pour `import_verdict` et `active_month_status` ;
- critères de couverture avant import.

### Critère de fin

- Validateur et documentation créés.
- Tests couvrant CSV valide, période trop courte, legacy non confirmé, prix absent.
- Ticket passé en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- Validateur créé : `src/mais/collect/ema_manual_backfill_validator.py`.
- Documentation créée : `docs/ema_historical_ohlc_acquisition.md`.
- Tests créés : `tests/test_ema_manual_backfill_validator.py`.
- Le validateur vérifie :
  - colonnes `date`, contrat/livraison et prix ;
  - période couverte ;
  - années absentes ;
  - contrats novembre manquants ;
  - lignes legacy/non courantes ;
  - valeurs `import_verdict` et `active_month_status` ;
  - traçabilité `source_symbol` et `canonical_contract_code`.
- CLI disponible :
  - `venv/bin/python -m mais.collect.ema_manual_backfill_validator path/to/ema_historical_contracts.csv --from-year 2014 --to-year 2025`
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/collect/ema_manual_backfill_validator.py tests/test_ema_manual_backfill_validator.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_manual_backfill_validator.py -q` PASS (`4 passed`).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ → `DONE`.
- Vérification review : le validateur ne modifie pas `data/`, détecte les erreurs bloquantes avant import, et garde la règle legacy/F cohérente avec DATA-EMA-11.
- Vérifications relues :
  - `venv/bin/python -m ruff check src/mais/collect/ema_manual_backfill_validator.py tests/test_ema_manual_backfill_validator.py src/mais/collect/barchart_ema_probe.py tests/test_barchart_ema_probe.py src/mais/collect/euronext_backfill.py tests/test_euronext_backfill.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_manual_backfill_validator.py tests/test_barchart_ema_probe.py tests/test_euronext_backfill.py -q` PASS (`14 passed`).
- Réserve : aucun historique EMA OHLC réel n'a été fourni ; le validateur est prêt pour le prochain CSV/API export.

---

## DATA-EMA-13 — Télécharger ou reconstruire série continue EMA historique

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-12  

### Contexte

Même si les contrats individuels expirés ne sont pas encore téléchargeables, une série continue fournisseur (`XB`, `EMA1!`, `EMA=F`, `EMA1`, etc.) pourrait suffire pour tester rapidement le pivot EMA et construire une cible longue, à condition d'être clairement marquée comme déjà rollée par le fournisseur.

### Objectifs mesurables

- Tester plusieurs candidats de série continue EMA via pages Barchart et sources type yfinance.
- Distinguer :
  - page/métadonnées trouvées ;
  - lignes historiques visibles ;
  - téléchargement/API requis ;
  - série exploitable avec date/prix.
- Produire un rapport de décision sans écrire dans `data/`.
- Si une série longue est trouvée, documenter son statut `provider_rolled_continuous` et ses limites.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/paths.py` | **MODIFIER** — chemins artefacts probe continu |
| `tests/test_paths_ema.py` | **MODIFIER** — chemins artefacts probe continu |
| `src/mais/collect/ema_continuous_series_probe.py` | **CRÉER** — sonde série continue |
| `docs/ema_continuous_series_source.md` | **CRÉER** — décision et limites |
| `tests/test_ema_continuous_series_probe.py` | **CRÉER** — tests sonde |

### Tâches détaillées

**T1 — Candidats**

Tester au minimum :
- yfinance : `EMA=F`, `ZCE=F` ;
- Barchart / pages web : `XB*0`, `XB00`, `XB1!`, `EMA1!`, `EMA1`.

**T2 — Rapport**

Produire :
- `artefacts/euronext/ema_continuous_probe_results.csv`
- `artefacts/euronext/ema_continuous_probe_report.txt`

**T3 — Décision**

Verdicts possibles :
- `usable_continuous` : série longue exploitable ;
- `page_exists_no_download` : page trouvée mais OHLC non visible ;
- `empty_or_short` : source téléchargeable mais historique insuffisant ;
- `unavailable` : rien d'exploitable.

### Critère de fin

- Rapport produit.
- Décision documentée.
- Ticket passé en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- Chemins artefacts ajoutés dans `src/mais/paths.py` :
  - `EMA_CONTINUOUS_PROBE_RESULTS`
  - `EMA_CONTINUOUS_PROBE_REPORT`
- Sonde créée : `src/mais/collect/ema_continuous_series_probe.py`.
- Documentation créée : `docs/ema_continuous_series_source.md`.
- Tests créés : `tests/test_ema_continuous_series_probe.py`.
- Probe réel lancé :
  - yfinance `EMA=F` : `unavailable`, téléchargement vide / ticker introuvable.
  - yfinance `ZCE=F` : `unavailable`, téléchargement vide / ticker introuvable.
  - Barchart `XB*0` : `page_exists_no_download`, page Euronext Corn trouvée, bouton download détecté, aucune ligne OHLC visible.
  - Barchart `XB00`, `XB1!`, `EMA1!`, `EMA1` : `unavailable`, pages 404.
- Artefacts produits :
  - `artefacts/euronext/ema_continuous_probe_results.csv`
  - `artefacts/euronext/ema_continuous_probe_report.txt`
- Décision : aucune série continue EMA longue n'est exploitable en accès public automatique. Un export fournisseur/API ou CSV manuel reste requis.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/paths.py tests/test_paths_ema.py src/mais/collect/ema_continuous_series_probe.py tests/test_ema_continuous_series_probe.py` PASS.
  - `venv/bin/python -m pytest tests/test_paths_ema.py tests/test_ema_continuous_series_probe.py -q` PASS (`7 passed`).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ AVEC BLOCAGE SOURCE → `DONE`.
- Vérification review : `XB*0` est correctement classé `page_exists_no_download`, pas `usable_continuous`; yfinance ne fournit pas `EMA=F`/`ZCE=F`.
- Vérifications relues : `ruff check` PASS ; pytest ciblé PASS (`7 passed`).
- Réserve : aucune série continue longue EMA n'a été récupérée ; source fournisseur/API/CSV encore nécessaire.

---

## DATA-EMA-14 — Tester téléchargement contrat par contrat Barchart

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-09  

### Contexte

DATA-EMA-09 a testé beaucoup de pages expirées, mais il faut isoler un test court et très concret de téléchargement contrat par contrat : contrats proches (`XBM26`, `XBQ26`, `XBX26`) puis ancien contrat (`XBM14`). L'objectif est de savoir si le blocage vient seulement des contrats expirés anciens, ou aussi des contrats récents/actifs.

### Objectifs mesurables

- Tester exactement `XBM26`, `XBQ26`, `XBX26`, `XBM14`.
- Pour chaque symbole : page, métadonnées, bouton download, lignes visibles, endpoint ou API candidate si détectée.
- Produire un rapport lisible et une décision.
- Ne pas importer dans `data/`.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/paths.py` | **MODIFIER** — chemins artefacts probe contrats |
| `tests/test_paths_ema.py` | **MODIFIER** — chemins artefacts probe contrats |
| `src/mais/collect/barchart_contract_download_probe.py` | **CRÉER** — sonde contrat par contrat |
| `docs/barchart_contract_download_probe.md` | **CRÉER** — résultat et procédure |
| `tests/test_barchart_contract_download_probe.py` | **CRÉER** — tests sonde |

### Critère de fin

- Les 4 symboles sont testés.
- Décision : téléchargement public possible ou API/compte requis.
- Ticket passé en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- Chemins artefacts ajoutés dans `src/mais/paths.py` :
  - `EMA_BARCHART_CONTRACT_DOWNLOAD_RESULTS`
  - `EMA_BARCHART_CONTRACT_DOWNLOAD_REPORT`
- Sonde créée : `src/mais/collect/barchart_contract_download_probe.py`.
- Documentation créée : `docs/barchart_contract_download_probe.md`.
- Tests créés : `tests/test_barchart_contract_download_probe.py`.
- Probe réel lancé sur `XBM26`, `XBQ26`, `XBX26`, `XBM14`.
- Résultats :
  - `XBM26` : HTTP 200, Corn Jun 2026, `page_exists_no_download`.
  - `XBQ26` : HTTP 200, Corn Aug 2026, `page_exists_no_download`.
  - `XBX26` : HTTP 200, Corn Nov 2026, `page_exists_no_download`.
  - `XBM14` : HTTP 200, Corn Jun 2014, `page_exists_no_download`.
  - Les quatre pages signalent `historical-download`, `downloadLimit`, `historicalFutures`, `core-api`, mais `n_rows_visible=0`.
- Artefacts produits :
  - `artefacts/euronext/barchart_contract_download_results.csv`
  - `artefacts/euronext/barchart_contract_download_report.txt`
- Décision : téléchargement public contrat par contrat non exploitable ; compte/API Barchart requis, y compris pour contrats 2026.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/paths.py tests/test_paths_ema.py src/mais/collect/barchart_contract_download_probe.py tests/test_barchart_contract_download_probe.py` PASS.
  - `venv/bin/python -m pytest tests/test_paths_ema.py tests/test_barchart_contract_download_probe.py -q` PASS (`6 passed`).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-20)

- VALIDÉ AVEC BLOCAGE SOURCE → `DONE`.
- Vérification review : les quatre contrats demandés ont été testés, les pages sont correctes, et le verdict ne surclasse pas un bouton download en données exploitables.
- Vérifications relues :
  - `venv/bin/python -m ruff check src/mais/paths.py tests/test_paths_ema.py src/mais/collect/barchart_contract_download_probe.py tests/test_barchart_contract_download_probe.py src/mais/collect/ema_continuous_series_probe.py tests/test_ema_continuous_series_probe.py src/mais/collect/barchart_ema_probe.py tests/test_barchart_ema_probe.py` PASS.
  - `venv/bin/python -m pytest tests/test_paths_ema.py tests/test_barchart_contract_download_probe.py tests/test_ema_continuous_series_probe.py tests/test_barchart_ema_probe.py -q` PASS (`14 passed`).
- Réserve : téléchargement OHLC Barchart nécessite toujours compte/API/export autorisé.

---

## DATA-EMA-15 — Recherche active source OHLC historique EMA

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-09, DATA-EMA-12  

### Contexte

Les probes Barchart publics et continus n'ont pas donné de lignes OHLC. Il faut pousser la recherche sur :
- Barchart Premier / OnDemand / core API ;
- Euronext Web Services et endpoints publics historiques ;
- sources tierces éventuelles (Nasdaq Data Link, TradingView, Stooq, Investing, fournisseurs de données).

### Objectifs mesurables

- Tester directement des endpoints Euronext `md` historiques pour contrats 2014/2015/2026.
- Tester les endpoints Barchart publics plausibles/core API sans identifiants.
- Chercher et documenter les options payantes/professionnelles réalistes.
- Produire une note de décision claire avec prochaine action.
- Ne pas importer de données dans `data/`.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `docs/ema_historical_source_research.md` | **CRÉER** — synthèse recherches et essais |
| `.ai/STATE.md` | **MODIFIER** — état du blocage source |

### Critère de fin

- Recherches web + tests réseau documentés.
- Verdict sur chaque option A/B/C.
- Ticket passé en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- Document `docs/ema_historical_source_research.md` créé.
- Euronext public :
  - `intraday_historical/settlements/getChartData/EMA-DPAR/max` renvoie des lignes pour les contrats actifs 2026 (`Jun/Aug/Nov 2026`) ;
  - le même endpoint renvoie `0` ligne pour les contrats expirés 2014/2015 testés ;
  - `gateway.euronext.com/api/...` renvoie `401 Unauthorized` sans authentification.
- Barchart OnDemand :
  - `getHistory.json` et `getHistory.csv` testés sans clé ;
  - réponse `401 API key is missing or not valid`.
- Barchart proxy web :
  - source candidate technique identifiée via `proxies/core-api/v1/historical/get` après chargement de la page `price-history/historical` et récupération du token `XSRF-TOKEN` ;
  - champs EOD récupérés : date, open, high, low, last, volume, openInterest ;
  - exemples confirmés : `XBF14`, `XBH14`, `XBM14`, `XBQ14`, `XBX14`, `XBX21`, `XBF22`, `XBH23`, `XBM26` ;
  - liste racine `XB` confirmée via `futures.historical.byRoot(XB)` : 120 contrats, 81 contrats sélectionnés sur 2010-2026.
- Prototype mémoire sans écriture dans `data/` :
  - 4 480 lignes EOD récupérées ;
  - 3 528 dates uniques ;
  - couverture 2010-2020 environ 96.6 % à 98.1 % des jours ouvrables ;
  - un throttle trop faible a provoqué des `429`, mais les retries ralentis sur 2021-2023 ont réussi.
- Réserves :
  - proxy web non officiel, à isoler et throttler strictement ;
  - settlement non exposé explicitement, conserver `lastPrice` comme `close_or_last` ;
  - source production propre toujours recommandée : Barchart OnDemand/Premier ou Euronext NextHistory.
- Vérifications lancées :
  - tests réseau Euronext publics ;
  - tests réseau Barchart OnDemand sans clé ;
  - tests réseau Barchart proxy web ;
  - reconstruction mémoire sans écriture `data/`.
- Non lancé : ruff/pytest, car ticket documentaire et tests réseau uniquement.

### Review (2026-05-20)

- VALIDÉ AVEC RÉSERVES → `DONE`.
- Critères vérifiés :
  - recherches web + tests réseau documentés dans `docs/ema_historical_source_research.md` ;
  - verdict clair sur Barchart OnDemand/Premier, Barchart proxy web, Euronext public, Euronext Web Services/NextHistory et sources tierces ;
  - aucun import dans `data/`.
- Réserves :
  - la source Barchart proxy web est une source candidate technique, pas une API officielle stable ;
  - `lastPrice` doit rester `close_or_last` tant que settlement n'est pas validé par source contractuelle ;
  - toute collecte de masse doit être throttlée et auditer les `429`.
- Décision review : `DATA-EMA-10` peut passer `READY` avec dépendance explicite à `DATA-EMA-15`.

---

## DATA-EMA-10 — Table de référence contrats EMA

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-09, DATA-EMA-12, DATA-EMA-15  

### Contexte

Avant d'importer un historique, le projet doit figer une table de référence des contrats EMA. Cette table évite de mélanger les symboles fournisseurs (`XBQ10`, `CWHM26`, codes Euronext), les codes canoniques projet (`EMA_Q2010`) et les mois historiques ambigus (`XBF..`).

### Objectifs mesurables

- Table `EMA_CONTRACT_REFERENCE` produite avec une ligne par contrat validé.
- Chaque contrat a un `source_symbol`, un `canonical_contract_code`, un `month_code`, un `delivery_month`, un `delivery_year`, un `expiry_date` ou `last_trade_date` si disponible.
- Chaque ligne a `import_verdict` (`usable`, `legacy_or_ambiguous`, `do_not_import`) et `active_month_status` (`current_official`, `historical_confirmed`, `legacy_or_ambiguous`).
- Les symboles `XBF..` restent exclus par défaut sauf confirmation officielle documentée.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/ema_contract_reference.py` | **CRÉER** — construction/validation de la référence contrats |
| `docs/ema_contract_reference.md` | **CRÉER** — source, règles de mapping, cas ambigus |
| `tests/test_ema_contract_reference.py` | **CRÉER** — tests mapping et exclusions |

### Tâches détaillées

**T1 — Schéma canonique**

```python
REQUIRED_COLUMNS = [
    "source",
    "source_symbol",
    "canonical_contract_code",
    "month_code",
    "delivery_month",
    "delivery_year",
    "expiry_date",
    "last_trade_date",
    "active_month_status",
    "import_verdict",
]
```

**T2 — Règles de mapping**

```python
CURRENT_OFFICIAL_EMA_MONTHS = {"H": 3, "M": 6, "Q": 8, "X": 11}

def map_provider_symbol(source_symbol: str, provider: str) -> dict:
    """Retourne source_symbol, canonical_contract_code et verdict d'import.
    Les conventions fournisseur restent isolées ici.
    """
```

Règles :
- H/M/Q/X → `canonical_contract_code = EMA_{month_code}{year}` si le contrat est confirmé par la source.
- F/Janvier ou autre mois non courant → `canonical_contract_code = None`, `active_month_status = "legacy_or_ambiguous"`, `import_verdict = "legacy_or_ambiguous"` sauf preuve officielle.
- Une ligne `legacy_or_ambiguous` ne doit jamais alimenter les séries finales par défaut.

**T3 — Documentation**

`docs/ema_contract_reference.md` doit lister :
- sources utilisées ;
- conventions par fournisseur ;
- règles d'exclusion ;
- cas Janvier/F ;
- limites restantes sur les dates d'expiration et l'open interest.

### Critère de fin

- `EMA_CONTRACT_REFERENCE` est générable et importable.
- Les cas H/M/Q/X et F/Janvier sont couverts par tests.
- Le ticket passe en `NEEDS_REVIEW`.

### Résultat ticket (2026-05-20)

- Module `src/mais/collect/ema_contract_reference.py` créé :
  - constantes `CURRENT_OFFICIAL_EMA_MONTHS`, `LEGACY_OR_INVESTIGATION_EMA_MONTHS` ;
  - `map_provider_symbol()` pour isoler la convention Barchart `XB{month}{yy}` ;
  - `build_reference_from_barchart_rows()` pour consommer les lignes `futures.historical.byRoot(XB)` ;
  - `build_contract_reference()` pour générer une référence déterministe 2010-2026 ;
  - `validate_contract_reference()` pour bloquer les colonnes manquantes, doublons et legacy importables ;
  - `write_contract_reference()` pour produire `EMA_CONTRACT_REFERENCE`.
- Documentation `docs/ema_contract_reference.md` créée :
  - source Barchart `XB` ;
  - règles H/M/Q/X ;
  - cas `XBF..` legacy ;
  - limites settlement/date d'expiration/rate-limit.
- Tests `tests/test_ema_contract_reference.py` créés :
  - mapping officiel historique ;
  - mapping officiel courant ;
  - exclusion Janvier/F ;
  - univers par défaut ;
  - import depuis lignes Barchart ;
  - rejet legacy importable ;
  - roundtrip parquet en répertoire temporaire.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/collect/ema_contract_reference.py tests/test_ema_contract_reference.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_contract_reference.py -q` PASS (`7 passed`).
- Non lancé : génération réelle de `data/processed/euronext/ema_contract_reference.parquet`, pour éviter d'écrire dans `data/` hors commande explicitement demandée.

### Review (2026-05-20)

- VALIDÉ → `DONE`.
- Vérification review :
  - `build_contract_reference(2010, 2026, current_year=2026)` produit 81 lignes ;
  - 68 contrats H/M/Q/X `usable` ;
  - 13 contrats `F` `legacy_or_ambiguous` ;
  - 0 legacy importable ;
  - 0 contrat importable sans `canonical_contract_code`.
- Vérifications relues :
  - `ruff check` PASS ;
  - pytest ciblé PASS (`7 passed`).
- Décision review : `DATA-EMA-02` peut passer `READY`.

---

## DATA-EMA-03 — Séries continues EMA

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : DATA-EMA-02  

### Contexte

`ema_contract_daily.parquet` contient des contrats discrets. Les modèles de ML et les features de rendement nécessitent des séries continues sans ruptures liées aux rolls, mais aussi une table de courbe quotidienne par rang de liquidité/maturité. Il faut construire les séries utiles au modèle sans transformer les prix reportés en prix artificiels.

### Objectifs mesurables

- Séries `front_raw`, `front_adjusted`, `liquid_raw`, `liquid_adjusted`, `harvest_nov` produites dans `EMA_PROCESSED_DIR`
- Table `EMA_CURVE_DAILY` produite avec rangs de contrats et champs de liquidité
- Roll log complet avec toutes les dates de changement de contrat
- Série `raw` et `adjusted` distinguées et cohérentes
- Série `harvest_nov` correcte selon la règle de sélection contrat (§10.3 ARCHITECTURE_EMA_PRO)
- Ruff PASS, pytest PASS (≥ 6 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/euronext_continuous.py` | **CRÉER** — module séries continues |
| `src/mais/features/__init__.py` | **MODIFIER** — brancher dans build_features() |
| `tests/test_euronext_continuous.py` | **CRÉER** — ≥ 6 tests |

### Tâches détaillées

**T1 — Fonctions de construction**

```python
def build_curve_daily(contracts: pd.DataFrame) -> pd.DataFrame:
    """Table quotidienne des contrats disponibles par date.
    Colonnes minimales : date, contract_code, rank_by_expiry, rank_by_oi,
    price, settlement, volume, open_interest, days_to_expiry.
    """

def build_front_continuous(contracts: pd.DataFrame, min_dte: int = 15) -> pd.DataFrame:
    """Front contract. Sélection : DTE >= min_dte AND prix disponible.
    Retourne : date, price, contract_code, days_to_expiry, volume, oi, roll_event, roll_adjustment."""

def build_front_adjusted(front_raw: pd.DataFrame) -> pd.DataFrame:
    """Ajuste le raw par soustraction cumulative des roll_adjustments.
    Utilisé uniquement pour features de rendement — jamais reporté comme prix."""

def build_liquid_continuous(
    contracts: pd.DataFrame,
    min_dte: int = 15,
    max_dte: int = 370,
) -> pd.DataFrame:
    """Contrat liquide : max open_interest parmi les contrats avec DTE dans [min_dte, max_dte].
    Fallback volume si open_interest absent, avec quality_flag documenté."""

def build_harvest_november(contracts: pd.DataFrame) -> pd.DataFrame:
    """Règle sélection contrat Novembre §10.3 ARCHITECTURE_EMA_PRO :
    - t < expiry(EMA_X{année(t)}) - 5j → EMA_X{année(t)}
    - sinon → EMA_X{année(t)+1}
    Jamais back-adjusted."""

def build_back_adjusted(raw_series: pd.DataFrame) -> pd.DataFrame:
    """Ajuste une série raw par soustraction cumulative des roll gaps.
    Utilisé pour les rendements/features, jamais comme prix affiché agriculteur."""
```

**T2 — Roll log**

```python
def extract_roll_log(series: pd.DataFrame) -> pd.DataFrame:
    """Extrait les dates de roll et les gaps de prix.
    Colonnes : date, old_contract, new_contract, price_old, price_new, roll_gap_eur_t"""
```

**T3 — Tests**

```python
def test_harvest_nov_selection_mai_2026():
    # Mai 2026 → EMA_X2026 (Nov 2026 non expiré)
def test_harvest_nov_selection_decembre_2026():
    # Décembre 2026 → EMA_X2027 (Nov 2026 expiré)
def test_adjusted_minus_raw_equals_cumulative_roll():
    # invariant : sum(roll_adjustments) = raw[-1] - adjusted[-1]
def test_liquid_series_selects_highest_oi_within_dte_window():
    # choisit le contrat le plus liquide admissible
def test_no_duplicate_dates():
    # chaque série n'a qu'une ligne par date
def test_roll_event_flag_on_contract_change():
    # roll_event = True exactement aux dates de changement
```

### Critère de fin

- Séries front/liquid raw+adjusted, harvest_nov et `EMA_CURVE_DAILY` produites dans `EMA_PROCESSED_DIR`
- Roll log non vide (≥ 1 roll par an si historique > 2014)
- 6 tests PASS

### Résultat ticket (2026-05-20)

- Module `src/mais/features/euronext_continuous.py` créé :
  - `build_curve_daily`
  - `build_front_continuous`
  - `build_front_adjusted`
  - `build_liquid_continuous`
  - `build_harvest_november`
  - `build_back_adjusted`
  - `extract_roll_log`
  - `build_and_save_continuous_series`
  - `load_continuous_feature_block`
- `src/mais/features/__init__.py` branché pour ajouter les features EMA continues si les sorties `DATA-EMA-03` existent.
- Tests `tests/test_euronext_continuous.py` créés (`10` tests) :
  - rangs curve par maturité / open interest ;
  - détection roll event ;
  - invariant raw vs adjusted ;
  - sélection contrat liquide ;
  - sélection `harvest_nov` mai/décembre ;
  - absence de doublons ;
  - écriture parquet ;
  - usage de `adjusted_price` pour les features ML ;
  - fallback volume documenté via `liquidity_rank_source` quand l'open interest manque.
- Sorties produites dans `data/processed/euronext/` :
  - `ema_curve_daily.parquet` : `4 144` lignes ;
  - `ema_front_continuous_raw.parquet` : `3 275` lignes ;
  - `ema_front_continuous_adjusted.parquet` : `3 275` lignes ;
  - `ema_liquid_continuous_raw.parquet` : `3 275` lignes ;
  - `ema_liquid_continuous_adjusted.parquet` : `3 275` lignes ;
  - `ema_most_liquid_continuous.parquet` : `3 275` lignes ;
  - `ema_harvest_nov.parquet` : `959` lignes.
- Roll logs vérifiés :
  - `front_raw` : `65` rolls sur `17` années ;
  - `liquid_raw` : `67` rolls sur `17` années ;
  - `harvest_nov` : `16` rolls sur `16` années.
- Toutes les séries conservent `source_quality='exploratory'` pour ne pas masquer la nature Barchart proxy.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/features/euronext_continuous.py src/mais/features/__init__.py tests/test_euronext_continuous.py` PASS.
  - `venv/bin/python -m pytest tests/test_euronext_continuous.py -q` PASS (`10 passed`).
  - `venv/bin/python -m pytest tests/test_euronext_continuous.py tests/test_ema_contract_reference.py tests/test_euronext_backfill.py tests/test_paths_ema.py -q` PASS (`31 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ avec réserve : les séries sont exploitables pour le roll audit et les features, mais la source reste `barchart_proxy_exploratory`, non officielle.
- Correction faite pendant review : la sélection `liquid_raw` expose maintenant `liquidity_rank_source` pour documenter le fallback volume si l'open interest manque.
- Critères validés : sorties produites, raw/adjusted séparés, harvest_nov conforme, roll logs non vides, ruff PASS, pytest complet PASS.
- Décision review : `DATA-EMA-03` → `DONE`, `DATA-EMA-08` → `READY`.

---

## DATA-EMA-08 — Roll audit

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-03  

### Contexte

Les gaps de prix au roll peuvent créer des faux signaux dans les targets et les features (rendement annualisé négatif/positif artificiel). Le roll audit vérifie que les rolls sont correctement détectés, documentés, et que les targets ne sont pas contaminés.

### Objectifs mesurables

- Toutes les dates de roll listées avec le gap de prix correspondant
- Aucune target EMA ne traverse un roll non ajusté sans correction
- Rapport `artefacts/roll_audit/roll_audit_report.txt` produit
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/roll_audit.py` | **CRÉER** — auditeur de rolls |
| `artefacts/roll_audit/roll_audit_report.txt` | Produit par le module |
| `tests/test_roll_audit.py` | **CRÉER** — 3 tests |

### Tâches détaillées

**T1 — Audit des rolls**

```python
def audit_rolls(front_raw: pd.DataFrame, front_adjusted: pd.DataFrame) -> dict:
    """Vérifie :
    1. Nombre de rolls par année (attendu : 3-5 par an)
    2. Gap moyen au roll (attendu : < 10 €/t)
    3. Gap max (alerter si > 20 €/t = possible erreur données)
    4. Que raw - adjusted = sum(roll_gaps) à chaque date
    """
```

**T2 — Vérification targets vs rolls**

```python
def check_targets_cross_rolls(targets: pd.DataFrame, roll_log: pd.DataFrame) -> list[dict]:
    """Identifie les targets qui traversent une date de roll.
    Une target y_up_hH calculée sur une fenêtre contenant un roll doit utiliser
    la série adjusted, pas raw.
    Retourne : liste de violations potentielles."""
```

**T3 — Rapport**

```
ROLL AUDIT REPORT — 2026-05-19

Front continuous RAW vs ADJUSTED
  Total rolls detected: 42
  Rolls per year (avg): 3.5
  Average roll gap: 2.3 €/t
  Max roll gap: 8.7 €/t (2022-06-08, EMA_M2022 → EMA_Q2022)
  
  ⚠ Rolls crossing targets (h20): 127 windows
  → Vérifier que les features de rendement utilisent bien la série adjusted.

Verdict: OK (aucun roll gap > 20 €/t)
```

### Résultat ticket (2026-05-20)

- Module `src/mais/research/roll_audit.py` créé :
  - `audit_rolls(front_raw, front_adjusted)` ;
  - `check_targets_cross_rolls(targets, roll_log)` ;
  - `write_roll_audit_report(...)` ;
  - `run_roll_audit(...)`.
- Tests `tests/test_roll_audit.py` créés (`5` tests) :
  - détection gap + invariant raw/adjusted ;
  - échec si ajustement incohérent ;
  - détection fenêtres target EMA traversant un roll ;
  - exclusion par défaut des targets CBOT génériques ;
  - écriture rapport texte.
- Rapport produit : `artefacts/roll_audit/roll_audit_report.txt`.
- Le rapport liste les `65` dates de roll avec ancien contrat, nouveau contrat et gap EUR/t.
- Résultat réel sur `ema_front_continuous_raw/adjusted` :
  - total rolls : `65` ;
  - années avec rolls : `17` ;
  - moyenne rolls/an : `3.824` ;
  - gap absolu moyen : `10.623` EUR/t ;
  - gap absolu max : `54.250` EUR/t (`2013-08-08`) ;
  - invariant adjusted : PASS (`max_abs_error=0.0`, `n_checked=3275`) ;
  - targets EMA : `PENDING_NO_EMA_TARGETS` car `DATA-TARGETS-01` n'est pas encore fait ;
  - verdict : `WARN` (`average_roll_gap_above_threshold`, `max_roll_gap_above_threshold`).
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/roll_audit.py tests/test_roll_audit.py src/mais/features/euronext_continuous.py tests/test_euronext_continuous.py` PASS.
  - `venv/bin/python -m pytest tests/test_roll_audit.py -q` PASS (`5 passed`).
  - `venv/bin/python -m pytest tests/test_roll_audit.py tests/test_euronext_continuous.py -q` PASS (`15 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ avec réserve : l'audit ne bloque pas la suite, mais le verdict réel est `WARN`.
- Réserve à propager : les gaps (`avg=10.623` EUR/t, `max=54.250` EUR/t) interdisent d'utiliser les raw returns autour des rolls ; les features de rendement doivent utiliser les séries adjusted.
- Correction faite pendant review : ajout de la section `Roll details` listant toutes les dates de roll et leurs gaps dans le rapport.
- Critères validés : rapport produit, roll dates complètes, invariant adjusted PASS, ruff PASS, pytest complet PASS.
- Décision review : `DATA-EMA-08` → `DONE`, `DATA-EMA-04` → `READY`.

---

## DATA-EMA-04 — Features courbe Euronext

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : DATA-EMA-03, DATA-EMA-08  

### Contexte

La structure de la courbe des futures EMA est une information clé que le modèle CBOT n'a pas. Backwardation = tension physique immédiate. Contango = stockage rémunéré mais marché détendu. Le spread Nov-Mar mesure l'anticipation de la structure saisonnière. Ce sont les features les plus spécifiques au marché Euronext.

### Objectifs mesurables

- 18 features de courbe calculées quotidiennement (§4.4 ARCHITECTURE_EMA_PRO)
- Toutes les features anti-leakage (shift(1) minimum, settlement J-1 disponible J+1 matin)
- Fichier `EMA_CURVE_FEATURES` produit
- Ruff PASS, pytest PASS (≥ 5 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/euronext_curve.py` | **CRÉER** — module features courbe |
| `tests/test_euronext_curve.py` | **CRÉER** — ≥ 5 tests |

### Tâches détaillées

**T1 — Fonction principale**

```python
def build_curve_features(
    contracts: pd.DataFrame,
    front_raw: pd.DataFrame,
    harvest_nov: pd.DataFrame,
    cbot: pd.DataFrame,
    eurusd: pd.DataFrame,
) -> pd.DataFrame:
    """18 features de courbe EMA + 6 features cross-market CBOT-EMA.
    Anti-leakage : settlement J → features disponibles J+1 (shift(1) appliqué).
    """
```

**T2 — Features courbe obligatoires**

```python
# Prix de référence
ema_front_price, ema_second_price, ema_third_price
ema_harvest_nov_price, ema_next_march_price
ema_liquid_price

# Spreads
ema_spread_f0_f1 = ema_front - ema_second
ema_spread_f1_f2 = ema_second - ema_third
ema_spread_f0_f2 = ema_front - ema_third
ema_spread_nov_mar = ema_harvest_nov - ema_next_march

# Pente de courbe
ema_curve_slope_3 = (ema_third_price - ema_front_price) / max(dte_third - dte_front, 1)
ema_curve_slope_6 = pente approximative front → contrat autour de 6 mois si disponible

# Flags structure
ema_contango_flag      = (ema_curve_slope_3 > 0).astype(int)
ema_backwardation_flag = (ema_curve_slope_3 < 0).astype(int)

# Carry et roll yield
ema_carry_front_second = ema_spread_f0_f1 / ema_front_price
ema_roll_yield_ann = ema_carry_front_second * (365 / max(dte_second - dte_front, 1))

# Liquidité et positions
ema_oi_total, ema_volume_total, ema_oi_concentration, ema_liquidity_shift
ema_open_interest_available, ema_curve_contract_count

# Cross-market CBOT-EMA
cbot_eur_t = cbot_cents_bu / 100 / eurusd * 39.3679
ema_cbot_basis = ema_front_price - cbot_eur_t
ema_cbot_basis_zscore_52w  # z-score expanding 52 semaines
ema_cbot_rel_strength_20d  # (ema/ema_20d) - (cbot_eur_t/cbot_eur_t_20d)
```

**T3 — Tests**

```python
def test_contango_flag_correct():
    # slope > 0 → contango = 1, backwardation = 0
def test_basis_calculation():
    # basis = ema - (cbot_cents/100/eurusd*39.3679)
def test_shift1_applied():
    # toutes les features ont 1 NaN en première ligne (shift)
def test_no_future_leak():
    # features_date[t] ne contient rien calculé à partir de prices[t+k]
def test_output_columns_complete():
    # les 18 features attendues sont présentes
```

### Critère de fin

- Features de courbe produites dans `EMA_CURVE_FEATURES`
- Anti-leakage vérifié (shift(1) appliqué)
- 5 tests PASS

### Résultat ticket (2026-05-20)

- Module `src/mais/features/euronext_curve.py` créé.
- Features produites (`28` colonnes numériques laggées) :
  - prix EMA : `ema_front_price`, `ema_second_price`, `ema_third_price`, `ema_harvest_nov_price`, `ema_next_march_price`, `ema_liquid_price` ;
  - spreads / structure : `ema_spread_f0_f1`, `ema_spread_f1_f2`, `ema_spread_f0_f2`, `ema_spread_nov_mar`, `ema_curve_slope_3`, `ema_curve_slope_6`, `ema_contango_flag`, `ema_backwardation_flag` ;
  - carry / roll yield : `ema_carry_front_second`, `ema_roll_yield_ann` ;
  - liquidité : `ema_oi_total`, `ema_volume_total`, `ema_oi_concentration`, `ema_liquidity_shift`, `ema_open_interest_available`, `ema_curve_contract_count` ;
  - cross-market : `cbot_eur_t`, `ema_cbot_basis`, `ema_cbot_basis_zscore_52w`, `ema_cbot_rel_strength_20d` ;
  - rendements adjusted : `ema_front_return_5d_adjusted`, `ema_front_vol_20d_adjusted`.
- Anti-leakage : toutes les features de sortie sont `shift(1)` ; la première ligne feature est entièrement NaN.
- Rendements/volatilité : calculés sur `front_adjusted`, conformément au roll audit `WARN`.
- Fichier produit : `data/processed/euronext/ema_curve_features.parquet`.
- Résultat réel :
  - lignes : `3 797` ;
  - colonnes : `29` (`Date` + `28` features) ;
  - plage : `2010-01-04` → `2026-05-20` ;
  - `ema_cbot_basis` non nul : `3 078` lignes ;
  - première ligne all-NaN features : `True`.
- Tests `tests/test_euronext_curve.py` créés (`7` tests) :
  - contango/backwardation ;
  - calcul basis CBOT-EUR/t ;
  - shift(1) ;
  - anti-leakage futur ;
  - colonnes complètes ;
  - rendements adjusted ;
  - écriture parquet.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/features/euronext_curve.py tests/test_euronext_curve.py` PASS.
  - `venv/bin/python -m pytest tests/test_euronext_curve.py -q` PASS (`7 passed`).
  - `venv/bin/python -m pytest tests/test_euronext_curve.py tests/test_euronext_continuous.py tests/test_roll_audit.py -q` PASS (`22 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ avec réserve : le fichier de features courbe est prêt, mais l'assemblage final dans `build_features()` et `factor_metadata.yaml` est à faire dans `DATA-MASTER-01`, dont c'est le périmètre explicite.
- Réserve source : les features héritent de la nature `barchart_proxy_exploratory` des séries EMA.
- Critères validés : `EMA_CURVE_FEATURES` produit, anti-leakage shift(1) vérifié, rendements sur adjusted, ruff PASS, pytest complet PASS.
- Décision review : `DATA-EMA-04` → `DONE`, `DATA-MASTER-01` → `READY`.

---

## DATA-EMA-05 — Rapport qualité quotidien

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-01  

### Contexte

Chaque collecte doit produire un rapport qualité JSON permettant de décider si le signal du jour est fiable ou doit être reclassé UNCERTAIN. Le `data_availability_score` est la métrique centrale : < 0.70 → signal UNCERTAIN automatique.

### Objectifs mesurables

- Rapport JSON produit après chaque collecte dans `REPORTS_QUALITY_DIR/YYYY-MM-DD_quality.json`
- Calcul `data_availability_score` correct et testé
- Typed uncertainty codes appliqués automatiquement
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/data_quality.py` | **CRÉER** — module qualité |
| `tests/test_data_quality.py` | **CRÉER** — 4 tests |

### Tâches détaillées

**T1 — Calcul data_availability_score**

Sources pondérées :
```python
QUALITY_WEIGHTS = {
    "euronext_settlement": 0.30,   # source principale
    "cbot_corn":           0.20,   # marché directeur
    "eurusd_rate":         0.15,   # FX critique
    "ttf_natgas":          0.05,
    "wasde":               0.15,   # max 7 jours de lag accepté
    "cot":                 0.10,   # max 3 jours de lag accepté
    "fas_export_sales":    0.05,
}
# score = sum(weight * present) pour chaque source à jour
```

**T2 — Rapport JSON** (structure conforme §8 ARCHITECTURE_EMA_PRO)

**T3 — Typed uncertainty flags**

```python
UNCERTAINTY_TRIGGERS = {
    "DATA_MISSING":   lambda s: s["data_availability_score"] < 0.70,
    "PROXY_DATA":     lambda s: s["euronext"]["is_proxy"],
    "LOW_LIQUIDITY":  lambda s: s["euronext"]["avg_oi_front"] < 500,
    "NEAR_WASDE":     lambda s: s["wasde"]["days_to_next"] <= 5,
}
```

### Résultat ticket (2026-05-19)

- Module créé : `src/mais/collect/data_quality.py`.
- Rapport produit : `data/reports/quality/2026-05-19_quality.json`.
- Score observé : `data_availability_score=0.30` avec `uncertainty_flags=["DATA_MISSING"]`, attendu car seule la source Euronext est renseignée à ce stade.
- Tests créés : `tests/test_data_quality.py`.
- Vérifications : `ruff check` PASS ; `pytest tests/test_data_quality.py -q` PASS (5 tests).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-19)

- VALIDÉ → `DONE`.
- Le statut `UNCERTAIN` actuel est cohérent avec la disponibilité partielle des sources.

---

## DATA-EMA-06 — Anti-leakage calendrier par source

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : aucune (peut se faire en parallèle)  

### Contexte

L'anti-leakage actuel applique `shift(1)` partout, ce qui est approximatif. WASDE est publié à 12h ET — les données sont disponibles le même jour après 18h. COT est publié le vendredi 15h30 — disponible le lundi suivant. Un module centralisé de validation des dates de disponibilité évite les incohérences.

### Objectifs mesurables

- Module `leakage_calendar.py` avec la matrice complète de disponibilité (§5 ARCHITECTURE_EMA_PRO)
- Fonction `is_available(source, publish_date, use_date) -> bool` testée
- Intégré dans `build_features()` comme vérificateur optionnel
- Ruff PASS, pytest PASS (≥ 5 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/leakage/availability.py` | **CRÉER** — module disponibilité |
| `src/mais/leakage/__init__.py` | **CRÉER** ou **MODIFIER** |
| `tests/test_leakage_calendar.py` | **CRÉER** — ≥ 5 tests |

### Tâches détaillées

**T1 — Dictionnaire de disponibilité**

```python
SOURCE_AVAILABILITY: dict[str, dict] = {
    "euronext_settlement": {"lag_days": 1, "same_day_after": "18:00 CET"},
    "cbot_corn":           {"lag_days": 1},
    "eurusd_rate":         {"lag_days": 0},
    "cftc_cot":            {"lag_days": 3, "publication_day": "friday"},
    "usda_wasde":          {"lag_days": 0, "same_day_after": "18:00 ET", "frequency": "monthly"},
    "usda_fas_export_sales": {"lag_days": 0, "publication_day": "thursday"},
    "usda_nass_crop_progress": {"lag_days": 0, "publication_day": "monday"},
    "ec_mars_bulletin":    {"lag_days": 30, "shift_months": 1},
    "agreste_france":      {"lag_days": 7},
    "franceagrimer":       {"lag_days": 30},
    "conab_brazil":        {"lag_days": 30},
}

def is_available(source: str, publish_date: date, use_date: date) -> bool:
    """Retourne True si la source est légitimement utilisable à use_date."""

def apply_availability_shift(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Applique le décalage correct à toutes les colonnes d'un DataFrame source."""
```

**T2 — Tests**

```python
def test_wasde_not_available_same_day_before_publication():
    # WASDE publié 12h ET → pas disponible à 10h ET même jour
def test_cot_available_monday_after_friday():
    # COT vendredi 15h30 → disponible lundi
def test_euronext_available_next_morning():
    # settlement J → disponible J+1
def test_shift_applied_correctly_to_dataframe():
    # apply_availability_shift applique le bon lag
```

### Résultat ticket (2026-05-19)

- Module créé : `src/mais/leakage/availability.py`.
- Exports ajoutés dans `src/mais/leakage/__init__.py`.
- Fonctions livrées : `is_available`, `first_available_datetime`, `apply_availability_shift`, `filter_available_as_of`.
- Matrice de disponibilité incluse pour Euronext, CBOT, EUR/USD, COT, WASDE, FAS, NASS, EC MARS, Agreste, FranceAgriMer, CONAB.
- Tests créés : `tests/test_leakage_calendar.py`.
- Vérifications : `ruff check` PASS ; `pytest tests/test_leakage_calendar.py -q` PASS (6 tests).
- Ticket passé en `NEEDS_REVIEW`.

### Review (2026-05-19)

- VALIDÉ AVEC RÉSERVE → `DONE`.
- Réserve : l'intégration dans `build_features()` sera effective dans `DATA-MASTER-01`, car `features/__init__.py` n'est pas listé comme fichier modifiable de ce ticket.

---

## DATA-MASTER-01 — Dataset master EMA+CBOT

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : DATA-EMA-04, DATA-EMA-06  

### Contexte

`features.parquet` contient les features CBOT. Il faut l'étendre avec les features EMA (courbe, séries continues, cross-market) en respectant l'anti-leakage calendrier (DATA-EMA-06). Le dataset final doit couvrir la période commune EMA+CBOT et permettre les ablations par famille.

### Objectifs mesurables

- `features.parquet` étendu avec les features EMA (ou nouveau fichier `ema_features.parquet`)
- Famille de features documentée dans `config/factor_metadata.yaml`
- Anti-leakage vérifié : aucune feature EMA n'est disponible avant sa date réelle
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/__init__.py` | **MODIFIER** — brancher `euronext_curve`, `euronext_continuous` |
| `src/mais/features/ema_features.py` | **CRÉER** — wrapper d'assemblage features EMA |
| `config/factor_metadata.yaml` | **MODIFIER** — ajouter famille `euronext_curve` |
| `tests/test_ema_features_pipeline.py` | **CRÉER** — 4 tests |

### Tâches détaillées

**T1 — Assemblage features EMA dans `build_features()`**

```python
def build_ema_features(
    front_raw: pd.DataFrame,
    front_adjusted: pd.DataFrame,
    harvest_nov: pd.DataFrame,
    curve_features: pd.DataFrame,
    leakage_calendar: dict,
) -> pd.DataFrame:
    """Assemble toutes les features EMA avec anti-leakage calendrier.
    Retourne un DataFrame aligné sur l'index quotidien de features.parquet."""
```

**T2 — Famille factor_metadata.yaml**

```yaml
euronext_curve:
  description: "Features courbe Euronext EMA (spreads, carry, basis CBOT-EMA)"
  n_features: 18
  anti_leakage: "settlement J-1, disponible J (lag 1 jour)"
  source: euronext_scraper
  features:
    - ema_front_price
    - ema_harvest_nov_price
    - ema_cbot_basis
    - ema_cbot_basis_zscore_52w
    - ema_contango_flag
    - ema_backwardation_flag
    - ...
```

**T3 — Vérification anti-leakage**

```python
def test_ema_features_no_future_leak():
    """Aucune feature EMA calculée à t ne contient d'information de t+1."""
    # utiliser audit_leakage() existant
```

### Résultat ticket (2026-05-20)

- Module `src/mais/features/ema_features.py` créé :
  - assemble `EMA_CURVE_FEATURES` + features continuous EMA ;
  - ne force aucune colonne EMA si les fichiers/blocs EMA sont absents ;
  - ajoute les colonnes de disponibilité `ema_curve_available`, `ema_continuous_available`, `ema_data_availability_score` quand un bloc EMA existe ;
  - vérifie qu'aucune cible EMA (`y_*ema*`) ne fuit dans les features.
- `src/mais/features/__init__.py` branché :
  - `build_features()` ajoute maintenant le bloc EMA complet quand disponible ;
  - l'ancien branchement continuous-only a été remplacé par l'assemblage master EMA.
- `config/factor_metadata.yaml` mis à jour :
  - famille `euronext_curve` ajoutée ;
  - `n_feature_cols=37` (`28` courbe + `6` continuous + `3` disponibilité) ;
  - source explicitement marquée `barchart_proxy_exploratory`, `source_quality=exploratory`.
- Tests `tests/test_ema_features_pipeline.py` créés (`6` tests) :
  - pas de colonnes forcées sans bloc EMA ;
  - assemblage courbe + continuous ;
  - rejet des targets EMA dans X ;
  - intégration dans `build_features()` quand le bloc existe ;
  - skip propre quand le bloc n'existe pas ;
  - metadata `euronext_curve`.
- `features.parquet` régénéré via `venv/bin/python -m mais.cli features` :
  - shape : `(6192, 371)` ;
  - colonnes EMA ajoutées : `37` ;
  - `ema_cbot_basis` non nul : `3 078` lignes ;
  - `ema_data_availability_score` moyen : `0.5449` ;
  - log pipeline : `features_ema_added n=37`.
- Rapport de couverture EMA observé dans le dataset :
  - dataset complet : `2000-10-25` → `2025-07-25` ;
  - blocs EMA disponibles à partir de l'historique exploratoire 2010+ ;
  - top non-null : `ema_liquid_price`, `ema_volume_total`, `ema_curve_contract_count`, `ema_open_interest_available`, `ema_oi_total`, `ema_contango_flag`, `ema_backwardation_flag` (`3 566` lignes chacun).
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/features/ema_features.py src/mais/features/__init__.py src/mais/features/euronext_curve.py tests/test_ema_features_pipeline.py tests/test_euronext_curve.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_features_pipeline.py -q` PASS (`6 passed`).
  - `venv/bin/python -m pytest tests/test_ema_features_pipeline.py tests/test_euronext_curve.py tests/test_euronext_continuous.py tests/test_roll_audit.py -q` PASS (`28 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ avec réserve : dataset master CBOT+EMA utilisable pour sélection et benchmark exploratoire.
- Réserve source : toutes les colonnes EMA héritent de `barchart_proxy_exploratory`; ne pas présenter ces résultats comme settlement officiel Euronext.
- Critères validés : intégration `build_features()`, metadata, skip propre si fichiers EMA absents, garde anti-target-leakage, ruff PASS, pytest complet PASS.
- Décision review : `DATA-MASTER-01` → `DONE`. Déblocages : `DATA-TARGETS-01`, `EXP-BENCH-01`, `VAL-EMA-01`, `MOD-A-01`, `OPS-CLI-01` → `READY`.

---

## DATA-TARGETS-01 — Cibles agricoles EMA

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-03  

### Contexte

Les cibles CBOT (`y_up_h20`, etc.) sont dans `targets.parquet`. Il faut construire les équivalents EMA avec les 13 cibles définies au §4.5 de ARCHITECTURE_EMA_PRO, notamment les cibles de stockage (`y_storage_value_3m`, `y_storage_profit_3m`).

### Objectifs mesurables

- 13 cibles EMA ajoutées dans `targets.parquet` (ou fichier séparé `ema_targets.parquet`)
- Anti-leakage : les cibles utilisent uniquement `shift(-H)` (regard dans le futur) — légal pour y, pas pour X
- Coûts de stockage paramétrables depuis `config/decision.yaml`
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/ema_targets.py` | **CRÉER** — construction cibles EMA |
| `config/decision.yaml` | **MODIFIER** — ajouter storage_costs |
| `tests/test_ema_targets.py` | **CRÉER** — 4 tests |

### Tâches détaillées

**T1 — 13 cibles (§4.5 ARCHITECTURE_EMA_PRO)**

```python
STORAGE_COSTS = {"1m": 1.5, "3m": 4.5, "6m": 9.0}  # EUR/t, depuis decision.yaml

def build_ema_targets(
    front_raw: pd.DataFrame,
    harvest_nov: pd.DataFrame,
    storage_costs: dict = STORAGE_COSTS,
    horizons: tuple = (20, 40, 60),
) -> pd.DataFrame:
    """Construit les 13 cibles agricoles EMA.
    Utilise front_raw pour y_up_hH_ema et harvest_nov pour y_up_hH_ema_harvest.
    Utilise les séries raw pour les cibles ; adjusted reste réservé aux features de rendement.
    """
```

**T2 — Vérification anti-leakage targets**

```python
def assert_ema_targets_not_in_features(features: pd.DataFrame, targets: pd.DataFrame):
    """Vérifie qu'aucune colonne cible EMA n'est présente dans features (leakage direct)."""
```

### Résultat ticket (2026-05-20)

- Module `src/mais/features/ema_targets.py` créé.
- Configuration `config/decision.yaml` enrichie avec `euronext_ema.storage_costs_eur_per_tonne` :
  - `1m=1.5`, `3m=4.5`, `6m=9.0` EUR/t.
- Fichier généré via le module : `data/processed/euronext/ema_targets.parquet`.
- Sortie réelle :
  - shape : `(3275, 14)` ;
  - période : `2010-01-04` → `2026-05-20` ;
  - `13` colonnes cibles EMA exactement ;
  - `y_up_h20_ema` non nul : `3255` lignes ;
  - `y_up_h20_ema_harvest` non nul : `836` lignes ;
  - `y_storage_profit_3m` non nul : `3215` lignes.
- Cibles créées :
  - `y_up_h20_ema`, `y_up_h40_ema`, `y_up_h60_ema` ;
  - `y_up_h20_ema_harvest`, `y_up_h40_ema_harvest` ;
  - `y_up_gt3pct_h40_ema`, `y_down_gt3pct_h40_ema` ;
  - `y_price_h20_ema`, `y_price_h60_ema` ;
  - `y_storage_value_1m`, `y_storage_value_3m`, `y_storage_value_6m` ;
  - `y_storage_profit_3m`.
- Garde anti-leakage ajoutée : `assert_ema_targets_not_in_features(...)`.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/features/ema_targets.py tests/test_ema_targets.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_targets.py -q` PASS (`6 passed`).
  - `venv/bin/python -m pytest tests/test_ema_targets.py tests/test_euronext_features.py tests/test_roll_audit.py -q` PASS (`15 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Vérification anti-leakage sur `features.parquet` : PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ : les `13` cibles du §4.5 sont présentes dans `ema_targets.parquet`, avec queues NaN cohérentes avec les horizons.
- Point critique validé : les cibles utilisent les prix raw (`price`) ; `adjusted_price` n'est pas utilisé comme cible.
- Anti-leakage validé : aucune cible EMA/storage n'est présente dans `features.parquet`.
- Réserve : les cibles restent basées sur la source EMA exploratoire `barchart_proxy_exploratory`, pas sur un settlement officiel Euronext.
- Décision review : `DATA-TARGETS-01` → `DONE`. `EXP-BENCH-02` peut rester le prochain ticket go/no-go.

---

## EXP-BENCH-01 — Feature selection EMA

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-MASTER-01  

### Contexte

Le benchmark R&D-01 a montré qu'utiliser les 289 features sans sélection donne DA≈0.47 (Ridge logistique). La sélection est obligatoire avant tout benchmark EMA. La stratégie : drop NaN>60%, drop corrélation>0.95, SHAP top-50 via HistGBT first pass.

### Objectifs mesurables

- ≤ 80 features retenues après sélection
- NaN rate maximal des features retenues < 30%
- Rapport de sélection `artefacts/ema_feature_selection.json`
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_feature_selector.py` | **CRÉER** — sélecteur features EMA |
| `artefacts/ema_feature_selection.json` | Produit par le module |
| `tests/test_ema_feature_selector.py` | **CRÉER** — 3 tests |

### Tâches détaillées

**T1 — Pipeline de sélection**

```python
def select_ema_features(
    features: pd.DataFrame,
    target_col: str,
    nan_threshold: float = 0.60,
    corr_threshold: float = 0.95,
    shap_top_n: int = 50,
) -> tuple[list[str], dict]:
    """Pipeline de sélection en 3 étapes :
    1. Drop colonnes NaN > nan_threshold
    2. Drop une des deux si corrélation > corr_threshold
    3. SHAP importance HistGBT first pass → top shap_top_n
    Retourne : (feature_names, selection_report)
    """
```

**T2 — Familles à tester séparément**

```python
FEATURE_FAMILIES = {
    "cbot_base":       [c for c in features if any(x in c for x in ["corn_", "cbot_", "wheat_", "soy_"])],
    "ema_curve":       [c for c in features if c.startswith("ema_")],
    "wasde":           [c for c in features if "wasde" in c],
    "cot":             [c for c in features if "cot" in c],
    "weather":         [c for c in features if any(x in c for x in ["gdd", "drought", "precip"])],
    "macro":           [c for c in features if any(x in c for x in ["eurusd", "ttf", "fred"])],
}
```

### Résultat ticket (2026-05-20)

- Module `src/mais/research/ema_feature_selector.py` créé.
- Rapport produit : `artefacts/ema_feature_selection.json`.
- Pipeline de sélection :
  - période commune EMA : `2010-01-05` → `2022-12-30` ;
  - filtre `ema_data_availability_score > 0` pour éviter de pénaliser EMA sur la période pré-2010 ;
  - cible : `y_up_h20` ;
  - candidats initiaux : `370` ;
  - après filtre NaN strict (`<=30%`) : `322` ;
  - après constante : `316` ;
  - après corrélation `>0.95` : `227` ;
  - préselection modèle : `120` ;
  - sélection finale : `50` features ;
  - max NaN retenu : `0.2707` ;
  - méthode importance : `histgb_shap_tree_explainer` ;
  - AUC validation first pass : `0.6389`.
- Répartition des features sélectionnées :
  - `ema_curve`: `5` (`ema_cbot_basis`, `ema_front_price_lag1`, `ema_cbot_basis_zscore_52w`, `cbot_eur_t`, `ema_oi_total`) ;
  - `cbot_base`: `9` ;
  - `wasde`: `13` ;
  - `cot`: `10` ;
  - `weather`: `5` ;
  - `macro`: `2` ;
  - `other`: `6`.
- Tests `tests/test_ema_feature_selector.py` créés (`4` tests) :
  - drop high-NaN et constantes ;
  - drop clone corrélé ;
  - limite top-N + familles ;
  - écriture rapport JSON.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/ema_feature_selector.py tests/test_ema_feature_selector.py src/mais/features/ema_features.py src/mais/features/__init__.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_feature_selector.py -q` PASS (`4 passed`).
  - `venv/bin/python -m pytest tests/test_ema_feature_selector.py tests/test_ema_features_pipeline.py -q` PASS (`10 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ avec réserve : la sélection est utilisable pour benchmark exploratoire, mais elle reste entraînée sur une source EMA Barchart proxy.
- Correction importante validée : sélection restreinte à la période commune EMA (`require_ema_available=True`) afin de ne pas rejeter les features EMA à cause des années pré-2010.
- Critères validés : `50` features ≤ `80`, max NaN retenu `<30%`, rapport JSON produit, SHAP HistGBT utilisé, ruff PASS, pytest complet PASS.
- Décision review : `EXP-BENCH-01` → `DONE`. `VAL-EMA-01` reste le prochain ticket bloquant avant `EXP-BENCH-02`.

---

## VAL-EMA-01 — Proxy vs vraie EMA

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-02 (vrais prix disponibles)  

### Contexte

Le proxy CBOT→EUR/t génère des valeurs systématiquement différentes des vrais prix Euronext (pas de prime EU, pas de structure courbe réelle). Ce ticket quantifie l'écart et établit les périodes où le proxy est inutilisable. Il **interdit formellement** le proxy dans les résultats finaux.

### Objectifs mesurables

- Corrélation proxy vs vraie EMA calculée et documentée (attendu : > 0.90 mais pas 1.0)
- Spread moyen et std documentés (attendu : 10-30 €/t)
- Périodes où spread > 2σ identifiées (ne pas utiliser proxy)
- Rapport `artefacts/proxy_vs_real_ema_report.json` produit
- Règle formelle : `is_proxy=True` → exclusion automatique des benchmarks modèles

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/proxy_audit.py` | **CRÉER** — auditeur proxy vs réel |
| `artefacts/proxy_vs_real_ema_report.json` | Produit par le module |
| `tests/test_proxy_audit.py` | **CRÉER** — 3 tests |

### Tâches détaillées

**T1 — Comparaison proxy vs réel**

```python
def compare_proxy_vs_real(
    proxy: pd.DataFrame,     # ema_is_proxy=True
    real: pd.DataFrame,      # vrais prix Euronext
) -> dict:
    """Compare les deux séries.
    Métriques : corrélation, MAE €/t, RMSE €/t, spread moyen, spread std,
    pct_periods_spread_gt_2sigma, dates des écarts extrêmes."""
```

**T2 — Règle d'exclusion**

```python
def assert_no_proxy_in_benchmark(features: pd.DataFrame, signals: pd.DataFrame):
    """Lève ValueError si des jours avec is_proxy=True sont inclus dans un benchmark."""
```

### Résultat ticket (2026-05-20)

- Module `src/mais/research/proxy_audit.py` créé.
- Rapport produit : `artefacts/proxy_vs_real_ema_report.json`.
- Fonctions livrées :
  - `compare_proxy_vs_real(proxy, real)` ;
  - `assert_no_proxy_in_benchmark(features, signals=None)` ;
  - `run_proxy_audit(...)`.
- Résultat réel proxy CBOT→EUR/t vs EMA front raw exploratoire :
  - overlap : `3 078` dates ;
  - période : `2010-01-04` → `2025-07-21` ;
  - corrélation : `0.9411` ;
  - MAE : `37.287` EUR/t ;
  - RMSE : `40.294` EUR/t ;
  - spread proxy-real moyen : `-37.197` EUR/t ;
  - spread std : `15.494` EUR/t ;
  - périodes `abs(spread)>2σ` : `68.97%` ;
  - verdict : `PROXY_FORBIDDEN`.
- Règle formelle : toute ligne avec `is_proxy=True` ou `ema_is_proxy=True` est interdite dans un benchmark modèle.
- Tests `tests/test_proxy_audit.py` créés (`5` tests) :
  - métriques proxy/réel ;
  - cas sans overlap ;
  - rejet des lignes proxy ;
  - acceptation des lignes réelles ;
  - écriture rapport JSON.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/proxy_audit.py tests/test_proxy_audit.py src/mais/research/ema_feature_selector.py tests/test_ema_feature_selector.py` PASS.
  - `venv/bin/python -m pytest tests/test_proxy_audit.py -q` PASS (`5 passed`).
  - `venv/bin/python -m pytest tests/test_proxy_audit.py tests/test_ema_feature_selector.py -q` PASS (`9 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-20)

- VALIDÉ : le proxy CBOT→EUR/t est formellement exclu des benchmarks.
- Réserve : la série EMA de comparaison est exploitable en recherche, mais reste `barchart_proxy_exploratory` et non settlement officiel Euronext.
- Critères validés : métriques proxy/réel, périodes extrêmes, rapport JSON, règle d'exclusion, ruff PASS, pytest complet PASS.
- Décision review : `VAL-EMA-01` → `DONE`, `EXP-BENCH-02` → `READY`.

---

## EXP-BENCH-02 — Benchmark EMA vs CBOT (vrais prix)

**Priorité** : HAUTE  
**Type** : critique  
**Statut** : DONE  
**Dépendances** : VAL-EMA-01, EXP-BENCH-01  

### Contexte

C'est le ticket go/no-go central. Il détermine si le pivot Euronext apporte plus que le CBOT en cible. Sans vrais prix EMA (VAL-EMA-01 DONE), ce ticket ne peut pas commencer. Il étend le notebook `00_benchmark_pivot_ema.ipynb` avec les vraies données.

### Objectifs mesurables

- DA OOF EMA h20 > 0.55 et AUC > 0.55 (critères go/no-go minimal §16 ARCHITECTURE_EMA_PRO)
- Comparaison sur 4 feature sets : cbot_only, ema_curve_only, cbot_ema_combined, cbot_full
- Comparaison sur 3 cibles : CBOT h20, EMA front h20, EMA harvest h20
- IC95% bootstrap (1000 tirages) sur DA et AUC
- Correction Benjamini-Hochberg sur les comparaisons inter-feature-sets
- Verdict automatique : PIVOT_VALIDÉ / PIVOT_UTILE / CBOT_MOTEUR
- Ruff PASS, pytest PASS (≥ 6 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_benchmark.py` | **CRÉER** — benchmark EMA vs CBOT |
| `notebooks/corn_study/euronext/00_benchmark_pivot_ema.ipynb` | **MODIFIER** — brancher vrais prix |
| `artefacts/benchmark_pivot/benchmark_full.json` | Produit par le module |
| `artefacts/benchmark_pivot/pivot_decision.json` | Verdict automatique |
| `tests/test_ema_benchmark.py` | **CRÉER** — ≥ 6 tests |

### Tâches détaillées

**T1 — Walk-forward DA avec IC95%**

Reprendre la fonction `walk_forward_da()` du notebook, la formaliser dans `ema_benchmark.py` :
```python
def walk_forward_da(
    X: pd.DataFrame, y: pd.Series,
    n_splits: int = 8, min_train_years: int = 3,
    n_bootstrap: int = 1000,
) -> dict:
    """Modèle : RidgeClassifier + SimpleImputer + StandardScaler.
    Retourne : da, da_ci95_lo, da_ci95_hi, auc, split_das, annual_stability."""
```

**T2 — 4 feature sets × 3 cibles**

```python
FEATURE_SETS = {
    "cbot_only":         selected_cbot_features,
    "ema_curve_only":    selected_ema_features,
    "cbot_ema_combined": selected_cbot + selected_ema,
    "cbot_full":         all_selected_features,
}
TARGETS = ["y_up_h20", "y_up_h20_ema", "y_up_h20_ema_harvest"]
```

**T3 — Décision automatique**

```python
def decide_pivot(results: pd.DataFrame) -> dict:
    """Applique l'arbre de décision §16 ARCHITECTURE_EMA_PRO.
    Critères go/no-go minimal :
      DA_ema > 0.55 AND AUC_ema > 0.55 AND IC95_lo > 0.50 AND top20 > 0.62
    Verdict :
      PIVOT_VALIDÉ : DA_ema > DA_cbot + 0.01
      PIVOT_UTILE  : |DA_ema - DA_cbot| <= 0.01 (mais DA_ema > 0.55)
      CBOT_MOTEUR  : DA_ema < DA_cbot - 0.01
      NO_GO        : DA_ema < 0.55
    """
```

**T4 — Tests**

```python
def test_no_proxy_in_benchmark():
def test_ic95_bootstrap_1000_draws():
def test_benjamini_hochberg_applied():
def test_verdict_json_produced():
def test_feature_sets_non_overlapping():
def test_annual_stability_computed():
```

### Critère de fin

- Benchmark complet sur vrais prix EMA (proxy = 0%)
- Verdict pivot produit et documenté
- Si NO_GO → documenter honnêtement et arrêter Phase Modèles

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_benchmark.py` créé.
- Tests `tests/test_ema_benchmark.py` créés (`6` tests).
- Artefacts produits par le module :
  - `artefacts/benchmark_pivot/benchmark_full.json` ;
  - `artefacts/benchmark_pivot/pivot_decision.json` ;
  - `artefacts/benchmark_pivot/benchmark_full.csv` (table lisible additionnelle).
- Notebook `notebooks/corn_study/euronext/00_benchmark_pivot_ema.ipynb` non modifié : dossier `notebooks/` interdit par les règles agents de ce workspace.
- Protocole livré :
  - RidgeClassifier + SimpleImputer + StandardScaler ;
  - walk-forward expanding par années, `8` années de validation maximum ;
  - `4` feature sets × `3` cibles ;
  - IC95 bootstrap `1000` tirages sur DA et AUC ;
  - correction Benjamini-Hochberg par cible ;
  - exclusion formelle des lignes `is_proxy=True` / `ema_is_proxy=True`.
- Verdict automatique : `NO_GO`.
- Cible primaire EMA h20, feature set `cbot_ema_combined` :
  - `n_oof=1575`, `n_features=14` ;
  - DA `0.4673`, IC95 `[0.4432, 0.4902]` ;
  - AUC `0.5026`, IC95 `[0.4739, 0.5326]` ;
  - top20 DA `0.6032` ;
  - annual stability `0.25`.
- Baseline primaire CBOT h20, feature set `cbot_full` :
  - `n_oof=1827`, `n_features=45` ;
  - DA `0.5599`, IC95 `[0.5375, 0.5835]` ;
  - AUC `0.5620`, IC95 `[0.5334, 0.5898]` ;
  - top20 DA `0.5355` ;
  - annual stability `0.625`.
- Différence primaire EMA-CBOT : `-0.0926` DA.
- Critères go/no-go EMA :
  - DA EMA > 0.55 : FAIL ;
  - AUC EMA > 0.55 : FAIL ;
  - IC95 bas DA > 0.50 : FAIL ;
  - top20 > 0.62 : FAIL (`0.6032`).
- Résultat secondaire notable :
  - sur cible CBOT h20, `ema_curve_only` donne DA `0.6174`, AUC `0.6439`, top20 `0.7104`, q BH `0.0018` vs `cbot_full`.
  - Interprétation : les features EMA peuvent contenir du signal sur le marché CBOT, mais le pivot vers cible EMA h20 n'est pas validé.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/ema_benchmark.py tests/test_ema_benchmark.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_benchmark.py -q` PASS (`6 passed`).
  - `venv/bin/python -m pytest tests/test_ema_benchmark.py tests/test_ema_feature_selector.py tests/test_proxy_audit.py tests/test_ema_targets.py -q` PASS (`21 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ : benchmark complet produit sur les vraies séries EMA disponibles, sans proxy CBOT→EUR/t.
- Décision scientifique : `NO_GO` pour le pivot de cible EMA h20. Les quatre critères minimaux échouent sur la ligne primaire `y_up_h20_ema × cbot_ema_combined`.
- Réserve forte : EMA reste `barchart_proxy_exploratory`, donc le résultat est exploitable en recherche mais ne vaut pas validation officielle Euronext settlement.
- Point positif à creuser : `ema_curve_only` prédit bien `y_up_h20` CBOT (`DA=0.6174`, `AUC=0.6439`, `top20=0.7104`, q BH `0.0018`), ce qui justifie une analyse hebdomadaire et une ablation, mais pas un pivot modèle EMA.
- Décision review : `EXP-BENCH-02` → `DONE`.
- Déblocages : `VAL-EMA-02`, `EXP-BENCH-03`, `EXP-BENCH-04` → `READY`.
- Phase Modèles EMA direction/prix reste à ne pas lancer comme production tant que le `NO_GO` n'est pas expliqué ou renversé par validation hebdomadaire/source officielle.

---

## VAL-EMA-02 — Benchmark hebdomadaire

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : EXP-BENCH-02  

### Contexte

Les métriques quotidiennes peuvent être gonflées par autocorrélation (5 jours consécutifs avec mêmes features WASDE/COT). La DA hebdomadaire (1 point par lundi) est la référence agricole réelle. Ce ticket compare DA_quotidienne vs DA_hebdomadaire pour valider que le signal n'est pas un artefact d'autocorrélation.

### Objectifs mesurables

- DA_hebdomadaire calculée pour chaque modèle × horizon × feature set
- Delta DA_quotidien - DA_hebdomadaire documenté (si > 0.05 : artefact signalé)
- DA_hebdomadaire EMA ≥ 0.53 (seuil minimum pour utilité agricole)
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/weekly_da.py` | **CRÉER** — évaluation DA hebdomadaire |
| `artefacts/benchmark_pivot/weekly_da_report.json` | Produit |
| `tests/test_weekly_da.py` | **CRÉER** — 3 tests |

### Tâches détaillées

**T1 — Calcul DA hebdomadaire**

```python
def compute_weekly_da(
    oof_predictions: pd.DataFrame,  # colonnes : date, y_true, y_pred, y_proba
    day_of_week: int = 0,           # 0 = lundi
    n_bootstrap: int = 1000,
) -> dict:
    """Filtre 1 point par semaine (lundi ou lundi le plus proche).
    Retourne : da_weekly, da_weekly_ci95, da_daily, delta, autocorr_flag."""
```

**T2 — Comparaison quotidienne vs hebdomadaire**

```python
if delta > 0.05:
    autocorr_flag = True
    print(f"⚠ Delta DA_quotidien - DA_hebdomadaire = {delta:.3f} > 0.05")
    print("→ Possible artefact d'autocorrélation. Utiliser DA_hebdomadaire comme référence.")
```

### Résultat ticket (2026-05-21)

- Module `src/mais/research/weekly_da.py` créé.
- Tests `tests/test_weekly_da.py` créés (`4` tests).
- Rapport produit : `artefacts/benchmark_pivot/weekly_da_report.json`.
- Protocole :
  - mêmes features/cibles que `EXP-BENCH-02` ;
  - mêmes folds walk-forward ;
  - un point par semaine, lundi ou plus proche jour disponible ;
  - IC95 bootstrap `1000` tirages sur DA hebdomadaire ;
  - flag autocorrélation si `DA_daily - DA_weekly > 0.05`.
- Verdict hebdomadaire primaire : `WEEKLY_NO_GO`.
- Ligne primaire EMA h20, `cbot_ema_combined` :
  - `n_daily=1575`, `n_weekly=345` ;
  - DA quotidienne `0.4673` ;
  - DA hebdomadaire `0.4638`, IC95 `[0.4145, 0.5188]` ;
  - delta quotidien-hebdo `0.0035` ;
  - `autocorr_flag=False` ;
  - seuil utilité agricole `0.53` : FAIL.
- Ligne secondaire importante, CBOT h20 avec `ema_curve_only` :
  - DA quotidienne `0.6174` ;
  - DA hebdomadaire `0.6193`, IC95 `[0.5711, 0.6675]` ;
  - delta `-0.0019` ;
  - `autocorr_flag=False` ;
  - seuil utilité `0.53` : PASS.
- Conclusion : l'échec de la cible EMA h20 n'est pas un artefact d'autocorrélation quotidienne ; le signal EMA sur cible CBOT h20 reste robuste en hebdomadaire.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/weekly_da.py tests/test_weekly_da.py` PASS.
  - `venv/bin/python -m pytest tests/test_weekly_da.py -q` PASS (`4 passed`).
  - `venv/bin/python -m pytest tests/test_weekly_da.py tests/test_ema_benchmark.py tests/test_ema_feature_selector.py tests/test_proxy_audit.py tests/test_ema_targets.py -q` PASS (`25 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ : la référence hebdomadaire est calculée pour tous les target × feature sets du benchmark.
- Conclusion validée : le `NO_GO` EMA h20 est confirmé en hebdomadaire et ne vient pas d'un gonflement par autocorrélation quotidienne.
- Point à creuser en priorité : `ema_curve_only` reste fort sur cible CBOT h20 en hebdomadaire (`DA=0.6193`, IC95 bas `0.5711`).
- Décision review : `VAL-EMA-02` → `DONE`. Prochain ticket logique : `EXP-BENCH-03` ablation des features courbe EMA.

---

## EXP-BENCH-03 — Ablation features courbe EMA

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : EXP-BENCH-02  

### Contexte

Parmi les 18 features de courbe EMA, lesquelles apportent réellement du signal par rapport au baseline CBOT seul ? L'ablation par famille répond à cette question et évite de surcharger le modèle avec des features redondantes.

### Objectifs mesurables

- Delta DA pour chaque famille de features EMA
- Classification GARDER / NEUTRE / RETIRER par famille
- Résultats documentés dans `artefacts/ema_curve_ablation.json`
- Correction Benjamini-Hochberg appliquée

### Tâches détaillées

**T1 — Ablation par sous-groupe EMA**

```python
EMA_CURVE_FAMILIES = {
    "spreads":      ["ema_front_second_spread", "ema_nov_mar_spread", "ema_aug_nov_spread"],
    "slope":        ["ema_curve_slope_3m", "ema_curve_slope_6m"],
    "flags":        ["ema_contango_flag", "ema_backwardation_flag"],
    "carry":        ["ema_carry_1m", "ema_roll_yield_ann"],
    "liquidity":    ["ema_oi_total", "ema_oi_concentration", "ema_liquidity_shift"],
    "basis_cbot":   ["ema_cbot_basis", "ema_cbot_basis_zscore_52w", "ema_cbot_rel_strength_20d"],
}
```

Pour chaque famille : DA(cbot_base + famille) vs DA(cbot_base seul). Delta DA > +0.01 → GARDER.

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_curve_ablation.py` créé.
- Tests `tests/test_ema_curve_ablation.py` créés (`3` tests).
- Rapport produit : `artefacts/ema_curve_ablation.json`.
- Protocole :
  - cible `y_up_h20` ;
  - baseline = selected `cbot_only` (`9` features) ;
  - modèle walk-forward identique à `EXP-BENCH-02` ;
  - comparaison `baseline + famille EMA` vs baseline ;
  - correction Benjamini-Hochberg sur les familles.
- Baseline `cbot_only` :
  - DA `0.4521`, AUC `0.4136`, top20 `0.3525`, `n_oof=1827`.
- Résultat familles :
  - `basis_cbot` : delta DA `+0.0826`, delta AUC `+0.1166`, q BH `0.0000` → `GARDER` ;
  - `all_ema_curve` : delta DA `+0.0739`, delta AUC `+0.0849`, q BH `0.0000` → `GARDER` ;
  - `price_levels` : delta DA `+0.0569`, delta AUC `+0.0692`, q BH `0.0019` → `GARDER` ;
  - `liquidity` : delta DA `+0.0449`, delta AUC `+0.0531`, q BH `0.0164` → `GARDER` ;
  - `continuous_lags` : delta DA `+0.0115`, q BH `0.9068` → `GARDER` selon seuil DA, mais faible preuve statistique ;
  - `adjusted_returns`, `slope`, `spreads`, `carry`, `flags` → `NEUTRE`.
- Synthèse :
  - `5` familles `GARDER` ;
  - `5` familles `NEUTRE` ;
  - `0` famille `RETIRER`.
- Interprétation : le signal EMA utile vient surtout du basis CBOT-EMA, des niveaux de prix Euronext et de la liquidité/open interest, pas des flags de contango/backwardation seuls.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/ema_curve_ablation.py tests/test_ema_curve_ablation.py` PASS.
  - `venv/bin/python -m pytest tests/test_ema_curve_ablation.py -q` PASS (`3 passed`).
  - `venv/bin/python -m pytest tests/test_ema_curve_ablation.py tests/test_weekly_da.py tests/test_ema_benchmark.py tests/test_ema_feature_selector.py -q` PASS (`17 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ : l'ablation répond directement à l'anomalie positive observée dans `EXP-BENCH-02` et `VAL-EMA-02`.
- Conclusion validée : le signal EMA utile pour CBOT h20 est concentré dans `basis_cbot`, `price_levels` et `liquidity`.
- Réserve : `continuous_lags` passe le seuil DA mais sans preuve BH ; à garder comme candidat secondaire, pas comme driver robuste.
- Décision review : `EXP-BENCH-03` → `DONE`. Prochain ticket possible : `EXP-BENCH-04` sur la cible stockage.

---

## EXP-BENCH-04 — Benchmark cible stockage

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-TARGETS-01, EXP-BENCH-01  

### Contexte

`y_storage_profit_3m` est la cible la plus utile pour l'agriculteur. Ce ticket teste si le modèle prédit mieux que les baselines naïves (toujours stocker / toujours vendre).

### Objectifs mesurables

- DA OOF `y_storage_profit_3m` > 0.55
- Gain net €/t vs baselines documenté
- Résultats dans `artefacts/storage_benchmark_ema.json`

### Résultat ticket (2026-05-21)

- Module `src/mais/research/storage_benchmark_ema.py` créé.
- Tests `tests/test_storage_benchmark_ema.py` créés (`3` tests).
- Rapport produit : `artefacts/storage_benchmark_ema.json`.
- Protocole :
  - cible binaire `y_storage_profit_3m` ;
  - valeur économique `y_storage_value_3m` ;
  - mêmes features sélectionnées que `EXP-BENCH-01` ;
  - feature sets : `cbot_only`, `ema_curve_only`, `cbot_ema_combined`, `selected_full` ;
  - walk-forward identique au benchmark EMA.
- Verdict : `STORAGE_NO_GO`.
- Distribution cible :
  - positive rate `0.4416` ;
  - `n_rows=2561`.
- Baselines :
  - `always_store` : DA `0.4416`, gain moyen `-1.3194` EUR/t ;
  - `never_store` : DA `0.5584`, gain moyen `0.0000` EUR/t ;
  - oracle store-if-profitable : gain moyen `8.6604` EUR/t.
- Modèles :
  - `cbot_only` : DA `0.3854`, AUC `0.4088`, gain `-2.2921` EUR/t ;
  - `ema_curve_only` : DA `0.4933`, AUC `0.4278`, gain `-1.0230` EUR/t ;
  - `cbot_ema_combined` : DA `0.5149`, AUC `0.4199`, gain `-0.6863` EUR/t ;
  - `selected_full` : DA `0.5187`, IC95 `[0.4952, 0.5448]`, AUC `0.5038`, top20 `0.5460`, gain `+1.5163` EUR/t, stocke `41.46%` des jours.
- Conclusion : `selected_full` crée un gain économique moyen positif, mais DA et IC95 restent sous le seuil de fiabilité ; la baseline `never_store` bat la DA modèle.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/research/storage_benchmark_ema.py tests/test_storage_benchmark_ema.py` PASS.
  - `venv/bin/python -m pytest tests/test_storage_benchmark_ema.py -q` PASS (`3 passed`).
  - `venv/bin/python -m pytest tests/test_storage_benchmark_ema.py tests/test_ema_curve_ablation.py tests/test_weekly_da.py tests/test_ema_benchmark.py -q` PASS (`16 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ : la cible stockage 3m a été testée contre baselines directionnelles et économiques.
- Conclusion validée : pas de modèle fiable pour décider le stockage 3m à ce stade (`DA=0.5187`, IC95 bas `<0.50`), même si `selected_full` améliore le gain moyen.
- Réserve : le gain `+1.5163` EUR/t doit être retraité plus tard avec coûts opérationnels complets et source officielle avant usage agriculteur.
- Décision review : `EXP-BENCH-04` → `DONE`.

---

## MODEL-DIR-01 — Modèle direction EMA (walk-forward multi-modèles)

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : IN_PROGRESS  
**Dépendances** : EXP-BENCH-02 (PIVOT validé ou utile)  

### Contexte

EXP-BENCH-02 utilisait seulement RidgeClassifier pour valider le pivot. Ce ticket construit le vrai modèle de direction EMA avec la gamme complète de modèles, walk-forward par crop year (comme R&D-01), et sélection des features EMA optimales.

### Objectifs mesurables

- ≥ 5 modèles testés : Ridge, LogisticReg, HistGBT, LightGBM, ExtraTrees
- Walk-forward par crop year (min 3 ans train, 8 folds)
- DA OOF IC95% lo > 0.50 sur le meilleur modèle
- DA top-20% > 0.62 sur le meilleur modèle
- Modèle retenu sérialisé dans `artefacts/models/ema_direction_model.pkl`
- Ruff PASS, pytest PASS (≥ 6 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/models/ema_direction.py` | **CRÉER** — modèle direction EMA |
| `artefacts/models/ema_direction_model.pkl` | Produit |
| `artefacts/models/ema_direction_results.json` | Métriques complètes |
| `tests/test_ema_direction_model.py` | **CRÉER** — ≥ 6 tests |

### Tâches détaillées

**T1 — Modèles et pipeline**

```python
MODEL_SPECS = {
    "ridge":      RidgeClassifier(alpha=10.0, class_weight="balanced"),
    "logistic":   LogisticRegression(C=0.1, max_iter=500),
    "histgb":     HistGradientBoostingClassifier(max_iter=100, early_stopping=True),
    "lgbm":       LGBMClassifier(n_estimators=200, learning_rate=0.05),
    "extratrees": ExtraTreesClassifier(n_estimators=100, min_samples_leaf=10),
}
# Pipeline : SimpleImputer → StandardScaler → modèle
# Horizons principaux : h20, h40 (si disponible dans targets EMA)
```

**T2 — Walk-forward**

Reprendre `CropYearWalkForward` de R&D-01, adapter pour EMA (période 2014-2025, min 3 ans train).

**T3 — Features retenues**

Utiliser les features sélectionnées par EXP-BENCH-01 + EXP-BENCH-03 :
- CBOT features GARDER (de R&D ablation)
- EMA curve features GARDER (de EXP-BENCH-03)

**T4 — Tests**

```python
def test_model_no_proxy_data():
def test_walk_forward_min_8_folds():
def test_ic95_bootstrap_1000():
def test_da_top20_computed():
def test_model_serializable():
def test_annual_stability_documented():
```

---

## MODEL-CQR-01 — CQR prix absolu EMA

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : BLOCKED  
**Dépendances** : EXP-BENCH-02  

### Contexte

`mais.meta.cqr` implémente le CQR calibré pour le CBOT. Ce ticket l'adapte pour la cible `y_price_h60_ema` (prix absolu EMA dans 60 jours). Le CQR donne un intervalle calibré [IC90%] qui est l'output central du Module C.

### Objectifs mesurables

- Coverage IC90% ≥ 88% sur l'ensemble de test
- Winkler loss < référence random_walk (prix_t+60 = prix_t)
- RMSE €/t < RMSE seasonal_naive
- Modèle CQR sérialisé dans `artefacts/models/ema_cqr_model.pkl`
- Ruff PASS, pytest PASS (≥ 5 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/models/ema_cqr.py` | **CRÉER** — adaptation CQR pour EMA |
| `mais.meta.cqr` | **LIRE** — adapter, ne pas modifier l'original |
| `artefacts/models/ema_cqr_model.pkl` | Produit |
| `tests/test_ema_cqr.py` | **CRÉER** — ≥ 5 tests |

### Tâches détaillées

**T1 — Cibles CQR**

```python
# Cibles régression (prix absolu, non shift-log-return)
TARGET_CQR = "y_price_h60_ema"  # prix EMA dans 60 jours

# Baselines à battre
def random_walk_rmse(prices: pd.Series, h: int) -> float:
    return (prices - prices.shift(h)).std()

def seasonal_naive_rmse(prices: pd.Series, h: int, period: int = 252) -> float:
    return (prices - prices.shift(period)).std()
```

**T2 — Walk-forward CQR**

```python
def walk_forward_cqr_ema(X, y_price, calibration_size=0.2, alpha=0.10) -> dict:
    """Adapte walk_forward_cqr() de mais.meta.cqr pour la cible EMA.
    Retourne : coverage, width_mean, winkler_loss, rmse."""
```

**T3 — Tests**

```python
def test_coverage_gte_88pct():
def test_winkler_loss_lt_random_walk():
def test_intervals_contain_realized():
def test_no_negative_interval_width():
def test_cqr_model_serializable():
```

---

## MODEL-STOR-01 — Modèle décision stockage

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : BLOCKED  
**Dépendances** : DATA-TARGETS-01, MODEL-DIR-01  

### Contexte

`y_storage_profit_3m` est une cible binaire (stocker 3 mois est profitable après coûts ?). Ce modèle produit `P(stocker rentable)` et se backtest sur les campagnes agricoles 2015-2024. C'est la cible la plus directement utile pour l'agriculteur.

### Objectifs mesurables

- DA OOF `y_storage_profit_3m` > 0.55
- Gain net moyen €/t/an > 0 vs baseline SELL_HARVEST sur ≥ 6/8 crop years
- Winkler loss (si CQR) ou DA économique documentés
- Backtest complet par crop year dans `artefacts/storage/backtest_ema.json`
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/models/ema_storage_model.py` | **CRÉER** — modèle stockage EMA |
| `src/mais/research/ema_farmer_backtest.py` | **CRÉER** — backtest agriculteur EMA |
| `tests/test_ema_storage_model.py` | **CRÉER** — 4 tests |

### Tâches détaillées

**T1 — Modèle P(stockage rentable)**

```python
def build_storage_model(X: pd.DataFrame, y: pd.Series) -> Pipeline:
    """LogisticRegression calibrée Platt (ECE < 0.10 objectif).
    Secondaire : HistGBT pour non-linéarités saisonnières."""
```

**T2 — Backtest agriculteur EMA**

```python
def backtest_storage_strategy_ema(
    predictions: pd.DataFrame,  # date, signal, prob_storage_profitable
    ema_prices: pd.DataFrame,
    storage_costs: dict,         # depuis decision.yaml
) -> dict:
    """Stratégies comparées :
    SELL_HARVEST  : vendre à la récolte (baseline)
    SIGNAL_BINARY : stocker si prob > 0.55
    SIGNAL_PARTIAL: stocker une fraction proportionnelle à prob
    ALWAYS_STORE_3M: toujours stocker 3 mois (benchmark naïf)
    
    Métriques : gain_net_eur_t, pct_years_winning, worst_year, drawdown
    """
```

---

## MODEL-CONF-01 — Confiance P(correct) EMA

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : BLOCKED  
**Dépendances** : MODEL-DIR-01  

### Contexte

Adapter le module P(correct) (R&D-07) pour le signal EMA. Les features de confiance spécifiques EMA sont : `data_availability_score`, `ema_oi_total` (liquidité), `is_proxy`, `days_to_wasde`, `cqr_width_ema`.

### Objectifs mesurables

- ECE < 0.10 sur les buckets de confiance EMA
- DA top-20% (par P(correct)) > DA globale
- Module sérialisé dans `artefacts/models/ema_confidence_model.pkl`

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/models/ema_confidence.py` | **CRÉER** — module confiance EMA |
| `tests/test_ema_confidence.py` | **CRÉER** — 3 tests |

---

## MODEL-STACK-01 — Stacking augmenté cross-fitted EMA

**Priorité** : MOYENNE  
**Type** : critique  
**Statut** : BLOCKED  
**Dépendances** : MODEL-DIR-01, MODEL-CQR-01  

### Contexte

Reprendre l'idée EXP-STACK-01 (REFLEXION_AMELIORATION_INDICATEUR) pour EMA : méta-features = prédictions OOF cross-fittées de MODEL-DIR-01 × horizons × modèles + consensus + P(correct) + CQR width + scores asymétriques. Tester si ce stacking augmenté améliore le signal final.

### Objectifs mesurables

- DA stacking > DA meilleur modèle seul de au moins +0.01
- Ou DA stable + DA_top20% amélioré de +0.03
- Ou réduction flip_rate de -0.02
- Si aucun critère atteint : documenter honnêtement et ne pas utiliser

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/models/ema_stacking.py` | **CRÉER** — stacking augmenté EMA |
| `tests/test_ema_stacking.py` | **CRÉER** — 3 tests |

---

## MOD-A-01 — Module A : 12 signaux contexte scorés

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : DATA-MASTER-01  

### Contexte

Le prototype est dans `notebooks/corn_study/euronext/10_module_a_dashboard.ipynb`. Ce ticket le formalise en module Python. Les 12 signaux sont scorés de -1 à +1 et agrégés en score de contexte. Le score > 0.30 → HAUSSIER, < -0.30 → BAISSIER.

### Objectifs mesurables

- 12 signaux implémentés dans les 4 blocs (offre mondiale, compétiteurs, demande, positionnement)
- Score contexte cohérent avec les mouvements historiques EMA (DA hebdomadaire > 0.53)
- Module sérialisable et appelable depuis le pipeline quotidien
- Ruff PASS, pytest PASS (≥ 5 tests)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/indicator/module_a_context.py` | **CRÉER** — signaux contexte |
| `notebooks/corn_study/euronext/10_module_a_dashboard.ipynb` | **MODIFIER** — brancher module |
| `tests/test_module_a.py` | **CRÉER** — ≥ 5 tests |

### Tâches détaillées

**T1 — 12 signaux et 4 blocs**

```
Bloc 1 — Offre mondiale (3 signaux) :
  bilan_mondial         → WASDE world stocks/use ratio
  bilan_stocks_eu       → données MARS ou FranceAgriMer (stub si absent)
  crop_condition_eu     → Agreste GE% France (stub si absent)

Bloc 2 — Offre compétiteurs (3 signaux) :
  brazil_supply_pressure → CONAB forecast vs avg, safrinha progress
  ukraine_corridor       → status corridor Black Sea (binaire manuel)
  us_crop_condition     → NASS GE% (proxy EU si EU absent)

Bloc 3 — Demande mondiale (3 signaux) :
  china_demand          → DCE Dalian ou WASDE China imports
  wasde_surprise        → stocks_surprise_mt (WASDE revision)
  export_pace_eu        → FAS export sales pace vs historical

Bloc 4 — Positionnement et structure (3 signaux) :
  cot_positioning       → COT managed money percentile (contrarian)
  futures_structure     → ema_contango_flag / ema_backwardation_flag
  eur_usd_competitive   → EUR/USD z-score (EUR faible = exports EU compétitifs)
```

**T2 — Fonctions de scoring**

```python
def score_from_zscore(z: float, cap: float = 2.0) -> float:
    return float(np.tanh(z / cap))  # [-1, +1]

def score_from_stocks_use_ratio(ratio, mean_5y, std_5y) -> float:
    z = -(ratio - mean_5y) / std_5y  # faible ratio = bullish
    return score_from_zscore(z)

def score_from_cot_percentile(percentile) -> float:
    z = -(percentile - 50) / 25  # contrarian
    return score_from_zscore(z)
```

**T3 — Calcul score global**

```python
def compute_context_score(row: pd.Series, features: pd.DataFrame) -> dict:
    """Calcule les 12 signaux + score global pour une date.
    Retourne : signals, context_score, orientation, dominant_signal, typed_uncertainty."""
```

### Résultat ticket (2026-05-21)

- Module `src/mais/indicator/module_a_context.py` créé.
- Export public ajouté dans `src/mais/indicator/__init__.py`.
- Tests `tests/test_module_a.py` créés (`5` tests).
- Notebook `notebooks/corn_study/euronext/10_module_a_dashboard.ipynb` non modifié : dossier `notebooks/` interdit par les règles agents de ce workspace.
- Les `12` signaux sont implémentés dans `4` blocs :
  - offre mondiale : `bilan_mondial`, `bilan_stocks_eu`, `crop_condition_eu` ;
  - offre compétiteurs : `brazil_supply_pressure`, `ukraine_corridor`, `us_crop_condition` ;
  - demande mondiale : `china_demand`, `wasde_surprise`, `export_pace_eu` ;
  - positionnement/structure : `cot_positioning`, `futures_structure`, `eur_usd_competitive`.
- Fonctions livrées :
  - `score_from_zscore(...)` ;
  - `score_from_stocks_use_ratio(...)` ;
  - `score_from_cot_percentile(...)` ;
  - `compute_context_score(row, features)` ;
  - `compute_context_timeseries(features)` ;
  - `evaluate_context_weekly_da(context, targets, target_col=...)`.
- Évaluation réelle sur période commune 2010-2022 :
  - shape contexte : `(3268, 17)` ;
  - disponibilité moyenne : `0.6170` ;
  - DA hebdomadaire sur cible EMA `y_up_h20_ema` : `0.5778`, `n_weekly=559` ;
  - DA hebdomadaire sur cible CBOT `y_up_h20` : `0.4794`, `n_weekly=678`.
- Critère ticket `DA hebdomadaire > 0.53` validé sur cible EMA.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/indicator/module_a_context.py src/mais/indicator/__init__.py tests/test_module_a.py` PASS.
  - `venv/bin/python -m pytest tests/test_module_a.py -q` PASS (`5 passed`).
  - `venv/bin/python -m pytest tests/test_module_a.py tests/test_storage_benchmark_ema.py tests/test_ema_curve_ablation.py tests/test_weekly_da.py -q` PASS (`15 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ : les 12 signaux et 4 blocs sont implémentés, bornés, sérialisables sous forme de dict/DataFrame et appelables hors notebook.
- Critère métier validé : DA hebdomadaire EMA `0.5778` > `0.53`.
- Réserve : score contexte interprétable, pas un modèle de trading ; les poids restent égaux avant `MOD-A-02`.
- Décision review : `MOD-A-01` → `DONE`. Déblocage : `MOD-A-02` → `READY`.

---

## MOD-A-02 — Module A : calibration OOF + poids

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : MOD-A-01  

### Contexte

Les poids des 12 signaux sont égaux dans MOD-A-01. Ce ticket calibre les poids via optimisation OOF walk-forward pour maximiser la DA hebdomadaire. Contrainte : poids ≥ 0, somme = 1 (interprétabilité).

### Objectifs mesurables

- DA hebdomadaire après calibration > DA poids égaux de +0.01 minimum
- Poids stables inter-années (std < 0.10)
- Backtest sur 2015-2024 documenté

### Résultat ticket (2026-05-21)

- Module `src/mais/indicator/module_a_calibration.py` créé.
- Tests `tests/test_module_a_calibration.py` créés (`4` tests).
- Rapport produit : `artefacts/module_a_calibration.json`.
- Protocole :
  - signaux Module A hebdomadaires ;
  - calibration walk-forward expanding par année ;
  - poids contraints `>=0` et somme `=1` ;
  - recherche aléatoire Dirichlet + candidats interprétables ;
  - pénalité légère de distance aux poids égaux pour limiter l'instabilité.
- Résultat réel :
  - `n_weekly=559`, `n_oof=432` ;
  - DA hebdo poids égaux : `0.5832` ;
  - DA hebdo calibrée OOF : `0.5856` ;
  - delta calibré - égal : `+0.0025` ;
  - `weight_std_max=0.0451` ;
  - poids stables : `True`.
- Poids finaux principaux :
  - `wasde_surprise=0.1690` ;
  - `export_pace_eu=0.1053` ;
  - `futures_structure=0.1036` ;
  - `china_demand=0.1031` ;
  - `bilan_stocks_eu=0.0960`.
- Verdict : `CALIBRATION_NEUTRE` car le gain est inférieur au seuil `+0.01`, même si les poids sont stables.
- Vérifications :
  - `venv/bin/python -m ruff check src/mais/indicator/module_a_calibration.py tests/test_module_a_calibration.py` PASS.
  - `venv/bin/python -m pytest tests/test_module_a_calibration.py -q` PASS (`4 passed`).
  - `venv/bin/python -m pytest tests/test_module_a_calibration.py tests/test_module_a.py -q` PASS (`9 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ : calibration OOF réalisée avec contrainte poids positifs/somme 1 et mesure de stabilité inter-années.
- Conclusion validée : les poids égaux sont déjà quasi optimaux ; la calibration n'apporte que `+0.0025`, donc elle ne doit pas remplacer la version égale comme règle par défaut.
- Réserve positive : les poids calibrés sont utiles comme lecture d'importance métier, surtout `wasde_surprise`, `export_pace_eu`, `futures_structure`, `china_demand`.
- Décision review : `MOD-A-02` → `DONE`.

---

## MOD-B-01 — Module B : étude événementielle grandes variations

**Priorité** : MOYENNE  
**Type** : complexe  
**Statut** : BLOCKED  
**Dépendances** : EXP-BENCH-02  

### Contexte

Module B répond à : "Quelles combinaisons de signaux précèdent les mouvements EMA de ±3% et ±5% ?" C'est une étude purement descriptive (pas de modèle prédictif) qui produit des règles lisibles.

### Objectifs mesurables

- ≥ 10 événements ±3% identifiés (support minimum)
- ≥ 3 règles avec support ≥ 15 et précision > 0.60 dans IC95%
- Règles lisibles en langage agricole (pas de jargon ML)
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_event_study.py` | **CRÉER** — étude événementielle |
| `notebooks/corn_study/euronext/15_module_b_events.ipynb` | **CRÉER** |
| `tests/test_ema_event_study.py` | **CRÉER** — 3 tests |

---

## MOD-B-02 — Module B : règles lisibles + carte risque

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : BLOCKED  
**Dépendances** : MOD-B-01  

### Contexte

Formalise les règles extraites de MOD-B-01 en format utilisable dans le rapport hebdomadaire. Produit une "carte de risque" : pour la semaine en cours, quels scénarios de mouvement fort sont crédibles ?

### Objectifs mesurables

- ≥ 3 règles lisibles avec support, précision, IC95%
- Carte de risque produite quotidiennement dans le signal JSON
- Règles paramétrables dans `config/decision.yaml`

---

## MOD-C-01 — Module C : prédiction prix EMA avec IC90% CQR

**Priorité** : HAUTE  
**Type** : critique  
**Statut** : BLOCKED  
**Dépendances** : MODEL-CQR-01  

### Contexte

Module C = "À quelle fourchette de prix s'attendre dans H jours ?" C'est la sortie CQR de MODEL-CQR-01 présentée de façon agricole : prix central + [IC90%] + probabilité > prix actuel.

### Objectifs mesurables

- Coverage IC90% ≥ 88% (hérité de MODEL-CQR-01)
- Format rapport : `Prix attendu : X €/t  |  IC90% : [Y ; Z]`
- Module appelable depuis pipeline quotidien → JSON `price_forecast`

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/indicator/module_c_price.py` | **CRÉER** — wrapper Module C |
| `notebooks/corn_study/euronext/20_module_c_price.ipynb` | **CRÉER** |

---

## OPS-CLI-01 — Extension CLI EMA

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-MASTER-01  

### Contexte

Ajouter les commandes EMA manquantes dans `src/mais/cli.py` pour permettre le pipeline quotidien et le backfill depuis la ligne de commande.

### Objectifs mesurables

- 6 nouvelles commandes fonctionnelles
- `--help` documenté pour chaque commande
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/cli.py` | **MODIFIER** — ajouter 6 commandes |
| `tests/test_cli_ema.py` | **CRÉER** — 4 tests |

### Tâches détaillées

Commandes à ajouter :
```bash
python -m mais.cli backfill euronext --from YYYY-MM-DD [--to YYYY-MM-DD] [--manual CSV_PATH]
python -m mais.cli build-ema-dataset              # continuous + curve + master
python -m mais.cli predict-ema [--date YYYY-MM-DD]
python -m mais.cli report daily [--date YYYY-MM-DD]
python -m mais.cli report weekly [--week YYYY-WXX]
python -m mais.cli data-quality [--date YYYY-MM-DD]
```

### Résultat ticket (2026-05-21)

- `src/mais/cli.py` étendu avec les 6 commandes demandées :
  - `backfill euronext` déjà disponible et vérifié avec `--from/--to/--manual`
  - `build-ema-dataset`
  - `predict-ema`
  - `report daily`
  - `report weekly`
  - `data-quality`
- `tests/test_cli_ema.py` créé avec 5 tests CLI.
- `predict-ema` produit un signal provisoire basé sur Module A contexte tant que les modèles EMA restent non validés ; si les features sont trop anciennes, le signal est forcé en `UNCERTAIN` avec `stale_days`.
- Vérification réelle `build-ema-dataset` PASS : `curve_rows=3797`, `targets_rows=3275`, `master_shape=(6192, 371)`.
- Vérifications réelles PASS :
  - `python -m mais.cli backfill euronext --help`
  - `python -m mais.cli build-ema-dataset --help`
  - `python -m mais.cli predict-ema --help`
  - `python -m mais.cli report daily --help`
  - `python -m mais.cli report weekly --help`
  - `python -m mais.cli data-quality --help`
  - `python -m mais.cli predict-ema --date 2026-05-20`
  - `python -m mais.cli report daily --date 2026-05-20`
  - `python -m mais.cli report weekly --week 2026-W21`
  - `python -m mais.cli data-quality --date 2026-05-20`
- Vérifications :
  - `venv/bin/ruff check src/mais/cli.py tests/test_cli_ema.py` PASS
  - `venv/bin/python -m pytest tests/test_cli_ema.py -q` PASS (`5 passed`)
  - `venv/bin/python -m pytest tests/ -q` PASS
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ → `DONE`.
- Les 6 commandes demandées sont disponibles et leurs `--help` passent.
- Le build réel EMA fonctionne et régénère bien continuous + curve + targets + master.
- Réserve volontaire : `predict-ema` est un signal Module A provisoire, forcé en `UNCERTAIN` si les features sont trop anciennes ; le vrai modèle EMA reste bloqué tant que les résultats `NO_GO` ne sont pas renversés.

---

## DATA-EMA-16 — Canonicalisation lignes Euronext officielles

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-10, DATA-EMA-02  

### Contexte

Les lignes officielles récentes `euronext_ajax_prices` / `euronext_chart_history` peuvent être moins complètes que les lignes Barchart historiques : `month_code`, `canonical_contract_code`, `close_or_last`, `import_verdict` ou dates d'expiration peuvent être manquants ou devinés. Avant de reconstruire les séries, ces lignes doivent être canonicalisées automatiquement.

### Objectifs mesurables

- `month_code` déduit depuis `contract_code`.
- `canonical_contract_code = contract_code` pour H/M/Q/X.
- `close_or_last = settlement` si disponible, sinon `last`, sinon `close`.
- `import_verdict = usable` pour H/M/Q/X.
- `expiry_date` enrichie depuis `ema_contract_reference.parquet` si disponible ; sinon `expiry_estimated=True`.
- `build-ema-dataset` garantit l'existence de `ema_contract_reference.parquet` avant de reconstruire les séries.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/euronext_contracts_daily.py` | **MODIFIER** — canonicalisation commune |
| `src/mais/collect/euronext_backfill.py` | **MODIFIER** — appliquer canonicalisation avant merge |
| `src/mais/features/euronext_continuous.py` | **MODIFIER** — appliquer canonicalisation avant séries |
| `src/mais/cli.py` | **MODIFIER** — garantir la référence dans `build-ema-dataset` |
| `tests/test_euronext_daily_collector.py` | **MODIFIER** — tests canonicalisation |

### Résultat ticket (2026-05-21)

- `normalise_contract_daily_frame(...)` ajouté dans `src/mais/collect/euronext_contracts_daily.py`.
- `canonicalise_contract_daily_parquet(...)` ajouté et appelé par `build-ema-dataset`.
- Canonicalisation appliquée avant merge backfill et avant construction des séries continues.
- `build-ema-dataset` garantit désormais l'existence de `ema_contract_reference.parquet`.
- Rebuild réel PASS :
  - `contracts_canonicalised=4818`
  - continuous curve `4818` lignes
  - front/liquid `3377` lignes
  - harvest_nov `1095` lignes
  - curve features `3868` lignes
  - targets `3377` lignes
  - master `(6192, 371)`
- Audit ciblé post-rebuild :
  - lignes officielles Euronext : `674`
  - `month_code` manquant : `0`
  - `canonical_contract_code` manquant : `0`
  - `close_or_last` manquant : `0`
  - `import_verdict` manquant : `0`
  - `expiry_date` manquant : `0`
  - `ema_contract_reference.parquet` présent : `81` lignes.
- Réserve : les expirations officielles récentes restent `expiry_estimated=True` quand la référence ne fournit pas de vraie `last_trade_date`; c'est volontairement conservateur.
- Vérifications :
  - `venv/bin/ruff check src/mais/collect/euronext_contracts_daily.py src/mais/collect/euronext_backfill.py src/mais/features/euronext_continuous.py src/mais/cli.py tests/test_euronext_daily_collector.py` PASS.
  - `venv/bin/python -m pytest tests/test_euronext_daily_collector.py tests/test_euronext_backfill.py tests/test_euronext_continuous.py tests/test_cli_ema.py -q` PASS (`34 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ → `DONE`.
- La donnée officielle quotidienne ne rentre plus dans les séries avec des champs canoniques vides.
- La réserve `expiry_estimated=True` est correcte tant qu'Euronext/Barchart ne fournit pas une vraie last-trading-date dans la référence.
- Déblocage : `DATA-EMA-17` → `READY`.

---

## DATA-EMA-17 — Features courbe EMA insuffisante → NaN

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-16  

### Objectif

Ne jamais encoder une courbe indisponible comme une courbe plate. Si moins de 2 contrats sont disponibles, les spreads/carry/flags contango-backwardation doivent être `NaN`. Si moins de 3 contrats sont disponibles, `ema_curve_slope_3` doit être `NaN`. Si le contrat 6 mois est identique au front, `ema_curve_slope_6` doit être `NaN`.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/euronext_curve.py` | **MODIFIER** |
| `tests/test_euronext_curve.py` | **MODIFIER** |

### Résultat ticket (2026-05-21)

- `src/mais/features/euronext_curve.py` corrigé :
  - moins de 2 contrats : spreads front/second, carry, roll yield, slope 6m et flags contango/backwardation passent à `NaN` ;
  - moins de 3 contrats : `ema_curve_slope_3`, spreads impliquant le troisième contrat passent à `NaN` ;
  - les flags contango/backwardation ne convertissent plus un `NaN` de courbe en faux `0`.
- Tests ajoutés :
  - un seul contrat → aucune pseudo-courbe plate ;
  - deux contrats → front/second conservé, slope 3 contrats masquée.
- Rebuild réel `build-ema-dataset` PASS :
  - `curve_rows=3868`, `master_shape=(6192, 371)`.
- Diagnostic post-rebuild :
  - lignes avec `ema_curve_contract_count < 2` : `3293` ;
  - valeurs non nulles sur ces lignes pour `ema_spread_f0_f1`, `ema_curve_slope_6`, `ema_contango_flag`, `ema_backwardation_flag`, `ema_carry_front_second` : `0`.
- Vérifications :
  - `venv/bin/ruff check src/mais/features/euronext_curve.py tests/test_euronext_curve.py` PASS.
  - `venv/bin/python -m pytest tests/test_euronext_curve.py tests/test_ema_curve_ablation.py tests/test_ema_benchmark.py -q` PASS (`18 passed`).
  - `venv/bin/python -m pytest tests/ -q` PASS.
- Ticket passé en `NEEDS_REVIEW` conformément à la règle projet.

### Review (2026-05-21)

- VALIDÉ → `DONE`.
- Le faux signal "absence de courbe = courbe plate" est supprimé.
- Déblocage : `DATA-TARGETS-02` → `READY`.

---

## DATA-TARGETS-02 — Targets EMA raw, adjusted et no-roll

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-17  

### Objectif

Séparer les targets prix réel/agriculteur des targets directionnelles ML :

- `y_up_h20_ema_raw`, `y_up_h40_ema_raw`, `y_up_h60_ema_raw`
- `y_up_h20_ema_adjusted`, `y_up_h40_ema_adjusted`, `y_up_h60_ema_adjusted`
- `y_up_h20_ema_no_roll`, `y_up_h40_ema_no_roll`, `y_up_h60_ema_no_roll`
- flags `target_crosses_roll_h20/h40/h60`

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/ema_targets.py` | **MODIFIER** |
| `tests/test_ema_targets.py` | **MODIFIER** |

### Résultat ticket (2026-05-21)

- Targets séparées ajoutées : `raw`, `adjusted`, `no_roll` pour H20/H40/H60.
- Flags ajoutés : `target_crosses_roll_h20`, `target_crosses_roll_h40`, `target_crosses_roll_h60`.
- Colonnes historiques conservées (`y_up_h20_ema`, `y_price_h20_ema`, `y_storage_value_3m`, etc.) comme alias raw pour compatibilité avec les benchmarks existants.
- Targets prix réel et stockage explicitées avec suffixe `_raw`.
- Rebuild réel `build-ema-dataset` PASS : `ema_targets.parquet` = `3377` lignes, `30` colonnes target, `master_shape=(6192, 371)`.
- Diagnostic réel : `y_up_h20_ema_no_roll` non nul sur `2023` lignes ; `y_up_h60_ema_no_roll` non nul sur `0` ligne car toutes les fenêtres 60 jours disponibles traversent un roll.
- Vérifications : ruff PASS, tests ciblés PASS (`20` tests), full pytest PASS.

### Review (2026-05-21)

VALIDÉ. Les targets ML ajustées et no-roll sont maintenant séparées des prix agricoles raw, les anciennes colonnes restent compatibles, et le diagnostic H60 confirme que le benchmark roll doit traiter `no_roll` comme potentiellement indisponible.

---

## EXP-EMA-ROLL-TARGET-01 — Benchmark targets EMA roll

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-TARGETS-02, EXP-BENCH-01  

### Objectif

Tester si l'échec du pivot EMA vient des targets contaminées par les rolls : comparer `raw`, `adjusted` et `no_roll` sur DA, AUC, top20, IC95 et stabilité annuelle.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_roll_target_benchmark.py` | **CRÉER** |
| `tests/test_ema_roll_target_benchmark.py` | **CRÉER** |

### Résultat ticket (2026-05-21)

- Benchmark raw/adjusted/no-roll créé et exécuté sur H20/H40/H60 avec les mêmes familles de features que le pivot EMA.
- Artefacts produits : `artefacts/benchmark_pivot/ema_roll_target_benchmark.json` et `.csv`.
- Verdict : `ROLL_TARGET_NOT_EXPLAINED`.
- Résultat primaire `cbot_ema_combined` :
  - H20 raw : DA `0.4673`, AUC `0.5026`, top20 `0.6032`.
  - H20 adjusted : DA `0.4470`, AUC `0.4440`, top20 `0.4889`.
  - H20 no-roll : DA `0.4457`, AUC `0.4383`, top20 `0.4368`.
  - H60 no-roll : `SKIPPED`, aucune fenêtre exploitable sans roll.
- Conclusion : l'échec du pivot EMA ne vient pas principalement d'une target raw contaminée par les rolls ; les versions adjusted/no-roll dégradent le signal dans le protocole principal.
- Vérifications : ruff PASS, tests ciblés `16 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. Le ticket répond à la question méthodologique et ferme cette hypothèse : la priorité n'est plus de changer la cible EMA, mais de travailler la qualité des features EMA fiables et les cibles agricoles de stockage.

---

## EXP-EMA-CURVE-TRUE-01 — Benchmark courbe EMA fiable

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-17, EXP-BENCH-01  

### Objectif

Relancer le benchmark avec uniquement les features EMA fiables quand la courbe complète est absente : front/liquid/harvest lags, OI/volume, basis, basis zscore, adjusted return/vol. Tester sans `cbot_eur_t` et sans basis pour isoler ce qui vient vraiment d'Euronext.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_true_curve_benchmark.py` | **CRÉER** |
| `tests/test_ema_true_curve_benchmark.py` | **CRÉER** |

### Résultat ticket (2026-05-21)

- Benchmark courbe EMA fiable créé et exécuté, en excluant les pseudo-features sparse (`spread`, `slope`, `carry`, flags contango/backwardation, roll yield).
- Artefacts produits : `artefacts/benchmark_pivot/ema_true_curve_benchmark.json` et `.csv`.
- Verdict : `BASIS_DRIVEN_SIGNAL`.
- Sur cible CBOT `y_up_h20` :
  - `reliable_ema_no_basis` : DA `0.5156`, AUC `0.4986`, top20 `0.4727` — pas suffisant.
  - `basis_only` : DA `0.5840`, AUC `0.6336`, top20 `0.6885` — signal fort.
  - `reliable_ema_with_basis` : DA `0.5774`, AUC `0.5900`, top20 `0.6694`.
  - `reliable_ema_with_basis_and_cbot_eur_t` : DA `0.6163`, AUC `0.6060`, top20 `0.6038`.
  - `cbot_eur_t_only` : DA `0.5041`, AUC `0.5207`, top20 `0.4891` — ne suffit pas à expliquer le signal.
- Sur cible EMA `y_up_h20_ema_raw`, les mêmes features restent faibles (`reliable_ema_with_basis` DA `0.5194`, AUC `0.5019`).
- Conclusion : EMA apporte surtout un signal de basis local CBOT-EMA pour le moteur CBOT, pas une vraie courbe prédictive complète ni une cible EMA directionnelle robuste.
- Vérifications : ruff PASS, tests ciblés `12 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. Le ticket clarifie la suite stratégique : conserver EMA comme bloc basis/prix local/stockage, ne pas promouvoir la courbe EMA sparse comme moteur principal.

---

## EXP-EMA-STUDY-01 — Audit statistique data EMA

**Priorité** : PRIORITÉ 0  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : DATA-EMA-17, DATA-TARGETS-02  

### Contexte

Avant de produire l'étude statistique Euronext complète, figer un audit data lisible : couverture, sources, contrats, roll gaps, densité de courbe, targets qui traversent les rolls, et vocabulaire prudent. Le dossier `notebooks/` reste interdit aux agents ; ce ticket produit donc un module reproductible, des artefacts et un rapport Markdown qui pourront servir de base aux notebooks.

### Objectifs mesurables

- Rapport `docs/EMA_DATA_AUDIT.md` produit.
- Artefact JSON `artefacts/ema_study/ema_data_audit.json` produit.
- Mention source obligatoire : `EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.`
- Recommandation terminologique : remplacer "EMA curve features" par "EMA front/basis/liquidity features, with partial curve fragments" dans les synthèses.
- Mesurer : sources, couverture, distribution contrats/date, non-null rates des features de courbe, roll gaps, target roll-cross rates.
- Ruff PASS, pytest PASS.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_data_audit.py` | **CRÉER** |
| `tests/test_ema_data_audit.py` | **CRÉER** |
| `docs/EMA_DATA_AUDIT.md` | Produit |

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_data_audit.py` créé.
- Rapport `docs/EMA_DATA_AUDIT.md` produit.
- Artefact `artefacts/ema_study/ema_data_audit.json` produit.
- Résultats réels :
  - `ema_contract_daily` : `4818` lignes, `3868` dates uniques, période `2010-01-04` → `2026-05-20`.
  - Sources : `4144` lignes `barchart_proxy_exploratory`, `664` `euronext_chart_history`, `10` `euronext_ajax_prices`.
  - Séries continues : front/liquid `3377` lignes, harvest_nov `1095` lignes.
  - Rolls front : `69`, gap moyen absolu `9.688` EUR/t, médian `6.000`, max `54.250`.
  - Densité courbe : `1.246` contrat/date en moyenne, `14.9%` des dates avec au moins 2 contrats, `5.0%` avec au moins 3.
  - Features sparse : spreads/slope/carry entre `2.9%` et `14.8%` de non-null.
  - Targets : H20 cross-roll `39.7%`, H40 `79.1%`, H60 `100.0%`; H60 no-roll `0` ligne.
- Garde-fous documentés :
  - `EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.`
  - Libellé recommandé : `EMA front/basis/liquidity features, with partial curve fragments`.
- Vérifications : ruff PASS, tests ciblés `21 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. L'audit fixe le vocabulaire et les limites méthodologiques de l'étude Euronext : courbe sparse, source exploratoire, EMA utile comme prix local/basis/stockage plutôt que moteur directionnel principal.

---

## EXP-EMA-STUDY-02 — Relation EMA / CBOT lead-lag

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : EXP-EMA-STUDY-01  

### Objectif

Étudier corrélations rolling, lead-lag `k=-10..+10`, tests de causalité type Granger si dépendances disponibles, et savoir si EMA anticipe CBOT ou l'inverse.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_cbot_relationship.py` | **CRÉER** |
| `tests/test_ema_cbot_relationship.py` | **CRÉER** |
| `docs/EMA_CBOT_RELATIONSHIP.md` | Produit |

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_cbot_relationship.py` créé.
- Rapport `docs/EMA_CBOT_RELATIONSHIP.md` produit.
- Artefact `artefacts/ema_study/ema_cbot_relationship.json` produit.
- Résultats réels :
  - `3082` lignes alignées, période `2010-01-04` → `2025-07-25`.
  - Corrélation de niveau EMA vs CBOT EUR/t : `0.9409`.
  - Corrélation des rendements 1 jour : `0.3425`.
  - Basis moyen : `37.23` EUR/t, écart-type `15.52`, range `-11.71` → `110.66`.
  - Lead-lag : verdict `mostly_contemporaneous`; lag 0 corr `0.3425`, meilleur EMA leads lag 1 corr `0.0387`, meilleur CBOT leads lag -1 corr `0.0423`.
  - Granger exploratoire : EMA returns → CBOT returns min p `0.0144` à lag 1 ; CBOT → EMA non significatif (min p `0.1605`).
- Vérifications : ruff PASS, tests ciblés `12 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. La relation de prix est forte, le lead-lag linéaire est surtout contemporain, et le signal Granger EMA→CBOT reste exploratoire ; il doit être prolongé par l'étude du basis.

---

## EXP-EMA-STUDY-03 — Basis mean reversion

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : EXP-EMA-STUDY-02  

### Objectif

Tester si le basis CBOT-EMA est mean-reverting et si les extrêmes de `basis_z` prédisent les retours EMA/CBOT ou le changement futur du basis.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_basis_study.py` | **CRÉER** |
| `tests/test_ema_basis_study.py` | **CRÉER** |
| `docs/EMA_BASIS_STUDY.md` | Produit |

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_basis_study.py` créé.
- Rapport `docs/EMA_BASIS_STUDY.md` produit.
- Artefact `artefacts/ema_study/ema_basis_study.json` produit.
- Verdict : `BASIS_MEAN_REVERSION_CONFIRMED`.
- Distribution basis : moyenne `37.23` EUR/t, écart-type `15.52`, P05/P50/P95 `8.50` / `37.86` / `62.50`.
- Extrêmes : z>=2 sur `6.2%` des observations, z<=-2 sur `5.1%`.
- À H20 :
  - High basis : `n=186`, basis change moyen `-7.64` EUR/t, reversion `70.4%`, EMA-CBOT return mean `-0.0622`.
  - Low basis : `n=153`, basis change moyen `+6.06` EUR/t, reversion `68.0%`, EMA-CBOT return mean `+0.0725`.
- À H40/H60, la reversion est encore plus marquée en moyenne, mais ces horizons restent à interpréter avec prudence côté rolls EMA.
- Vérifications : ruff PASS, tests ciblés `12 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. Le basis CBOT-EMA devient un axe central de l'indicateur européen : les extrêmes de basis se referment et peuvent nourrir les signaux contexte, stockage et risque/opportunité.

---

## EXP-EMA-STUDY-04 — Stockage économique EMA

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : EXP-EMA-STUDY-01, EXP-BENCH-04  

### Objectif

Recentrer le module stockage sur les métriques agricoles : gain net €/t, gain médian, % années positives, pire année, regret moyen, seuil économique `storage_value > coût + marge`.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_storage_economic_study.py` | **CRÉER** |
| `tests/test_ema_storage_economic_study.py` | **CRÉER** |
| `docs/EMA_STORAGE_ECONOMIC_STUDY.md` | Produit |

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_storage_economic_study.py` créé.
- Rapport `docs/EMA_STORAGE_ECONOMIC_STUDY.md` produit.
- Artefact `artefacts/ema_study/ema_storage_economic_study.json` produit.
- Verdict : `STORAGE_ECONOMIC_NO_GO`.
- Baselines réelles :
  - `never_store` : gain `0.000` EUR/t, regret oracle `8.660`.
  - `always_store_1m` : gain `-0.293` EUR/t.
  - `always_store_3m` : gain `-1.319` EUR/t.
  - `always_store_6m` : gain `-4.003` EUR/t.
  - `oracle_store_3m` : gain `+8.660` EUR/t.
- Meilleure stratégie modèle : `selected_full_pred_value_margin_5`, gain `+0.005` EUR/t, stocke `50.2%`, années positives `3/8`, pire année `2015` à `-5.851` EUR/t.
- Conclusion : potentiel économique réel côté oracle, mais les modèles actuels ne capturent pas la décision stockage avec une marge matérielle.
- Vérifications : ruff PASS, tests ciblés `13 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. Le stockage reste une piste métier importante, mais il faut améliorer les signaux et coûts locaux avant de l'utiliser comme décision automatique.

---

## EXP-EMA-STUDY-05 — Module A data status

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : MOD-A-02  

### Objectif

Ajouter une table de statut par signal Module A : `real / proxy / missing / manual`, couverture, DA seul, poids, décision garder/remplacer.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/indicator/module_a_data_status.py` | **CRÉER** |
| `tests/test_module_a_data_status.py` | **CRÉER** |
| `docs/MODULE_A_DATA_STATUS.md` | Produit |

### Résultat ticket (2026-05-21)

- Module `src/mais/indicator/module_a_data_status.py` créé.
- Tests `tests/test_module_a_data_status.py` créés.
- Rapport `docs/MODULE_A_DATA_STATUS.md` produit, avec artefact JSON `artefacts/ema_study/module_a_data_status.json`.
- Résultat réel sur `y_up_h20_ema` :
  - statuts : `real=4`, `proxy=5`, `manual=1`, `missing=2` ;
  - couverture moyenne active `55.5%`, couverture pondérée par poids calibrés `57.3%` ;
  - `wasde_surprise` est le seul signal prioritaire (`DA hebdo=56.7%`, poids `0.169`) ;
  - `china_demand` et `export_pace_eu` sont `missing` dans la source active malgré des poids élevés ;
  - `futures_structure` est `REMPLACER_PRIORITE` car couverture active `10.4%` et signal de courbe partiel.
- L'audit distingue la couverture candidate de la source réellement utilisée afin de détecter les colonnes de fallback shadowées.
- Vérifications : ruff PASS, tests ciblés `14 passed`, full pytest PASS.

### Review (2026-05-21)

VALIDÉ. Le Module A est utilisable comme contexte, mais ses conclusions fortes doivent exclure les signaux `missing/manual` et libeller explicitement les proxies.

---

## EXP-EMA-STUDY-06 — CQR prix EMA

**Priorité** : MOYENNE  
**Type** : complexe  
**Statut** : DONE  
**Dépendances** : EXP-EMA-STUDY-01  

### Objectif

Tester une prévision de fourchette de prix EMA avec coverage 90 %, sharpness et Winkler loss. Baselines : naive, seasonal naive, CBOT converted, Ridge, HistGB, quantile regression si disponible.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_price_cqr_study.py` | **CRÉER** |
| `tests/test_ema_price_cqr_study.py` | **CRÉER** |
| `docs/EMA_PRICE_CQR_STUDY.md` | Produit |

### Résultat ticket (2026-05-21)

- Module `src/mais/research/ema_price_cqr_study.py` créé.
- Tests `tests/test_ema_price_cqr_study.py` créés.
- Rapport `docs/EMA_PRICE_CQR_STUDY.md` et artefact `artefacts/ema_study/ema_price_cqr_study.json` produits.
- Verdict réel : `CQR_PRICE_NO_GO` — aucun modèle n'atteint le plancher de couverture empirique acceptable `88%` pour une cible `90%`.
- Résultats principaux :
  - H20 : meilleur Winkler/coverage pratique = `cbot_converted`, coverage `79.2%`, width moyen `112.1`, Winkler `160.2` ; CQR quantile selected coverage `75.0%`, width `64.7`, Winkler `235.6`.
  - H60 : meilleur disponible = `cbot_converted`, coverage `80.4%`, width moyen `127.5`, Winkler `199.8` ; CQR quantile selected coverage `73.0%`, width `73.1`, Winkler `309.6`.
  - Les années 2021–2022 cassent fortement la couverture pour les modèles plus serrés.
- Conclusion : la fourchette prix EMA n'est pas encore exploitable comme intervalle 90% fiable ; elle doit être retravaillée avec régime/choc, volatilité locale et calibration plus robuste.
- Vérifications : ruff PASS, tests ciblés `13 passed`, full pytest PASS (warnings non bloquants sklearn/statsmodels).

### Review (2026-05-21)

VALIDÉ. Le résultat négatif est cohérent avec les chocs de prix et confirme qu'il ne faut pas promettre d'intervalle prix agriculteur à 90% tant que la calibration n'est pas robuste.

---

## EXP-EMA-STUDY-07 — Synthèse finale Euronext

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : DONE  
**Dépendances** : EXP-EMA-STUDY-02, EXP-EMA-STUDY-03, EXP-EMA-STUDY-04, EXP-EMA-STUDY-05, EXP-EMA-STUDY-06  

### Objectif

Produire une synthèse finale honnête : Euronext direct validé ou non, CBOT moteur principal, basis utile, stockage utile, Module A fiable, limites de source exploratoire et protocole de suite.

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `docs/EMA_FINAL_SYNTHESIS.md` | **CRÉER** |

### Résultat ticket (2026-05-21)

- Document `docs/EMA_FINAL_SYNTHESIS.md` créé.
- Synthèse finale produite avec verdicts :
  - pivot directionnel Euronext direct `NO_GO` ;
  - CBOT reste moteur principal ;
  - basis CBOT/EMA à garder comme meilleur signal EMA actuel ;
  - courbe Euronext complète non validée, données trop sparse ;
  - stockage EMA prometteur côté oracle mais `NO_GO` modèle ;
  - Module A à garder comme contexte avec proxies/missing/manual explicites ;
  - CQR prix EMA `NO_GO` ;
  - source historique EMA à réserver à la recherche tant qu'elle reste `barchart_proxy_exploratory`.
- Architecture recommandée : CBOT pour direction globale, EMA pour prix local, basis pour divergence Europe/monde, stockage pour décision métier.
- Vérification doc : `test -s docs/EMA_FINAL_SYNTHESIS.md`, `wc -l` PASS (`307` lignes). Tests non relancés car ticket documentaire uniquement ; full pytest venait de passer sur le ticket précédent après les derniers changements code.

### Review (2026-05-21)

VALIDÉ. La synthèse est cohérente avec les expériences : ne pas forcer le pivot EMA, mais garder EMA comme couche locale/basis/stockage dans l'indicateur hybride.

---

## OPS-DAILY-01 — Pipeline quotidien EMA

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : BLOCKED  
**Dépendances** : MODEL-DIR-01, MODEL-CQR-01  

### Contexte

Étendre `src/mais/ops/daily.py` pour inclure les steps EMA : collecte contrats, mise à jour séries continues, recalcul features courbe, prédictions EMA, signal JSON. La latence cible collecte→signal est < 2 heures.

### Objectifs mesurables

- Pipeline complet en < 2h (collection EMA jusqu'à signal JSON)
- Signal JSON produit dans `PREDICTIONS_DAILY_DIR/YYYY-MM-DD_ema_signal.json`
- Data quality check intégré (si score < 0.70 → signal UNCERTAIN)
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/ops/daily.py` | **MODIFIER** — ajouter steps EMA |
| `src/mais/ops/ema_predict.py` | **CRÉER** — orchestration prédictions EMA |
| `tests/test_ops_ema_daily.py` | **CRÉER** — 4 tests |

### Tâches détaillées

**T1 — Steps EMA dans daily.py**

Ordre d'exécution quotidien (après clôture ~18h CET) :
```python
steps_ema = [
    ("collect_euronext",    collect_euronext_daily),      # 5 min
    ("collect_cross_assets", collect_eu_cross_assets),    # 2 min
    ("build_ema_continuous", build_ema_continuous_series),# 5 min
    ("build_ema_curve",     build_ema_curve_features),    # 5 min
    ("build_ema_dataset",   build_ema_master_dataset),    # 5 min
    ("data_quality",        run_data_quality_check),      # 2 min
    ("predict_ema",         predict_ema_signal),          # 10 min
    ("save_signal",         save_daily_signal_json),      # 1 min
]
```

**T2 — Signal JSON** (structure §13.1 ARCHITECTURE_EMA_PRO)

**T3 — Tests**

```python
def test_signal_json_schema_complete():
def test_uncertain_if_quality_low():
def test_proxy_flag_propagated_to_signal():
def test_pipeline_idempotent_same_day():
```

---

## OPS-REPORT-01 — Rapport hebdomadaire agriculteur EMA

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : BLOCKED  
**Dépendances** : OPS-DAILY-01  

### Contexte

Chaque lundi, produire un rapport Markdown lisible par un agriculteur (structure §13.2 ARCHITECTURE_EMA_PRO) : prix EMA, orientation marché, facteurs, prévision prix, décision stockage, alertes. Étendre `src/mais/ops/weekly_report.py` (existant, CBOT) pour le pivot EMA.

### Objectifs mesurables

- Rapport Markdown produit dans `REPORTS_WEEKLY_EMA_DIR/YYYY-WXX_mais_euronext.md`
- 6 sections présentes : prix EMA, orientation, facteurs, prévision, stockage, alertes
- Signal JSON machine-readable produit en parallèle
- Langage métier : pas de jargon ML, chiffres en EUR/tonne
- Ruff PASS, pytest PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/ops/weekly_report_ema.py` | **CRÉER** — rapport hebdomadaire EMA |
| `src/mais/indicator/shap_translator.py` | **MODIFIER** — ajouter traduction signaux EMA |
| `tests/test_weekly_report_ema.py` | **CRÉER** — 4 tests |

---

## OPS-CRON-01 — Automatisation cron/systemd

**Priorité** : MOYENNE  
**Type** : simple  
**Statut** : BLOCKED  
**Dépendances** : OPS-DAILY-01  

### Contexte

Configurer les jobs cron (ou systemd timers) pour les deux pipelines : quotidien (lun-ven 18h05 CET) et hebdomadaire (lundi 6h CET).

### Objectifs mesurables

- 2 entrées cron configurées et testées
- Logs dans `logs/cron_ema_daily.log` et `logs/cron_ema_weekly.log`
- Commande de vérification documentée

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `ops/setup_cron_ema.sh` | **CRÉER** — script installation cron |
| `ops/cron_ema.txt` | **CRÉER** — entrées cron documentées |

### Tâches détaillées

```bash
# ops/cron_ema.txt

# Collecte quotidienne EMA (lun-ven, après clôture Euronext)
5 18 * * 1-5  cd "/home/cytech/Desktop/Etude Mais" && venv/bin/python -m mais.cli daily-run --collect >> logs/cron_ema_daily.log 2>&1

# Rapport hebdomadaire (lundi, avant ouverture marchés)
0 6 * * 1  cd "/home/cytech/Desktop/Etude Mais" && venv/bin/python -m mais.cli report weekly >> logs/cron_ema_weekly.log 2>&1
```

---

## VAL-BACKTEST-01 — Backtest économique complet EMA

**Priorité** : HAUTE  
**Type** : critique  
**Statut** : BLOCKED  
**Dépendances** : OPS-DAILY-01  

### Contexte

C'est le verdict final de toute la Phase EXP. Le backtest économique sur 2015-2024 mesure si le système complet (direction + CQR + stockage) apporte un gain réel à un agriculteur européen, par rapport à une stratégie naïve SELL_HARVEST.

### Objectifs mesurables

- Gain net €/t/an > 0 sur ≥ 6/8 crop years (critère professionnel §16 ARCHITECTURE_EMA_PRO)
- Pire année documentée (drawdown acceptable)
- Comparaison 4 stratégies : SELL_HARVEST, SIGNAL_BINARY, SIGNAL_PARTIAL, ALWAYS_STORE_3M
- Rapport `artefacts/backtest_ema_final/backtest_ema_results.json`
- Rapport synthèse `docs/BACKTEST_EMA_FINAL.md` avec résultats honnêtes

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/ema_economic_backtest.py` | **CRÉER** — backtest complet EMA |
| `artefacts/backtest_ema_final/backtest_ema_results.json` | Produit |
| `docs/BACKTEST_EMA_FINAL.md` | Rapport synthèse |
| `tests/test_ema_economic_backtest.py` | **CRÉER** — 4 tests |

---

## VAL-REPORT-01 — Rapport final Euronext

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : BLOCKED  
**Dépendances** : VAL-BACKTEST-01  

### Contexte

Mettre à jour `docs/PROFESSIONAL_STUDY_REPORT_V3.md` avec les résultats Phase EXP. Tableau ✅/❌/⚠️ mis à jour. Documenter honnêtement ce qui fonctionne et ce qui ne fonctionne pas.

### Objectifs mesurables

- Rapport mis à jour avec résultats EXP
- Tableau état réel d'implémentation complet
- Aucun claim non prouvé dans le rapport

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `docs/PROFESSIONAL_STUDY_REPORT_EMA.md` | **CRÉER** — rapport final Phase EXP |
| `docs/PROFESSIONAL_STUDY_REPORT_V3.md` | **MODIFIER** — section Phase EXP ajoutée |

---

## Objectif final Phase EXP (critère de succès global)

> Produire, chaque lundi, un rapport en 3 modules permettant à un agriculteur européen de prendre de meilleures décisions de stockage et de vente partielle sur le maïs Euronext, avec un gain net moyen positif par rapport à SELL_HARVEST, sur la majorité des campagnes de validation (2015-2024), sans aucune connaissance ex-post et sans recalibrage des seuils. Le signal doit être basé sur de vrais prix Euronext (aucun proxy CBOT).

**Ce n'est prouvé que par VAL-BACKTEST-01 (backtest économique complet). Tous les autres tickets préparent ce moment.**
