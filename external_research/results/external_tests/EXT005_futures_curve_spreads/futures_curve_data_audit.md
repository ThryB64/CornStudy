# EXT005 — Audit données : courbe futures & full carry

**Verdict : DATA_BLOCKED.**

## Ce qu'il faut
Plusieurs maturités simultanées (nearby, deferred, Dec/Mar, Jul/Dec) pour calculer
spreads, contango/backwardation, slope, distance au full carry.

## Ce qui existe en interne (audité)
| Source | Contenu | Couverture | Verdict |
|---|---|---|---|
| `market.parquet` / `database.parquet` | CBOT continu (front roulé), une seule série | 2000-2025 | pas de multi-maturité |
| Contrats CBOT individuels par maturité | **absents** (confirmé EXT006 : historique front-only) | — | bloquant |
| `official_forward/ema_curve_history.parquet` | spreads EMA front/next, nov/mar, backwardation | **10 lignes, 2026-05-29 → 06-11** | trop court |
| `official_forward/matif_ratio_history.parquet` | settle blé/maïs MATIF | **9 lignes, 2026-06** | trop court |

## Conclusion
Côté CBOT : aucune profondeur de courbe historique (front-only) → impossible de
construire spreads/carry. Côté EMA : la courbe accumulée forward n'a que ~2 semaines
(démarrage de la collecte 2026). Aucune évaluation walk-forward possible.

## Plan d'acquisition (pour rouvrir)
1. Sourcer les contrats CBOT par maturité (Barchart/CME settlements ou reconstruction
   via la collecte multi-contrats déjà amorcée en V42/EXT006).
2. Continuer l'accumulation de `ema_curve_history` (≥1 an avant tout test).
3. Taux courts + coût de stockage ex ante pour le full carry (PATENT007, phase 2).
4. À rouvrir quand ≥250 jours de courbe exploitable → quantifie V125 (NARROWING) en signal.
