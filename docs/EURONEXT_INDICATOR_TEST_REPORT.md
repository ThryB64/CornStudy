# Indicateur Euronext — rapport de tests

Date : 2026-06-13.

## Commandes
```bash
./venv/bin/python -m pytest tests/test_euronext_indicator.py \
    tests/test_euronext_indicator_backtest.py tests/test_euronext_indicator_dashboard.py -q
./venv/bin/python -m ruff check src/mais/indicator/euronext_indicator*.py src/mais/cli.py \
    tests/test_euronext_indicator*.py
./venv/bin/python -m py_compile src/mais/indicator/euronext_indicator*.py
```

## Résultats
- **pytest : 12 passed**.
- **ruff : All checks passed**.
- **py_compile : OK**.

## Couverture
| Fichier | Test | Vérifie |
|---|---|---|
| `test_euronext_indicator.py` | `euronext_price_loads_clean` | prix chargé, trié, sans doublon, numérique |
| | `target_dates_use_market_rows` | H20/H40/H90 = vraie ligne `index[i+h]`, pas jours calendaires |
| | `forward_targets_not_used_in_score` | colonnes score ⟂ colonnes `target_*` (anti-fuite) |
| | `recommendations_allowed_only` | sorties ∈ {SELL_PARTIAL, WAIT, WATCH, RISK_HIGH, NO_SIGNAL}, jamais BUY/SHORT |
| | `stale_flag_beyond_cbot` | drapeau `score_stale` présent et binaire |
| `test_euronext_indicator_backtest.py` | `total_sold_not_above_100pct` | total vendu ≤ 100 % par campagne |
| | `no_buy_no_short_in_decisions` | fractions ∈ [0,1] (jamais de short) |
| | `cooldown_respected` | ventes partielles espacées ≥ cooldown séances |
| | `all_campaign_windows_run` | calendar / sep_aug / oct_sep exécutés |
| `test_euronext_indicator_dashboard.py` | `finalize_creates_artefacts` | 8 artefacts + verdict valides |
| | `html_is_self_contained` | HTML autonome, Plotly inline, **aucune balise `<img>`/`<script src=>`/`<link>` externe** |
| | `latest_json_shape` | dernier signal bien formé (price_forecast_enabled=false, note « pas un bot ») |

## Conclusion
Tous les tests passent. Les garde-fous sont verrouillés : cible ligne-de-marché, anti-fuite
(retours futurs jamais dans le score), vocabulaire de sortie, backtest sans short/buy avec
cooldown, et **dashboard HTML 100 % autonome sans image générée** (Plotly interactif, JS inline).
