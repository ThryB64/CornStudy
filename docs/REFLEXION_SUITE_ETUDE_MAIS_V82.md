# Réflexion stratégique — suite de l'étude maïs CBOT/EMA (phase V82+)

`RESEARCH_ONLY_NOT_TRADING`. Baseline figée, holdout 2024 verrouillé, aucun fit sur 42 trades. Document rédigé
puis durci en relecture critique (faisabilité, leakage, GO/NO_GO, limites). Fait suite à V60+ (V51-V81).

## 1. Résumé exécutif
Le signal central (short premium sur basis_z>1) est **trouvé, validé et robuste** (V81 : ex-crise 80% win /
+11.2 €/t, survit LOYO + coût 5 €/t). Les gains futurs ne viennent plus d'un meilleur modèle global mais de
la **compréhension fine du contexte** : distinguer anomalie compressible vs prime justifiée, qualifier le
moteur CBOT, choisir l'objectif, afficher des warnings. La phase V82+ industrialise cette compréhension en
une **bibliothèque d'épisodes** + des **scores de contexte v2** + une **validation forward**.

## 2. État actuel
Arc V8→V81 : mécanisme cartographié (V70 CBOT-driven, V72 horizon, V57 magnitude), diagnostics (V38/V64
ADVERSE, V41 CBOT_SUPPORT, V54 tension, V56 objectif), drivers (V36/V52 substitution, V71/V71b production EU,
V16 macro rejeté), météo/climat (V45/V48/V51/V60/V79), synthèse (V77), forward (V27/V45/V52/V59), robustesse
(V81). Cf. `IMPLEMENTATION_STATUS_PREMIUM.md`.

## 3. Validé
Basis = variable centrale ; compression du basis haut ; short ≫ long (V49) ; **CBOT porteur = pivot**
(V57/V70/V72) ; objectif contextuel risk-efficient (V56) ; pertes = primes modérées + CBOT faible (V50/V58) ;
**edge robuste** (V81) ; prime LOCALE (V16/V36/V60/V71b/V80).

## 4. Fragile
Tiers gradués (n=42) ; magnitude exacte (→ classes V57) ; queue météo (réelle mais anticipée V51) ; ENSO
(robuste ex-crise mais ~12 épisodes, forecastable, V79) ; production EU annuelle (confond tendance, V71).

## 5. Rejeté (négatifs documentés)
Macro→basis (V16), CBOT direction par ML (V65, AUC 0.54), météo réalisée/moyenne (V45/V48), météo US→basis
(V60), ADVERSE_RISK « gros score » (V64 : dilue), meta-model H40/H90 (V8). Vetos durs (sur-filtrage).

## 6. Bloqué par la donnée (vérifié)
COMEXT imports EU (DS-045409 hors API SDMX, **probé V80**), MARS yields intra-campagne (PDF), options/IV
(pas de source), intraday CBOT historique (payant), archive révisions météo (API time-out), météo EU réalisée.

## 7. Pourquoi l'impression de stagnation
Les signaux simples sont price-in (résultat correct, pas un échec). La marge restante = **compréhension du
contexte** + **données EU intra-campagne** + **forward**, pas « +features → AUC ». V81 confirme que l'edge est
là et stable ; inutile de le « réoptimiser ».

## 8. Grande question scientifique (centre de la phase)
> **Quand un basis EMA/CBOT élevé est-il une anomalie compressible, et quand est-il une prime justifiée par
> une tension physique européenne ou un contexte CBOT défavorable ?**

## 9. Nouvelles pistes
Bibliothèque d'épisodes (V82) ; fondamentaux EU intra-campagne (V83) ; MATIF blé/maïs officiel (V84) ;
extrêmes & révisions météo (V85) ; CBOT_SUPPORT v2 économique + ENSO (V86) ; basis intraday (V87) ; tension
courbe v2 (V88) ; survival v2 (V89) ; magnitude v2 (V90) ; ADVERSE_RISK v3 (V91) ; objectif v3 (V92).

## 10. Hypothèses économiques
Basis justifié si : substitution feed EU (MATIF blé/maïs haut), rareté physique (backwardation, faible offre
FR), CBOT non porteur (pas de rattrapage). Anomalie compressible si : CBOT porteur (uptrend/COT/La Niña),
courbe en contango, prime forte sans fondamentaux. La compression passe par le **CBOT mondial**.

## 11. Données nécessaires
Intra-campagne EU (MARS/FranceAgriMer mensuels) ; MATIF blé (EBM, live OK → forward) ; courbe EMA officielle
(forward) ; prévisions météo (forward, déjà journalisé) ; intraday CBOT (gated). La plupart = **accumulation
forward**.

## 12. Risques de leakage
shift(1) + z expandants/trailing sur tout fondamental/météo ; OOF embargo=horizon ; survival n'utilise que
l'info d'entrée pour stratifier ; ENSO décalé 2 mois ; pas de quantile look-ahead.

## 13. Risques de sur-optimisation
n=42 : interdiction de fit ; scores RÈGLE-BASÉS, banding fixe non optimisé ; comparer variantes en OOF/forward
seulement ; V64 a montré qu'empiler des composants DILUE → préférer des scores focalisés ; ne jamais toucher
au holdout.

## 14. Métriques
Séparation ADVERSE (binaire robuste), win/PnL/jour, MFE/MAE, time-to-event (KM), OOF AUC (contexte CBOT),
corrélations détrendées, stabilité LOYO + ex-crise + coût.

## 15. Roadmap V82→V100
V82 episode library · V83 fondamentaux EU intra-campagne · V84 MATIF officiel · V85 météo extrêmes/révisions ·
V86 CBOT_SUPPORT v2 · V87 intraday basis · V88 courbe tension v2 · V89 survival v2 · V90 magnitude v2 ·
V91 ADVERSE_RISK v3 · V92 objectif v3 · V93 casebook pro v2 · V94 ENSO→CBOT_SUPPORT · V95 production locality v2 ·
V96 intercommodity v2 · V97 proxy vs officiel · V98 rapport mensuel · V99 synthèse v2 · V100 décision.
(Réconciliation : V89≈V72, V90≈V57, V88≈V54, V93≈V58, V95≈V71b, V96≈V80, V98≈V59 sont DÉJÀ livrés v1 → v2 =
enrichissement seulement si apport net.)

## 16. Ce qu'il ne faut plus faire
Réoptimiser la règle/seuils ; ML opaque / meta-model ; AUC magique ; vetos durs ; toucher le holdout ; empiler
des composants qui diluent ; refaire des modules v1 déjà livrés sans apport net ; bot réel.

## 17. Conditions research → paper trading
Source officielle EMA validée (proxy vs officiel `PROXY_VALIDATED`) ; ≥40-90 j de forward ; signaux forward
cohérents avec l'historique ; coûts/slippage modélisés ; rapport mensuel stable.

## 18. Conditions paper trading → stratégie testable
6-12 mois de forward positif net de coûts ; drawdown maîtrisé ; nombre de signaux suffisant ; edge stable
en forward (pas seulement in-sample) ; décision V100 explicite. Conclusion possible : « excellent indicateur
d'analyse, pas stratégie tradable » — ce serait déjà une réussite.

## GO / WATCHLIST / NO_GO (critère commun)
**GO** : améliore une métrique OOF/forward de façon stable ET interprétable, sans toucher la baseline.
**WATCHLIST** : plausible mais n faible / data-gated → re-tester forward. **NO_GO** : pas d'amélioration
robuste / non causal / exige de tordre la règle. Tout négatif est un livrable.
