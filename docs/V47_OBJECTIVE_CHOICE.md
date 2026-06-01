# V47 — Choix d'objectif : z→0.5 (prudent) vs z→0 (complet)

Session 2026-06-01. La règle figée propose deux objectifs de sortie ; V47 répond à « lequel viser ? » en
comparant les deux à **conditions ÉGALES** (même stop −20, même horizon 90 j, recalcul via `_sim_detail`).
`RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé. Règle figée inchangée (on produit une recommandation
d'objectif, pas un changement de règle). Module `src/mais/research/v47_objective_choice.py`, tests (2 PASS).

## Global (42 trades)
| objectif | PnL moyen | jours moyens |
|---|---:|---:|
| z→0 (complet) | **12.8** | 42.5 |
| z→0.5 (prudent) | 10.3 | 28.6 |

z→0 gagne en PnL moyen (z0 bat z0.5 dans 59.5 % des trades) **mais tient 50 % plus longtemps**.

## DÉCOUVERTE : le bon objectif dépend du CBOT_SUPPORT
| CBOT_SUPPORT | n | PnL z→0 | PnL z→0.5 | z0 bat z0.5 | jours z→0 | jours z→0.5 |
|---|---:|---:|---:|---:|---:|---:|
| **LOW** (faible) | 23 | 8.44 | 8.24 | 0.48 | 38.6 | 28.8 |
| **MEDIUM** | 11 | **21.3** | 13.7 | 0.82 | 56.9 | 36.9 |
| **HIGH** | 8 | 13.8 | 11.6 | 0.63 | 33.8 | 16.9 |

- **CBOT soutenu (MEDIUM)** : viser **z→0** paie nettement (**+7.6 €/t** vs z→0.5) — la réversion complète
  se réalise quand le CBOT rattrape. C'est la logique du mécanisme (compression CBOT-driven).
- **CBOT faible (LOW)** : z→0 n'ajoute quasi RIEN (**+0.2 €/t**) tout en tenant **~9.8 j de plus** →
  **z→0.5 est plus efficace** (même gain, moins d'exposition / portage / risque ADVERSE).

## Interprétation honnête
La recommandation contexte (« z→0 si CBOT soutenu, sinon z→0.5 ») donne un PnL ≈ identique à *toujours z→0*
(12.7 vs 12.8) : **le gain n'est PAS en PnL brut mais en efficacité risque/temps** — on capte la réversion
complète là où elle paie (CBOT porteur) et on sort plus tôt là où z→0 ne sert à rien (CBOT faible).
Verdict : `OBJECTIVE_CHOICE_IS_RISK_EFFICIENCY`.

## Lecture opérationnelle
- Signal actif + **CBOT_SUPPORT MEDIUM/HIGH** → objectif **z→0** (laisser la réversion se compléter).
- Signal actif + **CBOT_SUPPORT LOW** → objectif **z→0.5** (verrouiller, ne pas s'exposer pour 0.2 €/t).
- Contexte, pas un veto ; n petit (42), à confirmer en forward. Aucune touche à la règle figée.
