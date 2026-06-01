# Série Continue EMA Historique

## Objectif

Chercher une série longue déjà rollée par un fournisseur (`provider_rolled_continuous`) pour tester rapidement le pivot EMA, même si elle ne remplace pas le backfill contrat par contrat.

## Candidats testés

Le ticket `DATA-EMA-13` teste :

- yfinance : `EMA=F`, `ZCE=F` ;
- Barchart/pages web : `XB*0`, `XB00`, `XB1!`, `EMA1!`, `EMA1`.

## Commande

```bash
venv/bin/python -m mais.collect.ema_continuous_series_probe
```

Sorties :

- `artefacts/euronext/ema_continuous_probe_results.csv`
- `artefacts/euronext/ema_continuous_probe_report.txt`

## Interprétation

Verdicts :

- `usable_continuous` : série longue exploitable, mais déjà rollée par le fournisseur ;
- `page_exists_no_download` : page et métadonnées trouvées, mais OHLC non visible en HTML public ;
- `empty_or_short` : source téléchargeable mais historique insuffisant ;
- `unavailable` : rien d'exploitable.

## Limite méthodologique

Une série continue fournisseur peut servir à tester :

- direction EMA H20/H40/H60 ;
- comparaison rapide CBOT vs EMA ;
- intérêt métier du pivot.

Elle ne suffit pas pour :

- construire une courbe EMA ;
- auditer les rolls ;
- calculer la liquidité par maturité ;
- faire un backtest stockage propre par contrat.

Pour ces usages, il faut toujours `DATA-EMA-10` puis `DATA-EMA-02`.

## Résultat du probe réel — 2026-05-20

Commande lancée :

```bash
venv/bin/python -m mais.collect.ema_continuous_series_probe
```

Résultat :

| Provider | Symbole | Verdict | Détail |
|---|---|---|---|
| yfinance | `EMA=F` | `unavailable` | ticker introuvable / téléchargement vide |
| yfinance | `ZCE=F` | `unavailable` | ticker introuvable / téléchargement vide |
| Barchart | `XB*0` | `page_exists_no_download` | page Euronext Corn trouvée, bouton download détecté, aucune ligne OHLC visible |
| Barchart | `XB00` | `unavailable` | page 404 |
| Barchart | `XB1!` | `unavailable` | page 404 |
| Barchart | `EMA1!` | `unavailable` | page 404 |
| Barchart | `EMA1` | `unavailable` | page 404 |

Décision :

Aucune série continue EMA longue n'est exploitable en accès public automatique. `XB*0` confirme seulement l'existence d'une page Barchart continue, mais pas l'accès aux lignes OHLC. Il faut encore un export fournisseur/API ou CSV manuel.
