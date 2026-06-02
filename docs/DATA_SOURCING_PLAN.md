# Plan de sourcing des données (V134)

Statut : RESEARCH_ONLY_NOT_TRADING. Tenu à jour quand une source change de statut.
Quand une brique est `DATA_BLOCKED`, ce tableau est la feuille de route.

| Source | Usage | Dispo | Coût | API | Contraintes | Statut | Débloque |
|--------|-------|-------|------|-----|-------------|--------|----------|
| Euronext Web Services / Datashop | Historique officiel EMA/EBM profond | commercial | abonnement | REST licence | redistribution restreinte | WATCHLIST | V126 hist., z rolling V27, PHYSICAL_TENSION backtest |
| Bloomberg/LSEG/Barchart/CQG/TT | Intraday CBOT + EMA aligné, courbe profonde | commercial | élevé | propriétaire | coût, licence | DATA_BLOCKED_PAID | V128 intraday, courbe hist. |
| Open-Meteo Historical Forecast | Archive prévisions « telle que connue J » (révisions) | gratuit | 0 | REST public | timeouts longues fenêtres | PARTIAL_BEST_EFFORT | V127 révisions multi-lead |
| NOAA GFS/GEFS (ensemble) | Prévision d'ensemble (incertitude/extrêmes) | gratuit | 0 | NOMADS/grib | volumineux, parsing lourd | WATCHLIST | V127 incertitude fine |
| EC MARS (JRC) | Anticipations rendement maïs EU | public | 0 | pas d'API (PDF/portail) | format non structuré, mensuel | PARTIAL_BEST_EFFORT | balance EU (V71), EU_BALANCE_UPDATE (V129) |
| FranceAgriMer | Bilans/stocks maïs France | public | 0 | datasets/portail | publication décalée | PARTIAL_BEST_EFFORT | driver local FR (V71b) |
| Eurostat COMEXT (DS-045409) | Flux physiques import/export maïs EU | public hors API | 0 | non exposé | bulk download manuel | DATA_BLOCKED | flux physiques EU |
| USDA NASS QuickStats / WASDE cal. | Dates exactes des rapports (catalyseurs) | gratuit | 0 | QuickStats REST (clé) | clé API, calendrier à scraper | WATCHLIST | attribution CBOT_WASDE (V129) |
| CFTC f_disagg (COT) | Managed-money net %OI | gratuit | 0 | fichier texte | hebdomadaire | **OK** | déjà branché (V107) |
| DX=F (dollar index) | Contexte dollar | Yahoo 404 | 0 | indispo | endpoint cassé | DATA_BLOCKED_SUBSTITUTED | substitut EUR/USD suffit |

## Priorités (gratuit / best-effort)

1. **Open-Meteo Historical Forecast** → révisions de prévision multi-lead (V127), choc d'information leading.
2. **USDA QuickStats + calendrier WASDE** → attribution exacte `CBOT_WASDE` dans le catalogue d'événements (V129).
3. **EC MARS + FranceAgriMer** → balance EU / driver local (V71/V71b, EU_BALANCE_UPDATE).

## Seul vrai déblocage payant

L'**historique officiel profond** (Euronext/Bloomberg) lèverait le `proxy_implied` du z-score officiel et
permettrait un backtest de PHYSICAL_TENSION. À défaut, le **forward l'accumule gratuitement** (journaux
append-only) : c'est la stratégie retenue, cohérente avec le statut research.
