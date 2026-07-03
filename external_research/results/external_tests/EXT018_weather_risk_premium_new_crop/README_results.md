# EXT018 — Résultats : prime de risque météo new-crop

**Data status : PARTIAL_DATA** (contrats décembre CBOT absents).
**Verdict : descriptif CONFIRMÉ ; prédictif REJECT.**

## Limite de données
Pas de contrats décembre CBOT par année en interne (confirmé par EXT006). Le test
new-crop strict est impossible. Approximation : série continue + saisonnalité,
conditionnée par stocks-to-use (WASDE vintage) et stress météo d'été.

## Volet 1 — réplication descriptive (Janzen / Li-Hayes-Jacobs)
Retour forward 90 j moyen du CBOT par mois pré-récolte, années de stress (canicule
juillet > médiane) vs normales :

| Mois | Année normale | Année de stress |
|---|---|---|
| Avril | −0.083 | **+0.237** |
| Mai | −0.086 | **+0.204** |
| Juin | −0.069 | **+0.216** |
| Juillet | −0.024 | −0.048 |
| Août | +0.057 | −0.134 |
| Sept | +0.074 | −0.050 |

**La prime météo existe et se comporte exactement comme dans la littérature** : en année
normale, le prix tend à baisser du printemps à l'été (prime qui se dissipe → biais
baissier pré-récolte) puis se redresse vers la récolte ; en année de stress, rally
estival (printemps fortement positif) suivi d'un repli post-pollinisation. Le SIGNE du
retour pré-récolte est conditionné par le caractère stress/normal de l'année.

## Volet 2 — test prédictif conditionnel (harnais)
| H | ΔRMSE % | ΔDA | DM p |
|---|---|---|---|
| 5 | +11.6 % | −0.001 | 8e-05 |
| 20 | +56.4 % | −0.043 | 0.058 |
| 40 | +85.7 % | −0.078 | 0.149 |
| 90 | +419 % | −0.092 | 0.030 |

Le test prédictif **échoue (REJECT)** : RMSE explose, DA recule.

## Lecture — pourquoi le descriptif marche mais pas le prédictif
Le classement « année de stress » repose sur la canicule de **juillet**, information connue
seulement *pendant/après* l'été. Au printemps (date de décision), on ne sait pas si l'été
sera chaud → la prime n'est pas exploitable *ex ante*. C'est précisément le constat V45 :
on ne prédit pas le rally météo à partir de l'information de printemps. Le seul levier
prédictif possible serait les **révisions de prévisions météo** (EXT033), pas le réalisé.

## Conclusion
**PARTIAL_DATA + descriptif confirmé.** La prime de risque météo new-crop est réelle et
documentée ici (réplication propre), mais non exploitable en prédiction sans (a) les
contrats décembre, (b) un flux de prévisions météo forward (EXT033). Parallèle structurel
fort avec notre prime EMA (short premium = pari sur dissipation hors stress). Action étape
5 : sourcer les contrats Dec CBOT + brancher EXT033 ; EXT042 (corrélation prime US ↔ EMA)
en P2.
