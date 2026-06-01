# Barchart EMA Expired Contracts

## Objectif

Valider si Barchart peut fournir l'historique des contrats Euronext Corn/EMA expirés pour reprendre `DATA-EMA-02`.

## Convention symbole

- Racine Barchart observée : `XB`
- Mois courants EMA retenus par défaut : `H` mars, `M` juin, `Q` août, `X` novembre
- Format : `XB{month_code}{year_2_digits}`, par exemple `XBQ10` pour août 2010
- Symboles `XBF..` : investigation legacy uniquement ; ne pas importer sans confirmation officielle

Le mapping fournisseur doit rester isolé dans `src/mais/collect/barchart_ema_probe.py`.

## Sonde

Commande :

```bash
venv/bin/python -m mais.collect.barchart_ema_probe --start-year 2010 --end-year 2026 --throttle-sec 2
```

Sorties :

- `artefacts/euronext/barchart_probe_results.csv`
- `artefacts/euronext/barchart_probe_report.txt`

Le probe teste 79 symboles :

- `XBH`, `XBM`, `XBQ`, `XBX` de 2010 à 2026 ;
- `XBF` de 2010 à 2020 pour investigation legacy.

## Champs recherchés

La source est considérée utilisable pour `DATA-EMA-02` seulement si les lignes historiques journalières sont accessibles automatiquement avec :

- date ;
- open, high, low ;
- close/last ou settlement ;
- volume ;
- open interest si disponible.

Si la page existe mais que les lignes historiques ne sont pas visibles dans le HTML public, le verdict reste `page_exists_no_download`. Dans ce cas, il faut une API Barchart OnDemand/Premier, un téléchargement manuel validé, ou une autre source.

## Résultat du probe réel — 2026-05-20

Commande lancée :

```bash
venv/bin/python -m mais.collect.barchart_ema_probe --start-year 2010 --end-year 2026 --throttle-sec 2
```

Résultat :

- 79 symboles testés ;
- 79 pages HTTP 200 ;
- H/M/Q/X : 68 pages trouvées, toutes classées `page_exists_no_download` ;
- F/Janvier : 11 pages trouvées, toutes classées `legacy_or_ambiguous` ;
- `has_download_button=True` sur 79 pages ;
- `has_historical_table=False` sur 79 pages ;
- `n_rows_visible=0` sur 79 pages.

Décision :

Barchart expose bien les pages et les métadonnées Euronext Corn pour les contrats expirés, mais l'historique journalier n'est pas visible dans le HTML public. Barchart ne débloque donc pas `DATA-EMA-02` en accès public automatisable.

Pour importer l'historique, il faut maintenant l'une des options suivantes :

- Barchart OnDemand/Premier ou API équivalente donnant accès aux séries OHLCV ;
- téléchargement manuel validé depuis un compte Barchart autorisé ;
- Euronext Web Services ;
- LSEG/Bloomberg ou autre fournisseur institutionnel.

## Verdicts

- `usable` : peut alimenter `DATA-EMA-02` ;
- `page_exists_no_download` : page et métadonnées trouvées, mais historique non importable automatiquement en accès public ;
- `unavailable` : page non exploitable ;
- `legacy_or_ambiguous` : mois non courant, notamment `F/Janvier`, exclu des séries finales.
