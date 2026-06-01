# ADVERSE casebook enrichi (V58)

Pile de diagnostics complète par trade perdant + « le warning aurait-il aidé ? ». Descriptif, anti-leakage, règle figée inchangée. `RESEARCH_ONLY_NOT_TRADING`.

7 trades ADVERSE. Le warning (objectif prudent recommandé) aurait été levé sur **5/7** (71%). CBOT non porteur : 5/7. Prime modérée (z<1.5) : 6/7.

| entrée | z | basis | ADVERSE_RISK | CBOT_SUPPORT | PHYS_TENSION | objectif reco | warning ? | PnL |
|---|---:|---:|---|---|---|---|:--:|---:|
| 2010-05-24 | 1.16 | 36.9 | MEDIUM | MEDIUM | LOW | z->0 | — | -22.8 |
| 2013-09-16 | 1.33 | 34.8 | MEDIUM | LOW | NO_CURVE_DATA | z->0.5 | ✅ prudent | -27.0 |
| 2014-03-06 | 1.02 | 46.8 | MEDIUM | HIGH | LOW | z->0 | — | -15.9 |
| 2018-06-15 | 1.25 | 45.7 | MEDIUM | LOW | NO_CURVE_DATA | z->0.5 | ✅ prudent | -22.0 |
| 2020-03-18 | 1.27 | 42.7 | HIGH | LOW | NO_CURVE_DATA | z->0.5 | ✅ prudent | -23.4 |
| 2020-04-27 | 2.18 | 50.9 | MEDIUM | LOW | NO_CURVE_DATA | z->0.5 | ✅ prudent | -2.1 |
| 2025-07-09 | 1.01 | 61.9 | MEDIUM | LOW | LOW | z->0.5 | ✅ prudent | -11.6 |

## Lecture

Sur 7 pertes, la pile de diagnostics aurait recommandé l'objectif PRUDENT (verrouiller plus tôt) dans 71% des cas — surtout via un CBOT non porteur. Le warning n'aurait PAS évité l'entrée (ce n'est jamais un veto) mais aurait incité à un objectif z→0.5, réduisant l'exposition au chemin adverse. Cohérent V56/V57 : sans CBOT porteur, viser le complet n'apporte rien et allonge l'exposition. Quelques pertes restent non flaggées (prime forte + contexte apparemment porteur) : ce sont les ADVERSE irréductibles à surveiller en forward.