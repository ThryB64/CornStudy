# V40 / V41 — Substitution blé/maïs approfondie + CBOT_SUPPORT_SCORE

Session 2026-06-01 (suite V39). On opérationnalise les découvertes V39 et on approfondit la substitution,
sans nouveau modèle ni touche à la règle figée. Holdout verrouillé. `RESEARCH_ONLY_NOT_TRADING`.

## V41 — CBOT_SUPPORT_SCORE (pendant positif d'ADVERSE_RISK)

Module `src/mais/research/v41_cbot_support.py`. Score règle-basé (aucun fit) miroir de V38, à partir des
découvertes V39 (E4 uptrend, E6 COT), composants causaux :

| composant | source | condition (signal actif z≥1) |
|---|---|---|
| `cbot_above_sma50` | E4 | corn_close > SMA50 |
| `cbot_mom20_positive` | E4 | log-return 20j > 0 |
| `mm_net_favorable` | E6 | managed money net (causal) > médiane expandante |

Score 0..3 → CBOT_SUPPORT LOW (≤1) / MEDIUM (2) / HIGH (≥3). Support HAUT = compression plus fiable.

**Validation (42 trades)** :

| CBOT_SUPPORT | n | taux ADVERSE | win | PnL z→0 |
|---|---:|---:|---:|---:|
| LOW | 23 | 21.7 % | 0.74 | 8.4 |
| MEDIUM | 11 | 9.1 % | 0.91 | 21.3 |
| HIGH | 8 | 12.5 % | 0.88 | 13.8 |

- Le **gradué 3-paliers n'est PAS monotone** (HIGH n=8 ne bat pas MEDIUM = bruit en petit n).
- **Mais le split binaire est robuste** : support faible (≤1) → ADVERSE **21.7 %**, PnL **8.4** vs
  CBOT soutenu (≥2) → ADVERSE **10.5 %**, PnL **18.1** → `CBOT_SUPPORT_BINARY_ROBUST_GRADED_NOISY`.
- **Pas de bidouillage de bins** (interdit sur 42 trades). On rapporte la non-monotonicité honnêtement.
- Confirme E4/E6 : « short premium ≈ long CBOT relatif » — un CBOT porteur fiabilise la compression.
  CONTEXTE, jamais un veto. Bloc ajouté au rapport quotidien (à côté d'ADVERSE_RISK).

## V40 — Substitution blé/maïs approfondie

Module `src/mais/research/v40_substitution_deep.py`.

### Spécificité EU (DÉCOUVERTE)
- `corr(ratio blé/maïs, basis EU) = +0.587` **mais** `corr(ratio, CBOT) = −0.464` → **signes opposés**.
- `substitution_is_EU_specific = True`. La substitution fait monter **la prime européenne** (et coïncide
  avec un CBOT plus bas), donc c'est **spécifiquement un phénomène de prime LOCALE EU**, pas un artefact
  mécanique du niveau CBOT. Renforce fortement la thèse (cohérent V16, V39-E5 : fondamentaux US faibles
  sur le basis).

### Reversion selon le ratio
| ratio blé/maïs | n | médiane (j) | reverted | ADVERSE | PnL |
|---|---:|---:|---:|---:|---:|
| HAUT (justifié) | 21 | 47.0 | 0.62 | 23.8 % | 12.9 |
| BAS (inexpliqué) | 21 | 29.0 | 0.81 | 9.5 % | 12.8 |

→ Ratio haut = reversion **plus lente** (47 vs 29 j) + **plus d'ADVERSE** (24 % vs 9.5 %), PnL moyen
identique (les survivants paient). Cohérent V37/V38 : prime justifiée = plus dangereuse / plus lente.

### Interaction énergie (NÉGATIF honnête)
TTF EU non chargé → proxy gaz US. corr ratio↔basis en énergie chère 0.561 vs faible 0.672 →
`energy_amplifies_substitution = False`. L'énergie n'amplifie pas le lien substitution↔basis.

### Limites data (honnêtes, NON simulées)
- **MATIF blé/maïs** : non disponible — le blé du pipeline est CBOT (ZW=F). La vraie substitution EU se
  mesurerait avec MATIF blé / MATIF maïs (Euronext milling wheat), à brancher comme la collecte EMA.
- **Météo EU forecast** réelle : data-gated (host historical-forecast time out).

## Synthèse

- **CBOT_SUPPORT** (V41) opérationnalise E4/E6 : robuste en binaire (support → ADVERSE ÷2, PnL ×2),
  bruité en gradué. Pendant positif d'ADVERSE_RISK ; les deux sont dans le rapport quotidien.
- **Substitution EU-spécifique** (V40) : ratio blé/maïs corrèle +0.59 au basis EU, −0.46 au CBOT →
  prime LOCALE européenne, pas artefact CBOT. La prime justifiée est plus lente + plus ADVERSE.
- Discipline : aucun fold dans la règle, tout en contexte ; MATIF blé & météo EU data-gated.
- Tests `tests/test_v40_*` (2), `tests/test_v41_*` (3) PASS. Artefacts `artefacts/v40`, `artefacts/v41`.
