# Étude fusion directionnelle H60/H90 — fondamentaux d'offre

**Date : 2026-07-03. Statut : VALIDÉE (protocole validate_pistes). Script : `scripts/build_direction_fusion.py`. Artefacts : `artefacts/direction_fusion/`.**

## Contexte et déblocage préalable

L'univers d'étude était figé au 2025-07-25 : `mais clean` était un stub legacy et
`data/interim/database.parquet` (l'ancre de `build_features()`) n'était jamais rafraîchi,
alors que les collecteurs quotidiens accumulaient des données brutes jusqu'à juillet 2026.
Le fix (`src/mais/clean/market_refresh.py`) étend l'ancre depuis `data/raw/`
(+235 séances, mapping vérifié : `oil_close`=WTI, `gas_close`=natgas, MAE 0.0000).

Conséquence scientifique : **~1 an de données (2025-07-26 → 2026-07-02) jamais vues par
aucun développement du projet** devient disponible comme test de généralisation pur.

## Question

Les blocs fondamentaux identifiés à l'Étape 4 (crop condition, niveaux WASDE) et la piste
blé/maïs ajoutent-ils un signal directionnel CBOT à H60/H90 au-delà du marché seul, et le
signal combiné généralise-t-il ?

## Protocole (identique à validate_pistes)

- Walk-forward expandant 2014→2026, refit annuel, purge = horizon, standardisation train-only,
  LogisticRegression (moteur `build_risk_indicator.walkforward`).
- AUC + IC95 bootstrap (1000), part d'années positives, placebo (labels permutés).
- Règle a priori : ROBUSTE si IC_bas > 0.52 ET ≥60 % d'années positives ET placebo ∈ [0.45 ; 0.55].
- Fondamentaux ffill (paliers connus jusqu'à la publication suivante), anti-leakage shift(1) amont.

Blocs : MARKET (logret 20j, dist 52w high, vol 60j) / CROP (crop_ge_zscore_seasonal,
crop_ge_5y_avg_deviation, crop_condition_momentum_2w) / WASDE (stocks_to_use_ratio, calc_z) /
WHEAT (corn_wheat_ratio, spread_corn_wheat) / FOND = CROP+WASDE+WHEAT / FULL = MARKET+FOND.

## Résultats (OOS 2014-2026, n≈3050-3080)

| Cible | Bloc | AUC | IC95 | Années+ | Placebo | Verdict |
|---|---|---|---|---|---|---|
| y_up_h90 | **FOND** | **0.626** | [0.607 ; 0.646] | 69 % | 0.489 | **Robuste** |
| y_up_h90 | CROP | 0.604 | [0.584 ; 0.623] | 77 % | 0.489 | Robuste |
| y_up_h90 | WHEAT | 0.602 | [0.581 ; 0.622] | 77 % | 0.493 | Robuste |
| y_up_h90 | WASDE | 0.570 | [0.549 ; 0.590] | 69 % | 0.496 | Robuste |
| y_up_h90 | FULL | 0.603 | [0.584 ; 0.623] | 69 % | 0.514 | Robuste |
| y_up_h90 | MARKET | 0.511 | [0.491 ; 0.532] | 54 % | 0.510 | Limite |
| y_up_h60 | FOND | 0.600 | [0.581 ; 0.620] | 77 % | 0.484 | Robuste |
| y_up_h60 | MARKET | 0.521 | [0.500 ; 0.541] | 62 % | 0.496 | Limite |
| y_down_gt_3pct_h60 | WHEAT | 0.590 | [0.570 ; 0.609] | 77 % | 0.481 | Robuste |
| y_down_gt_3pct_h60 | CROP | 0.584 | [0.562 ; 0.604] | 77 % | 0.504 | Robuste |

(table complète : `artefacts/direction_fusion/fusion_results.csv`)

## Découvertes

1. **FOND h90 = meilleur modèle directionnel de l'étude : AUC 0.626 [0.607 ; 0.646]**,
   supérieur à chaque bloc isolé (+0.022 vs CROP seul). Les trois familles portent une
   information complémentaire sur l'état de l'offre.
2. **Le marché seul ne prédit pas la direction** (0.511-0.521, IC contenant 0.50) — les
   fondamentaux sont la source du signal, pas le momentum.
3. **Ajouter le marché dilue** (FULL 0.603 < FOND 0.626 à h90) : la parcimonie gagne,
   cohérent avec la leçon « 2 variables » de V10.
4. **Structure des échecs lisible** : années d'offre réussies (2016, 2018-2020, 2023-2025,
   AUC 0.72-0.97), années de choc demande/géopolitique ratées (2021 : 0.11 ; 2022 : 0.41 ;
   2017 : 0.33). Le modèle lit l'offre ; il est aveugle aux chocs de demande. Un régime-gate
   n'est PAS ajouté (le filtre régime a déjà été réfuté en forward, V23).
5. **Confidence gate revalidé sur les fondamentaux** : DA h90 0.625 (tous les jours) →
   0.777 (|p−0.5| ≥ 0.20, couverture 6 %) ; h60 0.561 → 0.723 (seuil 0.15, couverture 14 %).
6. **Année inédite 2025-07 → 2026-07** (jamais vue par le projet, ~1.6 tirage indépendant
   à h90 — à lire comme UN tirage) : CROP 0.86 et WASDE 0.87 ont vu juste à h90 ;
   WHEAT s'est inversé (0.36). Les verdicts officiels re-calculés sur l'univers étendu
   tiennent : **crop_h90 ROBUSTE (0.604, en hausse), wheat_corn ROBUSTE (0.590, stable)**,
   wasde_h40 reste LIMITE (46 % d'années positives).

## Limites

- AUC 0.6 ≈ signal utile mais modeste : indicateur d'aide à la décision, pas de trading.
- L'année inédite ne fournit qu'un tirage indépendant à h90 : la « réussite » crop/WASDE
  sur cette fenêtre est une non-infirmation, pas une preuve supplémentaire.
- L'inversion WHEAT sur l'année inédite est un signal de fragilité à surveiller au prochain
  jalon forward (si 2 années consécutives s'inversent, requalifier la piste).
- Aucun coût de transaction : cible = information directionnelle, pas un PnL.
- 2026 : cible h90 non résolue au-delà d'avril — l'AUC 2026 (0.0, n petit) n'est pas
  interprétable isolément.

## Décision

- FOND h90 devient le candidat cœur « direction CBOT long terme » de l'indicateur
  (au-dessus de crop_h90 seul), avec gate d'abstention |p−0.5| < 0.15.
- Surveillance forward : re-mesurer FOND h90 et WHEAT à chaque jalon mensuel.
