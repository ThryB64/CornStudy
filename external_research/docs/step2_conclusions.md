# Conclusions de l'étape 2

Date : 2026-06-12. Livrables : 25 fiches sources, `ideas_matrix.csv` enrichie (45 idées, +8 nouvelles), `experiment_candidates.csv` (18 expériences), revue structurée, avancement.

## 1. Meilleures idées à tester (ordre proposé pour l'étape 3)

### Vague P0 — fondations (peu coûteuses, débloquent tout)

1. **EXT025 — baselines RW/futures/drift** (Reeve-Vigfusson) : tableau de référence pour CBOT, EMA officiel et basis, H5/H20/H40/H90 + DM-test. Trivial, sans risque, conditionne la lecture de tout le reste.
2. **EXT006 — méthode de roll** (RollFutures) : règle causale volume J-1, mesure d'artefacts, sensibilité de basis_z au roll. Hygiène qui protège V13-V17 et tous les EXT courbe.
3. **EXT026 — pipeline WASDE vintage** (wasdeparser, à cloner) : valeurs telles que publiées, vérification historique sur 3 rapports. Débloque EXT007/EXT008/EXT024/EXT038/EXT043.

### Vague P1 — fondamentaux à fort prior

4. **EXT027 — surprises crop progress/condition** (Lehecka) : la feature la plus actionnable du programme (donnée publique datée lundi, mécanisme prouvé, asymétrie documentée). Inclut le test 2 étages EXT041 (météo de stade → notation), dont l'étage 1 se teste SANS marché.
5. **EXT018 — prime météo new-crop** (Li-Hayes-Jacobs, Janzen) : réplication descriptive puis test conditionnel ; + EXT042 : corrélation prime US ↔ prime EMA (décomposition économique de notre objet).
6. **EXT007 — features de rapports USDA élargies** (calendrier Grain Stocks/Plantings/Acreage × saison) : event-study vol + drift post-rapport ; module le veto WASDE V9.
7. **EXT005 + EXT039 — courbe et full carry** : quantifie V125 (NARROWING) ; dépend de EXT006.

### Vague P2 — extensions structurées

8. **EXT003/EXT040 — COT Managed Money** (extrêmes/flux, calendrier publication vendredi à construire d'abord) : clôture honnête du dossier COT (V18 n'a falsifié que le net total).
9. **EXT013/EXT044 — VECM CBOT↔EMA** : formalisation publiable de V21 ; vitesse d'ajustement comme intrant machine d'état.
10. **EXT024/EXT038/EXT043 — offre régionale et stocks-to-use** (AGRICAF) : benchmark fondamental long horizon + test inédit : l'anomalie d'offre UE+Ukraine explique-t-elle le NIVEAU de la prime ?
11. **EXT009 (fusion 009+010+045) — vol GARCH/HAR/EGARCH** : meilleure vol conditionnelle pour les gates et drawdown_risk ; inverse leverage des grains.
12. **EXT004 — marge crush éthanol** (H60+, contexte de demande, pas signal court).
13. **EXT033 — révisions de prévisions météo** : la seule voie météo prédictive cohérente avec V45 — data-gated (archive courte), test forward saison 2026.

### Vague P3/P4 — benchmarks et diagnostics différés

EXT011 (trend EWMAC figé), EXT012 (OU expandant), EXT014 (DMA diagnostic), EXT015 (SHAP dans le split), EXT016 (NBEATSx, conditionnel, verdict attendu REJECT).

## 2. Idées rejetées (avec justification)

- **Day-trading des annonces USDA** : l'ajustement est intraday (Huang-Serra-Garcia), inaccessible en quotidien — les EXT événements ciblent vol et fenêtres post-rapport.
- **Répliquer les chiffres CropProphet** : backtest vendor invérifiable — on garde le principe (révisions), pas les résultats.
- **Réutiliser les CSV de RollFutures comme données** : provenance/licence inconnues — méthode seulement.
- **Sentiment Weibo/Dalian (PAPER019/020 volet texte)** : marché chinois non transférable ; si texte un jour, attention (volume/persistance GDELT) > sentiment, bloc 4.
- **crop-price-prediction (REPO001)** : projet étudiant sans baseline ni protocole temporel — contre-exemple pédagogique, rien à reprendre.
- **AgriJedi** : démo LLM sans évaluation — catalogue de sources EU tout au plus.

## 3. Idées à garder pour plus tard

- **EXT022 satellite/NDVI** (Piette, Sentinel-2) : mécanisme plausible (proxy d'info USDA) mais archive satellite absente chez nous → `not_ready_data_missing`.
- **EXT030 DDG** : inventaire des séries AMS d'abord ; sans séries fiables → DATA_BLOCKED (la marge crush simplifiée reste testable).
- **EXT021 TSFM** : risque de mémorisation/contamination temporelle élevé, après tout le reste.
- **EXT031 régimes biofuel** : descriptif, sert de garde-fou à EXT024 plutôt que d'expérience autonome.
- **PATENT007 coût de carry variable** : raffinement de EXT005 en phase 2.
- **Options/vol implicite** (do-corn-options, PriceAnalysis ch. 05-08 en ligne) : données options à sourcer, bloc 4.

## 4. Risques majeurs identifiés

1. **Fuites de calendrier** : COT mardi→vendredi (calendrier à construire et PROUVER) ; WASDE valeurs révisées (vintages EXT026 obligatoires) ; notations lundi 16h ET → J+1. Tout EXT événement a son prérequis calendrier listé dans `experiment_candidates.csv`.
2. **Mélange de régimes** (Carter et al.) : relations stocks→prix et énergie→corn instables aux ruptures de politique — dater les régimes ex ante (2006, 2020, 2022), estimer en expandant.
3. **Significativité illusoire aux horizons longs** : H60-H252 mensuel = très peu d'observations indépendantes — LOYO + DM prudents, accepter des conclusions descriptives.
4. **Chiffres de fiches non vérifiés** : les fiches papers reposent sur abstracts + littérature ; chaque fiche porte une note `à vérifier` — récupérer les PDF prioritaires (Singh, Brignoli, AGRICAF) avant d'écrire des claims dans le rapport professionnel (règle projet : pas de claim non implémenté/vérifié).
5. **Profil de pertes asymétrique du short de prime** (EXT018 comme chez nous) : espérance positive ≠ stratégie viable — documenter les queues (2012) systématiquement.

## 5. Données manquantes (récapitulatif)

| Donnée | Pour | Piste |
|---|---|---|
| Vintages WASDE datés publication | EXT007/008/024/038/043 | wasdeparser (cloner) ou archives USDA directes |
| Calendrier de publication COT | EXT003/040 | Historique release dates CFTC |
| NASS Crop Progress/Condition hebdo | EXT027/041 | API QuickStats (public, gratuit) |
| Spot physique UE (Bologne/FranceAgriMer) | EXT013 volet 2 | FranceAgriMer = gratuit, à sourcer |
| Séries DDG | EXT030 | USDA AMS feed grains (qualité incertaine) |
| Archive prévisions météo profonde | EXT033 | V136 (2026+) + previous-runs Open-Meteo |
| Archive satellite | EXT022 | Non prioritaire |
| PDF : Singh 2020, Brignoli, AGRICAF | fiabilisation des fiches | accès libre probable (thèse IState, revues) |

## 6. Plan proposé pour l'étape 3

1. **Tickets P0** (3 tickets, ~simples/moyens) : EXT025, EXT006, EXT026 — codables immédiatement dans `experiments/external_tests/EXT###_…/`, résultats sous `results/external_tests/`, chacun conclu KEEP/IMPROVE/REJECT/DATA_BLOCKED.
2. **Acquisition data en parallèle** : clonage wasdeparser, calendrier COT, QuickStats NASS, PDF prioritaires.
3. **Tickets P1** (4 tickets) : EXT027 (avec étage 1 de EXT041 comme gate), EXT018+EXT042, EXT007, EXT005+EXT039 (après EXT006).
4. **Revue intermédiaire** après P0+P1 : mise à jour de `ideas_matrix.csv` (statuts), fiches des sources restantes au fil du besoin, décision sur P2.
5. **Règles inchangées** : aucun import vers le modèle principal ; intégration éventuelle = ticket projet séparé après review (protocole étape I) ; holdout 2024 verrouillé.

## 7. Réponses aux six questions de l'étape

1. **Sources vraiment utiles** : Lehecka, Li-Hayes-Jacobs/Janzen, Hu et al., Mallory (livre+RollFutures), Reeve-Vigfusson, AGRICAF, Penone et al., cot_reports, wasdeparser, NCGA 2022, Carter et al., Mallory-Hayes-Irwin.
2. **Ce qu'elles apportent** : voir revue (`external_research_review_step2.md`) — 5 convergences externes↔internes confirmées, 2 tests inédits sur la prime (EXT042, EXT043).
3. **Idées testables** : 45 dans la matrice, dont 8 nouvelles ; 18 expériences cadrées dans `experiment_candidates.csv`.
4. **EXT à lancer en premier** : EXT025 → EXT006 → EXT026, puis EXT027/EXT018/EXT007/EXT005.
5. **Risques à éviter** : §4 ci-dessus (calendriers, vintages, régimes, horizons longs, chiffres non vérifiés).
6. **Étape 3** : §6 ci-dessus — 3 tickets P0 + acquisition data, puis 4 tickets P1, sans toucher au modèle principal.
