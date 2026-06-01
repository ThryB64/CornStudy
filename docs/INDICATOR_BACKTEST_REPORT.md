# Backtest de l'indicateur directionnel maïs

## Méthodologie

- Modèle : `ridge_factors`
- Observations totales (toutes horizons) : 9,882
- Évaluation walk-forward out-of-sample (même split que l'étude professionnelle)
- DA = Directional Accuracy = % de prédictions correctes (signal > 0.5 ↔ prix monte)
- Brier Score = erreur quadratique sur les probabilités (plus bas = meilleur)
- AUC = aire sous la courbe ROC (0.5 = aléatoire, 1.0 = parfait)
- Confidence = distance de P(up) par rapport à 0.5, normalisée

## Métriques globales par horizon

| Horizon | N | DA | Brier Score | AUC | CQR Coverage |
|---:|---:|---:|---:|---:|---:|
| J+5 | 2,475 | 0.562 | 0.2473 | 0.561 | 88.9% |
| J+10 | 2,473 | 0.583 | 0.2408 | 0.607 | 89.0% |
| J+20 | 2,469 | 0.616 | 0.2347 | 0.645 | 89.5% |
| J+30 | 2,465 | 0.625 | 0.2325 | 0.657 | 89.1% |

## Performance par niveau de confiance

> **Hypothèse clé** : le signal est plus fiable quand il est confiant.
> Si DA(confiance élevée) ≫ DA(confiance faible), le confidence score filtre correctement.

| Bucket | Plage confidence | N | DA | Brier |
|---|---|---:|---:|---:|
| low | [0.00, 0.50) | 6,633 | 0.559 | 0.2486 |
| medium | [0.50, 0.65) | 1,211 | 0.600 | 0.2449 |
| high | [0.65, 1.01) | 2,038 | 0.717 | 0.2034 |

## Performance par saison

| Saison | N | DA | Brier |
|---|---:|---:|---:|
| summer | 2,419 | 0.637 | 0.2236 |
| fall (récolte) | 2,503 | 0.594 | 0.2364 |
| spring (semis) | 2,552 | 0.583 | 0.2475 |
| winter | 2,408 | 0.572 | 0.2474 |

## Performance par régime de marché

| Régime | N | DA | Brier |
|---|---:|---:|---:|
| bear | 492 | 0.760 | 0.1830 |
| bull | 5,830 | 0.617 | 0.2352 |
| range | 3,560 | 0.539 | 0.2524 |

## Interprétation

### L'indicateur est-il utile ?

La DA globale mesure si la direction prédite est correcte. Une DA > 55% sur données out-of-sample est significative pour les marchés agricoles. La comparaison par confiance est le test clé : si les signaux confiants sont plus précis, le confidence score a une valeur de filtrage réelle.

### Quand l'indicateur se trompe-t-il ?

- **Régime bear** : peu d'observations (≈2% de l'historique), estimation instable.
- **Faible confiance** : le modèle ne discrimine pas bien → signal UNCERTAIN recommandé.

### Limites

- L'évaluation est walk-forward (pas de look-ahead) mais les modèles sont entraînés
  sur la même période historique → léger biais de survivorship si le pipeline change.
- La DA et l'AUC mesure la direction brute, pas l'amplitude. Un signal BULLISH correct
  à +0.1% et incorrect à -5% ne sont pas équivalents économiquement.
- Les prédictions pour h20 et h30 sont moins fraîches (manquent les 20-30 derniers jours)
  car le futur observé n'est pas encore disponible au moment de l'évaluation.
