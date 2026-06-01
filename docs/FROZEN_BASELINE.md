# Baseline figée — MaizePremiumIndicator_RESEARCH_V1

**Date de gel** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`.

Cette baseline est **figée**. À partir de maintenant, toute nouvelle idée doit être comparée à elle :
la question n'est plus « peut-on trouver un meilleur modèle ? » mais « cette idée améliore-t-elle
**clairement** cette baseline ? ». Aucune modification de la règle sans gain robuste démontré et,
idéalement, validation forward.

## Définition

**Modèle cœur** : régression logistique structurelle **2 variables** `basis_z + month_cos`, OOF purged
embargo 40j, calibration Isotonic train-only (AUC OOF 0.694, validée LOYO + red team p=0.0099).

**Signal (paliers)** sur `basis_z` (= z-score 52w du basis EMA/CBOT, construction causale rolling 260) :
- `NO_SIGNAL` si basis_z < 1
- `SHORT_PREMIUM_MODERATE` si 1 ≤ basis_z < 1.5
- `SHORT_PREMIUM_STRONG` si 1.5 ≤ basis_z < 2
- `SHORT_PREMIUM_EXTREME` si basis_z ≥ 2

**Sortie** :
- objectif prudent : `basis_z → 0.5` (efficacité capital)
- objectif complet : `basis_z → 0` (rendement)
- time stop : 90 jours
- stop indicatif : −20 à −25 €/t (un stop serré −10 détruit l'edge)

**Warnings (informationnels, pas vetoes)** :
- `DATA_STALE` (gate de fraîcheur : >5 j ouvrés → pas de signal)
- `ROLL_RISK` (mois de roll)
- `HIGH_VOL`
- `WEATHER_STRESS` (basis potentiellement justifié par un stress physique)
- `CBOT_DRAWDOWN_RISK` (contexte mondial)

**Contexte affiché (V21/V23)** : CBOT_UPTREND / NEUTRAL / BULLISH_WEATHER / RISK_OFF ; drawdown_risk ;
`compression_path_hint` (la compression vient surtout d'une hausse CBOT — 69%, jambe CBOT 6× jambe EMA).

## Performance de référence (research, hors holdout)

- Walk-forward strict 1-trade-à-la-fois, stop −20, coût dynamique : 32 trades, hit 0.66, net +138 €/t,
  max DD −40, 9/14 ans positifs.
- Portfolio strict coût 5 : 29 trades, hit 0.90, +116 €/t.
- Survit hors crises (coût 5) : +115 €/t (n=30).
- Rebuild de zéro (V24) cohérent : 47 trades, hit 0.851.

## Réserves permanentes

- EMA = 97% proxy exploratoire (historique) → research-only. Source officielle Euronext **débloquée**
  (V26) mais snapshot du jour seulement ; historique officiel à accumuler forward.
- Rentable jusqu'à ~3-4 €/t/leg ; fragile à 5 €/t en volume.
- Pas de validation forward longue. Pas de bot réel.

## Règle de gouvernance

1. La baseline ne change que si une idée obtient `ADD_TO_INDICATOR` robuste (delta AUC > +0.02 stable,
   ou amélioration nette du PnL net / loser-avoidance) ET ne dégrade aucune métrique clé.
2. Aucune optimisation de seuils a posteriori sans validation hors échantillon.
3. Holdout 2024 jamais utilisé pour choisir un modèle.
4. Toute conclusion reste `RESEARCH_ONLY_NOT_TRADING` tant que : source EMA officielle historique +
   forward ≥ 6-12 mois + coûts réels validés ne sont pas réunis.

## Enrichissements de contexte (V27/V29, règle inchangée)

- **V27** : suivi forward officiel branché dans le pipeline daily (`official_forward`). Chaque jour, le basis
  officiel Euronext + `basis_z_official_implied` (puis `_rolling` à ≥40j) sont journalisés append-only
  (`data/forward_journal/`). Le passé n'est jamais réécrit. Premier point live 2026-05-29 : SHORT_PREMIUM_EXTREME.
- **V29 — exploration C** : sous `drawdown_risk` CBOT élevé, pas de dégradation du short premium → `drawdown_risk`
  reste **contexte, pas veto**.
- **V29 — exploration D** : les pertes correspondent au chemin **ADVERSE** (le basis s'écarte au lieu de se
  comprimer, win 0.00). La compression profitable est surtout `CBOT_DRIVEN` (54 %, win 1.00) — confirme V21.
  Warning utile : surveiller un basis qui s'écarte après l'entrée (signature de perte), sans sur-filtrer a priori.

*Baseline gelée 2026-05-31. Référence unique pour toute comparaison ultérieure. V27/V29 n'ont pas modifié la règle.*
