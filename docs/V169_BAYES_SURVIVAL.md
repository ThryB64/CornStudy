# V169 — Survie bayésienne hiérarchique du time-to-z0.5 (T-BAYES, R9)

**Verdict : `POSTERIORS_DELIVERED_DESCRIPTIVE` — et deux NUANCES importantes sur des claims
existants (V130 niveau vs trade, V167 saison).** RESEARCH_ONLY_NOT_TRADING, baseline intouchée.

## Modèle

Weibull hiérarchique avec censure à droite sur le time-to-z0.5 des 42 épisodes V82 (5 censurés),
partial pooling par palier puis par saison (paramétrisation non centrée, priors faiblement
informatifs). Win-rate : logit hiérarchique. Inférence : random-walk Metropolis numpy 4 chaînes
(pymc absent — pas de dépendance lourde pour n=42), split-R̂ rapporté (1.00–1.06 sur les runs
réels). Module `src/mais/research/v169_bayes_survival.py`, artefact
`artefacts/v169/v169_bayes_survival.json`, 5 tests verts (récupération Weibull connue, censure,
shrinkage).

## Questions pré-déclarées et réponses

**Q1 — P(EXTREME atteint z0.5 plus vite que MODERATE) = 0.072.** Donc ~93 % de probabilité
que l'EXTREME soit plus LENT : médianes postérieures 47.1 j [29.5–81.9] (EXTREME) vs
28.6 j [20.3–39.7] (MODERATE). **Lecture** : V130 reste vrai au niveau du basis (la demi-vie de
DÉCROISSANCE rétrécit avec l'extrême), mais au niveau du TRADE la distance à parcourir
(z 2+ → 0.5) domine la vitesse — c'est exactement le mécanisme derrière le résultat négatif V138
(demi-vie analytique ≠ horizon de trade). Conséquence opérationnelle : ne pas promettre un
débouclage rapide sur les EXTREME ; le plafond 90 j et la patience restent justifiés.

**Q2 — P(été jul_aug plus lent que printemps apr_jun) = 0.377.** Le contraste brut V167
(32 j vs 11.5 j) **s'évapore après partial pooling** (médianes 32.8 vs 35.0 j) : il était
largement un artefact de la profondeur d'entrée (été 1.45z vs printemps 0.59z — même mécanisme
que Q1), pas un effet saison propre. V167 garde sa valeur descriptive (les départs piquent en
août) mais « l'été compresse lentement » ne doit plus être cité comme effet causal de la saison.

**Q3 — largeurs des intervalles crédibles win-rate.** Pooled 0.80 [0.62–0.91].
MODERATE 0.80 (largeur 0.21), EXTREME 0.80 (0.29), STRONG brut 4/4=1.0 **rétréci à 0.83
[0.65–0.96]** (0.32). Aucun palier ne se distingue de façon crédible sur le win-rate — les
écarts de PnL entre paliers (V15-05 : 29.9 vs 9.9 €/t) viennent de la MAGNITUDE, pas de la
probabilité de gain.

## Autres sorties

- Forme Weibull k = 1.10 [0.88–1.36] : hazard quasi exponentiel, faible dépendance à la durée —
  « être dans l'épisode depuis longtemps » n'accélère ni ne ralentit beaucoup la résolution.
- Médiane poolée 38 j [20–73], cohérente avec V14-02 (KM 47 j) et V138 (réel 28.6 j).

## Garde-fous

n=42 (7 ADVERSE, 5 censurés) → tout est DESCRIPTIF. Le partial pooling est la défense honnête
contre la sur-interprétation des sous-groupes (n=4 STRONG). Aucun seuil modifié, aucune fusion
avec la baseline. À re-runner quand le forward officiel aura ajouté des épisodes mûrs.
