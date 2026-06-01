# Carte causale du marché du maïs (CBOT / Euronext EMA)

But : formaliser le graphe causal pour tester des ARÊTES (liens), pas des variables au hasard. Chaque arête
porte un **statut empirique** (validé / fragile / rejeté / data-gated) et le module qui l'a testée.
`RESEARCH_ONLY_NOT_TRADING`.

---

## Graphe (texte)

```
         météo US extrême ──(+, anticipé)──▶ CBOT (prix mondial)
                  │                                │
                  │                                │ (rattrapage)
                  ▼                                ▼
         [pas d'effet net]              compression du BASIS  ◀──(pivot)── CBOT_SUPPORT
                                                  ▲                         (momentum/SMA/COT)
                                                  │
   FX EUR/USD ──(conversion)──▶ CBOT_eur_t ───────┤
                                                  │
   EMA settlement ───────────────────────────────┤──▶ BASIS = EMA − CBOT_eur_t
                                                  │
   substitution blé/maïs EU ──(+, justifie)──────▶│   (basis haut soutenu → moins compressible)
   (MATIF wheat/corn)                             │
                                                  │
   courbe EMA (backwardation) ──(tension)────────▶│   (basis haut + backwardation → compression lente)
                                                  │
   roll Euronext ──(bruit/microstructure)────────▶│
                                                  │
   désync horaire EMA/CBOT ──(bruit)─────────────▶│
                                                  │
   météo EU extrême ──(+, justifie prime)────────▶│   [data-gated]
```

---

## Arêtes et statut empirique

| # | Arête (cause → effet) | Signe attendu | Statut | Module |
|---|---|---|---|---|
| 1 | météo US extrême → CBOT | + (rally) | **fragile/anticipé** (queue réelle, corr backward≫forward) | V48/V51 |
| 2 | météo US extrême → basis | ? | **rejeté** (pas de driver net ; basis plutôt plus bas) | V60 |
| 3 | CBOT (rattrapage) → compression basis | + | **validé** (compression CBOT-driven majoritaire) | V21/V35/V57 |
| 4 | CBOT_SUPPORT → fiabilité compression | + (pivot) | **validé** (MFE 18→44 €/t ; ADVERSE ↓) | V41/V57 |
| 5 | FX EUR/USD → CBOT_eur_t | mécanique | **validé** (conversion) | features |
| 6 | substitution blé/maïs EU → basis (niveau) | + (justifie) | **validé** (r~0.60, EU-spécifique) | V36/V40 |
| 7 | substitution EU → ADVERSE | + (prime justifiée plus risquée à shorter) | **fragile** | V37/V38 |
| 8 | courbe EMA backwardation → compression lente | − (sur la vitesse) | **data-gated** (fenêtre courte) | V54 |
| 9 | roll Euronext → bruit basis | bruit | **fragile** (warning roll) | V27/V50 |
| 10 | désync horaire EMA/CBOT → bruit basis | bruit | **data-gated** (intraday) | V44/V46/V60-intraday |
| 11 | macro (TTF, USD, éthanol) → basis | faible | **rejeté** (R² OOF ≈ −0.25) | V16 |
| 12 | météo EU extrême → prime justifiée / ADVERSE | + | **data-gated** (pas de météo EU réalisée) | V45 (forward) |
| 13 | options/IV CBOT → risque move / ADVERSE | + | **data-gated** | V74 |

---

## Règles de lecture pour la suite

- Toute nouvelle expérience doit **cibler une arête** identifiée (et son signe attendu), pas balayer des
  variables. On teste une hypothèse économique, on documente le verdict (même négatif).
- Les arêtes **validées** alimentent les diagnostics (CBOT_SUPPORT, ADVERSE_RISK, objectif) — jamais des vetos.
- Les arêtes **data-gated** se valident en **forward** (journaux), pas en tordant le passé.
- Les arêtes **rejetées** (2, 11) sont des résultats : la prime EU est **locale**, pas un artefact CBOT/macro.

## Implication centrale
Le basis haut est **compressible** surtout quand le canal #3–#4 est actif (CBOT porteur qui rattrape) et que
les canaux #6–#8 (substitution / tension physique) ne le **justifient** pas. C'est exactement la grande
question de la phase : séparer anomalie (#3–#4 dominants) de prime justifiée (#6–#8 / #12 dominants).
