# Indicateur agriculteur

## Objectif

Donner à un agriculteur une recommandation actionnable :

- **SELL_NOW** : vendre tout (ou la fraction définie) au prix cash actuel
- **SELL_THIRDS** : vendre 1/3 maintenant, garder le reste
- **SELL_THIRDS_OVER_60_DAYS** : DCA classique (1/3 par mois pendant 3 mois)
- **STORE** : tout garder en stock
- **WAIT** : ne rien faire (signal trop incertain)

## Architecture

```
predictions modèle  ──┐
                     ▼
config/decision.yaml ──── src/mais/decision/rules.py ──── advise() ──── Recommendation
                     ▲
profil agriculteur ──┘
```

Voir [config/decision.yaml](../config/decision.yaml) pour les règles.

## Inputs attendus du méta-modèle

Le module `decision/` consomme :

| Variable | Description | Source |
|---|---|---|
| `p_up_strong_h{H}` | proba que P_{t+H} > P_t * 1.05 | classification binaire calibrée |
| `p_down_strong_h{H}` | proba que P_{t+H} < P_t * 0.97 | classification binaire calibrée |
| `q10_h{H}, q50_h{H}, q90_h{H}` | quantiles du prix prédit | régression quantile / conformal |
| `regime` | `bull` / `range` / `bear` / `unknown` | Markov-switching |
| `p_t` | prix actuel CBOT | spot |

## Profil agriculteur

```yaml
default:
  location_state: iowa
  storage_capacity_bushels: 50000
  storage_cost_usd_per_bu_per_month: 0.04
  cash_flow_constraint: medium
  risk_aversion: medium
  basis_local_typical_usd_per_bu: -0.20
```

Les règles peuvent référencer ces paramètres :

```yaml
- id: cashflow_urgency_override
  condition: "farmer_profile.cash_flow_constraint == 'high'"
  action: SELL_NOW
  sell_fraction: 0.5
```

## Règles par défaut (dans l'ordre de priorité)

1. **stop_loss_emergency** — `p_down_strong_h10 > 0.65 OR regime == 'bear'` → SELL_NOW (100%)
2. **strong_uptrend** — `p_up_strong_h20 > 0.6 AND regime == 'bull'` → STORE (0%)
3. **high_uncertainty** — `(q90 - q10) / q50 > 0.20` → SELL_THIRDS (33%)
4. **cashflow_urgency_override** — profil `cash_flow_constraint == 'high'` → SELL_NOW (50%)
5. **storage_economics_negative** — espérance de gain < coût stockage → SELL_NOW (70%)
6. **default_dca** — sinon → SELL_THIRDS_OVER_60_DAYS

## Backtest agronomique

`mais backtest --horizon 20 --state iowa` simule sur 2010-2024 :

1. À chaque récolte (mi-octobre), `initial_inventory_bushels` rentre en stock
2. Chaque jour ouvré, on demande une recommandation au moteur de règles
3. SELL liquide au cash price (`p_t + basis_local`), STORE incurre le storage cost
4. À la prochaine récolte, force-liquidation du résidu
5. On compare à 4 stratégies baseline :
   - **sell_at_harvest_100** : tout vendre à la récolte
   - **sell_dca_monthly** : 1/12 par mois
   - **sell_at_first_signal** : vendre au premier signal positif
   - **hold_until_planting_decision** : tout garder jusqu'à la décision de plantation suivante

Métriques :
- `revenue_per_bushel_usd`
- `sharpe_per_year`
- `max_drawdown_revenue`
- `pct_years_beating_harvest_only`

## Statut Phase 2

Implémenté :
- Moteur de règles (`src/mais/decision/rules.py`) avec eval sécurisé
- Squelette de backtest (`src/mais/decision/backtest.py`) — actuellement avec
  prédictions naïves, à wirer sur la meta-database réelle
- CLI `mais advise` et `mais backtest`
- Page Streamlit "Conseil agriculteur"

À faire :
- Calibrer les classificateurs (Platt/Isotonic) avant de calculer `p_up_strong`
- Implémenter Markov-switching pour produire `regime`
- Brancher les vraies prédictions du méta-modèle au backtest
- Ajouter SHAP local : "le modèle dit STORE parce que (1) drought, (2) export surprise..."
