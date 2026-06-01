# V49 / V50 — Jambe long premium + ADVERSE casebook

Session 2026-06-01. Deux incréments descriptifs, sans toucher la règle figée (short-only).
`RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé.

## V49 — Jambe LONG premium (test d'asymétrie)
Question symétrique du short : quand `basis_z < −1` (EMA anormalement BAS vs CBOT), le basis remonte-t-il ?
Méthode en miroir exact (entrée non-overlap, sortie z→−0.5/z→0, stop −20, max 90 j).

| jambe | n | win | PnL moyen | ADVERSE | jours |
|---|---:|---:|---:|---:|---:|
| **LONG** (basis_z<−1) | 40 | 0.75 | **8.2** | 0.25 | 37.6 |
| **SHORT** (basis_z>1) | 42 | 0.81 | **12.8** | — | 42.5 |

→ `ASYMMETRY_CONFIRMED_SHORT_BETTER`. La jambe longue **fonctionne** (PnL positif, 75 % win) mais reste
**nettement plus faible** que la jambe courte. Cohérent : vendre une prime EU trop chère est plus robuste
qu'acheter une prime trop basse (une prime basse peut refléter une faiblesse réelle d'EMA / un CBOT trop
cher qui se corrige autrement). **La règle reste short-only** ; la jambe longue est documentée, pas activée.

## V50 — ADVERSE casebook
Archéologie qualitative des 7 trades short-premium perdants (`docs/ADVERSE_CASEBOOK.md`). Raisons probables
agrégées :

| fréquence | raison probable |
|---:|---|
| **6×** | prime seulement modérée (z<1.5) |
| **5×** | CBOT non porteur (pas de rattrapage) |
| 2× | mois de roll |
| 2× | année de crise (2020-2022) |

→ Les pertes se concentrent sur **primes modérées + CBOT non porteur** — confirmation qualitative directe de
V32 (primes modérées échouent), V41/V39 (CBOT support), et de l'asymétrie. Le casebook sert à **reconnaître
ces contextes avant l'entrée** (warning), pas à filtrer durement (anti sur-filtrage V15).

## Synthèse
- Asymétrie short≫long confirmée chiffrée (12.8 vs 8.2 €/t).
- Les ADVERSE ont une signature qualitative claire et cohérente avec tous les modules de contexte.
- Tests `test_v49` (2) + `test_v50` (1) PASS. Artefacts `artefacts/v49`, `artefacts/v50`. Règle inchangée.
