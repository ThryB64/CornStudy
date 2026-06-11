# WEATHER FORECAST REVISION REPORT — V140-DATA / V155

_2026-06-11 · RESEARCH_ONLY_NOT_TRADING · données : Open-Meteo Previous Runs (gratuit)_

## Ce qui a été débloqué cette session

Le collecteur `openmeteo_previous_runs.py` était codé mais jamais lancé (réseau indisponible à la
session précédente). Premier lancement réel :

- **Bug réseau découvert et corrigé** : l'API Previous Runs n'expose les variables `_previous_dayN`
  qu'en **horaire** (les agrégats daily renvoient HTTP 400). Le collecteur fetch désormais en hourly et
  agrège par date de validité UTC (max pour tmax, somme pour precip). Tests offline inchangés et verts.
- **Collecte réelle** : 25 296 lignes, 17 zones (10 US corn belt + 7 EU), validités 2026-03-11 →
  2026-06-11, leads 0..7 complets, 0 erreur.
- **Archive append-only committée** : `data/weather/forecast_revisions.parquet` (40 Ko), dédupliquée
  sur (issue_date, valid_date, lead_day, zone, variable). **La fenêtre API n'est que ~92 jours : seule
  l'accumulation quotidienne construit un historique long.** Le daily CI append désormais (étape 15bis)
  et le workflow commite `data/weather/`.

## Anti-leakage

Format long lead-fixe : `issue_date = valid_date − lead_day`. Une révision `from_lead k → to_lead k−1`
est indexée par la date d'émission du run le plus récent : tout ce qui est utilisé au jour t était
publiquement connu au jour t. Test dédié `test_features_indexed_at_issue_date` vert.

## Features (V155, `build_revision_features`)

Par issue_date × région (us/eu), sur les révisions proches de l'échéance (from_lead 1..3) :
`rev_hot` (révision moyenne tmax, >0 = vers plus chaud), `rev_dry` (−révision precip, >0 = vers plus
sec), `bullish_revision = rev_hot + rev_dry` (canal V140 : chaud/sec US = soutien CBOT).

## Premier test exploratoire (honnête)

Révisions US vs rendements CBOT forward (ZC=F), 62 jours d'émission appariés (2026-03-09 → 2026-06-11) :

| Test | n | rho Spearman | p |
|---|---|---|---|
| rev_hot → CBOT h5 | 62 | −0.06 | 0.66 |
| rev_hot → CBOT h10 | 57 | −0.18 | 0.19 |
| rev_dry → CBOT h5 | 62 | +0.07 | 0.61 |
| rev_dry → CBOT h10 | 57 | +0.14 | 0.30 |
| bullish_revision → CBOT h5 | 62 | +0.11 | 0.40 |
| bullish_revision → CBOT h10 | 57 | +0.15 | 0.27 |

**Verdict : `PRELIMINARY_N_SMALL` — aucun signal démontré.** 4/6 tests dans le sens économique attendu
mais rien de significatif. Lecture honnête : (i) n=62 est très insuffisant (seuil interne : 150) ;
(ii) la fenêtre mars-juin est PRÉ-saison critique — le canal économique attendu (stress floraison juillet,
remplissage août) n'est pas encore actif ; (iii) cohérent avec V45 (réalisé price-in) : si la révision
porte un signal, il faut l'été pour le voir.

## Prochaine échéance

L'archive s'enrichit automatiquement chaque jour. **Re-run V155 prévu quand l'archive couvre juillet-août
2026 (saison de stress)** ou n≥150 jours d'émission. Aucun claim avant. Artefact :
`artefacts/v155/v155_weather_revision_results.json` (résultat négatif conservé).
