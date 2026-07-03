# EXT013 — Résultats : basis & transmission spot/futures

**Verdict : DATA_BLOCKED.** Voir `basis_data_audit.md`.

Deux blocages : (1) pas d'EUR/USD quotidien historique (seul le DXY existe ; l'ECB
eurusd interne couvre 13 jours de 2026) → basis €/t homogène non reconstructible en
externe ; (2) pas de spot physique UE quotidien (COMEXT est mensuel/transactionnel).
Aucun `basis_features.csv` ni `metrics_ext013.csv` produit. Plan d'acquisition (eurusd
FRED/ECB + spot FranceAgriMer) dans l'audit ; volet VECM CBOT↔EMA réorientable en P2
une fois l'eurusd réglé.
