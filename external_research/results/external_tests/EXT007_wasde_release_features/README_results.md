# EXT007 — Résultats : features de rapports WASDE

**Verdict : IMPROVE** (signal directionnel partiel et stable ; encodage à revoir).

## Protocole
Source unique = vintage EXT026 (`available_from` = publication+1BD, valeurs telles
que publiées). Features : 6 niveaux de bilan (ending_stocks, stocks_to_use_ratio,
production, exports, use_total, avg_farm_price) forward-fill + dummies calendrier
(jour WASDE, jours depuis/avant, Grain Stocks, Acreage, fenêtre post-rapport). BASE
marché seul vs BASE+WASDE, log-retour CBOT.

## Résultats (BASE vs BASE+FAMILLE)

| H | ΔRMSE % | R² base→fam | ΔDA | DM p |
|---|---|---|---|---|
| 5 | +3.0 % | −0.002→−0.06 | **+0.033** | 0.027 |
| 20 | +10.7 % | +0.006→−0.13 | **+0.061** | 0.177 |
| 40 | +24.0 % | +0.023→−0.31 | **+0.031** | 0.211 |
| 90 | +194 % | +0.05→−2.7 | +0.021 | 0.042 |

### Stabilité directionnelle (2 sous-périodes) — ΔDA
| H | 1re moitié | 2e moitié |
|---|---|---|
| 5 | +0.026 | +0.039 |
| 20 | +0.054 | +0.067 |
| 40 | +0.043 | +0.019 |
| 90 | +0.110 | −0.068 |

## Lecture
Deux signaux opposés, à séparer proprement :
- **Direction : signal réel et STABLE** à H5/H20/H40 (+2.6 à +6.7 pts de DA dans *les
  deux* sous-périodes). Les variables qui portent le gain sont économiquement sensées :
  prix ferme, usage total, exports, stocks de fin, stocks-to-use, et le compteur
  `days_since_last_wasde`. Le bilan WASDE encode bien un *état fondamental lent* avec un
  biais directionnel.
- **Magnitude : dégradée.** Le RMSE empire (jusqu'à +194 % à H90) car les niveaux bruts
  (stocks, production) sont fortement non-stationnaires : standardisés en expandant, ils
  extrapolent mal et explosent l'erreur quadratique. R² OOS négatif.

## Conclusion
**IMPROVE, pas KEEP.** Le critère KEEP exige un RMSE meilleur ET DM p<0.10 dans le bon
sens : non rempli (RMSE pire). Mais le gain de DA est trop stable et trop sensé pour un
REJECT. Action étape 5 : (1) ré-encoder les variables en formes stationnaires
(stocks-to-use en z-score expandant, déviations vs moyenne de campagne, ratios) plutôt
qu'en niveaux ; (2) tester en cible *directionnelle/classification* (où le gain se voit)
plutôt qu'en RMSE de niveau ; (3) garder les dummies calendrier (ex ante, sans fuite)
pour moduler le veto WASDE V9. Cohérent avec la littérature : l'effet WASDE sur le prix
est surtout un état de bilan (lent) ; la *surprise* intraday n'est pas captable en
quotidien (cf. EXT008).
