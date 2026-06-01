# EMA 07 — Basis Formel EMA/CBOT

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Résultats clés

| Métrique | Valeur | Verdict |
|---|---|---|
| Basis moyen | 37.2 €/t | EMA prime permanente sur CBOT |
| ADF basis | stat=-6.19, p=6.1e-8 | STATIONNAIRE |
| KPSS basis | non-stationnaire | CONTRADICTION (persistance forte) |
| AR(1) φ | 0.970 | Très persistant |
| Demi-vie AR(1) | 22.8 jours | ~1 mois |
| Hit rate mean-reversion H20 (2σ) | 43.1% | — |
| Hit rate mean-reversion H60 (2σ) | **85.0%** | CONFIRMÉ |
| Backtest arbitrage basis | 14 trades, 100% gagnants | Non validé OOF |

## Stationnarité

**Contradiction ADF/KPSS** : ADF rejette la racine unitaire (p=6.1e-8), mais KPSS rejette aussi la stationnarité. Ce pattern est typique des processus quasi-intégrés (fractionnellement intégrés ou AR persistant). Le basis est probablement I(0) avec une persistance très élevée (φ=0.97).

## Mean-reversion

Le basis revient vers sa moyenne dans 85% des cas sur un horizon H60 (3 mois) lorsqu'il dépasse 2σ. Ce signal est robuste et cohérent avec la demi-vie de 22.8 jours.

**Hit rate H20 à 43%** : le retour à la moyenne est lent — un horizon de 60 jours est nécessaire pour capturer ~85% des événements.

## Backtest arbitrage basis

Simple stratégie mean-reversion (entrée z>2σ, sortie z<0.5σ) sur 2010-2025 : 14 trades, 100% gagnants, +429.8 €/t total.

> ⚠️ **EXPLORATOIRE. NON VALIDÉ.** Backtest in-sample complet, sans coûts de transaction, sans contrainte de liquidité, sans walk-forward OOF. À traiter comme une hypothèse de recherche, pas comme un résultat de production. Un walk-forward OOF avec seuils gelés est requis pour valider (voir NB2-03).

## Artefact produit

`artefacts/ema_study/ema_basis_formal.json`
