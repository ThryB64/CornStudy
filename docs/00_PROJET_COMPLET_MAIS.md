# Document Maître — Etude Maïs
> **Ce document est la seule source de vérité du projet.**
> Toutes les décisions, tous les tickets et toutes les expériences en découlent.
> Version 2.0 — 2026-05-14 (pivot indicateur directionnel)

---

## Table des matières

1. [Résumé exécutif](#1-résumé-exécutif)
2. [Vision et objectif](#2-vision-et-objectif)
3. [Pilier A — Plateforme AutoML](#3-pilier-a--plateforme-automl)
4. [Pilier B — Étude du marché du maïs](#4-pilier-b--étude-du-marché-du-maïs)
5. [Architecture cible du projet](#5-architecture-cible-du-projet)
6. [Sources de données](#6-sources-de-données)
7. [Cadre factoriel — 13 familles](#7-cadre-factoriel--13-familles)
8. [Cibles à tester — 7 niveaux](#8-cibles-à-tester--7-niveaux)
9. [Modèles à tester](#9-modèles-à-tester)
10. [Plan des notebooks (01–12)](#10-plan-des-notebooks-0112)
11. [Liste complète des expériences (EXP-001–018)](#11-liste-complète-des-expériences-exp-001018)
12. [Méthode de travail obligatoire](#12-méthode-de-travail-obligatoire)
13. [Roadmap par phases (0–7)](#13-roadmap-par-phases-07)
14. [Critères de réussite](#14-critères-de-réussite)
15. [État actuel du projet](#15-état-actuel-du-projet)
16. [Journal des expériences](#16-journal-des-expériences)
17. [Règles de vérité du projet](#17-règles-de-vérité-du-projet)
18. [Prochaines étapes immédiates](#18-prochaines-étapes-immédiates)

---

## 1. Résumé exécutif

### Ce qu'est le projet

Ce projet est structuré autour de deux piliers indissociables mais distincts.

**Pilier A — Plateforme AutoML de séries temporelles**
Un moteur générique capable de prendre n'importe quel fichier CSV, de détecter automatiquement le type de problème, de préparer les données, de sélectionner les modèles adaptés, de les optimiser via Optuna, de les évaluer en walk-forward ou cross-validation, de produire un métamodèle par stacking, et de générer un rapport complet avec explications SHAP.

**Pilier B — Étude professionnelle du marché du maïs CBOT**
L'application principale de la plateforme. Une étude économique complète et honnête du prix du maïs sur le marché de Chicago. Elle collecte des données de 10+ sources (marchés, météo, WASDE, NASS, FRED, CFTC, EIA, FAS), construit des facteurs synthétiques interprétables, teste toutes les cibles possibles, identifie quand et comment le marché est partiellement prévisible, et construit progressivement un indicateur directionnel robuste.

### L'objectif final en une phrase

> Construire une plateforme AutoML générique, l'appliquer au marché du maïs CBOT sur 15+ ans de données, identifier les facteurs et contextes où le signal est exploitable, et produire un indicateur directionnel **BULLISH / BEARISH / NEUTRAL / UNCERTAIN** avec probabilités, confiance et explication économique — qui sera ensuite la base d'un futur outil d'aide à la vente agricole.

### La philosophie en une phrase

> "On ne cherche pas seulement à prédire le prix du maïs. On cherche à identifier dans quelles conditions le marché donne un signal exploitable de hausse ou de baisse, avec quel niveau de confiance, à quel horizon, et avec quelles explications économiques."

### Ce que ce projet N'est PAS (encore)

- Ce n'est **pas** encore l'application agriculteur finale (Agricorn, SELL/STORE/WAIT direct).
- Ce n'est **pas** une promesse de capture à 90% du prix maximum annuel.
- Ce n'est **pas** un pipeline de prévision exacte du prix.

La couche agricole (recommandation de vente, coûts de stockage, stratégie) vient **après** que l'indicateur directionnel soit solide.

---

## 2. Vision et objectif

### 2.1 Les trois niveaux du projet

Le projet est organisé en trois niveaux hiérarchiques. Ils doivent rester séparés dans le code et dans la réflexion.

```
Niveau 1 — Étude du marché du maïs           ← PRIORITÉ ACTUELLE
│   Objectif : comprendre et prédire direction / risque / incertitude
│   Livrable : Maize Market Direction Indicator
│
Niveau 2 — Moteur AutoML                     ← SOCLE TECHNIQUE
│   Objectif : tester automatiquement modèles, cibles, features, Optuna, stacking
│   Livrable : plateforme générique réutilisable
│
Niveau 3 — Futur outil agriculteur            ← PERSPECTIVE FUTURE
    Objectif : transformer l'indicateur en recommandation de vente
    Livrable : SELL / STORE / WAIT avec justification
```

### 2.2 L'indicateur final visé — Maize Market Direction Indicator

L'indicateur ne prédit pas le prix exact. Il estime si le marché a plus de probabilité de monter, de baisser, d'être neutre ou d'être trop incertain.

```
Maize Market Direction Indicator — Exemple de sortie

Horizon J+5  : NEUTRAL / confidence 38%
Horizon J+10 : BULLISH modéré / confidence 54%
Horizon J+20 : BULLISH / confidence 67%
Horizon J+30 : UNCERTAIN / confidence 31%

Probabilités (J+20) :
  P(hausse)       : 63%
  P(baisse)       : 28%
  P(forte hausse) : 21%
  P(forte baisse) : 8%
  Retour attendu  : +1.8%

Facteurs haussiers principaux :
  1. WASDE stocks/use tightness (+++)
  2. Weather stress Corn Belt (++)
  3. COT positioning (nets longs) (+)

Facteurs baissiers principaux :
  1. Macro dollar strength (–)
  2. Export sales en retard (–)

Interprétation : Marché tendu côté offre, La Niña active, positionnement spéculatif
haussier. Signal modérément exploitable à J+20 mais incertain à J+30.
```

### 2.3 Questions de recherche centrales

Ces questions pilotent toute l'étude. Chaque expérience doit apporter un élément de réponse à au moins une d'elles.

1. **Le maïs est-il prévisible ?** À quel horizon le signal est-il le plus fort ?
2. **Quelles familles de données portent le signal ?** Météo, fondamentaux, spéculation, macro ?
3. **La direction est-elle plus prédictible que l'amplitude ?** y_up_h20 vs y_logret_h20 ?
4. **Le signal dépend-il du contexte ?** Saison, régime, période WASDE, conditions de stocks ?
5. **Quels drivers futurs expliqueraient le prix (analyse oracle) ?** Si on connaissait le futur, quoi ?
6. **Quand l'indicateur est-il fiable ?** Performance quand confiance > 60/70/80% ?

### 2.4 L'ambition portfolio et recherche

Ce projet démontre la maîtrise de :
- ingestion et nettoyage de données hétérogènes multi-sources
- construction de features anti-leakage sur séries temporelles
- walk-forward validation avec embargo
- stacking et méta-apprentissage
- calibration probabiliste (CQR, Platt, isotonic)
- modèles de régimes (Markov-switching, rule-based)
- explicabilité SHAP sur modèles d'ensemble
- backtest économique rigoureux
- analyse oracle pour diagnostiquer les limites du signal

---

## 3. Pilier A — Plateforme AutoML

### 3.0 AutoML V1 vs AutoML V2

**Distinction critique :** la plateforme a deux niveaux de maturité. L'étude maïs ne doit pas être bloquée par la généralisation complète.

| Version | Périmètre | Priorité |
|---|---|---|
| **AutoML V1** | Tout ce qui est nécessaire pour lancer les expériences EXP-001–018 sur les données maïs | Maintenant |
| **AutoML V2** | Généralisation à n'importe quel CSV avec détection automatique complète, tests sur 5+ datasets externes, interface CLI complète | Après Phase 5 |

L'objectif immédiat est AutoML V1 opérationnelle, pas une plateforme générique parfaite.

### 3.1 Objectif

Avoir un moteur technique stable et générique qui permet de lancer rapidement n'importe quelle expérience : changer la cible, changer les features, changer le modèle, changer l'horizon — sans réécrire le code de validation, d'Optuna ou de reporting.

### 3.2 Fonctionnalités requises

La plateforme doit couvrir dans l'ordre suivant :

**1. Chargement et profiling**
- Lire n'importe quel CSV propre
- Détecter automatiquement le type de problème :
  - régression tabulaire
  - classification binaire / multi-classe
  - série temporelle univariée
  - série temporelle multivariée
  - classification directionnelle (cas du maïs)
- Détecter les colonnes de date, la cible, les features

**2. Preprocessing adaptatif**
- Typage des colonnes
- Gestion des dates (détection du calendrier, fréquence)
- Imputation des valeurs manquantes (forward-fill pour séries, médiane pour tabulaire)
- Encodage des variables catégorielles
- Normalisation si nécessaire (z-scores expandants pour anti-leakage)
- Création de lags si série temporelle
- Création de rolling features (moyenne mobile, volatilité)
- Suppression des colonnes inutiles ou suspectes (corrélation future > threshold)

**3. Validation temporelle**
- Walk-forward obligatoire si date détectée (split aléatoire interdit)
- Embargo = horizon H pour éviter le look-ahead
- Fenêtre initiale 60% des données, pas = 21 jours (1 mois de trading)
- Expansion du train (expanding window)
- Cross-validation classique uniquement si pas de date

**4. Registre de modèles**
- Baselines : zero return, historical mean, seasonal naive, momentum, mean reversion
- Linéaires : Ridge, Lasso, ElasticNet
- Arbres : Random Forest, ExtraTrees
- Boosting : HistGB, LightGBM, XGBoost, CatBoost
- Statistiques : ARIMA, SARIMAX, GARCH, VAR, Markov-switching
- Optionnel : SVR, MLP, LSTM, N-BEATS

**5. Optimisation Optuna**
- Espaces de recherche définis pour chaque modèle
- 50–100 essais par modèle minimum pour la production
- Études sauvegardées dans `artefacts/optuna.db` (reprise possible)
- Comparaison avant/après optimisation

**6. Meta-database et stacking**
- Prédictions out-of-fold (OOF) sauvegardées pour chaque modèle
- Stacking : Ridge méta sur OOF + features contextuelles (horizon, volatilité récente)
- Sauvegarde `artefacts/automl/meta_database.parquet`

**7. Métriques et résultats**
- Régression : RMSE, MAE, R², DA (directional accuracy)
- Classification : AUC, Brier score, F1, precision, recall
- Calibration : calibration curve, reliability diagram
- CQR : couverture empirique, largeur moyenne des intervalles
- Enregistrement dans `artefacts/automl/model_benchmarks.parquet`

**8. Explainability**
- SHAP global (feature importance)
- SHAP par famille de facteurs
- SHAP local sur cas individuels
- Ablation par famille : retirer une famille, mesurer la dégradation

**9. Rapport automatique**
- Markdown généré automatiquement : benchmark, SHAP, métriques, limites
- Génération en < 5 secondes sur tout dataset
- Historique des rapports sauvegardé

**10. Interface CLI**
```bash
# Lancer une expérience complète
mais automl run \
  --dataset data/processed/factors.parquet \
  --target y_up_h20 \
  --validation walk_forward \
  --optuna true \
  --stacking true \
  --exp-id EXP-006

# Lancer avec une seule famille de données (ablation)
mais automl run \
  --dataset data/processed/factors.parquet \
  --target y_up_h20 \
  --families market_momentum,weather_stress \
  --exp-id EXP-007a
```

### 3.3 Statut actuel de la plateforme

**Légende :** ✅ Validé (métrique vérifiée, artefact présent, résultat cohérent) | 🟡 Fonctionnel (code exécuté, validation scientifique incomplète) | 🟠 Fragile (fonctionne mais résultat peu exploitable) | ❌ Non fait

> Un composant est ✅ seulement si son artefact est présent, non vide, et que ses résultats ont été interprétés. Le code seul ne suffit pas.

| Composant | Statut | Commentaire |
|---|---|---|
| Profiler CSV | 🟡 | Fonctionnel sur maïs, non testé sur datasets externes |
| Preprocessing générique | 🟡 | Fonctionnel sur maïs, généralisation V2 |
| Walk-forward splits | ✅ | Validé, embargo respecté |
| Baselines (zero, mean, seasonal naive) | ✅ | Métriques mesurées et comparées |
| Ridge / RF / HGB | ✅ | Résultats dans model_benchmarks.parquet |
| LightGBM / XGBoost | 🟡 | Codé Palier 3, résultats à re-valider post-rebuild |
| SHAP TreeExplainer | 🟡 | Généré, cohérence économique des facteurs à vérifier |
| CQR walk-forward | ✅ couverture / 🟠 exploitabilité | Coverage 91.7% ✅, intervalles potentiellement larges |
| Stacking Ridge méta | 🟡 | Produit des prédictions, gain vs meilleur individuel à confirmer |
| Rapport Markdown auto | ✅ | < 5s, contenu à enrichir |
| Optuna production (50+ trials) | ❌ | Smoke test 1 essai seulement |
| ARIMA / SARIMAX / GARCH | ❌ | Non intégrés |
| Markov-switching | 🟠 | Codé, régime bear rare (~2.2%) = résultat fragile |
| CLI `mais automl run` | 🟠 | Partiel, V1 à finaliser |

---

## 4. Pilier B — Étude du marché du maïs

### 4.1 Philosophie de l'étude

L'étude n'est pas une succession de modèles lancés automatiquement. C'est une démarche de recherche appliquée :
- on formule des hypothèses économiques
- on teste des familles de données
- on compare des cibles
- on analyse les résultats honnêtement
- on interprète économiquement les signaux
- on archive les échecs autant que les succès
- on améliore progressivement l'indicateur

**Chaque expérience doit être tracée.** Rien ne se perd, même un résultat négatif.

### 4.2 Ce que l'étude doit produire

En sortie finale :

1. **Indicateur Maize Market Direction Indicator** (cf. section 2.2)
2. **EXPERIMENT_INDEX.md** — mémoire complète de toutes les expériences
3. **PROFESSIONAL_STUDY_REPORT.md** — rapport scientifique complet
4. **Notebooks 01–12** — raisonnement pas à pas, exportés en HTML

### 4.3 Ce que l'étude ne promet PAS

- Elle ne garantit pas de surpasser les baselines sur tous les horizons.
- Elle ne vise pas 90% de capture du prix maximum annuel (objectif retiré).
- Elle ne prétend pas que les modèles ML sont toujours meilleurs que le seasonal naive.

**Un résultat négatif honnêtement documenté a autant de valeur qu'un succès.**

---

## 5. Architecture cible du projet

```
Etude Mais/
│
├── Models/
│   └── (legacy — migration progressive vers src/mais/)
│
├── src/
│   └── mais/
│       ├── collect/          Collecteurs de données (CBOT, WASDE, NASS, FRED, CFTC, EIA, FAS…)
│       ├── clean/            Nettoyage et migration legacy
│       ├── features/         Construction des features brutes + z-scores anti-leakage
│       ├── targets/          Construction de toutes les cibles (retour, direction, force, oracle…)
│       ├── platform/         Plateforme AutoML générique
│       ├── models/           Registre de modèles propres
│       ├── walkforward/      Splits temporels walk-forward + embargo
│       ├── optimize/         Optuna et hyperparamètres
│       ├── meta/             Stacking, meta-database, CQR
│       ├── research/         Fonctions communes aux notebooks d'étude
│       ├── indicator/        Construction de l'indicateur directionnel final
│       └── reporting/        Génération automatique de rapports
│
├── notebooks/
│   └── corn_study/
│       ├── main/             Notebooks principaux 01–12
│       ├── experiments/
│       │   ├── successful/
│       │   ├── neutral/
│       │   └── failed/
│       ├── templates/        Template d'expérience (hypothèse → décision)
│       ├── exports/          Exports HTML des notebooks
│       └── EXPERIMENT_INDEX.md
│
├── data/
│   ├── raw/
│   ├── interim/              Données sources brutes collectées
│   └── processed/            features.parquet, factors.parquet, targets.parquet
│
├── artefacts/
│   ├── automl/               model_benchmarks, optuna_results, meta_database, stacking
│   ├── corn_study/           source_coverage, factor_importance, family_importance, ablation
│   ├── experiments/          EXP-XXX/ (config, metrics, predictions, plots, conclusion)
│   ├── models/               Modèles sérialisés (.pkl)
│   ├── predictions/          Prédictions par cible et horizon
│   ├── indicator/            direction_scores, confidence_scores, backtest, summary
│   └── reports/              PROFESSIONAL_STUDY_REPORT.md, INDICATOR_REPORT.md
│
├── docs/
│   ├── 00_PROJET_COMPLET_MAIS.md    ← CE FICHIER (source de vérité)
│   ├── DIRECTION.md                 Réflexions et analyses (référence historique)
│   ├── AUDIT_REPORT.md
│   ├── PROFESSIONAL_STUDY_REPORT.md
│   └── FINAL_REPORT.md
│
└── Archive/
    └── Ancien code conservé mais hors workflow principal
```

**Règle d'architecture :**
- `src/mais/` = code propre, pas de notebooks
- `notebooks/` = raisonnement, analyses, visualisations
- `artefacts/` = résultats générés (jamais modifiés à la main)
- `docs/` = synthèse et rapports officiels
- `Archive/` = ancien code conservé hors workflow

**Hiérarchie des documents :**

En cas de contradiction entre documents, l'ordre de priorité est :

1. `docs/00_PROJET_COMPLET_MAIS.md` — **source de vérité absolue**
2. `.ai/TICKETS.md` — tickets actifs en cours d'exécution
3. `docs/AUDIT_REPORT.md` — état technique à une date donnée
4. `docs/PROFESSIONAL_STUDY_REPORT.md` — résultats scientifiques générés
5. `docs/DIRECTION.md` — **archive de réflexion, non normative**

`DIRECTION.md` est une archive de pensée. Il ne pilote pas les tickets. Si une idée de DIRECTION.md n'est pas reprise ici, elle n'est pas prioritaire.

---

## 6. Sources de données

### 6.1 Sources actuelles et statuts

| Source | Fréquence | Lag | Statut | Fichier interim |
|---|---|---|---|---|
| Prix CBOT maïs (ZC=F) | Quotidien | 0 j | ✅ | `database.parquet` |
| Météo Corn Belt (10 états) | Quotidien | 0 j | ✅ | `meteo.parquet` |
| WASDE USDA | Mensuel | 0 j après pub | ✅ | `wasde.parquet` |
| NASS QuickStats (yield, area, stocks) | Annuel/Trimestriel | — | ✅ | `quickstats.parquet` |
| FRED macro (FedFunds, CPI, DGS10, DXY) | Daily/Monthly | 1 j | ✅ | `macro_fred.parquet` |
| CFTC COT maïs (code 002602) | Hebdo (pub. mar→ven) | ~3 j | ✅ | `cftc_cot.parquet` |
| USDA Crop Progress / Condition | Hebdo (saison mai–oct) | 1 j | 🟠 | Collecteur partiel |
| Drought Monitor (corn states) | Hebdo (jeu) | 1 j | 🟠 | Collecteur prêt, non câblé |
| EIA éthanol (API v2) | Hebdo | ~6 j | 🟠 | `eia_ethanol.parquet` (3805 lignes) |
| FAS Export Sales (US) | Hebdo | 1 j | 🟠 | Collecteur présent, clé manquante |
| Prix blé, soja, pétrole | Quotidien | 0 j | ✅ | `database.parquet` |
| Calendrier USDA (dates rapports) | Événementiel | — | ✅ | `usda_calendar.parquet` |
| Basis locaux (Iowa/Illinois) | Quotidien/Hebdo | 0–1 j | ❌ | Non collecté |
| Production Brésil/Argentine | Mensuel | 0 j | ❌ | Non collecté |
| Indice PDSI Midwest (sécheresse) | Mensuel | 0 j | ❌ | Via NOAA |

### 6.2 Sources additionnelles à intégrer (priorisées)

| Source | Priorité | Valeur ajoutée | Comment collecter |
|---|---|---|---|
| FAS Export Sales (hebdo) | Haute | Demande externe, surprises exports | API FAS avec FAS_API_KEY |
| EIA éthanol réel | Haute | Demande intérieure structurelle | API EIA avec EIA_API_KEY |
| Crop Progress complet | Haute | Condition des cultures en temps réel | NASS API hebdo saison |
| Drought Monitor câblé | Moyenne | Stress hydrique localisé | Déjà collecté, à câbler |
| Basis locaux Iowa/Illinois | Moyenne | Prix réel vs CBOT, arbitrage | Agrégation journalière, shift(1) |
| Taux USD/BRL, USD/ARS | Moyenne | Compétitivité Brésil/Argentine | FRED |
| VIX (appétit risque global) | Faible | Sentiment marché global | FRED |
| Engrais (gaz naturel) | Faible | Coût de production | FRED |
| Prix diesel | Faible | Coût de transport / stockage | FRED ou EIA |
| Production CONAB/Argentine | Faible | Concurrence mondiale | Scraping ou API |
| ENSO / El Niño | Faible | Météo globale multisaison | NOAA |

### 6.3 Règles anti-leakage pour toutes les sources

- **Toujours** appliquer `shift(1)` sur les données fondamentales (WASDE, COT, Export, EIA).
- Les rapports mensuels (WASDE, NASS) ne sont utilisés qu'**après** leur date de publication.
- Les z-scores sont calculés de façon **expansive** (expanding window), jamais sur la fenêtre complète.
- Les moyennes mobiles de référence (ex : exportations moyennes 5 ans) sont calculées uniquement sur les données disponibles à la date `t`.
- L'audit anti-leakage doit passer à **0 erreur critique** avant chaque rebuild validé.

---

## 7. Cadre factoriel — 13 familles

Les variables brutes (~250 colonnes) doivent être condensées en **facteurs économiques interprétables**. L'objectif est que la catégorie `others` (variables brutes non agrégées `f_raw__`) représente **moins de 10% de l'importance SHAP totale**.

### 7.1 Les 13 familles

| # | Famille | Variables clés | Signe économique |
|---|---|---|---|
| 1 | `market_momentum` | retours passés J-5/J-10/J-20, tendance | + si trend haussier |
| 2 | `market_volatility` | volatilité réalisée 10/30j, ATR | – si stress élevé |
| 3 | `wasde_supply_demand` | stocks/use ratio, production, importations, exports USDA | – si tightness élevé |
| 4 | `weather_stress` | T° max Corn Belt, GDD, précipitations, écart à la normale | – si stress élevé |
| 5 | `crop_condition` | % excellent/good, % poor/very poor (NASS hebdo) | – si condition dégradée |
| 6 | `drought` | Drought Monitor D2/D3/D4 sur corn states, PDSI | – si drought sévère |
| 7 | `exports` | FAS export sales hebdo, surprises vs moyenne 5 ans | + si surprises positives |
| 8 | `ethanol_demand` | Production éthanol EIA, stocks éthanol, marge éthanol | + si demande forte |
| 9 | `cot_positioning` | Net positions commerciaux/non-commerciaux COT, momentum COT | + si nets longs spéculatifs |
| 10 | `macro` | Dollar DXY, FedFunds, CPI, spread 10y-2y, S&P500 | – si dollar fort |
| 11 | `curve_structure` | Spread front/deferred, contango/backwardation | signal stockage |
| 12 | `global_competition` | Spread blé/maïs, spread soja/maïs, USD/BRL, production Argentine | – si concurrence forte |
| 13 | `seasonality` | Mois sin/cos, semaine agricole, dummy semis/pollinisation/récolte | cyclique |

### 7.2 Règles de construction des facteurs

- Chaque facteur doit avoir un **signe économique documenté** (+ = bullish, – = bearish).
- Les normalisations doivent être **expansives** (mean et std calculés jusqu'à la date t seulement).
- Les facteurs doivent être lisibles par un économiste agricole, pas seulement par un data scientist.
- Un `factor_metadata.yaml` doit documenter chaque facteur : description, sources, signe, lag appliqué.
- Les variables brutes résiduelles (`f_raw__`) doivent être réduites à moins de 10% de l'importance.

### 7.3 Problème identifié : facteur "others" trop large

Actuellement, une part importante de l'importance SHAP est allouée à des variables brutes non regroupées. Cela nuit à l'interprétabilité et favorise l'overfitting. Les facteurs à créer en priorité :
- `factor_crop_condition` (NASS Crop Progress)
- `factor_drought_severity` (Drought Monitor)
- `factor_export_demand_surprise` (FAS vs moyenne 5 ans)
- `factor_ethanol_demand_pull` (EIA réel via API)

---

## 8. Cibles à tester — 7 niveaux

Le choix de la cible est crucial. `y_logret_h20` est peut-être la mauvaise cible. Il faut tester toutes les reformulations possibles.

### Niveau 1 — Retour continu

| Cible | Description |
|---|---|
| `y_logret_h1` | log-retour à J+1 |
| `y_logret_h5` | log-retour à J+5 |
| `y_logret_h10` | log-retour à J+10 |
| `y_logret_h20` | log-retour à J+20 |
| `y_logret_h30` | log-retour à J+30 |
| `y_logret_h60` | log-retour à J+60 |
| `y_logret_h90` | log-retour à J+90 |

### Niveau 2 — Direction (binaire)

| Cible | Description |
|---|---|
| `y_up_h5` | 1 si prix monte à J+5, 0 sinon |
| `y_up_h10` | 1 si prix monte à J+10 |
| `y_up_h20` | 1 si prix monte à J+20 |
| `y_up_h30` | 1 si prix monte à J+30 |
| `y_up_h60` | 1 si prix monte à J+60 |
| `y_down_h5` | symétrique pour la baisse |
| … | |

### Niveau 3 — Force du mouvement (seuils)

| Cible | Description |
|---|---|
| `y_up_strong_1pct_h20` | 1 si hausse > 1% à J+20 |
| `y_up_strong_2pct_h20` | 1 si hausse > 2% à J+20 |
| `y_up_strong_3pct_h20` | 1 si hausse > 3% à J+20 |
| `y_up_strong_5pct_h20` | 1 si hausse > 5% à J+20 |
| `y_down_strong_1pct_h20` | 1 si baisse > 1% à J+20 |
| … | |

### Niveau 4 — Volatilité future

| Cible | Description |
|---|---|
| `realized_vol_h10` | volatilité réalisée sur les 10 jours suivants |
| `realized_vol_h20` | volatilité réalisée sur les 20 jours suivants |
| `realized_vol_h30` | volatilité réalisée sur les 30 jours suivants |

### Niveau 5 — Potentiel futur (max/min)

| Cible | Description |
|---|---|
| `future_max_return_h30` | meilleur retour atteignable dans les 30 prochains jours |
| `future_max_return_h60` | meilleur retour atteignable dans les 60 prochains jours |
| `future_min_return_h30` | pire retour dans les 30 prochains jours |
| `future_min_return_h60` | pire retour dans les 60 prochains jours |

### Niveau 6 — Risque / opportunité asymétrique

| Cible | Description |
|---|---|
| `downside_risk_h30` | percentile 10% du retour sur les 30 jours suivants |
| `upside_potential_h30` | percentile 90% du retour sur les 30 jours suivants |
| `prob_better_price_h30` | probabilité empirique que le prix soit supérieur à J+30 |

### Niveau 7 — Cibles intermédiaires pour analyse oracle

Ces cibles testent si des variables futures spécifiques expliquent le prix. Elles ne doivent jamais être utilisées dans un modèle réaliste (fuite contrôlée et assumée).

| Cible | Description |
|---|---|
| `oracle_future_weather_stress_h20` | stress météo moyen sur les 20 prochains jours |
| `oracle_future_crop_condition_change` | évolution de la condition des cultures |
| `oracle_future_wasde_yield_surprise` | surprise sur le rendement WASDE suivant |
| `oracle_future_export_sales_surprise` | surprises d'exportations sur les 4 prochaines semaines |
| `oracle_future_cot_position_change` | évolution des positions COT |
| `oracle_future_drought_change` | évolution de la sécheresse |
| `oracle_future_ethanol_change` | évolution de la demande éthanol |
| `oracle_future_basis_change` | évolution des basis locaux |

---

## 9. Modèles à tester

### 9.1 Baselines obligatoires

Toujours présentes comme référence. Un modèle ML qui ne bat pas toutes les baselines est inutile.

| Baseline | Description |
|---|---|
| `zero_return` | prédit 0 (retour nul) |
| `historical_mean` | moyenne mobile des retours passés |
| `seasonal_naive` | retour moyen du même mois / même semaine agricole |
| `momentum` | signal basé sur la tendance récente (retour J-20) |
| `mean_reversion` | signal contrarian si écart > 2σ |

### 9.2 Modèles statistiques temporels

| Modèle | Usage | Remarque |
|---|---|---|
| AR / ARMA | Structure autoregressive simple | Benchmark temporel |
| ARIMA | Avec différenciation | Si série non stationnaire |
| SARIMAX | Avec saisonnalité + exogènes | Tester avec facteurs météo |
| VAR | Multivariée | Si plusieurs prix corrélés |
| GARCH | Volatilité | Pour `realized_vol_hX` |
| Markov-switching | Régimes | Tester 2 états (bull/bear) |
| HMM | Régimes cachés | Alternative Markov |

**Note Markov-switching :** Le modèle à 3 états est instable (régime bear quasi absent à 2.2%). Tester d'abord 2 états bull/bear ou une segmentation saisonnière rule-based.

### 9.3 Modèles ML sur facteurs

| Modèle | Notes |
|---|---|
| Ridge | Linéaire régularisé — souvent compétitif sur facteurs |
| Lasso | Sélection de features automatique |
| ElasticNet | Mix L1/L2 |
| Random Forest | Baselines non-linéaires |
| ExtraTrees | Variante plus rapide |
| HistGradientBoosting | Robuste aux valeurs manquantes |
| LightGBM | Meilleur boosting sur grandes données |
| XGBoost | Alternative LightGBM |
| CatBoost | Si variables catégorielles |
| SVR | Pour séries à faible bruit |
| MLP | Réseau simple, tester sur facteurs uniquement |

### 9.4 Stacking et métamodèle

- **OOF predictions** : pour chaque modèle, sauvegarder les prédictions out-of-fold
- **Stacking Ridge méta** : apprendre sur les OOF de tous les modèles + features contextuelles
- **Features contextuelles du méta** : horizon, volatilité récente, saison, régime courant
- **Évaluation** : le stacking doit battre le meilleur modèle individuel

### 9.5 Deep Learning (optionnel)

À tester **uniquement après exhaustion des modèles classiques** et si ML ne donne pas de signal clair.

| Modèle | Notes |
|---|---|
| LSTM | Séries multivariées longues |
| N-BEATS | Séries temporelles sans exogènes |

---

## 10. Plan des notebooks (01–12)

### Définition de "notebook terminé"

Un notebook est **terminé** si et seulement si :
- [ ] Il s'exécute de haut en bas sans erreur (kernel restart → run all)
- [ ] Tous ses artefacts de sortie (table ci-dessous) sont présents et non vides
- [ ] Chaque résultat important est suivi d'une interprétation économique
- [ ] Il se termine par une section **"Conclusion"** avec décision CONSERVER/ABANDONNER/RETESTER/INTÉGRER
- [ ] Export HTML présent dans `notebooks/corn_study/exports/`
- [ ] Son entrée est ajoutée ou mise à jour dans `EXPERIMENT_INDEX.md`

### Artefacts obligatoires par notebook

| Notebook | Artefacts attendus dans `artefacts/` |
|---|---|
| 01 | `corn_study/source_coverage.parquet`, `reports/data_quality_report.md` |
| 02 | `corn_study/seasonality_results.parquet`, graphiques dans `corn_study/plots/` |
| 03 | `corn_study/factor_importance.parquet`, `corn_study/factor_metadata.yaml` |
| 04 | `corn_study/target_comparison.parquet`, `experiments/EXP-006–008/oracle_results.parquet` |
| 05 | `automl/baseline_results.parquet`, `automl/stat_models_results.parquet` |
| 06 | `automl/ml_benchmarks.parquet`, `automl/optuna_results.parquet`, `automl/meta_database.parquet` |
| 07 | `corn_study/ablation_results.parquet` |
| 08 | `corn_study/regime_context_results.parquet` |
| 09 | `corn_study/calibration_results.parquet`, `corn_study/confidence_analysis.parquet` |
| 10 | `indicator/direction_scores.parquet`, `indicator/indicator_config_used.yaml` |
| 11 | `indicator/indicator_backtest.parquet`, `reports/INDICATOR_BACKTEST_REPORT.md` |
| 12 | `reports/final_synthesis.md`, `reports/next_steps.md` |

### Règles communes à tous les notebooks

Chaque notebook doit être :
- **lisible** : une personne sans code peut suivre le raisonnement
- **orienté recherche** : hypothèse → test → interprétation → conclusion
- **exporté en HTML** dans `notebooks/corn_study/exports/`
- **sourcé en fonctions** dans `src/mais/research/` pour les calculs complexes

### 01 — Données et qualité

**Fichier :** `01_problem_data_quality.ipynb`

**Objectif :** Comprendre et documenter toutes les sources, leur qualité, leurs lacunes, et les premiers signaux statistiques.

**À traiter :**
- Couverture temporelle de chaque source (1ère date, dernière date, fréquence)
- Distribution des valeurs manquantes (heatmap temporelle des NaN)
- Statistiques descriptives des prix (CBOT, blé, soja, pétrole)
- Autocorrélation des retours par horizon
- Effet des publications WASDE (fenêtres autour des dates)
- Effet des saisons (prix moyen par mois, volatilité par mois)
- Visualisation de la COT (nets positions vs prix)
- Tableau récapitulatif de toutes les sources (✅ / 🟠 / ❌)

**Conclusion attendue :** Les données sont exploitables mais hétérogènes. Le signal brut est faible sur les retours, mais des structures saisonnières et événementielles existent. Il faut structurer les variables en facteurs et tester proprement.

---

### 02 — Saisonnalité et structure de marché

**Fichier :** `02_seasonality_market_structure.ipynb`

**Objectif :** Quantifier et comprendre les cycles saisonniers agricoles et leur impact sur le prix.

**À traiter :**
- Cycle agricole : semis (avril-mai), croissance (juin-août), récolte (sept-oct), stockage (nov-mars)
- Retour moyen et médian par mois (J+20, J+30) — heatmap
- Volatilité réalisée par mois
- Impact statistique des rapports WASDE (fenêtre ±5 jours autour de chaque publication)
- Impact des rapports NASS Crop Progress (hebdo saison)
- Analyse des pics et creux historiques (2012 sécheresse, 2022 guerre Ukraine…)
- Baseline saisonnière formalisée : est-elle vraiment utile ?
- Spread saisonnier entre contrats (courbe forward) : contango vs backwardation

**Conclusion attendue :** La saisonnalité existe et doit servir de baseline, mais elle ne suffit pas seule. Le signal WASDE et les périodes de stress sont des moments clés.

---

### 03 — Cadre factoriel

**Fichier :** `03_factor_framework.ipynb`

**Objectif :** Transformer les ~250 variables brutes en 13 familles de facteurs économiques lisibles et vérifier leur qualité.

**À traiter :**
- Visualisation de chaque famille : distribution, stationnarité, autocorrélation
- Corrélation entre familles (matrice de corrélation)
- Contribution actuelle des facteurs à l'importance SHAP (identifier les `f_raw__` résiduels)
- Construction des facteurs manquants : `crop_condition`, `drought_severity`, `export_demand_surprise`, `ethanol_demand_pull`
- Vérification du signe économique de chaque facteur
- Anti-leakage : audit que chaque facteur est basé sur des données passées uniquement
- Proportion `others` < 10% vérifiée

**Conclusion attendue :** Les 13 familles de facteurs permettent de comprendre le marché. La catégorie `others` est sous le seuil de 10%.

---

### 04 — Reformulation des cibles et analyse oracle

**Fichier :** `04_target_reformulation_and_oracle_analysis.ipynb`

**Objectif central :** Identifier si `y_logret_h20` est vraiment la meilleure cible, et découvrir quels drivers futurs expliquent vraiment le prix.

**Partie A — Reformulation des cibles**
- Calculer et visualiser toutes les cibles des niveaux 1 à 6 (cf. section 8)
- Comparer les distributions : y_logret vs y_up vs y_up_strong
- Calculer la corrélation entre cibles à différents horizons
- Tester chaque cible avec un modèle simple (Ridge) — laquelle donne le meilleur DA ?

**Partie B — Analyse oracle**

C'est la partie la plus importante de ce notebook. Elle répond à :
> "Si je connaissais certaines variables futures, lesquelles expliqueraient vraiment le prix du maïs ?"

Protocol :
1. Créer les cibles intermédiaires niveau 7 (oracle) — données futures connues
2. Prédire y_logret_h20 en utilisant l'oracle comme feature
3. Comparer performance modèle réaliste vs modèle oracle
4. Tableau de synthèse :

| Variable oracle | Améliore le DA ? | Est-elle prédictible ? | Décision |
|---|---|---|---|
| oracle_future_weather_stress | oui/non | oui/non | investir/abandonner |
| oracle_future_crop_condition | oui/non | oui/non | investir/abandonner |
| oracle_future_wasde_surprise | oui/non | oui/non | investir/abandonner |
| oracle_future_export_surprise | oui/non | oui/non | investir/abandonner |
| oracle_future_cot_change | oui/non | oui/non | investir/abandonner |

**Conclusion attendue :** Le prix exact est difficile à prédire. Les cibles directionnelles ou intermédiaires peuvent être plus exploitables. L'analyse oracle identifie quels drivers futurs valent la peine d'être prédits.

---

### 05 — Baselines et modèles statistiques

**Fichier :** `05_baselines_and_statistical_models.ipynb`

**Objectif :** Établir des références solides et tester si le marché contient une structure temporelle simple.

**Baselines :**
- zero_return, historical_mean, seasonal_naive, momentum, mean_reversion
- Métriques pour chaque baseline et chaque horizon (h5, h10, h20, h30)
- Tableau comparatif RMSE / MAE / DA / AUC

**Modèles statistiques :**
- AR, ARMA sur log-retours
- ARIMA avec sélection auto du (p,d,q)
- SARIMAX avec facteurs météo ou WASDE comme exogènes
- VAR multivariée (maïs + blé + soja)
- GARCH pour `realized_vol_hX`
- Markov-switching 2 états (bull/bear)

**Conclusion attendue :** Ces modèles donnent une base scientifique. Le marché a une structure temporelle faible mais existante. Le modèle Markov à 2 états est plus stable qu'à 3 états.

---

### 06 — AutoML et modèles ML

**Fichier :** `06_automl_ml_models.ipynb`

**Objectif :** Utiliser la plateforme AutoML pour tester tous les modèles ML sur toutes les cibles et horizons principaux.

**À tester systématiquement :**
- Sur features brutes vs facteurs : lequel gagne ?
- Sur chaque cible principale (y_logret_h20, y_up_h20, y_up_strong_3pct_h20)
- Sur chaque horizon (h5, h10, h20, h30)
- Avant vs après Optuna
- Modèle individuel vs stacking

**Métriques enregistrées :**
- Régression : RMSE, MAE, R², DA
- Classification : AUC, Brier score, F1
- Pour chaque (modèle, cible, horizon, features) → `artefacts/automl/model_benchmarks.parquet`

**Analyse de confiance du signal** (crucial) :

| Filtre de confiance | % jours conservés | DA | AUC | Interprétation |
|---|---|---|---|---|
| Tous les jours | 100% | ~55% | ~0.54 | signal moyen |
| confiance > 60% | ~45% | ? | ? | à mesurer |
| confiance > 70% | ~20% | ? | ? | à mesurer |
| confiance > 80% | ~8% | ? | ? | rare mais fort ? |

**Conclusion attendue :** On identifie les modèles vraiment utiles. On élimine ceux qui n'apportent rien. On sait à quel horizon et sur quelle cible le signal est le plus fort.

---

### 07 — Ablation des familles de données

**Fichier :** `07_feature_family_ablation.ipynb`

**Objectif :** Comprendre quelles familles de données portent réellement le signal. Tester la contribution marginale de chaque famille.

**Tests d'ablation :**
- market_momentum only
- weather_stress only
- wasde_supply_demand only
- cot_positioning only
- macro only
- seasonality only
- all features
- all minus market_momentum
- all minus weather_stress
- all minus wasde_supply_demand
- … (all minus one family pour chaque famille)

**Métrique d'ablation :** dégradation du RMSE et du DA quand on retire la famille.

**Tableau attendu :**

| Famille retirée | ΔRMSE | ΔDA | Importance relative |
|---|---|---|---|
| market_momentum | +X% | -Y% | élevée |
| weather_stress | +X% | -Y% | moyenne |
| wasde_supply_demand | +X% | -Y% | élevée |
| macro | +X% | -Y% | faible |
| … | | | |

**Conclusion attendue :** On sait quelles familles sont utiles, redondantes ou inutiles selon les horizons. Cela guide les futures collectes de données.

---

### 08 — Régimes et saisons

**Fichier :** `08_regime_and_seasonal_models.ipynb`

**Objectif :** Tester si le marché est mieux prédit selon le contexte (saison, régime, condition).

**Contextes à tester :**
- Saison agricole : semis / croissance / récolte / stockage
- Régime de volatilité : marché calme vs marché agité (volatilité > percentile 75%)
- Régime directionnel : période haussière vs baissière (Markov-switching 2 états)
- Condition fondamentale : stocks tendus (stocks/use < 10%) vs stocks confortables
- Période météo critique : juin-août (pollinisation) vs reste de l'année
- Fenêtre WASDE : ±5 jours autour des publications
- COT extrême : nets longs > percentile 90% vs normal

**Pour chaque contexte :** calculer DA, RMSE, AUC du meilleur modèle dans ce contexte uniquement.

**Conclusion attendue :** On identifie dans quels contextes le signal est plus fort ou plus faible. Cela permet de créer des modèles spécialisés par contexte et d'améliorer la confiance de l'indicateur.

---

### 09 — Incertitude et calibration

**Fichier :** `09_uncertainty_and_calibration.ipynb`

**Objectif :** Mesurer quand et comment le modèle est fiable. L'indicateur doit savoir dire "incertain".

**À tester :**
- CQR (Conformalized Quantile Regression) : couverture empirique vs α cible
- Split conformal prediction : alternative à CQR
- Quantile regression directe : LightGBM quantile
- Platt scaling : calibration des probabilités
- Isotonic regression : calibration non-paramétrique
- Reliability diagram (calibration curve) : si le modèle dit 65%, est-ce vrai historiquement ?
- Brier score par horizon et par contexte
- Largeur des intervalles CQR : est-elle exploitable (< coût stockage) ?

**Question centrale :** Quand le modèle dit P(hausse) = 65%, est-ce historiquement vrai ?

**Score de confiance V1 :** Construire un `confidence_score` composite selon la formule définie dans `config/indicator.yaml` :

```
confidence_score =
  0.30 × probability_distance_score   # abs(P(up) - 0.5) × 2
  + 0.25 × model_agreement_score      # % modèles du stacking avec même signe
  + 0.25 × interval_width_score       # 1 - normalized_cqr_width (clampé 0–1)
  + 0.20 × signal_stability_score     # % des 3 derniers jours avec même signal
```

Cette formule est la V1 officielle. Elle doit être utilisée identiquement dans tous les notebooks et dans l'indicateur final. Toute modification de la formule passe par une mise à jour de `config/indicator.yaml` et une nouvelle EXP.

**Conclusion attendue :** L'indicateur sait dire "incertain" quand les probabilités ne sont pas fiables. La calibration permet de transformer les scores en probabilités interprétables.

---

### 10 — Construction de l'indicateur

**Fichier :** `10_indicator_construction.ipynb`

**Objectif :** Combiner tous les résultats des modèles en un indicateur final Maize Market Direction Indicator.

**Algorithme de construction :**
1. Agréger P(up_hX) et P(down_hX) par horizon (stacking pondéré)
2. Calculer P(strong_up_hX) et P(strong_down_hX)
3. Calculer `confidence_score` (cf. notebook 09)
4. Appliquer les règles de signal dans **cet ordre strict** (défini dans `config/indicator.yaml`) :
   ```
   1. Si confidence_score < 0.45                          → UNCERTAIN
   2. Sinon si P(up) > 0.60 ET P(up) - P(down) > 0.15   → BULLISH
   3. Sinon si P(down) > 0.60 ET P(down) - P(up) > 0.15 → BEARISH
   4. Sinon si abs(P(up) - P(down)) < 0.10               → NEUTRAL
   5. Sinon                                               → UNCERTAIN
   ```
   L'ordre est critique : la confiance est vérifiée en premier pour éviter qu'un signal soit à la fois BULLISH et UNCERTAIN.
5. Sélectionner les top 3 facteurs haussiers et top 3 facteurs baissiers (SHAP)
6. Générer l'interprétation économique

**Sorties de l'indicateur :**
- `P(up)` par horizon
- `P(down)` par horizon
- `P(strong_up)` et `P(strong_down)` à h20 et h30
- `expected_return` par horizon
- `confidence_score`
- `market_signal` : BULLISH / BEARISH / NEUTRAL / UNCERTAIN
- `top_bullish_factors` (3 facteurs avec contribution SHAP)
- `top_bearish_factors`
- `economic_interpretation` (texte généré)

**Sauvegarde :** `artefacts/indicator/direction_scores.parquet`

---

### 11 — Backtest de l'indicateur

**Fichier :** `11_indicator_backtest.ipynb`

**Objectif :** Tester si les signaux historiques de l'indicateur avaient une vraie valeur informationnelle.

**Questions clés :**
- Quand l'indicateur dit BULLISH, le marché monte-t-il plus souvent qu'au hasard ?
- Quand il dit BEARISH, baisse-t-il ?
- Quand il dit UNCERTAIN, les résultats sont-ils proches du hasard (50/50) ?
- Les signaux confiants (confidence > 70%) sont-ils meilleurs que les signaux faibles ?

**Métriques à mesurer :**

| Dimension | Métriques |
|---|---|
| Global | DA, AUC, Brier score |
| Par horizon | DA h5, h10, h20, h30 |
| Par signal | DA sur BULLISH only, BEARISH only |
| Par confiance | DA à confidence > 60/70/80% |
| Par saison | DA en période semis, croissance, récolte |
| Par régime | DA en marché bull/bear/range |
| Stabilité | DA par année (2010–2026) |

**Conclusion attendue :** On sait si l'indicateur a une vraie valeur historique, dans quels contextes, et à quel niveau de confiance il est exploitable.

---

### 12 — Synthèse finale

**Fichier :** `12_final_synthesis.ipynb`

**Objectif :** Résumer tout ce qui a été testé, ce qui marche, ce qui ne marche pas, et ce qu'il faut améliorer.

**Contenu :**
- Meilleures données (familles les plus utiles)
- Meilleures cibles (niveau 1 vs niveau 2 vs niveau 3)
- Meilleurs modèles (par horizon, par cible)
- Meilleur horizon (signal le plus fort)
- Contextes où le signal marche (saison, régime, condition)
- Contextes où il échoue
- Limites connues du projet
- Prochaines pistes d'amélioration prioritaires

---

## 11. Liste complète des expériences (EXP-001–018)

Ces expériences constituent le programme de recherche. Chacune est tracée dans `EXPERIMENT_INDEX.md`.

| ID | Notebook | Hypothèse principale | Cible | Statut |
|---|---|---|---|---|
| EXP-001 | 05 | Les baselines simples établissent le plancher de performance | y_logret_h20 | À lancer |
| EXP-002 | 06 | Le signal est plus fort à J+20/J+30 qu'à J+5/J+10 | y_logret_h5/20/30 | À lancer |
| EXP-003 | 06 | Les familles de données seules ont chacune un signal mesurable | y_logret_h20 | À lancer |
| EXP-004 | 07 | L'ablation d'une famille dégrade le modèle de façon mesurable | y_logret_h20 | À lancer |
| EXP-005 | 06 | Les facteurs économiques battent les variables brutes | y_logret_h20 | À lancer |
| EXP-006 | 04 | y_up_h20 est plus prédictible que y_logret_h20 | y_up_h20 | À lancer |
| EXP-007 | 04 | y_up_strong_3pct_h20 est plus prédictible que y_up_h20 | y_up_strong_3pct | À lancer |
| EXP-008 | 04 | L'analyse oracle identifie les drivers futurs dominants | oracle variables | À lancer |
| EXP-009 | 05 | ARIMA/SARIMAX battent les baselines naïves | y_logret_h20 | À lancer |
| EXP-010 | 06 | LightGBM/XGBoost/CatBoost battent Ridge et RF | y_logret_h20 | À lancer |
| EXP-011 | 06 | Optuna améliore LightGBM significativement | y_logret_h20 | À lancer |
| EXP-012 | 06 | Le stacking méta bat le meilleur modèle individuel | y_up_h20 | À lancer |
| EXP-013 | 08 | Les modèles entraînés par saison sont meilleurs | y_logret_h20 | À lancer |
| EXP-014 | 08 | Les modèles entraînés par régime sont meilleurs | y_up_h20 | À lancer |
| EXP-015 | 09 | La calibration améliore la fiabilité des probabilités | y_up_h20 | À lancer |
| EXP-016 | 09/11 | Le modèle est significativement meilleur sur les signaux confiants | y_up_h20 | À lancer |
| EXP-017 | 10 | L'indicateur construit bat les baselines directionnelles | signal | À lancer |
| EXP-018 | 11 | L'indicateur a une valeur informationnelle historique stable | signal backtest | À lancer |

---

## 12. Méthode de travail obligatoire

**Toute nouvelle idée ou expérience doit suivre cette structure :**

```
Hypothèse :
  [Quelle est la prédiction ? Pourquoi économiquement ?]

Données nécessaires :
  [Quelles sources, quelles familles, quelles dates ?]

Cible testée :
  [y_logret_h20 ? y_up_h20 ? autre ?]

Méthode :
  [Quel modèle, quelle validation, quel horizon, quel split ?]

Résultat :
  RMSE = X | DA = Y% | AUC = Z

Interprétation économique :
  [Que disent ces résultats sur le marché ? Sont-ils cohérents ?]

Décision :
  CONSERVER / ABANDONNER / RETESTER / INTÉGRER DANS L'INDICATEUR
```

**Règle absolue :** Chaque expérience terminée doit être ajoutée à `EXPERIMENT_INDEX.md` avec sa conclusion et son statut (`successful / neutral / failed / active`).

---

## 13. Roadmap par phases (0–7)

> **Note :** Les dates ci-dessous sont indicatives. Chaque phase ne passe à la suivante que si ses **critères de sortie** sont tous vérifiés. Une phase qui prend plus de temps n'est pas un échec — c'est une mesure de rigueur.

---

### Phase 0 — Stabilisation *(cible : mai 2026)*

**Objectif :** Avoir un pipeline qui tourne de bout en bout, sans erreur.

- Corriger tous les chemins cassés (legacy Models/)
- Rebuild complet : `make clean && make data && make features && make study`
- Anti-leakage : 0 erreur critique
- Artefacts non vides vérifiés
- Notebooks 01 et 02 exécutables
- Rapport `AUDIT_REPORT.md` à jour

**Critères de sortie (tous obligatoires) :**
- [ ] `make clean && make data && make features && make study` passe sans erreur
- [ ] `python -m audit` → 0 erreur critique de leakage
- [ ] Tous les artefacts listés en section 15.1 sont non vides
- [ ] `AUDIT_REPORT.md` contient le tableau ✅/🟡/🟠/❌ à jour

---

### Phase 1 — AutoML V1 opérationnelle *(cible : juin 2026)*

**Objectif :** Moteur technique suffisant pour lancer toutes les expériences EXP-001–018.

- Optuna production (50+ trials par modèle)
- ARIMA / SARIMAX / GARCH intégrés dans le registre de modèles
- Stacking meta-database propre
- `config/indicator.yaml` en place
- Tests automatisés du pipeline

**Critères de sortie :**
- [ ] `mais automl run --dataset factors.parquet --target y_up_h20` s'exécute de bout en bout
- [ ] `artefacts/automl/model_benchmarks.parquet` contient Optuna results
- [ ] ARIMA/SARIMAX apparaissent dans model_benchmarks
- [ ] `config/indicator.yaml` existe et est valide

---

### Phase 2 — Base scientifique *(cible : juillet 2026)*

**Objectif :** Fondations scientifiques solides avant les expériences avancées.

- Sources manquantes intégrées (FAS, EIA réel, Crop Progress, Drought câblé)
- Cadre factoriel complet : 13 familles, `others < 10%`
- Toutes les cibles niveaux 1 à 7 dans `targets.parquet`
- Notebooks 01 à 05 exécutés et exportés HTML
- EXP-001 à EXP-005 dans `EXPERIMENT_INDEX.md`

**Critères de sortie :**
- [ ] `factor_metadata.yaml` présent, 13 familles documentées
- [ ] SHAP : `others` < 10% de l'importance totale
- [ ] `targets.parquet` contient colonnes niveaux 1 à 6
- [ ] Notebooks 01–05 exécutés, exports HTML présents dans `notebooks/corn_study/exports/`
- [ ] EXP-001–005 dans EXPERIMENT_INDEX avec statut et décision

---

### Phase 3 — Expérimentations avancées *(cible : août 2026)*

**Objectif :** Tester toutes les hypothèses EXP-006 à EXP-014.

- Modèles ML + Optuna + stacking sur toutes les cibles principales
- Analyse oracle complète (EXP-008)
- Ablation des familles (EXP-004)
- Régimes et saisons (EXP-013, EXP-014)

**Critères de sortie :**
- [ ] EXP-006 à EXP-014 toutes dans EXPERIMENT_INDEX avec décision finale
- [ ] `artefacts/experiments/EXP-XXX/` existent pour chaque EXP
- [ ] On peut répondre aux 6 questions de recherche de la section 2.3

---

### Phase 4 — Incertitude et confiance *(cible : septembre 2026)*

**Objectif :** Construire et valider le `confidence_score`.

- CQR final calibré, Brier score, calibration Platt/isotonic
- Performance par niveau de confiance (EXP-015, EXP-016)
- Signal UNCERTAIN formalisé

**Critères de sortie :**
- [ ] Reliability diagram : courbe proche de la diagonale
- [ ] DA sur signaux confidence > 70% > DA globale (statistiquement)
- [ ] `confidence_score` calculé selon la formule de `config/indicator.yaml`
- [ ] EXP-015–016 dans EXPERIMENT_INDEX avec décision

---

### Phase 5 — Construction de l'indicateur *(cible : octobre 2026)*

**Objectif :** Maize Market Direction Indicator V1 avec backtest.

- Notebook 10 exécuté, notebook 11 exécuté
- EXP-017, EXP-018 terminées
- `artefacts/indicator/` complet

**Critères de sortie :**
- [ ] `artefacts/indicator/direction_scores.parquet` présent et non vide
- [ ] `INDICATOR_REPORT.md` généré avec métriques par horizon et signal
- [ ] Backtest : quand BULLISH, DA > 55% sur au moins 3 horizons
- [ ] Quand UNCERTAIN, DA ≈ 50% (vérification honnêteté)

---

### Phase 6 — Synthèse et amélioration *(cible : novembre 2026)*

**Objectif :** Rapport final + décision sur les pistes suivantes.

- Notebook 12 exécuté
- Rapport de recherche final rédigé
- Erreurs par année, saison, régime analysées

**Critères de sortie :**
- [ ] `docs/FINAL_REPORT.md` complet avec conclusion honnête
- [ ] `docs/PROFESSIONAL_STUDY_REPORT.md` table ✅/❌/⚠️ à jour
- [ ] Pistes d'amélioration V2 listées et priorisées

---

### Phase 7 — Futur outil agriculteur *(cible : 2027+)*

**Objectif :** Transformer l'indicateur en aide à la décision agricole.

- Couche SELL / STORE / WAIT basée sur l'indicateur + coûts de stockage
- Backtest agriculteur complet (capture rate, regret, % années gagnantes)
- Pipeline quotidien automatique
- Dashboard Streamlit ou équivalent

**Critères de sortie :**
- [ ] `FARMER_BACKTEST_REPORT.md` avec stratégie IA vs baselines agricoles
- [ ] `make daily` génère un rapport quotidien avec signal du jour
- [ ] Dashboard accessible en localhost

---

## 14. Critères de réussite

Les performances sont mesurées contre des baselines simples. Il n'y a **aucun objectif chiffré arbitraire** (l'objectif "≥90% capture rate" a été retiré).

**L'indicateur est considéré intéressant si :**

| Critère | Définition |
|---|---|
| DA significative | DA globale > baseline seasonal naive |
| DA élevée sur confiants | DA sur signaux confidence > 70% nettement > DA globale |
| AUC > 0.55 | Sur au moins un horizon et une cible |
| Brier score correct | Calibration acceptable (reliability diagram) |
| Cohérence économique | Les facteurs haussiers/baissiers ont du sens économique |
| Stabilité temporelle | Pas de dépendance à une seule crise (2012, 2022) |
| Robustesse anti-leakage | Audit 0 erreur critique à chaque rebuild |
| UNCERTAIN honnête | Quand signal incertain, résultats proches du hasard (DA ≈ 50%) |

**L'indicateur est décevant si :**
- DA globale ≤ seasonal naive sur tous les horizons
- Les signaux confiants ne sont pas meilleurs que les signaux faibles
- L'importance SHAP est dominée par une seule période de crise

---

## 15. État actuel du projet

**Dernière mise à jour : 2026-05-13**

### 15.1 Paliers complétés

**Légende :** ✅ Validé | 🟡 Fonctionnel, validation incomplète | 🟠 Fragile | ❌ Non fait

| Palier | Description | Statut | Commentaire |
|---|---|---|---|
| 1 | macro_fred + quickstats + production dans build_features() | ✅ | Intégré et testé |
| 2 | CFTC COT collecteur + intégration features | ✅ | 3152 lignes, NaN post-2021 à surveiller |
| 2b | EIA éthanol collecteur (API v2 réelle) | 🟡 | 3805 lignes, séries EIA à auditer |
| 3 | XGBoost + LightGBM dans _model_specs() | 🟡 | Codé, résultats à re-valider sur rebuild complet |
| 4 | SHAP réel via TreeExplainer | 🟡 | Généré, cohérence économique des top facteurs à vérifier |
| 5 | CQR walk-forward | ✅ couverture / 🟠 exploitabilité | Coverage 91.7% ✅, largeur des intervalles non analysée |
| 6 | Markov-switching dans _build_regimes() | 🟠 | Codé mais régime bear ~2.2% = quasi inutile, 2 états à tester |
| 7 | Plateforme AutoML générique | 🟡 | Rapport auto ✅, généralisation hors maïs non testée |
| 8 | Pipeline quotidien ops/daily.py | 🟡 | `make daily` tourne 1m54s, signal quotidien non validé |

### 15.2 Résultats mesurés

| Métrique | Valeur |
|---|---|
| CQR coverage | **91.7%** (objectif ≥88%) |
| Split-conformal coverage | 88.9% |
| Meilleur modèle h5 | `rf_factors` RMSE=0.036, DA=0.535 |
| Meilleur modèle h10 | `rf_factors` RMSE=0.050, DA=0.556 |
| Meilleur modèle h20 | `baseline_seasonal_naive` RMSE=0.071, DA=0.555 |
| Meilleur modèle h30 | `baseline_seasonal_naive` RMSE=0.085, DA=0.583, R²=0.091 |
| `lgbm_factors` DA h20 | **0.613** (meilleure direction 20j) |
| Backtest SELL_HARVEST | 82.8% capture prix max annuel |
| Backtest MODEL_SIGNAL | 82.0% capture |
| Pipeline quotidien | `make daily` PASS en 1m54s |
| AutoML platform | rapport Markdown en < 5s |

**Note :** Le meilleur modèle ML (LightGBM, DA=0.613 à h20) bat le seasonal naive à cet horizon. La baseline seasonal naive domine à h30 (DA=0.583). Signal partiel exploitable à J+20.

### 15.3 Tickets actuels

| Ticket | Statut | Description |
|---|---|---|
| ETUDE-01 | NEEDS_REVIEW | EXPERIMENT_INDEX.md créé |
| ETUDE-02 | NEEDS_REVIEW | Nettoyage cadre factoriel |
| ETUDE-03 | NEEDS_REVIEW | Cibles de recherche + oracle |
| ETUDE-04 | NEEDS_REVIEW | AutoML bridge propre |
| ETUDE-05 | READY (après review ETUDE-02+03) | 12 notebooks exécutés + HTML |
| ETUDE-06 | READY (après review ETUDE-03) | Backtest agriculteur V2 |
| ETUDE-07 | Vague 3 (après ETUDE-03+04) | Indicateur directionnel |

### 15.4 Problèmes connus résiduels

- **FAS Export Sales** : `FAS_API_KEY` non fournie — `export_sales_mt` NaN. Activer via `config/sources.yaml` + clé.
- **Régime bear rare** (~2.2% des obs) — résultat honnête du marché, pas un bug. Markov 2 états à tester.
- **Optuna production** : smoke 1 essai seulement. Tuning complet : `--optuna-trials 50+`.
- **COT NaN post-2021** : contrats expirés à filtrer ou recaler sur OI global.

---

## 16. Journal des expériences

Le fichier `notebooks/corn_study/EXPERIMENT_INDEX.md` est la mémoire du projet.

### Structure d'une entrée

```markdown
## EXP-XXX — [Titre court]

**Date :** YYYY-MM-DD
**Notebook :** 0X_nom_du_notebook.ipynb
**Statut :** active / successful / neutral / failed

**Hypothèse :**
[Description de ce qu'on teste et pourquoi économiquement]

**Données :** [Sources utilisées]
**Cible :** [y_logret_h20 / y_up_h20 / etc.]
**Modèle :** [LightGBM / Ridge / etc.]
**Validation :** [walk-forward, fenêtre initiale X%, horizon Y]

**Résultats :**
- RMSE = X
- DA = Y%
- AUC = Z
- Comparaison baseline : +/- X%

**Interprétation :**
[Ce que ça dit sur le marché économiquement]

**Décision :** CONSERVER / ABANDONNER / RETESTER / INTÉGRER
**Raison :** [Pourquoi cette décision]
```

### Structure des artefacts par expérience

```
artefacts/experiments/EXP-XXX/
├── config.yaml          # paramètres exacts de l'expérience
├── metrics.parquet      # métriques par fold
├── predictions.parquet  # prédictions OOF
├── plots/               # graphiques
├── interpretation.md    # analyse économique
└── conclusion.md        # décision et raison
```

---

## 17. Règles de vérité du projet

Ces règles sont non négociables.

### Règles de données
- **Anti-leakage obligatoire** : `shift(1)` sur toutes les sources fondamentales (WASDE, COT, Export, EIA, Crop Progress).
- **Z-scores expansifs** : jamais calculés sur la fenêtre future. Toujours `expanding().mean()` et `expanding().std()`.
- **Rapports USDA** : utilisés uniquement après leur date de publication.
- **L'audit anti-leakage** doit passer à 0 erreur critique avant tout rebuild validé.

### Règles de modélisation
- **Walk-forward obligatoire** si date présente. Split aléatoire interdit.
- **Embargo = horizon H** minimum. Toujours appliqué.
- **Baselines toujours présentes** comme référence. Un modèle qui ne bat pas toutes les baselines est documenté comme tel, pas ignoré.

### Règles de documentation
- **Pas de claim non implémenté** dans le rapport (`PROFESSIONAL_STUDY_REPORT.md`).
- **Table ✅/❌/⚠️** à jour après chaque palier.
- **Chaque expérience documentée** dans `EXPERIMENT_INDEX.md` avec conclusion et décision.
- **Rien n'est perdu** : même les expériences échouées sont archivées avec leur conclusion.

### Règles de code
- Anti-leakage : `shift(1)` + z-scores expansifs sur toutes les données fondamentales.
- Ne pas casser `build_features()` dans `src/mais/features/__init__.py`.
- Ne pas casser `walk_forward_cqr()` dans `src/mais/meta/cqr.py`.
- Schéma de sortie `_build_regimes()` : colonnes `Date, corn_close, return_60d, realized_vol_60d, regime_score, regime`.
- Imports optionnels (lightgbm, xgboost, shap, statsmodels) dans des blocs `try/except ImportError`.
- Pas de commentaires évidents. Pas de docstrings multi-paragraphes.

### Règles de versionning des artefacts
- Versionner le code (git) avant chaque phase majeure.
- Produire des exports HTML/PDF de chaque notebook pour archivage.
- Les artefacts `.parquet` et `.json` ne sont jamais modifiés à la main.

---

## 18. Prochaines étapes immédiates

### À faire maintenant

0. **Créer ETUDE-00 — Validation des résultats actuels** (PRIORITÉ ABSOLUE avant tout)

   Avant de lancer de nouveaux notebooks, vérifier que les métriques de la section 15.2 sont reproductibles, propres et sans leakage. Un résultat non reproduit n'est pas un résultat.

   **Objectif :** Reproduire toutes les métriques de la section 15.2.
   **Sortie attendue :** `artefacts/validation/current_results_validation.md`

   | Métrique | Valeur attendue | Valeur reproduite | Écart | Statut |
   |---|---|---|---|---|
   | CQR coverage | 91.7% | ? | ? | ? |
   | lgbm_factors DA h20 | 0.613 | ? | ? | ? |
   | seasonal_naive DA h30 | 0.583 | ? | ? | ? |
   | MODEL_SIGNAL capture | 82.0% | ? | ? | ? |
   | Anti-leakage audit | 0 erreur | ? | ? | ? |

   De plus vérifier : période exacte du test, nombre d'observations, équilibre des classes, stabilité de la DA par année.

1. **Revoir les tickets ETUDE-01 à ETUDE-04** (en NEEDS_REVIEW) — valider ou demander corrections.

   **Critères de review par ticket :**
   - ETUDE-01 (EXPERIMENT_INDEX) : contient EXP-001–018 avec hypothèse, notebook, artefacts attendus, statut
   - ETUDE-02 (factorisation) : `others < 10%`, `factor_metadata.yaml` présent, `f_raw__` fortement réduit
   - ETUDE-03 (cibles + oracle) : cibles niveaux 1–7 dans `targets.parquet`, oracle séparé, aucune oracle dans modèle réaliste
   - ETUDE-04 (AutoML bridge) : un notebook peut appeler AutoML sans toucher au legacy, résultats dans `artefacts/automl/`

2. **Lancer Vague 2** après review :
   - ETUDE-05 : exécuter les 12 notebooks + export HTML
   - ETUDE-06 : Backtest agriculteur V2

3. **Nouvelles idées à transformer en tickets** (issues identifiées dans DIRECTION.md) :
   - Markov-switching 2 états (plus stable que 3 états)
   - Optuna production (50+ trials)
   - ARIMA/SARIMAX dans le registre de modèles
   - Analyse oracle complète (EXP-008)
   - Performance par niveau de confiance (EXP-016)
   - Calcul des cibles niveaux 3 à 7 (fort, volatilité, max/min, oracle)

### Commandes de référence

```bash
# Rebuild complet
make clean && make data && make features && make study

# Pipeline quotidien
venv/bin/python -m mais.cli daily-run --collect

# AutoML générique sur nouveau dataset
venv/bin/python -m mais.cli platform run --csv dataset.csv --target prix

# Vérification anti-leakage
cd src && python -m ruff check ../src/mais/
python -m pytest tests/ -x -q

# Validation artefacts
python -c "from mais.study.professional import build_professional_study"
```

---

*Ce document est la seule source de vérité. Toute décision de conception ou de priorisation doit en découler.*
*Dernière mise à jour : 2026-05-14 — Version 2.0 (pivot indicateur directionnel)*
