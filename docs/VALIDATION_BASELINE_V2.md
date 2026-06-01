# Validation Baseline V2 — 2026-05-15

Ticket : `IND-01`

Sources verifiees :

- `artefacts/professional_study/model_benchmarks.parquet` : `(44, 14)`
- `artefacts/professional_study/model_predictions.parquet` : `(108702, 8)`
- `artefacts/professional_study/cqr_results.parquet` : `(9882, 10)`
- `artefacts/professional_study/shap_importance.parquet` : `(68, 7)`
- `artefacts/indicator/indicator_backtest.parquet` : absent
- `docs/VALIDATION_BASELINE.md`
- `docs/PROFESSIONAL_STUDY_REPORT.md`

## 1. DA par horizon — tableau complet

La baseline saisonniere est la reference economique principale. La baseline momentum disponible dans l'artefact est `baseline_momentum_20d`, mais elle predit un retour continu et donne une DA proche de zero parce que le retour nul est mappe en direction baissiere. Elle est donc documentee, mais elle n'est pas une bonne reference directionnelle exploitable.

| Horizon | Meilleur modele | DA meilleur | DA baseline saisonniere | DA baseline momentum | Ecart vs saisonnier | N test | Periode test |
|---|---|---:|---:|---:|---:|---:|---|
| h5 | `elasticnet_factors` | 0.559 | 0.526 | 0.006 | +0.033 | 2475 | 2015-09-10 -> 2025-07-18 |
| h10 | `elasticnet_factors` | 0.569 | 0.531 | 0.002 | +0.038 | 2473 | 2015-09-04 -> 2025-07-11 |
| h20 | `elasticnet_factors` | 0.593 | 0.555 | 0.005 | +0.037 | 2469 | 2015-08-27 -> 2025-06-26 |
| h30 | `baseline_seasonal_naive` | 0.583 | 0.583 | 0.005 | +0.000 | 2465 | 2015-08-19 -> 2025-06-11 |

Lecture : le signal modelise bat la saisonnalite a h5, h10 et h20. A h30, la meilleure ligne reste la baseline saisonniere, ce qui confirme que l'horizon long est surtout porte par un effet calendaire dans les artefacts actuels.

## 2. AUC et Brier par horizon

`model_benchmarks.parquet` ne contient pas `auc`, `brier`, `probability`, `proba` ou score calibre. `model_predictions.parquet` contient uniquement `y_true` et `y_pred` sur la cible continue `y_logret_h{5,10,20,30}`.

Conformement au ticket, AUC et Brier ne sont pas recalcules depuis un score de regression non calibre.

| Horizon | AUC | Brier | Raison |
|---|---|---|---|
| h5 | incalculable proprement | incalculable | Predictions continues non calibrees, pas de probabilite directionnelle |
| h10 | incalculable proprement | incalculable | Predictions continues non calibrees, pas de probabilite directionnelle |
| h20 | incalculable proprement | incalculable | Predictions continues non calibrees, pas de probabilite directionnelle |
| h30 | incalculable proprement | incalculable | Predictions continues non calibrees, pas de probabilite directionnelle |

Lacune pour IND-02 et IND-04 : produire des predictions probabilistes explicites pour les cibles binaires (`y_up_h*`, fortes hausses/baisses) afin de mesurer AUC et Brier sans approximation.

## 3. CQR — coverage et width

Coverage globale : `0.9048` sur `9882` observations. L'objectif projet `>= 0.88` est confirme.

| Horizon | N test | Coverage | Width moyenne | Cible |
|---:|---:|---:|---:|---:|
| h5 | 2475 | 0.905 | 0.1133 | 0.900 |
| h10 | 2473 | 0.906 | 0.1563 | 0.900 |
| h20 | 2469 | 0.904 | 0.2355 | 0.900 |
| h30 | 2465 | 0.905 | 0.2748 | 0.900 |

Coverage par saison : non disponible dans l'artefact source, car `cqr_results.parquet` ne contient pas de colonne saison. Aucune saison n'a ete inferee manuellement pour eviter d'ajouter une metrique non produite par le pipeline.

## 4. SHAP — top facteurs par horizon

| Horizon | Rang | Facteur | Famille | Part mean abs SHAP |
|---|---:|---|---|---:|
| h5 | 1 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.124 |
| h5 | 2 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.122 |
| h5 | 3 | `factor_curve_structure` | `market_momentum` | 0.101 |
| h5 | 4 | `factor_positioning` | `positioning` | 0.094 |
| h5 | 5 | `factor_seasonality` | `seasonality` | 0.082 |
| h10 | 1 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.157 |
| h10 | 2 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.139 |
| h10 | 3 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.108 |
| h10 | 4 | `factor_seasonality` | `seasonality` | 0.106 |
| h10 | 5 | `factor_positioning` | `positioning` | 0.090 |
| h20 | 1 | `factor_wasde_supply_demand` | `wasde_supply_demand` | 0.133 |
| h20 | 2 | `factor_crop_condition_pressure` | `weather_belt_stress` | 0.123 |
| h20 | 3 | `factor_positioning` | `positioning` | 0.120 |
| h20 | 4 | `factor_seasonality` | `seasonality` | 0.111 |
| h20 | 5 | `factor_curve_structure` | `market_momentum` | 0.094 |
| h30 | 1 | `factor_macro_dollar_rates` | `macro_dollar_rates` | 0.148 |
| h30 | 2 | `factor_positioning` | `positioning` | 0.144 |
| h30 | 3 | `factor_cross_commodity` | `cross_commodity` | 0.116 |
| h30 | 4 | `factor_seasonality` | `seasonality` | 0.114 |
| h30 | 5 | `factor_curve_structure` | `market_momentum` | 0.096 |

Cohérence économique :

- h5 à h20 : l'offre-demande WASDE, les conditions de culture et la structure de courbe dominent. C'est cohérent pour un marché agricole ou stocks, météo et tension de terme structurent le risque court/moyen terme.
- h20 : le positionnement arrive dans le top 3, ce qui est plausible pour un indicateur de direction car les flux speculatifs peuvent amplifier ou freiner les mouvements.
- h30 : macro dollar/taux, positionnement, cross-commodity et saisonnalite dominent. C'est coherent avec un horizon plus long, ou les facteurs globaux et calendaires prennent plus de poids que le bruit quotidien.

## 5. Indicateur V1 — distribution des signaux

`artefacts/indicator/indicator_backtest.parquet` est absent et le dossier `artefacts/indicator/` n'est pas present. La distribution des signaux `BULLISH / BEARISH / NEUTRAL / UNCERTAIN` et la DA par label ne peuvent donc pas etre validees dans ce ticket.

Conclusion : l'indicateur V1 est documente ailleurs, mais son artefact de backtest n'est pas disponible comme source verifiable pour cette baseline V2.

## 6. Lacunes identifiees

| Lacune | Impact | Ticket concerne |
|---|---|---|
| AUC/Brier absents | Impossible de juger la calibration directionnelle actuelle | IND-02, IND-04 |
| Predictions probabilistes absentes | Les modeles actuels sortent un retour continu, pas `P(hausse)` | IND-04 |
| `artefacts/indicator/indicator_backtest.parquet` absent | Impossible de verifier la distribution des signaux V1 | IND-07, IND-08 |
| Coverage CQR par saison absente | Robustesse saisonniere non documentee | IND-05 ou IND-08 |
| Baseline momentum directionnelle non exploitable | La comparaison simple momentum doit etre recodee en vrai indicateur directionnel | IND-02 |
| DA h30 dominee par la saisonnalite | Le modele complexe ne bat pas la reference simple a h30 | IND-02, IND-04 |

## 7. Questions ouvertes pour IND-02 et IND-03

- IND-02 : quelle cible binaire donne une vraie probabilite exploitable (`y_up_h20`, forte hausse, forte baisse, asymetrie) ?
- IND-02 : le momentum 20 jours directionnel, code comme indicateur simple, bat-il ou non les modeles sur les signaux confiants ?
- IND-02 : h20 reste-t-il le meilleur compromis entre DA, nombre d'observations et exploitabilite ?
- IND-03 : les facteurs qui expliquent les gros mouvements futurs sont-ils les memes que les top SHAP du modele actuel ?
- IND-03 : les variables oracle confirment-elles l'importance court terme de la meteo/crop condition et l'importance h30 de la macro/cross-commodity ?

## 8. Anti-leakage

Commande lancee :

```bash
venv/bin/python -m mais.cli audit-leakage
```

Resultat :

```text
[PASS] features=275 targets=72 suspect_names=0 naming=0 perfect_fit=0 future_dep=0
```

Statut : PASS, aucun avertissement residuel signale par l'audit.

## 9. Decision IND-01

La baseline V2 est suffisamment documentee pour servir de reference aux tickets suivants :

- DA h5/h10/h20/h30 complete avec baseline saisonniere.
- CQR coverage `0.9048`, superieure a l'objectif `0.88`.
- SHAP top 5 par horizon present et interprete.
- Lacunes explicites, sans claim non verifie.
- Audit anti-leakage PASS.

Decision : `IND-01` peut passer en `NEEDS_REVIEW`.
