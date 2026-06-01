# Protocol Freeze — R&D maïs

Ce protocole est figé par R&D-01 avant les tickets de modélisation suivants.

- Période d'optimisation : 2010–2022 uniquement.
- Backtest final non réoptimisé : 2023–2025.
- Validation crop years : 2015–2022 si les données 2022 sont complètes.
- Horizons autorisés : J+28, J+35, J+40, J+45, J+60.
- Target directionnelle : `y_up_hH` construite par `build_multi_horizon_targets`.
- Features autorisées : colonnes numériques de `build_features()`, hors `Date` et colonnes `y_*`.
- Heure du signal : fin de journée ; les fondamentaux restent shiftés selon leur calendrier de publication.
- Fréquences d'évaluation : quotidienne et hebdomadaire lundi.
- Métriques principales : DA, AUC, Brier, DA_top20, DA par crop year, IC95 bootstrap.
- Correction tests multiples : Benjamini-Hochberg sur les comparaisons inter-modèles.
- Règle 2026+ production : aucun seuil métier ne doit être recalibré hors validation OOF documentée.
