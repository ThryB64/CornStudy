# EXT002 — Résultats : lags et anomalies météo

**Verdict : REJECT.**

## Résultats (BASE vs BASE+FAMILLE)

| H | RMSE base | RMSE +fam | ΔRMSE % | R² base | R² +fam | ΔDA | DM p |
|---|---|---|---|---|---|---|---|
| 5 | 0.0392 | 0.0401 | +2.2 % | +0.002 | −0.042 | +0.001 | 0.001 |
| 20 | 0.0790 | 0.0837 | +6.0 % | +0.015 | −0.106 | +0.015 | 0.026 |
| 40 | 0.1069 | 0.1145 | +7.1 % | +0.031 | −0.113 | +0.029 | 0.196 |
| 90 | 0.1579 | 0.1852 | +17.3 % | +0.051 | −0.306 | −0.013 | 0.038 |

## Lecture
Même conclusion qu'EXT001, dégradation moins violente mais réelle : RMSE pire à tous les
horizons, R² qui retombe en négatif. Le seul point d'intérêt est un gain de DA à H20-H40
(+1.5 à +2.9 pt) — mais il s'accompagne d'un RMSE significativement pire (R² négatif) et
disparaît à H90 (−1.3 pt). Signal directionnel marginal, non robuste, non exploitable car
l'erreur quadratique se dégrade.

## Conclusion
**REJECT.** Les anomalies/lags de météo réalisée n'aident pas la prévision de retour. Le
petit gain de DA à moyen horizon est trop fragile (un horizon, RMSE en regard négatif)
pour valoir mieux qu'IMPROVE, et le critère KEEP exige RMSE meilleur — non rempli.
Aligné sur V45.
