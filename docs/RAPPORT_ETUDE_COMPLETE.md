# Étude du cours du maïs — rapport de démarche complète

Auteur : ThryB64. Date : 2026-06-14. Ce rapport retrace **comment** et **pourquoi** j'ai mené
l'étude : la récolte des données, puis le fil scientifique **question → test → analyse →
nouvelle question**. Chaque test est expliqué en une phrase ; quand il n'a rien donné, je le
dis et je l'ai abandonné. Inventaire complet (310 tests/expériences) et arbre visuel à la fin.

---

## PARTIE 1 — Comment j'ai commencé : la récolte des données

J'ai d'abord rassemblé **toutes les données publiques gratuites** disponibles, par source.

### Sources et variables (par source)
| Source | Fichier | Variables principales |
|---|---|---|
| **CBOT (Chicago)** | `data/interim/market.parquet` | prix maïs (OHLC, volume), blé, soja |
| **Euronext (EMA)** | `data/processed/euronext/ema_*` | prix €/t continu, courbe, contrats, settlements (97 % proxy) |
| **WASDE / USDA** | `data/interim/wasde.parquet` + vintage | stocks de fin, stocks-to-use, production, exports, usage, prix ferme |
| **Crop Progress/Condition** | `data/raw/usda_nass_crop_condition/` | % good/excellent, poor/very-poor, floraison, récolte |
| **Météo (Open-Meteo)** | `data/interim/meteo.parquet` | température, pluie, GDD, stress (réalisé + prévu) |
| **COT (CFTC)** | `data/interim/cftc_cot.parquet` | positions Managed Money, commerciaux, open interest |
| **Éthanol / énergie (EIA)** | `data/interim/eia_ethanol.parquet` | production éthanol, ratios énergie |
| **Macro (FRED)** | `data/interim/macro_fred.parquet` | EUR/USD, taux, indices |
| **Exports (USDA FAS)** | `data/interim/fas_export_sales.parquet` | ventes export hebdo |
| **Sécheresse / production** | `drought_monitor.parquet`, `production.parquet`, `quickstats.parquet` | indices de stress, production par État |
| **Calendrier USDA** | `data/interim/usda_calendar.parquet` | dates de publication (anti-fuite) |

> Règle posée dès le départ : **anti-fuite**. Chaque variable n'est utilisée qu'**après sa
> date de publication réelle** ; le futur ne sert jamais à calculer un signal ; le **holdout
> 2024+** est mis de côté et n'est ouvert qu'une seule fois, à la toute fin.

---

## PARTIE 2 — Comment j'ai étudié : le fil question → test → analyse

### Q1 (question principale) — Peut-on prédire le prix du maïs avec ces données ?
**Tests** : `test_benchmark_canonical`, `test_benchmark_suite`, `test_ema_benchmark`,
`test_ema_smart_baselines`, `EXT025_random_walk` — comparer tout modèle à la marche aléatoire.
**Analyse** : la **random walk est imbattable en RMSE** (0 modèle sur 36 ne la bat). Le prix
exact n'est pas prévisible → je **change d'objectif** : viser la direction et expliquer le basis.

### Q2 — Si CBOT donne la tendance, Euronext révèle-t-il une prime via le basis ?
**Tests** : `test_ema_cbot_cointegration`, `test_ema_decomposition`, `test_ema_return_decomposition`,
`test_ema_residual_study`, `test_ema_residual_eu_v2`, `test_ema_basis_formal`.
**Analyse** : CBOT et Euronext sont **cointégrés** ; la prime se compresse surtout quand le CBOT
**monte** (la jambe CBOT pèse 6× la jambe EMA). Le résidu européen pur est faible → j'étudie le
**basis** comme objet central.

### Q3 — Le basis revient-il à la moyenne ? Peut-on en tirer un signal de vente ?
**Tests** : `test_v10_market_discovery`, `test_v12_mean_reversion_lab`, `test_v13_basis_reversion`,
`test_v14_short_indicator`, `test_v15_short_realism`, `test_v9_structural_indicator`.
**Analyse** : le basis a une **demi-vie ~17-47 j** ; vendre quand le basis est haut survit aux
coûts hors crise ; l'edge est concentré sur les extrêmes (z>2). Indicateur structurel **AUC
0.656-0.694** → encourageant, mais faible.

### Q4 — La macro, la météo, le COT expliquent-ils le basis et la prime ?
**Tests** : `test_v16_basis_explanation` (macro), `test_v18_weather_deep`, `test_v19_cbot_weather`,
`test_v45_weather_crop_stress` (météo), `test_cot_advanced` (COT).
**Analyse** : la macro **n'explique pas** le basis (R² OOF −0.25, prime locale) ; la météo
réalisée est **déjà price-in** (AUC 0.508) ; le COT **n'aide pas** hors échantillon. → **ces
trois pistes sont abandonnées** comme prédicteurs (gardées comme contexte).

### Q5 — Quand la prime se compresse-t-elle mal (cas ADVERSE) ? Est-ce prévisible ?
**Tests** : `test_v32_adverse_path`, `test_v35_cbot_engine`, `test_v38_adverse_risk`,
`test_v41_cbot_support`.
**Analyse** : l'**issue ADVERSE est prévisible** (LOO AUC 0.72) à partir du niveau d'entrée,
mais le **mécanisme** de compression ne l'est pas (AUC 0.48). Un **support CBOT** divise le
risque ADVERSE par 2 → utile pour doser, pas pour prédire.

### Q6 — Mes résultats sont-ils propres (pas de fuite de données) ?
**Tests** : `test_leakage_global`, `test_leakage_calendar`, `test_purged_cv`,
`test_v24_data_forensic`, `test_v26_official_ema`, `EXT026_wasde_vintage`.
**Analyse** : j'ai **détecté et corrigé** une fuite WASDE interne (~8 j d'avance) via un
pipeline « vintage » daté à la publication ; la série Euronext brute a des **artefacts de roll**
(corrigés par la série ajustée). La rigueur anti-fuite est durcie pour toute la suite.

### Q7 — En repartant de zéro, **systématiquement**, quelles familles portent un vrai signal ?
**Tests** : **recherche externe `EXT001`→`EXT050`** (24 expériences, 1 famille chacune :
météo, WASDE, COT, courbe, éthanol, basis, crop condition, volatilité, régimes, modèles).
**Analyse** : seules **Crop Condition (H90)** et **WASDE stocks-to-use (H40)** donnent un gain
**directionnel stable** ; la **volatilité (HAR/EGARCH)** se prévoit bien (risque). **Tout le
reste est rejeté** (météo, COT, éthanol, surprise WASDE, trend-following, stacking, deep learning).

### Q8 — Ces signaux survivent-ils hors échantillon (holdout 2024+) ? En faire un score de vente ?
**Tests** : `test_cbot_sale_score`, `test_cbot_sale_score_leakage`, `test_cbot_sale_score_outputs`.
**Analyse** : Crop@H90 fait **DA 0.686 / AUC 0.816** sur 2024+ (jamais vu avant) et bat la
random walk, **mais ne bat pas une simple saisonnalité** ; le backtest dépend du cadrage. →
score **FRAGILE** : aide à la décision, pas un modèle de prix.

### Q9 — À quoi ressemble l'indicateur sur l'historique Euronext réel ?
**Tests** : `test_euronext_indicator`, `test_euronext_indicator_backtest`,
`test_euronext_indicator_dashboard` + dashboard HTML.
**Analyse** : les recommandations **séparent bien les retours futurs** (SELL_PARTIAL → −5.8 % à
H90, WAIT → +5.1 %), mais l'AUC **hors échantillon est faible (0.561)** et le prix Euronext est
à 97 % un proxy → **RESEARCH_ONLY** (visualisation honnête, pas une validation).

---

## PARTIE 3 — Les tests qui n'ont rien donné (feuilles vides)
J'assume les impasses : elles prouvent que j'ai **tout exploré**. Une phrase chacune.
- **Météo réalisée** (`test_v18_weather_deep`, `EXT001/002/020`) : price-in, dégrade le RMSE → abandonné.
- **COT / positions** (`test_cot_advanced`, `EXT003`) : aucun signal hors échantillon → abandonné.
- **Éthanol / crush** (`EXT004`) : sans vrais prix éthanol/DDG, proxys inutiles → abandonné.
- **Surprise WASDE** (`EXT008`) : non captable sans consensus analystes → abandonné.
- **Trend-following** (`EXT011`) : le maïs ne tend pas (DA < 0.5) → abandonné.
- **Stacking / deep learning** (`test_stacking`, `test_deep_learning`, `EXT016/050`) : sur-apprennent → abandonnés.
- **Granger / fair-value basis** (`test_ema_granger_validation`, `test_v16_basis_explanation`) : non significatifs → abandonnés.
- **Mécanisme de compression, hazard timing** (`test_v35_cbot_engine`, `test_hazard_compression`) : ≈ hasard → abandonnés.
- **Courbe, basis quotidien, OU, satellite** (`EXT005/012/013`, `test_curve_*`) : **bloqués faute de données**.

---

## PARTIE 4 — L'arbre de cheminement (le cœur de la démarche)
Toute la démarche est représentée comme un **arbre de cheminement** qui descend, couche par
couche : **❓ question (bleu) → 📄 fichiers de tests qui y ont répondu → 🔎 analyse des
résultats → nouvelle(s) question(s)**. Une question peut en générer plusieurs. **Les 310
fichiers de l'étude y sont tous rattachés** à la question qu'ils ont servi à répondre — rien
n'est oublié. Couleur des fichiers (5 catégories claires) : **🟢 gardé (exploitable), 🔴
abandonné (n'a rien donné), 🟠 bloqué (données manquantes), 🔧 outil (audit/anti-fuite), 🔵
exploration (étape de cadrage)**.

- **Arbre interactif (flowchart)** : `artefacts/rapport_etude/arbre_etude.html`. Chaque couche
  affiche **📋 ce qu'on a cherché à faire** (résumé global), puis les **📄 fichiers** (chips
  colorés), puis **🔎 l'analyse globale des résultats + la transition** vers la question
  suivante. **Cliquer sur un fichier** ouvre un panneau de détail : ce qu'on fait / pourquoi /
  comment (docstring complète) + les **résultats et l'analyse**. Conclusion verte en bas.
- **Arbre en texte** (exhaustif, tous les fichiers + résumé/analyse par question) : `docs/ARBRE_ETUDE.md`.
- **Tests performants** : `artefacts/rapport_etude/tests_performants.html`.
- **Inventaire** : `artefacts/rapport_etude/inventaire_tests.csv` (310 lignes, description =
  vraie docstring du fichier, + la question rattachée).

Squelette des couches (chaque couche = une analyse qui mène à la suivante) :
```
Q-DATA données propres ?  → fuite WASDE corrigée, roll corrigé → on peut tester
   └ Q1 prédire le prix ?  → random walk imbattable → on vise la DIRECTION
      └ Q2 direction/basis ? → cointégrés, prime par hausse CBOT
         ├ Q3 basis réversible ? → demi-vie 17-47j, AUC 0.66-0.69
         │   ├ Q5 ADVERSE ? → issue prévisible (0.72), mécanisme non (0.48 🔴)
         │   │   └ Q6 doser le risque ? → support CBOT, volatilité −24% RMSE 🟢
         │   └ Q-LIVE indicateur suivi ? → système forward, reste analytique
         │       └ Q7 familles EXT ? → Crop+WASDE+vol 🟢 ; trend/stacking/DL 🔴
         │           └ Q8 holdout ? → FRAGILE → Q9 Euronext → RESEARCH_ONLY
         ├ Q4 explication du basis ? → macro 🔴, Granger 🔴, substitution=contexte
         ├ Q2b météo ? → réalisée price-in 🔴
         └ Q2c COT/éthanol ? → rien 🔴
```
Répartition globale (310 fichiers) : **44 gardés 🟢, 41 abandonnés 🔴, 26 bloqués 🟠, 32
outils 🔧, 167 explorations 🔵**.

---

## PARTIE 5 — Conclusion

**Prédire le prix : impossible** avec les données gratuites — la random walk reste imbattable.
**Construire un indicateur fiable : très difficile** — le meilleur signal (Crop Condition + WASDE
+ volatilité) est réel mais **modeste et fragile** (ne bat pas la saisonnalité hors échantillon).

**Mais ces tests ont aussi donné de bons résultats**, et on peut en déduire, à chaque fois, une
brique solide : la **direction long-horizon** (H40-H90) porte de l'information (Crop@H90 **AUC
0.816** en holdout), la **volatilité se prévoit** (HAR/EGARCH, **−24 % de RMSE**), et les
**recommandations ordonnent correctement les baisses et les hausses** sur l'historique Euronext.

> **En une phrase** : l'étude permet de détecter un **risque de baisse à 90 jours avec ~73 % de
> précision** quand l'indicateur dit « vendre une partie », mais ces signaux forts
> **n'apparaissent qu'environ 1 fois par an** (17 épisodes en 16 ans) — utile comme **repère
> prudent d'aide à la vente**, pas comme prévision de prix ni système automatique.
