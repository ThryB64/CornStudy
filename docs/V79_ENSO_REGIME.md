# V79 — Régime climatique ENSO (El Niño / La Niña) → CBOT

Session 2026-06-01. Extension CLIMAT de V51 : la météo quotidienne est anticipée (V48/V51), mais ENSO est un
régime LENT et persistant, donc potentiellement moins entièrement pricé à horizon saisonnier. Source NOAA CPC
ONI (ASCII). Anti-leakage : ONI décalé de 2 mois (centralisation 3 mois + publication) + shift(1) jour.
Descriptif, aucun fit, baseline figée inchangée. `RESEARCH_ONLY_NOT_TRADING`.

## Résultats
- **corr(ONI connu à J, rendement CBOT forward)** : −0.111 (20j), **−0.141 (60j)**, −0.098 (120j). Signe
  NÉGATIF attendu (La Niña = ONI bas = risque sécheresse = haussier maïs).
- **Rendement CBOT 60j par régime** : La Niña **+5.38 %**, Neutre −1.31 %, El Niño −1.04 % (écart La Niña−El
  Niño ≈ **+6.4 pts**).
- **Robustesse au confond crise** : la La Niña 2020-2022 chevauche le bull COVID/Ukraine. HORS 2020-2022,
  La Niña **+3.9 %** vs El Niño **+0.1 %** → l'effet **SURVIT** (`robust=True`, pas un simple artefact de crise).
- **Basis par régime** : La Niña 39.2 vs El Niño 34.3 €/t (modeste) → l'effet passe surtout par le **CBOT
  mondial**, pas par la prime EU (cohérent prime locale).

→ Verdict `ENSO_LA_NINA_BULLISH_ROBUST_EX_CRISIS_WATCHLIST`. **Le meilleur signal directionnel macro de
l'étude**, économiquement sensé et robuste au confond le plus évident.

## Caveats (honnêteté)
- **Peu d'épisodes indépendants** (~12 transitions ENSO sur la période) : la puissance effective est très
  inférieure à n_days (5939), les rendements 60j se chevauchent fortement.
- **ENSO est public et forecastable** des mois à l'avance → une partie est probablement déjà dans les courbes
  forward ; le réalisé décalé capte surtout la composante de régime persistante.
- C'est un **CONTEXTE macro-climatique**, pas un timing tradeable ni un veto. Il pourrait, au mieux, nuancer
  un biais directionnel CBOT de fond (et donc CBOT_SUPPORT) — à confirmer en forward.

## Place dans la thèse
Cohérent avec le reste : l'effet météo/climat sur le maïs passe par le **CBOT mondial** (offre), pas par la
**prime EU locale**. La Niña renforce le biais haussier CBOT → contexte plus porteur pour la compression du
basis (canal CBOT-driven, V70). Tests V79 PASS, ruff PASS.
