# V7-02 — Purged CV avec Embargo : Comparaison des 9 Protocoles

**Version** : V7-02 | **Horizon de référence** : 90 jours

## Protocoles comparés

| Protocole | n_splits | mean_train | mean_test | total_OOF | Embargo | Recommandation |
|---|---|---|---|---|---|---|
| classic | 5 | 1751 | 583 | 2915 | ❌ | AVOID |
| embargo_H | 5 | 1751 | 519 | 2595 | ✅ forward_H | RECOMMANDÉ |
| embargo_2H | 5 | 1751 | 455 | 2274 | ✅ forward_2H | RECOMMANDÉ (conservateur) |
| non_overlap | 5 | 21 | 6 | 30 | ✅ stride_H | ACCEPTABLE (perte data) |
| block_bootstrap | 10 | 2855 | 645 | 6454 | ❌ random | COMPLÉMENTAIRE |
| leave_one_year | 13 | 1821 | 249 | 3239 | ⚠️ 7j gap | RECOMMANDÉ (saisonnier) |
| leave_one_crop_year | 13 | 1739 | 256 | 3327 | ❌ | RECOMMANDÉ MAÏS |
| leave_one_crisis | 3 | 2087 | 261 | 783 | ❌ | STRESS TEST uniquement |
| purged_kfold | 5 | 2801 | 583 | 2915 | ✅ bilatéral | RECOMMANDÉ meta-modèles |

*Évalué sur 3500 jours ouvrés (~2010-2023)*

## Conclusions

### Protocole principal : `embargo_H`
Standard anti-leakage pour walk-forward temporel. Supprime les observations de test dans la fenêtre H jours après la fin du train. Recommandé pour tous les tickets V7 avec horizon ≤ 90j.

### Méta-modèles : `purged_kfold`
Purging bilatéral — exclut du train toutes les observations dans une fenêtre ±H autour du test. Préférable pour les méta-features OOF où le train peut inclure des points proches du test dans les deux sens.

### Stress tests : `leave_one_crisis` + `leave_one_year`
3 splits (2012, 2020, 2022) pour tester la robustesse hors-distribution. `leave_one_year` (13 splits) pour valider la généralisation saisonnière.

### À éviter : `classic`
Sans embargo, les périodes à forte autocorrélation (≥ 90j) introduisent du leakage. 320 violations sur 2915 observations test dans notre test de référence.

### `non_overlap` : attention à la perte de données
Avec stride = H = 90j, seule 1 observation sur 90 est conservée → total_OOF = 30 sur 3500 jours. À utiliser uniquement pour des features à très longue mémoire.

## Artefact
`artefacts/v7/purged_cv_embargo_study.json`

## Caveats
- Évaluation sur données synthétiques (dates uniformes). L'impact de l'embargo sur les données réelles dépend de la densité et des gaps naturels.
- `block_bootstrap` ignore l'ordre temporel — ne pas utiliser comme split principal, seulement pour estimer la variance de l'AUC.
- `leave_one_crop_year` préférable à `leave_one_year` pour les études maïs (année agricole Sep-Août).
