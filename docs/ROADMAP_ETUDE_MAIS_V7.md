# Document de cadrage V7 — Étude du cours du maïs CBOT + Euronext
## Version intégrale — Étude de niveau recherche

---

## 1. Verdict général

L'étude a maintenant atteint un niveau de recherche sérieux. Le résultat principal n'est plus la prédiction brute du prix Euronext, mais la compréhension de la formation du prix européen par rapport au marché mondial.

Thèse centrale :

```text
CBOT = moteur mondial du maïs
Euronext EMA = prix européen
Basis EMA/CBOT = prime européenne
Résidu EU = choc spécifique Europe
Signal principal = EMA surperforme ou sous-performe CBOT
```

Le prix Euronext brut reste difficile à prédire directement. En revanche, la performance relative EMA/CBOT, surtout lorsque le basis est extrême et dans certaines saisons, est devenue le cœur exploitable de l'étude.

Verdict production : l'étude reste en `RESEARCH_ONLY_NOT_TRADING`, car l'historique EMA repose encore sur une source exploratoire/proxy et non sur un flux officiel Euronext complet.

---

## 2. Résultats actuels importants

### 2.1 CBOT

Le CBOT reste le moteur mondial. Le signal directionnel global est modeste mais réel.

Résultat canonique principal :

```text
CBOT J+60 HistGB
DA ≈ 62.4 %
AUC ≈ 67.5 %
DA hebdo ≈ 61.6 %
```

Nouveaux résultats V6 côté CBOT : les cibles spécialisées sont plus intéressantes que la direction brute.

Meilleures cibles auxiliaires CBOT :

```text
y_cbot_drawdown_5pct_h20 : AUC ≈ 0.750, top20 ≈ 0.889
y_cbot_drawdown_5pct_h60 : AUC ≈ 0.718, top20 ≈ 0.919
y_cbot_large_down_3pct_h90 : AUC ≈ 0.716, top20 ≈ 0.956
y_cbot_large_down_3pct_h60 : AUC ≈ 0.705, top20 ≈ 0.825
```

Lecture : pour CBOT, il faut davantage travailler sur les risques de drawdown, les grands mouvements et les contextes spécifiques que sur le simple `up/down`.

### 2.2 Euronext brut

La direction absolue EMA reste faible :

```text
y_up_h40_ema_raw
DA ≈ 51.9 %
AUC ≈ 52.9 %
Verdict : NO_GO comme cible principale
```

Conclusion : ne plus chercher à forcer cette cible. Elle mélange trop de dimensions : CBOT, change, basis, rolls, liquidité, Europe, Ukraine, météo, bruit.

### 2.3 EMA relatif au CBOT

C'est le cœur de l'étude.

Résultats robustes historiques :

```text
H40 : DA ≈ 64.0 %, AUC ≈ 70.8 %, top20 ≈ 77.1 %, weekly AUC ≈ 72.8 %
H90 : DA ≈ 69.0 %, AUC ≈ 77.0 %, top20 ≈ 88.7 %, weekly AUC ≈ 76.6 %
```

Résultats V6 meta-model :

```text
y_rel_outperform_h90 / classic_plus_meta
n = 503
DA ≈ 83.7 %
Balanced accuracy ≈ 85.4 %
AUC ≈ 93.7 %
top20 ≈ 97.0 %
ECE ≈ 0.121
```

Point de vigilance : ces résultats sont très forts, mais ils doivent rester `research-only` tant que la source EMA n'est pas officialisée et tant que les tests de robustesse complets ne sont pas terminés.

### 2.4 Basis EMA/CBOT

Le basis est le driver central.

```text
basis moyen ≈ 37.25 €/t
écart-type ≈ 15.50 €/t
AR(1) phi ≈ 0.970
half-life ≈ 22.8 jours
stationnarité ADF p ≈ 6.1e-8
cointégration EG p ≈ 7.3e-7 CONFIRMÉE
demi-vie VECM ≈ 83 jours
```

Les meilleures cibles conditionnelles utilisent le basis extrême :

```text
y_rel_outperform_when_basis_extreme_h40 : AUC ≈ 0.968, n OOF ≈ 91
y_rel_outperform_when_basis_extreme_h90 : AUC ≈ 1.000, n ≈ 29 (contexte étroit)
```

Lecture : le basis n'est pas une variable secondaire. C'est le cœur économique de la prime européenne.

### 2.5 Saisonnalité et roll-aware filters

Les politiques saisonnières et les filtres de roll améliorent fortement la sélectivité.

Meilleur résultat policy V6 :

```text
seasonal_expert / top20_train_only
n = 68
coverage ≈ 13.5 %
DA ≈ 98.5 %
balanced accuracy ≈ 98.3 %
AUC ≈ 98.2 %
```

Meilleur backtest research-only :

```text
seasonal_expert / top40_no_roll
9 trades
PnL total ≈ +179.65 €/t à coût 1 €/t/leg
PnL total ≈ +53.65 €/t à coût 8 €/t/leg
```

Point de vigilance : très prometteur, mais seulement 9 trades. Ce n'est pas encore une preuve production.

### 2.6 Tableau de bord global des verdicts V6

| Cible | Verdict | AUC | Remarque |
|---|---|---|---|
| EMA direction absolue H40 | NO_GO | 0.529 | Trop de bruit |
| EMA direction absolue H20 | NO_GO | 0.503 | Aucun signal |
| EMA premium relatif H40 | GO_RESEARCH | 0.708 | Signal robuste |
| EMA premium relatif H90 | PROMISING | 0.770 | Stress-test requis |
| EMA basis reversion H20 | DESCRIPTIF | 0.786 | Non prédictif OOF |
| CBOT direction H60 | GO_RESEARCH | 0.675 | Modeste mais réel |
| CBOT drawdown H20 | GO_RESEARCH | 0.750 | Meilleure cible CBOT |
| EMA basis extrême H40 | GO_RESEARCH | 0.968 | n faible, étroit |
| Meta-model H90 | PROMISING | 0.937 | Très fort, n=503 |
| Stockage EMA | NO_GO | — | Pas rentable OOF |
| CQR prix absolu | NO_GO | — | Coverage insuffisante |

---

## 3. Principes V7

1. Ne rien supprimer : tous les résultats positifs et négatifs sont conservés.
2. Tout enregistrer : chaque expérience doit entrer dans un registre global.
3. OOF strict obligatoire : aucune prédiction in-sample comme feature.
4. Purged CV / embargo obligatoire pour H40/H90/H120.
5. Les seuils doivent être appris uniquement sur le train.
6. Les meilleurs signaux à faible support ne doivent pas devenir des preuves centrales.
7. Le backtest reste research-only tant que la donnée EMA n'est pas officielle.
8. Le but n'est pas seulement d'augmenter la DA : le but est de comprendre le cours du maïs.
9. Chaque expérience doit avoir une hypothèse économique claire avant d'être lancée.
10. Toute découverte doit être réplicable avec le seed fixé.
11. Séparer nettement : signal économique descriptif / signal prédictif OOF.
12. Les vraies découvertes sont dans les erreurs autant que dans les succès.

---

## 4. Cadre théorique — Formation du prix du maïs

Avant de lancer des expériences, il faut poser le cadre économique formel. Chaque signal testé doit s'y rattacher.

### 4.1 Modèle structurel du prix Euronext

```text
P_EMA(t) = P_CBOT(t) × S(t) + Basis(t) + ε_EU(t)
```

où :
- `P_CBOT(t)` = prix CBOT en USD/boisseau, converti en EUR/t
- `S(t)` = taux EUR/USD
- `Basis(t) = P_EMA(t) - P_CBOT_EUR(t)` = prime européenne
- `ε_EU(t)` = résidu purement européen (météo EU, bilans EU, Ukraine, énergie)

### 4.2 Décomposition du basis

Le basis reflète en théorie :

```text
Basis(t) = coût de transport (FOB → ARA) 
         + coût de qualité (standard EU vs US)
         + prime de liquidité
         + différentiel réglementation/OGM
         + anticipation de récolte EU
         + prime de risque EUR/USD
         + écart saisonniers EU/US
         + résidu non expliqué
```

La thèse centrale de l'étude est que ce basis est partiellement prédictible, surtout quand il est extrême et dans certains contextes saisonniers.

### 4.3 Théorie du stockage (Kaldor-Working)

La théorie du stockage (Working, 1949 ; Kaldor, 1939) prédit :

```text
F(T) = S(t) × (1 + r)^(T-t) + coût_stockage - convenience_yield
```

Implications pour notre étude :
- Quand les stocks EU sont tendus, la convenience yield est élevée → basis haut.
- Quand les stocks EU sont abondants, le coût de portage domine → basis bas ou négatif.
- Les tests de cette relation (basis vs stocks) sont directement testables avec les données WASDE EU.

Hypothèse à tester :
```text
H1 : basis ~ f(ending_stocks_eu / utilisation_eu)
Attendu : corrélation négative (stocks bas → basis haut)
Test : régression OLS + OOF validation
```

### 4.4 Parité d'exportation

Le prix FOB Ukraine fixe un plancher pour EMA :

```text
P_EMA ≥ P_FOB_Ukraine + coût_transport_ARA + prime_qualité
```

Si P_EMA descend sous ce niveau, les importateurs européens achètent ukrainien/américain, ce qui fait remonter EMA.
Si P_EMA est très au-dessus, les exportateurs européens accélèrent les ventes, ce qui fait baisser EMA.

Hypothèse à tester :
```text
H2 : basis ~ f(P_EMA / P_FOB_Ukraine_EUR)
Attendu : mean-reversion autour d'un niveau d'équilibre d'importation
Test : régression cointegration + demi-vie
```

### 4.5 Parité éthanol CBOT

Le prix du maïs CBOT est ancré par la demande éthanol américain :

```text
P_ethanol_corn_parity = P_éthanol_maïs_US / rendement_éthanol
```

Si le maïs est trop cher par rapport à l'éthanol, la demande baisse → pression baissière.
Si le maïs est bon marché, les raffineries achètent → soutien.

Hypothèse à tester :
```text
H3 : signal CBOT conditionnel à (prix_maïs / prix_éthanol_parity)
Attendu : signal plus fort quand la parity est extrême
```

### 4.6 Substitution fourrages

Le maïs est en compétition avec le soja (protéines), le blé (énergie), le tournesol (huile) :

```text
Ratio maïs/soja = indicateur de substitution
Ratio maïs/blé = indicateur de compétitivité
```

Hypothèse à tester :
```text
H4 : mouvement relatif EMA/CBOT corrélé aux ratios de substitution EU
Attendu : quand blé/maïs EU est défavorable, demande maïs EU monte → basis monte
```

---

## 5. Hypothèses de recherche formelles

Chaque expérience V7 est rattachée à une hypothèse économique qu'elle teste.

| # | Hypothèse | Variable testée | Méthode | Priorité |
|---|---|---|---|---|
| H1 | Basis ~ stocks EU | ending_stocks_eu / use_eu | OLS + Granger OOF | HAUTE |
| H2 | Basis ~ parité FOB Ukraine | P_EMA / P_FOB_Ukraine_EUR | Cointégration | HAUTE |
| H3 | Signal CBOT ~ parité éthanol | corn_to_ethanol_parity | Ablation OOF | HAUTE |
| H4 | Basis ~ substitution fourrages EU | blé/maïs ratio EU | Corrélation + OOF | HAUTE |
| H5 | Premium EMA prédit si saison récolte EU | mois sep-nov | Modèle saisonnier | HAUTE |
| H6 | Premium EMA prédit si basis extrême | basis_zscore > 1.5 | Filtre + OOF | HAUTE |
| H7 | WASDE surprise cause mouvement CBOT | wasde_surprise | Event study + OOF | HAUTE |
| H8 | Roll crée des artefacts de prix EMA | DTE < 20 jours | Filtre roll-risk | HAUTE |
| H9 | EUR/USD amplifie ou atténue le basis | EURUSD_regime | Interaction term | MOYENNE |
| H10 | TTF gaz corrèle avec coûts transport/séchage | TTF price | Corrélation lead-lag | MOYENNE |
| H11 | Ukraine corridor crée un plancher basis | flux_export_Ukraine | Event study | MOYENNE |
| H12 | COT positioning prédit direction CBOT | cot_net_noncomm | Granger OOF | MOYENNE |
| H13 | Météo US (GDD, pluie) prédit CBOT | heat_stress + rain_deficit | Ablation OOF | MOYENNE |
| H14 | Météo EU (MARS) prédit premium | ndvi_eu + anomalie_pluie | Ablation OOF | MOYENNE |
| H15 | Soja/maïs ratio CBOT prédit direction CBOT | soy_corn_ratio | Corrélation OOF | BASSE |
| H16 | Baltic Dry Index prédit flux import | BDI | Lead-lag OOF | BASSE |
| H17 | Volatilité CBOT prédite est plus forte si WASDE proche | vol_implied × WASDE_proximity | Interaction | BASSE |
| H18 | EMA premium est auto-corrélé à court terme | ACF basis_delta | AR(1) | HAUTE |
| H19 | Crise Ukraine 2022 a changé le régime du basis | dummy 2022+ | Structural break | HAUTE |
| H20 | Basis est plus prédictible entre crises | exclusion crise | Leave-one-crisis-out | HAUTE |

---

## 6. Programme V7 — expériences à lancer

### V7-00 — Audit de cohérence V6

Objectif : valider que tous les résultats V6 sont cohérents entre eux.

Contexte : les résultats V6 meta-model (AUC 0.937) sont très au-dessus des résultats V5 (AUC 0.770). Avant d'aller plus loin, il faut s'assurer qu'il n'y a pas de leakage ou d'artefact.

À faire :

```text
- Vérifier toutes les périodes d'évaluation V6 (train/test non chevauchants) ;
- Vérifier que les meta-features V6-02 sont strictement OOF (pas de leakage) ;
- Vérifier les tailles d'échantillon de chaque expérience ;
- Vérifier la présence d'embargo temporel H jours sur H40/H90 ;
- Vérifier que les seuils dans V6-04 sont train-only ;
- Comparer les périodes d'évaluation V5 vs V6 (mêmes folds ?) ;
- Vérifier le registre V6-00 : IDs, métriques, configs hash ;
- Identifier toute expérience avec n < 50 et la marquer fragile ;
- Produire un rapport de cohérence complet.
```

Hypothèses à vérifier :

```text
- Les n très faibles (n=29 pour basis_extreme_h90) sont cohérents avec le filtre appliqué ?
- L'écart V5 (AUC 0.770) → V6 (AUC 0.937) est dû aux meta-features ou à un changement de période ?
- Le seasonal_expert/top20 (n=68, AUC 0.982) utilise bien des seuils train-only ?
```

Livrables :

```text
artefacts/v7/v6_consistency_audit.json
docs/V6_CONSISTENCY_AUDIT.md
```

---

### V7-01 — Source EMA officielle ou validation proxy

Objectif : transformer la limite principale en plan d'action concret.

Contexte : 100% des résultats EMA reposent sur la source Barchart proxy exploratory. Ce n'est pas le prix de settlement officiel Euronext. Avant tout claim, il faut valider que les signaux sont robustes sur la donnée réelle.

À faire :

```text
- Identifier toutes les sources officielles disponibles :
  * Euronext NextHistory (abonnement professionnel)
  * Refinitiv / LSEG Eikon
  * Bloomberg (EMA Comdty)
  * Nasdaq Data Link (anciennement Quandl)
  * Barchart OnDemand (EOD premium)
  * Roper Technologies / CQG
  * ICE Data Services
- Pour chaque source : noter coût, granularité, couverture historique, settlement vs close ;
- Comparer proxy vs officiel sur la période 2023-2025 (données récentes disponibles) :
  * corrélation niveau
  * corrélation rendements
  * MAE settlement vs close
  * gap max observé
  * jours où proxy est absurde
- Recalculer le benchmark premium H40/H90 sur la sous-période officielle ;
- Classer les périodes du dataset :
  * OFFICIAL (post-acquisition officielle)
  * PROXY_HIGH_CONF (2018-2022, faible écart observé)
  * PROXY_LOW_CONF (2010-2017, écart potentiel élevé)
  * UNKNOWN
- Mesurer l'impact sur AUC si on retire PROXY_LOW_CONF.
```

Critère de succès :

```text
Si AUC premium H40 ≥ 0.65 sur période officielle → crédibilité élevée
Si delta AUC proxy vs officiel < 0.05 → proxy utilisable sous réserve
Si delta AUC > 0.10 → résultats antérieurs à réviser
```

Livrables :

```text
artefacts/v7/ema_source_validation.json
docs/EMA_SOURCE_VALIDATION.md
```

---

### V7-02 — Purged CV avec embargo pour H40/H90/H120

Objectif : vérifier que les horizons longs ne profitent pas du chevauchement des fenêtres.

Contexte : avec H90, deux observations consécutives partagent 89 jours de chevauchement. Si les labels sont corrélés, le modèle peut "voir" le futur indirectement. Il faut tester des protocoles stricts.

Protocoles à comparer :

```text
1. Walk-forward classique (actuel)
2. Walk-forward avec embargo H jours (aucune observation dans les H jours précédant le test)
3. Walk-forward avec embargo 2×H jours (précaution maximale)
4. Non-overlap strict (une observation par fenêtre non chevauchante)
5. Block bootstrap (blocs de 20/40/60 jours)
6. Leave-one-year-out (12 variantes)
7. Leave-one-crop-year-out (saison sep-août, ~7-8 variantes)
8. Leave-one-crisis-out (2012, 2020, 2022, 2024)
9. Purged KFold avec taille de gap variable (5/10/20/45/90 jours)
```

Cibles à tester :

```text
y_rel_outperform_h40
y_rel_outperform_h90
y_rel_outperform_h120
y_rel_outperform_when_basis_extreme_h40
y_cbot_drawdown_5pct_h20
```

Questions :

```text
- L'AUC chute-t-elle avec embargo strict ? De combien ?
- La cible H90 est-elle plus fragile à l'embargo que H40 ?
- Quel est le protocole minimum pour avoir confiance dans les résultats ?
- Le walk-forward classique est-il optimiste ?
```

Livrables :

```text
artefacts/v7/purged_cv_embargo_study.json
docs/PURGED_CV_EMBARGO.md
```

---

### V7-03 — Cross-target stacking V2

Objectif : utiliser toutes les meilleures cibles comme capteurs de marché dans un méta-modèle augmenté.

Contexte V6 : V6-02/V6-03 montrent que les OOF auxiliaires améliorent H90 premium. Il faut maintenant généraliser et tester toutes les combinaisons possibles.

Experts niveau 0 (séries OOF à générer) :

```text
Famille CBOT :
  cbot_direction_h20, cbot_direction_h40, cbot_direction_h60, cbot_direction_h90
  cbot_drawdown_5pct_h20, cbot_drawdown_5pct_h60
  cbot_rally_5pct_h20, cbot_rally_5pct_h40
  cbot_large_down_3pct_h60, cbot_large_down_3pct_h90
  cbot_vol_high_h20, cbot_vol_high_h40

Famille EMA relative :
  ema_rel_outperform_h20, ema_rel_outperform_h40, ema_rel_outperform_h60,
  ema_rel_outperform_h90, ema_rel_outperform_h120
  ema_large_outperform_h40, ema_large_outperform_h90
  ema_large_underperform_h40, ema_large_underperform_h90

Famille basis :
  basis_extreme_h20, basis_extreme_h40, basis_extreme_h90
  basis_compression_h20, basis_compression_h40
  basis_expansion_h20, basis_expansion_h40
  basis_reversion_h20, basis_reversion_h40

Famille contexte :
  volatility_warning_h20, volatility_warning_h40
  residual_shock_up_h20, residual_shock_down_h20
  seasonal_strong_signal_h40
  roll_risk_warning
```

Meta-features à calculer :

```text
mean_rel_signal
std_rel_signal
median_rel_signal
h40_h90_agreement  (signe identique oui/non)
h90_h120_agreement
cbot_ema_disagreement
basis_model_agreement
volatility_warning_flag
residual_shock_warning_flag
signal_entropy  (distribution des probabilités)
max_confidence_any_model
n_models_bullish
n_models_bearish
n_models_uncertain
cbot_bullish × basis_extreme  (interaction)
ema_rel_h40 × season_harvest  (interaction)
```

Comparaisons :

```text
features classiques seules (baseline)
meta-features seules
features classiques + meta-features
basis rule seule
basis z-score rule + meta
basis + meta + saison
basis + meta + saison + roll filters
basis + meta + saison + roll filters + P(correct)
```

Protocole : walk-forward avec embargo H90 jours, seuils train-only.

---

### V7-04 — CBOT Target Lab avancé

Objectif : appliquer les découvertes EMA à CBOT et trouver les meilleures cibles CBOT.

Contexte : les résultats V6 montrent que les cibles CBOT spécialisées (drawdown, rally, large move) sont plus prédictibles que la direction brute. Il faut explorer toutes les variations.

Cibles à tester (exhaustif) :

```text
Direction simple :
  y_cbot_up_h20, y_cbot_up_h40, y_cbot_up_h60, y_cbot_up_h90

Grands mouvements :
  y_cbot_large_up_3pct_h20, y_cbot_large_up_3pct_h40
  y_cbot_large_up_5pct_h20, y_cbot_large_up_5pct_h40
  y_cbot_large_down_3pct_h20, y_cbot_large_down_3pct_h40, y_cbot_large_down_3pct_h60, y_cbot_large_down_3pct_h90
  y_cbot_large_down_5pct_h20, y_cbot_large_down_5pct_h40

Drawdown / Rally :
  y_cbot_drawdown_3pct_h20, y_cbot_drawdown_5pct_h20, y_cbot_drawdown_5pct_h40, y_cbot_drawdown_5pct_h60
  y_cbot_rally_3pct_h20, y_cbot_rally_5pct_h20, y_cbot_rally_5pct_h40

Triple barrier :
  y_cbot_triple_barrier_3pct_h40  (up/down/neutral)
  y_cbot_triple_barrier_5pct_h60

Conditionnels (le vrai intérêt) :
  y_cbot_up_when_stocks_tight_h60       (condition : ending_stocks/use < percentile25)
  y_cbot_down_when_stocks_abundant_h60  (condition : ending_stocks/use > percentile75)
  y_cbot_down_when_cot_extreme_long_h40 (condition : cot_net_noncomm > percentile80)
  y_cbot_up_when_cot_extreme_short_h40  (condition : cot_net_noncomm < percentile20)
  y_cbot_up_when_weather_stress_h40     (condition : GDD_heat > 2σ ou rain_deficit > 2σ)
  y_cbot_move_after_wasde_h5            (5 jours post-WASDE)
  y_cbot_up_when_ethanol_parity_cheap   (condition : maïs < parité éthanol)
  y_cbot_down_when_ethanol_parity_dear  (condition : maïs > parité éthanol)
  y_cbot_up_when_brazil_export_slow     (condition : Brazil pace < moyenne)
  y_cbot_down_when_brazil_export_fast   (condition : Brazil pace > moyenne)
```

Métriques à calculer pour chaque cible :

```text
AUC, DA, balanced accuracy, top20 DA, MCC
positive rate (classe +)
n OOF exploitable
stability par année
stability par saison
meilleur horizon parmi H20/H40/H60/H90
```

---

### V7-05 — Cross-market CBOT ↔ EMA

Objectif : tester formellement si EMA aide CBOT et si CBOT aide EMA.

Contexte : V6-05 montre que EMA premium ajoute du signal à certains risques CBOT (delta AUC +0.059 sur y_cbot_up_h60). Il faut systématiser ce test.

Direction EMA → CBOT :

```text
Features EMA ajoutées au modèle CBOT :
  ema_cbot_basis
  basis_zscore_52w
  premium_indicator_signal
  pred_rel_outperform_h40  (OOF)
  pred_rel_outperform_h90  (OOF)
  eu_weather_stress
  ukraine_export_risk
  ec_mars_yield_revision
  franceagrimer_bilan_surprise
  ema_oi_total (liquidité)
  ema_roll_risk
```

Direction CBOT → EMA premium :

```text
Features CBOT ajoutées au modèle EMA premium :
  pred_cbot_up_h60  (OOF)
  pred_cbot_drawdown_h20  (OOF)
  pred_cbot_vol_high  (OOF)
  cot_crowding_signal
  wasde_surprise_net
  export_sales_pace_vs_usda
  ethanol_demand_vs_trend
  brazil_corn_crop_revision
```

Questions fondamentales :

```text
1. Une prime EU extrême précède-t-elle un mouvement CBOT ?
   → Test : Granger OOF, basis_extreme → cbot_h5/h10/h20 AUC
2. Le signal CBOT améliore-t-il le premium EMA/CBOT ?
   → Test : ablation OOF pred_cbot sur EMA premium
3. Les divergences EMA/CBOT sont-elles des signaux d'arbitrage ou de stress local ?
   → Test : event study autour des divergences > 2σ
4. Quel est le sens de causalité dominant ?
   → Test : Granger OOF dans les deux sens
5. La transmission CBOT→EMA varie-t-elle selon les régimes ?
   → Test : modèle avec interaction β(t) rolling
```

---

### V7-06 — Modèles saisonniers experts

Objectif : exploiter la forte saisonnalité du marché du maïs.

Contexte : V6-04 montre que les politiques saisonnières donnent les meilleurs résultats (AUC 0.982). Il faut maintenant construire des modèles séparés par saison.

Saisons à définir :

```text
jan-mar : old crop / import / stocks hiver
  driver principal : pace d'importation EU
  features clés : import_eu_pace, ema_oi, eurusd, basis_level

apr-jun : semis Europe / récolte Brésil
  driver principal : avancement des semis EU + météo US semis
  features clés : ec_mars_sowing, GDD_us_plant, brazil_harvest_pace

jul-aug : stress rendement EU et US
  driver principal : météo été US et EU
  features clés : heat_stress_us, heat_stress_eu, rain_deficit_us, rain_deficit_eu, NDVI

sep-nov : récolte Europe / nouvelles récoltes
  driver principal : rendements EU confirmés + pression saisonnière
  features clés : ec_mars_yield_final, franceagrimer_recolte, harvest_progress_eu

dec : arbitrage import/export / transition crop year
  driver principal : anticipation carryout EU + WASDE
  features clés : wasde_eu_ending_stocks, cot_rebalancing, basis_niveau
```

Pour chaque saison, optimiser :

```text
- meilleur horizon cible (H20, H40, H60, H90)
- meilleur target (direction, premium, drawdown)
- seuil basis adapté (z-score calibré sur train-saison uniquement)
- meilleur modèle (LogReg, HistGB, Ridge, Ensemble)
- meilleures features (ablation par famille)
- performance top20 / top40
- backtest research-only avec seuils train-only
```

Méta-modèle saisonnier :

```text
score_global(t) = w_saison(t) × score_saison(t)
               + (1 - w_saison(t)) × score_global_baseline(t)

où w_saison = confiance de la saison courante (calibrée OOF)
```

---

### V7-07 — Roll-aware premium model

Objectif : réduire les erreurs dues aux rolls de contrats EMA.

Contexte : V6-04 montre que les erreurs de roll sont la première source d'erreur du modèle premium (ROLL_ARTIFACT = 86 sur H40, 70 sur H90). Il faut y remédier.

À tester :

```text
Filtres durs (no signal) :
  DTE < 10 jours
  DTE < 15 jours
  DTE < 20 jours
  DTE < 30 jours
  DTE < 45 jours (prudent)
  mois de roll proxy (H, M, Q, X selon calendrier EMA)
  fenêtre [-5j, +3j] autour de la date de roll estimée

Score continu de roll-risk :
  roll_risk = f(DTE, gap_historique_moyen, volatilité_récente)
  roll_risk_percentile = percentile du gap historique
  expected_roll_gap_eur = gap moyen estimé pour ce roll

Comparaisons de séries :
  front vs liquid (liquidité)
  harvest_nov vs front (saison)
  adjusted vs raw (rendements ajustés)
  séries continues lissées vs brutes

Modèle séparé par période de roll :
  modèle_near_roll (DTE < 20j)
  modèle_mid_expiry (DTE 20-60j)
  modèle_far_expiry (DTE > 60j)
```

Métriques d'amélioration :

```text
delta AUC baseline → roll-filtered
delta % erreurs tagguées ROLL_ARTIFACT
delta PnL backtest avec exclusion roll vs sans
nombre de trades disponibles avec filtre strict
```

---

### V7-08 — Régimes de basis

Objectif : classifier les états de prime européenne pour mieux contextualiser les signaux.

Contexte : le basis varie énormément (37 ± 15 €/t, max observé > 100 €/t). Ces régimes ne sont pas aléatoires — ils reflètent des états fondamentaux du marché.

Régimes à chercher :

```text
NORMAL        : basis dans intervalle ±1σ, pas de choc
HIGH_STABLE   : basis > +1.5σ, stable ≥ 3 semaines
HIGH_COMPRESSING : basis > +1.5σ ET en baisse (mean reversion en cours)
HIGH_EXPANDING : basis > +1σ ET en hausse (feed du choc)
LOW_BASIS     : basis < -1σ (importations compétitives dominent)
CRISIS_EUROPE : choc EU brutal, résidu EU élevé
ROLL_DISTORTED : periode de roll, basis peu fiable
```

Méthodes de détection :

```text
1. Règles manuelles sur z-score + delta basis
2. KMeans (k=4, k=5, k=6, k=7) sur (basis_level, basis_delta, basis_accel, vol, saison)
3. Gaussian Mixture Model (GMM) : permet clusters elliptiques
4. Markov Switching Regression : régimes latents avec transitions probabilistes
5. HDBSCAN : détection non paramétrique si disponible
6. Hidden Markov Model (HMM) : séquence d'états avec émissions gaussiennes
```

Validation des régimes :

```text
- Stabilité des clusters sur différentes sous-périodes
- Interprétabilité économique (chaque cluster doit avoir un sens)
- Performance différentielle : AUC premium H40 par régime
- Transition probability matrix : état suivant prévisible ?
- Score de Silhouette / BIC pour comparer k
```

Utilisation dans le modèle final :

```text
feature = regime_courant  (one-hot ou ordinal)
feature = regime_probability_vector  (prob de chaque régime)
feature = jours_dans_regime_courant
feature = transition_imminent_score  (prob de changement prochain)
```

---

### V7-09 — Décomposition dynamique EMA

Objectif : mieux expliquer la formation du prix EMA dans le temps.

Modèle général :

```text
ΔEMA(t) = β1(t)×ΔCBOT(t) + β2(t)×ΔEURUSD(t) + β3(t)×Δbasis(t)
        + β4(t)×ΔTTF(t) + β5(t)×Δweather_EU(t) + β6(t)×Δukraine(t)
        + ε(t)
```

L'objectif est de mesurer comment ces bêtas (β) varient dans le temps.

Méthodes :

```text
1. Rolling OLS (fenêtre 60j, 120j, 252j)
   → Observer la non-stationnarité des bêtas
   → Détecter les moments où β_CBOT chute et β_EU monte

2. Rolling Ridge
   → Même chose avec régularisation si multicolinéarité

3. Kalman Filter (DLM - Dynamic Linear Model)
   → Estimation state-space des bêtas variant en continu
   → Plus fluide que rolling OLS
   → Permet de prédire le beta prochain

4. VECM (Vector Error Correction Model)
   → Modélise la relation de long terme (cointegration)
   → Teste la vitesse d'ajustement EMA → équilibre
   → Asymétrie : ajustement plus rapide quand EMA est trop haut ?

5. Markov Switching Regression
   → Bêtas différents selon le régime latent
   → Deux ou trois régimes : crise, normal, rally

6. TVTP (Time-Varying Transition Probability)
   → Probabilités de transition conditionnelles à des variables d'état
   → Par exemple : prob(crise → normal) ~ f(basis_zscore)
```

Questions :

```text
- Quelle est la sensibilité EMA/CBOT pendant les crises (2020, 2022) ?
- Y a-t-il des périodes où EMA s'autonomise du CBOT (β_CBOT faible) ?
- Ces périodes correspondent-elles à des chocs EU spécifiques ?
- Le VECM montre-t-il une asymétrie d'ajustement (au-dessus vs en-dessous de la valeur juste) ?
```

---

### V7-10 — Event study premium

Objectif : mesurer l'impact des événements fondamentaux sur la prime EMA/CBOT.

Protocole d'event study :

```text
Pour chaque événement :
  - Identifier date de publication (t=0)
  - Calculer rendements EMA, CBOT, basis dans les fenêtres :
    [-5j, +5j], [-5j, +20j], [-5j, +40j]
  - Calculer rendement relatif EMA vs CBOT
  - Calculer changement basis
  - Estimer la réaction de volatilité (volatilité après vs avant)
  - Calculer le hit rate (EMA > CBOT ou CBOT > EMA)

Normalisation : rendements ajustés = rendement - benchmark (marché calme)
Test : t-test sur l'abnormal return cumulé
```

Événements à tester :

```text
WASDE mensuel USDA :
  - surprise positive vs consensus stocks mondiaux
  - surprise négative vs consensus stocks mondiaux
  - surprise sur stocks EU spécifiquement
  - surprise sur production Ukraine

EC MARS mensuel :
  - révision positive rendement EU > +0.3 t/ha
  - révision négative rendement EU < -0.3 t/ha
  - première publication saison (mai)
  - publication récolte (octobre)

FranceAgriMer bilans :
  - révision bilan maïs France positif
  - révision bilan maïs France négatif

Ukraine :
  - corridor Mer Noire ouvert/fermé
  - révision production Ukraine majeure
  - incidents shipping majeurs

Météo extrême EU :
  - chaleur > 35°C sur zone production EU ≥ 3 jours
  - déficit pluviométrique EU ≥ 30% sur 4 semaines
  - gel printanier tardif EU (< +2°C après 15 avril)

Météo extrême US :
  - heat stress GDD anormal juillet-août
  - corn belt drought D2+ apparaît/s'intensifie

COT Extrêmes :
  - non-commerciaux net long > percentile90 historique
  - non-commerciaux net short < percentile10 historique
  - reversement rapide > 50k contrats en une semaine

EUR/USD chocs :
  - journée EUR/USD > +1.5% ou < -1.5%
  - changement de tendance EUR/USD > 5% en 10 jours

TTF / Énergie :
  - spike TTF > +20% en une semaine (coût séchage maïs)
  - chute TTF > -20% en une semaine
```

Sorties :

```text
- abnormal_return_cumul_h5, h20, h40 (EMA vs CBOT)
- basis_response_h5, h20, h40
- volatility_spike_ratio
- hit_rate_ema_outperforms_post_event
- post_event_predictability_auc (signal model post-event)
```

---

### V7-11 — Données européennes V2

Objectif : renforcer les vrais drivers européens et éliminer les données proxy faibles.

Priorités par catégorie :

```text
CATÉGORIE 1 — Fondamentaux production EU (priorité HAUTE) :
  1. EC MARS mensuel réel
     - yield_revision_eu par mois
     - ndvi_anomaly_eu (indices de végétation)
     - yield_estimate_corn_eu_monthly
     Source : JRC MARS Bulletin (gratuit, mensuel)

  2. FranceAgriMer bilans mensuels maïs
     - production_france_corn
     - utilisation_france_corn
     - stocks_france_corn
     - exportations_france_corn
     Source : FranceAgriMer publications mensuelles (PDF parseable)

  3. Eurostat COMEXT import/export maïs UE
     - import_eu_corn_mt (depuis Ukraine, USA, Brésil)
     - export_eu_corn_mt
     Source : Eurostat COMEXT API (gratuit)

  4. Production Ukraine par zone
     - surface_plantée, surface_récoltée, rendement
     - exportations Ukraine mensuelles
     Source : USDA FAS, Grain Ukraine
```

```text
CATÉGORIE 2 — Logistique et prix fret (priorité HAUTE) :
  5. Prix FOB Ukraine (Odessa/Mykolaiv)
     - fob_ukraine_corn_usd_t
     - spread FOB Ukraine / CBOT
     - spread FOB Ukraine / EMA
     Source : IGC, USDA, Argus Media, GASC tenders

  6. Prix FOB Brésil (Paranaguá)
     - fob_brazil_corn_usd_t
     - spread FOB Brazil / CBOT
     Source : MDIC Brazil, SECEX

  7. Prix FOB Bordeaux / ARA
     - fob_bordeaux_corn_eur_t
     - fob_ara_corn_eur_t
     Source : FranceAgriMer, Reuters commodities

  8. Fret maritime
     - baltic_dry_index  (global shipping)
     - capesize_rates (blé/maïs gros volumes)
     - panamax_rates (maïs typique)
     - supramax_rates
     - fret_specifique_mais_ukraine_ara
     Source : Baltic Exchange (via yfinance BDI proxy), IGC
```

```text
CATÉGORIE 3 — Énergie et intrants EU (priorité MOYENNE) :
  9. TTF gaz naturel EU (déjà en partie)
     - ttf_prix, ttf_zscore
     - corrélation ttf → coût séchage maïs
     - ttf_forward_curve slope

  10. ETS CO2 (EU emissions trading)
      - co2_price_eur_t
      - corrélation CO2 → coût énergie agro-industrie

  11. Engrais EU
      - urea_price_eu_eur_t  (azote → coût production)
      - ammonia_price_eu
      - phosphate_price
      Source : Yara, CRU Group, ICIS
```

```text
CATÉGORIE 4 — Météo EU pondérée (priorité MOYENNE) :
  12. Météo EU pondérée par zone de production maïs
      - Zones principales : France/Gironde, Espagne/Aragon, Hongrie, Roumanie, Ukraine west
      - Variables : temperature, precipitation, GDD (growing degree days)
      - Pondération : poids proportionnel à production EU par pays
      Source : Open-Meteo (déjà partiellement collecté)
      Amélioration : pondération production vs zones égales

  13. Indices de végétation
      - NDVI anomaly EU corn belt
      - EVI (enhanced vegetation index)
      Source : NASA MODIS, Sentinel via Copernicus
```

```text
CATÉGORIE 5 — Contexte macroéconomique EU (priorité BASSE) :
  14. EUR/USD régimes
      - eurusd_level, eurusd_zscore
      - eurusd_regime (appréciation / dépréciation accélérée)
      - eurusd_carry_proxy

  15. Spreads obligataires EU (indicateur de stress financier EU)
      - spread Italy/Germany 10y
      - spread Spain/Germany 10y
      - indicator : stress financier EU = spread > 2% →
        potentiellement: imports moins abordables, basis compressé
```

Validation de chaque nouvelle donnée :

```text
- delta_auc : impact sur AUC premium H40 en ablation OOF
- delta_top20 : impact sur top20 DA
- delta_pnl : impact sur backtest research-only
- delta_explicabilite : feature importance SHAP relative
- disponibilité : couverture historique réelle
- fiabilité : source officielle ou proxy
```

---

### V7-12 — P(correct) et calibration avancée

Objectif : apprendre quand le signal sait qu'il sait.

Contexte : le modèle premium a une proba OOF. Mais cette proba est-elle bien calibrée ? Et peut-on prédire, avant de donner le signal, si ce signal va être correct ?

Cible de méta-apprentissage :

```text
correct(t) = 1 si pred_premium(t) dans la bonne direction sur H40
correct(t) = 0 sinon

Note : correct est calculé OOF (on ne peut pas utiliser la proba du même modèle comme feature)
```

Features pour prédire correct(t) :

```text
probabilité modèle  (proba OOF du meta-model)
basis_zscore  (signal économique direct)
basis_extreme  (flag)
saison  (one-hot)
roll_risk_score  (continu)
volatilité_récente  (std 20j)
h40_h90_agreement  (accordent-ils ?)
meta_entropy  (entropie du vecteur de probas)
data_quality_score  (disponibilité features EU)
event_proximity  (jours avant prochain WASDE ou MARS)
jours_dans_regime  (combien de temps dans le regime courant)
regime_change_score  (prob que le regime change)
n_models_agree  (combien de modèles dans la même direction)
prev_correct_rate_30j  (taux de succès récent du modèle)
```

Critères de validation :

```text
ECE (Expected Calibration Error) < 0.05
  → bucket 70% ≈ 70% correct (±5%)
  → bucket 80% ≈ 80% correct (±5%)
Brier score inférieur au modèle sans P(correct)
Top20 P(correct) supérieur au top20 modèle actuel (≥+2 pts)
AUC P(correct) > 0.60
```

Utilisation dans l'indicateur final :

```text
signal_final = signal_premium × P(correct)  (pondération confiance)
abstention si P(correct) < 0.45
signal_fort si P(correct) > 0.65 ET signal_premium > 0.60
```

---

### V7-13 — Backtests recherche avancés

Deux familles de backtests research-only.

#### Famille A — CBOT

```text
Stratégie : long CBOT si pred_cbot_direction positif, flat ou short sinon
Horizon : H40 ou H60

Protocole strict :
  1. Signal calculé le vendredi
  2. Entrée le lundi ouverture (slippage estimé)
  3. Sortie après H jours
  4. Seuil décision : percentile70 ou percentile80 de la distribution train
  5. Non-overlap strict (H jours de gap minimum entre trades)
  6. No trade si volatilité > 2σ historique (risque incontrôlé)
  7. Coûts : 1/2/3/5/8 EUR/t (stress test)
```

#### Famille B — EMA premium

```text
Stratégie : long EMA/short CBOT si pred_outperform positif
            short EMA/long CBOT si pred_outperform négatif
Horizon : H40 ou H90

Protocole strict :
  1. Signal calculé le vendredi
  2. Entrée le lundi (slippage 1-3 EUR/t par leg)
  3. Sortie après H jours
  4. Seuil train-only (percentile70 ou percentile80)
  5. Non-overlap strict (H jours de gap minimum)
  6. No trade si DTE < 20 jours (filtres roll)
  7. No trade si roll_risk_score > 0.7
  8. No trade si data_quality_score < 0.4
  9. Coûts : 1/2/3/5/8 EUR/t par leg
  10. Slippage additionnel : 1/2 EUR/t (bid-ask proxy)
```

Métriques de backtest :

```text
- nombre de trades
- coverage (% du temps en position)
- hit rate
- PnL total EUR/t
- PnL moyen par trade
- PnL par année (stabilité)
- max drawdown
- max losing streak
- profit factor (sum wins / sum losses)
- Sortino ratio
- Calmar ratio (PnL / max drawdown)
- rolling 12m PnL (est-ce stable ?)
- worst single trade
- stress test à 5 EUR/t et 8 EUR/t
```

Verdict toujours `RESEARCH_ONLY_NOT_TRADING`.

---

### V7-14 — Explicabilité et analyse des erreurs

Objectif : comprendre POURQUOI le modèle se trompe.

Protocole :

```text
Phase 1 : Caractériser les erreurs
  - Pour chaque erreur (pred wrong) du model premium H40 :
    * basic features au moment t
    * basis_zscore, saison, roll_risk
    * distance temporelle au prochain événement majeur
    * regime au moment t
    * performance récente du modèle (était-il chaud ou froid ?)
  - Tagger chaque erreur (liste ci-dessous)

Phase 2 : Analyser les erreurs par catégorie
  - Fréquence par tag
  - Fréquence par saison
  - Fréquence par régime basis
  - Fréquence par roll-risk level
  - AUC du modèle en excluant chaque catégorie

Phase 3 : Analyser les top20 faux positifs
  - Quand le modèle est sûr mais faux : c'est le plus dangereux
  - Caractériser leurs features spécifiques
  - Y a-t-il un pattern commun ?

Phase 4 : Construire une règle de veto
  - Si l'erreur est dominée par ROLL_ARTIFACT → filtre roll-risk
  - Si l'erreur est dominée par CRISIS_PERIOD → filtre volatilité
  - Si l'erreur est dominée par UNKNOWN → signal peu fiable
```

Taxonomie des tags :

```text
ROLL_ARTIFACT   : erreur liée à la mécanique de roll EMA
DATA_PROXY      : erreur liée à la qualité données EMA (proxy)
CBOT_SHOCK      : choc CBOT inattendu qui domine EMA
EU_WEATHER      : événement météo EU qui perturbe la prime
UKRAINE         : corridor Ukraine, conflit, export
EURUSD_SHOCK    : mouvement EUR/USD > 1.5% en 1 jour
MARS_SURPRISE   : révision EC MARS inattendue
WASDE_SURPRISE  : WASDE surprise contre le signal
ENERGY_SPIKE    : choc TTF ou énergie EU
LIQUIDITY_LOW   : OI EMA très faible, spread large
SEASONALITY_BREAK : saisonnalité perturbée (ex: 2022 guerre → récolte différée)
UNKNOWN         : aucun tag dominant
```

---

### V7-15 — Rapport final V7

Objectif : produire une étude finale lisible par un professionnel du marché et par un chercheur académique.

Structure du rapport :

```text
0. Abstract (une page)
1. Introduction et contexte de marché
2. Données et sources (avec table de fiabilité)
3. CBOT — moteur mondial du maïs
   3.1 Signal directionnel global
   3.2 Cibles spécialisées (drawdown, rally, large moves)
   3.3 Drivers fondamentaux validés
4. Euronext EMA — prix européen
   4.1 Pourquoi EMA brut est NO_GO
   4.2 Décomposition structurelle EMA
   4.3 Relation de cointégration EMA/CBOT
5. Basis EMA/CBOT — la prime européenne
   5.1 Propriétés statistiques du basis
   5.2 Drivers économiques du basis
   5.3 Mean reversion et régimes
6. Performance relative EMA/CBOT
   6.1 Signal H40 : résultats et robustesse
   6.2 Signal H90 : candidat prometteur
   6.3 Cibles conditionnelles (basis extrême)
7. Cross-target stacking V7
   7.1 Meta-features et méta-modèle
   7.2 Protocole OOF strict
   7.3 Comparaison des combinaisons
8. Saisonnalité
   8.1 Résultats par saison
   8.2 Modèles experts saisonniers
9. Roll-aware filters
   9.1 Impact des rolls sur les erreurs
   9.2 Filtres optimaux
10. Données européennes
    10.1 Données actuelles et lacunes
    10.2 Impact des nouvelles sources
11. Event study
    11.1 Réaction au WASDE
    11.2 Réaction aux données EU
12. Backtests research-only
    12.1 CBOT
    12.2 EMA premium
    12.3 Stress tests
13. Ce qui marche (table complète)
14. Ce qui ne marche pas (table complète)
15. Limites
    15.1 Source EMA proxy
    15.2 Taille des échantillons
    15.3 Overfitting de structure saisonnière
    15.4 Coûts non observés
16. Roadmap indicateur professionnel
    16.1 Conditions pour passer en production
    16.2 Architecture de l'indicateur final
    16.3 Infrastructure nécessaire
```

---

## 7. Nouvelles expériences V7 (non prévues dans V6)

### V7-16 — Analyse microstructure et liquidité EMA

Objectif : comprendre comment la liquidité EMA affecte la formation du basis et la fiabilité des signaux.

Contexte : EMA est un marché moins liquide que CBOT. Cette liquidité varie selon les contrats, les saisons et les périodes. Elle peut expliquer pourquoi certains signaux sont artefacts.

Variables à étudier :

```text
volume_ema : volume journalier par contrat
oi_ema : open interest par contrat
bid_ask_spread_proxy : estimé par volatilité intra-journalière si disponible
volume_ratio = volume_ema / volume_cbot_eur_equivalent
oi_ratio = oi_ema / oi_cbot
oi_change_1j : variation OI (accumulation ou liquidation)
oi_change_5j : variation OI semaine
front_vs_next_oi_ratio : concentration sur le front vs le prochain contrat
near_roll_liquidite_drop : chute de liquidité avant roll
```

Questions :

```text
1. La liquidité EMA est-elle plus élevée dans certaines saisons ?
   → Attendu : pic liquidité autour de la récolte EU (sep-nov)

2. Le basis est-il plus "fiable" (moins de bruit) quand l'OI est élevé ?
   → Test : corrélation abs(basis_error_proxy) ~ 1/OI_ema

3. Les erreurs du modèle premium sont-elles corrélées à la faible liquidité ?
   → Test : AUC par décile de OI_ema

4. Les spreads bid-ask implicites sont-ils dans les coûts de backtest ?
   → Estimation via Corwin-Schultz estimator si données OHLC disponibles

5. L'OI change est-il un signal (smart money positioning sur EMA) ?
   → Test : AUC OI_change_5j sur target premium H20/H40
```

---

### V7-17 — Relations inter-commodités

Objectif : comprendre comment le maïs s'inscrit dans le complexe agricole mondial.

Relations fondamentales :

```text
1. Maïs / Soja (CBOT)
   ratio = ZC/ZS (bushels)
   Interprétation :
   - ratio bas → soja cher → incitation à planter soja → moins maïs l'an prochain
   - ratio haut → maïs cher → incitation à planter maïs → pression supply future
   Signal : ratio extrême → reversement probable ?
   Liens EMA : substitution fourrage EU maïs vs soja

2. Maïs / Blé (CBOT et EMA)
   ratio_us = ZC/ZW
   ratio_eu = EMA/EWA (Euronext blé)
   Interprétation :
   - ratio_eu bas → blé EU moins cher → éleveurs EU préfèrent blé → demande maïs EU faible
   - ratio_eu haut → maïs EU trop cher → arbitrage vers blé ou soja

3. Maïs / Pétrole (éthanol parity)
   ethanol_corn_parity = prix éthanol CBOT / (prix maïs × yield éthanol)
   Interprétation :
   - parity > 1 → éthanol rentable → demande maïs éthanol forte → soutien CBOT
   - parity < 1 → éthanol pas rentable → demande éthanol faible → pression baissière

4. Maïs / Engrais (production cost)
   urea_corn_ratio = prix urée / prix maïs
   Interprétation :
   - ratio élevé → marges agriculteurs EU compressées → risque de réduction surface

5. Maïs / Gaz naturel (énergie séchage)
   ttf_corn_ratio = TTF EUR/MWh / prix maïs EUR/t
   Interprétation :
   - TTF cher → coût séchage maïs EU élevé → pression sur prix net agriculteur EU
   - TTF très cher → réduction séchage → qualité maïs EU potentiellement dégradée

6. Maïs brésilien / maïs américain
   fob_brazil_vs_cbot = FOB Paranaguá - CBOT-converti
   Interprétation :
   - spread négatif → Brésil compétitif → pression sur CBOT et EMA
   - spread positif → Brésil cher → CBOT et EMA soutenu
```

Tests à réaliser :

```text
- Corrélation de chaque ratio avec le premium EMA/CBOT
- AUC en utilisant le ratio comme feature pour H40
- Lead-lag (le ratio prédit-il le premium à H5/H10/H20 ?)
- Event study : que se passe-t-il quand le ratio franchit un percentile extrême ?
```

---

### V7-18 — Causalité formelle

Objectif : tester rigoureusement les relations causales entre les variables et le premium EMA/CBOT.

Méthodes :

```text
1. Granger OOF strict
   - Ne pas utiliser Granger in-sample (résultats déjà invalidés)
   - Protocole : walk-forward, p-value minimale sur le fold test
   - Variables à tester dans les deux sens :
     * fedfunds → premium (lien macro/change)
     * wasde_surprise → premium
     * basis_zscore → premium H40 (auto-causalité basis)
     * cot_net_noncomm → premium
     * ttf → premium
     * ukraine_export → premium
     * ec_mars → premium

2. PCMCI (Peter-Clark Momentary Conditional Independence)
   - Adapté aux séries temporelles avec auto-corrélation
   - Détecte la causalité conditionnelle (en contrôlant les autres variables)
   - Nécessite la librairie Tigramite (Python)
   - Permet de construire un graphe de causalité temporelle

3. Variables instrumentales (IV)
   - Pour tester si WASDE surprises causent le premium :
     * Instrument : date publication WASDE (exogène au premium)
     * First stage : WASDE_surprise ~ f(date_WASDE)
     * Second stage : premium ~ f(WASDE_surprise_prédit)
   - Élimine le biais d'endogénéité

4. Régression par discontinuité (RDD)
   - Si on peut identifier un seuil naturel :
     * basis > 2σ vs basis < 2σ
     * Traitement : signal premium
     * Outcome : rendement H40 EMA vs CBOT
   - Test causal au seuil
```

---

### V7-19 — Détection de ruptures structurelles

Objectif : identifier formellement si les paramètres du modèle ont changé après certains événements.

Événements candidats :

```text
2010-2011 : crise alimentaire mondiale (prix très hauts)
2012 : sécheresse US majeure (CBOT +60% en quelques semaines)
2014 : chute des prix (offre mondiale excédentaire)
2020 : COVID-19 (disruption demande/logistique)
2022 : invasion Ukraine (choc supply ukrainien)
2023 : sortie crédits agricoles US (changement demande)
2024 : record production US + Brazil (offre pléthorique)
```

Tests statistiques :

```text
1. Test de Chow (structural break à date connue)
   - H0 : les paramètres sont identiques avant et après la date
   - Appliqué à : régression EMA ~ f(CBOT, basis, EURUSD)
   - Pour chaque date candidate

2. CUSUM test (cumulative sum of recursive residuals)
   - Détecte si les résidus s'accumulent anormalement
   - Visuel + test de significativité

3. Bai-Perron test (multiple structural breaks, dates inconnues)
   - Détecte automatiquement le nombre optimal de breaks
   - Donne les dates estimées de changement de régime

4. Zivot-Andrews unit root test with structural break
   - Test racine unitaire en permettant un break endogène

5. Rolling AUC du modèle
   - AUC calculé sur une fenêtre glissante de 1 an
   - Visualise quand le modèle devient plus ou moins fort
   - Identifie les périodes de changement de régime
```

Impact sur les conclusions :

```text
Si rupture en 2022 confirmée :
  → Les résultats pré-2022 et post-2022 doivent être séparés
  → Le modèle "global" est peut-être un mélange de deux régimes différents
  → L'AUC global surestimé si le signal était meilleur avant la crise ?

Si pas de rupture majeure :
  → Confirmation de la robustesse du signal dans le temps
  → Signal plus crédible pour l'avenir
```

---

### V7-20 — Modèles espace-état dynamiques

Objectif : exploiter des modèles capables de s'adapter aux non-stationnarités.

Modèles à tester :

```text
1. Kalman Filter classique
   - State = [bêta_cbot, bêta_basis, bêta_eurusd]
   - Observation = EMA return
   - Q = bruit système (variance des changements de bêta)
   - R = bruit observation
   - Sortie : bêtas variant dans le temps + intervalles de confiance

2. Kalman Filter avec contrôle
   - Inputs exogènes (WASDE, weather event) comme vecteur de contrôle

3. Unscented Kalman Filter (UKF)
   - Pour les non-linéarités dans la relation EMA/CBOT

4. Particle Filter (Sequential Monte Carlo)
   - Pour les distributions non gaussiennes
   - Permet de capturer des régimes multimodaux

5. DLM (Dynamic Linear Model) Bayésien
   - Priors sur les bêtas
   - Posterior updating à chaque observation
   - Intervalles de crédibilité

6. Prophet (Facebook)
   - Pour décomposition tendance + saisonnalité + chocs
   - Appliqué au basis et aux returns relatifs
```

Utilisation prédictive :

```text
- Les bêtas estimés par Kalman sont des features pour le meta-model
  * beta_cbot_current (transmission CBOT→EMA courante)
  * beta_eurusd_current (sensibilité au change)
  * beta_basis_current (mean-reversion speed courante)
  * kalman_residual (résidu non expliqué par le modèle linéaire)
- Ces features sont naturellement anti-leakage (calculées à t-1)
```

---

### V7-21 — Analyse facteur EUR/USD et régimes de change

Objectif : comprendre l'impact du taux de change sur le basis et le premium.

Contexte : EMA est coté en EUR, CBOT en USD. Le taux EUR/USD est donc un facteur central. Mais ce n'est pas une simple conversion : le change affecte aussi la compétitivité des exportations US vs EU, et les décisions d'importateurs.

Variables EUR/USD à construire :

```text
eurusd_level : niveau courant
eurusd_zscore_52w : z-score sur 52 semaines
eurusd_trend : momentum 20j vs 60j
eurusd_vol : volatilité 10j
eurusd_regime : appréciation / dépréciation / stable
eurusd_carry_signal : différentiel taux court terme USD-EUR
eurusd_rsi : indicateur technique
eurusd_breakout : rupture de range 52 semaines
```

Hypothèses à tester :

```text
H_EUR1 : EUR fort → importateurs US achètent plus EU → basis monte ?
H_EUR2 : EUR fort → exportateurs EU moins compétitifs → prix EMA baisse ?
H_EUR3 : Le signal premium H40 est plus fort quand EUR/USD est stable ?
H_EUR4 : En période d'appréciation USD rapide, le basis se comprime ?
H_EUR5 : La sensibilité CBOT→EMA (bêta) dépend du régime EUR/USD ?
```

Tests :

```text
- Corrélation croisée basis ~ eurusd (différents lags)
- AUC premium conditionnel au régime EUR/USD
- Modèle avec interaction: basis_zscore × eurusd_regime
- Event study autour des chocs EUR/USD > 1.5%/jour
- Rolling regression: β_eurusd dans le modèle EMA sur 120j
```

---

### V7-22 — Analyse logistique et prix de parité

Objectif : construire et tester des indicateurs de parité économique réelle.

Indicateurs de parité à construire :

```text
1. Parité FOB Ukraine → EMA (prix d'importation équilibré)
   import_parity_ukraine = FOB_Ukraine_EUR + fret_ARA + quality_premium
   basis_vs_import_parity = basis - (import_parity_ukraine - CBOT_EUR)
   Lecture : positif → EMA plus cher que l'import ukrainien → pression baissière EMA

2. Parité FOB Brésil → EMA
   import_parity_brazil = FOB_Brazil_EUR + fret_ARA + phyto_premium
   Lecture : similaire Ukraine mais Brésil uniquement disponible saison 2 (mars-août)

3. Parité export EU → monde
   export_parity_eu = EMA - fret_ARA_monde - marges_export
   Lecture : si export_parity_eu > FOB_monde → EU peut exporter → pression haussière EMA ?

4. Coût de production EU (break-even)
   breakeven_eu = coût_semences + coût_engrais + coût_mécanique + coût_foncier
   Lecture : si EMA < breakeven → pression politique (aides, quotas) ?

5. Cash-and-carry (base nette)
   carry_3m = EMA_nov - EMA_front - coût_stockage_3m - coût_financement_3m
   Lecture : positif → incentive à stocker ; négatif → vendre maintenant
```

Tests :

```text
- Corrélation de chaque parité avec le basis
- AUC en utilisant la parité comme feature pour H40
- Event study : quand la parité change de signe, que se passe-t-il en H20 ?
- Régression OLS : basis ~ f(parité_ukraine, parité_brazil) — quelles proportions ?
- Test de stationnarité de (basis - import_parity_ukraine) → co-mouvement stable ?
```

---

### V7-23 — Analyse textuelle WASDE et rapports officiels

Objectif : extraire du signal supplémentaire des textes officiels.

Sources textuelles :

```text
1. WASDE report commentary (USDA)
   - Paragraphe maïs world supply/use
   - Révision commentée
   Source : USDA (PDF monthly)

2. FranceAgriMer rapport mensuel maïs
   - Bilan offre/demande France
   - Commentaire sur récolte et prix
   Source : FranceAgriMer (PDF mensuel)

3. EC MARS Bulletin
   - Commentaire sur rendements EU
   - Alertes météo
   Source : JRC (PDF mensuel)

4. IGC Grain Market Report
   - Synthèse mondiale maïs
   - Révisions prix et bilans
   Source : IGC (bi-mensuel)
```

Méthodes NLP :

```text
1. Sentiment polarity
   - Positif/négatif sur le paragraphe maïs
   - Outil : VADER (adapté finance) ou FinBERT (adapté finance)
   - Feature : sentiment_score [-1, +1]

2. Détection des mots-clés économiques
   - "raised", "lowered", "revised upward" → signal de révision
   - "tightening" / "loosening" (bilans stocks)
   - "drought" / "flooding" / "stress"
   - Compter fréquence et pondérer

3. Topic modelling (LDA)
   - Extraire les topics dominants dans chaque rapport
   - Identifier si le topic dominant est supply EU ou demand US ou prix

4. Change detection textuelle
   - Quel est le changement de langage rapport à rapport ?
   - Nouveau "mot-clé alerte" apparu vs absent le mois précédent

Feature engineering :

  wasde_text_sentiment_score
  wasde_text_revision_direction  (+1/-1/0)
  wasde_text_eu_focus_score  (proportion EU vs monde)
  mars_text_yield_alarm  (mention de stress rendement)
  mars_text_positive_revision  (révision à la hausse explicite)
```

Validation :

```text
- AUC des features textuelles seules sur target premium H40
- Delta AUC ajouté aux features classiques
- Robustesse : signal in-sample vs OOF walk-forward
- Comparaison vs signal quantitatif seul (wasde_surprise numérique)
```

---

### V7-24 — Signaux options et volatilité implicite

Objectif : extraire du signal des options sur futures maïs CBOT (et EMA si disponible).

Contexte : les marchés d'options reflètent les anticipations des participants professionnels. La volatilité implicite (IV) et le skew portent de l'information sur la distribution attendue des prix futurs.

Variables à construire (CBOT options, si données disponibles) :

```text
iv_atm_30d : volatilité implicite at-the-money 30 jours
iv_atm_60d : vol implicite 60 jours
iv_atm_90d : vol implicite 90 jours
iv_skew_25d = IV_put_25delta - IV_call_25delta  (skew puts vs calls)
iv_term_spread = IV_60d - IV_30d  (pente de la surface)
iv_vs_realized = IV_30d - realized_vol_30d  (prime de risque volatilité)
put_call_ratio : volume puts / volume calls (sentiment)
iv_rank = percentile(iv_atm, 252j)  (IV relative à son historique)
iv_percentile = percentile(iv_atm, 52w)
vol_of_vol : volatilité de IV (incertitude sur l'incertitude)
```

Hypothèses :

```text
H_OPT1 : IV élevé → incertitude → signal premium moins fiable
H_OPT2 : Skew très négatif (puts chers) → marché craint une chute → basis baisse ?
H_OPT3 : IV_term_spread négatif (contango implicite inversé) → choc à court terme attendu
H_OPT4 : iv_rank > 80% → période de stress → filtrer signaux premium
H_OPT5 : put_call_ratio > 2 → sentiment très négatif → potentiel rebond (contrarian)
```

Tests :

```text
- Corrélation croisée IV ~ basis (lags 1-20 jours)
- AUC des features options sur target premium H20/H40
- Interaction : IV × basis_zscore comme feature composite
- Event study : que se passe-t-il sur EMA premium quand IV spike > +50% en une semaine ?
```

---

### V7-25 — Tests des anomalies de marché

Objectif : tester formellement les anomalies connues de la littérature académique sur les commodités.

Anomalies à tester (literature review) :

```text
1. Momentum (Gorton, Hayashi, Rouwenhorst 2013)
   - Le retour passé 12-1 mois prédit la direction ?
   - Hypothèse : momentum existe dans les commodités
   - Test : régression retour h40 ~ f(retour passé -3m, -6m, -12m)

2. Mean reversion à long terme (Bessembinder et al. 1995)
   - Existe-t-il une mean reversion à 6-12 mois ?
   - Test : ADF test sur rendements cumulés à différents horizons

3. Basis momentum (Koijen et al. 2018)
   - Signe du basis prédit-il la direction du spot ?
   - Hypothèse : basis positif → convenience yield → spot tend à monter
   - Test : AUC basis_sign → cbot_direction_h20

4. Seasonal return patterns
   - Rendements saisonniers en maïs (Bodie & Rosansky 1980)
   - Hypothèse : mois de récolte → rendement négatif ?
   - Test : rendement moyen CBOT et EMA par mois et semaine

5. WASDE announcement premium
   - Les jours WASDE ont-ils des rendements anormaux ?
   - Hypothèse : annonce WASDE → saut de volatilité
   - Test : t-test rendement abs le jour WASDE vs autres jours

6. Weather effect (Roll 1984)
   - La météo US prédit le prix du maïs
   - Test : AUC weather_stress → cbot_direction_h20

7. Financialization (Tang & Xiong 2012)
   - Depuis 2008, les marchés des commodités sont plus corrélés aux marchés financiers
   - Test : rolling correlation CBOT ~ SP500 avant vs après 2008
   - Test : impact COT index traders sur signal

8. Convenience yield mean reversion (Working 1949)
   - Convenience yield = spot - futures ajusté
   - Test : convenience yield est-il mean-reverting ?
   - Test : convenience yield extrême prédit-il la direction ?
```

---

### V7-26 — Analyse de mémoire longue et persistance

Objectif : tester si les series de prix et de basis ont une mémoire longue.

Tests :

```text
1. Exposant de Hurst (H)
   - H = 0.5 → marche aléatoire (marché efficient)
   - H > 0.5 → persistance (tendance se prolonge)
   - H < 0.5 → anti-persistance (mean reversion)
   - Appliqué à : prix CBOT, prix EMA, basis, premium H40/H90
   - Méthode : R/S analysis, DFA (Detrended Fluctuation Analysis)

2. ARFIMA (AutoRegressive Fractionally Integrated Moving Average)
   - Extension de ARIMA avec différenciation fractionnaire d
   - d = 0 → pas de mémoire longue
   - d > 0 → mémoire longue (shocks persistent)
   - d < 0 → anti-persistance
   - Appliqué au basis : d > 0 → basis met très longtemps à mean-reverted

3. Tests de racine unitaire saisonnière
   - HEGY test (Hylleberg, Engle, Granger, Yoo)
   - Teste s'il y a une racine unitaire à fréquence saisonnière

4. Autocorrélation à longs lags
   - ACF plot jusqu'à 520 lags (2 ans de données)
   - Partielle PACF pour identifier l'ordre AR

5. Spectral analysis
   - Densité spectrale du basis et du premium
   - Identifier les fréquences dominantes (saisonnalité)
   - Ondelettes (wavelet analysis) pour analyse multi-échelle
```

Implications pour la modélisation :

```text
- Si H > 0.55 pour le premium H40 : utiliser des modèles avec mémoire longue
- Si basis a d > 0 : le demi-vie réel est plus long que les 22j estimés par AR(1)
- Si saisonnalité unitaire : ajouter des termes saisonniers explicites aux modèles
```

---

### V7-27 — Modèles multi-facteurs conditionnels

Objectif : construire le modèle le plus complet possible en intégrant tous les drivers validés.

Architecture du modèle final conditionnel :

```text
Niveau 0 — Experts atomiques (OOF chacun) :
  E1: signal_cbot_direction_h40
  E2: signal_cbot_drawdown_h20
  E3: signal_ema_premium_h40
  E4: signal_ema_premium_h90
  E5: signal_basis_regime
  E6: signal_seasonal_expert
  E7: signal_roll_risk
  E8: signal_eu_weather
  E9: signal_wasde_event
  E10: signal_p_correct

Niveau 1 — Meta-features de niveau 1 (combinaisons OOF) :
  M1: accord_h40_h90
  M2: accord_cbot_ema
  M3: entropie_signaux
  M4: confiance_max
  M5: n_modeles_bullish
  M6: basis_extreme × accord_signaux  (interaction)
  M7: saison × confiance  (interaction)

Niveau 2 — Meta-modèle final (entraîné sur M + E, OOF strict) :
  Features : E1..E10 + M1..M7 + features classiques shift(1)
  Modèle : LogReg (interprétable) + HistGB (performance)
  Cible : y_rel_outperform_h40 ou y_rel_outperform_h90

Niveau 3 — P(correct) wrapper :
  Features : prob_meta_level2 + context_features
  Cible : correct OOF
  Sortie : signal_final avec confiance calibrée
```

Évaluation :

```text
- Comparer chaque niveau vs niveau précédent
- Toujours: AUC, balanced accuracy, top20 DA, ECE
- Stabilité par année (12-15 ans)
- Robustesse aux crises (LOO-crisis-out)
- Performance brute vs avec abstention (top20/top30/top40)
```

---

### V7-28 — Architecture finale de l'indicateur

Objectif : transformer les meilleurs signaux en un indicateur final professionnel.

L'indicateur ne sera pas une boîte noire IA. Ce sera un indicateur hybride transparent.

#### Couche 1 — Moteur mondial CBOT

```text
Signal : pred_cbot_direction_h40
Drivers : WASDE stocks, weather US, COT, ethanol parity, Brazil pace
Output : CBOT_SIGNAL = {BULLISH, NEUTRAL, BEARISH}
Confiance : calibrée [0, 1]
```

#### Couche 2 — Prime européenne EMA/CBOT

```text
Signal : pred_ema_premium_h40 ou h90
Drivers : basis_zscore, saison, OI_EMA, weather_EU, MARS, FranceAgriMer
Output : PREMIUM_SIGNAL = {HIGH_PREMIUM → EMA_UNDERPERFORM, 
                            LOW_PREMIUM → EMA_OUTPERFORM,
                            NEUTRAL}
Confiance : calibrée [0, 1]
```

#### Couche 3 — Contexte et filtres

```text
Filtres de veto (signal = ABSTAIN si) :
  - roll_risk > 0.7 (trop proche du roll)
  - data_quality < 0.35 (données insuffisantes)
  - volatilité > 2.5σ (marché en stress incontrôlé)
  - P(correct) < 0.40

Filtres de boost (confiance × 1.2 si) :
  - basis_extreme = True ET saison = harvest_eu
  - accord h40-h90 = True
  - P(correct) > 0.65
```

#### Couche 4 — Signal final

```text
Signal final (journalier, donné le vendredi soir) :

EMA_EXPECTED_TO_OUTPERFORM_CBOT
  → Conditions : PREMIUM_SIGNAL=LOW, P(correct)≥0.45, pas de filtre veto
  → Confiance : LOW / MEDIUM / HIGH

EMA_EXPECTED_TO_UNDERPERFORM_CBOT
  → Conditions : PREMIUM_SIGNAL=HIGH, P(correct)≥0.45, pas de filtre veto
  → Confiance : LOW / MEDIUM / HIGH

UNCERTAIN
  → Toutes les autres situations
```

#### Couche 5 — Explicabilité

```text
Pour chaque signal :
  - top 3 drivers (SHAP values)
  - basis_zscore courant
  - saison courante
  - régime basis courant
  - P(correct) courant
  - jours avant prochain WASDE/MARS
  - contexte économique bref (texte narratif)
```

---

### V7-29 — Multiple testing et discipline statistique

Objectif : éviter de confondre vraie découverte et hasard après des centaines de tests.

Contexte : le programme V7 teste plusieurs dizaines de cibles, horizons, filtres, modèles et saisons. À ce niveau de multiplicité, des résultats positifs apparaissent par pur hasard. La discipline statistique est non négociable.

À faire :

```text
1. Compter toutes les comparaisons effectuées dans V7
   - nombre de cibles × horizons × modèles × filtres
   - documenter dans un registre exhaustif

2. Appliquer la correction Benjamini-Hochberg (FDR)
   - Sur toutes les p-values ou IC95 AUC de l'ensemble des expériences
   - q_BH < 0.05 pour signal GO
   - Ajouter colonne selection_adjusted dans tous les résultats

3. Créer un holdout final gelé
   - Période : 2024 entier (données récentes non vues pendant l'exploration)
   - Ce holdout ne doit être utilisé QU'UNE SEULE FOIS
   - Aucun réglage de modèle après avoir vu le holdout

4. Interdire la sélection post-hoc
   - Le modèle final ne peut pas être choisi sur le set d'exploration
   - Si un modèle est testé sur 2010-2023, le rapport final doit le distinguer de
     l'évaluation sur le holdout 2024

5. Rapporter TOUTES les expériences
   - Y compris les négatives
   - Y compris les expériences abandonnées
   - Y compris les expériences avec n trop faible
```

Critère obligatoire :

```text
Tout signal principal doit survivre à la correction FDR
ou être explicitement marqué EXPLORATORY_ONLY dans le rapport.

Un signal EXPLORATORY_ONLY ne peut pas devenir un signal d'indicateur.
```

Livrables :

```text
artefacts/v7/multiple_testing_report.json
docs/MULTIPLE_TESTING_CONTROL.md
```

---

### V7-30 — Red team validation des meilleurs résultats

Objectif : attaquer volontairement les résultats trop bons pour comprendre leur origine.

Contexte : les résultats meta-model H90 (AUC 0.937), basis_extreme (AUC 0.968), seasonal_expert (AUC 0.982) sont très élevés. Ils peuvent être réels, mais ils peuvent aussi être gonflés par des artefacts. Il faut les attaquer systématiquement.

Cibles de la red team :

```text
meta-model H90 (classic_plus_meta, n=503, AUC 0.937)
basis_extreme_h90 (AUC 0.968, n=29)
basis_extreme_h40 (AUC 0.968, n=91)
seasonal_expert/top20_train_only (n=68, AUC 0.982)
backtest seasonal/top40_no_roll (9 trades, PF=100)
cross-target stacking (OOF factory)
```

Tests à réaliser pour chaque cible :

```text
Test 1 — Shuffle labels temporel
  Mélanger les labels y en gardant les features à la même date
  → Si AUC reste élevé = leakage ou feature colinéaire au label
  → Si AUC chute vers 0.50 = signal réel

Test 2 — Permutation des meta-features
  Permuter aléatoirement les colonnes OOF auxiliaires (décaler de 1 an)
  → Si AUC ne chute pas beaucoup = les meta-features ne servent pas vraiment

Test 3 — Décalage temporel des prédictions OOF
  Décaler les prédictions OOF de +H jours vers le futur
  → Simule un leakage artificiel
  → Comparer avec AUC sans décalage

Test 4 — Embargo 2H
  Embargo de 2×H jours au lieu de H jours
  → Si AUC chute fortement = chevauchement de labels responsable

Test 5 — Non-overlap strict
  Ne garder qu'une observation par fenêtre de H jours
  → Si AUC chute > 0.10 = chevauchement gonflait les résultats

Test 6 — Retrait des crises
  Exclure 2020 et 2022 entiers
  → Si AUC chute > 0.10 = signal dépendant des crises

Test 7 — Retrait des 10 meilleurs trades
  Retirer les 10 meilleures observations du test
  → Mesure la fragilité vis-à-vis des outliers positifs

Test 8 — Suppression features basis
  Modèle sans aucune feature basis (ni basis_level, ni basis_zscore)
  → Si AUC reste > 0.80 = signal non basique → suspect ou très robuste

Test 9 — Suppression features saison
  Modèle sans aucun indicateur saisonnier
  → Si AUC chute > 0.15 = overfitting saison spécifique

Test 10 — Période récente uniquement
  Évaluation seulement sur 2021-2023 (données proxy récentes)
  → Si AUC chute fortement = signal pas dans les données récentes

Test 11 — Proxy vs officiel
  Évaluation seulement sur la sous-période officielle Euronext
  → Si AUC chute > 0.10 = signal porté par le proxy
```

Verdict possible pour chaque résultat :

```text
ROBUST           : AUC stable sur au moins 8/11 tests
PROMISING_BUT_FRAGILE : AUC stable sur 5-7/11 tests
LIKELY_SELECTION_BIAS : AUC chute > 0.15 sur 4+ tests
LEAKAGE_SUSPECTED    : AUC stable sur label shuffled (Test 1)
```

Livrables :

```text
artefacts/v7/red_team_validation.json
docs/RED_TEAM_VALIDATION.md
```

---

### V7-31 — Benchmark naïf et professionnel

Objectif : comparer tous les modèles ML à des règles simples économiquement fondées.

Contexte : la vraie mesure d'utilité d'un modèle ML n'est pas de battre le hasard — c'est de battre les règles simples que n'importe quel trader professionnel applique. Un modèle qui ne bat pas la règle basis z-score n'apporte rien.

Baselines à implémenter :

```text
Baseline 1 — Random walk
  Prédiction aléatoire uniforme [0.5, 0.5]
  AUC attendu ≈ 0.50

Baseline 2 — Seasonal month rule
  Prédiction = 1 si mois dans (sep, oct, nov)
  Prédiction = 0 sinon
  AUC attendu ≈ 0.55-0.60

Baseline 3 — Basis z-score rule
  Prédiction = 1 si basis_zscore < -1 (EMA sous-évalué → outperform prévu)
  Prédiction = 0 si basis_zscore > +1 (EMA sur-évalué → underperform prévu)
  C'est la règle simple la plus forte identifiée dans FIX-EMA-06
  AUC attendu ≈ 0.65-0.70

Baseline 4 — Moving average EMA/CBOT spread
  Prédiction = 1 si spread(10j) < spread(60j)  (spread comprime → EMA va rattraper)
  Prédiction = 0 sinon

Baseline 5 — AR(1) basis
  Prédiction = 1 si AR(1) basis prédit une baisse du basis
  Prédiction = 0 sinon

Baseline 6 — Carry / futures curve rule
  Prédiction = 1 si EMA_harvest < EMA_front (backwardation → soutien EMA)
  Prédiction = 0 sinon

Baseline 7 — COT contrarian rule
  Prédiction = 1 si non-commerciaux net short très extrême (< percentile10)
  Prédiction = 0 si net long très extrême (> percentile90)

Baseline 8 — WASDE calendar rule
  Prédiction = 1 dans les 5j après WASDE bearish surprise
  Prédiction = 0 sinon

Baseline 9 — No-trade baseline
  Toujours UNCERTAIN → taux de succès = 50%
  Coût = 0 → PnL = 0

Baseline 10 — Always long EMA / short CBOT spread
  Toujours long EMA vs CBOT
  Performance = rendement moyen de la prime → baseline économique

Baseline 11 — Combinaison règles simples (ensemble)
  Basis z-score + saison + carry
  Poids égaux ou optimisés train-only
```

Critère de validation ML :

```text
Un modèle ML est réellement utile seulement s'il bat :
  - Baseline 3 (basis z-score rule)        → le plus important
  - Baseline 2 (seasonal rule)             → signal saisonnier robuste
  - Baseline 5 (AR(1) basis)               → signal statistique simple
  - Baseline 11 (combinaison règles)        → combinaison intelligente

Si le ML ne bat pas ces baselines :
  → L'indicateur final peut être une combinaison de règles économiques simples
  → Ce serait une conclusion tout aussi valide et professionnelle
```

Livrables :

```text
artefacts/v7/professional_benchmark.json
docs/PROFESSIONAL_BENCHMARK.md
```

---

### V7-32 — Fair value model EMA/CBOT

Objectif : construire une valeur théorique "fair value" d'Euronext basée sur les fondamentaux.

Contexte : au lieu de prédire la direction d'EMA, on prédit ce qu'EMA DEVRAIT valoir selon les fondamentaux, puis on étudie l'écart entre EMA réel et EMA juste. Cet écart est prévisiblement mean-reverting.

Modèle fair value :

```text
EMA_fair(t) = CBOT_EUR(t)
            + transport_adjustment(t)   (fret Golfe → ARA)
            + quality_premium           (constante ≈ 5-10 €/t)
            + EU_stock_tightness_premium(t)  (f(ending_stocks_eu / use_eu))
            + Ukraine_risk_premium(t)   (proxy : corridor_open/closed)
            + seasonality_premium(t)    (mois ∈ sep-nov → +x €/t)
            + EUR/USD_carry_component(t)

EMA_premium_vs_fair(t) = EMA_actual(t) - EMA_fair(t)
```

Calibration :

```text
- Estimer les coefficients par OLS sur train strict (2010-2018)
- Tester les coefficients sur 2019-2023
- Evaluer : EMA_premium_vs_fair est-il mean-reverting ?
  → ADF test sur EMA_actual - EMA_fair
  → Demi-vie de la correction
- Comparer : EMA_premium_vs_fair vs basis_zscore
  → Lequel mean-revert plus vite ?
  → Lequel prédit mieux H40 EMA outperform ?
```

Utilisation prédictive :

```text
Si EMA_actual >> EMA_fair :
  → EMA trop cher → signal EMA underperform CBOT
  → Analogue au basis_zscore mais fondé économiquement

Si EMA_actual << EMA_fair :
  → EMA trop bon marché → signal EMA outperform CBOT
```

Questions :

```text
- La fair value est-elle plus informative que le basis z-score seul ?
- Quelle composante est la plus importante (stocks, saisonnalité, fret) ?
- L'erreur de modèle fair value est-elle corrélée aux crises ?
- Le fair value model aide-t-il à distinguer crise réelle vs artefact proxy ?
```

Livrables :

```text
artefacts/v7/fair_value_ema_cbot.json
docs/FAIR_VALUE_MODEL.md
```

---

### V7-33 — Cartographie des drivers par horizon

Objectif : comprendre formellement quel driver agit à quel horizon et avec quel retard.

Contexte : les traders professionnels savent que le marché à J+5 est dominé par les événements, tandis que le marché à J+90 est dominé par les bilans fondamentaux. Cette cartographie doit être quantifiée.

Structure horizon × driver :

```text
Horizon très court H5-H10 :
  Drivers dominants attendus :
    - WASDE surprise (t=0 → effet J+5)
    - EUR/USD daily move
    - Événement Ukraine (corridor, conflit)
    - Liquidité EMA (OI très faible → volatilité accrue)
    - COT publication surtout si surprise
    - Météo US extreme jour-même
  Test : AUC de chaque feature seule sur y_rel_outperform_h5 et h10

Horizon moyen H20-H40 :
  Drivers dominants attendus :
    - basis_zscore (mean reversion)
    - COT positioning cumulé
    - Export sales US vs pace USDA
    - Weather stress EU et US sur 10-20j
    - Futures curve slope (carry)
    - Saison (début ou fin)
  Test : AUC de chaque feature sur y_rel_outperform_h20 et h40

Horizon long H60-H120 :
  Drivers dominants attendus :
    - Ending stocks EU (bilan annuel)
    - Crop progress EU (MARS harvest estimate)
    - Production mondiale USDA World Supply/Use
    - Ukraine export volume cumulé (saison)
    - Régime saisonnier (old crop / new crop)
    - FOB Ukraine vs EMA (parité d'importation)
  Test : AUC de chaque feature sur y_rel_outperform_h60 et h90
```

Livrables :

```text
artefacts/v7/driver_horizon_map.json  (matrice AUC driver × horizon)
docs/DRIVER_HORIZON_MAP.md
Visualisation : heatmap driver × horizon × AUC/SHAP
```

Questions :

```text
- Certains drivers ont-ils un retard optimal (lag) ?
  → Ex : WASDE actif H5 mais aussi H40 ?
- Les drivers EU sont-ils uniquement pertinents pour les horizons longs ?
- Le basis est-il utile à tous les horizons ou surtout H20-H60 ?
- Quels drivers "vieillissent vite" (signal court uniquement) ?
```

---

### V7-34 — Modèle de scénario de marché

Objectif : produire des scénarios de marché au lieu d'une simple direction.

Contexte : un indicateur professionnel ne dit pas seulement "hausse/baisse". Il explique DANS QUEL SCÉNARIO on se trouve, et ce que ce scénario implique historiquement pour EMA et CBOT.

Scénarios à définir et calibrer :

```text
Scénario 1 — GLOBAL_BULLISH_STABLE_EU_PREMIUM
  Conditions : pred_cbot_direction = BULLISH
               basis_zscore dans [-1, +1]  (prime normale)
  Comportement historique : EMA et CBOT montent ensemble

Scénario 2 — GLOBAL_BEARISH_COMPRESSED_EU_PREMIUM
  Conditions : pred_cbot_direction = BEARISH
               basis_zscore < -1  (prime faible)
  Comportement historique : les deux baissent, EMA moins que CBOT

Scénario 3 — GLOBAL_NEUTRAL_HIGH_EU_PREMIUM
  Conditions : pred_cbot_direction = NEUTRAL
               basis_zscore > +1.5  (prime élevée)
  Signal : EMA va mean-reverted → EMA UNDERPERFORM attendu
  C'est le signal le plus clair de l'étude

Scénario 4 — EU_LOCAL_SHOCK
  Conditions : residual_shock_flag = True
               (résidu EU élevé non expliqué par CBOT + change)
  Comportement : EMA bouge indépendamment de CBOT
  Signal : peu fiable → ABSTAIN ou signal EMA seul

Scénario 5 — US_GLOBAL_SHOCK
  Conditions : CBOT move > 3% journalier
               basis compression accélérée
  Comportement : EMA suit CBOT avec décalage 1-3j

Scénario 6 — ROLL_LIQUIDITY_DISTORTED
  Conditions : DTE < 20j OU OI très faible
  Comportement : basis peu fiable → signal unreliable
  Signal : ABSTAIN

Scénario 7 — SEASONAL_HARVEST_EU
  Conditions : mois in (sep, oct, nov)
               crop_progress_eu > 50%
  Comportement : pression saisonnière sur EMA
  Signal : EMA UNDERPERFORM probable si basis haut

Scénario 8 — NORMAL_NO_SIGNAL
  Aucun des scénarios ci-dessus actif
  Signal : UNCERTAIN
```

Classifier les scénarios :

```text
Méthode :
  1. Règles manuelles d'abord (interprétable)
  2. KMeans en second (valider que les clusters correspondent)
  3. Probabilité de chaque scénario par HistGB OOF (soft classification)

Sortie pour chaque date t :
  - scénario dominant (hard classification)
  - P(scénario) pour chaque scénario (soft)
  - comportement historique EMA/CBOT dans ce scénario
  - signal recommandé (outperform / underperform / abstain)
```

Livrables :

```text
artefacts/v7/market_scenario_classifier.json
docs/MARKET_SCENARIO_CLASSIFIER.md
```

---

### V7-35 — Distributional forecasting du premium

Objectif : prédire la distribution du premium, pas seulement la direction.

Contexte : savoir que EMA va outperformer CBOT est utile. Savoir de COMBIEN et avec quelle incertitude est encore plus utile pour la gestion du risque.

Cibles distributionnelles :

```text
Quantile regression targets :
  relative_return_h40 : quantile 10 / 25 / 50 / 75 / 90
  relative_return_h90 : quantile 10 / 25 / 50 / 75 / 90
  basis_change_h40 : quantile 10 / 25 / 50 / 75 / 90

Probabilités de grands mouvements :
  P(relative_return_h40 > +2%)
  P(relative_return_h40 > +3%)
  P(relative_return_h40 > +5%)
  P(relative_return_h40 < -2%)
  P(relative_return_h40 < -3%)

Risque de queue :
  expected_shortfall_5pct  (moyenne des 5% pires outcomes)
  conditional_value_at_risk
```

Méthodes :

```text
1. Quantile regression (sklearn LinearQuantileRegression)
   - Rapide, interprétable
   - Baselines des quantiles

2. Conformalized quantile regression (CQR)
   - Coverage garanti
   - Déjà utilisé dans l'étude (walk_forward_cqr)
   - Appliquer au premium relatif

3. NGBoost (Natural Gradient Boosting)
   - Modèle probabiliste qui apprend la distribution complète
   - Output : P(y ≤ q) pour tout q

4. Distributional random forest
   - Chaque feuille contient la distribution empirique
   - Output : distribution entière, pas seulement un quantile

5. Normalizing flows (avancé)
   - Si NGBoost insuffisant
   - Apprend la transformation vers une distribution normale
```

Validation :

```text
Coverage empirique vs coverage nominal
  → Q90 doit couvrir 90% des observations
Winkler score (pénalise la largeur des intervalles)
  → Intervalles pas trop larges
Reliability diagram par quantile
  → Calibration visuelle
```

Utilisation dans l'indicateur :

```text
Signal = direction + magnitude + incertitude

Exemple de sortie :
  EMA expected to OUTPERFORM CBOT H40
  Médiane : +2.3 EUR/t
  Intervalle 80% : [+0.5, +5.1] EUR/t
  Probabilité de mouvement > 3% : 38%
  Risque : P(underperform > 2%) = 12%
```

Livrables :

```text
artefacts/v7/distributional_forecast_premium.json
docs/DISTRIBUTIONAL_FORECAST.md
```

---

### V7-36 — Graphe de causalité économique

Objectif : construire une carte formelle des relations causales entre variables du marché du maïs.

Contexte : les tests de Granger OOF donnent des p-values. Les graphes de causalité donnent une vue d'ensemble des dépendances conditionnelles entre toutes les variables simultanément.

Noeuds du graphe :

```text
Variables prix :
  CBOT_price
  EMA_front_price
  EMA_basis
  EUR_USD
  TTF_gas

Variables fondamentaux US :
  WASDE_ending_stocks_world
  WASDE_us_supply_use
  NASS_crop_progress
  drought_monitor_us
  COT_net_noncomm

Variables fondamentaux EU :
  WASDE_eu_supply_use
  EC_MARS_yield_revision
  FranceAgriMer_bilan
  OI_EMA (liquidité)
  weather_eu_heat_stress
  weather_eu_rain_deficit

Variables logistiques :
  FOB_Ukraine
  FOB_Brazil
  Baltic_Dry_Index
  Ukraine_export_corridor

Variables macro :
  fedfunds_rate
  EUR_USD_carry
  SP500_return
  VIX
```

Méthodes :

```text
1. Granger OOF (déjà commencé)
   - Résultats par paire de variables
   - Ne contrôle pas les autres variables

2. PCMCI (Peter-Clark Momentary Conditional Independence)
   - Test de causalité conditionnelle temporelle
   - Contrôle les autres variables (pas de fausse causalité)
   - Requiert Tigramite (pip install tigramite)
   - Protocole :
     * Lag max = 20 jours
     * Alpha = 0.05
     * MCI test

3. PC algorithm (constraint-based causal discovery)
   - Structure skeleton puis orientation des flèches
   - Skeleton : tests d'indépendance conditionnelle
   - Orientation : V-structures + Meek rules

4. Bayesian network (score-based)
   - BIC score pour comparer structures
   - Bootstrap pour identifier liens robustes
```

Interprétation attendue :

```text
Liens forts attendus :
  CBOT → EMA (contemporain et lead 1-3j)
  WASDE → CBOT (lag 0-1j après publication)
  basis → EMA outperform H40 (lag 1-5j)
  weather_eu_stress → EMA_basis (lag 5-20j)

Liens suspects (à tester) :
  fedfunds → basis (pas de mécanisme direct clair)
  EMA → CBOT (Granger OOF non confirmé)
  BDI → EMA (logistique → coût import)

Liens impossibles (doivent être rejetés) :
  futur → passé (vérification anti-leakage)
  CBOT → fedfunds (reverse causality impossible)
```

Livrables :

```text
artefacts/v7/causal_graph_corn.json
docs/CAUSAL_GRAPH_CORN.md
Visualisation : graphe orienté avec forces des liens
```

---

### V7-37 — Analyse de stabilité des features

Objectif : identifier les features réellement robustes dans le temps vs les features opportunistes.

Contexte : une feature peut être très importante pour 2012 mais nulle pour 2020. Ces features opportunistes gonflent les résultats in-sample mais sont inutiles hors de la période spécifique.

Protocole :

```text
Pour chaque feature dans les top-30 SHAP :

1. SHAP importance par année
   - Entraîner le modèle sur les N-1 années, calculer SHAP sur l'année N
   - Répéter pour chaque année 2014-2023
   - Résultat : matrice SHAP_importance[feature, year]

2. Permutation importance par année
   - Même protocole que SHAP mais avec permutation de la feature
   - delta AUC si feature permutée, par année

3. Rank stability
   - Rang de la feature dans le classement d'importance par année
   - Kendall tau des rangs inter-années

4. Top features par saison
   - Même analyse mais par saison (jan-mar / apr-jun / jul-aug / sep-nov / dec)

5. Top features en crise vs hors crise
   - Features importantes en 2020-2022 vs 2014-2019
```

Classification des features :

```text
STABLE_ROBUST :
  - Importance élevée dans ≥ 8/10 années
  - Rang dans top 20 sur ≥ 60% des années
  - Kendall tau rang inter-années > 0.5

SEASONAL_ROBUST :
  - Importance élevée dans ≥ 3/5 saisons
  - Stable dans sa saison de référence
  - Utile mais limité dans le temps

CRISIS_SPECIFIC :
  - Importance élevée uniquement 2020-2022
  - Nulle ou faible hors crise
  - Marquer dans le rapport : ne pas surpondérer

OPPORTUNISTIC :
  - Importante dans < 4/10 années
  - Rang instable (Kendall tau < 0.3)
  - Exclure du modèle de production

SPURIOUS :
  - Corrélation élevée mais pas de sens économique
  - Importance chute si shuffle partiel
  - Exclure immédiatement
```

Livrables :

```text
artefacts/v7/feature_stability_report.json
docs/FEATURE_STABILITY.md
```

---

### V7-38 — Étude du model decay

Objectif : mesurer combien de temps un modèle entraîné reste valable sans réentraînement.

Contexte : dans un marché qui change, un modèle entraîné en 2015 peut être obsolète en 2020. Il faut savoir à quelle fréquence réentraîner et quelles features vieillissent le plus vite.

Protocole :

```text
Séquence d'évaluation expanding window :

Pour chaque année de test Y de 2016 à 2023 :
  Pour chaque âge du modèle A = 1, 2, 3, 4, 5 ans :
    Entraîner sur 2010 à Y-A
    Évaluer sur Y
    Calculer AUC, balanced accuracy, top20 DA

Résultat :
  Matrice AUC[age_du_modèle, année_de_test]
  Courbe de dégradation : AUC en fonction de l'âge
```

Questions :

```text
1. À quel âge l'AUC chute-t-elle de façon significative (> 0.05) ?
   → Ça donne la fréquence minimale de réentraînement

2. Certaines années de test voient plus de dégradation que d'autres ?
   → Crise 2022 → le modèle pré-2022 est-il particulièrement mauvais ?

3. Quelles features vieillissent le plus vite ?
   → Calculer le rang SHAP par âge du modèle

4. La recalibration (seuils seulement) suffit-elle ?
   → Tester réentraînement complet vs recalibration seuils seulement

5. Le rolling retraining améliore-t-il vs expanding ?
   → Comparer fenêtre 5 ans glissante vs expanding
```

Recommandation attendue :

```text
Fréquence de réentraînement recommandée :
  Si decay < 0.02 par an → annuel OK
  Si decay 0.02-0.05 par an → trimestriel
  Si decay > 0.05 par an → mensuel nécessaire
```

Livrables :

```text
artefacts/v7/model_decay_study.json
docs/MODEL_DECAY_STUDY.md
```

---

### V7-39 — Indicateur de qualité des données

Objectif : intégrer formellement la fiabilité des données dans la confiance du signal.

Contexte : le signal EMA varie fortement selon que les données sont officielles, proxy ou manquantes. Il faut quantifier cette incertitude dans le signal final.

Score de qualité des données (calculé à chaque date t) :

```text
data_quality_score(t) =
  w1 × coverage_score(t)        (proportion de features non-NaN)
+ w2 × official_source_score(t) (proportion de features source officielle)
+ w3 × no_proxy_ema_score(t)    (1 si EMA non proxy, 0 sinon)
+ w4 × no_missing_key_score(t)  (1 si WASDE + MARS + EMA tous présents)
+ w5 × liquidity_score(t)       (OI_EMA > median → score 1.0, sinon linéaire)
+ w6 × low_roll_risk_score(t)   (1 - roll_risk_score)

Poids : w1=0.20, w2=0.20, w3=0.25, w4=0.15, w5=0.10, w6=0.10
```

Utilisation dans le modèle :

```text
1. Feature pour P(correct)
   → data_quality_score comme feature de méta-apprentissage

2. Filtre d'abstention
   → Signal = UNCERTAIN si data_quality_score < 0.35

3. Coefficient de confiance
   → confidence_final = confidence_model × (0.5 + 0.5 × data_quality_score)

4. Annotation du rapport
   → Afficher data_quality_score dans chaque signal
   → Distinguer : signal fort + data haute qualité vs signal fort + data proxy
```

Classification des périodes :

```text
HIGH_QUALITY    : data_quality_score ≥ 0.75
MEDIUM_QUALITY  : 0.50 ≤ score < 0.75
LOW_QUALITY     : 0.35 ≤ score < 0.50
ABSTAIN_QUALITY : score < 0.35
```

Livrables :

```text
src/mais/research/data_quality_score.py
artefacts/v7/data_quality_score_history.parquet
docs/DATA_QUALITY_SCORE.md
```

---

### V7-40 — Étude des unknown unknowns

Objectif : documenter et analyser les erreurs du modèle qui ne sont expliquées par aucun facteur connu.

Contexte : les erreurs tagguées UNKNOWN dans l'analyse V7-14 sont particulièrement importantes. Elles représentent soit des données manquantes, soit des événements non capturés, soit des limites fondamentales du modèle.

Protocole :

```text
Étape 1 — Identifier les erreurs UNKNOWN
  Prendre toutes les erreurs du modèle premium H40 avec tag UNKNOWN
  Créer une liste datée

Étape 2 — Recherche d'événements externes
  Pour chaque date d'erreur UNKNOWN :
  - Consulter Reuters / Bloomberg archives (date + "corn" ou "maïs")
  - Consulter IGC reports archives
  - Vérifier la table des événements EU (eu_event_catalogue.json)
  - Vérifier les événements Ukraine
  - Vérifier les données météo archives

Étape 3 — Construire external_events.csv
  Format : date, event_type, description, severity (1-5), source

Catégories d'événements :
  GEOPOLITICAL    : embargo, conflit, sanction
  PORT_STRIKE     : grève portuaire EU ou Ukraine
  LOGISTICS       : accident fret, canal bloqué, Danube gelé
  POLICY          : PAC, régulation EU, changement quotas
  DATA_ERROR      : erreur de données source (à corriger)
  CONTRACT_CHANGE : changement de spécification contrat EMA
  WEATHER_EXTREME : événement météo non capturé par Open-Meteo
  UNKNOWN_REMAIN  : toujours inexpliqué après recherche
```

Classification finale des UNKNOWN :

```text
EXPLAINED_POST_HOCK :
  Un événement a été trouvé → ajouter à la base des événements
  → Potentiellement récupérable si on collecte la donnée

UNEXPLAINED_SYSTEMATIC :
  Aucun événement trouvé + erreurs regroupées temporellement
  → Peut indiquer une rupture de structure non détectée

RANDOM_NOISE :
  Aucun pattern → erreurs dispersées dans le temps
  → Limite fondamentale du signal ; ne pas chercher à les corriger

DATA_ERROR :
  Erreur identifiée dans les données source
  → Corriger immédiatement dans la pipeline
```

Livrables :

```text
data/external_events.csv
artefacts/v7/unknown_unknowns_analysis.json
docs/UNKNOWN_UNKNOWNS.md
```

---

## 7b. Tagging obligatoire des expériences

Chaque expérience V7 doit être annotée avec son type pour éviter de confondre "comprendre" et "prédire".

```text
experiment_type doit être l'un de :

DATA_VALIDATION
  → V7-00, V7-01, V7-39
  Objectif : valider la qualité ou la source des données
  Pas de claim prédictif

STATISTICAL_VALIDATION
  → V7-02, V7-29, V7-30
  Objectif : valider que les résultats résistent aux tests
  Pas de claim prédictif

DESCRIPTIVE_ECONOMIC
  → V7-09, V7-10, V7-19, V7-25, V7-26, V7-32, V7-33, V7-36, V7-40
  Objectif : comprendre les mécanismes économiques
  Utile pour l'explicabilité mais PAS une preuve prédictive directe

PREDICTIVE_OOF
  → V7-03, V7-04, V7-05, V7-06, V7-07, V7-08, V7-12, V7-17, V7-18, V7-21, V7-22,
    V7-23, V7-24, V7-27, V7-31, V7-35, V7-37, V7-38
  Objectif : mesurer une performance prédictive réelle hors échantillon
  Peut donner des claims GO/PROMISING/NO_GO

BACKTEST_RESEARCH
  → V7-13
  Objectif : simuler une performance économique (non production)
  Verdict obligatoire : RESEARCH_ONLY_NOT_TRADING

MODEL_VALIDATION
  → V7-11, V7-14, V7-16, V7-20, V7-34
  Objectif : comprendre et améliorer les modèles existants
  Peut amener des ajustements mais pas des claims directs

INDICATOR_CANDIDATE
  → V7-28
  Objectif : transformer les signaux en indicateur structuré
  Requiert que tous les signaux utilisés soient GO ou PROMISING_ROBUST
```

---

## 8. Protocoles de validation statistique

Toute expérience V7 doit suivre ces protocoles. Aucune exception.

### 8.1 Protocole standard

```text
1. Définir l'hypothèse avant de lancer (H0 et Ha)
2. Fixer le seed = 42
3. Choisir le protocole CV (walk-forward avec embargo par défaut)
4. Calculer AUC, DA, balanced accuracy, top20, MCC
5. Calculer l'intervalle de confiance bootstrap (n=1000)
6. Tester avec n réel (vérifier que n > 50 pour AUC fiable)
7. Appliquer Benjamini-Hochberg si tests multiples > 5
8. Tester la stabilité par année (variation > 20 pts = fragile)
9. Documenter le verdict : GO / PROMISING / WATCHLIST / NO_GO
```

### 8.2 Règles de significativité

```text
Signal FORT (GO) :
  - AUC ≥ 0.65 stable par année
  - Balanced accuracy ≥ 0.60
  - n OOF ≥ 100
  - IC95 AUC inférieur ≥ 0.55
  - Non dépendant d'une seule crise

Signal PROMETTEUR (PROMISING) :
  - AUC ≥ 0.60 OU
  - top20 DA ≥ 0.70 avec n ≥ 50

Signal INTÉRESSANT (WATCHLIST) :
  - AUC ≥ 0.55 avec explication économique claire
  - Valeur si < 0.60 mais delta AUC vs baseline > 0.05

Signal NULS (NO_GO) :
  - AUC < 0.55 OU IC95 inclut 0.50
  - OU balanced accuracy < 0.53
```

### 8.3 Règles anti-leakage

```text
Obligatoire dans toutes les expériences :
  - shift(1) sur toutes les features fondamentales
  - shift(1) sur toutes les features OI/volume
  - shift(H) sur toutes les cibles H-jours
  - Les seuils (percentiles, z-scores) calculés sur train uniquement
  - Les meta-features sont des prédictions OOF uniquement
  - L'imputation des NaN apprises sur train uniquement
  - Pas de StandardScaler sur l'ensemble train+test
  - Embargo de H jours pour les cibles longues (H ≥ 40 jours)

Vérifications automatiques :
  - Future dependency check : aucune feature avec date > t
  - Perfect fit check : aucune feature avec corrélation > 0.95 avec la cible
  - OOF check : toutes les meta-features ont is_oof = True
```

### 8.4 Tests de robustesse obligatoires

```text
Pour tout signal candidat indicateur :
  1. Leave-one-year-out : performance acceptable chaque année ?
  2. Leave-one-crisis-out : 2012, 2020, 2022 exclus → signal toujours positif ?
  3. No-proxy period : signal uniquement sur période haute fiabilité données ?
  4. Stress test coûts : PnL positif à 3 EUR/t et à 5 EUR/t ?
  5. Décomposition par régime : le signal marche-t-il HORS des bases extrêmes ?
```

---

## 9. Plan d'acquisition de données V7

### 9.1 Données critiques (BLOQUANTES pour certaines expériences)

| Source | Utilisation | Priorité | Coût estimé |
|---|---|---|---|
| Euronext NextHistory (settlement officiel EMA) | V7-01, valider tous signaux | HAUTE | Abonnement pro (~500-2000€/an) |
| FOB Ukraine quotidien (IGC ou Argus) | V7-11, V7-22 | HAUTE | Abonnement IGC gratuit (hebdo) |
| FOB Bordeaux / ARA maïs | V7-11, V7-22 | HAUTE | FranceAgriMer (gratuit) |
| EC MARS mensuel complet (yield revision) | V7-11 | HAUTE | JRC (gratuit) |

### 9.2 Données importantes (améliorent mais pas bloquantes)

| Source | Utilisation | Priorité | Coût estimé |
|---|---|---|---|
| WASDE texte parsé | V7-23 | MOYENNE | USDA (gratuit PDF) |
| FranceAgriMer bilans mensuels parsés | V7-11 | MOYENNE | FranceAgriMer (gratuit PDF) |
| Eurostat COMEXT API (import/export EU) | V7-11 | MOYENNE | Gratuit API |
| Baltic Dry Index proxy (BDI) | V7-11, V7-22 | MOYENNE | Yahoo Finance (gratuit) |
| CBOT options IV (vol surface) | V7-24 | BASSE | Barchart Premier (~100€/mois) |
| Tigramite (PCMCI Python) | V7-18 | BASSE | Open source (pip install) |
| Engrais EU (urea, ammonia) | V7-11 | BASSE | ICIS (payant) ou FAO (gratuit annuel) |

### 9.3 Données déjà disponibles

```text
DÉJÀ DANS LE PIPELINE :
  - CBOT OHLCV via yfinance
  - EUR/USD via yfinance
  - TTF gaz via yfinance
  - COT CFTC (hebdo)
  - WASDE USDA (mensuel, chiffres)
  - NASS Crop Progress (hebdo, mai-nov)
  - Drought Monitor US (hebdo)
  - EIA éthanol (hebdo)
  - Open-Meteo EU 6 zones (quotidien)
  - EMA proxy Barchart (exploratory)
  - EMA targets parquet (13 cibles originales + 30 cibles V2)
  - Features EMA courbe (28 features shift(1))
```

### 9.4 Données flux physiques

```text
INSPECTIONS ET FLUX PHYSIQUES US :
  - Weekly Export Inspections USDA (grain hebdo, gratuit)
  - FAS Grain Circular (mensuel, gratuit)
  - US Weekly Export Sales (hebdo, gratuit)
  - US Grain Transport costs (PNW, Gulf - trimestriel USDA)

FLUX EUROPÉENS ET INTERNATIONAUX :
  - Volumes export France maïs (FranceAgriMer, mensuel)
  - Flux Danube / ports Mer Noire (IGC, hebdo ou mensuel)
  - Certificats d'export EU maïs (Eurostat ou DG AGRI)
  - Imports Espagne / Italie (Eurostat COMEXT, mensuel)
  - Tenders Egypte GASC (chaque semaine disponible publiquement)
  - Tenders Corée / Japon maïs (reports Commerce)
  - Ukraine export monitoring (UN FAO, UkrAgroConsult)
```

Priorité d'acquisition :

```text
HAUTE (V7-11, V7-22) :
  Export Inspections US hebdo
  Flux Ukraine mensuel
  GASC tenders (proxy FOB Ukraine)

MOYENNE (V7-10, V7-36) :
  Flux Danube
  Tenders internationaux
  Certificats export EU

BASSE :
  Flux portuaires granulaires par terminal
```

### 9.5 Données satellitaires et indices de végétation

```text
GRATUIT (open source) :
  NASA MODIS NDVI (16 jours, 250m)
    → Téléchargement via earthdata.nasa.gov ou AppEEARS
    → Zones : France, Espagne, Hongrie, Roumanie, Ukraine ouest

  Copernicus MODIS/Sentinel NDVI
    → Accès via openeo.eu ou WEkEO

  ERA5 (ECMWF réanalyse atmosphérique)
    → Temperature, précipitations, sol moisture
    → Historique 1940-présent, quotidien
    → Gratuit via CDS API (copernicus.eu)

  Copernicus AGRI-STICS / Agri4Cast
    → Modèle de végétation EU pour cultures principales
    → Déjà partiel dans EC MARS

Variables à construire :
  ndvi_eu_corn_weighted       (NDVI pondéré par zone maïs EU)
  ndvi_anomaly_vs_5y_mean     (anomalie vs moyenne 5 ans)
  ndvi_trend_14d              (tendance sur 14 jours)
  soil_moisture_eu_corn       (humidité sol pondérée)
  soil_moisture_anomaly       (anomalie vs 5 ans)
  heat_stress_satellite       (jours > 35°C via ERA5)
  frost_risk_eu               (jours < 0°C après 15 avril)
```

### 9.6 Données coût et industrie

```text
ENGRAIS (coût production EU) :
  Urea prix EU (EUR/t)            → Yara publications, ICIS, ou FAO (annuel)
  Ammonia prix EU (EUR/t)         → CRU Group (hebdo payant), ou ICIS
  DAP/phosphate prix EU           → World Bank Commodities
  NPK composite index

  Proxy disponible :
    Henry Hub gas price → proxy coût ammoniac US
    TTF → proxy coût ammoniac EU (azote synthèse = gaz naturel × énergie)

INDUSTRIE AVAL (demande EU) :
  Production éthanol Europe (eBIO, mensuel, gratuit)
  Cheptel porcin EU (Eurostat, trimestriel)
  Prix alimentation animale EU (Eurostat, mensuel)
  Aliment bétail composite index (COCERAL ou Eurostat)

COÛTS LOGISTIQUES :
  Coût séchage maïs EU (proxy : TTF × rendement énergie)
  Coût stockage (taux intérêt court terme EU × durée × coût capital)
  Tarif péage Rhin (proxy logistique intérieure EU)

IMPORT/EXPORT PARITÉ :
  Marge exportateur EU → ARA → monde
  Marge importateur Ukraine / Brésil → ARA → EU
```

### 9.7 Données marchés financiers

```text
INDICES ET MACRO :
  DXY (Dollar Index) via yfinance    → proxy USD strength → CBOT
  SP500 total return                 → risk-on/off → commodités
  VIX                                → volatilité implicite US → CBOT vol
  CRB Index ou GSCI Commodity        → indice commodités global
  US 10Y yield vs EU 10Y             → différentiel taux → EUR/USD carry

FLOWS ET SENTIMENT :
  Managed money flows CFTC (déjà en partie via COT)
  Commodity index rebalancing calendar
  Implied forward rates (curve steepness)

CROSS-ASSET SIGNALS :
  Soja / maïs ratio (ZS/ZC)         → déjà prévu V7-17
  Blé / maïs ratio US (ZW/ZC)       → déjà prévu V7-17
  Blé Euronext / maïs Euronext ratio → déjà prévu V7-17
  Pétrole WTI vs maïs (éthanol parity)
  Gaz naturel Henry Hub vs maïs US   → engrais US
  EUR/USD régimes                     → déjà prévu V7-21
```

### 9.8 Données options (volatilité implicite)

```text
CBOT OPTIONS (maïs ZC) :
  Implied volatility at-the-money 30/60/90 jours
  IV skew : IV_put_25delta - IV_call_25delta
  Term structure : IV_90d - IV_30d
  Realized vol vs IV (prime de risque)
  Put/call ratio (volume)
  Open interest par strike

Sources :
  CMEGroup public data (certaines données gratuites)
  Barchart Premier (~100€/mois)
  CBOE si options maïs disponibles

EMA OPTIONS (si disponibles) :
  Very limited : Euronext ne propose que peu d'options liquides sur EMA
  Si disponible : IV EMA vs IV CBOT → spread volatilité
  Proxy : calculer vol réalisée EMA vs vol réalisée CBOT
```

---

## 10. Critères de décision

Une expérience devient `GO` seulement si elle améliore au moins un point important :

```text
AUC +0.02 minimum
ou top20 +3 points
ou balanced accuracy +2 points
ou PnL supérieur sans drawdown plus élevé
ou meilleure calibration (ECE -0.02)
ou meilleure explicabilité économique (hypothèse confirmée)
```

Un signal devient candidat indicateur si :

```text
performance stable par année (CV annuel < 15 pts)
support suffisant (n OOF ≥ 100)
pas dépendant d'une seule crise
pas uniquement porté par proxy data
robuste aux coûts (positif à 5 EUR/t)
explicable économiquement (hypothèse validée dans H1-H20)
stable sur différents protocoles CV (purged, non-overlap, LOO)
```

Un signal candidat indicateur est ÉLIMINÉ si :

```text
IC95 AUC inclut 0.50
balanced accuracy < 0.53 hors crises
AUC chute > 0.10 quand on exclut les données proxy
PnL négatif à 3 EUR/t/leg
ROLL_ARTIFACT > 50% des erreurs top20
```

---

## 11. Conclusion opérationnelle

La suite de l'étude doit devenir :

```text
V7 = étude intégrale des signaux économiques du maïs
     par cibles auxiliaires,
     stacking OOF,
     régimes saisonniers,
     basis,
     CBOT,
     EMA premium,
     confiance et P(correct),
     backtests research-only,
     données européennes enrichies,
     causalité formelle,
     régimes structurels,
     microstructure,
     explicabilité,
     et architecture indicateur final.
```

Le but final n'est pas de produire immédiatement un indicateur. Le but est d'épuiser toutes les pistes sérieuses pour comprendre le prix du maïs, puis seulement ensuite construire un indicateur professionnel fiable.

### Ordre d'exécution recommandé

```text
Phase 0 — Sécurité statistique absolue (AVANT DE CROIRE AUX RÉSULTATS)
  Ces expériences doivent être faites avant toute conclusion sur V6.

  V7-00 (audit cohérence V6)
  V7-29 (multiple testing et FDR)
  V7-30 (red team validation des résultats > 0.85 AUC)
  V7-02 (purged CV avec embargo)
  V7-01 (source EMA officielle ou validation proxy)

  ⚠ Si des résultats V6 ne survivent pas à cette phase,
    ils sont marqués EXPLORATORY_ONLY et ne peuvent pas être
    des preuves centrales de l'étude.

Phase 1 — Consolidation des signaux validés
  V7-31 (baselines professionnelles et règles simples)
  V7-07 (roll-aware premium model)
  V7-08 (régimes de basis)
  V7-06 (modèles saisonniers experts)
  V7-12 (P(correct) et calibration avancée)
  V7-39 (data quality score)

Phase 2 — Exploration des signaux économiques
  V7-04 (CBOT target lab avancé)
  V7-17 (relations inter-commodités)
  V7-19 (ruptures structurelles)
  V7-25 (anomalies de marché de la littérature)
  V7-26 (mémoire longue et persistance)
  V7-32 (fair value model EMA/CBOT)
  V7-33 (cartographie drivers × horizon)

Phase 3 — Amélioration des modèles
  V7-03 (cross-target stacking V2)
  V7-05 (cross-market CBOT ↔ EMA)
  V7-27 (modèle multi-facteurs conditionnel)
  V7-20 (modèles espace-état dynamiques)
  V7-34 (market scenario classifier)
  V7-35 (distributional forecasting du premium)
  V7-37 (stabilité des features)
  V7-38 (model decay study)

Phase 4 — Enrichissement données et sources alternatives
  V7-11 (données européennes V2)
  V7-16 (microstructure et liquidité EMA)
  V7-22 (parités logistiques FOB/ARA)
  V7-23 (analyse textuelle WASDE/MARS/IGC)
  V7-24 (options et volatilité implicite CBOT)

Phase 5 — Causalité, compréhension et erreurs
  V7-09 (décomposition dynamique EMA)
  V7-10 (event study premium)
  V7-14 (explicabilité et analyse des erreurs)
  V7-18 (causalité formelle PCMCI)
  V7-21 (EUR/USD régimes de change)
  V7-36 (graphe de causalité économique)
  V7-40 (unknown unknowns)

Phase 6 — Construction et validation de l'indicateur final
  V7-13 (backtests recherche avancés)
  V7-28 (architecture finale de l'indicateur)
  V7-15 (rapport final V7)
```

### Matrice priorité × impact × risque par expérience

| Expérience | Priorité | Impact attendu | Risque leakage | Type |
|---|---|---|---|---|
| V7-00 | CRITIQUE | Valide tout V6 | Nul | DATA_VALIDATION |
| V7-29 | CRITIQUE | Sécurité stat | Nul | STATISTICAL_VALIDATION |
| V7-30 | CRITIQUE | Confiance résultats | Nul | STATISTICAL_VALIDATION |
| V7-02 | CRITIQUE | Protocole robuste | Faible | STATISTICAL_VALIDATION |
| V7-01 | CRITIQUE | EMA officiel | Nul | DATA_VALIDATION |
| V7-31 | HAUTE | Baseline réelle | Faible | PREDICTIVE_OOF |
| V7-07 | HAUTE | Réduction erreurs roll | Moyen | PREDICTIVE_OOF |
| V7-08 | HAUTE | Contexte régimes | Moyen | MODEL_VALIDATION |
| V7-06 | HAUTE | Meilleur signal saison | Moyen | PREDICTIVE_OOF |
| V7-12 | HAUTE | Confiance calibrée | Moyen | PREDICTIVE_OOF |
| V7-39 | HAUTE | Qualité données | Faible | DATA_VALIDATION |
| V7-03 | HAUTE | Stacking amélioré | Élevé | PREDICTIVE_OOF |
| V7-04 | HAUTE | Cibles CBOT | Faible | PREDICTIVE_OOF |
| V7-32 | HAUTE | Fair value basis | Moyen | DESCRIPTIVE_ECONOMIC |
| V7-33 | HAUTE | Carte drivers | Faible | DESCRIPTIVE_ECONOMIC |
| V7-37 | HAUTE | Features stables | Faible | MODEL_VALIDATION |
| V7-38 | HAUTE | Fréquence retraining | Faible | MODEL_VALIDATION |
| V7-11 | MOYENNE | Données EU réelles | Faible | DATA_VALIDATION |
| V7-05 | MOYENNE | Cross-market | Élevé | PREDICTIVE_OOF |
| V7-27 | MOYENNE | Modèle complet | Élevé | PREDICTIVE_OOF |
| V7-35 | MOYENNE | Distribution forecast | Moyen | PREDICTIVE_OOF |
| V7-34 | MOYENNE | Scénarios marché | Moyen | MODEL_VALIDATION |
| V7-17 | MOYENNE | Inter-commodités | Faible | DESCRIPTIVE_ECONOMIC |
| V7-19 | MOYENNE | Ruptures struct. | Faible | DESCRIPTIVE_ECONOMIC |
| V7-25 | MOYENNE | Anomalies academic | Faible | DESCRIPTIVE_ECONOMIC |
| V7-14 | MOYENNE | Comprendre erreurs | Faible | MODEL_VALIDATION |
| V7-10 | MOYENNE | Event study | Faible | DESCRIPTIVE_ECONOMIC |
| V7-09 | MOYENNE | Décomposition dyn. | Moyen | DESCRIPTIVE_ECONOMIC |
| V7-18 | MOYENNE | Causalité formelle | Faible | DESCRIPTIVE_ECONOMIC |
| V7-36 | MOYENNE | Graphe causal | Faible | DESCRIPTIVE_ECONOMIC |
| V7-16 | BASSE | Microstructure | Faible | MODEL_VALIDATION |
| V7-20 | BASSE | Kalman filter | Moyen | MODEL_VALIDATION |
| V7-21 | BASSE | EUR/USD | Moyen | PREDICTIVE_OOF |
| V7-22 | BASSE | Parités logistique | Faible | DESCRIPTIVE_ECONOMIC |
| V7-23 | BASSE | NLP rapports | Moyen | PREDICTIVE_OOF |
| V7-24 | BASSE | Options IV | Moyen | PREDICTIVE_OOF |
| V7-26 | BASSE | Mémoire longue | Faible | DESCRIPTIVE_ECONOMIC |
| V7-40 | BASSE | Unknown unknowns | Faible | MODEL_VALIDATION |
| V7-13 | FINALE | Backtests avancés | Faible | BACKTEST_RESEARCH |
| V7-28 | FINALE | Indicateur final | Moyen | INDICATOR_CANDIDATE |
| V7-15 | FINALE | Rapport V7 | Nul | — |

### Vision finale de l'indicateur

```text
Prix Euronext attendu =
  Mouvement mondial du maïs (CBOT, WASDE, météo US, COT, éthanol)
  + Variation de prime européenne (basis, stocks EU, météo EU, Ukraine, FOB)
  + Filtre de confiance (P(correct), saison, roll-risk, liquidité)
  + Incertitude / risque (CQR bounds, volatilité implicite)

Ceci est un indicateur hybride :
  règle économique simple  (basis z-score, saison)
  + modèle statistique     (HistGB stacked OOF)
  + contexte saisonnier    (expert par saison)
  + filtre de confiance    (P(correct) calibré)
  + filtre de roll         (exclusion near-roll)
  + explication marché     (SHAP narratif)
```

Ce n'est pas une boîte noire IA. C'est une étude de marché structurée, rendue partiellement prédictive par des méthodes statistiques transparentes.

---

## 12. Les trois axes de renforcement V7

Le document V7 doit maintenant être renforcé sur trois axes simultanément.

### Axe 1 — Sécurité statistique

Empêcher les faux bons résultats.

```text
Contrôle multiple testing (V7-29)
Red team des AUC > 0.85 (V7-30)
Purged CV / embargo strict (V7-02)
Baselines professionnelles fortes (V7-31)
Holdout final gelé 2024
```

### Axe 2 — Exploration économique

Tester encore plus de mécanismes explicatifs pour comprendre.

```text
Fair value model (V7-32)
Cartographie drivers × horizon (V7-33)
Scénarios de marché (V7-34)
Forecast distributionnel (V7-35)
Graphe causal (V7-36)
Anomalies de marché (V7-25)
Ruptures structurelles (V7-19)
Causalité formelle PCMCI (V7-18)
Données EU enrichies (V7-11)
```

### Axe 3 — Préparation indicateur

Transformer les découvertes en briques robustes.

```text
P(correct) calibré (V7-12)
Data quality score (V7-39)
Stabilité des features (V7-37)
Model decay study (V7-38)
Roll-aware model (V7-07)
Backtests avancés stress test (V7-13)
Architecture finale 5 couches (V7-28)
Unknown unknowns (V7-40)
```

---

## 13. Séparation fondamentale : comprendre / prédire / backtester / produire

La prochaine étape n'est pas de produire l'indicateur. La prochaine étape est de finaliser l'étude exhaustive en séparant clairement :

```text
CE QUI EXPLIQUE (DESCRIPTIVE_ECONOMIC) :
  Décomposition EMA, causalité, fair value, drivers × horizon,
  event study, ruptures structurelles, anomalies, mémoire longue.
  → Utilisable dans le rapport. Pas une preuve prédictive.

CE QUI PRÉDIT (PREDICTIVE_OOF) :
  Stacking OOF, modèles saisonniers, P(correct), cross-target,
  baselines professionnelles, distributional forecast.
  → Claim GO/PROMISING/NO_GO avec IC95 et Benjamini-Hochberg.

CE QUI BACKTESTE (BACKTEST_RESEARCH) :
  Simulations spread CBOT ou EMA premium, protocole strict,
  coûts stressés, non-overlap, verdict RESEARCH_ONLY_NOT_TRADING.
  → Aucun claim production.

CE QUI EST ROBUSTE (INDICATOR_CANDIDATE) :
  Stable par année + non dépendant d'une crise + hors proxy + positif à 5€/t.
  → Peut entrer dans l'architecture indicateur final.

CE QUI EST IMPOSSIBLE AVEC LES DONNÉES ACTUELLES :
  Direction EMA brute (NO_GO confirmé).
  CQR prix absolu EMA (NO_GO confirmé).
  Settlement officiel EMA (bloqué jusqu'à acquisition).
  → Documenter honnêtement dans le rapport final.
```

---

## 14. Phrase directrice finale

```text
CBOT donne le mouvement mondial du maïs.
Euronext EMA ajoute une prime européenne.
Le basis EMA/CBOT mesure cette prime.
L'étude cherche à comprendre quand cette prime est justifiée, 
excessive ou en correction, et dans quels contextes cela 
permet d'anticiper la performance relative du maïs européen 
face au maïs américain.

Ce n'est pas un indicateur production.
C'est une étude de recherche rigoureuse et honnête
sur la formation du prix du maïs.
```
