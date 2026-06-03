# Périmètre PREMIUM vs LEGACY

Statut : RESEARCH_ONLY_NOT_TRADING. Ce document fixe le périmètre pour éviter la confusion historique.

## Le produit PREMIUM (le seul périmètre actif)

**Objet** : indicateur de prime EMA/CBOT (basis), explicable, forward, auditable.

- **Single source of truth** : `data/premium/premium_daily_head.json` (`mais.premium.head.build_premium_head`).
- **Signal** : journal officiel forward append-only (V27) — règle figée `basis_z`.
- **Contexte** : ADVERSE_RISK (V108), CBOT_SUPPORT (V107/V86), PHYSICAL_TENSION (V109/V125), substitution
  (V126), météo forecast (V127), objectif (V56/V131), horizon (V27×V130, estim. V138).
- **Synthèse** : V132 (intégrée) ; cohérence V122 ; fraîcheur V123 ; checkpoint V135.
- **Reporting** : `scripts/run_daily_collect.py` (premium-only), rapport mensuel V133.

Couches `REPORTING_ONLY` (peuvent être en retard, s'y référer pour l'historique mais pas comme « head ») :
V101, V99.

## LEGACY (hors périmètre premium — NE PAS mélanger)

Conservé pour l'historique de l'étude, mais **jamais affiché dans le head premium** :

- `src/mais/ops/daily.py` + commande CLI `mais daily-run` : pipeline farmer/cash
  (features→targets→audit→factors→train/study/backtest, décisions agriculteur).
- `src/mais/decision/` (rules/backtest **SELL_NOW**), `farmer_backtest.py`, `asymmetric_module.py`.
- Rapports « SELL_NOW / vendre / stocker » : décision agriculteur, sans rapport avec l'indicateur premium.

Règle : le head premium est `scope_clean` (aucune occurrence SELL_NOW/farmer/vendre/stocker). Le legacy doit
porter une bannière « LEGACY — hors périmètre premium » s'il est exposé.

## Pourquoi cette séparation

Un même dépôt portait deux projets ; un lecteur pouvait confondre un `SELL_NOW` agriculteur avec l'état de
l'indicateur de prime. La séparation rend l'étude lisible, auditable et défendable.
