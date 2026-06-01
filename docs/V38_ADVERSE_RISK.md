# V38 — Module ADVERSE_RISK + approfondissement substitution blé/maïs

Session 2026-06-01 (suite V37). Discipline : on transforme les découvertes V32/V36/V37 en **contexte
explicite**, JAMAIS en veto, SANS toucher la règle figée. Aucun modèle ajusté sur n=42. Holdout
verrouillé. `RESEARCH_ONLY_NOT_TRADING`.

## V38-01 — Score ADVERSE_RISK règle-basé

Module `src/mais/research/v38_adverse_risk.py`. Score 0..3 assemblé à partir des signatures découvertes,
toutes causales au moment du signal (aucun fit) :

| composant | source | condition (signal actif z≥1) |
|---|---|---|
| `c_moderate_premium` | V32 | basis_z ∈ [1, 1.5) — les primes modérées échouent |
| `c_low_residual` | V37 | résidu < 0 — prime déjà justifiée par la substitution |
| `c_high_substitution` | V36 | ratio blé/maïs (z expandant) > 0.5 |

Score → palier : 0 = **LOW**, 1 = **MEDIUM**, ≥2 = **HIGH**.

## V38-04 — Validation descriptive du palier (42 trades réels)

Le palier règle-basé sépare l'ADVERSE **et** le PnL, de façon **monotone**, sans aucun seuil optimisé :

| ADVERSE_RISK | n | taux ADVERSE | win | PnL z→0 | PnL z→0.5 |
|---|---:|---:|---:|---:|---:|
| LOW | 5 | **0.0 %** | 0.80 | **27.6** | 30.1 |
| MEDIUM | 33 | 18.2 % | 0.82 | 11.5 | 10.9 |
| HIGH | 4 | **25.0 %** | 0.75 | **5.0** | 5.1 |

- `tier_monotone_increasing = True`, `verdict = ADVERSE_RISK_TIER_SEPARATES`.
- **Le signal le plus net est le gradient de PnL** : LOW gagne ~5× HIGH (27.6 vs 5.0). LOW = prime
  extrême, inexpliquée par la substitution, résidu haut → forte compression. HIGH = prime modérée,
  justifiée par blé/maïs → compression molle.
- **Objectif z→0.5 vs z→0 ≈ neutre en PnL** (27.6 vs 30.1 ; 5.0 vs 5.1) : l'objectif prudent ne *gagne*
  pas plus, il **plafonne la queue de perte**. C'est un choix de risque, pas de rendement.
- **n petit** (LOW 5, HIGH 4) → descriptif, à re-tester en forward officiel. CONTEXTE, pas un veto.

## V38-02 — Approfondissement ratio blé/maïs

- `corr(basis, ratio blé/maïs z) = 0.587` (confirme V36 r≈0.60, substitution fourragère).
- Compression à 40 j : ratio HAUT 11.0 % vs ratio BAS 19.4 % → **un ratio élevé se comprime MOINS**
  (`HIGH_WHEAT_CORN_RATIO_LESS_COMPRESSIBLE`).
- ADVERSE : ratio HAUT 23.8 % vs ratio BAS 9.5 % → la prime soutenue par la substitution finit plus
  souvent ADVERSE (`substitution_supports_premium = True`).
- Par saison : avr-juin le plus ADVERSE (33 %), juil-août le moins (6 %).

→ Cohérent et économiquement interprétable : **un basis haut peut être une prime physique justifiée
(blé cher → maïs demandé), pas une anomalie compressible.** C'est exactement ce que le palier HIGH capte.

## V38-05 — Bloc contexte dans le rapport quotidien

`adverse_risk_report_block(df)` produit un bloc markdown (palier, facteurs actifs, objectif suggéré),
appendé à `generate_daily_report` de façon **purement additive et protégée** (try/except) : il n'altère
jamais le signal de la règle figée, il module seulement l'objectif (prudent vs complet) et la prudence.

## Synthèse

- L'ADVERSE_RISK règle-basé (V32+V36+V37) **sépare monotonement** ADVERSE (0 %→18 %→25 %) et PnL
  (27.6→11.5→5.0) sur les trades réels — sans fit, sans toucher la règle.
- La grande question scientifique « anomalie compressible vs prime justifiée » reçoit une réponse
  opérationnelle : **prime justifiée par la substitution = ADVERSE-prone, prime inexpliquée = compressible.**
- Limites honnêtes : n petit, objectif prudent neutre en PnL (gestion de queue, pas de rendement).
- Tests `tests/test_v38_adverse_risk.py` (3 PASS). Artefacts `artefacts/v38/`.
- Reste (data) : merger MARS/FranceAgriMer/Ukraine (module physique EU complet), accumuler forward
  officiel pour re-tester le palier hors-échantillon.
