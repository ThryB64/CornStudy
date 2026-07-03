# Limites — score de vente CBOT

Version : `cbot_sale_score_v1`. Date : 2026-06-13. **À lire avant tout usage.**

## 1. Ce que le score N'EST PAS
- **Pas une prévision de prix** : la random walk reste imbattable en RMSE (étape 6).
- **Pas un bot de trading** : aucune exécution automatique, jamais de short, de levier ni de
  rachat spéculatif. C'est une **aide à la décision de vente**.
- **Pas une garantie** : un score n'est pas une certitude ; il peut se tromper.

## 2. Limites de robustesse (verdict FRAGILE)
- **Edge modeste** : en recherche, gain directionnel faible (Diebold-Mariano non significatif,
  IC bootstrap chevauchant le marché seul).
- **Pas de gain vs saisonnalité sur le holdout** : sur 2024+, une **pure saisonnalité** (DA
  0.752) et le **marché seul** (0.752) font aussi bien voire mieux que le score crop@H90
  (0.686). Les fondamentaux n'ajoutent pas de valeur démontrable sur cette fenêtre.
- **Holdout court** : ~1,5 an (n≈300), **un seul cycle baissier** (2024). Puissance faible ;
  un bon chiffre n'y est pas une preuve.
- **Backtest mitigé et sensible au cadrage** : seulement **2 campagnes** (2025 incomplète).
  Selon le découpage, le score **bat ou perd** contre les baselines (année civile : perd vs
  vente précoce ; Sep-Aug : bat tout). Le **cooldown** (20 séances) rend la simulation plus
  réaliste mais **réduit** légèrement la performance — pas de free lunch. Cette dépendance au
  cadrage est elle-même un signe de fragilité.
- **Régimes post-hoc** : `regime_*` servent **uniquement** à doser la confiance, pas la
  direction ; à valider en forward.

## 3. Familles REJETÉES (non intégrées — étapes 4-6)
Météo réalisée (brute/lags/extrême), COT, surprise WASDE proxy, éthanol/DDG proxy,
trend-following, stacking, deep learning. Elles **dégradent** le signal ou sur-apprennent.

## 4. Familles BLOQUÉES / FUTURE_DATA_REQUIRED
Courbe futures par contrat, basis / cash bids, OU mean-reversion, satellite/NDVI, météo
**prévue** (archive forward), options (vol implicite), consensus WASDE pré-rapport. Pistes à
fort prior **non testables** faute de données.

## 5. Données payantes / à acquérir pour progresser
Priorité 1 (dont gratuites débloquantes) : **EUR/USD quotidien** (FRED, débloque basis/OU/
VECM), **archive de prévisions météo forward** (Open-Meteo previous-runs), **export flows**
(USDA FAS) ; puis payantes : **consensus analystes pré-WASDE**, **options maïs (vol
implicite)**, **contrats CBOT par maturité**, **prix physiques FOB**. Détail :
`external_research/docs/step6_missing_data_recommendations.md` et
`external_research/matrices/data_blocked_ideas.csv`.

## 5bis. Limites opérationnelles immédiates
- **Données arrêtées au 2025-07-25.** Le dernier signal (WATCH) **n'est pas à jour** ; il n'a
  aucune valeur décisionnelle aujourd'hui tant que les prix CBOT, le WASDE vintage et le Crop
  Condition ne sont pas reconstruits jusqu'à la date courante, puis `sale-score --latest`
  relancé.
- **Score en CBOT ¢/bu, pas en prix ferme.** Il manque la chaîne **CBOT ¢/bu → €/t (EUR/USD)
  → basis Euronext / local → prix ferme coop**. Le score dit « risque CBOT », pas « vends ton
  maïs à tel prix local maintenant ».
- **Cadre de campagne** : la décision agricole réelle se joue par campagne (Sep-Aug / Oct-Sep),
  pas par année civile ; le backtest le teste mais sur trop peu de campagnes.

## 6. Recommandation d'usage
Utiliser le score comme **repère prudent parmi d'autres** (et non comme déclencheur unique de
vente). Le reconfirmer **en forward** sur plusieurs campagnes avant tout usage opérationnel.
Toujours afficher la **confiance** et le **drapeau de risque** ; en cas de `RISK_HIGH` ou
`NO_SIGNAL`, ne pas se fier au signal directionnel.
