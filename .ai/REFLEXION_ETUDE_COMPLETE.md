# Réflexion — Étude statistique complète du cours du maïs CBOT & Euronext EMA

> Créé le 2026-05-20. Document vivant — développement continu.
> Nature : document de réflexion, de conception et d'idées.  
> **Ce document n'est pas un plan figé. Il évolue à chaque session.**

---

## 0. Le pivot : de l'indicateur à l'étude

### 0.1 Ancien objectif (mis en pause)

Créer un indicateur opérationnel BULLISH/BEARISH/UNCERTAIN pour aider les agriculteurs à décider de vendre ou stocker leur maïs. Avec un rapport agriculteur hebdomadaire, un CQR prix, un backtest économique.

**Pourquoi en pause :**
- Le signal directionnel EMA est faible (DA ≈ 0.47, AUC ≈ 0.50 actuellement)
- Le CQR prix EMA : couverture empirique ~79%, insuffisant pour promettre 90%
- L'historique EMA reste exploratoire (Barchart proxy, pas settlement officiel complet)
- Promettre un outil de décision commerciale sans validation économique solide est risqué scientifiquement

**Ce qui reste valide :** les modules d'analyse sont des outils d'étude excellents. Le rapport CBOT Phase R&D est bien avancé. La base technique (CQR, walk-forward, ablation, IC95%) est solide.

### 0.2 Nouvel objectif (actif)

> **Mener une étude statistique et économique complète du cours du maïs CBOT et Euronext EMA, afin d'identifier les facteurs explicatifs, mesurer les relations inter-marchés, et quantifier les limites de prédictibilité — sans prétendre à un outil opérationnel non encore validé.**

**Ce qu'on garde :**
- Prix Euronext EMA en EUR/tonne
- Prix CBOT converti en EUR/tonne
- Basis CBOT/EMA
- Variables explicatives mondiales et européennes
- Analyse statistique rigoureuse
- Prévision expérimentale documentée honnêtement

**Ce qu'on sort définitivement du périmètre principal :**
- Prix local coopérative
- Stockage physique, coûts, décision vendre/stocker
- Hedging personnalisé
- Rapport agriculteur opérationnel
- Recommandation commerciale directe

**Modules en archive définitive** (travail conservé, mais hors pipeline principal) :
- `src/mais/research/storage_targets.py` → archive
- `src/mais/research/farmer_backtest_v2.py` → archive
- `src/mais/ops/weekly_report.py` → archive (remplacé par rapport statistique hebdomadaire EMA)
- `src/mais/indicator/module_a_context.py` → conservé comme outil de contexte, pas comme indicateur opérationnel

**Formulation correcte pour les signaux :**
- Pas : "RECOMMANDATION : STOCKER"
- Mais : "Le marché présente une tension relative Europe/monde positive (+2.1σ basis), historiquement associée à une hausse relative EMA dans 62% des cas à H20 [IC95% : 55-69%]"

**Vocabulaire obligatoire :**
- Pas : "courbe futures EMA complète" → mais : "features EMA front, basis, liquidité et fragments de courbe"
- Pas : "prévision prix EMA validée" → mais : "prévision prix EMA expérimentale (coverage 79%, objectif non atteint)"
- Pas : "EMA Granger-cause CBOT (signal exploitable)" → mais : "EMA→CBOT prometteur, non encore confirmé OOF"

### 0.3 Phrase directrice de toute l'étude

> **CBOT explique la tendance mondiale du maïs. Euronext EMA ne se prédit pas encore bien directement, mais il révèle la prime européenne via le basis. La vraie étude Euronext consiste à expliquer le basis, la transmission CBOT→EMA, les périodes de découplage, et le résidu européen spécifique.**

Cette phrase guide chaque décision d'expérience :
- Si une expérience n'éclaire pas le basis, la transmission ou le résidu → différer
- Si une expérience prétend prédire EMA directement sans validation OOF stricte → marquer EXPÉRIMENTAL
- Si un résultat contredit CBOT comme moteur principal → documenter et investiguer (cf. §15 Granger)
- Si une variable européenne n'améliore pas le delta DA de +0.008 ou n'explique pas le résidu → NEUTRE, ne pas garder

---

## 1. Architecture de l'étude

```
ÉTUDE STATISTIQUE DU COURS DU MAÏS
│
├── PARTIE A — MARCHÉ MONDIAL (CBOT)
│   ├── Contexte : marché de référence mondiale
│   ├── Variables : WASDE, COT, météo US, exports, macro
│   ├── Signal directionnel : faible mais documenté (DA ≈ 0.58 J+20, AUC ≈ 0.63)
│   ├── Meilleur modèle : histgb + crop year walk-forward
│   └── Limites connues : autocorrélation, régimes, données WASDE rares
│
└── PARTIE B — MARCHÉ EUROPÉEN (EURONEXT EMA)
    ├── Construction des séries (contrats, rolls, continues)
    ├── Relation EMA ↔ CBOT (cointegration, lead-lag, decomposition)
    ├── Basis CBOT/EMA : variable centrale
    ├── Signal directionnel EMA : à quantifier proprement
    ├── Grandes variations : event study
    ├── Variables européennes : EC MARS, Agreste, FranceAgriMer
    ├── Décomposition du retour EMA
    └── Prévision expérimentale
```

---

## 2. Résultats actuels — état honnête

### 2.1 Phase CBOT (R&D-01 à R&D-10 — DONE)

| Métrique | Valeur | Horizon |
|---|---|---|
| DA walk-forward crop year | 0.624 | J+60 (histgb) |
| AUC | 0.675 | J+60 |
| DA hebdomadaire | 0.616 | J+60 |
| Backtest SELL_HARVEST | 82.8% | — |
| CQR coverage | 91.7% | — |
| IC95% lo DA | > 0.50 | J+60 |

**Verdict CBOT :** CONFIRMÉ sur J+60. Le signal mondial CBOT est réel mais modeste.

### 2.2 Phase EMA — résultats réels (études complétées 2026-05-20/21)

#### Données construites

| Artefact | Lignes | Qualité |
|---|---|---|
| ema_contract_daily.parquet | 4 818 | Exploratoire (Barchart proxy) |
| ema_contract_reference.parquet | 81 contrats | H/M/Q/X validés 2010-2026 |
| ema_front_raw/adjusted | 3 377 | Front avec rolls |
| ema_harvest_nov | 1 095 | Non ajusté |
| ema_curve_features.parquet | 3 868 dates, 28 features laggées | |
| ema_targets.parquet | 3 377 lignes, 30 colonnes cibles | |
| features.parquet master | (6 192, 371) | 37 colonnes EMA ajoutées |

**Limite structurelle clé :** seules **14.9%** des dates ont ≥ 2 contrats actifs simultanément → la courbe est quasi inexistante la plupart du temps. Spreads, carry, slope → NaN sur ~85% des dates. Ce n'est pas un bug : EMA est un marché peu liquide.

#### Benchmark directionnel — résultats réels

| Setup | Cible | DA | AUC | IC95 DA | Verdict |
|---|---|---|---|---|---|
| cbot_ema_combined | y_up_h20_ema_raw | 0.4673 | 0.5026 | [0.4432, 0.4902] | **NO_GO** |
| reliable_ema_with_basis | y_up_h20_ema_raw | 0.5194 | 0.5019 | — | FAIBLE |
| ema_curve_only | y_up_h20 (CBOT) | **0.6174** | **0.6439** | — | SIGNAL FORT |
| basis_only | y_up_h20 (CBOT) | **0.5840** | **0.6336** | — | SIGNAL FORT |
| ema_curve_only hebdo | y_up_h20 (CBOT) | **0.6193** | — | [0.5711, 0.6675] | CONFIRMÉ HEBDO |
| Module A context | y_up_h20_ema (hebdo) | **0.5778** | — | — | PASSE LE SEUIL |

**Conclusion principale :** EMA ne prédit pas EMA directement (NO_GO). Mais EMA prédit CBOT (signal fort). C'est une inversion de la causalité attendue.

#### Basis mean reversion — quantifiée

| Situation | N dates | Δbasis à H20 (moyen) | Taux reversion | Retour EMA-CBOT moyen |
|---|---|---|---|---|
| Basis élevé (basis_z > 1.5) | 186 | **-7.64 €/t** | **70.4%** | -6.22% |
| Basis faible (basis_z < -1.5) | 153 | **+6.06 €/t** | **68.0%** | +7.25% |

**Signal actionnable confirmé :** quand le basis est extrême, il revient à la moyenne dans **~70% des cas à H20**.

#### Ablation features EMA (sur cible CBOT y_up_h20)

| Famille | Delta DA vs baseline | Significatif BH |
|---|---|---|
| basis_cbot | **+0.0826** | q=0.0000 |
| all_ema_curve | **+0.0739** | — |
| price_levels | **+0.0569** | — |
| liquidity | **+0.0449** | — |
| continuous_lags | +0.0115 | Non |
| adjusted_returns / slope / spreads | ~0 | Non |

#### Lead-lag EMA/CBOT — découverte inattendue

| Test | Valeur | Interprétation |
|---|---|---|
| Corrélation niveaux | 0.9411 | Quasi parfaite |
| Corrélation rendements 1j | 0.3425 | Modérée |
| Granger EMA→CBOT min p (lag 1) | **0.0144** | ⚠ SIGNIFICATIF |
| Granger CBOT→EMA min p | 0.1605 | Non significatif |

**→ Voir §15 pour l'analyse complète de cette découverte.**

#### CQR prix EMA

| Modèle | Coverage IC90% | Winkler loss | Verdict |
|---|---|---|---|
| cbot_converted | 79.2% (H20) | 160.2 | NO_GO (< 88%) |
| CQR quantile selected | 75.0% (H20) | — | NO_GO |
| **Objectif** | **≥ 88%** | | — |

| Métrique complémentaire | Valeur | Statut |
|---|---|---|
| Roll gap moyen front | 9.7 €/t | ⚠ Important sur H40/H60 |
| % fenêtres H20 traversant un roll | 39.7% | À noter |
| % fenêtres H60 traversant un roll | 100% | Critique |
| Proxy CBOT vs EMA réel (MAE) | 37.3 €/t | PROXY_FORBIDDEN |

**Verdict EMA phase actuelle :** benchmark directionnel NO_GO sur EMA comme cible. Signal fort existant sur CBOT via features EMA (basis). Basis mean reversion confirmée. CQR prix NO_GO. Granger EMA→CBOT : à valider rigoureusement.

### 2.3 Ce que les résultats confirment

1. **CBOT est le moteur mondial** — 94% de corrélation en niveau, mais la causalité Granger pointe EMA→CBOT (pas CBOT→EMA)
2. **Le basis est la variable centrale** — il mean-reverts à 70%, predit CBOT avec delta DA +0.083, c'est le meilleur signal EMA
3. **Les rolls EMA biaisent les targets longues** — H60 : 100% des fenêtres traversent un roll, la cible H60 brute est non fiable
4. **Le proxy CBOT est inutilisable** — MAE 37 €/t, > 2σ sur 69% des jours : les résultats sur proxy sont sans valeur
5. **EMA prédit CBOT, pas l'inverse** — résultat Granger qui inverse la narrative classique
6. **Le Module A contexte EMA donne DA hebdo 57.8%** — seul signal passant le seuil minimal, via contexte structurel (stocks, exports, saisonnalité)

### 2.4 Ce qui reste non résolu

1. **Granger EMA→CBOT : artefact ou vrai signal ?** — à valider OOF sur sous-périodes (voir §15)
2. **Données EU européennes manquantes** — EC MARS, Open-Meteo EU, FranceAgriMer non collectés
3. **Settlement officiel Euronext absent** — historique Barchart proxy ≠ prix de règlement officiels
4. **CQR prix non validé** — coverage 79% vs 88% requis : amélioration possible via données EU ou regime-conditioned CQR
5. **Résidu EMA non étudié** — la partie non expliquée par CBOT+EUR/USD peut-elle être prédite par données EU ?

---

## 3. Le basis CBOT/EMA : axe central de l'étude Euronext

### 3.1 Définition

```
cbot_eur_t = cbot_cents_bu / 100 / eurusd_rate * 39.3679   (conversion exacte)
basis      = ema_front_price_raw - cbot_eur_t              (prime européenne)
```

Le basis encode la **divergence prix européen vs mondial**. Il capte :
- La prime ou décote de l'offre européenne
- Les coûts de transport et logistique
- Les barrières commerciales et compétitivité
- L'impact de l'EUR/USD sur la compétitivité des exports EU
- La tension relative entre stocks EU et stocks mondiaux

### 3.2 Études à mener sur le basis

**Distribution et régimes :**
- Distribution du basis 2014-2025
- z-score basis 260j, 52w, 104w
- Percentile historique basis (expanding window)
- Détection de régimes de basis (HMM 2-3 états : contraction / normal / expansion)
- Saisonnalité du basis (mois par mois, campagne par campagne)

**Mean reversion :**
- Test ADF sur basis : stationnaire ? (attendu : oui, I(0))
- Test KPSS complémentaire
- AR(1) : coefficient autorégressif et half-life
- `half_life = -log(2) / log(rho)` où rho = AR(1) coefficient
- Threshold autoregressive model (STAR) : mean reversion asymétrique ?
- Taux de hit reversion à H20/H40 selon z-score initial

**Basis comme prédicteur :**
```
Étude 1 : basis_z extrême → retour EMA à H20
  Classes : basis_z > +2 (EMA très cher vs CBOT)
            basis_z < -2 (EMA très pas cher)
            basis_z ∈ [-1, +1] (neutre)

Étude 2 : régression Δbasis_H20 ~ basis_z
  → donne la vitesse de retour estimée

Étude 3 : classification basis reversion
  y = int(basis_t20 < basis_t) si basis_z > +1.5
  → probabilité de contraction du basis
```

**Basis et variables externes :**
- `basis ~ EUR/USD_z` : un EUR faible compresse le basis (exports EU moins compétitifs)
- `basis ~ stocks_EU / stocks_world` : divergence stocks explique basis
- `basis ~ TTF_gas_z` : coûts énergie élèvent le basis (coûts production EU)
- `basis ~ Ukraine_corridor_flag` : tension supply Ukraine élève le basis EU
- `basis ~ Brazil_harvest_pct` : harvest Brésil comprime le basis (concurrence export)

### 3.3 Nouvelles features basis à construire

```python
basis                      # niveau absolu
basis_zscore_52w           # z-score expanding 52w
basis_zscore_260d          # z-score expanding 260j
basis_percentile_5y        # percentile dans les 5 dernières années
basis_ar1_residual         # résidu par rapport à la prédiction AR(1)
basis_mean_reversion_score # = -basis_z (score de retour attendu)
basis_regime               # -1 / 0 / +1 (HMM 2-3 états si possible)
basis_momentum_20d         # variation du basis sur 20j
basis_acceleration         # variation de la variation (2ème différence)
basis_vs_3y_mean           # écart vs moyenne mobile 3 ans (expanding)
basis_vol_20d              # volatilité du basis sur 20j
basis_eur_adjusted         # basis corrigé de l'EUR/USD
```

---

## 4. Décomposition du retour EMA

C'est l'expérience la plus importante de la Partie B.

### 4.1 Modèle de décomposition

```
EMA_return_1d ≈ α + β₁ * CBOT_return_1d
                    + β₂ * EURUSD_return_1d
                    + β₃ * Δbasis_1d
                    + ε_EU_specific

EMA_return_1d = partie_mondiale + partie_change + partie_basis + résidu_EU
```

**Objectif** : quantifier la variance expliquée par chaque composante.

**Méthode :**
1. Régression OLS rolling (fenêtre 260j) → betas variables dans le temps
2. Régression OLS sur toute la période → betas globaux
3. Régression par régime (2018 / 2020 / 2022 / normal)
4. Résidu = variation spécifique Euronext non expliquée par CBOT/EUR

### 4.2 Exploitation du résidu

Une fois le résidu calculé :
```python
ema_residual_return_1d = ema_return_1d - beta_cbot * cbot_eur_return - beta_eurusd * eurusd_return

# Ce résidu est ce que les données européennes doivent expliquer :
# - EC MARS / Agreste / FranceAgriMer
# - Ukraine
# - Brésil / Argentine
# - basis
# - TTF gas
# - EMA liquidity
```

**Questions à tester :**
- Le résidu est-il prévisible (DA > 0.50) avec des features européennes seulement ?
- Le résidu est-il plus prévisible que le retour brut EMA ?
- Quelles variables expliquent les résidus extrêmes (>3σ) ?

---

## 5. Structure des 15 notebooks Euronext (structure cible)

### Tableau de bord des notebooks

| Notebook | Titre | Bloc | Priorité |
|---|---|---|---|
| `00` | ema_project_overview | Fondations | P0 |
| `01` | ema_data_audit | Fondations | P0 |
| `02` | ema_contracts_and_rolls | Fondations | P0 |
| `03` | ema_continuous_series | Fondations | P0 |
| `04` | ema_cbot_relationship | Fondations | P0 |
| `05` | **ema_return_decomposition** (NOUVEAU) | Stat lourdes | P1 |
| `06` | **ema_residual_study** (NOUVEAU) | Stat lourdes | P1 |
| `07` | ema_basis_study | Stat lourdes | P1 |
| `08` | ema_direction_benchmark | Prédictif | P2 |
| `09` | ema_big_moves_event_study | Prédictif | P2 |
| `10` | ema_feature_importance | Prédictif | P2 |
| `11` | ema_european_fundamentals | Données EU | P3 |
| `12` | ema_price_forecast_experimental | Prédictif | P2 |
| `13` | **ema_weekly_benchmark** (NOUVEAU) | Prédictif | P2 |
| `14` | ema_synthesis_report | Rapport final | P4 |

**Logique de construction :**
- P0 : fondations — données, séries, relation EMA/CBOT
- P1 : stats lourdes — décomposition, résidu, basis
- P2 : études prédictives — benchmark, événements, features
- P3 : données EU — enrichissement sources
- P4 : rapport final

---

### `00_ema_project_overview.ipynb`

**Objectif :** justifier le projet et définir le périmètre.

Contenu :
- Graphique prix EMA vs CBOT converti (2014-2025)
- Graphique basis sur la même période avec highlight crises
- Tableau résultats actuels (DA/AUC actuels)
- Tableau ce qu'on cherche vs ce qu'on ne cherche pas
- Roadmap notebooks

**Résultat attendu :** document de référence, 1 seule figure synthétique par section.

---

### `01_ema_data_audit.ipynb`

**Objectif :** valider la donnée EMA avant tout modèle.

Contenu :
- Période disponible par source (Barchart proxy vs Euronext récent)
- Nombre de jours, contrats, rolls, NaN
- Distribution des prix EMA par contrat et par mois (H/M/Q/X)
- Couverture OI et volume par contrat et par période
- Trous de données : quelles périodes manquantes
- Comparaison proxy CBOT vs vrais prix Euronext récents (chevauchement 2024-2025)
- Verdict : période utilisable pour ML, période exploratoire, période à exclure

**Tables produites :**
- `artefacts/euronext/data_audit_summary.json`
- Graphique heatmap couverture par contrat × année

---

### `02_ema_contracts_and_rolls.ipynb`

**Objectif :** documenter la complexité des contrats et leurs effets.

Contenu :
- Cycles des contrats H/M/Q/X par campagne
- Distribution roll gaps (histogram)
- Roll gaps les plus importants (table top 10)
- Impact sur targets H20 / H40 / H60 : % de fenêtres traversant un roll
- Comparaison rendements raw vs adjusted autour des rolls
- Distribution du nombre de contrats actifs par jour

**Expérience centrale :**
```
Pour chaque horizon H ∈ {20, 40, 60} :
  pct_windows_crossing_roll = % de fenêtres [t, t+H] qui traversent ≥ 1 roll
  → si > 20% : la cible raw est biaisée, il faut adjusted ou no-roll target
```

---

### `03_ema_continuous_series.ipynb`

**Objectif :** construire et valider les séries continues.

Séries à documenter :
- `ema_front_raw` vs `ema_front_adjusted`
- `ema_liquid_raw` vs `ema_liquid_adjusted`
- `ema_harvest_nov` (jamais ajusté)
- `cbot_eur_t`
- `basis`

Vérifications :
- Invariant cumsum roll_gaps = raw - adjusted
- Transitions smooth dans adjusted
- Nombre de rolls par série et par année
- Corrélation front vs liquid (attendu > 0.99 mais pas 1.0)
- Différence front vs liquid : à quelles périodes divergent-ils ?

---

### `04_ema_cbot_relationship.ipynb`

**Objectif :** caractériser la relation EMA ↔ CBOT.

Tests à mener :

**Cointegration :**
```python
# Engle-Granger sur log(EMA_raw) vs log(CBOT_eur_t)
# Johansen si on veut tester plusieurs vecteurs
# Attendu : cointegration confirmée (relation long terme)
```

**VAR / VECM :**
```python
# Si cointegré : VECM(p)
# → vitesse d'ajustement alpha : qui s'ajuste l'un vers l'autre ?
# → matrices d'impact à court terme
# → impulse response functions (IRF)

# Si pas cointegré : VAR sur returns
# Granger causality EMA → CBOT et CBOT → EMA
```

**Rolling correlation :**
```python
# Fenêtres : 20j, 60j, 120j, 260j
# Correlation sur returns, pas niveaux
# → détecter les périodes de découplage
```

**Lead-lag :**
```python
# Cross-correlation à lags 0, ±1, ±2, ±3, ±5, ±10 jours
# → qui bouge en premier ?
# Caution : ne pas interpréter comme prédictif sans validation OOF
```

**Décomposition beta :**
```python
# Régression rolling 260j :
# EMA_return ~ CBOT_return + EURUSD_return
# → R² : part expliquée
# → résidu : variation spécifique EU
# → betas variables dans le temps → à graphiquer
```

---

### `05_ema_return_decomposition.ipynb` ⭐ (NOUVEAU — priorité absolue)

**Objectif :** quantifier la part de la variance EMA expliquée par CBOT, EUR/USD et basis.

**Modèle central :**
```
EMA_return_1d = α + β₁ * CBOT_return_1d + β₂ * EURUSD_return_1d + β₃ * Δbasis_1d + ε_EU
              = partie_mondiale   + partie_change    + partie_basis   + résidu_EU
```

**Analyses :**

**Régression globale (OLS sur toute la période) :**
```python
import statsmodels.formula.api as smf
model = smf.ols('ema_return ~ cbot_eur_return + eurusd_return + basis_change', data=df).fit()
# → R², betas, t-stats, F-test
# → résidu = ema_residual_return_1d
```

**Régression rolling 260j :**
```python
# β₁, β₂, β₃ variables dans le temps
# Graphe : betas rolling 2014-2025
# Identifier : périodes de haute intégration vs découplage
# Saisonnalité des betas ? Crise 2022 change-t-elle les betas ?
```

**Régression par régime :**
```python
regimes = {
    'normal_2014_2017': ...,
    'drought_2018':     ...,
    'covid_2020':       ...,
    'ukraine_2022':     ...,
    'return_2023_2025': ...,
}
# Comparer R² et betas par régime
```

**Résultats attendus :**
```
R² global : 25-45% ?
  Part CBOT    : ~60-75% de la variance expliquée
  Part EUR/USD : ~10-20%
  Part Δbasis  : ~5-15%
  Résidu EU pur : ~25-40% de la variance totale

Betas attendus :
  β₁(CBOT) ≈ 0.5-0.8 (corrélation partielle forte)
  β₂(EURUSD) ≈ -0.3 à -0.5 (EUR fort → EMA baisse en €/t)
  β₃(basis) ≈ 0.3-0.6 (mean reversion)
```

**Outputs :**
- `artefacts/ema_study/ema_return_decomposition.json` — betas, R², variance décomposée
- Graphe betas rolling
- Table régimes × betas

---

### `06_ema_residual_study.ipynb` ⭐ (NOUVEAU — le cœur de l'étude Euronext)

**Objectif :** étudier et tenter de prédire le résidu EU pur — la partie d'EMA non expliquée par CBOT/EUR/USD.

C'est **le notebook le plus important de la Partie B**. Le résidu est ce que les données européennes doivent expliquer.

**Construction du résidu :**
```python
# Méthode 1 : OLS rolling (robuste, expanding window)
residual_ema = ema_return - (alpha_rolling + beta_cbot_rolling * cbot_return 
                              + beta_eurusd_rolling * eurusd_return)

# Méthode 2 : OLS global (simple mais moins robuste)
residual_ema_simple = model.resid

# Règle anti-leakage :
# Les betas sont calculés jusqu'à t-1, pas avec les données t→t+H
# expanding window min 60 jours pour avoir des betas stables
```

**Analyse descriptive du résidu :**
```python
# Distribution : normal ? fat tails ? (Jarque-Bera)
# Autocorrélation : Ljung-Box à lag 5, 10, 20
# Clustering de vol : ARCH test
# Grands résidus (>3σ) : à quoi correspondent-ils ?
# → Cataloguer les résidus extrêmes : sécheresse 2018, Ukraine 2022, ...
```

**Prédictibilité du résidu avec features EU :**
```python
# Cibles :
y_residual_up_h5  = int(sum(residual_ema, h=5)  > 0)
y_residual_up_h20 = int(sum(residual_ema, h=20) > 0)
y_residual_extreme_h20 = int(abs(sum(residual_ema, h=20)) > 1σ)

# Feature sets :
# EU_only    : EUR/USD, TTF gas, basis, EMA OI
# EU_extended : + EC MARS (si dispo), + Open-Meteo EU, + Ukraine proxy
# basis_residual : basis_z + basis_ar1_residual (résidu du résidu)

# Si DA(résidu) > DA(EMA brut) :
# → les variables EU apportent de l'info qui disparaît dans le bruit mondial
# → le résidu est un meilleur signal pour les données européennes
```

**Identification des "big EU shocks" dans le résidu :**
```python
# Quels événements correspondent aux résidus > 3σ ?
# → construire un catalogue EU shocks :
#   2018-07-XX : sécheresse EU → résidu ++
#   2022-02-24 : invasion Ukraine → résidu ++
#   202X-XX-XX : autre événement ?
# Ce catalogue sera réutilisé dans le notebook 09 (event study)
```

**Outputs :**
- `artefacts/ema_study/ema_residual_analysis.json` — stats résidu, DA résidu
- `artefacts/ema_study/eu_shocks_catalog.json` — catalogue des chocs EU
- Graphe résidu temporel avec annotation des événements

---

### `07_ema_basis_study.ipynb`

Voir §3 pour le détail complet des analyses.

**Résultats attendus :**
- Half-life du basis (attendu : 20-80 jours)
- Taux de reversion à H20 selon z-score initial (table 3×3 : basis_z < -2 / -2;+2 / > +2)
- Corrélation basis vs EUR/USD, TTF, Ukraine_flag
- Régimes de basis identifiés si possible

---

### `08_ema_direction_benchmark.ipynb`

**Objectif :** tester honnêtement la prédictibilité directionnelle EMA.

Protocole identique à R&D-01 CBOT :
- Walk-forward par crop year (min 3 ans train, 8 folds)
- IC95% bootstrap 1000 tirages
- Correction Benjamini-Hochberg
- DA quotidienne ET hebdomadaire
- DA par crop year

**Feature sets :**
| Set | Description |
|---|---|
| `cbot_only` | Features CBOT sélectionnées (R&D ablation) |
| `ema_technical_only` | Returns, momentum, RSI, BB — série adjusted |
| `basis_only` | basis + z-score + momentum + régime |
| `cbot_basis` | CBOT + basis |
| `cbot_ema_combined` | CBOT + EMA technique + basis |
| `cbot_eu_macro` | CBOT + EUR/USD + TTF + EC MARS si dispo |
| `all_selected` | Toutes les features sélectionnées par EXP-BENCH-01 |

**Cibles :**
| Cible | Série | Commentaire |
|---|---|---|
| `y_up_h20_ema_raw` | front_raw | Cible principale |
| `y_up_h20_ema_adjusted` | front_adjusted | Test sensibilité rolls |
| `y_up_h40_ema_noroll` | fenêtres sans roll | Contrôle qualité |
| `y_up_h20_ema_liquid` | liquid_raw | Alternative |
| `y_up_h20_basis_reversion` | `basis < basis_t` si basis_z > 1.5 | Spécifique basis |
| `y_up_h20_residual` | résidu après décomposition CBOT/EUR | Expérimental |

**Verdict pivot go/no-go (critères corrigés) :**
- go minimal : DA_mean > 0.55 AND AUC > 0.55 AND IC95_lo > 0.50
- go professionnel : IC95_lo > 0.55 AND DA_top20 > 0.62

---

### `09_ema_big_moves_event_study.ipynb`

**Objectif :** identifier les conditions précédant les grandes variations EMA.

**Événements étudiés :**
| Événement | Source | Fréquence |
|---|---|---|
| WASDE publication | USDA | Mensuel |
| EC MARS bulletin | Commission EU | Mensuel |
| Agreste / FranceAgriMer | MASA | Hebdo/Mensuel |
| Ukraine corridor status | Manuel / news | Ponctuel |
| Ukraine invasion | 2022-02-24 | Unique |
| Grande sécheresse EU | Proxy météo | Ponctuel |
| Forte variation CBOT > ±3% | CBOT data | Quotidien |
| Forte variation EUR/USD > ±1.5% | FX data | Quotidien |
| Basis extreme > ±2σ | Calculé | Quotidien |

**Cibles grands mouvements :**
```python
large_up_3pct_h20   = int(return_ema_h20 > +0.03)
large_down_3pct_h20 = int(return_ema_h20 < -0.03)
large_up_5pct_h40   = int(return_ema_h40 > +0.05)
large_down_5pct_h40 = int(return_ema_h40 < -0.05)
# triple barrier : premier à atteindre +3% ou -3% ou H20 sans barrière
```

**Event windows :**
- J-10 → J-1 avant l'événement
- J+1 → J+10 après l'événement
- Comparaison vs période normale (bootstrap)

**Outputs :**
- Table : event × retour moyen J+1 à J+20 avec IC95%
- Heatmap : matrice événement × amplitude retour
- Règles lisibles (decision tree max_depth=2)

---

### `10_ema_feature_importance.ipynb`

**Objectif :** identifier les variables qui comptent pour EMA.

**Familles de features testées :**
| Famille | Description | Hypothèse prédictive |
|---|---|---|
| CBOT market | prix CBOT, returns, momentum | Très forte |
| CBOT technical | RSI, BB, MA, volatilité | Modérée |
| WASDE world | stocks/use, surprise, révision | Forte (mensuel) |
| COT CFTC | positions MM, hedgers, percentile | Faible-modérée |
| US weather | GDD, drought, précipitations | Modérée (saison) |
| US crop condition | G+E%, silkage, phénologie | Faible-modérée |
| FAS exports | pace, accumulation, Chine pct | Modérée (saison) |
| EUR/USD | niveau, z-score, momentum | Forte |
| TTF gas | niveau, z-score | Faible-modérée |
| Basis | niveau, z-score, momentum | Attendu forte |
| EMA technical | returns, momentum, RSI | À tester |
| EMA rolls/liquidity | OI concentration, liquid_shift | Incertain |
| EU crop proxies | si EC MARS dispo | Attendu importante |
| world production | WASDE world balance | Forte |

**Méthodes :**
- Permutation importance (modèle histgb, walk-forward)
- SHAP values (si lgbm compatible)
- Ablation one-family-out (delta DA par retrait d'une famille)
- Ablation only-family (DA de chaque famille seule)
- Stabilité : importance par crop year (variance inter-années)

---

### `11_ema_european_fundamentals.ipynb`

**Objectif :** mesurer l'apport des données spécifiquement européennes.

**Données à tester progressivement :**

Priorité 0 (déjà présentes ou facilement ajoutables) :
- EUR/USD → déjà dans eu_cross_assets
- TTF gas → déjà dans eu_cross_assets

Priorité 1 (à collecter) :
- EC MARS bulletin mensuel : rendement maïs UE, anomalie stress hydrique, prévision récolte
  → Source : https://agri4cast.jrc.ec.europa.eu/DataPortal/
- FranceAgriMer : bilans céréaliers mensuels, collecte, exportations, stocks
  → Source : agreste.agriculture.gouv.fr + franceagrimer.fr
- Eurostat COMEXT : import/export maïs UE mensuel
  → Source : ec.europa.eu/eurostat/web/international-trade-in-goods/data
- Ukraine exports maïs : données MARS + UN FAO
  → Source : USDA PSD ou MARS Ukraine

Priorité 2 (à collecter) :
- Brésil CONAB : forecast production + safrinha progress (mars-juin)
- Argentine Bolsa de Comercio de Rosario : forecast annuel
- Chine : imports USDA PSD + Dalian corn (DCE via proxy)
- Black Sea FOB price : proxy freight/compétitivité (Bloomberg ou Reuters)

Priorité 3 (avancé) :
- Open-Meteo Europe : températures, précipitations, GDD maïs par zone
  Zones maïs EU : France SO, France CO, Italie N, Roumanie, Hongrie, Ukraine O
- NDVI/MODIS anomaly Europe (si accessible gratuitement)

**Pour chaque nouvelle source :**
1. Collecter et audit qualité
2. Aligner anti-leakage (date de publication réelle, pas date de référence)
3. Mesurer delta DA vs baseline CBOT seul
4. Si delta DA < +0.008 : NEUTRE, ne pas garder
5. Si delta DA ≥ +0.008 : PROMETTEUR, ajouter

---

### `12_ema_price_forecast_experimental.ipynb`

**Objectif :** tester les approches de prévision de prix avec IC.

**Statut :** EXPÉRIMENTAL — ne pas promettre de résultats fiables avant validation complète.

**Baselines à battre :**
```python
random_walk     : prix_t+H = prix_t              → RMSE référence
seasonal_naive  : prix_t+H = prix_{t-252}         → RMSE saisonnier
cbot_conversion : prix_t+H_ema = f(CBOT_t+H_conv) → meilleur baseline
ar1_basis       : modèle AR(1) sur basis + random walk prix → souvent très compétitif
```

**Modèles à tester :**
| Modèle | Type | Cible |
|---|---|---|
| Ridge regression | Linéaire | y_price_h60_ema |
| HistGBT quantile | Gradient boosting | Intervalles directs |
| Quantile regression linéaire | Linéaire | Intervalles |
| CQR split conformal | Post-hoc | Coverage garanti |
| CQR par régime | Adaptatif | Coverage par état de marché |
| CQR excluant 2021-2022 | Robustesse | Impact crise sur coverage |
| GARCH-M | Volatilité | Prix + volatilité |
| HAR (Heterogeneous Autoregression) | Réalised vol | Volatilité à H20/H40/H60 |

**Métriques :**
- RMSE vs baselines
- MAE vs baselines
- Coverage IC90% (objectif ≥ 88%)
- Winkler loss (coverage × width trade-off)
- CRPS (Continuous Ranked Probability Score) — métrique plus complète que RMSE

**Condition de passage en production :**
- Coverage IC90% ≥ 88% ET Winkler loss < random walk

---

### `13_ema_weekly_benchmark.ipynb` ⭐ (NOUVEAU)

**Objectif :** établir que les études doivent être menées en hebdomadaire, pas seulement en journalier.

**Problème :** beaucoup de features fondamentales (WASDE, EC MARS, COT) sont hebdomadaires ou mensuelles. En daily, on répète souvent la même information 5 jours consécutifs, ce qui gonfle artificiellement les statistiques de performance.

**Comparaison des fréquences d'échantillonnage :**
```python
# 4 versions du dataset :
daily_close     = toutes les clôtures journalières
weekly_friday   = un point par semaine (clôture vendredi)
weekly_monday   = un point par semaine (clôture lundi)
post_report     = un point par semaine le lendemain de la publication majeure

# Pour chaque fréquence, calculer :
# DA, AUC, IC95%, autocorrélation des prédictions
# Comparer sur le même modèle (histgb, features sélectionnées)
```

**Hypothèses à tester :**
```python
# H1 : DA weekly < DA daily (effet autocorrélation daily gonflé)
# H2 : AUC weekly ≈ AUC daily (même information, moins de répétition)
# H3 : Autocorrélation prédictions daily > 0.80 (signal répété)
# H4 : Weekly résout le problème d'autocorrélation
```

**Recommandation attendue :**
- Si DA hebdo > 0.53 ET AUC hebdo > 0.55 ET IC95 lo > 0.50 : fréquence validée pour usage hebdomadaire
- Si DA hebdo < 0.53 : signal trop faible même sans biais autocorrélation

**Benchmark spécifique "grands mouvements hebdomadaires" :**
```python
# Cibles hebdomadaires :
large_up_3pct_week   = int(return_ema_5d > +0.03)
large_down_3pct_week = int(return_ema_5d < -0.03)
large_up_5pct_2weeks = int(return_ema_10d > +0.05)

# Pourquoi ces cibles ?
# Prédit hausse >3% en semaine → beaucoup plus utile que DA global
# Ces événements rares ont plus d'intérêt pratique
```

**Outputs :**
- `artefacts/ema_study/weekly_sampling_benchmark.json`
- Table comparative : daily vs weekly × DA, AUC, autocorr

---

### `14_ema_synthesis_report.ipynb`

**Objectif :** synthèse lisible et défendable répondant aux 8 questions centrales.

**8 questions auxquelles le rapport doit répondre :**

1. **Le CBOT est-il prédictible ?**
   → Oui, modestement : DA 0.624, AUC 0.675, IC95 lo > 0.50. Signal réel.

2. **EMA est-il prédictible directement ?**
   → Non (NO_GO) : DA 0.467, IC95 [0.44, 0.49]. Benchmark walk-forward strict.

3. **EMA et CBOT sont-ils co-intégrés ?**
   → À établir : Engle-Granger / Johansen sur log-prix. Résultat attendu : oui.

4. **Qui mène qui : CBOT ou EMA ?**
   → Résultat surprenant (à confirmer) : EMA→CBOT Granger p=0.014. CBOT→EMA non sig.

5. **Le basis est-il stationnaire et mean-reverting ?**
   → Mean reversion confirmée à 70% hit rate. ADF + AR(1) + half-life formels à produire.

6. **Qu'est-ce qui explique le résidu européen EMA ?**
   → À étudier via notebook 06. EC MARS, Open-Meteo EU, basis, TTF, Ukraine attendus.

7. **Quels événements précèdent les grandes variations EMA ?**
   → À étudier via notebook 09 + catalogue EU shocks (notebook 06).

8. **Quelles sont les limites de prédictibilité ?**
   → Données exploratoires, courbe incomplète (14.9%), rolls importants (9.7 €/t), CQR NO_GO.

Structure :
1. Ce que le CBOT explique (résultats Phase R&D)
2. Comment EMA se relie au CBOT (corrélation, cointegration, lead-lag)
3. Ce que le basis encode (mean reversion, drivers)
4. Décomposition du retour EMA (R², betas, résidu EU)
5. Ce que les modèles prédisent (honnêtement)
6. Ce qu'ils ne prédisent pas (limites)
7. Ce qu'il faut ajouter comme données (roadmap)
8. Conclusion : prédictibilité EMA vs CBOT

---

## 6. Les 10 expériences prioritaires

### EXP-01 : Décomposition du retour EMA (fondamentale)

```
Régression rolling 260j :
EMA_return_1d ~ CBOT_return_1d + EURUSD_return_1d + Δbasis_1d

Résultats attendus :
  R² moyen ≈ 25-45% ?
  Part CBOT : ~60-75%
  Part EUR/USD : ~10-20%
  Part basis : ~5-15%
  Résidu EU pur : ~25-40%
  
  Variabilité temporelle des betas (à graphiquer)
  Régimes de haute / basse intégration
```

### EXP-02 : Basis mean reversion quantifiée

```
Half-life = -log(2) / log(rho) où rho = AR(1) coeff sur basis
Test ADF sur basis (stationnarité)
Table hit_rate selon z-score :
  z < -2 : P(basis hausse dans 20j) = ?
  z > +2 : P(basis baisse dans 20j) = ?
```

### EXP-03 : Benchmark directionnel EMA propre

Voir §5 notebook 06. Objectif : DA walk-forward crop year avec IC95% et correction BH. Verdict go/no-go.

### EXP-04 : Roll-aware targets

```
Pour H ∈ {20, 40, 60} :
  y_raw    = (price_t+H_raw - price_t_raw) / price_t_raw > 0
  y_adj    = (price_t+H_adj - price_t_adj) / price_t_adj > 0
  y_noroll = seulement les fenêtres sans roll intermédiaire
  
Comparer DA sur les 3 versions → quantifier le biais de roll
Si DA(y_adj) - DA(y_raw) > 0.02 : les rolls biaisent la cible
```

### EXP-05 : Basis comme prédicteur directionnel

```
Benchmark dédié basis :
  Features : basis seul
  Features : basis + EUR/USD
  Features : basis + CBOT
  Features : basis + CBOT + EUR/USD

Cibles : y_up_h20_ema, y_basis_reversion_h20, y_residual_up_h20

→ Le basis seul est-il prédictif (DA > 0.52, AUC > 0.54) ?
```

### EXP-06 : Test artefact — EMA features aident CBOT

Résultat inattendu : features EMA aident à prédire CBOT. Vérifier :
```
Hypothèse artefact :
  EMA features = proxy CBOT (même information reformatée)
  
Test :
  1. EMA features SANS cbot_eur_t (retirer la composante CBOT directe)
  2. EMA technical features uniquement (returns adjusted, RSI, momentum)
  3. EMA liquidity uniquement (OI, volume, liquid_shift)
  4. basis uniquement (sans composante CBOT brute)
  5. Chaque groupe avec shift(2) au lieu de shift(1) (extra délai)
  
Si DA tombe proche de 0.50 avec shift(2) → probablement un artefact de timing
Si DA reste > 0.55 → vraie information européenne
```

### EXP-07 : Analyse par régimes historiques

```
Régimes identifiés :
  2010-2013 : période normale, stocks tendus
  2014-2017 : surabondance, prix bas
  2018      : sécheresse Europe (cas unique)
  2019      : normal
  2020      : Covid choc puis rebond
  2021-2022 : inflation + Ukraine (crise extrême)
  2023-2025 : retour progressif à la normale

Pour chaque régime :
  corrélation EMA/CBOT (rolling ou par bloc)
  basis moyen et volatilité
  DA directionnelle EMA
  importance des variables
  taux de hit basis reversion
  
Objectif : identifier si le modèle tient en dehors des crises
```

### EXP-08 : Event study complet

Voir §5 notebook 07. Pour chaque type d'événement, mesurer le retour moyen EMA J+1 à J+20 avec IC95% bootstrap.

Ajouter :
```
Event clustering :
  Quand plusieurs événements se superposent dans la même fenêtre,
  quelle est la réaction cumulée vs individuelle ?
  
Asymétrie haussière/baissière :
  Les grands événements baissiers sont-ils plus brusques que les haussiers ?
  (souvent oui sur les marchés agricoles : "going up by stairs, down by elevator")
```

### EXP-09 : Prévision volatilité EMA

La volatilité du maïs est parfois plus prévisible que la direction.
```
Cibles :
  ema_vol_realized_20d     = std(ema_return_1d, 20j) * sqrt(252)
  ema_vol_relative_h20     = std(ema_return sur 20j suivants)
  ema_vol_regime           = haute / normale / basse (quantiles)

Modèles :
  HAR (Heterogeneous Autoregression) :
    vol_t = c + β₁*vol_{t-1} + β₂*vol_weekly + β₃*vol_monthly + ε
  GARCH(1,1)
  HistGBT sur lag features vol

Métriques :
  Qlike (log loss asymétrique)
  MSE sur vol
  Rank correlation (Diebold-Mariano test)
  
Pourquoi c'est utile :
  - Dimension "risque" de l'indicateur
  - Signal de prudence marché
  - Pondération du signal directionnel par vol
```

### EXP-10 : Cross-market lead-lag rigoureux

```
VAR(p) sur returns quotidiens :
  Y = [EMA_return, CBOT_return, EURUSD_return, basis_change]
  Sélection ordre p par AIC/BIC

Tests Granger :
  H0: CBOT ne Granger-cause pas EMA → à rejeter (attendu)
  H0: EMA ne Granger-cause pas CBOT → ? (à tester)
  H0: basis ne Granger-cause ni CBOT ni EMA → probable

Impulse Response Functions :
  Choc 1σ CBOT → IRF sur EMA (combien de jours pour absorber ?)
  Choc 1σ EMA → IRF sur CBOT
  Choc 1σ basis → IRF sur EMA

FEVD (Forecast Error Variance Decomposition) :
  À horizon H20 : quelle part de la variance EMA est due à CBOT vs propre EMA ?
```

---

## 7. Données à récupérer — feuille de route

### Priorité 0 — Données de base (toutes DONE)

| Donnée | Statut | Note |
|---|---|---|
| EMA contrats Barchart 2010-2026 | ✅ DONE | 4 818 lignes, proxy exploratoire |
| EMA séries continues (front/liquid/harvest_nov) | ✅ DONE | 3 377 lignes |
| EMA features courbe (28 features + basis) | ✅ DONE | 3 868 dates |
| EUR/USD (yfinance) | ✅ DONE | 5 827 lignes |
| TTF gas (yfinance) | ✅ DONE | 2 155 lignes |
| CBOT maïs (database.parquet) | ✅ DONE | — |
| WASDE world | ✅ DONE | — |
| COT CFTC | ✅ DONE | — |
| US crop condition | ✅ DONE | — |
| FAS export sales | ✅ DONE (code) | Clé API FAS_API_KEY requise |
| ENSO ONI | ✅ DONE | — |

### Priorité 1 — Europe (à créer)

| Donnée | Source | Collecteur à créer | Impact attendu |
|---|---|---|---|
| EC MARS monthly bulletin | JRC Agri4cast API | `src/mais/collect/ec_mars.py` | Fort (rendements EU) |
| FranceAgriMer bilans | franceagrimer.fr | `src/mais/collect/franceagrimer.py` | Moyen (France) |
| Agreste (culture + récolte) | agreste.agriculture.gouv.fr | `src/mais/collect/agreste.py` | Moyen (France) |
| Eurostat COMEXT | ec.europa.eu/eurostat | `src/mais/collect/eurostat_trade.py` | Faible-moyen |

### Priorité 2 — Monde influençant Euronext

| Donnée | Source | Collecteur | Impact attendu |
|---|---|---|---|
| Brésil CONAB | conab.gov.br | `src/mais/collect/conab.py` | Moyen-fort (mars-juin) |
| Ukraine production/exports | USDA PSD | Extension `usda_psd.py` | Fort (2022+) |
| Chine imports | USDA PSD / Dalian | Extension + DCE proxy | Moyen |
| Black Sea FOB price | USDA AMS | `src/mais/collect/fob_prices.py` | Moyen (logistics) |
| Argentine Bolsa | bcr.com.ar | `src/mais/collect/bolsa_rosario.py` | Moyen (janv-mars) |

### Priorité 3 — Météo Europe

| Donnée | Source | API | Impact attendu |
|---|---|---|---|
| Open-Meteo EU zones maïs | open-meteo.com | REST gratuit | Fort (saison mai-oct) |
| Précipitations FR/IT/RO/HU | Open-Meteo | idem | Fort |
| GDD maïs EU zones | Open-Meteo → calculé | idem | Fort |
| Jours > 32°C / > 35°C | Open-Meteo → calculé | idem | Fort (stress thermique) |
| Déficit hydrique SPEI | SPEI Global Database | Fichiers netCDF | Moyen |

Zones maïs EU à couvrir :
- France Sud-Ouest (Gers, Landes, Hautes-Pyrénées) : coord ~43.5°N, 0°E
- France Centre-Ouest (Charente, Vienne, Deux-Sèvres) : ~46°N, 0°E
- Italie du Nord (Plaine du Pô) : ~45°N, 11°E
- Roumanie (Valachie, Moldavie) : ~44.5°N, 26°E
- Hongrie : ~47°N, 19°E
- Ukraine Ouest (Vinnytsia, Khmelnytski) : ~49°N, 28°E
- Pologne (Silésie, Mazovie) : ~52°N, 20°E

---

## 8. Tests statistiques à inclure dans l'étude

### 8.1 Tests de base sur les séries

```python
# Pour chaque série (prix EMA, rendements, basis) :
adf_test          # stationnarité (prix : non-stationnaire attendu)
kpss_test         # confirmation stationnarité
jarque_bera       # normalité des rendements
ljung_box         # autocorrélation des rendements (lag 5, 20)
arch_test         # hétéroscédasticité (clustering de volatilité)
acf_pacf          # identification lag structure
```

### 8.2 Tests relation EMA/CBOT

```python
engle_granger_coint     # cointegration EMA/CBOT en log-prix
johansen_trace          # nombre de vecteurs cointegrants
vecm_adjustment_speed   # vitesse alpha (qui s'ajuste ?)
granger_causality       # avec correction BH sur tous les couples
```

### 8.3 Tests sur le basis

```python
adf_on_basis            # basis stationnaire ? (I(0) attendu)
ar1_halflife            # -log(2)/log(rho)
threshold_ar_model      # STAR ou SETAR sur basis (régimes extrêmes)
```

### 8.4 Tests modèles prédictifs

```python
diebold_mariano         # comparaison RMSE entre modèles
model_confidence_set    # Hansen-Lunde-Timmermann (MCS) sur les modèles
dm_test_on_da           # DA du modèle vs baseline (avec IC bootstrap)
```

---

## 9. Nouvelles idées à explorer

### 9.1 Idée : résidu EMA comme meilleure cible

Hypothesis : la partie de EMA_return non expliquée par CBOT est plus prévisible que EMA_return brut, car elle est moins bruitée par les mouvements mondiaux.

```python
# Étape 1 : régresser ema_return ~ cbot_eur_return (fenêtre 260j expanding)
# Étape 2 : calculer le résidu
ema_residual = ema_return - beta_cbot_rolling * cbot_eur_return

# Étape 3 : essayer de prédire ema_residual avec features européennes
# Cibles : y_residual_up_h20, y_residual_extreme_h20

# Si DA(résidu) > DA(brut) : les variables EU apportent de l'information
# Même si DA est modeste, ça prouve que le signal EU existe
```

### 9.2 Idée : Markov Switching Model pour les régimes de basis

```python
# Modèle 2-états ou 3-états sur le basis
# État 1 : basis faible (EMA moins cher que CBOT → exports EU compétitifs)
# État 2 : basis normal
# État 3 : basis élevé (EMA plus cher → tension approvisionnement EU)

# Probabilités de transition entre états
# Features d'état au niveau macro

# Utilité : signal de contexte marché
# "Le marché est en régime tension européenne (état 3), probabilité 84%"
```

### 9.3 Idée : prédire le basis plutôt que le prix EMA

```python
# Cible alternative : basis_change_h20 > 0 (basis monte = EU se renchérit)
# ou : basis_z_future = basis_z_{t+20}

# Drivers attendus :
#   - EUR/USD (fort EUR → basis baisse)
#   - Ukraine corridor (fermé → basis monte)
#   - EC MARS rendement (mauvais → basis monte)
#   - CBOT_z (CBOT très haut → basis compressé par arbitrage)
```

### 9.4 Idée : indicateur de synchronisation EMA/CBOT

```python
# Quand EMA et CBOT divergent beaucoup, quel marché "a tort" ?
sync_score = rolling_correlation_20d(ema_return, cbot_eur_return)
# sync_score > 0.80 : marchés synchronisés (CBOT pilote)
# sync_score < 0.40 : marchés découplés (information européenne locale)

# Signal de trading potentiel :
# Si désynchronisation ET basis extrême → fort signal de retour à la moyenne
```

### 9.5 Idée : analyse de la "transmission de chocs"

Quand CBOT fait un grand mouvement (> ±3%), combien de temps met EMA pour l'incorporer ?
```python
# Event window : jour CBOT ≥ ±3%
# Mesurer EMA J+0, J+1, J+2, J+3, J+5
# Comparer par régime de synchronisation (sync_score élevé vs bas)
# → Mesure de la vitesse de transmission

# Si EMA absorbe en J+1 : marchés très intégrés
# Si EMA absorbe en J+3 : friction, possible opportunité d'arbitrage
```

### 9.6 Idée : benchmark "constant maturity"

Plutôt que le front contract, utiliser un contrat à maturité constante (interpolé) :
```python
price_30d  = interpolation(front, next1, target_dte=30)
price_90d  = interpolation(front, next1, next2, target_dte=90)
price_180d = interpolation(...)
```

Avantage : pas d'artefact de roll. Compare des prix de même maturité.
Test : la série constant maturity donne-t-elle un meilleur signal directionnel ?

### 9.7 Idée : intégrer l'information intraday

Pour Euronext EMA, les prix intraday (bid/ask) peuvent indiquer :
- la liquidité instantanée
- la direction à très court terme (imbalance bid/ask)
- les conditions d'ouverture vs clôture

```python
ema_open_close_return = (settlement - open) / open
ema_intraday_vol      = (high - low) / ((high + low) / 2)
ema_gap_previous_day  = (open_t - settlement_{t-1}) / settlement_{t-1}
```

Ces features de microstructure sont disponibles si on collecte open/high/low dans le snapshot.

### 9.8 Idée : comparaison EMA avec autres grains EU

Euronext cote aussi :
- Blé meunier (BL, EBWT) — lien avec rotation culturale
- Orge (BO, EBRY) — compétition fourrages
- Colza (ECO) — pression alternative

```python
# Features ratio :
ema_wheat_spread = prix_ble_eur_t - prix_ema_eur_t
ema_corn_wheat_ratio = ema_price / wheat_price
# → signal de substitution alimentation animale
# → signal de rotation culturale pour l'année suivante
```

### 9.9 Idée : EMA comme leading indicator de CBOT (si Granger confirmé)

Le résultat Granger EMA→CBOT (p=0.0144, lag 1) suggère que EMA contient de l'information sur les futurs mouvements CBOT. Si validé OOF :

```python
# Feature supplémentaire dans le modèle CBOT :
ema_return_lag1          = ema_front_return.shift(1)
basis_change_lag1        = basis_change.shift(1)
ema_oi_change_lag1       = ema_oi_change.shift(1)

# Test :
# DA(CBOT y_up_h20) avec vs sans ema_return_lag1
# Si delta DA > +0.005 et OOF strict : le signal est réel

# Extension — "EMA sentiment composite pour CBOT" :
ema_cbot_leading_score = (
    0.5 * ema_return_lag1_z
    + 0.3 * basis_change_lag1_z
    + 0.2 * ema_oi_change_lag1_z
)
# Interpret : état du marché EU transmissible à CBOT le lendemain
```

**Attention :** ce signal peut disparaître OOF car le Granger marginal (p=0.014) est proche du seuil. Tester en sous-périodes avant d'incorporer.

### 9.10 Idée : formaliser le signal de basis arbitrage

La mean reversion est quantifiée (70% hit rate à H20, 7.64 €/t moyen pour high basis). Construire un backtest paper formel :

```python
# Signal de basis trade :
basis_signal = 0
if basis_z > +2.0:
    basis_signal = -1   # EMA va sous-performer CBOT (compression attendue)
elif basis_z < -2.0:
    basis_signal = +1   # EMA va sur-performer CBOT (expansion attendue)

# Retour de la stratégie :
return_basis_trade = basis_signal_t * (basis_{t+20} - basis_t)

# Métriques du backtest :
# - Hit rate à H20 / H40
# - Gain moyen par trade (brut et net)
# - Max drawdown
# - Sharpe ratio annualisé
# - Robustesse par sous-période (2014-2018 / 2019-2022 / 2023+)
# - Avec coûts de transaction simulés : 2 × 0.30 €/t = 0.60 €/t par trade

# Baseline à battre :
# always_neutral : return = 0
# always_long_ema : return = ema_return_h20
# random_signal : shuffled basis_signal
```

**Hypothesis économique :** le basis revient à la moyenne car les opérateurs physiques arbitrent les écarts EMA/CBOT (acheter/vendre physique + couvrir en futures). La vitesse de retour (half-life ~30 jours ?) limite le délai d'exploitation.

### 9.11 Idée : régimes de corrélation et périodes de découplage

La corrélation quotidienne EMA/CBOT varie dans le temps. Identifier et exploiter ces régimes :

```python
# Corrélation rolling 60j sur returns :
corr_60d = ema_return.rolling(60).corr(cbot_return)

# Seuils de régime :
# HIGH SYNC   : corr_60d > 0.60 → EMA suit CBOT, pas d'information propre
# MEDIUM SYNC : corr_60d ∈ [0.30, 0.60] → EMA partiellement autonome
# LOW SYNC    : corr_60d < 0.30 → marchés découplés, information EU locale

# Question clé :
# Le signal basis (DA=0.58) est-il concentré dans les périodes LOW SYNC ?
# Si oui : le basis est le meilleur signal précisément quand EMA est autonome

# Applications :
# - Feature "sync_regime" dans les modèles
# - Sélection du modèle à utiliser selon le régime de synchronisation
# - Alerte sur les périodes de découplage prolongé (choc EU potentiel)
```

### 9.12 Idée : décomposition STL (Seasonal-Trend decomposition using LOESS)

```python
# Application aux 3 séries principales :
from statsmodels.tsa.seasonal import STL

# Series à décomposer :
# - ema_front_adjusted : tendance long terme + saisonnalité annuelle + résidu
# - basis : saisonnalité du basis (pic pré-récolte, creux post-récolte ?)
# - ema_oi_total : cycles de liquidité par campagne

# Paramètres STL :
stl = STL(series, period=252, robust=True)  # 252 jours = 1 an
result = stl.fit()
trend, seasonal, residual = result.trend, result.seasonal, result.resid

# Utilité :
# 1. Détrending : travailler sur le résidu "pure surprise" → moins autocorrélé
# 2. Saisonnalité du basis : pic avant récolte EU (sept-oct) ? creux après ?
# 3. Prédiction saisonnière simple : "en octobre, le basis baisse typiquement de X €/t"

# Extension :
# MSTL (Multiple STL) avec période hebdo + annuelle pour capturer les 2 cycles
```

### 9.13 Idée : score composite multi-signal EMA

Combiner les signaux EMA identifiés en un seul score synthétique calibré :

```python
# Composantes validées ou prometteuses :
score_ema_composite = (
    w1 * basis_mean_reversion_score   # -basis_z (70% hit rate confirmé)
    + w2 * (-sync_score_z)            # découplage = plus de signal propre
    + w3 * ema_vol_regime_signal      # vol faible → signal plus stable
    + w4 * ema_oi_change_z            # OI monte → liquidité = intérêt institutionnel
    + w5 * granger_signal_lag1        # EMA leading CBOT (si validé)
)

# Calibration :
# Poids par régression logistique walk-forward sur y_up_h20_ema
# Évaluation : DA par décile du score composite
# Objectif : les déciles extrêmes (1 et 10) doivent avoir DA > 0.60

# Avantage vs modèle ML direct :
# Plus interprétable, moins sujet à l'overfitting
# Chaque composante est économiquement justifiée
```

### 9.14 Idée : prix du carbone EU (ETS) comme variable d'état

Le prix du CO₂ EU (Emissions Trading System) influence les coûts de production agricole en Europe via les engrais et l'énergie.

```python
# Source : EEX European Energy Exchange, données quotidiennes
# Ticker yfinance : CO2.EEX ou via commodity databases
# Alternative : Ember Climate Data (gratuit)

# Hypothèse :
# ETS > 80 €/tCO2 → coûts production EU élevés → basis monte
# ETS < 25 €/tCO2 → coûts production EU faibles → basis stable

# Features à créer :
ets_log_price    = log(co2_ets_price)
ets_zscore_52w   = expanding_zscore(ets_log_price, min_periods=52)
ets_yoy_change   = pct_change(ets_log_price, 252)
ets_x_fertilizer = ets_zscore * natural_gas_zscore  # interaction énergie × intrants

# Contexte 2022 particulièrement révélateur :
# ETS > 80 €/tCO2 + TTF gas > 300 €/MWh → basis EMA très élevé (prime EU coûts)
# Ce signal n'est pas capturé par WASDE/COT/météo US
```

### 9.15 Idée : calibration par régime du CQR prix

Le CQR prix EMA échoue globalement (coverage 79% vs 88% requis). Mais peut-être passe-t-il dans certains régimes ?

```python
# Stratégie : CQR conditionnel au régime de marché
# Régimes :
#   - Période basse volatilité (2014-2019 hors 2018)
#   - Période haute volatilité (2020, 2021-2022)
#   - Sécheresse EU (2018, 2022 partiel)

# Test :
# CQR calibré séparément sur chaque régime
# Coverage vérifié in-regime (pas globalement)
# Si coverage > 88% en basse vol, < 80% en haute vol :
# → CQR conditionnel au régime = acceptable pour usage en période stable

# Extension : CQR avec feature d'incertitude
# Wider intervals automatiques quand : VIX élevé, basis instable, données EMA sparse
# Utiliser la densité de courbe EMA comme proxy d'incertitude locale

# Métrique alternative :
# CRPS (Continuous Ranked Probability Score) au lieu de coverage uniquement
# Le CRPS pénalise les distributions trop larges ET trop étroites
# → Meilleure métrique pour évaluer la qualité globale des intervalles
```

---

## 10. Corrections à apporter aux documents existants

### 10.1 Objectif du projet

**Avant :** "Créer un indicateur opérationnel pour agriculteurs"  
**Après :** "Mener une étude statistique et économique complète du cours du maïs CBOT et Euronext"

Fichiers à mettre à jour : `README.md`, `CLAUDE.md`, `STATE.md`

### 10.2 Stockage sorti du périmètre principal

Modules à garder en archive (pas supprimer) :
- `src/mais/research/storage_targets.py`
- `src/mais/research/farmer_backtest_v2.py`
- `src/mais/indicator/module_a_context.py`
- `src/mais/ops/weekly_report.py`

Ces fichiers représentent du travail réel. Les archiver dans `src/mais/research/archive/` et ne plus les inclure dans le pipeline quotidien.

### 10.3 Formulations à corriger dans les notebooks

- Remplacer "signal de trading" par "signal de marché"
- Remplacer "recommandation STOCKER/VENDRE" par "indication de tension/décontraction"
- Remplacer "indicateur agriculteur" par "lecture de marché Euronext"
- Ajouter disclaimer sur toute prévision : "Résultat expérimental, non validé en production"

### 10.4 Tickets TICKETS_RD.md

Tickets à conserver tels quels (logique d'étude) :
- DATA-* : tous valides (infrastructure)
- EXP-BENCH-* : tous valides (benchmark)
- MODEL-DIR-01, MODEL-CQR-01 : valides comme outils d'étude
- MOD-B-01/02 (event study) : valides

Tickets à reformuler (scope réduit) :
- MODEL-STOR-01 → renommer "EXP-STOR-01 : étude expérimentale stockage"
- MODEL-CONF-01 → garder mais reformuler comme outil d'étude
- MOD-A-01/02 → reformuler comme "dashboard de contexte", pas "indicateur"
- OPS-REPORT-01 → "rapport de synthèse hebdomadaire EMA", pas "recommandation agriculteur"
- VAL-BACKTEST-01 → "backtest économique exploratoire"

---

## 11. Roadmap de l'étude

### Phase A — Nettoyage et fondations ✅ DONE (2026-05-20)
1. ~~DATA-EMA-09 : valider Barchart expired contracts~~ **DONE**
2. ~~DATA-EMA-02 : backfill historique~~ **DONE** — 4 818 lignes, source proxy exploratoire
3. ~~DATA-EMA-03 : séries continues~~ **DONE** — front/liquid/harvest_nov/curve
4. ~~DATA-EMA-08 : roll audit~~ **DONE** — verdict WARN, gap moyen 9.7 €/t
5. ~~DATA-EMA-04 : features courbe EMA~~ **DONE** — 28 features laggées, 3 868 dates
6. ~~DATA-MASTER-01 : dataset master EMA+CBOT~~ **DONE** — (6 192, 371), 37 colonnes EMA

### Phase B — Études fondamentales ✅ DONE (2026-05-21)
7. ~~EXP-EMA-STUDY-01 : data audit~~ **DONE** — 4 818 lignes, 14.9% dates avec ≥2 contrats
8. ~~EXP-EMA-STUDY-02 : lead-lag EMA/CBOT~~ **DONE** — Granger EMA→CBOT p=0.014
9. ~~EXP-EMA-STUDY-03 : basis mean reversion~~ **DONE** — 70% hit rate, half-life ~30j estimé
10. ~~EXP-EMA-ROLL-TARGET-01 : roll-aware targets~~ **DONE** — roll target hypothesis REJECTED
11. ~~EXP-EMA-CURVE-TRUE-01 : signal courbe réel~~ **DONE** — BASIS_DRIVEN_SIGNAL confirmé

### Phase C — Benchmark directionnel ✅ DONE (2026-05-20/21)
12. ~~EXP-BENCH-01 : sélection features~~ **DONE** — 50 features, 5 EMA, AUC 0.6389
13. ~~VAL-EMA-01 : proxy vs réel~~ **DONE** — PROXY_FORBIDDEN (MAE 37 €/t)
14. ~~EXP-BENCH-02 : benchmark EMA~~ **DONE** — NO_GO direction EMA, signal CBOT fort
15. ~~EXP-BENCH-03 : ablation familles~~ **DONE** — basis_cbot +0.083 DA
16. ~~EXP-BENCH-04 : benchmark stockage~~ **DONE** — STORAGE_NO_GO
17. ~~VAL-EMA-02 : benchmark hebdo~~ **DONE** — ema_curve_only→CBOT DA hebdo 0.619
18. ~~MOD-A-01 : Module A contexte~~ **DONE** — DA hebdo EMA 0.578 (passe seuil)
19. ~~MOD-A-02 : calibration poids~~ **DONE** — poids stables, gain marginal
20. ~~EXP-EMA-STUDY-04 : étude stockage~~ **DONE** — STORAGE_ECONOMIC_NO_GO
21. ~~EXP-EMA-STUDY-05 : data status Module A~~ **DONE** — 4 real, 5 proxy, 2 missing
22. ~~EXP-EMA-STUDY-06 : CQR prix EMA~~ **DONE** — CQR_PRICE_NO_GO (79% coverage)
23. ~~EXP-EMA-STUDY-07 : synthèse finale~~ **DONE** — verdict: garder CBOT moteur, EMA basis

### Phase D — Enrichissement données EU 🔄 À FAIRE
24. Collecteur EC MARS (JRC Agri4cast) → delta DA sur CBOT et résidu EMA
25. Collecteur Open-Meteo EU : 7 zones maïs EU (GDD, stress hydrique)
26. ETS CO2 EU (§9.14) : variable d'état coûts production
27. FranceAgriMer / Agreste : bilans céréaliers mensuels
28. Extension CONAB Brésil : forecast safrinha mars-juin
29. EXP-EU-FUNDAMENTALS : tester delta DA de chaque source EU

### Phase E — Études avancées 🔄 PRIORITAIRE
30. **Validation Granger EMA→CBOT** (§15) : OOF strict + sous-périodes + neutralisation EUR/USD
31. **Backtest basis arbitrage** (§9.10) : signal formalisé, hit rate, Sharpe
32. **Corrélation rolling et régimes** (§9.11) : LOW SYNC = meilleur signal ?
33. **STL decomposition** (§9.12) : saisonnalité basis, résidu pure
34. **Score composite EMA** (§9.13) : calibration walk-forward
35. EXP-09 : prévision volatilité EMA (HAR/GARCH) — réalisée vol plus prévisible que direction ?
36. EXP-10 : VAR/VECM/FEVD rigoureux — impulse response CBOT → EMA
37. Notebook `07_ema_big_moves_event_study` : conditions pré-grande variation

### Phase F — Rapport final
38. Notebook `11_ema_synthesis_report`
39. Document `docs/ETUDE_MAIS_CBOT_EURONEXT_FINAL.md`

---

## 12. Questions ouvertes (à trancher au fil de l'étude)

| Question | Hypothèse actuelle | Statut | Résultat |
|---|---|---|---|
| EMA est-il cointegré avec CBOT ? | Oui (fort) | ⚠ Partiel | Corrélation 0.94, Granger asymétrique confirmé. Engle-Granger/Johansen pas encore fait. |
| Quel est le half-life du basis ? | 20-80 jours | ⚠ Estimé | ~30j estimé. ADF + AR(1) formel pas encore calculé. |
| EMA est-il directionnellement prévisible ? | Faible | ✅ RÉPONDU | **NO_GO** : DA 0.4673, IC95 [0.44, 0.49] |
| Le basis est-il prédictif (seul) ? | Probablement oui | ✅ RÉPONDU | **OUI** : DA 0.5840, AUC 0.6336 sur CBOT y_up_h20 |
| Les features EMA sur CBOT sont-elles un artefact ? | Probable | ⚠ Non tranché | Granger p=0.014 suggère signal réel. À valider OOF (§15). |
| La sécheresse EU 2018 est-elle modélisable ? | Probablement oui | ❌ Non testé | Event study pas encore fait |
| EMA ou CBOT mène l'autre ? | CBOT mène EMA | ✅ RÉPONDU inversé | **EMA→CBOT significatif (p=0.014), CBOT→EMA non** |
| Le résidu EMA est-il prévisible ? | Inconnu | ❌ Non testé | EXP-01 non exécuté — prioritaire |
| La volatilité EMA est-elle prévisible ? | Probablement plus que direction | ❌ Non testé | EXP-09 non exécuté |
| Faut-il DTE 15 ou DTE 20 pour exclure ? | 15 jours (actuel) | ✅ Validé | 15j conservé, roll audit WARN mais invariant PASS |
| Le basis arbitrage est-il viable papier ? | Oui (70% hit rate) | ❌ Non backtesté | À formaliser (§9.10) |
| Le signal EMA améliore-t-il CBOT OOF ? | Inconnu | ❌ Non testé | Si Granger réel : delta DA à mesurer |
| Qu'explique le résidu EMA (non-CBOT) ? | Variables EU | ❌ Non testé | EXP-01 + données EU requises |
| La corrélation EMA/CBOT varie-t-elle ? | Oui, par régime | ❌ Non calculé | Rolling corr 60j à construire (§9.11) |

---

## 13. Critères de succès de l'étude (révisés)

L'étude sera considérée solide si :

**Sur la relation EMA/CBOT :**
- Cointegration EMA/CBOT confirmée ou infirmée avec test rigoureux
- Vitesse d'ajustement documentée (VECM)
- Part de variance EMA expliquée par CBOT quantifiée (R² décomposition)

**Sur le basis :**
- Stationnarité testée (ADF)
- Half-life mesuré
- Drivers du basis identifiés et quantifiés
- Mean reversion documentée avec probabilités par z-score

**Sur la prédiction directionnelle :**
- Benchmark walk-forward crop year avec IC95% et BH
- Verdict go/no-go documenté honnêtement
- Si NO GO : documenté sans chercher à tricher

**Sur les données européennes :**
- ≥ 2 sources EU collectées (EC MARS, Open-Meteo EU)
- Contribution mesurée en delta DA

**Sur la prévision prix :**
- Coverage IC90% mesuré
- Winkler loss vs random walk documenté
- Résultat honnête : si < 88% coverage, dire EXPÉRIMENTAL

---

## 14. Document de référence — liens vers les autres fichiers

| Document | Rôle | Statut |
|---|---|---|
| `.ai/REFLEXION_CONTRATS_EMA.md` | Logique de construction des séries EMA | Actif |
| `.ai/TICKETS_RD.md` | Tous les tickets Phase R&D et EXP | Actif |
| `.ai/STATE.md` | État d'avancement actuel | Actif |
| `docs/BENCHMARK_CANONICAL.md` | Résultats R&D-01 CBOT | Figé |
| `docs/PROTOCOL_FREEZE.md` | Protocole figé benchmark | Figé |
| `docs/EMA_DATA_AUDIT.md` | Audit données EMA (EXP-EMA-STUDY-01) | DONE |
| `docs/EMA_CBOT_RELATIONSHIP.md` | Lead-lag + Granger (EXP-EMA-STUDY-02) | DONE |
| `docs/EMA_BASIS_STUDY.md` | Mean reversion basis (EXP-EMA-STUDY-03) | DONE |
| `docs/EMA_FINAL_SYNTHESIS.md` | Synthèse finale Euronext (EXP-EMA-STUDY-07) | DONE |
| `artefacts/ema_study/` | Artefacts JSON des études EMA | Actif |
| `artefacts/benchmark_pivot/` | Benchmark EXP-BENCH-01 à 04 | DONE |
| `notebooks/corn_study/euronext/` | Notebooks EMA | À développer |

---

## 15. Découverte inattendue : EMA Granger-cause CBOT

### 15.1 Le résultat

EXP-EMA-STUDY-02 a produit un résultat contraire à la théorie classique :

```
Granger causality EMA → CBOT :  lag 1 : p-value = 0.0144  ← SIGNIFICATIF
                                 lag 2+ : non significatifs

Granger causality CBOT → EMA :  lag 1 : p-value = 0.1605  ← NON SIGNIFICATIF
```

**Narrative attendue :** CBOT est le référentiel mondial → EMA suit.  
**Résultat observé :** EMA mène CBOT d'un jour.

C'est l'une des trouvailles les plus importantes de l'étude. Elle inverse la hiérarchie marché supposée.

### 15.2 Interprétations possibles

**Hypothèse 1 : Differential de fuseaux horaires**

EMA (Euronext) cote de 10:45 à 18:30 CET.  
CBOT close habituel = 13:20 CET (session day), mais session électronique continue jusqu'à 18:00 CET.  
Le close EMA (18:30 CET) est postérieur au close CBOT électronique.  
Si on prend close-to-close en jours calendaires :
- EMA_{J close} incorpore des informations post-close CBOT
- Ces informations apparaissent dans CBOT_{J+1 open}
→ Granger apparent dû au décalage de fermeture.

**Hypothèse 2 : Price discovery EU → US**

Des informations spécifiques à l'Europe arrivent en matinée CET (avant le CBOT day session) :
- Données de récolte EU (Agreste, FranceAgriMer)
- News Black Sea / Ukraine corridor
- Tenders d'exportation EU
- EMA incorpore ces informations dans sa session de 10:45
- CBOT ne les intègre que dans sa session suivante (19:00 CET)
→ EMA est un vecteur de price discovery pour les facteurs EU influençant CBOT.

**Hypothèse 3 : Flux d'arbitrage**

Quand EMA dévie de CBOT (basis anormal), des opérateurs arbitrent en achetant/vendant simultanément sur les deux marchés. Ce flux d'arbitrage tire CBOT vers EMA, apparaissant comme une "causalité" EMA→CBOT.

**Hypothèse 4 : Artefact statistique marginal**

- p=0.0144 est proche du seuil 5%
- Sur ~3 000 observations, un faux positif reste possible
- La correction BH sur plusieurs tests pourrait le faire tomber
→ À confirmer avant exploitation.

### 15.3 Plan de validation rigoureux

```python
# Test 1 — Robustesse temporelle (priorité haute)
# Diviser en 3 sous-périodes :
#   2014-2017 (normal), 2018-2020 (sécheresse + covid), 2021-2025 (crise + retour)
# Tester Granger séparément dans chaque sous-période
# Critère robustesse : p < 0.05 dans ≥ 2/3 sous-périodes

# Test 2 — Robustesse au choix de lag
# Si p(lag1)=0.014 mais p(lag2,3,4,5)=non significatifs :
# Le signal est court (1 jour) — compatible avec timing ou arbitrage

# Test 3 — Neutralisation EUR/USD
# EMA et CBOT sont mécaniquement liés par EUR/USD
# Tester Granger sur les résidus après régression EMA_return ~ cbot_eur_return
# Si Granger disparaît → c'était la corrélation EUR/USD
# Si Granger persiste → signal propre EU

# Test 4 — Validation OOF (test ultime)
# Feature : ema_return_lag1 dans le modèle CBOT
# Évaluer DA(CBOT) avec vs sans ema_return_lag1 en walk-forward strict
# Si delta DA > +0.008 : signal réel exploitable
# Si delta DA ≈ 0 : Granger statistiquement significatif mais non exploitable

# Test 5 — Exclusion de la crise 2022
# 2022 a eu des chocs EU exceptionnels (Ukraine, énergie)
# Re-tester Granger sans 2022
# Si le signal disparaît → il était concentré dans la crise unique
```

### 15.4 Implications si validé

Si la Granger-causalité EMA→CBOT est confirmée hors-échantillon sur ≥ 2 sous-périodes et survit à la neutralisation EUR/USD :

1. **EMA comme leading indicator de CBOT** — la hiérarchie est inversée
2. **Feature ema_return_lag1 valide dans le modèle CBOT** — justifiée par test OOF strict
3. **Mécanisme de transmission EU→US documenté** — contribution scientifique potentielle
4. **Amélioration du modèle CBOT** — combien de points de DA ?
5. **Signal de contexte** : "le marché EU anticipe un mouvement US demain"

### 15.5 Implications si infirmé

Si le résultat ne tient pas OOF ou en sous-périodes :

1. **Conclusion honnête** : Granger statistiquement présent mais non exploitable
2. **Les features EMA aident CBOT** via le basis (information EU correctement shifté d'1 jour), pas via la causalité directe
3. **La corrélation est contemporaine**, pas prédictive à lag 1
4. **Ne pas sur-exploiter** — la règle est : si le signal ne passe pas OOF, il n'existe pas

### 15.6 Revue de littérature à consulter

Pour contextualiser ce résultat dans la littérature académique :

- Frey, Herbst, Walter (2015) : "Measuring feedback trading in crude oil markets" — asymétrie Granger dans les commodités
- Bekiros, Diks (2008) : lead-lag entre marchés futures — méthodes non-linéaires
- Joëts, Mignon, Razafindrabe (2015) : volatility spillovers entre marchés agricoles
- Rua (2013) : Granger causality avec correction pour tests multiples
- Papiers spécifiques maïs CBOT/Euronext : rechercher dans EconLit ou Google Scholar avec "corn CBOT Euronext Granger causality"

---

## 17. Ordre d'exécution — Plan de bataille P0 → P4

### P0 — Fondations (notebooks 00-04) — PRIORITÉ ABSOLUE

**Objectif :** poser les bases avant tout modèle. Aucune expérience prédictive sans ces 5 notebooks.

| Étape | Notebook | Produit | Statut |
|---|---|---|---|
| 1 | 00_ema_project_overview | Document de cadrage, graphiques EMA vs CBOT | À faire |
| 2 | 01_ema_data_audit | audit_summary.json, heatmap couverture | À faire (EXP-EMA-STUDY-01 DONE comme base) |
| 3 | 02_ema_contracts_and_rolls | roll_gaps distribution, % fenêtres traversées | À faire |
| 4 | 03_ema_continuous_series | Validation invariants, comparaison front/liquid | À faire |
| 5 | 04_ema_cbot_relationship | Cointegration, VAR, Granger rigoureux, rolling corr | À faire |

**Note :** EXP-EMA-STUDY-01 à 03 ont produit des artefacts JSON. Les notebooks P0 les visualisent et les approfondissent formellement (ADF, Engle-Granger, Johansen).

---

### P1 — Études statistiques lourdes (notebooks 05-07) — AVANT TOUT MODÈLE

**Objectif :** établir les faits statistiques fondamentaux sur lesquels tout le reste repose.

| Étape | Notebook | Produit | Découverte attendue |
|---|---|---|---|
| 6 | 05_ema_return_decomposition | R² décomposition, betas rolling, variance par composante | Part CBOT, EUR/USD, basis dans la variance EMA |
| 7 | 06_ema_residual_study | Résidu EU pur, catalogue EU shocks, DA résidu | Résidu EU > DA EMA brut ? |
| 8 | 07_ema_basis_study | ADF test, half-life AR(1), régimes HMM, drivers basis | Half-life mesuré, stationnarité confirmée |

**Condition de passage à P2 :** les trois questions fondamentales répondues :
- Part de variance EMA expliquée par CBOT (R² notebook 05)
- Stationnarité et half-life du basis (notebook 07)
- Granger EMA→CBOT validé ou infirmé (notebook 04)

---

### P2 — Études prédictives (notebooks 08-10, 12-13) — APRÈS P1

**Objectif :** tester les modèles prédictifs sur les bases construites en P0-P1.

| Étape | Notebook | Produit | Critère de succès |
|---|---|---|---|
| 9 | 08_ema_direction_benchmark | DA walk-forward + IC95% + BH, verdict go/no-go | DA > 0.55 ET AUC > 0.55 AND IC95_lo > 0.50 |
| 10 | 09_ema_big_moves_event_study | Table event × retour J+1-J+20, catalogue | Différence vs période normale significative |
| 11 | 10_ema_feature_importance | Ablation, permutation, SHAP, stabilité | Delta DA par famille |
| 12 | 12_ema_price_forecast_experimental | Coverage IC90%, Winkler, CRPS | Coverage > 88% (objectif actuel non atteint) |
| 13 | 13_ema_weekly_benchmark | Daily vs weekly × DA, AUC, autocorr | DA hebdo > 0.53 ET IC95_lo > 0.50 |

---

### P3 — Enrichissement données EU (notebook 11) — EN PARALLÈLE de P2

**Objectif :** ajouter les vraies données européennes une par une, mesurer delta DA.

| Priorité | Source | Collecteur | Mécanisme | Delta DA estimé |
|---|---|---|---|---|
| 1 | Open-Meteo EU (7 zones) | `src/mais/collect/openmeteo_eu.py` | GDD + stress hydrique + précip | Fort (saison) |
| 2 | EC MARS bulletin mensuel | `src/mais/collect/ec_mars.py` | Rendement UE, anomalie hydrique | Fort (mensuel) |
| 3 | ETS CO2 EU | Extension `eu_fundamentals_collector.py` | Coûts production EU | Moyen-fort |
| 4 | FranceAgriMer bilans | `src/mais/collect/franceagrimer.py` | Collecte, exports, stocks France | Moyen |
| 5 | Eurostat COMEXT | `src/mais/collect/eurostat_trade.py` | Imports/exports UE maïs | Faible-moyen |
| 6 | Ukraine USDA PSD | Extension WASDE collector | Production, exports Ukraine | Fort (2022+) |
| 7 | CONAB Brésil | `src/mais/collect/conab.py` | Safrinha (mars-juin) | Moyen-fort |
| 8 | Black Sea FOB | `src/mais/collect/fob_prices.py` | Compétitivité export | Moyen |

**Règle d'intégration :**
- Collecter → audit qualité → aligner anti-leakage → mesurer delta DA
- Si delta DA < +0.008 sur le **résidu EMA** (pas brut) : NEUTRE
- Si delta DA ≥ +0.008 sur résidu : PROMETTEUR, intégrer

---

### P4 — Rapport final (notebook 14)

**Objectif :** synthèse honnête et défendable. Pas avant P0-P3 terminés.

Répondre aux 8 questions de `14_ema_synthesis_report.ipynb` (voir §5).

Document de sortie : `docs/ETUDE_MAIS_CBOT_EURONEXT_FINAL.md`

---

## 18. Limites connues des données EMA (à documenter dans le rapport final)

Ce chapitre doit figurer dans le rapport final. C'est ce qui rend l'étude crédible.

### 18.1 Source exploratoire (Barchart proxy)

```
Source : Barchart.com scraping / proxy (non officiel)
Nature : OHLCV quotidien par contrat, pas settlement officiel Euronext
Couverture : 2010-2026, ~4818 lignes
Risque : prix de clôture Barchart ≠ prix de règlement Euronext officiel
         → les roll gaps peuvent être artificiels si la source est incohérente
Impact : roll audit WARN, gap moyen 9.7 €/t, max 54.25 €/t
```

**Conséquence :** tous les résultats sur données EMA doivent mentionner "source exploratoire Barchart proxy, non settlement officiel".

### 18.2 Courbe EMA quasi-inexistante

```
Seulement 14.9% des dates ont ≥ 2 contrats actifs simultanément
Spreads, carry, slope, slope6m : NaN sur ~85% des dates
→ Les features de courbe sont quasi inutilisables
→ Dire : "features EMA front, basis, liquidité et fragments de courbe"
   Pas : "courbe futures EMA complète"
```

### 18.3 Rolls importants sur les targets longues

```
Roll gap moyen : 9.7 €/t (front)
Roll gap max   : 54.25 €/t (2013-08-08)
% fenêtres H20 traversant un roll : 39.7%
% fenêtres H40 traversant un roll : 79.1%
% fenêtres H60 traversant un roll : 100%
→ Cible H60 brute inutilisable — doit être no-roll ou adjusted
→ Résultat EXP-EMA-ROLL-TARGET-01 : roll target hypothesis rejetée mais rolls restent un problème
```

### 18.4 Proxy CBOT interdit

```
MAE proxy vs EMA réel : 37.3 €/t
Spread absolu > 2σ sur 68.97% des jours
Corrélation : 0.9411 (niveau), mais 0.34 (rendements)
Verdict VAL-EMA-01 : PROXY_FORBIDDEN
→ Ne jamais présenter des résultats obtenus avec le proxy comme des résultats sur EMA réel
```

### 18.5 Settlement officiel manquant

```
Euronext publie les prix de règlement officiels des contrats
Ces prix ne sont pas dans notre dataset actuel
→ Les dividendes en cash, les variations de margin, les prix de livraison sont inconnus
→ L'historique 2010-2020 reste incomplet — Barchart couvre bien 2021+
→ Solution idéale : Euronext NextHistory ou Refinitiv/Bloomberg
```

### 18.6 Modules A : sources partiellement manquantes

```
Sources Module A status :
- real : 4 sources actives
- proxy : 5 sources (substituts imparfaits)
- missing : 2 sources (china_demand, export_pace_eu)
Couverture active moyenne : 55.5%
Poids principal wasde_surprise (DA hebdo 56.7%) mais proxy de toutes les variables EU
→ Le Module A contexte reste exploratoire tant que china_demand et export_pace_eu ne sont pas en source réelle
```

---

## 19. Table des claims et preuves

Chaque affirmation factuelle de l'étude doit être reliée à une preuve. Cette table assure l'honnêteté du rapport final.

| Claim | Statut | Source de preuve | Valeur | Réserve |
|---|---|---|---|---|
| CBOT a un signal directionnel modeste | **VALIDÉ** | R&D-01, IND-08 | DA 0.624 [IC95 > 0.50], AUC 0.675 | Walk-forward crop year 2015-2022 |
| EMA direct est peu prédictible | **VALIDÉ** | EXP-BENCH-02 | DA 0.4673, IC95 [0.44, 0.49], AUC 0.5026 | Source exploratoire |
| Basis mean-revert à ~70% à H20 | **VALIDÉ** | EXP-EMA-STUDY-03 | high basis 70.4%, low basis 68.0% | ADF et half-life formel pas encore calculés |
| Le basis est le meilleur signal EMA | **VALIDÉ** | EXP-BENCH-03 | delta DA basis_cbot +0.083, q=0.0000 | Sur cible CBOT, pas EMA |
| EMA Granger-cause CBOT | **PROMETTEUR** | EXP-EMA-STUDY-02 | p=0.0144 lag 1 | Non validé OOF — voir §15 |
| CQR EMA à 90% non fiable | **VALIDÉ** | EXP-EMA-STUDY-06 | Coverage 79.2% vs 88% requis | Basse vol peut passer |
| Courbe EMA complète exploitable | **REJETÉ** | EXP-EMA-STUDY-01 | 14.9% dates avec ≥ 2 contrats | EMA marché peu liquide |
| Proxy CBOT→EMA résultats utilisables | **REJETÉ** | VAL-EMA-01 | MAE 37.3 €/t, 69% dates > 2σ | PROXY_FORBIDDEN |
| Roll EMA biaise les targets longues | **VALIDÉ** | EXP-EMA-ROLL-TARGET-01 | 100% des fenêtres H60 | Roll target hypothesis rejetée mais rolls importants |
| Module A contexte EMA passe le seuil | **PROMETTEUR** | MOD-A-01 | DA hebdo 0.5778, 559 semaines | Sources proxy/missing |
| Features EMA aident la prédiction CBOT | **VALIDÉ** | EXP-BENCH-02, EXP-BENCH-03 | ema_curve_only DA 0.617, AUC 0.644 | À valider par sous-période |
| Stockage EMA non économiquement viable | **VALIDÉ** | EXP-EMA-STUDY-04 | oracle €8.66/t, meilleur modèle €0.005/t | Source exploratoire |
| EMA et CBOT sont co-intégrés | **ATTENDU** | — | Non encore testé | Engle-Granger/Johansen à faire (notebook 04) |
| Half-life du basis : 20-60 jours | **ESTIMÉ** | EXP-EMA-STUDY-03 | ~30j estimé | AR(1) formel pas encore calculé |
| Données EU améliorent le résidu EMA | **INCONNU** | — | Non encore testé | EC MARS, Open-Meteo EU, FranceAgriMer à collecter |

---

## 16. Actualisation des résultats — tableau synthèse (2026-05-21)

### Ce qu'on sait maintenant

| Domaine | Résultat | Confiance |
|---|---|---|
| Signal directionnel EMA primaire | NO_GO (DA 0.467) | ÉLEVÉE (IC95 confirmé) |
| Signal EMA sur cible CBOT | Fort (DA 0.617, AUC 0.644) | ÉLEVÉE (validé hebdo) |
| Basis mean reversion | CONFIRMÉ (70% hit rate, 7.64 €/t) | ÉLEVÉE |
| Granger EMA→CBOT | Significatif mais marginal (p=0.014) | FAIBLE (non validé OOF) |
| CQR prix EMA | NO_GO (79% coverage) | ÉLEVÉE |
| Stockage économique | NO_GO | ÉLEVÉE |
| Module A contexte | DA hebdo 57.8% (passe seuil) | MODÉRÉE |
| Proxy CBOT → EMA | INTERDIT (MAE 37 €/t) | ÉLEVÉE |
| Courbe EMA (spreads/carry) | Inutilisable (14.9% dates actives) | ÉLEVÉE |

### Ce qu'il faut encore faire

| Priorité | Expérience | Potentiel estimé |
|---|---|---|
| 🔴 Très haute | Validation Granger OOF (§15) | Signal CBOT +0.005-0.010 DA si réel |
| 🔴 Très haute | EXP-01 : décomposition résidu EMA | Comprendre la part EU dans EMA |
| 🔴 Très haute | Données EC MARS + Open-Meteo EU | Premier test delta DA européen |
| 🟠 Haute | Backtest basis arbitrage (§9.10) | Signal économique quantifié |
| 🟠 Haute | EXP-09 : volatilité EMA (HAR) | Vol plus prévisible que direction ? |
| 🟠 Haute | EXP-10 : VAR/VECM/FEVD rigoureux | Impulse response EMA ↔ CBOT |
| 🟡 Moyenne | STL decomposition (§9.12) | Saisonnalité basis |
| 🟡 Moyenne | Score composite EMA (§9.13) | Signal unificateur |
| 🟡 Moyenne | ETS CO2 EU (§9.14) | Variable d'état coûts EU |
| 🟢 Basse | Grains EU comparaison (§9.15) | Contextualisation MATIF/EMA |
