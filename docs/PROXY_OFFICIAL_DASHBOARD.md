# Dashboard proxy vs officiel (V103)

Validation continue de la source EMA. `RESEARCH_ONLY_NOT_TRADING`.

## Historique (proxy Barchart vs EMA officiel, overlap 2010-2022)
- corrélation 0.941116138174688 · MAE 37.28746097610513 €/t · verdict **PROXY_FORBIDDEN**
- Lecture : niveau proxy interdit en absolu ; z-score relatif utilisable.

## Forward officiel (journal V27)
- jours : **2** · plage ['2026-05-29', '2026-06-01'] · signaux 2
- basis officiel [75.9, 76.2] €/t · z [2.04, 2.06] · source z {'proxy_implied': 2}

## Milestones research→paper
- 10 j : pending
- 40 j : pending
- 90 j : pending
- 180 j : pending
- 365 j : pending

Prochain palier : **10 j**. Statut : **PROXY_RESEARCH_ONLY**.

## Limite
Comparaison forward proxy↔officiel sur dates communes = PENDING (master features arrêté mi-2025). À activer dès ré-collecte ou proxy live parallèle.