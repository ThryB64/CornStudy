# Décision & prochaines étapes après V30 (2026-05-31)

Document décisionnel (pas un artefact). Référence pour ne pas tourner en rond. Baseline figée
`MaizePremiumIndicator_RESEARCH_V1` (cf. `FROZEN_BASELINE.md`). Statut `RESEARCH_ONLY_NOT_TRADING`.

## 1. Ce qui est VALIDÉ
- Thèse centrale : la bonne variable n'est pas le prix EMA brut mais le **basis EMA/CBOT** ; un basis haut
  tend à se comprimer. Mean-reversion confirmée (demi-vie ~17 j, V10).
- Précision V21/V29 : **short premium ≈ pari de rattrapage CBOT** (compression surtout CBOT_DRIVEN, 54-59 %).
- Audit data propre (V24), conversion CBOT→EUR/t correcte, contrats H/M/Q/X, leakage propre, rebuild cohérent.
- Source EMA officielle débloquée et live (V26), journal forward append-only (V27), pipeline daily
  `PASS_WITH_WARNINGS` (V22), courbe officielle caractérisée (V30).
- **V32 (nouveau) : le chemin ADVERSE est PARTIELLEMENT prévisible à l'entrée (LOO AUC 0.72)** — les pertes
  ne sont pas aléatoires. Signature : entry_z plus bas + basis_level plus bas (les primes modérées échouent,
  les extrêmes compriment — cohérent V15).

## 2. Ce qui est REJETÉ (honnêtement)
- Meta-models lourds / deep learning / H90 / EMA up-down brut (V8, V10, V18).
- Aucune famille de la littérature ne bat `basis_z + saison` (V18, 4 confirmations).
- Filtre de régime CBOT en veto (V11/V23). Macro n'explique pas le basis (V16, R² OOF négatif).
- **V35 (nouveau) : prédire le MÉCANISME de compression (CBOT_DRIVEN vs EMA_DRIVEN) par trade = NON
  prévisible (LOO AUC 0.48 ≈ hasard).** On affiche « compression souvent par rattrapage CBOT » comme
  contexte général, pas une prédiction par signal.
- drawdown_risk CBOT comme veto (V29-C : pas de dégradation, reste contexte).

## 3. Ce qui est BLOQUÉ par la data
- **Validation date-par-date proxy vs officiel** : besoin d'historique officiel accumulé (V37).
- **Étude courbe officielle (V33)** : 1 snapshot seulement ; besoin de jours officiels.
- **Archive météo prévue réelle (V34)** : host historical-forecast time out dans cet env ; l'API forward
  `forecast` marche → accumuler forward. Tant que synthétique → `METHODOLOGY_DEMO_SYNTHETIC`, jamais publié.
- **Drivers physiques Europe (V36)** : `ec_mars`, `franceagrimer`, `eu_cross_assets` (TTF) existent en raw
  mais NE sont PAS mergés dans le master (pas de colonnes EU physiques alignées). Intégration requise avant test.

## 4. Ce qui passe en FORWARD (suivi, pas modélisation)
- Journal officiel quotidien (V27) branché dans `ops/daily.py` (step `official_forward`).
- Dashboard forward (V31) : date | basis | z | tier | courbe | warnings | objectifs | statut.
- Bascule auto `basis_z_official_rolling` à ≥ 40 jours.

## 5. Ce qu'on NE MODIFIE PLUS (gel pendant le forward)
- Paliers basis_z (1 / 1.5 / 2), objectifs z→0.5 et z→0, stop −20/−25, warnings.
- Aucune optimisation de seuil a posteriori. Holdout 2024 jamais utilisé pour choisir une règle.
- Le module `daily_snapshot` (SELL_THIRDS / cash / stockage) est un **PROJET 2 distinct** — non mélangé au
  PROJET 1 (indicateur premium). Le dashboard V31 ne mélange pas les deux.

## 6. Ce qu'on EXPLORE ENCORE (sans toucher la règle)
- **V32 → score ADVERSE_RISK** comme CONTEXTE : si élevé (z modéré + basis bas), viser z→0.5 seulement,
  prudence sur z→0. À re-tester en forward (plus de trades).
- **V33** courbe officielle (quand jours suffisants) : basis haut + backwardation nearby vs contango.
- **V34** archive météo réelle : la météo aide-t-elle à savoir si un basis haut est justifié/compressible ?
- **V36** drivers physiques EU (après intégration) : un basis haut se comprime-t-il moins si tension EU réelle ?
- **V35-bis** : le mécanisme n'est pas timable, mais surveiller si le forward officiel le confirme.

## 7. Conditions research → paper trading
1. ≥ 3-6 mois de journal officiel forward cohérent avec les backtests (tier, fréquence).
2. `basis_z_official_rolling` disponible (≥ 40 j) et proche de l'implied proxy (V37).
3. Aucune dérive majeure proxy vs officiel sur le basis.
4. Score ADVERSE_RISK qui tient en forward (réduit réellement les pertes).

## 8. Conditions paper trading → trading réel (NON réunies, lointaines)
1. ≥ 12 mois de paper trading forward avec coûts réels + slippage mesurés.
2. PnL net positif après coûts réels (le mur ~3-4 €/t/leg doit être franchi en pratique).
3. Liquidité réelle vérifiée sur le contrat le plus liquide (Q/X), exécution du spread EMA/CBOT.
4. Validation officielle complète (historique officiel suffisant), pas proxy.
5. Gouvernance : règle figée respectée sur toute la période, track record auditable.

---
*Discipline : on arrête de chercher le modèle miracle. On valide en forward officiel et on explore
uniquement ce qui explique les échecs (ADVERSE, courbe, météo prévue, CBOT engine, physique EU).*
