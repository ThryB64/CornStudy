# Résumé des résultats — Étape 4 (P1 : familles fondamentales)

Date : 2026-06-13. Périmètre : 11 expériences P1. Modèle principal, scripts et
résultats internes **non touchés**. Tout sous `external_research/experiments/external_tests/`
et `external_research/results/external_tests/`. Harnais commun :
`_common/ext_harness.py` (+ `wx_utils`, `wasde_utils`, `series_utils`).

## 0. Méthode (rappel)

Question unique par famille : **ajoutée à un modèle de marché minimal (BASE :
ret_5d, ret_20d, vol_20, saison), apporte-t-elle un gain robuste sur le log-retour
CBOT t→t+h (H5/H20/H40/H90) ?** Walk-forward expandant, refit annuel purgé, Ridge
α=10 fixe ex ante, standardisation/imputation **train-only**, holdout 2024+ exclu.
Comparaison BASE vs BASE+FAMILLE, DM-test (HAC lag h−1), stabilité sur 2 sous-périodes.
Référence absolue : RW (EXT025). Chaque famille est fournie **datée à sa disponibilité
réelle** (anti-fuite) : WASDE publication+1BD ; COT mardi→lundi+ ; crop condition
lundi→mardi ; météo réalisée J+1 ; climatologies expandantes ; poids d'État figés 2000-07.

## 1. Résumé général

- **Tentées : 11.** Terminées (testées) : 8. Bloquées données : 2 (EXT005, EXT013).
  Partielles : 2 (EXT004 proxys seulement ; EXT018 descriptif testé, prédictif limité).
- **Aucune famille ne bat la random walk en RMSE. Aucun KEEP.**
- **Deux IMPROVE** : WASDE niveaux de bilan (EXT007) et Crop Condition (EXT019) —
  un signal **directionnel** partiel et stable, à horizon moyen/long, jamais sur le RMSE.
- **Six REJECT** : météo agronomique (EXT001), météo lags/anomalies (EXT002), météo
  extrême (EXT020), surprise WASDE (EXT008), COT (EXT003), crush éthanol proxys (EXT004).
- **Deux DATA_BLOCKED** : courbe futures (EXT005), basis/transmission (EXT013).

## 2. Résultats par famille

### Météo réalisée (EXT001, EXT002, EXT020) — REJECT
Quelle que soit l'agrégation (fenêtres agronomiques, lags/anomalies glissantes,
événements extrêmes), la météo réalisée **dégrade fortement le RMSE OOS** (R² qui
plonge en négatif, jusqu'à −3.4 pour les extrêmes) avec des gains de DA négligeables et
instables. **Confirmation directe de V45** : la météo réalisée est price-in par
anticipation. Elle reste un descripteur de *contexte* (basis moins compressible en été
de stress), pas un prédicteur de direction.

### WASDE niveaux de bilan (EXT007) — IMPROVE
Gain de DA **stable sur les deux sous-périodes** : +2.6→+6.7 pts à H5-H40 (porté par
prix ferme, usage, exports, stocks de fin, stocks-to-use). Mais RMSE dégradé (jusqu'à
+194 % à H90) car les niveaux bruts sont non-stationnaires. Signal directionnel réel d'un
**état de bilan lent** ; à ré-encoder en formes stationnaires et tester en cible
direction. DM non significatif → IMPROVE, pas KEEP.

### Surprise WASDE (EXT008) — REJECT
Les révisions M-M-1 (proxy de surprise *sans consensus analystes*) dégradent RMSE **et**
DA (jusqu'à −16 pts). Cohérent avec Huang-Serra-Garcia (ajustement intraday, non captable
en quotidien). Dossier surprise WASDE clos côté quotidien.

### COT (EXT003) — REJECT
Managed Money disaggregated, calendrier de publication (vendredi) respecté, éval 2016+ :
dégrade RMSE et DA à tous horizons. **Clôture honnête du dossier COT** (V18 n'avait
falsifié que le net total ; aucun signal de second ordre dans la décomposition MM).

### Crush éthanol / énergie (EXT004) — REJECT / PARTIAL_DATA
Sans prix éthanol ni DDG, pas de vraie marge crush. Les proxys disponibles (demande
éthanol EIA, ratios énergie-corn) dégradent RMSE et DA. Conforme à V39-E3/E5.

### Courbe futures (EXT005) — DATA_BLOCKED
Pas de contrats CBOT par maturité (front-only, EXT006) ; courbe EMA accumulée ~2 semaines.

### Basis / transmission (EXT013) — DATA_BLOCKED
Pas d'EUR/USD quotidien historique (basis €/t non reconstructible) ; pas de spot UE
quotidien (COMEXT mensuel).

### Prime météo new-crop (EXT018) — PARTIAL_DATA
Pas de contrats décembre. **Volet descriptif réussi** (réplication Janzen / Li-Hayes-
Jacobs) : biais baissier pré-récolte en année normale, rally estival en année de stress.
**Volet prédictif REJECT** : le classement de stress n'est connu qu'en contemporain
(juillet), pas ex ante au printemps → non exploitable (cf. V45). Seul levier prédictif
possible : révisions de prévisions météo (EXT033).

### Crop condition (EXT019) — IMPROVE
Aucun apport à court terme, mais gain de DA **stable sur les deux moitiés** à long
horizon : **+4.4 pts à H90** (et +1.8 à H40) avec RMSE quasi neutre (+0.3 %). La
condition good/excellent informe la tendance de fond (état d'offre lent). DM non
significatif → IMPROVE. Avec EXT007, l'un des deux seuls signaux fondamentaux non triviaux.

## 3. Tableau final

| experiment_id | family | data_status | best_horizon | best_metric_gain | direction_accuracy_change | stability | leakage_risk | verdict | next_action |
|---|---|---|---|---|---|---|---|---|---|
| EXT001 | météo agronomique | DATA_READY | — | ΔRMSE +8.5 % (pire) | +0.017 (H5) | n/a | none | REJECT | abandon direction |
| EXT002 | météo lags/anomalies | DATA_READY | H40 | ΔRMSE +7.1 % (pire) | +0.029 (H40) | instable | none | REJECT | abandon direction |
| EXT020 | météo extrême | DATA_READY | — | ΔRMSE +32→116 % (pire) | négatif | n/a | none | REJECT | garder en contexte seulement |
| EXT007 | WASDE niveaux | DATA_READY | H20 | **ΔDA +6.1 pts** | +0.061 (H20) | stable (2 moitiés) | none | **IMPROVE** | ré-encoder stationnaire + cible direction |
| EXT008 | WASDE surprise proxy | DATA_READY | — | ΔDA −16 pts | négatif | n/a | none | REJECT | sourcer consensus analystes |
| EXT003 | COT | DATA_READY (2016+) | — | dégrade | négatif | none (cal. OK) | REJECT | dossier clos |
| EXT005 | futures curve | DATA_BLOCKED | — | — | — | — | — | DATA_BLOCKED | contrats CBOT + courbe ≥250 j |
| EXT004 | ethanol/DDG | PARTIAL_DATA | — | dégrade | négatif | none | REJECT (proxys) | sourcer prix éthanol/DDG |
| EXT013 | basis/transmission | DATA_BLOCKED | — | — | — | — | — | DATA_BLOCKED | eurusd quotidien + spot UE |
| EXT018 | weather premium | PARTIAL_DATA | — | descriptif confirmé | n/a (prédictif KO) | n/a | conditionnement contemporain | PARTIAL_DATA | contrats Dec + EXT033 |
| EXT019 | crop condition | DATA_READY | H90 | **ΔDA +4.4 pts** | +0.044 (H90) | stable (2 moitiés) | none | **IMPROVE** | cible direction/score long-horizon |

## 4. Conclusions importantes (réponses honnêtes)

- **Quelle famille apporte le plus ?** Les **niveaux de bilan WASDE (EXT007)** et la
  **condition de culture (EXT019)** — et uniquement sur la **direction**, à horizon
  moyen/long, jamais sur le RMSE. Ce sont des variables d'**état d'offre lent**, pas des
  signaux courts.
- **Quelle famille est inutile ?** La météo réalisée sous toutes ses formes (EXT001/002/
  020 — confirme V45), la surprise WASDE (EXT008), le COT (EXT003), les proxys éthanol
  (EXT004). Toutes dégradent le RMSE OOS.
- **Quelle famille est bloquée ?** Courbe futures (EXT005) et basis/transmission (EXT013)
  par absence de données (contrats CBOT par maturité ; EUR/USD quotidien ; spot UE). Prime
  new-crop (EXT018) partiellement bloquée (contrats décembre).
- **Les fondamentaux améliorent-ils les benchmarks ?** **Non en RMSE** : aucune famille ne
  bat la random walk d'EXT025. En **direction**, deux familles donnent un edge modeste mais
  stable (WASDE état + condition) à H40-H90.
- **Stables ou ponctuels ?** Les deux IMPROVE sont stables sur les deux sous-périodes (d'où
  IMPROVE et non REJECT) mais modestes (DM non significatif). Tous les autres gains
  apparents sont ponctuels ou de signe négatif.
- **Faut-il changer d'objectif ?** **Oui.** L'évidence converge : ces fondamentaux n'aident
  pas la prévision de *niveau/retour* (RMSE), mais portent un signal **directionnel** lent.
  Le bon objectif n'est pas la régression de retour mais un **score de direction / de vente
  à horizon H40-H90** (et la **volatilité/risque** pour les gates), pas le point de prix.

## 5. Recommandation pour l'étape 5 (modèles avancés P2)

Familles à reprendre (les deux seules à porter un signal) :
- **WASDE état de bilan (EXT007) + Crop condition (EXT019)** → intrants d'un modèle
  **supply-demand / VAR parcimonieux (EXT024)** et de **market regimes** ; valider par
  **SHAP-in-split (EXT015)** que stocks-to-use + condition ressortent dans chaque train.
  Cible = **direction long-horizon**, pas RMSE.
- **Volatilité GARCH/EGARCH/HAR (EXT009)** : non testée ici mais prioritaire — meilleure
  vol conditionnelle pour les gates `UNCERTAIN_VOL` et `drawdown_risk`.
- **OU mean-reversion (EXT012)** sur le basis : formalise la demi-vie V10/V138 (dès que
  l'eurusd débloque le basis).
- **Bayesian model averaging / DMA (EXT014)** : diagnostic *quand* chaque famille est
  informative (utile vu la rareté des signaux).
- **Trend-following EWMAC (EXT011)** : plancher technique de référence.
- **NBEATSx (EXT016)** : basse priorité, verdict attendu REJECT (à documenter, pas à
  prioriser).

À NE PAS reprendre : météo réalisée, surprise WASDE, COT, proxys éthanol — sauf comme
variables de **contexte** descriptif. EXT005/EXT013/EXT018 restent en attente de données.

L'étape 5 n'est pas codée (règle respectée). Aucun import vers le modèle principal.
