# EXT015 — Résultats : sélection de variables / importances train-only

**Verdict : KEEP** (diagnostic) — confirme de façon indépendante que WASDE (stocks-to-use)
et Crop Condition sont des variables **stables et utiles**, et que la parcimonie gagne.

## Protocole
Importance par **permutation sur le TRAIN** (RandomForest régularisé, balanced accuracy),
calculée DANS chaque fenêtre d'entraînement (16 refits annuels 2008-2023), jamais sur tout
le dataset (anti-fuite n10). Comparaison de la DA : RF toutes variables vs logit top-6
sélectionné train-only vs marché seul. Cibles dir H20/H40/H90.

## Stabilité des variables (frac_in_topk = fréquence dans le top-6 ; frac_positive = part des années où l'importance est >0)

**Toujours sélectionnées, importance toujours positive (16/16 ans)** :
- `base_cos` / `base_sin` (saisonnalité) — variable la plus forte à tous horizons ;
- **`s2u_pctile`, `s2u_z`** (bilan WASDE stationnaire) — top-k 88-100 % des années ;
- **`cond_gd_ex_anom`, `cond_dev5y`, `cond_poor_vp`** (Crop Condition) — top-k 62-88 % ;
- `s2u_slow_chg` (variation lente du bilan) monte à H90 (top-k 88 %).

**Faibles / instables (jamais dans le top-6)** :
- `bilan_tight`, `bilan_loose` (dummies binaires du bilan) — l'info est déjà dans `s2u_z`/
  `s2u_pctile` continus → les dummies sont redondantes et bruitées ;
- `base_ret_5d`, `base_ret_20d` (momentum court) — peu utiles à H40/H90.

## Performance (DA, walk-forward)

| H | RF toutes vars | logit top-6 train-only | marché seul |
|---|---|---|---|
| 20 | 0.551 (AUC 0.561) | **0.567** (AUC 0.567) | 0.546 (AUC 0.544) |
| 40 | 0.583 (AUC 0.607) | **0.604** (AUC 0.597) | 0.555 (AUC 0.579) |
| 90 | 0.577 (AUC 0.624) | **0.656** (AUC 0.691, Brier 0.226) | 0.599 (AUC 0.608) |

## Lecture
1. **Les deux familles IMPROVE ressortent VRAIMENT** : `s2u_z`/`s2u_pctile` (WASDE) et
   `cond_gd_ex_anom`/`cond_dev5y`/`cond_poor_vp` (Crop) sont sélectionnées train-only la
   grande majorité des années, avec une importance systématiquement positive. Le gain de
   l'étape 4 n'était PAS fragile.
2. **La parcimonie gagne** : le logit top-6 (sélection train-only) bat à la fois le RF
   kitchen-sink (qui surapprend, surtout à H90 : 0.577 vs 0.656) et le marché seul.
3. **La saisonnalité domine** — normal pour le maïs (cycle agronomique) ; c'est un
   prédicteur directionnel structurel, pas un artefact.
4. **À jeter** : dummies `bilan_tight/loose` (redondants), momentum court à long horizon.

## Variables à garder pour l'étape 6
`base_sin`, `base_cos`, `s2u_z`, `s2u_pctile`, `s2u_slow_chg` (H90), `cond_gd_ex_anom`,
`cond_dev5y`, `cond_poor_vp`. **À écarter** : `bilan_tight`, `bilan_loose`, `base_ret_5d`.

## Conclusion
**KEEP** (comme diagnostic de sélection). WASDE état de bilan et Crop Condition sont des
variables robustes et stables pour un modèle **directionnel** parcimonieux H40/H90 ;
combinées à la saisonnalité, elles forment le cœur d'un score de vente. Validation
indépendante d'EXT024.
