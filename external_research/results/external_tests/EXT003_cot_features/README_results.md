# EXT003 — Résultats : features COT (Managed Money disaggregated)

**Verdict : REJECT.** Data status : DATA_READY (COT Disaggregated 2013-2026, éval 2016+).

## Protocole
Source `cftc_cot.parquet` (hebdo, Date=mardi=positions). **Anti-fuite majeure** :
positions du mardi publiées le vendredi → disponible lundi suivant
(`available = Date + 6 j`, conservateur). Features : MM net/OI, PM net/OI, z-score
expandant et percentile du MM net, flux hebdo, OI z, long/short %, ratio
spéculateurs/commerciaux. Éval 2016+. Comparaison explicite à V18.

## Résultats (BASE vs BASE+FAMILLE)

| H | ΔRMSE % | ΔDA | DM p |
|---|---|---|---|
| 5 | +2.5 % | −0.019 | 0.035 |
| 20 | +9.3 % | −0.042 | 0.020 |
| 40 | +20.7 % | −0.087 | 0.016 |
| 90 | +28.5 % | −0.137 | 0.060 |

## Lecture
Les positions COT (y compris la décomposition Managed Money, que V18 n'avait pas testée)
**dégradent RMSE et DA** à tous les horizons, de façon significative dans le mauvais sens.
Aucun signal exploitable une fois la date de publication (vendredi) respectée.

## Conclusion
**REJECT.** Le dossier COT est désormais clos honnêtement : V18 n'avait falsifié que le
net total ; l'extension au Managed Money disaggregated, avec calendrier de publication
correct, ne révèle aucun signal de second ordre. Le positionnement spéculatif n'aide pas
la prévision de retour CBOT sur 2016-2023.
