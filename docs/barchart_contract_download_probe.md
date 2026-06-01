# Barchart Contract Download Probe

## Objectif

Tester explicitement le téléchargement contrat par contrat Barchart sur un petit jeu de symboles :

- `XBM26`
- `XBQ26`
- `XBX26`
- `XBM14`

Ce ticket complète `DATA-EMA-09`, qui avait testé beaucoup de pages expirées, en isolant la question pratique : est-ce qu'un contrat récent ou ancien expose des lignes OHLC téléchargeables en accès public ?

## Commande

```bash
venv/bin/python -m mais.collect.barchart_contract_download_probe
```

Sorties :

- `artefacts/euronext/barchart_contract_download_results.csv`
- `artefacts/euronext/barchart_contract_download_report.txt`

## Verdicts

- `downloadable_public` : lignes historiques visibles dans le HTML public ;
- `page_exists_no_download` : page, métadonnées ou signaux download/API détectés, mais pas de lignes OHLC visibles ;
- `page_exists_metadata_only` : page trouvée sans signal de téléchargement ;
- `unavailable` : page inutilisable.

## Limite

Même si un bouton download apparaît sur la page, cela ne suffit pas : il faut des lignes historiques visibles ou une API/export accessible et autorisé. Sans cela, `DATA-EMA-02` reste bloqué.

## Résultat du probe réel — 2026-05-20

Commande lancée :

```bash
venv/bin/python -m mais.collect.barchart_contract_download_probe XBM26 XBQ26 XBX26 XBM14
```

Résultat :

| Symbole | HTTP | Contrat détecté | Verdict |
|---|---:|---|---|
| `XBM26` | 200 | Corn Jun 2026 | `page_exists_no_download` |
| `XBQ26` | 200 | Corn Aug 2026 | `page_exists_no_download` |
| `XBX26` | 200 | Corn Nov 2026 | `page_exists_no_download` |
| `XBM14` | 200 | Corn Jun 2014 | `page_exists_no_download` |

Les quatre pages contiennent des signaux `historical-download`, `downloadLimit`, `historicalFutures` et `core-api`, mais aucune ligne OHLC n'est visible dans le HTML public (`n_rows_visible=0`). La conclusion est donc la même pour contrats récents et ancien contrat : compte/API Barchart requis.
