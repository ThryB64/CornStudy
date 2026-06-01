# Recherche source historique EMA OHLC

Date : 2026-05-20  
Ticket : DATA-EMA-15

## Verdict

Une source technique exploitable a ete identifiee pour reconstruire un historique exploratoire contrat par contrat :

- Barchart expose les contrats Euronext Corn sous la racine `XB`.
- Le HTML statique ne contient pas les lignes OHLC, mais le proxy web public utilise par la page `price-history/historical` renvoie des lignes EOD par contrat apres recuperation d'un cookie de session et du token `XSRF-TOKEN`.
- Les champs recuperables sont : date, open, high, low, last, priceChange, percentChange, volume, openInterest.
- Le champ settlement n'est pas expose explicitement par ce proxy. `lastPrice` doit donc etre traite comme `close_or_last`, pas comme settlement officiel sans validation croisee.

Ce n'est pas une source officielle stable de production. C'est une source candidate pour un backfill exploratoire, a isoler dans un collecteur fournisseur avec throttle, retries et audit de couverture. Pour une version juridiquement propre et robuste, les deux pistes contractuelles restent Barchart OnDemand/Premier et Euronext NextHistory.

## Sources officielles consultees

- Barchart OnDemand `getHistory` : API historique pour actions, indices, futures, FX et autres, avec types tick/minute/end-of-day et parametre `apikey`.
- Barchart Price History : la page indique que les visiteurs ont un historique quotidien limite, et que Barchart Premier donne acces a davantage de donnees historiques et aux telechargements CSV.
- Euronext Web Services : acces HTTP/JSON REST a la market data Euronext, avec formulaire de contact pour les donnees commodity derivatives.
- Euronext NextHistory : offre officielle historique, incluant End of Day Summary avec open, high, low, last, volumes, turnover, et livraison CSV/PCAP via Euronext Datashop SFTP.
- Databento Futures : source utile pour CBOT/CME, ICE, EEX, Eurex, mais aucune couverture Euronext/Matif n'a ete confirmee sur la page futures.

## Tests Euronext publics

Endpoint teste :

```text
https://live.euronext.com/en/intraday_historical/settlements/getChartData/EMA-DPAR/max?fOrO=F&md=<DD-MM-YYYY>&cOrP=&sp=
```

Resultats :

| `md` | Statut | Lignes | Conclusion |
|---|---:|---:|---|
| `01-03-2014` | 200 | 0 | contrat expire non disponible |
| `01-06-2014` | 200 | 0 | contrat expire non disponible |
| `01-08-2014` | 200 | 0 | contrat expire non disponible |
| `01-11-2014` | 200 | 0 | contrat expire non disponible |
| `01-03-2015` | 200 | 0 | contrat expire non disponible |
| `01-06-2015` | 200 | 0 | contrat expire non disponible |
| `01-08-2015` | 200 | 0 | contrat expire non disponible |
| `01-11-2015` | 200 | 0 | contrat expire non disponible |
| `01-06-2026` | 200 | 237 | actif 2026 disponible |
| `01-08-2026` | 200 | 185 | actif 2026 disponible |
| `01-11-2026` | 200 | 174 | actif 2026 disponible |

Conclusion : l'endpoint public Euronext est utile pour les contrats actifs, mais ne debloque pas le backfill 2010-2025. Les routes `gateway.euronext.com/api/...` testees sans authentification repondent `401 Unauthorized`.

## Tests Barchart OnDemand

Endpoints testes sans cle :

```text
https://ondemand.websol.barchart.com/getHistory.json?symbol=XBM14&type=daily&startDate=20140101&endDate=20141231
https://ondemand.websol.barchart.com/getHistory.csv?symbol=XBM14&type=daily&startDate=20140101&endDate=20141231
```

Resultat : `401 API key is missing or not valid`.

Conclusion : OnDemand est la voie contractuelle propre, mais necessite une cle API. C'est la meilleure option pour recuperer des champs complets, tester `dailyNearest`/`dailyContinue`, demander settlement explicite et eviter de dependre d'un proxy web.

## Tests Barchart proxy web

Sequence minimale valide :

1. Charger la page :

```text
https://www.barchart.com/futures/quotes/XBM26/price-history/historical
```

2. Recuperer les cookies de session, notamment `XSRF-TOKEN`.
3. Appeler le proxy :

```text
https://www.barchart.com/proxies/core-api/v1/historical/get
```

Parametres testes :

```text
symbol=XBM14
fields=tradeTime.format(m/d/Y),openPrice,highPrice,lowPrice,lastPrice,priceChange,percentChange,volume,openInterest
type=eod
orderBy=tradeTime
orderDir=asc
method=historical
limit=65
meta=field.shortName,field.type
raw=1
```

Exemples confirmes :

| Symbole | Lignes | Premiere date | Derniere date | Champs valides |
|---|---:|---|---|---|
| `XBF14` | 64 | 2013-10-04 | 2014-01-06 | OHLCV + OI |
| `XBH14` | 64 | 2013-12-03 | 2014-03-05 | OHLCV + OI |
| `XBM14` | 64 | 2014-03-05 | 2014-06-05 | OHLCV + OI |
| `XBQ14` | 64 | 2014-05-08 | 2014-08-05 | OHLCV + OI |
| `XBX14` | 64 | 2014-08-08 | 2014-11-05 | OHLCV + OI |
| `XBX21` | 64 | 2021-08-10 | 2021-11-05 | OHLCV + OI |
| `XBF22` | 64 | 2021-10-08 | 2022-01-05 | OHLCV + OI |
| `XBH23` | 64 | 2022-12-06 | 2023-03-06 | OHLCV + OI |
| `XBM26` | 64 | 2026-02-17 | 2026-05-20 | OHLCV + OI |

Le endpoint `quotes/get` confirme aussi la liste des contrats par racine :

```text
list=futures.historical.byRoot(XB)
```

Resultat observe :

- `count=120`, `total=120` contrats disponibles.
- Selection 2010-2026 : 81 contrats.
- Mois disponibles 2010-2022 : `F/H/M/Q/X`.
- Mois disponibles 2023-2026 : `H/M/Q/X`.

## Reconstruction memoire rapide

Un prototype en memoire a appele les 81 contrats 2010-2026. Il n'a rien ecrit dans `data/`.

Resultat du premier run rapide :

- 4 480 lignes EOD recuperees ;
- 3 528 dates uniques ;
- plage observee : 2009-10-06 a 2026-05-20 ;
- couverture jours ouvrables 2010-2020 : environ 96.6 % a 98.1 % selon l'annee ;
- un throttle trop faible a provoque des `429 Too Many Attempts` sur une partie 2021-2023 ;
- des retries ralentis sur `XBX21`, `XBF22`, `XBH23` ont ensuite reussi, ce qui confirme que le trou 2021-2023 etait un probleme de cadence, pas une absence de donnees.

Limites de couverture :

- Chaque contrat public renvoie environ 64 lignes EOD, soit la fenetre visible de la page.
- Le mois `F` existe jusqu'en 2022 dans Barchart, mais disparait des contrats listes a partir de 2023.
- Sans `F`, les series post-2022 ont plus de trous calendaires et doivent etre reconstruites prudemment.
- Il faut choisir une regle de roll explicite : maximum volume, maximum open interest, ou calendrier par contrat.

## Validation couverture lente DATA-EMA-02

Commande lancee :

```bash
venv/bin/python -m mais.cli backfill euronext --from 2010-01-01 --to 2026-05-20 --throttle-sec 3 --barchart-coverage-only
```

Sorties produites :

- `artefacts/euronext/barchart_xb_eod_coverage_contracts.csv`
- `artefacts/euronext/barchart_xb_eod_coverage_by_year.csv`
- `artefacts/euronext/barchart_xb_eod_coverage_report.txt`

Resultat :

| Univers | Definition | Crop years complets >= 90 % | Couverture moyenne crop years complets | Verdict |
|---|---|---:|---:|---|
| `strict_official` | H/M/Q/X uniquement | 7 | 89.854 % | insuffisant pour GO strict |
| `exploratory_with_F` | F/H/M/Q/X | 13 | 95.935 % | `GO_EXPLORATORY` |

Tous les 81 contrats testes ont retourne des lignes utilisables (`verdict=usable`) sans retry (`total_retries=0`).

Conclusion importante :

- Barchart proxy web debloque un historique exploratoire tres solide si on accepte `F/Janvier`.
- La version stricte officielle H/M/Q/X reste juste sous le seuil : 7 crop years >= 90 % au lieu de 8.
- Les contrats `F` ne doivent donc pas entrer silencieusement dans les series finales. Ils peuvent servir a diagnostiquer la couverture et a tester la sensibilite, mais la version finale doit rester marquee comme exploratoire tant qu'une source officielle ne confirme pas leur usage.
- Toute importation Barchart doit utiliser `source = "barchart_proxy_exploratory"` et conserver `lastPrice` dans `close_or_last`, sans le renommer `settlement`.

## Backfill strict H/M/Q/X execute

Commande lancee apres validation de couverture :

```bash
venv/bin/python -m mais.cli backfill euronext --from 2010-01-01 --to 2026-05-20 --throttle-sec 3
```

Resultat CLI :

```text
EMA backfill: source=barchart_proxy_exploratory rows=4333 coverage=90.009% contracts=68
```

Controle du parquet `data/processed/euronext/ema_contract_daily.parquet` :

- 4 818 lignes au total ;
- 4 144 lignes conservees avec `source = "barchart_proxy_exploratory"` apres fusion/deduplication ;
- 664 lignes `euronext_chart_history` et 10 lignes `euronext_ajax_prices` deja presentes conservees comme sources plus prioritaires ;
- 0 ligne `F/Janvier` ;
- plage observee : 2010-01-04 -> 2026-05-20 ;
- `close_or_last` non nul sur 4 144 lignes Barchart ;
- `settlement` reste nul sur les lignes Barchart, comme voulu.

Le rapport `artefacts/backfill_coverage_report.json` garde `coverage_status = "PARTIAL_REQUIRES_MANUAL_BACKFILL"` : le backfill est suffisant pour experimenter, mais pas encore une source finale officielle.

## Comparaison des options

| Option | Statut | Avantage | Limite |
|---|---|---|---|
| Barchart proxy web | Candidate technique | OHLCV/OI disponibles maintenant par contrat `XB` | Non officiel, rate-limite, settlement non explicite |
| Barchart OnDemand/Premier | Recommande production | API documentee, historique futures, continu/nearest possible | Cle API ou compte requis |
| Euronext public live | Valide quotidien actif | Source officielle pour collecte quotidienne | Contrats expires non disponibles |
| Euronext Web Services | Recommande production | REST/JSON officiel, commodity derivatives dans le formulaire | Authentification/contrat requis |
| Euronext NextHistory | Recommande historique officiel | EOD officiel, CSV SFTP, backtesting | Acces commercial |
| Databento | Utile CBOT, pas EMA confirme | API moderne, OHLCV, reference data | Pas de couverture Euronext/Matif confirmee |
| Nasdaq Data Link / Quandl | Non confirme | Potentiellement historique continu | Aucune reference verifiee `CHRIS/LIFFE_EMA1` trouvee |

## Decision pour la suite

1. Utiliser Barchart proxy web comme source candidate exploratoire pour debloquer la table de contrats et tester le pivot EMA.
2. Ne pas presenter cette source comme officielle ou stable.
3. Garder `lastPrice` sous le nom `close_or_last` tant que settlement n'est pas valide par Euronext/Barchart OnDemand.
4. Implementer le prochain ticket avec une couche fournisseur isolee :

```python
def build_barchart_symbol(month_code: str, year: int) -> str:
    return f"XB{month_code}{str(year)[-2:]}"
```

5. Ajouter un throttle minimal de 1 a 2 secondes et retries exponentiels sur `429`.
6. Produire d'abord la reference contrats (`DATA-EMA-10`) depuis `futures.historical.byRoot(XB)`, avec `XBF..` marque `legacy_or_ambiguous` mais techniquement disponible jusqu'en 2022.
7. Lancer ensuite `DATA-EMA-02` sur une commande de backfill controlee, avec audit de couverture avant import dans les donnees finales.
