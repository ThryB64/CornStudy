# Validation holdout 2024+ — score de vente CBOT

Date : 2026-06-13. **Le holdout 2024+ n'avait jamais été utilisé** (étapes 1-6, règle 12). Il
est évalué **une seule fois** ici. Features et seuils **figés avant** holdout ; modèles
entraînés sur **≤ 2023 uniquement**. Aucun tuning sur le holdout.

## Protocole
- Frontière : `2024-01-01`. Période évaluable : décisions 2024-01 → ~2025-03 (H90) / ~2025-05
  (H40), bornée par la fin des prix (`market.parquet` → 2025-07-25).
- Cible = signe du log-retour CBOT t→t+h, **vraie ligne de marché** `index[i+h]`.
- Modèles : logit L2 (≤2023), standardisation/imputation/gate **gelés** sur ≤2023.
- **HAR purgé** (revue) : la prévision de volatilité n'utilise que des fenêtres dont la vraie
  date de fin < holdout. Effet sur le gate négligeable (0.1922 → 0.1923) ; les métriques
  directionnelles ci-dessous (logit Crop/WASDE) sont inchangées.

## Résultats directionnels (artefact : `final_holdout_2024_metrics.csv`)
| modèle | h | n | DA | vs majorité | AUC | Brier | rappel baisse | préc. baisse |
|---|---|---|---|---|---|---|---|---|
| **score_h90_crop** | 90 | 303 | **0.686** | +0.182 | **0.816** | 0.191 | 0.627 | 0.716 |
| score_h40_wasde | 40 | 353 | 0.705 | +0.184 | 0.709 | 0.227 | 0.571 | 0.808 |
| crop_only_h90 | 90 | 303 | 0.657 | +0.152 | 0.708 | 0.227 | 0.601 | 0.681 |
| wasde_only_h40 | 40 | 353 | 0.657 | +0.136 | 0.621 | 0.245 | 0.397 | 0.880 |
| **season_only_h90** | 90 | 303 | **0.752** | +0.248 | **0.840** | 0.196 | 0.699 | 0.787 |
| **market_only_h90** | 90 | 303 | **0.752** | +0.248 | **0.878** | 0.190 | 0.634 | 0.836 |
| random_walk_h90 | 90 | 303 | 0.495 | −0.010 | 0.500 | 0.250 | 0.000 | — |

DA walk-forward pré-2024 (contexte recherche, crop@H90) : **0.653**.

## Lecture honnête
1. **Le signal survit vs random walk** : crop@H90 fait **0.686 / AUC 0.816** contre 0.495 pour
   la random walk (+18 pts de DA). Économiquement cohérent : 2024 = grosse récolte US,
   conditions good/excellent élevées → baisse → vendre, ce que le modèle capte (rappel baisse
   0.63, précision baisse 0.72).
2. **MAIS il ne bat pas les baselines naïves** : une **pure saisonnalité** (0.752 / AUC 0.840)
   et le **marché seul** (0.752 / AUC 0.878) font **aussi bien voire mieux**. Sur ce holdout,
   **les fondamentaux Crop/WASDE n'ajoutent pas de valeur démontrable** au-dessus de la
   saisonnalité : 2024 était un repli saisonnièrement typique, où saison ⟂ fondamentaux sont
   fortement corrélés.
3. **Fenêtre courte** : ~1,5 an, n=303, **un seul cycle baissier**. Puissance statistique
   faible ; un bon résultat ici n'est pas une preuve de robustesse.

## Verdict : **FRAGILE**
Le score est directionnellement informatif et cohérent, **mais** ne surpasse pas une baseline
de saisonnalité sur le holdout, et la fenêtre est trop courte pour conclure. → **aide
indicative**, non opérationnelle sans reconfirmation forward. Conforme à la règle de l'étape 7
(« si le holdout est mitigé → FRAGILE ; ne pas cacher »).
