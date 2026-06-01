# Document d'amélioration complet — Étude maïs et indicateur professionnel

> **Version 2.0 — 2026-05-15**
> Document de référence unique pour toutes les pistes d'amélioration de l'étude et de l'indicateur.
> Objectif : construire un indicateur directionnel professionnel du marché du maïs, capable de fournir un signal de marché fiable pour raisonner les périodes favorables, défavorables ou incertaines.

> **Légende des statuts :** ✅ exécuté, artefact présent, résultat interprété — 🟡 codé ou généré, validation scientifique incomplète — 🟠 partiel / fragile — ❌ non fait

---

## 1. Executive summary

L'étude actuelle du marché du maïs est déjà avancée : le pipeline fonctionne, les données principales sont intégrées, les modèles sont testés en walk-forward, les baselines sont présentes, les intervalles CQR existent, les facteurs économiques sont structurés, et un premier indicateur directionnel a été construit.

Cependant, le projet n'est pas encore terminé. Les résultats actuels montrent un signal directionnel partiel, surtout à horizon J+20/J+30, mais ils ne prouvent pas encore que l'indicateur est assez robuste pour devenir un vrai outil de décision fiable.

**Point central :**

Il ne faut pas chercher à prédire tous les jours si le maïs va monter ou baisser. Il faut identifier les contextes où le marché donne un signal exploitable.

**Objectif final :**

Construire un indicateur BULLISH / BEARISH / NEUTRAL / UNCERTAIN, avec une probabilité, un score de confiance, une explication économique, et une validation historique montrant dans quels contextes il est fiable.

Le projet doit maintenant passer d'une étude technique à une vraie étude de recherche appliquée. On doit tester toutes les hypothèses possibles : horizons, cibles, familles de données, régimes, saisons, périodes WASDE, météo, tendances, volatilité, signaux forts, signaux faibles, modèles spécialisés, calibration, robustesse par année, et performance selon le niveau de confiance.

---

## 2. Changement de philosophie

### Mauvais objectif

L'ancien raisonnement implicite était parfois :

> On veut prédire le prix du maïs avec la meilleure DA possible.

Ce n'est pas suffisant, parce que :
- le marché du maïs est très bruité ;
- beaucoup d'informations sont déjà intégrées dans les prix ;
- une DA globale de 60 % peut cacher des signaux forts très utiles ;
- un modèle peut être faible tous les jours mais très bon dans certains contextes.

### Bon objectif

Le bon objectif est :

> Trouver les situations où l'indicateur a réellement un avantage.

On doit donc chercher :
- à quels horizons le maïs est le plus prévisible ;
- dans quelles saisons le signal est le plus fort ;
- dans quels régimes le modèle fonctionne ;
- quelles familles de données apportent vraiment du signal ;
- si la direction est plus prédictible que l'amplitude ;
- si les fortes hausses / fortes baisses sont plus prévisibles que les petits mouvements ;
- si l'indicateur devient vraiment bon lorsqu'il est confiant ;
- si l'indicateur sait reconnaître les périodes où il ne sait pas.

---

## 3. État actuel de l'étude

### Ce qui est déjà solide

| Composante | État | Note |
|---|---|---|
| Pipeline de données | ✅ | opérationnel, cron 07:15 |
| Génération de features | ✅ | 306 cols, 6192 lignes |
| Génération de targets | ✅ | 96 colonnes, niveaux 1-7 |
| Facteurs économiques | ✅ | 13 familles documentées dans factor_metadata.yaml |
| Validation walk-forward + embargo temporel | ✅ | protocole solide, anti-leakage PASS |
| Audit anti-leakage | ✅ | 5 checks PASS, calendrier exempté |
| Baselines sérieuses | ✅ | saisonnière, momentum, zero, historical_mean |
| Modèles ML (Ridge, RF, HGB, XGB, LGB) | ✅ | walk-forward complet, artefacts présents |
| CQR calibré | ✅ | 91.7% coverage (objectif ≥88%) |
| SHAP via TreeExplainer | ✅ | importance mesurée par famille |
| Backtests agriculteur V2 | ✅ | 8 stratégies, SELL_HARVEST 82.8% |
| Journal d'expériences | ✅ | EXPERIMENT_INDEX.md à jour |
| Pipeline quotidien avec cron | ✅ | clés API actives, collecte incrémentale |
| 12 notebooks exécutés + HTML | ✅ | tous exportés dans exports/ |
| Modèles TS (ARIMA, SARIMAX, GARCH) | 🟡 | codés dans _model_specs(), smoke test OK, pas encore analysés dans les notebooks avec conclusions |
| Indicateur directionnel V1 | 🟡 | règles codées dans direction.py, pas encore backtesté par tranche de confiance |
| Calibration probabiliste | 🟠 | CQR calibré, mais reliability curves pas encore produites |
| Futures curve | ❌ | factor_curve_structure absent — données non collectées |
| FAS Export Sales | ❌ | FAS_API_KEY manquante — factor_export_demand_surprise = 100% NaN |

### Résultats actuels importants

- Le signal court terme J+5/J+10 est faible
- Le signal J+20/J+30 est meilleur
- La baseline saisonnière reste très compétitive
- LightGBM / RF / Ridge captent parfois un signal directionnel
- Certains signaux confiants montent beaucoup plus haut que la DA globale
- CQR est calibré mais doit encore être analysé en largeur/exploitabilité
- Les régimes et saisons semblent importants
- L'indicateur ne doit pas être utilisé tous les jours de la même manière

**Conclusion actuelle :**

> Le marché du maïs n'est pas fortement prédictible en continu, mais il existe probablement des fenêtres, contextes et régimes où le signal devient exploitable.

---

## 4. Problèmes actuels à corriger

### 4.1 Trop de jugement sur la DA globale

Une DA globale de 58–62 % peut sembler faible, mais elle est normale sur un marché financier. Elle ne dit pas si le modèle est bon **quand il est confiant**.

**À corriger :**
- Ajouter DA par niveau de confiance
- Ajouter DA sur top 10 %, 20 %, 30 % des signaux les plus forts
- Ajouter DA quand le modèle dit UNCERTAIN
- Vérifier que UNCERTAIN ≈ hasard
- Vérifier que HIGH CONFIDENCE > DA globale

**L'indicateur est bon si :**

| Contexte | DA attendue |
|---|---|
| Tous les jours | DA modérée (~58-62%) |
| Jours confiants | DA nettement meilleure (>67%) |
| Jours incertains | DA proche de 50% |

### 4.2 Cibles encore trop simples

Prédire seulement `y_logret_h20` ou `y_up_h20` est trop limité. Il faut tester plusieurs familles de cibles (voir section 6.B).

### 4.3 Modèles trop globaux

Un modèle unique sur toute l'année est probablement trop faible. Il faut tester des modèles spécialisés par saison, régime, volatilité, période WASDE.

### 4.4 Indicateur encore trop simple

L'indicateur ne doit pas seulement faire :
```
P(up) > 0.60 → BULLISH
```

Il doit intégrer : probabilité, confiance, accord entre modèles, stabilité du signal, largeur CQR, saison, régime, force du mouvement attendu, cohérence économique, historique de performance du même contexte.

---

## 5. Objectif final de l'indicateur

L'indicateur final doit produire une sortie comme :

```
Horizon J+20 : BULLISH
Probabilité de hausse      : 64 %
Probabilité de forte hausse: 22 %
Probabilité de forte baisse:  9 %
Confiance                  : 71 %
Contexte                   : été / stress météo / stocks tendus
Signal historique comparable: DA 69 % sur les cas similaires
Facteurs haussiers         : météo, stocks/use, momentum
Facteurs baissiers         : dollar, exports faibles
Décision modèle            : signal exploitable mais à surveiller
```

Il ne doit pas promettre que le prix va monter. Il doit dire :

> Historiquement, dans ce type de situation, le signal a été favorable avec tel niveau de fiabilité.

C'est ça qui rend l'indicateur professionnel.

---

## 6. Liste complète des tests à ajouter

### Ordre strict d'exécution — 5 blocs séquentiels

**L'ordre est critique.** Ajouter des modèles ou des données sans savoir d'abord quelle cible est prédictible et dans quel contexte est une perte de temps.

```
BLOC 1 — Valider les résultats actuels
    Avant toute amélioration : vérifier artefacts, métriques, DA par horizon,
    CQR, indicateur V1. C'est le socle. Sans lui, on ne sait pas d'où on part.

BLOC 2 — Trouver la meilleure cible
    Comparer toutes les cibles (y_up, y_up_strong, regret, vol, skew, oracle).
    Tant que la cible optimale n'est pas identifiée, tester des modèles est prématuré.

BLOC 3 — Trouver les meilleurs contextes
    Sur la cible retenue : saison, mois, WASDE, volatilité, régime, météo, stocks.
    C'est là que se trouvent les "poches de signal".

BLOC 4 — Améliorer les facteurs
    Futures curve, COT corrigé, FAS exports, WASDE surprises, météo avancée.
    Seulement après avoir compris quel contexte importe.

BLOC 5 — Construire l'indicateur final
    Confidence V2/V3, calibration, score cohérence économique,
    consensus multi-horizon, backtest complet.
```

---

### A. Tests sur les horizons

Tester tous les horizons : J+1, J+3, J+5, J+10, J+15, J+20, J+30, J+45, J+60, J+90

**Questions à répondre :**
- Le maïs est-il plus prévisible à court, moyen ou long terme ?
- J+20 est-il vraiment meilleur que J+10 ?
- J+30 est-il plus stable que J+20 ?
- J+60 est-il trop loin ou plus agricole ?
- Le signal change-t-il selon la saison ?

**Sortie attendue :**

| Horizon | DA | AUC | Brier | RMSE | % signaux confiants | DA signaux confiants |
|---|---|---|---|---|---|---|

---

### B. Tests sur les cibles

#### B1. Retour continu
`y_logret_h5/h10/h20/h30/h60` — prédire l'amplitude (très difficile, bruité)

#### B2. Direction simple
`y_up_h5/h10/h20/h30/h60` — prédire hausse / baisse (cible principale)

#### B3. Fortes hausses
`y_up_strong_1/2/3/5pct_h20` — Les grosses hausses sont-elles plus détectables que les petites variations ?

#### B4. Fortes baisses
`y_down_strong_1/2/3/5pct_h20` — Le modèle détecte-t-il mieux les risques de baisse ?
> Un indicateur peut être utile s'il prévient surtout les risques.

#### B5. Potentiel futur
`future_max_return_h30/h60/h90` — Existe-t-il une probabilité qu'une meilleure fenêtre de prix apparaisse bientôt ?

#### B6. Risque futur
`future_min_return_h30/h60`, `downside_risk_h30/h60` — Le marché présente-t-il un risque élevé de baisse ?

#### B7. Regret
`sell_today_regret_h30/h60` — Si on vend maintenant, risque-t-on de regretter fortement dans 30 ou 60 jours ?

#### B8. Volatilité future
`realized_vol_h10/h20/h30` — Peut-on prédire les périodes où le marché va devenir plus instable ?

#### B9. Asymétrie de risque (déjà dans `targets.parquet`)
`y_skew_h5/h10/h20/h30` = upside potential / downside potential

---

### C. Tests par saison agricole

| Saison | Mois |
|---|---|
| Pré-semis | février–mars |
| Semis | avril–mai |
| Croissance | juin |
| Pollinisation | juillet–août |
| Récolte | septembre–octobre |
| Post-récolte | novembre–janvier |

**Pour chaque saison :** DA globale, DA signaux confiants, AUC, Brier, importance SHAP, meilleure cible, meilleur modèle, meilleure famille de données.

**Questions :**
- La météo est-elle surtout utile en été ?
- Les stocks sont-ils plus utiles en hiver ?
- La saisonnalité est-elle plus forte en post-récolte ?
- Les signaux baissiers sont-ils plus fiables à la récolte ?
- Les signaux haussiers sont-ils plus fiables pendant les stress météo ?

---

### D. Tests par mois

Analyser mois par mois (janvier → décembre) :
- Probabilité historique de hausse
- Retour moyen et volatilité
- DA du modèle vs DA baseline saisonnière
- DA des signaux confiants
- Fréquence BULLISH / BEARISH / UNCERTAIN

Objectif : savoir si certains mois sont prévisibles et d'autres impossibles.

---

### E. Tests autour des rapports USDA / WASDE

| Fenêtre | Description |
|---|---|
| WASDE −5 à −1 j | Avant publication |
| Jour WASDE | Jour J |
| WASDE +1 à +5 j | Après publication |
| Hors WASDE | Période neutre |

**Questions :**
- Le modèle doit-il éviter de prédire juste avant WASDE ?
- Le marché devient-il plus prévisible après publication ?
- Les surprises WASDE changent-elles la direction ?
- Faut-il un modèle spécial WASDE ?

---

### F. Tests sur les surprises WASDE

Variables à créer :
```
wasde_yield_surprise
wasde_production_surprise
wasde_ending_stocks_surprise
wasde_exports_surprise
wasde_stocks_use_surprise
```
Calculées comme : `valeur - moyenne_3m_trend`, `valeur - estimation_precedente`, `valeur - moyenne_5y`

**Questions :**
- Les surprises expliquent-elles mieux que les valeurs brutes ?
- Le marché réagit-il plus à ending stocks qu'à yield ?
- Le signal WASDE est-il plus fort à J+5 ou J+20 ?

---

### G. Tests météo avancés

**Variables à ajouter :**
```
heat_days_30c / 35c / 38c
rain_deficit_7d / 14d / 30d
excess_rain_7d / 14d
gdd_accumulated / gdd_anomaly
dry_spell_days / wet_spell_days
weather_stress_index
pollination_heat_stress
```

**Tests à faire :**
- Météo uniquement en juin–août
- Météo par État (pondérée par production)
- Stress chaleur >35°C vs température moyenne
- Stress sécheresse vs précipitations excessives par période

**Questions :**
- Le modèle météo est-il inutile hors été ?
- Les stress extrêmes sont-ils plus prédictifs que les moyennes ?
- La chaleur >35°C est-elle plus importante que la température moyenne ?

---

### H. Tests Crop Progress / condition

**Variables à tester :**
```
corn_planted_pct / emerged_pct / silking_pct / dough_pct
corn_dented_pct / mature_pct / harvested_pct
condition_good_excellent / condition_poor_very_poor
condition_change_1w / condition_change_4w
condition_vs_5y_avg
```

**Questions :**
- Une dégradation brutale de la condition provoque-t-elle un signal haussier ?
- Le niveau absolu est-il moins utile que la variation ?
- Les conditions sont-elles déjà pricées avant publication ?

---

### I. Tests COT / positionnement

**Variables à ajouter ou corriger :**
```
cot_mm_net / cot_mm_long / cot_mm_short
cot_commercial_net / cot_open_interest
cot_mm_net_zscore
cot_mm_net_change_1w / change_4w
cot_extreme_long_flag / cot_extreme_short_flag
cot_crowding_score
```

**Tests importants :** COT brut vs COT variation, COT extrême uniquement, COT + momentum, COT en régime haussier/baissier, COT comme indicateur contrarian.

**Questions :**
- Quand les fonds sont très longs, le marché continue-t-il ou risque-t-il de corriger ?
- Les variations COT sont-elles plus utiles que les niveaux ?
- Les positions commerciales ont-elles plus de signal que les managed money ?

---

### J. Tests futures curve

**Très important à ajouter. Vient directement du marché.**

**Variables à créer :**
```
spread_front_second / spread_front_third / spread_second_third
contango_flag / backwardation_flag
curve_slope / curve_inversion_strength
roll_yield_proxy / carry_pressure
```

**Questions :**
- Le contango annonce-t-il un marché faible ?
- La backwardation annonce-t-elle une tension haussière ?
- La pente de courbe améliore-t-elle le signal J+20/J+30 ?
- Le marché est-il plus prédictible quand la courbe est inversée ?

---

### K. Tests cross-commodities

**Variables dérivées :**
```
corn_wheat_spread / corn_soy_spread / soy_corn_ratio
wheat_corn_ratio / oil_corn_ratio
cross_commodity_momentum
```

**Questions :**
- Le blé entraîne-t-il parfois le maïs ?
- Le soja explique-t-il mieux certaines périodes ?
- Les spreads sont-ils plus utiles que les prix bruts ?

---

### L. Tests macro

**Variables :** `dollar_index`, `real_rate_10y`, `fed_funds`, `inflation`, `vix`, `sp500`, `usd_brl`, `usd_ars`

**Questions :**
- Le dollar fort pèse-t-il sur le maïs ?
- Les taux réels influencent-ils les commodités ?
- Le VIX aide-t-il à détecter les phases de stress ?
- Les devises Brésil / Argentine améliorent-elles le signal ?

---

### M. Tests par régime

**Régimes à tester :**

| Régime | Méthode de détection |
|---|---|
| Bull / Bear | Markov 2 états |
| High / Low volatility | Quantiles de vol réalisée |
| Trend up / down | SMA 60j |
| Mean reversion | Bandes de Bollinger |
| Stocks tight / abundant | Quantiles stocks/use USDA |
| Weather stress / normal | Index stress composite |

**Questions :**
- Le modèle fonctionne-t-il surtout en tendance ?
- Est-il meilleur en bear market ?
- Faut-il désactiver l'indicateur en range ?
- Faut-il un modèle spécifique par régime ?

---

### N. Tests par volatilité

| Tranche | Définition |
|---|---|
| Volatilité basse | < percentile 25 |
| Normale | 25–75 |
| Élevée | > percentile 75 |
| Extrême | > percentile 90 |

**Questions :**
- Le modèle est-il meilleur quand la volatilité est élevée ?
- Faut-il mettre UNCERTAIN automatiquement en volatilité extrême ?
- Les fortes baisses sont-elles plus prévisibles en forte volatilité ?

---

### O. Tests de confiance et fréquence des signaux

**Tranches à analyser :**
- confidence < 0.45
- 0.45–0.55
- 0.55–0.65
- 0.65–0.75
- > 0.75
- top 30 % / top 20 % / top 10 %

**Métriques par tranche :**

| Tranche | DA | % jours couverts | Signaux/an | Retour moyen |
|---|---|---|---|---|
| Top 10 % | ? | ~25 j/an | ~25 | ? |
| Top 20 % | ? | ~50 j/an | ~50 | ? |
| Top 30 % | ? | ~75 j/an | ~75 | ? |
| Tous | DA globale | 100 % | ~252 | neutre |

**Fréquence utile des signaux — métrique indispensable :**

Un indicateur qui fait 75 % de DA mais seulement 3 jours par an n'est pas forcément utile. La fréquence est aussi importante que la qualité.

```
signals_per_year_strong    = nombre de signaux confidence > 0.70
signals_per_year_moderate  = nombre de signaux confidence 0.55–0.70
signals_per_year_uncertain = nombre de jours UNCERTAIN
avg_signal_duration        = durée moyenne d'un signal avant retournement
```

**Questions :**
- La DA augmente-t-elle avec la confiance ? (si non, le score de confiance est mauvais)
- Quel est le compromis optimal entre fréquence et qualité ?
- Combien de jours exploitables par an l'indicateur produit-il ?
- La fréquence est-elle suffisante pour être utile en pratique ?

> C'est probablement le test le plus important pour juger l'indicateur.

---

### P. Tests de calibration probabiliste

**Métriques :** Brier score, AUC, reliability curve, calibration slope/intercept, ECE

**Méthodes :** Platt scaling, Isotonic regression, Beta calibration, Temperature scaling

**Questions :**
- Quand le modèle dit 65 %, est-ce réellement 65 % ?
- Les probabilités sont-elles trop optimistes ?
- Faut-il recalibrer par horizon ? Par saison ?

---

### Q. Tests CQR avancés

- Coverage par horizon / saison / régime
- Width moyenne par horizon et par niveau de volatilité
- DA par décile de width
- Erreur absolue vs width
- Signal fort quand intervalle étroit → UNCERTAIN quand intervalle large

**Questions :**
- Les intervalles larges correspondent-ils vraiment à plus d'erreur ?
- La largeur CQR améliore-t-elle le score de confiance ?
- Faut-il créer un label UNCERTAIN uniquement basé sur CQR ?

---

### R. Tests de robustesse temporelle

- Performance par année et par décennie
- Performance avant/après 2020
- Performance hors années exceptionnelles (sans 2012, sans 2022)
- Train 2010–2018 → test 2019–2025
- Train 2010–2020 → test 2021–2025

**Questions :**
- Le modèle dépend-il d'une seule crise ?
- Les résultats viennent-ils uniquement de 2012 / 2022 ?
- Est-ce que le signal existe vraiment sur plusieurs périodes ?

---

### S. Tests d'ablation

```
market only          | weather only        | WASDE only
COT only             | seasonality only    | macro only
cross-commodity only | curve only          | exports only
ethanol only         | all minus market    | all minus weather
all minus WASDE      | all minus COT       | all minus seasonality
```

**Questions :**
- Quelle famille apporte réellement du signal ?
- Certaines familles dégradent-elles les résultats ?
- Peut-on simplifier le modèle sans perdre de performance ?

---

### T. Tests de sélection de variables

- Ridge coefficients / Lasso selection
- Permutation importance / SHAP importance
- Mutual information / Boruta / RFE
- PCA / ACP / Clustering de variables corrélées

Objectif : réduire le bruit, garder les signaux stables, améliorer la généralisation.

---

### U. Tests sur les modèles

**Modèles statistiques :** AR, ARMA, ARIMA, SARIMA, SARIMAX, VAR, GARCH, EGARCH, Markov-switching, Kalman filter

**Modèles ML :** Ridge, Lasso, ElasticNet, RF, ExtraTrees, HGB, LGB, XGB, CatBoost, SVM, MLP

**Modèles spécialisés :**
- Modèle par saison (été, hiver, récolte)
- Modèle par régime (bull, bear, high-vol)
- Modèle par horizon
- Modèle météo été uniquement
- Modèle WASDE

**Ensembles :** stacking, blending, weighted average, model voting, mixture of experts

---

### V. Tests Optuna

Optuna ne doit pas être lancé trop tôt. À faire **seulement après** avoir identifié : meilleure cible, meilleur horizon, meilleur featureset, meilleur contexte.

**Tests prioritaires :**
- Optuna LightGBM h20 sur `y_up_h20`
- Optuna LightGBM h30 sur `y_up_h30`
- Optuna XGBoost h20 sur `y_up_strong_h20`
- Optuna CatBoost sur `future_max_return_h60`

**Comparer :** modèle défaut vs optimisé → DA globale, AUC, Brier, DA signaux confiants, stabilité annuelle.

---

### W. Tests d'oracle analysis

**Variables oracle à tester :**
```
oracle_future_weather_stress_h20
oracle_future_crop_condition_change
oracle_future_wasde_surprise
oracle_future_export_change
oracle_future_cot_change
oracle_future_drought_change
oracle_future_volatility
oracle_future_max_return
```

**Questions :**
- Si on connaissait la météo future, le maïs serait-il beaucoup plus prévisible ?
- Si on connaissait la prochaine surprise WASDE, le signal s'améliore-t-il ?
- Quels drivers futurs valent vraiment la peine d'être prédits ?

**Décision :** Si une variable oracle améliore fortement la DA → créer un sous-modèle pour prédire cette variable intermédiaire.

Exemple :
```
X_t → prédire météo future → prédire direction maïs
```

---

### X. Tests de stratégie d'indicateur

**Signaux :** BULLISH / BEARISH / NEUTRAL / UNCERTAIN

**Tests :**
- DA quand BULLISH / DA quand BEARISH
- Fréquence de chaque signal
- Retour moyen après BULLISH / BEARISH
- Volatilité après UNCERTAIN
- Performance par horizon / saison / régime
- Matrice de confusion

**Objectif — valider que :**

| Signal | Comportement attendu |
|---|---|
| BULLISH | Hausse plus fréquente que la moyenne |
| BEARISH | Baisse plus fréquente que la moyenne |
| NEUTRAL | Faible mouvement |
| UNCERTAIN | Résultats proches du hasard ou forte volatilité |

---

### Y. Tests de persistance du signal

Un signal d'un seul jour est fragile. Un signal stable 3 à 5 jours consécutifs est beaucoup plus crédible.

**Variables à calculer :**
```
signal_persistence_1d  = signal identique j-1 → j
signal_persistence_3d  = signal identique sur 3 jours consécutifs
signal_persistence_5d  = signal identique sur 5 jours consécutifs
signal_flip_rate       = fréquence des BULLISH→BEARISH ou BEARISH→BULLISH le lendemain
signal_streak_avg      = durée moyenne d'un signal avant inversion
confirmation_lag       = faut-il 2 ou 3 jours de confirmation avant d'agir ?
```

**Tests à faire :**
- DA globale vs DA signaux persistants 3j / 5j
- Taux de flip (changement de signe en 24h)
- Retour moyen selon durée du signal
- Comparaison : signal unique vs signal confirmé 3j

**Questions :**
- Le signal change-t-il trop souvent (flip rate élevé = signal instable) ?
- BULLISH qui dure 5 jours est-il plus fiable que BULLISH isolé ?
- Faut-il attendre une confirmation de 2–3 jours avant d'émettre un signal ?
- Les signaux stables ont-ils un meilleur retour moyen ?

**Règle à tester :**
```
if signal_persistence_3d and confidence > 0.65:
    → signal émis (plus crédible)
else:
    → signal en attente de confirmation
```

> Un bon indicateur professionnel ne change pas d'avis tous les jours.

---

### Z. Analyse des erreurs

Indispensable pour améliorer l'indicateur de façon ciblée plutôt qu'aléatoire.

**À analyser :**
- Les 20 pires erreurs (prédit BULLISH, résultat très baissier)
- Erreurs par année — concentrées sur 2012 / 2022 / autres ?
- Erreurs par saison — l'été est-il la période la plus difficile ?
- Erreurs autour WASDE — le modèle anticipe-t-il mal les publications ?
- Erreurs en volatilité extrême — le modèle est-il battu par les chocs ?
- Erreurs quand les modèles sont en désaccord (model_agreement faible)
- Erreurs quand CQR était paradoxalement étroit (fausse confiance)
- Erreurs quand SHAP est incohérent économiquement (facteurs contradictoires)

**Métriques d'erreur :**
```
worst_20_errors         = cas où |y_true - y_pred| est maximal
false_bullish_rate      = prédit BULLISH, résultat négatif
false_bearish_rate      = prédit BEARISH, résultat positif
missed_strong_up_rate   = forte hausse non détectée
missed_strong_down_rate = forte baisse non détectée
error_concentration     = % des erreurs totales concentrées sur top 10 % jours
```

**Questions diagnostiques :**
- Le modèle rate-t-il surtout les retournements de tendance ?
- Suit-il trop le momentum (prédit la hausse d'hier pour demain) ?
- Sous-estime-t-il les chocs exogènes (WASDE surprise, météo extrême) ?
- Est-il trop optimiste en été (biais haussier pendant la pollinisation) ?
- Quand le modèle se trompe avec confiance, pourquoi ?

**Action :** Chaque catégorie d'erreur identifiée doit déclencher une amélioration concrète (nouvelle feature, seuil UNCERTAIN, modèle spécialisé, ou exclusion du signal).

---

## 7. Nouveau score de confiance à tester

### Confidence V1 (actuelle)
```
0.30 × distance probabilité à 0.5
0.25 × accord entre modèles
0.25 × largeur CQR inversée
0.20 × stabilité du signal
```

### Confidence V2 — contexte historique
```
0.25 × distance probabilité à 0.5
0.20 × accord entre modèles
0.20 × largeur CQR inversée
0.15 × stabilité du signal
0.20 × fiabilité historique du contexte
```

Exemple : si on est en été, en régime bear, avec météo stressée, et que ce contexte a historiquement une DA de 68 %, alors la confiance augmente.

### Confidence V3 — score prudent (minimum)
```python
confidence = min(
    probability_confidence,
    model_agreement,
    cqr_confidence,
    historical_context_confidence
)
```

Cette version évite qu'un seul composant fort compense une grosse incertitude.

---

## 8. Améliorations concrètes de l'indicateur

### 8.1 Ne pas prédire tous les jours

Créer trois modes :

| Mode | Condition | Priorité |
|---|---|---|
| Signal fort | confidence > 0.70 | Agir |
| Signal faible | 0.50 < confidence ≤ 0.70 | Surveiller |
| Pas de signal | confidence ≤ 0.50 | Attendre |

> Mieux vaut 70 % de DA sur 20 % des jours que 58 % sur 100 % des jours.

### 8.2 Seuil "no signal"

```
if confidence < seuil → UNCERTAIN
if |P(up) - 0.5| < 0.05 → NEUTRAL
if CQR_width > percentile_90 → UNCERTAIN
if model_agreement < 0.55 → UNCERTAIN
```

### 8.3 Modèle par contexte

```
Détecter contexte actuel
    └── Choisir modèle adapté
        └── Produire signal
            └── Calibrer avec historique du contexte
```

Exemples :
- Été + stress météo → modèle météo
- Hiver + stocks tendus → modèle WASDE/export
- Forte volatilité → modèle risque
- Range market → neutralisation

### 8.4 Score de cohérence économique

L'indicateur doit aussi dire si le signal est économiquement cohérent.

```
Signal BULLISH mais :
  - stocks confortables
  - météo normale
  - dollar fort
  - COT très long
  → signal fragile
```

Créer : `economic_consistency_score` — mesure si les facteurs principaux vont dans le même sens que le label.

### 8.5 Consensus multi-horizon

```
J+5  bullish
J+10 bullish
J+20 bullish  →  horizon_agreement_score = 1.0
J+30 bullish
```

Si J+5 bearish mais J+30 bullish → signal plus prudent, confiance réduite.

---

## 9. Notebooks à produire ou améliorer

### Notebook 01 — Données et qualité
- Tableau de couverture par source (jours disponibles / total)
- NaN par période et par famille
- Test anti-leakage par famille
- Sources absentes / inutilisables
- Périodes à exclure

### Notebook 02 — Saisonnalité
- DA de baseline saisonnière par mois
- Retour moyen + volatilité par mois
- Probabilité de forte hausse / baisse par mois
- Saisonnalité par horizon

### Notebook 03 — Facteurs
- Corrélation entre facteurs + VIF
- SHAP par horizon / saison / régime
- Stabilité des facteurs dans le temps
- Top facteurs haussiers / baissiers

### Notebook 04 — Cibles et oracle
- Toutes les cibles niveaux 1–7
- Comparaison prédictibilité par cible
- Oracle analysis complète
- Décision : quelles cibles garder

### Notebook 05 — Baselines et modèles statistiques
- ARIMA / SARIMAX / GARCH / VAR / Markov 2 états
- Comparaison baselines sérieuses

### Notebook 06 — AutoML / ML
- Features brutes vs facteurs
- Optuna après sélection
- Stacking
- Performances par année et par confiance
- Modèles rejetés avec raison

### Notebook 07 — Ablation (indispensable)
- Importance marginale de chaque famille
- Familles inutiles / redondantes / prioritaires

### Notebook 08 — Régimes et saisons
- Modèle par saison
- Modèle par régime
- Modèle par volatilité
- Modèle par stocks
- Modèle par période WASDE

### Notebook 09 — Incertitude
- Calibration + reliability curves
- Largeur CQR par contexte
- Score de confiance V1 / V2 / V3

### Notebook 10 — Construction indicateur
- Règles finales
- Score de confiance + score cohérence économique
- Consensus horizon
- Exemples de signaux historiques

### Notebook 11 — Backtest indicateur
- DA par signal / confiance / saison / régime
- AUC, Brier, matrice de confusion
- Erreurs majeures

### Notebook 12 — Synthèse finale
- Ce qui marche / ce qui ne marche pas
- Meilleures cibles / horizons / contextes / familles utiles
- Limites connues
- Version finale de l'indicateur
- Prochaines pistes

---

## 10. Liste priorisée des tickets à créer

### Priorité 0 — Stabiliser la base

| Ticket | Objectif | Sortie |
|---|---|---|
| ETUDE-A01 | Validation baseline complète de tous les résultats actuels | `docs/VALIDATION_BASELINE_V2.md` |
| ETUDE-A02 | Corriger COT post-2021 (gap structurel) | `factor_positioning` fiable |
| ETUDE-A03 | Activer FAS Export Sales (nécessite FAS_API_KEY) | `factor_export_demand_surprise` |
| ETUDE-A04 | Ajouter futures curve (spread front/second, contango, backwardation) | `factor_curve_structure` |

### Priorité 1 — Cibles et analyse

| Ticket | Objectif |
|---|---|
| ETUDE-B01 | Ajouter toutes les cibles niveau 1–7 (strong moves, max/min, regret, vol) |
| ETUDE-B02 | Lancer target comparison — DA/AUC/Brier par cible |
| ETUDE-B03 | Lancer oracle analysis complète — identifier les drivers futurs clés |

### Priorité 2 — Contextes

| Ticket | Objectif |
|---|---|
| ETUDE-C01 | Performance par saison agricole |
| ETUDE-C02 | Performance par mois (calendrier) |
| ETUDE-C03 | Performance autour des publications WASDE |
| ETUDE-C04 | Performance par régime (Markov) |
| ETUDE-C05 | Performance par volatilité (quantiles) |

### Priorité 3 — Facteurs

| Ticket | Objectif |
|---|---|
| ETUDE-D01 | Ablation complète des 13 familles |
| ETUDE-D02 | VIF et corrélation inter-facteurs |
| ETUDE-D03 | SHAP par horizon / saison / régime |
| ETUDE-D04 | Sélection de variables stable dans le temps |

### Priorité 4 — Modèles

| Ticket | Objectif |
|---|---|
| ETUDE-E01 | Ajouter modèles spécialisés par contexte (saison, régime) |
| ETUDE-E02 | Tester stacking / blending / mixture of experts |
| ETUDE-E03 | Optuna sur meilleurs couples cible × horizon après sélection |

### Priorité 5 — Indicateur

| Ticket | Objectif |
|---|---|
| ETUDE-F01 | Confidence score V2 (contexte historique) + V3 (min) |
| ETUDE-F02 | Calibration probabiliste (Platt, Isotonic) par horizon/saison |
| ETUDE-F03 | Score de cohérence économique |
| ETUDE-F04 | Consensus multi-horizon |
| ETUDE-F05 | Backtest complet de l'indicateur (DA par confiance / saison / régime) |

---

## 11. Critères de réussite finaux

### L'indicateur sera intéressant si :

| Critère | Objectif | Priorité |
|---|---|---|
| DA globale | > baseline saisonnière sur ≥1 horizon clé | Indispensable |
| AUC | > 0.55 sur ≥1 cible directionnelle | Indispensable |
| DA signaux confiants | > DA globale (au moins +5 pts) | Indispensable |
| DA top 20 % signaux | > 65 % | Indispensable |
| DA top 10 % signaux | > 70 % | Important |
| Fréquence signaux forts | ≥ 20 jours/an exploitables | Important |
| Persistance | Signal tient ≥ 3 jours dans 60 % des cas | Important |
| UNCERTAIN | ≈ hasard (DA ~50 %) ou forte volatilité | Indispensable |
| BULLISH | Retour moyen positif après signal | Indispensable |
| BEARISH | Retour moyen négatif après signal | Indispensable |
| Robustesse temporelle | Stable sur plusieurs années (pas une seule crise) | Indispensable |
| Cohérence économique | Facteurs SHAP économiquement interprétables | Important |
| Calibration | Reliability curve proche de la diagonale | Important |

### L'indicateur sera rejeté ou à revoir si :

- Les signaux confiants ne sont pas meilleurs que les autres
- La calibration est mauvaise (Brier > baseline, reliability curve dévie fortement)
- Les résultats viennent d'une seule année (2012 ou 2022) — test de robustesse échoue
- Le modèle ne bat jamais la baseline saisonnière
- Le score de confiance ne sert à rien (DA flat par tranche de confiance)
- Les facteurs SHAP n'ont pas de sens économique
- Le flip rate est trop élevé (signal instable, change de signe tous les 2 jours)
- La fréquence de signaux exploitables est < 10 jours par an (pas utilisable en pratique)

---

## 12. Conclusion

L'étude ne doit pas s'arrêter à "on a 60 % de DA". Ce n'est pas suffisant comme conclusion, mais ce n'est pas non plus mauvais.

La vraie suite est de **transformer ce signal moyen en indicateur sélectif, prudent, contextualisé et explicable.**

Le projet doit maintenant explorer systématiquement :
- Les bons horizons
- Les bonnes cibles
- Les bons contextes
- Les bonnes familles de données
- Les bons régimes
- Les signaux forts vs les signaux incertains
- La calibration
- L'explication économique
- La robustesse temporelle

**Le vrai indicateur professionnel ne doit pas être un modèle qui parle tout le temps.**

Il doit être un système qui dit :

```
Je vois un signal haussier exploitable.
Je vois un signal baissier exploitable.
Je ne vois pas de signal clair.
Le marché est trop incertain.
```

Et surtout :

> Historiquement, dans ce type de contexte, voilà à quel point ce signal était fiable.

C'est cette direction qui peut faire passer le projet d'une simple étude de prédiction à un vrai indicateur professionnel du marché du maïs — capable de fournir un signal de marché supplémentaire pour aider à raisonner les périodes favorables, défavorables ou incertaines, en s'appuyant sur de vraies études mathématiques et des validations historiques rigoureuses.

**Ce que l'indicateur ne doit pas promettre :**
- Il ne prédit pas le prix avec certitude
- Il ne garantit pas de vendre au plus haut
- Il ne remplace pas le jugement de l'agriculteur ou du négociant
- Il n'est pas conçu pour des décisions automatisées sans supervision

**Ce que l'indicateur peut apporter :**
- Un signal directionnel contextualisé avec niveau de confiance
- Une alerte sur les périodes à risque élevé ou à opportunité potentielle
- Une explication économique (quels facteurs poussent le signal)
- Une validation historique honnête (dans ce type de contexte, voilà ce qui s'est passé)
- Un outil d'aide à la décision, pas une décision automatique

---

## 13. Garde-fous scientifiques — règles anti-biais

### 13.1 Règle contre le sur-test (p-hacking)

Tu vas tester des dizaines de contextes, de cibles et de seuils. Le risque est de trouver un bon résultat par hasard statistique pur.

**Règle obligatoire :**

> Tout résultat prometteur doit être validé sur une période hors-échantillon séparée ou par validation temporelle robuste. Aucun seuil ne doit être choisi uniquement parce qu'il maximise le passé.

En pratique :
- Les seuils (confidence > 0.65, horizon J+20, tranche summer) sont choisis sur le jeu train/validation
- Ils sont ensuite évalués une seule fois sur la période test finale, sans ré-ajustement
- Si un contexte marche avec DA = 73 % mais seulement sur 8 jours, ce n'est pas robuste — c'est du bruit

### 13.2 Taille d'échantillon minimale par contexte

Quand on intersecte plusieurs filtres (été + bear + haute volatilité + WASDE), il peut rester très peu d'observations.

**Règle obligatoire :**

> Chaque analyse contextuelle doit afficher `n_obs`. Aucun résultat n'est considéré robuste si `n_obs < 50`.

Exemples :

| Résultat | n_obs | Interprétation |
|---|---|---|
| DA = 75 % | 18 | Intéressant mais non robuste — bruit probable |
| DA = 67 % | 420 | Robuste — à conserver |
| DA = 63 % | 1200 | Très robuste — base solide |

Corollaire : les contextes trop rares doivent être agrégés avec des contextes voisins, ou signalés comme "non concluant — n trop faible".

### 13.3 Validation out-of-time finale

**Principe :**

Réserver une période finale non utilisée pour choisir les seuils ou les règles. Cette période sert uniquement à évaluer la généralisation finale.

**Proposition :**
- Train + validation : jusqu'en décembre 2022
- Out-of-time final : 2023–2025

Cette période de test finale ne doit jamais être regardée avant que toutes les décisions de conception soient figées. Sinon elle est contaminée.

### 13.4 Comparaison à des indicateurs simples

L'indicateur complexe ne doit pas seulement battre les modèles ML bruts. Il doit aussi battre des indicateurs simples et naïfs :

| Indicateur simple | Description |
|---|---|
| `seasonal_indicator` | Signal basé uniquement sur la saisonnalité historique |
| `momentum_indicator` | Signal basé sur le momentum 20 jours |
| `wasde_tightness_indicator` | Signal basé sur le ratio stocks/use WASDE |
| `weather_stress_indicator` | Signal basé sur l'index de stress météo été |
| `cot_trend_indicator` | Signal basé sur la direction COT managed money |

Si l'indicateur complexe ne bat pas un indicateur "saisonnalité + momentum" sur les signaux confiants, il faut en tirer les conclusions honnêtement.

---

## 14. Prochains tickets à créer (8 tickets séquentiels)

8 tickets séquentiels, dans l'ordre des blocs. Développés entièrement dans `.ai/TICKETS_INDICATEUR.md`.

| # | Ticket | Bloc | Priorité |
|---|---|---|---|
| IND-01 | Validation baseline V2 — vérifier artefacts et résultats actuels | 1 | Immédiat |
| IND-02 | Comparaison complète des cibles — DA/AUC/Brier par cible | 2 | Après IND-01 |
| IND-03 | Oracle analysis — identifier les drivers futurs clés | 2 | Après IND-01 |
| IND-04 | Analyse par contexte — saison, mois, WASDE, régime, volatilité | 3 | Après IND-02 |
| IND-05 | Ablation des 13 familles + sélection de variables | 3 | Après IND-02 |
| IND-06 | Futures curve + surprises WASDE + météo avancée | 4 | Après IND-04+05 |
| IND-07 | Confiance, fréquence, persistance et calibration | 5 | Après IND-06 |
| IND-08 | Analyse des erreurs + indicateur V2 + backtest final | 5 | Final |

---

*Document maintenu dans `docs/INDICATEUR_PRO_ROADMAP.md` — version 2.0*
*Tickets développés dans `.ai/TICKETS_INDICATEUR.md`*
