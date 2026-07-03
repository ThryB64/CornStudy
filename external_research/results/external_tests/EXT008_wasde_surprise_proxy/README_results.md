# EXT008 — Résultats : proxys de surprise WASDE (révisions)

**Verdict : REJECT.**

## Protocole
Révisions M-M-1 (vintage EXT026) de 7 variables de bilan + surprise standardisée
(révision / vol expandante des révisions) + direction de surprise du bilan. Aucune
attente analyste → ce ne sont **pas** de « vraies » surprises de marché.
Note : l'évaluation tombe à n≈700-750 car l'intersection des révisions non-NaN
(avg_farm_price absent des rapports d'hiver) ampute l'échantillon — limite documentée.

## Résultats (BASE vs BASE+FAMILLE)

| H | ΔRMSE % | ΔDA | DM p |
|---|---|---|---|
| 5 | +3.0 % | −0.021 | 0.124 |
| 20 | +9.0 % | −0.092 | 0.063 |
| 40 | +22.5 % | −0.157 | 0.031 |
| 90 | +24.8 % | −0.136 | 0.019 |

## Lecture
Les révisions dégradent **RMSE et DA** à tous les horizons (DA jusqu'à −16 pts), de façon
significative dans le mauvais sens. Aucun signal exploitable. Contraste net avec EXT007 :
ce sont les *niveaux* de bilan (état lent) qui portent un peu de direction, pas les
*révisions* (la « surprise »).

## Conclusion
**REJECT.** Cohérent avec Huang-Serra-Garcia : l'ajustement à la surprise WASDE est
intraday et non captable en quotidien ; sans attentes analystes, le proxy révision n'est
qu'un bruit retardé. Le dossier surprise WASDE est clos côté quotidien.
