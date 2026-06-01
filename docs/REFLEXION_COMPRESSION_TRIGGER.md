# Réflexion — phase Compression Trigger (déclencheur de retournement de la prime EMA/CBOT)

`RESEARCH_ONLY_NOT_TRADING`. Baseline `basis_z>1` figée. Holdout verrouillé. Aucun fit sur les 42 épisodes
pour le score ; la partie prédictive se teste sur le PANEL QUOTIDIEN (jours basis_z>1) en OOF.

> Note numérotation : les tickets sont labellisés **CT-01…CT-11** (vision utilisateur « V101-xx »). Comme
> V101/V102/V103 sont déjà pris (live fix / monitoring / dashboard), les modules code sont **v104-v106**.

## 1. Limite actuelle
L'indicateur dit : « la prime est trop haute → elle devrait finir par se comprimer ». Il ne dit pas QUAND la
compression commence, ni quel DÉCLENCHEUR apparaît juste avant. On passe de l'étude « zone de surchauffe » à
l'étude « déclencheur de retournement ».

## 2. Zone vs déclencheur — deux couches
- **Couche ÉTAT** (existante) : `basis_z>1` → prime excessive (MODERATE/STRONG/EXTREME).
- **Couche DÉCLENCHEUR** (nouvelle) : `COMPRESSION_TRIGGER ∈ {NONE, EARLY, CONFIRMED}` — y a-t-il un signe
  que la compression commence MAINTENANT ? On n'altère PAS la baseline ; on ajoute un diagnostic de timing.

## 3. Grande question
Quand `basis_z>1`, quels signaux apparaissent JUSTE AVANT que la compression commence ? Candidats : rattrapage
CBOT, essoufflement EMA, détente de la courbe EMA, retournement du ratio blé/maïs, météo prévue, volumes/OI,
catalyseurs (WASDE/COT/roll).

## 4. Hypothèses de déclencheur (économiques)
- **CBOT rebound** : le CBOT remonte (>SMA, momentum+, RSI sort d'oversold) → compression CBOT-driven.
- **EMA exhaustion** : l'EMA cesse de faire des hauts, volume/OI baissent → compression EMA-driven.
- **wheat/corn reversal** : le ratio blé/maïs se détend → prime feed moins justifiée → compression.
- **curve relaxation** : backwardation/front-next se détend → tension physique qui retombe.
- **weather** : US bullish (CBOT monte) / EU relief (EMA perd sa prime).

## 5. Variables candidates (toutes causales, connues à t)
basis_z, Δbasis 3/5j, CBOT ret 3/5/10j, dist SMA10/20/50, RSI14, EMA ret 3/5/10j, wheat/corn z & ret,
front-next spread, backwardation, OI/volume EMA, COT MM, vol CBOT, EUR/USD.

## 6. Risques de leakage (et protocole)
- `compression_start_date` utilise le futur relatif à l'entrée → **DESCRIPTIF uniquement**, JAMAIS une feature.
- La cible `compression_imminent_h{5,10,20}` est forward ; les FEATURES n'utilisent que l'info ≤ t (shift où
  besoin). OOF TimeSeriesSplit + embargo = horizon.
- Panel quotidien (jours basis_z>1) → n bien > 42, puissance correcte ; mais signaux autocorrélés → embargo
  et lecture prudente. Pas de multiplication de seuils ; banding fixe pour le score.

## 7. Méthode
1. CT-01 : définir `compression_start_date` (5 définitions, comparées).
2. CT-02 : event study t=−20..+10 autour du start → ce qui bouge AVANT.
3. CT-09 : cible `compression_imminent_h10` (panel) + OOF AUC des features causales.
4. CT-10 : `COMPRESSION_TRIGGER_SCORE` règle-basé (NONE/EARLY/CONFIRMED), validé (ADVERSE/timing).
5. CT-11 : ajouter au rapport quotidien.

## 8. Tickets
| Ticket | Sujet | Statut |
|---|---|---|
| CT-01 | compression_start_date (5 défs) | 🔨 v104 |
| CT-02 | event study before compression | 🔨 v105 |
| CT-03 | CBOT rebound trigger | 🔨 (folded into v105/v106) |
| CT-04 | EMA exhaustion trigger | 🔨 (folded) |
| CT-05 | wheat/corn reversal trigger | 🔨 (folded) |
| CT-06 | EMA curve relaxation trigger | ⚠️ (courbe data-gated récente, folded best-effort) |
| CT-07 | weather forecast trigger | ⛔ révisions non archivées (forward) |
| CT-08 | fundamental event trigger | ⛔ calendriers partiels (forward) |
| CT-09 | compression_imminent target | 🔨 v106 |
| CT-10 | compression_trigger_score | 🔨 v106 |
| CT-11 | add trigger score to daily report | 🔨 v106 |

## 9. Architecture cible de l'indicateur
PREMIUM_STATE · JUSTIFICATION_STATE · CBOT_SUPPORT · **COMPRESSION_TRIGGER** · TARGET_RECOMMENDATION ·
HORIZON · WARNINGS.

## 10. Pièges à éviter (rappel)
Pas de feature future ; pas de sur-optimisation sur 42 épisodes ; pas de multiplication de seuils ; ne pas
confondre corrélation a posteriori et prédiction réelle ; un trigger faible n'est pas un signal de trading.
Critère GO/WATCHLIST/NO_GO : un trigger n'est retenu (ADD_TO_DAILY_REPORT) que s'il améliore l'OOF du timing
de façon stable ET reste interprétable ; sinon WATCHLIST.

---

## Résultats (implémentation CT-01/02/09/10/11)
- **CT-01 (v104)** : 5 définitions de `compression_start_date` cohérentes (std ~2.7 j) ; offset entrée→start ~5 j (hors ADVERSE).
- **CT-02 (v105)** : event study → le basis fait un **OVERSHOOT** (blow-off) ; la hausse est **EMA-driven** (EMA surperforme jusqu'au pic, CBOT faible), la compression démarre quand l'**EMA se retourne** (figure `docs/COMPRESSION_TRIGGER_EVENT_STUDY.png`). Le « CBOT monte d'abord » N'EST PAS un précurseur propre. Verdict `NO_CLEAR_SINGLE_PRECURSOR` (relatif EMA/CBOT).
- **CT-09/10 (v106)** : panel quotidien (460 j basis_z>1), base rate compression imminente (Δz≥0.3 / 10 j) = **0.65** ; OOF AUC features causales = 0.578 (marginal). **DÉCOUVERTE CLÉ** : le `COMPRESSION_TRIGGER_SCORE` est **inversé** (NONE 0.79 > EARLY 0.65 > CONFIRMED 0.60) → les précurseurs détectables signalent une compression **déjà en cours**, pas à venir. Verdict `COMPRESSION_TRIGGER_REFLECTS_ONGOING_NOT_LEADING`.
- **CT-11** : bloc `Déclencheur de compression` ajouté au daily report comme **état descriptif** (compression amorcée ou non), pas un prédicteur.

## Conclusion de la phase
Timer le DÉBUT précis de la compression est **intrinsèquement difficile** (réversion quasi-efficiente) : le seul signal « leading » est le **taux de base élevé** de basis_z>1 (la prime haute se comprime souvent à 10 j). Les précurseurs (momentum basis qui se retourne, EMA qui s'essouffle, blé/maïs qui se détend) **coïncident** avec la compression plutôt qu'ils ne la **précèdent**. C'est un résultat honnête et important : il borne ce qu'on peut espérer du timing et oriente l'indicateur vers un **état** (« compression amorcée ») plutôt qu'une **prédiction** de déclenchement. CT-07/08 (météo prévue, événements fondamentaux) restent data-gated/forward.
