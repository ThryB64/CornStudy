# EMA 01 — Audit Données EMA v2

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Verdict période ML

`NO_RELIABLE_PERIOD` — La source Barchart proxy est exploratoire. Aucun crop year n'atteint 80% de couverture H sur la période complète (les contrats H expirent en mars, couvrant naturellement ~50% du crop year oct-sept). La donnée reste utilisable pour des études descriptives et des benchmarks avec réserves.

## Résultats clés

| Métrique | Valeur |
|---|---|
| Total lignes contrats | 4 818 |
| Source exploratoire | 4 144 lignes (86%) |
| Source officielle/manuelle | 674 lignes (14%) |
| Gaps ≥5 jours ouvrés | 46 périodes |
| % dates avec ≥2 contrats actifs | 14.9% |

## Couverture par mois contrat

La matrice de couverture (crop year × mois) est disponible dans le JSON.  
Seuils : 80%+ = acceptable, 60-80% = partiel, <60% = insuffisant.

## OI et volume

Stats Open Interest par mois contrat disponibles dans `artefacts/ema_study/ema_data_audit_v2.json`.

## Proxy vs officiel

Aucun overlap exploitable détecté entre proxy et officiel dans ce run.  
Les 674 lignes officielles/manuelles couvrent principalement 2024-2026.

## Artefact produit

`artefacts/ema_study/ema_data_audit_v2.json`
