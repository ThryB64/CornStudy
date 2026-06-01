# V43 — Matrice de qualité de signal (ADVERSE_RISK × CBOT_SUPPORT)

Session 2026-06-01. Synthèse de V38 (ADVERSE_RISK) et V41 (CBOT_SUPPORT) en une lecture unique de qualité,
sans nouveau modèle ni touche à la règle. Descriptif, CONTEXTE jamais un veto. `RESEARCH_ONLY_NOT_TRADING`.

## Quality = ADVERSE_RISK bas + CBOT soutenu
`signal_quality` croise les deux par date : **HIGH** = prime propre (ADVERSE_RISK LOW) + CBOT soutenu ;
**LOW** = prime justifiée (ADVERSE_RISK HIGH) + CBOT faible ; **MEDIUM** sinon.

| quality | n | taux ADVERSE | win | PnL z→0 |
|---|---:|---:|---:|---:|
| LOW | 3 | 0.333 | 0.67 | −0.3 |
| MEDIUM | 38 | 0.158 | 0.82 | 12.8 |
| HIGH | 1 | 0.0 | 1.0 | 53.0 |

→ monotone (ADVERSE ↓, PnL ↑) = `QUALITY_SEPARATES_OUTCOMES`. **Mais les extrêmes sont fins (HIGH n=1,
LOW n=3)** — à confirmer en forward.

## Matrice ADVERSE_RISK × CBOT_SUPPORT (la cellule solide)
| | CBOT faible | CBOT soutenu |
|---|---|---|
| **ADVERSE_RISK LOW** | n=4, ADV 0%, PnL 21.3 | n=1, ADV 0%, PnL 53.0 |
| **ADVERSE_RISK MEDIUM** | **n=16, ADV 25%, PnL 6.9** | **n=17, ADV 11.8%, PnL 15.9** |
| **ADVERSE_RISK HIGH** | n=3, ADV 33%, PnL −0.3 | n=1, ADV 0%, PnL 21.0 |

**Le résultat statistiquement robuste** (n adéquat) est le bucket MEDIUM : à ADVERSE_RISK égal, un **CBOT
soutenu divise l'ADVERSE par ~2 (11.8% vs 25%) et double le PnL (15.9 vs 6.9)**. C'est la confirmation,
au sein du bucket dominant, de l'effet CBOT_SUPPORT (V41/V39-E4-E6). Le coin franchement mauvais reste
HIGH|faible (ADV 33%, PnL négatif).

## Lecture & rapport
Bloc ajouté au rapport quotidien (3e contexte après ADVERSE_RISK et CBOT_SUPPORT). Signal LIVE 1er juin :
quality **MEDIUM** (ADVERSE_RISK LOW *mais* CBOT_SUPPORT LOW) — prime propre mais CBOT non porteur :
lecture nuancée, objectif prudent indiqué. Module l'objectif, jamais le signal.

## Synthèse
- La qualité combinée sépare les issues, mais sa valeur statistiquement sûre vient de l'effet
  CBOT_SUPPORT **dans** le bucket ADVERSE_RISK dominant (n=16 vs 17).
- Discipline : extrêmes fins signalés, aucun fold dans la règle, contexte seulement.
- Tests `tests/test_v43_signal_quality.py` (2 PASS). Artefacts `artefacts/v43/`.
