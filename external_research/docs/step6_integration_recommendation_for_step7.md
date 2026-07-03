# Étape 6 → préparation de l'étape 7 — Recommandation d'intégration

Date : 2026-06-13. Prépare l'étape 7 **sans la coder**. Décrit quoi intégrer, comment, et ce
qu'il faut garder en garde-fou. Décision retenue : **Option B** (score de vente/direction/
risque H40-H90). Règle 12 : le holdout 2024+ ne sera ouvert que par un ticket projet humain.

## 1. À intégrer dans l'étude principale (KEEP / IMPROVE solides)
| Brique | Source | Forme intégrée |
|---|---|---|
| **Crop Condition @ H90** | EXT019/EXT024/EXT015 | logit L2 : saison + `cond_gd_ex_anom` + `cond_dev5y` + `cond_poor_vp` |
| **WASDE stocks-to-use @ H40** | EXT007/EXT024/EXT015 | logit L2 : saison + `s2u_z` + `s2u_pctile` + `s2u_slow_chg` |
| **Volatilité (gate de risque)** | EXT009/EXT010 | HAR (défaut) ou EGARCH ; flag décile haut de vol prévue |
| **Conditionnement régime** | EXT017 | pondère la confiance (uptrend/low-vol/bilan extrême) — **à valider forward** |
| **Pipeline WASDE vintage** | EXT026 | source unique WASDE publication-only (anti-fuite) |
| **Hygiène de roll** | EXT006 | features EMA sur `adjusted_price` ou hors jours de roll |

## 2. À NE PAS intégrer
- **REJECT** : météo réalisée (EXT001/002/020), surprise WASDE (EXT008), COT (EXT003), proxys
  éthanol (EXT004), trend-following (EXT011), stacking (EXT050).
- **DATA_BLOCKED** : courbe (EXT005), basis/VECM (EXT013), OU (EXT012).
- **LEAKAGE_RISK** : aucun après correction étape 5 bis.
- **FRAGILE non confirmé** : filtre de régime tant qu'il n'est pas validé en forward ; BMA
  comme source de signal (garder seulement comme filet de robustesse).
- **NOT_WORTH_YET** : NBEATSx/DL (EXT016).

## 3. Architecture recommandée du score (Option B)
Score composite, sortie ternaire + confiance + risque. Chaque sous-score est **passé-only** et
**parcimonieux**.

```
score_marche        : base directionnelle (ret_5d, ret_20d, vol_20, saison)        [benchmark]
score_wasde         : logit s2u_z + s2u_pctile + s2u_slow_chg                        H40
score_crop          : logit cond_gd_ex_anom + cond_dev5y + cond_poor_vp + saison     H90  <-- coeur
score_volatilite    : HAR/EGARCH -> niveau de risque (gate)                          H20-H90
score_regime        : uptrend/low-vol/bilan extreme -> multiplicateur de confiance    (forward-validé)
score_incertitude   : largeur IC + désaccord des sous-scores -> abstention
```

**Sortie possible** : VENDRE / VENDRE PARTIELLEMENT / ATTENDRE / SURVEILLER, accompagnée de
RISQUE ÉLEVÉ / RISQUE FAIBLE (gate vol) et d'un niveau de CONFIANCE (régime + incertitude).
Jamais un ordre automatique : indicateur d'aide à la décision.

## 4. Variables candidates (exactes)
| Variable | Source | Fichier | Horizon | Justification | Risque |
|---|---|---|---|---|---|
| `cond_gd_ex_anom` | Crop Condition | features_p2 (EXT024/019) | H90 | meilleur signal dir. | faible |
| `cond_dev5y` | Crop Condition | features_p2 | H90 | déviation 5 ans stable | faible |
| `cond_poor_vp` | Crop Condition | features_p2 | H90 | queue basse de récolte | faible |
| `s2u_z` | WASDE vintage | features_p2 (EXT007/026) | H40 | état de bilan lent | faible (non-station. si brut) |
| `s2u_pctile` | WASDE vintage | features_p2 | H40 | percentile expandant | faible |
| `s2u_slow_chg` | WASDE vintage | features_p2 | H40 | variation lente | faible |
| `base_sin`/`base_cos` | saison | ext_harness | tous | saisonnalité (porte l'edge) | faible |
| vol HAR (`rv_w/m/q`) | retours CBOT | vol_utils (EXT010) | H20-H90 | gate de risque | faible |
| vol EGARCH | retours CBOT | EXT009 | H20-H90 | asymétrie | faible |
| régimes (uptrend/low-vol/bilan) | marché+WASDE | EXT017 | H90 | confiance | **moyen (post-hoc)** |
À **jeter** : dummies `bilan_tight/loose`, momentum court (EXT015).

## 5. Modèles candidats
- **Directionnel simple** : logit L2 (défaut, le meilleur — EXT024).
- **Supply-demand parcimonieux** : 1 signal par horizon (crop@H90, wasde@H40).
- **Volatilité** : HAR (défaut) / EGARCH (asymétrie).
- **Régime** : règles passé-only (pas de modèle fitté par régime).
- **Combinaison** : BMA **seulement** comme filet de robustesse, jamais pour battre le membre.
- **Exclus** : stacking, RF kitchen-sink, DL.

## 6. Benchmarks à garder
Random walk (EXT025), RW+drift saisonnier, trend-following EWMAC (plancher), baseline marché
seul. Tout score doit être rapporté **face à ces planchers**.

## 7. Tests à refaire après intégration
1. **Walk-forward** expandant, refit annuel purgé (vraie `target_date` = `index[i+h]`).
2. **Holdout 2024+** (ticket projet humain, règle 12) — épreuve décisive.
3. **Backtest décisionnel** vendre/attendre, coût-aware (3-5 €/t éq.).
4. **Robustesse par sous-période** (≥ 2 moitiés) + bootstrap par blocs de la DA.
5. **Calibration** du score (fiabilité des probabilités) + **stabilité** des variables.
6. **Validation forward** du filtre de régime avant de l'activer.
