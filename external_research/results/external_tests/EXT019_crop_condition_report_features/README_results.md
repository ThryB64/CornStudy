# EXT019 — Résultats : USDA Crop Progress / Crop Condition

**Verdict : IMPROVE** (signal directionnel long-horizon stable ; nul à court terme).
Data status : **DATA_READY** (NASS Crop Progress hebdo 1980-2026 présent en interne).

## Protocole
Source `crop_progress.parquet` (hebdo, dimanche=semaine finissante). Publication NASS
lundi 16h ET → disponible mardi (`available = Date + 2 j`). Features : niveau et
variation good/excellent, anomalie par semaine de l'année (climatologie expandante),
surprise (Δ hebdo vs Δ attendu), poor/very-poor, gap d'avancement 5 ans, silking,
harvested. Cible : log-retour CBOT.

## Résultats (BASE vs BASE+FAMILLE)

| H | ΔRMSE % | ΔDA | DM p | ΔDA 1re moitié | ΔDA 2e moitié |
|---|---|---|---|---|---|
| 5 | +0.7 % | −0.006 | 0.041 | — | — |
| 20 | +1.2 % | −0.002 | 0.243 | — | — |
| 40 | +2.0 % | +0.018 | 0.313 | +0.004 | +0.032 |
| 90 | **+0.3 %** | **+0.044** | 0.892 | +0.042 | +0.045 |

## Lecture
Profil cohérent avec une variable d'**état d'offre lent** : aucun apport (voire léger
recul) à court terme (H5/H20), mais un gain de direction à H40 et surtout **H90 (+4.4 pts
de DA, stable dans les deux sous-périodes ~+4.2/+4.5)** avec un RMSE quasi neutre (+0.3 %).
La condition good/excellent et son anomalie saisonnière informent la tendance de fond
(une bonne récolte pèse plusieurs mois sur les prix). Le DM n'est pas significatif (p=0.89
à H90) : le signal est réel mais modeste.

## Conclusion
**IMPROVE.** Pas KEEP (RMSE non amélioré, DM non significatif), mais le gain directionnel
long-horizon est stable et économiquement sensé. Action étape 5 : tester crop condition
comme intrant d'un modèle *direction/risque long-horizon* (H40-H90) ou d'un score de
vente saisonnier, plutôt qu'en RMSE de niveau ; combiner avec WASDE stocks-to-use (EXT007,
même profil long-horizon). C'est, avec EXT007, l'un des deux seuls signaux fondamentaux
non triviaux de l'étape 4.
