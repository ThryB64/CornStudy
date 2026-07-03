# EXT013 — Audit données : basis & transmission spot/futures

**Verdict : DATA_BLOCKED.**

## Ce qu'il faut
Un prix spot physique (local) + un prix futures à la même fréquence pour calculer
basis = spot − futures, sa convergence à l'expiration, et la transmission CBOT↔local.

## Ce qui existe en interne (audité)
| Source | Contenu | Couverture | Verdict |
|---|---|---|---|
| `market.parquet` | CBOT futures continu (cents/bu) | 2000-2025 | OK comme futures |
| EMA officiel (V26) | settlement Euronext (€/t) | 2010+ | « futures » EU, pas un spot |
| Taux EUR/USD quotidien historique | **absent** : `macro_fred` n'a que `usd_index` (DXY) ; `official_forward/ecb_eurusd` = **13 lignes (2026)** | — | bloque le basis €/t homogène |
| Spot physique UE (FranceAgriMer / Bologne) | **absent** : `comext` = valeurs unitaires **mensuelles** de commerce (366 lignes), pas un spot quotidien | — | bloquant |

## Conclusion
Deux blocages :
1. **EMA−CBOT en €/t** : nécessite un EUR/USD quotidien historique (2010+), absent
   (seul le DXY est présent ; l'ECB EUR/USD interne ne couvre que mai-juin 2026). Le
   basis officiel utilisé en interne (V26) repose sur cette conversion ; en externe sans
   eurusd historique, on ne peut pas reconstruire la série proprement.
2. **Vrai spot physique** : aucune série spot quotidienne (COMEXT est mensuel et
   transactionnel, pas un prix de cash). La transmission spot→futures n'est pas testable.

## Plan d'acquisition (pour rouvrir)
1. Sourcer un EUR/USD quotidien historique (FRED DEXUSEU, ECB SDW) → débloque le basis
   €/t et le tableau de référence basis d'EXT025.
2. Sourcer un spot UE quotidien/hebdo (FranceAgriMer rendu Rouen/Bordeaux, Bologne) →
   volet transmission physique de Penone et al. (V21 le formalise via VECM EXT013/EXT044).
3. À défaut, le volet VECM CBOT↔EMA officiel (sans spot, sans €/t) reste faisable en
   descriptif (P2, EXT044) une fois l'eurusd réglé.
