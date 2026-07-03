# EXT020 — Résultats : événements météo extrêmes

**Verdict : REJECT.**

## Résultats (BASE vs BASE+FAMILLE)

| H | RMSE base | RMSE +fam | ΔRMSE % | R² base | R² +fam | ΔDA | DM p |
|---|---|---|---|---|---|---|---|
| 5 | 0.0373 | 0.0492 | +31.9 % | +0.016 | −0.712 | −0.007 | 1.5e-05 |
| 20 | 0.0731 | 0.1577 | +115.8 % | +0.057 | −3.391 | +0.010 | 0.034 |
| 40 | 0.1016 | 0.1945 | +91.5 % | +0.100 | −2.302 | −0.040 | 0.139 |
| 90 | 0.1440 | 0.2147 | +49.1 % | +0.185 | −0.811 | −0.097 | 0.173 |

## Lecture
Le pire des trois blocs météo. Les indicateurs d'extrêmes (canicule, streaks, stress de
stade) produisent des coefficients très instables : R² OOS s'effondre (jusqu'à −3.4),
RMSE plus que doublé à H20-H40. La DA recule à la plupart des horizons. Les épisodes
extrêmes sont rares (peu d'observations informatives) et fortement saisonniers, ce que le
Ridge surinterprète.

## Conclusion
**REJECT, sans ambiguïté.** Les événements extrêmes réalisés ne prédisent pas le retour
CBOT — ils sont soit anticipés (price-in), soit trop rares pour estimer un effet stable.
Confirme V45 et le caractère non prévisible du mécanisme (cf. V35). La météo extrême
peut rester un descripteur de *contexte* (basis moins compressible en été de stress,
note V45) mais pas un prédicteur de direction.
