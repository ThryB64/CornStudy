# Audit des données Euronext (EMA) — pour l'indicateur visuel

Date : 2026-06-13. Objet : identifier la série de prix Euronext utilisable pour visualiser
l'indicateur de vente CBOT sur l'historique européen.

## Fichier retenu
`data/processed/euronext/ema_liquid_continuous_adjusted.parquet` — série continue **la plus
liquide**, **back-adjusted** (recommandée par EXT006 pour éviter les artefacts de roll).

| Propriété | Valeur |
|---|---|
| Lignes | 3 377 |
| Période | **2010-01-04 → 2026-05-20** |
| Colonne date | `date` (quotidienne) |
| Colonne prix | `price` (**€/t**, settlement/close ajusté) |
| Fréquence | quotidienne (jours de bourse) |
| Doublons de date | 0 |
| Valeurs manquantes (prix) | 0 |
| Trous > 7 j | 46 (max 48 j ; week-ends/fériés + périodes creuses) |
| Lignes 2024+ | 542 |
| Prix (min/médiane/max) | 130.75 / 187.25 / 379.50 €/t |

## ⚠️ Limitation MAJEURE : série très majoritairement PROXY
La qualité de source est :

| `source_quality` | lignes | part |
|---|---|---|
| `exploratory` (proxy Barchart) | 3 275 | **97 %** |
| `official_or_manual` (Euronext) | 102 | 3 % (surtout 2024-2026) |

**La série n'est donc PAS de l'historique officiel Euronext** : 97 % des points sont un
**proxy exploratoire** dérivé de Barchart/CBOT, back-adjusté. Les autres séries du projet sont
pires : `data/raw/euronext_ema/euronext_ema.csv` est **100 % proxy** (`ema_is_proxy=True`,
5 417 lignes) ; `data/official_forward/ema_curve_history.parquet` ne contient que des
**features de courbe** (10 lignes, 2026). Aucune série de **settlements officiels Euronext
quotidiens 2010-2024** n'est disponible dans le projet (cf. V26 : seuls quelques settlements
officiels récents collectés).

## Conséquences
- La série est **utilisable pour une visualisation exploratoire** de l'indicateur (niveaux
  €/t plausibles, continue, datée), **mais pas pour une validation** : on évalue un score
  CBOT sur un **proxy** de prix Euronext, pas sur le vrai marché physique européen.
- **Aucune conclusion forte** ne peut être tirée de la performance « Euronext » : tout résultat
  est **illustratif**. Cela plafonne le verdict de l'indicateur à **RESEARCH_ONLY** au mieux.
- Le `source_quality` est conservé dans l'historique exporté pour tracer quelles dates sont
  proxy vs officielles.

## Verdict données : **USABLE_EXPLORATORY** (pas DATA_BLOCKED, pas OFFICIAL)
On peut construire et visualiser l'indicateur sur cette série, **à condition d'afficher
partout que la série est à 97 % un proxy**. Pour une vraie étude Euronext, il faudrait des
**settlements officiels Euronext quotidiens** (Euronext Live / Refinitiv / Nasdaq Data Link) —
voir `external_research/matrices/data_blocked_ideas.csv`.

## Format attendu (si remplacement par données officielles)
`date, price` (ou OHLC + `settlement` ; priorité `settlement`/`close`), quotidien, €/t,
idéalement par contrat avec roll volume-based pour une série continue propre.
