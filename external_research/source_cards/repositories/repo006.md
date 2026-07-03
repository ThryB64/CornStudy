---
id: REPO006
source_type: repository
title: YavuzAkbay/Ornstein-Uhlenbeck
priority: medium
status: analyzed_2026-06-12
---
# YavuzAkbay/Ornstein-Uhlenbeck

## 1. Identification

- URL : https://github.com/YavuzAkbay/Ornstein-Uhlenbeck — propriétaire : Yavuz Akbay
- Licence : ✅ GPL v3 (code réutilisable avec contrainte copyleft — préférer réimplémentation, l'OU se code en 30 lignes)
- État : cloné ; 2 scripts : `calibrated_ou_analyzer.py`, `ml_ou_analyzer.py`
- Langage : Python

## 2. Objectif

Calibrer un processus OU `dX = θ(μ−X)dt + σdW` sur des commodities pour le trading mean-reversion : estimation θ/μ/σ, demi-vie, signaux d'écart à la moyenne.

## 3. Données utilisées

Prix de commodities (yfinance vraisemblablement). Pas de basis ni de spreads — nous l'appliquerions à NOTRE basis EMA−CBOT, usage différent du repo.

## 4. Cible prédite

Signal de retour à la moyenne (écart au μ estimé), temps de reversion attendu.

## 5. Horizons

Implicite : la demi-vie estimée (ln 2/θ).

## 6. Modèles

OU par MLE/régression discrète AR(1)↔OU ; variante « ML » (calibration assistée).

## 7. Méthode d'évaluation

Faible : calibration in-sample, visualisations. Pas de walk-forward natif → à imposer nous-mêmes.

## 8. Risques de fuite

μ et θ estimés sur tout l'échantillon = fuite classique du pairs trading. Pour EXT012 : calibration expandante ou roulante PASSÉE uniquement (anti_leak_rules n°7), cohérent avec nos z expandants.

## 9. Réutilisable

- **Méthode** : formules de calibration OU discrète et demi-vie — cadre formel pour ce que V10-A a déjà mesuré empiriquement (AR(1) φ=0.96, demi-vie 17j, roulante 7.6-42j).
- **Idée** : intervalle de confiance sur θ → quand la demi-vie est incertaine, s'abstenir (rejoint nos gates UNCERTAIN).

## 10. Faible / inutilisable

Pas de coûts, pas de backtest sérieux, single-asset. GPL si copie directe.

## 11. Hypothèses testables

- H1 : OU calibré en expandant sur basis_z : la demi-vie OU prédit-elle mieux le temps de reversion réalisé que la demi-vie AR(1) roulante de V10 ? (V138 a montré niveau≠horizon trade : calage ×3 — l'OU formel peut-il réduire cet écart ?)
- H2 : θ time-varying (fenêtre 252j) comme feature de régime : reversion rapide vs lente → moduler le plafond de détention (90j actuel).

## 12. EXT associées

EXT012 (principal), EXT017 (θ comme variable de régime).

## 13. Conclusion

**À garder pour plus tard** (après les blocs fondamentaux) : utile comme formalisation de V10/V138, pas comme découverte. Benchmark, pas signal.
