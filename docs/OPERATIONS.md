# Exploitation quotidienne

Ce document décrit la boucle quotidienne de production du projet maïs CBOT.

## Commande principale

```bash
make daily
```

Équivalent CLI:

```bash
venv/bin/python -m mais.cli daily-run
```

Par défaut, cette commande exécute:

1. `features` - reconstruit `data/processed/features.parquet`.
2. `targets` - reconstruit les cibles J+5/J+10/J+20/J+30.
3. `audit_leakage` - vérifie l'absence de fuite temporelle.
4. `factors` - reconstruit les facteurs économiques synthétiques.
5. `study` - régénère l'étude professionnelle, SHAP, CQR et régimes.
6. `farmer_backtest` - simule les règles de vente agriculteur contre les baselines.

Le statut est écrit dans:

- `artefacts/daily/daily_status.json`
- `artefacts/daily/daily_status.parquet`

La commande de consultation rapide est:

```bash
make status
```

## Collecte officielle

Sur un serveur configuré avec les clés nécessaires, lancer:

```bash
venv/bin/python -m mais.cli daily-run --collect
```

Les collecteurs sans clé publique restent explicites. Si une source officielle
échoue, le statut quotidien passe en `FAIL` et l'étape concernée contient le
message d'erreur.

Variables d'environnement utiles:

- `FRED_API_KEY`
- `EIA_API_KEY`
- `NASS_API_KEY`
- `FAS_API_KEY`

## Cron recommandé

Exemple simple, chaque jour ouvré à 07:15 heure serveur:

```cron
15 7 * * 1-5 cd /path/to/CornStudy && venv/bin/python -m mais.cli daily-run --collect >> logs/cron_daily.log 2>&1
```

Si les sources officielles ne sont pas encore toutes configurées:

```cron
15 7 * * 1-5 cd /path/to/CornStudy && venv/bin/python -m mais.cli daily-run --no-collect >> logs/cron_daily.log 2>&1
```

## Artefacts de décision

- Étude professionnelle: `docs/PROFESSIONAL_STUDY_REPORT.md`
- Analyse factorielle: `docs/FACTOR_ANALYSIS_REPORT.md`
- Backtest agriculteur: `docs/FARMER_BACKTEST_REPORT.md`
- Décision courante: `artefacts/professional_study/decision_snapshot.json`
- Backtest revenu: `artefacts/farmer_backtest/summary.json`

## Lecture des métriques

Le système ne doit pas être jugé uniquement au RMSE. Les métriques clés sont:

- revenu net moyen USD/bu;
- pourcentage d'années où le modèle bat `sell_at_harvest_100`;
- Sharpe annuel du revenu;
- couverture réelle des intervalles CQR;
- statut anti-fuite.

Une amélioration statistique faible peut être acceptable si la décision réduit
le risque commercial. À l'inverse, une bonne précision directionnelle ne suffit
pas si le revenu simulé n'améliore pas les baselines agriculteur.
