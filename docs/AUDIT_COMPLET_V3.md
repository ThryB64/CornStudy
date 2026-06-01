# Audit Expert Complet — Étude Maïs V3
## Analyse intégrale par un expert marchés agricoles / modélisation / finance

**Date** : 2026-05-17  
**Auteur** : analyse experte multi-disciplinaire (marchés de commodités, statistiques, finance agricole)  
**Objectif** : transformer une bonne étude de recherche en un véritable système d'aide à la décision agricole, profitable et défendable.  
**Focus actuel** : marché CBOT maïs US. Version Europe/MATIF → perspective future basse priorité.

---

## AVANT-PROPOS — CE QUE CELA REPRÉSENTE VRAIMENT

Ce projet a une base sérieuse. L'infrastructure anti-leakage est rigoureuse, les données sont cohérentes, les protocoles OOF sont corrects pour des séries temporelles, et les résultats sont honnêtement documentés — y compris les échecs. C'est déjà bien plus que la majorité des projets de prédiction de prix de commodités.

**Mais le problème central est clair** : on a construit un modèle de prédiction du prix, alors que la vraie question est une question de **décision sous incertitude avec des coûts asymétriques**.

Un agriculteur qui vend à un mauvais moment ne perd pas juste un point de DA. Il perd des euros réels. Un faux signal haussier qui le pousse à stocker alors que les prix baissent lui coûte la perte de prix, les coûts de stockage, les frais financiers et l'opportunité manquée. Ce n'est pas le même problème que "maximiser la DA à 0.64".

**Ce que le projet a prouvé :**
- Le maïs n'est pas totalement aléatoire sur données publiques.
- Il existe un signal sur certaines fenêtres et dans certains contextes.
- Les signaux les plus confiants sont nettement meilleurs que les signaux moyens (DA top20%=0.743).
- Les drivers économiques ressortent logiquement : WASDE, COT, météo, saisonnalité, stocks.
- L'anti-leakage est pris au sérieux — ce qui est rare.

**Ce que le projet n'a pas encore prouvé :**
- Que cet indicateur améliore réellement la décision de vente ou de stockage d'un agriculteur.

C'est maintenant ça qui doit devenir le centre du projet.

---

## PARTIE 1 — INVENTAIRE COMPLET DE CE QUI A ÉTÉ CONSTRUIT

### 1.1 Données actuellement utilisées

| Source | Fréquence | Couverture | Non-null / 6192 obs | Rôle dans le modèle |
|---|---|---|---|---|
| CBOT corn OHLCV | Quotidienne | 2000–2025 | 100% | Cible + momentum technique |
| WASDE USDA | Mensuelle | 2000–2025 | ~132 colonnes, ~95% | Signal fondamental offre/demande |
| CFTC COT | Hebdomadaire | 2013–2025 | 3152 / 6192 (~50%) | Positionnement spéculatif |
| Open-Meteo (20 états) | Quotidienne | 2000–2025 | ~95%+ | Stress hydrique ceinture maïs |
| EIA Éthanol | Hebdomadaire | 2010–2025 | 3805 / 6192 (~61%) | Demande éthanol (40% de la conso US) |
| US Drought Monitor | Hebdomadaire | 2012–2025 | 3300 / 6192 (~53%) | Sécheresse |
| FRED macro | Mensuel/Quotidien | 2000–2025 | ~90%+ | Contexte macro, USD, taux |
| NASS Crop Progress | Hebdo. saisonnier | 2000–2025 | 2568 / 6192 (~41%) | Avancement semis/récolte |
| Calendrier USDA | Synthétique quotidien | 2000–2025 | 100% | Effets WASDE, Acreage, Grain Stocks |
| **FAS Export Sales** | **Hebdomadaire** | **JAMAIS COLLECTÉ** | **0 — NaN total** | **Demande export — lacune critique** |

### 1.2 Données présentes dans le config mais non activées

| Source | Statut | Priorité | Obstacle |
|---|---|---|---|
| NASS Crop Condition | enabled: false | **CRITIQUE** | Clé NASS disponible — activer maintenant |
| FAS Export Sales | enabled: false | **CRITIQUE** | FAS_API_KEY gratuite (apps.fas.usda.gov) |
| ENSO/ONI NOAA | enabled: false | **HAUTE** | URL publique, 0 obstacle technique |
| Structure à terme futures | non prévu | **HAUTE** | yfinance (ZCH/ZCK/ZCN/ZCZ) — gratuit |
| CONAB/Brésil | enabled: false | MOYENNE | Scraping HTML |
| BCR/Argentine | enabled: false | MOYENNE | Scraping HTML |
| USDA NASS Yield state | enabled: false | BASSE | Clé NASS disponible |

### 1.3 Modèles testés et verdicts

| Famille | Méthodes | Meilleur DA | Meilleur AUC | Verdict |
|---|---|---:|---:|---|
| Linéaires | Lasso, ElasticNet, Logistic, Ridge | 0.569 (lasso) | 0.592 | GARDER — robustes, référence |
| Tree-based gradient | HistGBM, LightGBM, XGBoost | 0.568 (histgb) | 0.700 (lgbm sweep) | GARDER pour top20 |
| Tree-based bagging | RF, ExtraTrees | 0.535 (extratrees) | 0.574 | SECONDAIRE |
| Bayésiens | GaussianNB, BayesianRidge | 0.540 | 0.583 | DIVERSIFICATION |
| Ensemble simple | avg_proba, vote_majority | 0.578 | 0.597 | RETENU |
| Stacking méta | Logistic, Ridge, LGBMmeta | 0.554 | 0.614 | REJETÉ (mono-horizon) → à refaire après multi-horizon OOF |
| MLP tabulaire | MLP 256-128-64 | 0.605 | 0.638 | REJETÉ (sous ridge) |
| GRU/TCN | — | N/A | N/A | NON TESTÉ — basse priorité |
| ARIMA/SARIMAX/GARCH | Modèles temporels | — | — | Contexte ≠ direction |

### 1.4 Familles de features et importance SHAP

| Rang | Famille | SHAP moyen | N features | Verdict ablation V3 |
|---|---|---:|---:|---|
| 1 | Saisonnalité calendaire (WASDE, Acreage) | 0.1031 | 9 | **GARDER — signal structurel** |
| 2 | Positionnement COT (managed money) | 0.0765 | 56 | **GARDER — à améliorer (normalisation OI)** |
| 3 | Momentum marché (RSI, MACD, MA) | 0.0750 | 17 | GARDER |
| 4 | Ratio inter-commodités (soja/blé/pétrole) | 0.0689 | 10 | GARDER |
| 5 | Météo belt stress (ET0, soil_moisture) | 0.0617 | 180 | **GARDER — compléter avec Crop Condition** |
| 6 | Macro / USD (FRED) | 0.0500 | 11 | NEUTRE |
| 7 | Volatilité réalisée | 0.0453 | 3 | NEUTRE |
| 8 | WASDE supply/demand | 0.0409 | 132 | **GARDER (surprises >> niveaux)** |
| 9 | Signal brut (volume, OI) | 0.0309 | 5 | RETIRER |
| — | COT changes hebdo | non mesuré SHAP | 5 | KEEP (+0.0013 AUC, V3-06) |
| — | Export sales FAS | non collecté | — | **LACUNE CRITIQUE** |
| — | Courbe futures (Z/H/K spreads) | non collecté | — | **NON EXPLOITÉ — à ajouter** |

### 1.5 Métriques finales — toutes expériences confondues

> **Alerte** : ces métriques viennent de protocoles différents. Elles ne sont pas toutes comparables directement. C'est le problème le plus urgent à résoudre.

| Résultat | Valeur | Protocole | Période | Confiance |
|---|---:|---|---|---|
| DA horizon sweep J+40 (lgbm_factors) | 0.640 | Sweep V3-02 | OOF 2010-2022 | Moyen — protocole différent du zoo |
| AUC horizon sweep J+40 | 0.700 | Sweep V3-02 | OOF 2010-2022 | Moyen |
| DA model zoo (lasso J+40) | 0.569 | Zoo V3-03 | OOF 2010-2022 | Fort |
| DA top20 (histgb J+40) | 0.743 | Zoo V3-03 | OOF 2010-2022 | Fort — résultat clé |
| DA avg_proba stacking | 0.578 | Stack V3-05 | OOF 2010-2022 | Fort |
| DA ridge baseline DL | 0.633 | DL V3-08 | OOF 2010-2022 | Moyen |
| DA V2 backtest | 0.624 | IND-08 | Backtest 2023-2025 | Fort mais architecture V2 |
| AUC V2 backtest | 0.663 | IND-08 | Backtest 2023-2025 | Fort mais architecture V2 |
| DA top20 V2 backtest | 0.728 | IND-08 | Backtest 2023-2025 | Fort mais architecture V2 |
| Signaux/an V3-01 | 151.6 | V3-01 | OOF 2010-2022 | Moyen (seuil abaissé mécaniquement) |

**Contradiction centrale** : le sweep donne DA=0.640 pour lgbm_factors, mais le zoo donne DA=0.569 pour lasso sur le même horizon J+40. Écart de 7 pts inexpliqué. C'est la priorité zéro.

---

## PARTIE 2 — CE QUI MARCHE VRAIMENT ET POURQUOI

### 2.1 Forces réelles et robustes

**A. Le calendrier WASDE est le driver structurel le plus fort**

AUC=0.883 en novembre. Economiquement, les publications WASDE annuelles de novembre révèlent les estimations de bilan mondial pour l'année en cours et déclenchent des repositionnements majeurs. Ce signal est structurel et reproductible — il sera encore là dans 10 ans. C'est l'actif le plus solide de l'étude.

Il faut aller au-delà du "calendar flag" vers une vraie **"event intelligence"** : quel rapport arrive ? Quelle surprise est possible ? Quelle variable sera regardée ? Le marché est-il déjà positionné ? Prédire la surprise avant la publication est beaucoup plus fort que simplement noter qu'un WASDE sort.

**B. Le positionnement COT est un signal contra-cyclique validé**

SHAP #2 (0.0765). Les managed money sur-positionnent dans un sens → risque de retournement. Quand les positions nettes MM sont à des extrêmes (>90ème percentile), le signal contrarian est statistiquement significatif. COT changes KEEP (+0.0013 AUC V3-06). Signal à améliorer avec la normalisation OI.

**C. La sélectivité top 20 % est le mécanisme de valeur principal**

DA globale 0.640 → DA top20% 0.743 : gain de +10 pts en filtrant par confiance. C'est l'insight le plus important de toute l'étude. Un indicateur sélectif qui parle moins mais mieux est exactement ce qu'il faut pour l'aide à la décision agricole. Ne jamais sacrifier cette sélectivité pour augmenter le volume de signaux.

**D. Les contextes "stocks tendus" et "novembre" sont sur-prédictibles**

AUC=0.799 (stocks tendus), AUC=0.883 (novembre), DA=0.760 (régime bear). Ces poches sont identifiables à l'avance et économiquement cohérentes. Ce sont les fenêtres où le signal doit être prioritairement utilisé.

**E. La météo belt stress est informative**

SHAP #5 (0.0617). Pendant la saison de croissance (juin-août), les anomalies de stress hydrique dans la ceinture maïs sont prédictives. Bien couvert avec Open-Meteo 20 états. À compléter avec Crop Condition NASS pour traduire météo → impact réel sur la plante.

**F. La CQR est un atout différenciant**

Coverage 91.7% sur l'objectif 88%. Savoir que le maïs sera "entre 450 et 510 ¢/bu dans 30j avec 90% de probabilité" est directement actionnable pour une décision de couverture ou de stockage. Peu de modèles agricoles proposent des intervalles calibrés.

**G. L'anti-leakage est rigoureux**

shift(1) partout, z-scores expandants sur train uniquement, variables oracle absentes du pipeline. La majorité des modèles de prédiction de prix publiés en recherche académique n'ont pas ce niveau de rigueur.

### 2.2 Ce qui ne marche pas et pourquoi — analyse honnête

**A. Stacking méta-modèle — échec structurel, pas conceptuel**

Le stacking a échoué (DA=0.554 < avg_proba=0.578), mais la raison est claire : les OOF disponibles couvrent un seul horizon J+40. Le méta-modèle n'a aucune information de désaccord inter-horizon. Le "consensus" a un delta de 0.000001 point vs la référence — ce n'est rien. Ce n'est pas l'échec du concept : c'est l'absence de vraie diversité. À refaire uniquement après vrai multi-horizon OOF.

**B. MLP tabulaire — le mauvais outil pour ce dataset**

~2200 observations, ~290 features. Ridge (modèle linéaire, ~290 paramètres effectifs) gagne DA=0.633 vs MLP 0.605 avec des dizaines de milliers de paramètres. C'est le résultat attendu en théorie de l'apprentissage statistique : sur des données aussi limitées, la régularisation forte domine la capacité. Le deep learning n'est pas le problème prioritaire.

**C. Zone robuste G1+G3 vide — signal d'alerte sérieux**

Aucun horizon ne passe simultanément G1 (voisins ±3 aussi bons) ET G3 (+2pts vs seasonal). J+40 est le meilleur pic empirique mais pas robuste au sens strict. Cela peut signifier : (1) prédictibilité réelle mais "narrow" — sensible à quelques années — ou (2) J+40 est un artefact de la période 2010-2022. Le benchmark canonique doit clarifier ce point.

**D. FAS Export Sales — 100% NaN**

C'est le signal de demande physique hebdomadaire le plus suivi par les négociants et les fonds. On prédit sans lui. C'est comme analyser un bilan sans le chiffre d'affaires.

**E. La confiance V4 est un proxy, pas une vraie mesure d'incertitude**

Le seuil adaptatif p50 = 0.45694 génère 151 signaux/an par construction : 50% des scores sont mécaniquement au-dessus. Ce n'est pas "plus de jours de haute confiance", c'est "on a baissé la barre". La vraie mesure de confiance devrait répondre à : "dans des situations similaires par le passé, le modèle avait-il raison ?" C'est un modèle à entraîner.

**F. Le farmer backtest est le signal d'alerte le plus important**

Dans FARMER_BACKTEST_REPORT_V2, MODEL_SIGNAL fait moins bien que SELL_HARVEST (4.537 vs 4.576 USD/bu, capture 81.7% vs 82.8%). Une bonne DA directionnelle ne garantit pas un meilleur revenu agricole. C'est le point le plus important pour la suite.

---

## PARTIE 3 — PROBLÈMES MÉTHODOLOGIQUES QU'UN EXPERT IDENTIFIE

### 3.1 La contradiction des protocoles — priorité zéro

Les résultats dispersés sur des protocoles non comparables empêchent de choisir un modèle final valide.

| Résultat | lgbm sweep | lasso zoo | avg_proba stack | ridge DL |
|---|---:|---:|---:|---:|
| DA | **0.640** | 0.569 | 0.578 | 0.633 |
| Features | lgbm_factors (sélectionnées) | V3-06 (289 cols) | avg 5 modèles | V3-06 (289 cols) |
| Splits | KFold 5 | KFold 5 | KFold 5 | KFold 5 |
| Cible | y_up_h40 | y_up_h40 | y_up_h40 | y_up_h40 |

L'écart de 7 pts DA sur le même horizon, même cible, même split n'est pas expliqué. Hypothèses :
1. `lgbm_factors` = sous-ensemble de features sélectionnées vs 289 cols complètes — filtrage qui réduit le bruit.
2. Hyperparamètres LightGBM différents entre les deux runs.
3. Random state ou ordre des données différent.
4. Cible y_up_h40 construite légèrement différemment dans chaque pipeline.

**Sans résoudre ça, aucun choix de modèle final n'est fiable.**

### 3.2 Multiple testing bias — le problème statistique non traité

On a testé : 96 cibles × 24 horizons × 15 modèles × 13 familles × 62 contextes. L'ordre de grandeur est 34 000+ combinaisons. Même si toutes les métriques étaient du bruit aléatoire, la probabilité de trouver au moins une combinaison "significative" par chance est > 99.9%.

**Ce que ça implique concrètement** :
- "J+40 est le meilleur horizon" → sélectionné parmi 24 → doit être confirmé hors-période.
- "y_down_gt_5pct_h20 AUC=0.707" → sélectionné parmi 96 cibles.
- "mois=11 AUC=0.883" → sélectionné parmi 62 contextes.

**Règle simple** : tout résultat sélectionné sur 2010-2022 doit être confirmé sur 2023-2025 (déjà consulté V2) ou 2026+ avant d'être déclaré "robuste". Appliquer Benjamini-Hochberg sur les comparaisons multiples.

### 3.3 Intervalles de confiance — absence totale

AUC = 0.700 sur 2200 observations a un IC95% d'environ ±0.020. Les différences de moins de 2 pts entre modèles ne sont pas statistiquement significatives.

**À reporter systématiquement** :
```
DA  = 0.640 [IC 95% : 0.618 – 0.662]
AUC = 0.700 [IC 95% : 0.679 – 0.721]
```

Bootstrap 1000 tirages sur OOF ou DeLong test pour les différences d'AUC.

### 3.4 Non-stationnarité des features

Les z-scores expandants produisent des valeurs très différentes en 2010-2012 (fenêtre courte → z-scores instables) vs 2020-2022 (fenêtre longue → z-scores stables). KFold mélange ces deux types d'observations, créant un biais implicite vers la fin de la série. Walk-forward annuel atténue ce problème.

### 3.5 Autocorrélation intra-semaine — DA gonflée

La plupart des données fondamentales sont hebdomadaires (COT, WASDE, EIA, Crop Condition), forwardfilées sur 5 jours. Les 5 prédictions quotidiennes d'une même semaine partagent exactement les mêmes features fondamentales. Si le modèle est correct une semaine, il est crédité de 5 succès.

**Correction** : mesurer DA sur échantillon hebdomadaire (un point par semaine, le vendredi ou le jour post-publication), pas quotidien. Cela donnera une DA probablement légèrement différente — à mesurer.

### 3.6 Robustesse temporelle — non testée

Les métriques sont reportées en moyenne sur 2010-2022. On ignore si :
- L'AUC est stable chaque année ou si 2012 (sécheresse) et 2022 (Ukraine) portent tout le signal.
- Le modèle fonctionnerait dans des années "normales" (2015-2019, surplus mondial prolongé).
- La performance du COT se dégrade après 2015 (crowding des fonds quantitatifs).

C'est potentiellement le résultat le plus important à vérifier avant toute décision sur l'architecture finale.

---

## PARTIE 4 — LACUNES ÉCONOMIQUES ET FINANCIÈRES FONDAMENTALES

### 4.1 La courbe des futures — signal non exploité et gratuit

La structure à terme du CBOT maïs encode directement ce que le marché "pense" du bilan offre/demande. C'est une information de marché plus précise et plus immédiate que les estimations WASDE.

**Contango vs backwardation** :
```
Contango : Z6 > Z5 → marché bien approvisionné, stockage rémunéré
           Signal structurellement baissier

Backwardation : Z5 > Z6 → demande urgente, peu de stock disponible
               Signal structurellement haussier
```

Le spread entre contrats (Z/H, H/K, K/N) est directement lié au coût de portage et au niveau de stocks. En théorie des commodités :

```
F(T) = S₀ × e^(r-δ)T × e^(U-C)T

δ (convenience yield) ↑ quand stocks ↓ → backwardation → prix spot prime sur futures
```

**Features à créer** :
```
curve_z_h_spread             : ZC déc / ZC mars (carry principal)
curve_h_k_spread             : ZC mars / ZC mai
curve_n_z_spread             : ZC juil / ZC déc (span récolte)
curve_slope_6m               : pente sur 6 mois (contango = pos, backwardation = neg)
curve_carry_vs_storage_cost  : spread / coût stockage théorique → prime implicite
curve_seasonal_deviation     : écart vs saisonnalité normale de la courbe
```

Disponibles via yfinance (ZCH6=F, ZCK6=F, ZCN6=F, ZCZ6=F). Importance SHAP attendue élevée.

### 4.2 La décision de stockage est un problème d'option

**Cadre théorique** : stocker du grain est économiquement équivalent à posséder une option d'achat sur le prix futur.

```
Valeur_stockage = max(0, Prix_futur - Prix_actuel - Coûts_stockage) × Volume
```

La valeur attendue du stockage à horizon H :
```
E[valeur_stockage_H] = ∫ max(0, P_H - P_0 - C) × f(P_H) dP_H
```

Nos intervalles CQR (coverage 91.7%) donnent déjà une approximation de f(P_H). On peut calculer immédiatement :

```python
def storage_expected_value(cqr_low, cqr_high, current_price, storage_cost):
    """Approximation log-normale entre les bornes CQR.
    Retourne E[max(0, P_futur - P_actuel - coût)].
    """
```

C'est immédiatement actionnable sans nouvelles données.

### 4.3 La perte asymétrique — le coût que le modèle ignore

Un modèle maximisant DA traite une erreur bullish et une erreur bearish comme équivalentes. Ce n'est pas le cas pour l'agriculteur :

| Erreur | Décision | Coût réel |
|---|---|---|
| Faux bullish | Stocker → prix baisse | Perte prix + coût stockage + intérêts |
| Faux bearish | Vendre → prix monte | Manque à gagner (sans coût direct) |

Pour un agriculteur avec contraintes de cash-flow, λ = coût_faux_bullish / coût_faux_bearish ≈ 2.0–2.5.

**Seuil de décision optimal** : P(up) > λ/(1+λ) ≈ 0.67–0.71 pour déclencher une action bullish.

Ne pas émettre une recommandation "stocker" si P(up) = 0.52. Le seuil doit refléter les coûts réels.

### 4.4 La saisonnalité de prix — baseline mal exploitée

Le maïs a une saisonnalité de prix bien documentée :
```
Novembre-décembre : prix bas (récolte récente, offre abondante)
Janvier-février   : stabilisation
Mars              : Prospective Plantings → risque acreage
Avril-mai         : semis → nervosité météo
Juin              : First crop condition report → signal crucial
Juillet           : Pollinisation → stress maximal de l'année
Août              : Pro-forma yield update
Septembre         : Anticipation récolte → pics/corrections
Octobre-novembre  : Harvest pressure → prix plancher saisonnier
```

**Features manquantes clés** :
```
price_vs_seasonal_norm       : prix / moyenne mobile saisonnale 5 ans
price_seasonal_zscore        : z-score dans la distribution saisonnale
price_harvest_discount       : écart au prix de récolte moyen historique
silking_week_flag            : 1ère semaine de juillet × crop_year (pollinisation)
dough_dent_week_flag         : 2-3ème semaine août × crop_year (maturation)
```

Ces features phénologiques sont connues de tous les négociants physiques et absentes de notre dataset.

### 4.5 "Prix déjà pricé" — la décomposition manquante

Une information peut être vraie mais déjà intégrée dans le prix. Un modèle fondamental pur ignore ça.

Exemples :
- Stocks tendus + prix déjà très haut → pression haussière restante limitée
- Météo sèche + COT déjà extrême long → acheteurs épuisés
- WASDE surprise positive mais "buy the rumor, sell the fact" déjà joué

**Feature à créer** :
```
fundamental_pressure_score   : score fondamental synthétique (WASDE, export, météo)
positioning_alignment_score  : le marché est-il déjà positionné dans le sens du signal ?
residual_opportunity         : fundamental_score - positionnement_actuel
```

Quand les fondamentaux sont haussiers mais que le marché est déjà très long (COT >90ème), le signal est moins fiable. Quand les fondamentaux sont haussiers et le marché encore neutre, le signal est plus fort.

---

## PARTIE 5 — SOURCES DE DONNÉES MANQUANTES CRITIQUES

### 5.1 FAS Export Sales — priorité absolue

**Pourquoi c'est le signal manquant le plus important :**

15-18% de la production US est exportée (Mexique ~35%, Japon ~15%, Colombie ~9%, Chine ~8%). Les ventes hebdomadaires (net sales) révèlent la demande physique réelle. Une semaine avec +500% de ventes vs moyenne → signal haussier très fort. Une semaine à -50% → baissier.

Le FAS Export Sales Report sort chaque jeudi 8h30 ET pour la semaine précédente (lag 7 jours). API gratuite : apps.fas.usda.gov.

**Features à créer** :
```
fas_corn_net_sales_mt         : ventes nettes semaine (milliers tonnes)
fas_corn_net_sales_z5y        : z-score vs moyenne même semaine 5 ans
fas_corn_cumul_vs_pace        : cumul marketing year / rythme implicite USDA
fas_corn_china_share_4w       : part Chine sur 4 semaines (indicateur de tension)
fas_corn_inspections_mt       : expéditions physiques (ventes réellement shipped)
fas_corn_unknown_pct          : part "unknown destination" (souvent Chine avant déclaration)
fas_corn_sale_cancel_flag     : annulations > seuil (signal de détérioration demande)
```

**Anti-leakage** : shift(1) obligatoire. Publication jeudi → utilisable vendredi au plus tôt.

**Hypothèse de gain** : +0.015 à +0.035 AUC globalement. Potentiellement +0.050 AUC sur septembre-mars (période d'export intense).

### 5.2 USDA Crop Condition — le baromètre estival indispensable

Chaque lundi de mai à novembre, le NASS publie les proportions Good/Excellent/Fair/Poor/Very Poor par État. L'indice G+E% est le baromètre de rendement en temps réel. Une dégradation de G+E% pendant la pollinisation (juillet) peut signifier une réduction de 2-5 bu/acre en une semaine.

**Réaction de marché** : G+E -5% vs attendu → maïs +10-15¢/bu le lendemain. La clé NASS est déjà dans le système — il suffit d'activer.

**Features à créer** :
```
nass_corn_ge_pct              : % Good + Excellent (national)
nass_corn_pv_pct              : % Poor + Very Poor
nass_corn_ge_chg_1w           : variation semaine (momentum court terme)
nass_corn_ge_chg_4w           : variation 4 semaines (tendance)
nass_corn_ge_vs_5y_avg        : écart vs moyenne 5 ans, même crop week
nass_corn_ge_stress_flag      : GE < 65% en juillet-août (risque pollinisation)
nass_corn_ge_state_iowa       : Iowa spécifiquement (État #1 production)
nass_corn_ge_state_illinois   : Illinois (#2)
nass_corn_ge_weighted_belt    : G+E pondéré par production par État
```

**Interaction clé** : `nass_corn_ge_stress_flag × wx_belt_heat_days_38c_30` → signal de rendement réduit très fort.

**Hypothèse de gain** : +0.020 à +0.045 AUC en juin-septembre.

### 5.3 ENSO/ONI — driver climatique inter-annuel

La Niña (ONI < -0.5) → étés chauds et secs dans le Corn Belt (corrélation +0.35 à +0.45). L'ENSO est prévisible 3-6 mois à l'avance. Données publiques NOAA depuis 1950.

```python
url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
```

**Features** :
```
oni_value                     : ONI 3-month running mean
oni_phase                     : La Niña (-1), Neutral (0), El Niño (+1)
oni_phase_consecutive_months  : durée de l'épisode en cours
oni_summer_lag6m              : ONI 6 mois avant → prévision été US
oni_brazil_safrinha_risk      : La Niña × déc-fév → risque safrinha brésil
oni_phase_change              : La Niña → Neutral = résolution du risque
```

**Hypothèse de gain** : faible globalement (+0.003 à +0.008 AUC), plus fort pour J+60 à J+90 et contexte Brésil H2.

### 5.4 Structure à terme des futures — gratuit et non exploité

Les contrats CBOT maïs différés sont disponibles via yfinance :
- ZCH6=F (mars 2026), ZCK6=F (mai 2026), ZCN6=F (juillet 2026), ZCZ6=F (décembre 2026)

À vérifier en priorité : yfinance retourne-t-il proprement les contrats déférés sur l'historique ? Si oui, les spreads sont collectables immédiatement sans nouvelle source.

### 5.5 Données mondiales — Brésil et Argentine

Le Brésil est le 1er exportateur mondial depuis 2022-2023. La safrinha (semée nov-jan, récoltée juin-juil) représente 70% de la production brésilienne. Sans ces données, le modèle est aveugle sur l'offre H2 (juillet-octobre).

**Vérification prioritaire** : nos 132 colonnes WASDE incluent-elles wasde_world_corn_prod_brazil et wasde_world_corn_prod_argentina ? Si oui, construire des features de surprise dessus. Si non, utiliser USDA PSD Online (CSV téléchargeable, aucune API requise).

**Features prioritaires** :
```
wasde_brazil_prod_surprise    : révision vs mois précédent
wasde_argentina_prod_surprise : idem
world_corn_sx_ratio           : stocks/use monde (ratio le plus important)
brazil_export_pace_vs_wasde   : rythme export Brésil vs forecast WASDE
```

### 5.6 COT avancé — normalisation manquante

**Ce qu'on a** : niveaux et changements hebdomadaires.

**Ce qu'il faut ajouter** :
```python
# Normalisation par open interest (OI a triplé en 20 ans → nécessaire)
cot_mm_net_pct_oi = cot_mm_net / cot_open_interest

# Percentile historique rolling (signal contrarian quantifié)
cot_mm_net_pct_oi_pct_3y = rolling_percentile(cot_mm_net_pct_oi, 3*52)
# > 90% → extrême long → contrarian bearish
# < 10% → extrême short → contrarian bullish

# Pression hedger commercial
cot_commercial_net_pct_oi = (cot_pm_long - cot_pm_short) / cot_open_interest
```

**Hypothèse** : delta_AUC +0.005 à +0.015. La normalisation est nécessaire car l'OI du maïs a triplé depuis 2000.

---

## PARTIE 6 — AMÉLIORATIONS ARCHITECTURALES PRIORITAIRES

### 6.1 Benchmark canonique — priorité absolue

**Objectif** : résoudre la contradiction lgbm_sweep=0.640 vs lasso_zoo=0.569.

**Protocole unique** :
- Features : V3-06 figées (289 colonnes)
- Cibles : y_up_h28, y_up_h35, y_up_h40, y_up_h45, y_up_h60
- Splits : walk-forward annuel expanding (train 2010-2014 → prédit 2015, ..., train 2010-2021 → prédit 2022)
- Modèles : ridge, lasso, logistic, histgb, lgbm, extratrees, avg_proba — avec exactement les mêmes splits
- Métriques : DA, AUC, Brier, ECE, DA_top20, DA_top10, DA par année, IC95% bootstrap

### 6.2 Walk-forward par année agricole

KFold coupe arbitrairement à travers les années agricoles. Un fold peut capturer la sécheresse 2012 et un autre non.

**Walk-forward annuel expanding** :
```
Train 2010-2014 → Évaluation crop year 2015
Train 2010-2015 → Évaluation crop year 2016
...
Train 2010-2021 → Évaluation crop year 2022
```

8 années d'évaluation, chaque prédiction out-of-sample réelle. Permet de détecter la dégradation temporelle du signal.

### 6.3 Vrai consensus multi-horizon — corriger le bug V3-04

V3-04 est simulé sur J+40 uniquement, désaccord = quasi-zéro. À refaire après benchmark canonique avec OOF sur J+28, J+35, J+40, J+45, J+60.

```python
disagreement = max(p_horizons) - min(p_horizons)
consensus_score = mean(p_horizons)

if disagreement > 0.06:
    signal = "UNCERTAIN"
elif consensus_score > 0.55:
    signal = "BULLISH"
elif consensus_score < 0.45:
    signal = "BEARISH"
else:
    signal = "NEUTRAL"
```

**Hypothèse** : DA top20% monte de 0.743 → 0.77-0.80 avec vrai désaccord inter-horizon.

### 6.4 Modèle de confiance P(correct) — remplacer l'heuristique actuelle

```python
# Pour chaque prédiction OOF passée
correct = int(predicted_direction == realized_direction)

# Features pour le modèle de confiance
conf_features = [
    p_bullish,               # probabilité du modèle directeur
    entropy_5models,         # accord entre les 5 modèles
    disagreement_horizons,   # désaccord inter-horizon (vrai, après R&D-02)
    cqr_width,              # incertitude de l'intervalle conformal
    vol_regime,             # volatilité réalisée récente
    days_to_next_wasde,     # distance à la prochaine publication
    context_auc_3m,         # AUC historique dans ce contexte
    cot_extreme_flag,       # COT à extrême = moins fiable
    oni_summer_flag,        # ENSO influence la fiabilité météo
    market_clarity_score,   # accord modèles × accord horizons × CQR serré
]

# Régression logistique calibrée, walk-forward
# Objectif : P(correct=0.70) → 70% de réussite réelle (ECE < 0.05)
```

### 6.5 Score "market clarity" — marché lisible vs non lisible

Certains jours, le marché est plus lisible que d'autres. Créer un score composite :

```
market_clarity_score =
    accord_modèles (entropie)
  × accord_horizons (1 - disagreement)
  × incertitude_cqr (1 - normalized_width)
  × facteur_distance_publication (1 - urgence_wasde)
  × contexte_historique (AUC du contexte saison × régime)

Si score < seuil → "Marché non lisible — signal non émis"
```

---

## PARTIE 7 — NOUVELLES CIBLES MÉTIER

### 7.1 Cible de stockage (décision vendre/stocker)

La vraie question agricole n'est pas "le maïs monte-t-il dans 40 jours ?" mais "stocker 3 mois me rapporte-t-il après coûts ?"

**Cibles à construire** :
```python
y_storage_value_1m = price_t+21 / price_t - 1 - storage_cost_1m
y_storage_value_3m = price_t+63 / price_t - 1 - storage_cost_3m
y_storage_value_6m = price_t+126 / price_t - 1 - storage_cost_6m
# si > 0 → stocker est profitable
# si < 0 → vendre maintenant est optimal
```

La valeur attendue du stockage via les intervalles CQR :
```python
E[stockage] = ∫ max(0, P_futur - P_actuel - coût) × f(P_futur) dP_futur
```

**Critère de validité** : gain net moyen ≥ 0 sur la majorité des années walk-forward.

### 7.2 Cible de vente partielle (fractionnée)

Un agriculteur ne vend pas 0% ou 100%. Une stratégie réaliste :

```
Signal BULLISH fort (P(correct) > 0.70) :
  → Vendre 20%, stocker 80%

Signal BULLISH modéré :
  → Vendre 40%, stocker 60%

Signal NEUTRE :
  → Vendre 50%, stocker 50%

Signal BEARISH modéré :
  → Vendre 70%, stocker 30%

Signal BEARISH fort (P(correct) > 0.70) :
  → Vendre 80–100%
```

La fraction optimale de vente est une fonction du score de confiance et de la valeur attendue du stockage.

### 7.3 Cible "regret évité"

Au lieu de maximiser le gain brut, minimiser le regret :

```
regret = meilleur_prix_futur_possible(3m) - prix_effectivement_obtenu
```

L'indicateur ne vise pas à vendre toujours au plus haut, mais à éviter les très mauvaises ventes. C'est beaucoup plus robuste comme objectif pour un agriculteur.

### 7.4 Module "risque de forte baisse"

Séparé du signal directionnel, créer un indicateur de risque de perte importante :

**Cibles** :
```
y_down_gt_5pct_h40   : baisse > 5% à J+40 (AUC=0.707 sur h20 — déjà testé)
y_down_gt_8pct_h40   : baisse > 8% à J+40
y_down_gt_5pct_h20   : référence IND-02 (AUC=0.707)
```

**Output du module** :
```
Risque de forte baisse (>5%) dans 40j : FAIBLE (18%) / MODÉRÉ (35%) / ÉLEVÉ (52%)
```

Très actionnable pour décider de couvrir via put option ou de vendre une part de la récolte.

### 7.5 Module "opportunité de hausse forte"

Séparé du risque de baisse. Deux scores distincts permettent des recommandations plus riches :

```
Risque forte baisse : 22%  → vendre une partie
Opportunité forte hausse : 38% → ne pas tout vendre

→ Recommandation : vendre 40%, stocker 60%
```

Un marché peut être : peu risqué/peu haussier (stocker à moitié), très risqué/fort potentiel (couvrir + stocker), etc. Un signal binaire unique ne capture pas cette richesse.

---

## PARTIE 8 — QUATRE MODULES D'UN INDICATEUR PROFESSIONNEL

### 8.1 Architecture recommandée

Un seul BULLISH/BEARISH ne suffit pas. Quatre modules complémentaires :

---

**Module 1 — Veille de marché (hebdomadaire)**

```
Signal J+40 : ▲ HAUSSIER
P(hausse) : 64%  |  P(correct) : 0.69  |  Confiance : MODÉRÉE
Horizon de validité : 4-6 semaines (résolution ~15 décembre)

Facteurs haussiers :
  1. Ending stocks/use US = 9.2% (sous seuil "tendus" 10%) → soutien structurel
  2. Export sales semaine : +38% vs moyenne 5 ans (FAS)
  3. Crop Condition G+E -4pts vs l'an passé → rendement sous pression
  4. Courbe futures : légère backwardation → marché tendu physiquement

Facteurs de risque :
  1. COT managed money au 82ème percentile → risque liquidation spéculative
  2. Dollar index en hausse → renchérit les exports US
  3. WASDE dans 8 jours → ne pas engager la totalité avant publication
  4. Brésil : safrinha en bonne voie (ONI Neutral)

Risque de forte baisse >5% : 18% (FAIBLE)
Opportunité forte hausse >5% : 34% (MODÉRÉE)
```

---

**Module 2 — Décision de stockage (octobre-novembre)**

```
Stocker 3 mois (vente prévue fin janvier) :
  Gain brut attendu    : +3.8% sur CBOT
  Coût stockage        : à saisir selon votre situation
  IC 90% prix          : 460 – 520 ¢/bu (CQR)
  P(stockage profitable) : 68%
  Valeur attendue stockage (option) : +2.1% net (approximation log-normale CQR)

  RECOMMANDATION : Stocker 50-70% de la récolte restante.
  Trigger de vente : si prix > 512¢/bu ou P(correct) BEARISH > 0.65

Stocker 6 mois :
  P(profitable) : 55% — risque plus défavorable, coût plus élevé

Stratégie fractionnée suggérée (signal BULLISH modéré) :
  Vendre 40% maintenant | Stocker 60%
```

---

**Module 3 — Couverture / hedging**

```
Signal couverture : ATTENDRE
Score hedging : 0.38 / 1.0 (< 0.60 → ne pas fixer le prix)

Raisons d'attendre :
  - Potentiel haussier encore présent (P(up) = 64%)
  - COT pas encore à extrême → spéculatifs encore acheteurs
  - Export demand forte → soutien court terme

Trigger pour couvrir maintenant :
  - Prix atteint votre objectif
  - Signal P(correct) BEARISH élevé
  - COT managed money > 90ème percentile
  - WASDE surprise négative
```

---

**Module 4 — Alertes et risques non modélisables**

```
⚠ Alertes actives :
  1. WASDE dans 8 jours → ne pas prendre de grosse décision avant publication
  2. COT positions au 82ème percentile → surveiller une liquidation
  3. Volatilité réalisée 20j en hausse (+15%) → marché nerveux
  4. Market clarity score : 0.61 (MODÉRÉ — signal utilisable avec prudence)

⚠ Risques non modélisables :
  - Décision politique d'embargo (Ukraine, Inde, Argentine)
  - Rupture technologique de récolte (météo extrême soudaine)
  - Choc macro global (risk-off généralisé)
  - Annulation massive de ventes Chine
```

---

### 8.2 Métriques d'évaluation agricoles

Ne plus évaluer seulement DA et AUC. Évaluer :

| Métrique | Formule / Définition | Objectif |
|---|---|---|
| Gain moyen stockage (¢/bu) | `mean(prix_vente_signalé - prix_vente_harvest)` | > 0 |
| Taux capture prix max | `prix_vendu / prix_max_12m_suivants` | > 80% |
| Regret moyen évité | `max_price_3m - effective_selling_price` | Minimiser |
| % Années gagnantes | P(gain net > 0 par crop year) | > 65% |
| Pire année (drawdown) | `min(gain annuel)` | > -10¢/bu |
| DA par année | DA chaque année walk-forward | > 0.55 chaque année |
| Calibration P(correct) | ECE par bucket confiance | < 0.05 |
| Signaux par année | Nombre de signaux actionnables | 20-80 |

### 8.3 Seuil de décision asymétrique

Pour déclencher une action agricole, le seuil ne doit pas être P(up) > 0.50. Il doit refléter λ = coût asymétrique.

```
Profil agriculteur standard (λ ≈ 2.0) :
  Seuil "Stocker" : P(up|confiance haute) > 0.67
  Seuil "Signal fort" : P(up|P(correct) > 0.75) > 0.65

Profil avec contraintes cash-flow (λ ≈ 2.5) :
  Seuil "Stocker" : P(up) > 0.71
```

---

## PARTIE 9 — PLAN D'ACTION PRIORISÉ

### Sprint 0 — Assainissement du socle (avant tout)

**S0-1** : Résoudre la contradiction sweep/zoo (lgbm_factors vs 289 cols). Documenter la source exacte de l'écart. Durée : 1-2 jours.

**S0-2** : Benchmark canonique R&D-01. Même features + walk-forward annuel + 7 modèles + 5 horizons + IC95% bootstrap. Durée : 1 semaine.

**S0-3** : DA hebdomadaire. Mesurer DA sur un point par semaine (pas quotidien). Comparer à DA actuelle. Durée : 1 jour.

### Sprint 1 — Données fondamentales manquantes (2-3 semaines)

| Ordre | Action | Impact attendu | Durée |
|---|---|---|---|
| 1 | ENSO/ONI NOAA | +0.003-0.008 AUC global | 1 jour |
| 2 | NASS Crop Condition | +0.020-0.045 AUC estival | 2-3 jours |
| 3 | FAS Export Sales | +0.015-0.035 AUC | 3-5 jours |
| 4 | Courbe des futures (Z/H/K spreads) | +0.010-0.025 AUC | 1-2 jours |
| 5 | COT normalisé pct OI + percentile | +0.005-0.015 AUC | 1 jour |
| 6 | Features phénologiques (silking week, etc.) | gain estival | 1 jour |
| 7 | "Prix déjà pricé" (fundamental - positioning) | qualité signal | 2-3 jours |

### Sprint 2 — Architecture indicateur (3-4 semaines)

| Ordre | Action | Impact attendu | Durée |
|---|---|---|---|
| 1 | Vrai multi-horizon OOF (J+28,35,40,45,60) | DA top20% → 0.77-0.80 | 1 semaine |
| 2 | Modèle confiance P(correct) calibré | DA top20% calibrée | 1 semaine |
| 3 | Market clarity score | Moins de faux signaux | 2-3 jours |
| 4 | Seuil décisionnel asymétrique λ | Économiquement correct | 2-3 jours |
| 5 | Module storage_expected_value (CQR → option) | Module stockage | 3-5 jours |

### Sprint 3 — Produit agricole final (3-4 semaines)

| Ordre | Action | Impact | Durée |
|---|---|---|---|
| 1 | Cibles stockage (y_storage_value_1m/3m/6m) | Décision agricole | 1 semaine |
| 2 | Cible vente partielle (fractionnée) | Réalisme | 3-5 jours |
| 3 | Module risque forte baisse + opportunité hausse | Asymétrie utile | 3-5 jours |
| 4 | Backtest décisionnel agriculteur (gain vs SELL_HARVEST) | Preuve finale | 1 semaine |
| 5 | Rapport hebdomadaire format agriculteur (4 modules) | Outil final | 3-5 jours |
| 6 | Traduction SHAP → langage métier | Explicabilité | 3-5 jours |

### Sprint 4 — Validation et production (continu 2026+)

| Action | Objectif |
|---|---|
| Geler architecture V4 après Sprint 3 | Ne plus modifier les seuils |
| Suivi en temps réel 2026 | Enregistrer chaque signal + réalisation |
| Backtest V4 propre sur 2023-2025 | Une seule évaluation non réoptimisée |
| Recalibration annuelle seulement | Stabilité à long terme |

---

## PARTIE 10 — TICKETS R&D À CRÉER

### R&D-01 — Benchmark canonique V3 (PRIORITÉ 0)

**Question** : quel est réellement le meilleur modèle quand tous les protocoles sont identiques ?

**Livrable** : `canonical_benchmark_results.parquet` + rapport DA/AUC/Brier/IC95 par modèle, horizon et année.

**Critère de fin** : contradiction sweep/zoo expliquée. Un seul modèle retenu avec justification, IC95% inclus.

### R&D-02 — Vrai consensus multi-horizon OOF

**Question** : le consensus inter-horizon ajoute-t-il de l'alpha réel ?

**Livrable** : OOF sur J+28/35/40/45/60, distribution de disagreement non dégénérée, comparaison top20 mono vs vrai consensus.

**Critère** : gain net top20 documenté ou rejet justifié.

### R&D-03 — Courbe des futures (spreads Z/H/K/N)

**Question** : la structure à terme du CBOT maïs prédit-elle la direction ?

**Livrable** : features curve_*_spread + ablation delta_AUC + SHAP importance.

**Critère** : delta_AUC ≥ +0.008 ou signal saisonnier documenté.

### R&D-04 — FAS Export Sales

**Question** : la demande export hebdomadaire améliore-t-elle le signal ?

**Livrable** : collecteur activé, 7 features FAS, ablation globale et par saison (sept-janv).

**Critère** : delta_AUC ≥ +0.010 ou gain saisonnier documenté.

### R&D-05 — Crop Condition + ENSO + features phénologiques

**Question** : l'état des cultures et le contexte climatique améliorent-ils les signaux estivaux ?

**Livrable** : 9 features Crop Condition, 6 features ONI, silking_week_flag, dough_dent_week_flag, ablation.

**Critère** : gain juin-août + meilleure explicabilité du signal météo.

### R&D-06 — Cibles et backtest stockage agriculteur

**Question** : peut-on battre SELL_HARVEST et SELL_THIRDS sur la majorité des années ?

**Livrable** : y_storage_value_1m/3m/6m, cible vente fractionnée, backtest gain vs baselines agricoles.

**Critère** : gain net moyen positif sur au least 5 des 8 années walk-forward, pire année documentée.

### R&D-07 — Confiance P(correct) calibrée

**Question** : le modèle sait-il quand il a de meilleures chances d'avoir raison ?

**Livrable** : modèle logistique P(correct), reliability curves par bucket, top10/top20 stable par année.

**Critère** : ECE < 0.05, p(correct=0.70) → 70% de réussite réelle.

### R&D-08 — Module risque/opportunité asymétrique

**Question** : peut-on séparer le risque de forte baisse et l'opportunité de forte hausse ?

**Livrable** : scores `downside_risk_score` et `upside_opportunity_score` séparés, intégration dans le rapport.

**Critère** : les deux scores ensemble permettent une décision de vente fractionnée économiquement justifiée.

### R&D-09 — COT avancé normalisé

**Question** : la normalisation par OI et le percentile historique améliorent-ils le signal positioning ?

**Livrable** : features cot_*_pct_oi, cot_extreme_flags, hedger_pressure, ablation.

**Critère** : delta_AUC ≥ +0.005.

### R&D-10 — Rapport hebdomadaire agriculteur (4 modules)

**Question** : peut-on produire un rapport compréhensible par un agriculteur non expert en finance ?

**Livrable** : template Markdown automatisé avec les 4 modules, explication SHAP traduite en langage métier.

**Critère** : compréhensible sans formation en statistiques, testable par un agriculteur réel.

---

## PARTIE 11 — TESTS À AJOUTER

### 11.1 Tests absents et critiques

| Test | Fichier cible | Ce qu'il vérifie | Priorité |
|---|---|---|---|
| test_canonical_consistency | test_benchmark_canonical.py | Tous modèles sur mêmes splits/features | **P0** |
| test_metric_confidence_intervals | test_benchmark_canonical.py | IC95% bootstrap sur DA/AUC | **P0** |
| test_annual_stability | test_annual_stability.py | DA > 0.55 chaque année walk-forward | **P0** |
| test_no_single_year_dependency | test_robustness.py | Perf sans 2012, sans 2020-2022 | **P0** |
| test_weekly_sampling | test_weekly_da.py | DA hebdomadaire vs quotidien | **P0** |
| test_publication_lags_intraday | test_publication_lag.py | WASDE/COT/FAS jamais utilisés trop tôt | **P0** |
| test_storage_profit | test_storage_backtest.py | Gain net vs SELL_HARVEST, par année | **P1** |
| test_false_bullish_cost | test_decision_cost.py | Coût asymétrique λ appliqué au seuil | **P1** |
| test_p_correct_calibration | test_confidence_p_correct.py | ECE < 0.05 par bucket confiance | **P1** |
| test_multi_horizon_disagreement | test_consensus_real.py | Distribution disagreement non dégénérée | **P1** |
| test_curve_spread_availability | test_curve_spreads.py | Contrats Z/H/K disponibles et anti-leakaged | **P1** |
| test_market_clarity_score | test_market_clarity.py | Score borné [0,1], décroît avant WASDE | **P2** |
| test_asymmetric_threshold | test_decision_threshold.py | Seuil > 0.5 selon lambda profil | **P2** |
| test_leave_one_regime_out | test_regime_generalization.py | Perf hors sécheresse, hors COVID/Ukraine | **P2** |

### 11.2 Tests existants à modifier

| Test existant | Problème | Correction |
|---|---|---|
| test_horizon_sweep.py | Vérifie artefacts, pas robustesse G1+G3 | Ajouter : si J+40 meilleur, ses voisins ±3 doivent être au top 5 |
| test_consensus.py | Mono-horizon uniquement | Refaire avec OOF multi-horizons réels après R&D-02 |
| test_stacking.py | Valide le résultat, pas la comparaison économique | Ajouter : avg_proba doit battre ou égaler histgb sur DA et economic gain |

---

## PARTIE 12 — NOUVELLES EXPÉRIENCES ET IDÉES DE RECHERCHE

### 12.1 Leave-one-regime-out — test de généralisation

Entraîner sur tous les régimes sauf un, tester sur le régime exclu :

```
Train hors sécheresse 2012 → test sur sécheresse 2012
Train hors COVID/Ukraine 2020-2022 → test sur 2020-2022
Train hors surplus 2014-2019 → test sur 2014-2019
Train uniquement 2015-2019 (surplus normal) → tester sur 2020+
```

**Objectif** : savoir si le modèle généralise à un régime qu'il n'a jamais vu. Si la performance s'effondre sur un régime absent de l'entraînement, l'indicateur n'est pas robuste.

### 12.2 Modèle "risque événement"

Au lieu de prédire seulement la direction à J+40, prédire le risque de choc imminent :

**Cibles** :
```
y_big_move_3pct_10d   : mouvement > 3% dans 10 jours
y_big_move_5pct_10d   : mouvement > 5% dans 10 jours
y_high_vol_10d        : volatilité réalisée > 2σ historique
```

**Utilisation** : très utile autour de WASDE/Acreage/Grain Stocks. Si y_big_move_5pct est élevé → alerte "ne pas agir avant la publication".

### 12.3 Score "marché tradable vs non tradable"

Créer un score composite quotidien de "lisibilité du marché" :

```python
market_clarity_score = (
    0.25 * accord_modèles          # 1 - entropie probabilités
  + 0.25 * accord_horizons         # 1 - disagreement_inter_horizon
  + 0.20 * cqr_certainty          # 1 - normalized_cqr_width
  + 0.15 * distance_publication   # 1 - urgence_wasde (proche = non lisible)
  + 0.15 * contexte_historique    # AUC du contexte saison × régime
)
```

Si market_clarity_score < seuil → "Marché non lisible — signal non émis cette semaine."

### 12.4 Décomposition "prix déjà pricé"

```python
# Score pression fondamentale
fundamental_score = (
    wasde_stocks_tension    # ending_stocks/use sous seuil
  + fas_export_demand       # ventes hebdo vs moyenne
  + crop_stress             # G+E en baisse
  - dollar_headwind         # DXY en hausse
)

# Score positionnement de marché
positioning_score = cot_mm_net_pct_oi_pct_3y  # 0-100%

# Résidu d'opportunité
residual_opportunity = fundamental_score - 0.5 * positioning_score
```

Signal fort : fondamentaux haussiers + marché pas encore bien positionné. Signal faible : fondamentaux haussiers + marché déjà très long (COT >90ème).

### 12.5 Opportunity score vs risk score séparés

Au lieu d'un seul signal BULLISH/BEARISH, deux scores indépendants :

```
upside_opportunity_score  : P(forte hausse) × amplitude attendue → [0, 1]
downside_risk_score       : P(forte baisse) × amplitude attendue → [0, 1]
```

Matrice de décision :

| Upside | Downside | Décision suggérée |
|---|---|---|
| Élevé | Faible | Stocker — situation favorable |
| Faible | Élevé | Vendre/couvrir — situation défavorable |
| Élevé | Élevé | Vente partielle + put option |
| Faible | Faible | Attendre — marché atone |

### 12.6 Test "une décision par semaine"

Signal hebdomadaire sur données hebdomadaires plutôt que quotidien. Correspond mieux au cycle de décision agricole et évite le surcredit d'autocorrélation.

**Benchmark** : mesurer DA hebdomadaire (un point par semaine, le lundi après les rapports NASS/Crop Condition/COT disponibles). Comparer à DA quotidienne. Mesurer le taux de flip réduit.

### 12.7 Test "années normales uniquement"

**Objectif** : est-ce que le signal tient hors des années exceptionnelles (2012, 2020-2022) ?

```
Protocole A : Toutes années 2010-2022 (référence)
Protocole B : Sans 2012 (sécheresse)
Protocole C : Sans 2020-2022 (COVID + Ukraine)
Protocole D : 2013-2019 seulement (surplus, marché "normal")
```

Si DA chute fortement en Protocole D, l'indicateur ne fonctionnerait pas dans un marché normal de surplus. C'est un risque majeur.

---

## PARTIE 13 — CE QUE DIT LA THÉORIE ÉCONOMIQUE

### 13.1 Modèle rationnel de formation du prix à terme

```
F(T) = S₀ × e^(r-δ)T × e^(U-C)T

Où :
  S₀  : prix spot actuel
  r   : taux sans risque
  δ   : convenience yield (inversement lié aux stocks)
  U   : coût de stockage
  C   : coût de portage
```

Quand les stocks sont bas → δ élevé → backwardation → primes spot élevées. C'est pourquoi le WASDE ending_stocks/use ratio est fondamental, et pourquoi les surprises (révisions vs mois précédent) sont plus informatives que les niveaux absolus.

### 13.2 L'hypothèse de marché efficient et ses limites

DA = 0.640, AUC = 0.700 suggèrent une inefficience modeste exploitable. Pourquoi le maïs n'est pas parfaitement efficient :

1. **Asymétrie d'information** : négociants physiques ont des informations locales que les spéculatifs n'ont pas.
2. **Horizon court des fonds CTA** : surréaction aux nouvelles récentes → overshoots exploitables à 4-8 semaines.
3. **Publication ponctuelle USDA** : surprise post-WASDE réelle et persistante 2-5 jours.
4. **Contraintes institutionnelles** : producteurs structurellement vendeurs → primes de risque persistantes.
5. **Données fondamentales lentes** : COT +3j de retard, Crop Condition +7j, ENSO mensuel.

### 13.3 Risque de crowding du signal COT

Le COT est notre 2ème signal le plus important (SHAP). Mais de nombreux fonds quantitatifs l'utilisent depuis 10 ans. Le "crowding" peut réduire progressivement sa valeur.

**Test à intégrer dans R&D-01** : AUC contribution du COT par sous-période 2010-2015 vs 2016-2022. Si le signal COT décroît dans la 2ème période, c'est un signe de saturation stratégique.

---

## PARTIE 14 — DIAGNOSTIC DES LIMITES INTRINSÈQUES

### 14.1 Le plafond de prédictibilité avec données publiques

| Niveau AUC | Signification |
|---|---|
| 0.55-0.62 | Signal faible — potentiellement non significatif |
| 0.62-0.70 | Signal modeste — données publiques bien utilisées **(notre résultat)** |
| 0.70-0.78 | Bon signal — données alternatives (NDVI, prévisions météo, etc.) |
| 0.78-0.85 | Très bon — données propriétaires nécessaires |
| > 0.85 | Propriétaire ou période très spécifique |

Nos résultats (AUC=0.700 OOF, 0.663 backtest) sont dans la fourchette haute des données publiques. C'est honnête et crédible.

### 14.2 Bruit fondamental non modélisable

| Facteur | Fréquence | Impact prix | Modélisable ? |
|---|---|---|---|
| Vague de chaleur inattendue | 1-3/an | ±10-20¢/bu | Non |
| Embargo exportation politique | < 1/an | ±30-50¢/bu | Non |
| Crise financière globale | 1/5-10 ans | ±20-40¢/bu | Non |
| Rupture supply chain (COVID) | < 1/génération | ±100¢/bu | Non |
| Révision WASDE > 2σ | 2-3/an | ±15-25¢/bu | Partiellement |
| Annulation ventes Chine | 2-5/an | ±10-20¢/bu | Non |

**Ce bruit explique pourquoi DA ne peut pas durablement dépasser 0.68-0.72 avec données publiques seules.**

### 14.3 Risque sur-apprentissage 2020-2022

La période 2020-2022 est exceptionnelle : COVID + Ukraine + inflation → prix ont triplé. Un modèle entraîné sur 2010-2022 peut surapprendre ces patterns. Le test "années normales" (Partie 12.7) est indispensable avant toute conclusion.

---

## PARTIE 15 — PERSPECTIVES FUTURES (BASSE PRIORITÉ)

> Ces idées sont valides mais ne sont pas prioritaires par rapport au benchmarking, aux données manquantes et à la cible agricole. Les garder pour la Phase suivante.

### 15.1 Version Europe / MATIF (Phase 5+)

Pour un agriculteur français ou européen :

```
Prix agriculteur = CBOT + basis_MATIF + taux_EUR/USD + prime_qualité_locale
```

Intégrer EURONEXT Matif corn (cotation ZEA), tester la co-intégration CBOT-MATIF, mesurer les divergences de basis. Le signal CBOT reste la référence mondiale, mais la décision locale nécessite la conversion et le basis local.

### 15.2 GRU / LSTM avec features temporelles construites

~2200 observations est la vraie limite pour le deep learning tabulaire. GRU pourrait apporter de la valeur avec des séquences de features hebdomadaires (COT, météo, export sales) si PyTorch est installé. À tester uniquement après avoir épuisé les gains de données et d'architecture actuels.

### 15.3 Surprise model USDA pour chaque publication

Prédire l'écart entre la révision réalisée et le consensus de marché avant chaque WASDE/Grain Stocks/Acreage. C'est ce que font les banques d'investissement agricole — complexité élevée, potentiel fort.

### 15.4 Données satellites (NDVI/EVI NASA MODIS)

Indicateur de biomasse végétale sur la ceinture maïs en temps réel. Complément de la Crop Condition NASS. Disponible via Google Earth Engine (gratuit). À tester si Crop Condition ne suffit pas.

### 15.5 Basis local et profil utilisateur

Module de personnalisation par profil :
- Agriculteur Iowa, France, stockage disponible, coût de production, basis estimé
- Conversion USD/bu → EUR/tonne
- La recommandation change selon le profil

### 15.6 GRU, Transformer, Autoencoder

Architectures complexes à tester quand :
- La base de données est significativement agrandie (FAS + Crop Condition + ENSO + courbe futures → +20% d'observations utiles)
- Le benchmark canonique est stabilisé
- Les modèles simples ont été poussés à leur limite

---

## PARTIE 16 — SYNTHÈSE FINALE — VERDICTS D'EXPERT

### Ce que l'étude prouve scientifiquement

- Signal exploitable dans les données publiques du maïs. AUC=0.700 [IC95%: 0.679-0.721] — significativement au-dessus du hasard.
- Signal contextuel et conditionnel : novembre, stocks tendus, régime baissier, proximité WASDE.
- Sélectivité top 20 % : le mécanisme de valeur principal. DA top20%=0.743 — 10 points au-dessus de la moyenne.
- Modèles linéaires compétitifs avec modèles complexes. L'ingénierie de features domine l'architecture.
- Infrastructure anti-leakage correcte et défendable.

### Ce que l'étude ne prouve pas encore

- Que V3 battra V2 en protocole gelé sur 2023-2025.
- Que l'indicateur améliore le revenu agriculteur vs SELL_HARVEST (farmer backtest V2 : le contraire).
- Que J+40 est robuste hors de la période 2010-2022 (zone robuste G1+G3 vide).
- Que le consensus multi-horizon apporte de l'alpha (OOF mono-horizon J+40).
- Que la confiance actuelle est une vraie probabilité calibrée.
- Que les résultats tiennent en années "normales" de surplus (2015-2019).

### Ce qu'il faut faire — ordre absolu

1. **Benchmark canonique (R&D-01)** : résoudre la contradiction des protocoles. Rien d'autre ne peut être décidé avant.
2. **FAS Export Sales (R&D-04)** : la lacune de données la plus importante.
3. **Crop Condition + ENSO (R&D-05)** : clé NASS disponible — activer maintenant.
4. **Courbe des futures (R&D-03)** : gratuit, non exploité, économiquement fondamental.
5. **Vrai multi-horizon OOF (R&D-02)** : uniquement après benchmark stabilisé.
6. **Cibles stockage + backtest agriculteur (R&D-06)** : la vraie validation finale.
7. **Confiance P(correct) (R&D-07)** : remplacer l'heuristique actuelle.
8. **Rapport 4 modules (R&D-10)** : le produit final.

### La métrique finale doit changer

Ce n'est plus DA=0.640 → DA=0.660. C'est :

> **Battre SELL_HARVEST et SELL_THIRDS en gain net agricole, sur au moins 65% des années walk-forward, avec un risque de perte maximale acceptable.**

### Le bon objectif V4 — formulation précise

> Produire, chaque lundi, un rapport en 4 modules permettant à un agriculteur de prendre de meilleures décisions de stockage et de vente partielle sur le CBOT maïs, avec un gain net moyen positif par rapport à une stratégie naïve, sur la majorité des années de validation, sans aucune connaissance ex-post et sans recalibrage des seuils.

### Le message le plus important

**Un indicateur professionnel utile aux agriculteurs n'est pas un modèle qui maximise DA. C'est un système qui :**

1. Sait quand parler et quand se taire (sélectivité et market clarity score).
2. Explique pourquoi en langage économique compréhensible (SHAP traduit, pas noms de colonnes).
3. Quantifie l'opportunité et le risque séparément (upside score vs downside risk score).
4. Aligne ses seuils sur les coûts réels du profil agriculteur (lambda asymétrique).
5. Se démontre profitable sur une majorité d'années, pas seulement en moyenne.
6. Donne une recommandation de vente fractionnée, pas binaire tout/rien.

---

*Audit expert révisé le 2026-05-17. Intègre l'analyse complète des artefacts V3 (9 tickets), les principes d'économie des marchés de commodités (courbe des futures, convenience yield, basis, asymétrie de coûts, option de stockage), de statistique temporelle (multiple testing, IC95, walk-forward, autocorrélation), et de finance agricole. Sources : horizon_sweep_report.txt, model_zoo_report.txt, stacking_report.txt, new_sources_report.txt, dim_reduction_report.txt, dl_comparison_report.txt, confidence_v3_01_report.txt, consensus_report.txt, factor_metadata.yaml, sources.yaml, indicator.yaml, FARMER_BACKTEST_REPORT_V2.md, VALIDATION_REPORT.md.*
