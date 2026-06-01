# V45 — Météo & stress cultural : la météo future explique-t-elle le cours ?

Session 2026-06-01. On ajoute l'étude météo demandée, faite proprement et **anti-leakage**. Idée
agronomique : un stress hydrique/thermique sur la fenêtre critique du maïs (pollinisation ~juillet US)
réduit le rendement attendu → le CBOT monte. `RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé. Règle figée
inchangée. Module `src/mais/research/v45_weather_crop_stress.py`, tests (2 PASS), artefacts `artefacts/v45/`.

## Indice de stress cultural US (causal, phénologique)
`crop_stress_index` combine 4 composantes connues à J (z expandant + `shift(1)`) : chaleur
(`wx_belt_tmax_c_anom_z`), déficit de pluie 14 j, anomalie de précip 30 j (inversée), sécheresse
(`drought_composite`). Pondéré par la **phénologie** : juillet 1.0, juin 0.7, août 0.8, mai 0.4, … (la
fenêtre pollinisation/remplissage est critique). `heat_days_38c` ignoré (toujours 0 dans le corn belt).

## DÉCOUVERTE centrale : la météo RÉALISÉE est déjà price-in

**E1 — stress US réalisé → CBOT (H=20 j) :**
- `corr(stress, rendement CBOT futur) = −0.071` (légèrement NÉGATIF)
- rendement futur : stress élevé **−2.8 %** vs stress bas **−1.1 %** (n=826 en fenêtre critique)
- `OOF AUC (CBOT up) = 0.508` ≈ hasard → `US_STRESS_WEAK_PREDICTOR`

→ **Le stress météo une fois RÉALISÉ et connu n'annonce PAS une hausse du CBOT — il tend même à précéder un
léger repli.** C'est cohérent avec un marché efficient : le CBOT price la météo par **anticipation
(prévisions)**, pas quand le stress est déjà constaté. Quand la sécheresse est visible (juillet), le rallye
a déjà eu lieu et le marché se retourne souvent (effet saisonnier de récolte qui suit). 

**Conséquence professionnelle, qui REFORMULE l'idée initiale** : la valeur prédictive de la météo n'est PAS
dans la météo réalisée mais dans la **prévision/anticipation** — d'où la nécessité d'un **archive de
prévisions daté à l'émission** (ci-dessous). L'intuition « sécheresse → ça monte » est vraie *au moment où
la prévision se dégrade*, pas quand la sécheresse est déjà dans les données.

**E2 — stress US & compression d'un basis haut (H=40 j) :**
- basis haut + stress US ÉLEVÉ → compression **+4.1 €/t** ; stress US BAS → **+9.2 €/t**.
- → un stress US élevé (été) va de pair avec une compression PLUS FAIBLE du basis. Le stress d'été est donc
  un **contexte de prudence** (prime globalement justifiée par le risque météo, moins compressible),
  cohérent avec le thème « prime justifiée = ADVERSE-prone » (V37/V40) mais côté CBOT/global.

## Forward : archive de prévisions (anti-leakage par construction)
`collect_weather_forecast_forward` appelle l'API Open-Meteo Forecast (US corn belt + EU), calcule un
**indice de stress prévu** (lead 1-10 j : chaud + sec) et l'écrit dans un **journal append-only daté à
l'émission** (`data/official_forward/weather_forecast_journal.jsonl`) — l'équivalent météo du forward EMA.
Amorcé en réel le 2026-06-01 : **stress prévu US 27.4, EU 22.7** (réseau OK). C'est la SEULE façon
non-fuitée de tester l'anticipation : on accumule jour après jour ce qui était *prévu* à J.

## Limites honnêtes (data-gated, non simulées)
- Le master ne contient que la météo **US réalisée** : le **stress EU** (qui justifierait un basis haut) est
  data-gated et n'existe qu'en **forward** (collecteur EU) → à mesurer en accumulant le journal.
- L'archive historique de prévisions (Open-Meteo historical-forecast) **time out** → on accumule le forward.
- E1 peut être en partie confondu avec la saisonnalité (stress concentré en juillet, repli CBOT post-juillet) :
  à départager avec l'archive de prévisions et le contrôle saisonnier.

## Est-ce que ça apporte quelque chose ?
**Oui, mais pas comme prévu.** Ça n'apporte PAS un prédicteur de hausse via la météo réalisée (négatif
honnête, marché efficient). Ça apporte : (1) une **reformulation propre** (la météo se joue en anticipation
→ forward forecast archive), (2) un **contexte de prudence** (stress d'été = basis moins compressible),
(3) une **infrastructure forward** anti-leakage prête à valider l'anticipation météo. Aucune touche à la règle.
