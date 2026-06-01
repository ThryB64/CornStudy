# V23 — Risque drawdown CBOT + régime basis + déblocage météo-prévue live

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v23_cbot_risk_and_regime.py` · runner `run_v23.py` · tests (2 PASS)
**Artefacts** : `artefacts/v23/` (cbot_drawdown_risk, regime_conditional_basis, live_forecast_snapshot)
**Données** : hors holdout 2024 ; holdout verrouillé. Règle basis inchangée.

Enrichissement post-V22 : formaliser la meilleure trouvaille CBOT, tester un raffinement du mécanisme V21,
et **débloquer réellement** la collecte météo-prévue (réseau disponible).

---

## V23-01 — Module risque de drawdown CBOT (formalisé)

La meilleure trouvaille CBOT (V19 : les baisses sont prévisibles) devient un **score de risque OOF** :

| Cible | AUC OOF (technique + météo réalisée) | base rate |
|---|---:|---:|
| drawdown 5% h20 | 0.668 | 0.34 |
| **drawdown 8% h40** | **0.738** | 0.32 |

Sortie : un **contexte `drawdown_risk` low/medium/high** (terciles de la proba), à afficher à côté du signal
de prime. Utile et fiable, contrairement à la direction CBOT brute (~0.53).

## V23-02 — Régime CBOT et reversion du basis : hypothèse RÉFUTÉE (honnête)

Hypothèse (issue de V21) : la règle short basis-haut marcherait **mieux quand le CBOT est sous sa tendance**
(plus de marge pour rebondir → compression via hausse CBOT).

| Régime CBOT à l'entrée | n | win rate | mean PnL €/t | jambe CBOT moy. | jambe EMA moy. | part CBOT dominante |
|---|---:|---:|---:|---:|---:|---:|
| **sous** sa tendance | 21 | 0.81 | 10.5 | 0.050 | 0.001 | **0.71** |
| **au-dessus** de sa tendance | 18 | 1.00 | 22.0 | 0.080 | 0.021 | 0.56 |

**Résultat honnête** : l'hypothèse est **FAUSSE**. Les entrées **au-dessus** de la tendance font *mieux*
(win 1.00, PnL 22.0 vs 10.5) — la règle ne bénéficie pas d'un filtre « CBOT sous tendance ». (Cohérent avec
V11-02 qui rejetait déjà un filtre de régime forward.)

**Mais découverte robuste** : la **jambe CBOT domine dans les DEUX régimes** (part dominante 0.71 sous /
0.56 au-dessus ; jambe CBOT ≫ jambe EMA partout). → **V21 confirmé et renforcé** : la compression de la
prime vient surtout d'une hausse du CBOT *quel que soit le régime*. Pas de filtre régime à ajouter
(discipline anti sur-filtrage).

## V23-03 — Déblocage : collecte météo-prévue LIVE réussie

Réseau disponible → `fetch_forecast(region="us")` collecte une vraie prévision US Corn Belt (10 zones,
J+1..J+15), passe `assert_forecast_no_leakage`, et `build_forecast_features` produit les features pondérées
(anomalies/révisions/phénologie). Snapshot réel : `issue_date=2026-05-31`, tmax pondéré ~31.1°C, etc.

**Le pipeline forecast est opérationnel end-to-end sur données réelles.** Le collecteur gère proprement les
erreurs réseau transitoires (502 → `SKIP`, pas de crash).

> **Reste à faire (data)** : pour un **backtest** rigoureux des révisions de prévision, il faut l'archive
> **Previous-Runs** (prévisions telles qu'émises à chaque date passée, multi-lead) — désormais faisable
> (réseau OK), avec le protocole anti-leakage déjà en place. Le forecast simple par date est proche du
> réalisé (risque de leakage multi-lead) → ne pas l'utiliser tel quel pour le backtest forward.

---

## Synthèse V23

| Question | Réponse |
|---|---|
| Risque de drawdown CBOT exploitable ? | **Oui** (AUC 0.74 à h40) → contexte `drawdown_risk`. |
| Filtrer le short basis-haut par régime CBOT ? | **Non** — au-dessus de tendance fait même mieux ; pas de filtre. |
| La compression est-elle CBOT-driven dans tous les régimes ? | **Oui** (jambe CBOT domine partout) → V21 robuste. |
| Collecte météo-prévue ? | **Débloquée et démontrée live** (anti-leakage OK). |

## Décisions

- `drawdown_risk` (V23-01) : intégré comme **contexte** (déjà présent dans V21 via une heuristique ;
  V23-01 fournit la version modèle OOF AUC 0.74). Pas un veto.
- Filtre de régime : **rejeté** (V23-02). Indicateur inchangé.
- Météo-prévue forward : **opérationnelle**. Backtest des révisions = prochaine tâche data (Previous-Runs).

---

*V23 — 2026-05-31. Risque drawdown CBOT formalisé (0.74), filtre régime rejeté honnêtement, compression*
*CBOT-driven robuste tous régimes, collecte météo-prévue débloquée live. Research-only, règle basis inchangée.*
