# V7-31 — Benchmark Suite : Baselines Naïves et Professionnelles

**Version** : V7-31 | Tableau de référence pour évaluer les signaux V7

## Benchmarks implémentés

### Benchmarks naïfs (5)

| Benchmark | Description | AUC attendue |
|---|---|---|
| `random` | Scores uniformes U(0,1) — seed=42 | ~0.50 |
| `persistence` | Répète la direction passée H | ~0.50 |
| `naive_seasonal` | Tendance saisonnière mensuelle moyenne | ~0.50-0.52 |
| `always_up` | Prédit toujours 1 (haussier) | ~0.50 (symétrique) |
| `always_down` | Prédit toujours 0 (baissier) | ~0.50 (symétrique) |

### Benchmarks professionnels (3)

| Benchmark | Description | Signal |
|---|---|---|
| `momentum_20d` | Momentum 20j — direction rolling mean | Trend-following court terme |
| `trend_following_52w` | Prix > MA 252j | Trend-following long terme |
| `carry_signal` | Basis > rolling(60) mean | Contango/backwardation |

## Règle d'évaluation V7

Pour tout résultat V7 avec AUC observée :

```
delta_auc = AUC_model - best_baseline_auc
GO_RESEARCH : delta_auc > 0.05 ET AUC_model > 0.60
MARGINAL    : delta_auc > 0 mais < 0.05
NO_VALUE    : delta_auc ≤ 0
```

## Usage

```python
from mais.research.benchmark_suite import evaluate_all_benchmarks, compute_delta_auc

# Évaluer les baselines pour une cible
aucs = evaluate_all_benchmarks(y_true, prices=cbot_prices, basis=ema_basis)

# Calculer le delta vs votre modèle
delta = compute_delta_auc(auc_model=0.72, benchmark_aucs=aucs)
print(f"Delta vs best baseline: {delta['delta_vs_best']:+.3f}")
```

## Artefact
`artefacts/v7/benchmark_suite.json`
