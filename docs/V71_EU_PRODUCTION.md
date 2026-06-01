# V71 / V71b — Bilan physique EU (production) comme justification de la prime

Session 2026-06-01. Déblocage de l'axe fondamentaux EU via la production maïs (Eurostat apro_cpsh1 C1500,
collecteurs `ec_mars.py` + `franceagrimer.py`, annuelle, anti-leakage shift(1)+ffill). Baseline figée
inchangée, aucun fit, pas d'intégration `build_features` (différée à validation forward).
`RESEARCH_ONLY_NOT_TRADING`.

## V71 — Production EU totale vs basis (niveaux)
Hypothèse : faible production EU (rareté) → basis haut justifié → moins compressible, plus d'ADVERSE.

- **Confond de tendance** : production EU et basis dérivent tous deux sur 2010-2026 → corr en niveau
  (+0.255) et « basis année rare 35.4 < ample 41.6 €/t » NON fiables.
- Seul élément propre (intra-régime, basis déjà haut) : compression **plus faible** en année de faible
  production (**5.6 vs 7.4 €/t**) → cohérent avec une prime partiellement justifiée par la rareté EU.
- ADVERSE ne se sépare pas (0.167 vs 0.176).
- Verdict `EU_PRODUCTION_PARTIAL_SIGNAL_WATCHLIST`. **Leçon** : l'annuel est trop grossier ; la bonne donnée
  serait les prévisions de rendement MARS intra-campagne (bulletins PDF, non parsés).

## V71b — Localité géographique (détrendé YoY)
On corrige le confond en travaillant sur les **variations annuelles** (YoY), et on teste la **localité** : le
contrat EMA étant livré en France, la production FRANÇAISE devrait peser plus que l'UE totale.

| Géographie | corr(Δprod YoY, Δbasis) | n années |
|---|---:|---:|
| France | **−0.174** | 13 |
| FR+RO+HU | −0.132 | 13 |
| UE totale | −0.091 | 13 |

- **Le signe redevient NÉGATIF** une fois détrendé (production en baisse → basis en hausse), ce qui
  **confirme que le +0.255 de V71 était bien un artefact de tendance**.
- **La France est le driver le plus local** (−0.174 < UE −0.091) → `FRENCH_PRODUCTION_MORE_LOCAL_DRIVER_OF_BASIS`,
  cohérent avec la livraison française du contrat → renforce la thèse **prime LOCALE** (V16/V36/V60).

**Caveat** : ~13 campagnes, très faible puissance, corrélations modestes. Comparaison RELATIVE descriptive,
aucun fit. À confirmer en forward / avec des données intra-campagne.

## Conclusion d'étape
La production EU n'est pas un timing exploitable (annuel, faible puissance), mais elle **éclaire la nature de
la prime** : (1) une faible offre EU rend le basis haut un peu moins compressible (prime partiellement
justifiée) ; (2) l'offre **française** prime sur l'UE totale, confirmant la localité géographique. La donnée
qui débloquerait vraiment cet axe = **prévisions de rendement MARS intra-campagne** (mensuelles). Tests V71/V71b
PASS, ruff PASS.
