# Étape 6 — Synthèse par famille de données

Date : 2026-06-13. Une fiche par famille testée. Réponses : données disponibles ? fiables ?
signal trouvé ? horizon utile ? type de signal (prix/direction/vol/risque/score) ?
robustesse ? risque de fuite ? verdict ? action. Verdicts : KEEP / IMPROVE / FRAGILE /
REJECT / DATA_BLOCKED / LEAKAGE_RISK / NOT_WORTH_YET.

---

## 1. Prix / indicateurs techniques / benchmarks (EXT025, EXT011)
- **Disponibles / fiables** : oui (CBOT continu propre).
- **Signal** : la **random walk est imbattable en RMSE** (0/36 couples benchmark×horizon, DM
  p<0.10). Le trend-following (EWMAC, MA, momentum) a **DA < 0.5** sur le maïs (Sharpe ≤ 0.20).
- **Horizon / type** : référence à tous horizons ; aucun signal de prix exploitable.
- **Robustesse / fuite** : très robuste (négatif) ; aucun risque de fuite.
- **Verdict** : **KEEP (benchmark RW)** ; **REJECT (trend-following)**.
- **Action** : garder RW/drift/trend comme planchers de référence ; ne pas prédire le prix.

## 2. Contrat continu / roll (EXT006)
- **Disponibles / fiables** : CBOT par-expiry **fiable** (pas d'artefact détecté) ; **EMA
  front raw NON fiable** (saut 10,2 €/t/roll, 6,6×, 27/68 flips de momentum) ; `adjusted` OK ;
  reconstruction historique volume-based **bloquée** (front-only).
- **Signal** : hygiène, pas de signal direct.
- **Verdict** : **IMPROVE** (règle d'hygiène) + **DATA_BLOCKED** (reconstruction).
- **Action** : features de retour EMA sur `adjusted_price` ou hors jours de roll ; auditer la
  série amont de `basis_z` (ticket projet).

## 3. WASDE / USDA (EXT007, EXT008, EXT026, EXT024)
- **Disponibles / fiables** : vintage publication-réelle **construit et validé** (EXT026,
  24/24) ; **fuite ~8 j corrigée** dans le vintage (la série interne quotidienne reste à
  recaler côté projet).
- **Signal** : les **niveaux de bilan / stocks-to-use** (état d'offre lent) donnent un gain
  **directionnel** stable (+6,1 pts DA H20, et porteur à H40/H90 via EXT024) ; **mais RMSE
  dégradé** (niveaux non-stationnaires). La **surprise** WASDE (révisions M-M-1, sans
  consensus analystes) **dégrade** RMSE et DA (−16 pts).
- **Horizon / type** : H20-H90, **direction** uniquement.
- **Robustesse** : modérée (stable 2 moitiés, DM non significatif).
- **Verdict** : **IMPROVE** (niveaux/stocks-to-use, à ré-encoder stationnaire) ; **REJECT**
  (surprise proxy) ; **KEEP** (pipeline vintage = infra).
- **Action** : `s2u_z`, `s2u_pctile`, `s2u_slow_chg` en cible direction ; sourcer un
  consensus analystes pour rouvrir la surprise.

## 4. Crop Progress / Crop Condition (EXT019, EXT024, EXT015 ; EXT027 non lancé)
- **Disponibles / fiables** : NASS Crop Condition hebdo, public, daté (lundi 16 h ET → J+1).
  Fiable et anti-fuite.
- **Signal** : **le meilleur signal fondamental directionnel** — good/excellent (anomalie,
  déviation 5 ans, poor/very-poor) à **H90 : DA 0.669, AUC 0.724, stable (0,632/0,707)**,
  +4,4 pts vs marché (EXT019) / +6,6 pts (EXT024 corrigé). EXT015 confirme que ces variables
  ressortent train-only **16/16 ans**. Nul à court terme.
- **Horizon / type** : **H90** (et H40), **direction / score de vente**.
- **Robustesse** : la meilleure du programme, mais reste modeste (DM non significatif, IC
  chevauche le marché) → **score de confiance**, pas signal binaire fort.
- **Fuite** : aucune (corrigée étape 5 bis).
- **Verdict** : **IMPROVE (fort)**.
- **Action** : pivot central du score de vente H90 ; tester EXT027 (surprises hebdo) en
  complément.

## 5. Météo réalisée (EXT001, EXT002, EXT020)
- **Disponibles / fiables** : oui (Open-Meteo, datée J+1).
- **Signal** : **aucun** — toutes les formes (fenêtres agronomiques, lags/anomalies, extrêmes)
  **dégradent le RMSE** (R² OOS jusqu'à −3,4) avec DA négligeable/instable. **Price-in par
  anticipation** (confirme V45).
- **Type** : descripteur de **contexte** seulement (basis moins compressible en été de stress).
- **Verdict** : **REJECT** (comme prédicteur).
- **Action** : garder en contexte ; la seule voie prédictive est la météo **prévue** (EXT033).

## 6. COT (EXT003)
- **Disponibles / fiables** : COT Disaggregated, calendrier vendredi **prouvé** (anti-fuite OK),
  éval 2016+.
- **Signal** : **aucun** — Managed Money (net z, flux, percentiles, concentration) **dégrade**
  RMSE et DA à tous horizons. Aucun signal de second ordre.
- **Verdict** : **REJECT** (dossier COT clos honnêtement).
- **Action** : ne pas forcer ; rien à sourcer de plus en quotidien.

## 7. Futures curve / spreads (EXT005)
- **Disponibles / fiables** : **NON** — pas de contrats CBOT par maturité (front-only) ;
  courbe EMA accumulée seulement ~2 semaines.
- **Signal** : non testable (spread nearby-deferred, full carry, contango/backwardation).
- **Verdict** : **DATA_BLOCKED**.
- **Action** : sourcer des contrats CBOT par maturité + accumuler ≥250 j de courbe.

## 8. Ethanol / DDG / énergie (EXT004)
- **Disponibles / fiables** : partiel — pas de prix éthanol ni DDG ; seulement proxys
  (demande EIA, ratios énergie-corn).
- **Signal** : **aucun** — les proxys dégradent RMSE et DA (conforme V39-E3/E5).
- **Verdict** : **REJECT (proxys)** / PARTIAL_DATA.
- **Action** : sourcer prix éthanol (CME/EIA) + DDG (AMS) pour une vraie marge crush.

## 9. Basis / transmission spot-futures (EXT013, VECM)
- **Disponibles / fiables** : **NON** — pas d'EUR/USD quotidien historique (basis €/t non
  reconstructible) ; pas de spot UE quotidien (COMEXT mensuel).
- **Signal** : non testable (vitesse d'ajustement VECM, formalisation de V21).
- **Verdict** : **DATA_BLOCKED**.
- **Action** : sourcer FRED `DEXUSEU`/ECB (eurusd) + FranceAgriMer/Bologne (spot UE).

## 10. Volatilité (EXT009, EXT010)
- **Disponibles / fiables** : oui (retours CBOT).
- **Signal** : **SOLIDE** — **HAR** et **EGARCH** battent la RW de vol et rolling-20 sur
  RMSE/MAE/QLIKE **à tous les horizons** (−22 à −24 % RMSE à H90). EGARCH capte l'asymétrie.
  Le **filtre de vol** est actionnable : dans le décile haut de vol prévue, le score
  directionnel **s'inverse (DA 0,41, PnL<0)** ; le filtrer fait passer la DA de 0,669 à 0,699.
- **Horizon / type** : H20-H90, **volatilité / risque** (gate).
- **Robustesse** : la **plus solide** du programme.
- **Verdict** : **KEEP** (les deux).
- **Action** : brique de risque du score de vente (HAR par simplicité, EGARCH si asymétrie).

## 11. Régimes de marché (EXT017)
- **Disponibles / fiables** : oui (régimes définis sur info passée : vol, tendance, bilan,
  condition, saison, proximité WASDE).
- **Signal** : **hétérogène** — fort en **uptrend** (balanced 0,723), **low-vol** (0,694),
  **bilan extrême** (loose 0,738) ; **nul** en neutre/normal/good-crop (≈ hasard).
- **Horizon / type** : H90, **conditionnement** de la confiance directionnelle.
- **Robustesse** : à valider en forward (découpage post-hoc, risque d'overfitting modéré).
- **Verdict** : **IMPROVE**.
- **Action** : moduler la confiance du score selon le régime ; **ne pas** fitter un modèle par
  régime ; valider le filtre en forward.

## 12. Modèles avancés (EXT024, EXT015, EXT014, EXT050, EXT016, EXT012)
- **Supply-demand logit (EXT024)** : meilleur modèle directionnel, **parcimonieux** → IMPROVE.
- **Sélection de variables (EXT015)** : valide la parcimonie (top-6 > RF) → KEEP (diagnostic).
- **BMA (EXT014)** : robustesse seulement, ne dépasse pas le meilleur membre → IMPROVE (filet).
- **Stacking (EXT050)** : **sur-apprend**, instable → REJECT.
- **NBEATSx / DL (EXT016)** : non justifié, sur-apprentissage attendu → NOT_WORTH_YET.
- **OU mean-reversion (EXT012)** : cible basis stationnaire absente → DATA_BLOCKED.
- **Message transversal** : **la complexité n'apporte rien** ici ; avec un edge faible, la
  **parcimonie gagne**.

---

## Tableau récapitulatif

| Famille | Données | Signal | Horizon | Type | Robustesse | Fuite | Verdict |
|---|---|---|---|---|---|---|---|
| Benchmarks prix / trend | OK | RW imbattable ; trend KO | tous | prix | très robuste (nég.) | none | KEEP (RW) / REJECT (trend) |
| Roll / série continue | OK (CBOT) / bloqué (reconstr.) | hygiène | tous | — | stable | none | IMPROVE + DATA_BLOCKED |
| WASDE niveaux / stocks-to-use | OK (vintage) | direction modeste | H20-H90 | direction | modérée | none (corrigé) | IMPROVE |
| WASDE surprise | OK | dégrade | — | — | — | none | REJECT |
| Crop Condition | OK (public) | **meilleur dir.** | H90 | direction/score | la meilleure (modeste) | none | **IMPROVE (fort)** |
| Météo réalisée | OK | aucun (price-in) | — | contexte | robuste (nég.) | none | REJECT |
| COT | OK (2016+) | aucun | — | — | robuste (nég.) | none | REJECT |
| Futures curve | **absente** | non testable | — | — | — | — | DATA_BLOCKED |
| Ethanol/DDG | proxys seuls | aucun | — | — | — | none | REJECT |
| Basis / VECM | **absente** | non testable | — | — | — | — | DATA_BLOCKED |
| Volatilité (HAR/EGARCH) | OK | **solide** | H20-H90 | vol/risque | **la plus solide** | none | **KEEP** |
| Régimes | OK | hétérogène | H90 | conditionnement | post-hoc | none | IMPROVE |
| Modèles complexes (stack/DL) | OK | sur-apprend | — | — | instable | none | REJECT / NOT_WORTH_YET |
