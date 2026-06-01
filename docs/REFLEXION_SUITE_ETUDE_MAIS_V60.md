# Réflexion — suite de l'étude maïs CBOT / Euronext EMA (phase V60+)

Document de cadrage scientifique. `RESEARCH_ONLY_NOT_TRADING`. Baseline figée, holdout verrouillé.
Rédigé puis durci en relecture critique (limites, leakage, dépendances data, GO/NO_GO) — Étapes 1+2.

---

## 1. La grande question (le nouveau cœur)

> **Quand un basis EMA/CBOT élevé est-il une ANOMALIE compressible, et quand est-il une PRIME JUSTIFIÉE par
> le marché physique européen ?**

Tout le programme V60→V78 doit servir cette question. Deux régimes à séparer :

- **Cas 1 — anomalie compressible** : Euronext cher sans justification physique → compression probable →
  objectif z→0 envisageable.
- **Cas 2 — prime justifiée** : Euronext cher car marché EU réellement tendu (substitution feed, rareté
  physique, météo EU) → compression lente ou échec → objectif prudent z→0.5, voire simple *warning*.

L'étude ne cherche plus une AUC plus haute : elle cherche à **classer le contexte d'un signal figé**.

---

## 2. État des connaissances — validé / fragile / rejeté / data-gated

### Validé (robuste, OOF ou descriptif cohérent multi-angles)
- Le **basis EMA/CBOT** est la variable centrale ; le prix EMA brut est peu prédictible (V8/EXP-BENCH).
- **Basis haut → compression** (réversion ; demi-vie ~17–54 j selon mesure).
- **short premium ≫ long premium** (V49 : 12.8 vs 8.2 €/t, asymétrie confirmée).
- **CBOT porteur = facteur pivot** : compression plus forte (V57 : MFE médiane 18→44 €/t avec CBOT_SUPPORT),
  plus complète/rapide, et justifie l'objectif complet (V47/V56).
- **Objectif contextuel** (V56) : z→0.5 si CBOT_SUPPORT=LOW ∨ ADVERSE_RISK=HIGH ∨ PHYSICAL_TENSION=HIGH —
  capte ~le PnL du complet en −7.2 j d'exposition (`RISK_EFFICIENT`).
- **Pertes concentrées sur primes modérées (z<1.5) + CBOT non porteur** (V32/V50/V58 : warning prudent aurait
  couvert 5/7 ADVERSE).
- **Prime LOCALE** : ni la macro (V16) ni la météo US (V60) n'expliquent le basis ; corr(ratio CBOT, basis)
  faible/inverse (V36/V40).
- **Météo : signal dans la QUEUE, pas la moyenne, et ANTICIPÉ** (V48/V51 : corr backward 0.34 ≫ forward 0.15 ;
  persistance > intensité).

### Fragile (signal réel mais petit n / instable)
- Tiers gradués (MODERATE/STRONG/EXTREME) sur n=42 : usage descriptif seulement.
- Tier ADVERSE_RISK gradué 3 niveaux (V38) : robuste en binaire, bruité en gradué.
- Magnitude exacte de compression (V44) : non prédictible → on bascule en classes (V57).
- Queue météo (décile chaud → +2.4 % CBOT/10j) : réelle mais en partie déjà pricée.

### Rejeté (testé, ne bat pas la baseline / non causal)
- WASDE direct, COT seul, fair-value macro simple, EMA up/down brut, CBOT up/down brut, météo réalisée
  moyenne, meta-model H40/H90 (overfit sous protocole strict, V8-META).
- Inversion saisonnière V8 (falsifiée V9). Granger basis (rejeté OOF).
- Filtres durs / vetos (sur-filtrage : V15/V23/V29).

### Bloqué par la donnée (data-gated — code prêt, attend accumulation forward)
- **Intraday CBOT** (alignement settlement) : pas d'historique intraday gratuit 2014+.
- **MATIF blé/maïs historique** (V52/EBM) : endpoint snapshot-only → journal forward.
- **Courbe EMA officielle** (V54 tension) : fenêtre récente ~330 j, contango-dominée.
- **Prévisions météo historiques** (archive révisions) : Open-Meteo historical-forecast time-out.
- **Météo EU réalisée** : master n'a que l'US.
- **Fondamentaux EU** (FranceAgriMer, EC MARS, COMEXT, Ukraine FOB), **options/IV CBOT**.

---

## 3. Pourquoi l'impression de stagnation (et pourquoi ce n'est pas un échec)

Les signaux « évidents » sont **déjà price-in** : un marché liquide intègre WASDE, COT, météo de base. Le fait
que ces signaux soient faibles est un **résultat scientifique correct**, pas une faiblesse de l'étude. La marge
de progrès n'est plus dans « +200 features → AUC magique » (chemin overfit, déjà invalidé V8-META), mais dans :

1. **améliorer la donnée** (alignement intraday, ratio MATIF, courbe officielle) ;
2. **mieux séparer anomalie vs prime justifiée** (substitution, tension physique) ;
3. **mieux qualifier le moteur CBOT** (rebound engine) ;
4. **mieux décrire la dynamique** (time-to-reversion, classes de magnitude) ;
5. **valider en forward officiel** (track record).

---

## 4. Axes de recherche et hypothèses économiques

| Axe | Hypothèse économique | Statut |
|---|---|---|
| A — Basis intraday aligné | Une part du bruit du basis = désynchro horaire EMA(settle)/CBOT(close). Aligner réduit le bruit sans modèle. | data-gated (probe) |
| B — Ratio MATIF blé/maïs | Si blé EU cher vs maïs, la demande feed soutient le maïs EU → basis haut plus justifié, moins compressible. | live OK, hist. data-gated (V52) |
| C — Tension physique courbe EMA | Basis haut + backwardation = rareté réelle → compression lente ; + contango = anomalie → compressible. | live OK, hist. data-gated (V54) |
| D — Prévisions météo extrêmes & révisions | Le réalisé est anticipé ; seule la **surprise de prévision** (révision) est tradeable. Persistance > intensité. | V51 fait ; révisions = forward |
| E — CBOT rebound engine | La compression est CBOT-driven ; mieux prédire la capacité de rattrapage améliore CBOT_SUPPORT. | **NOUVEAU faisable** |
| F — Time-to-reversion (survival) | On veut l'HORIZON probable de compression, pas seulement oui/non. | **NOUVEAU faisable** |
| G — ADVERSE casebook pro | Chaque perte = enseignement économique (semi-quantitatif, n=7). | V58 fait, version pro |
| H — Cibles utiles ≠ up/down | Les classes (compression>5/10/20, time-to-z) sont plus prédictibles que la direction brute. | V57 fait + survival |
| I — Options / IV | Le marché options anticipe les gros moves / périodes dangereuses. | data-gated |
| J — Spreads inter-commodités EU | Substitution réelle (orge, colza, soja, énergie) soutient ou non le maïs EU. | partiel (CBOT dispo) |
| K — Carte causale | Formaliser le graphe pour tester des arêtes, pas des variables au hasard. | **doc V73** |

---

## 5. Ce qu'il ne faut PAS faire (garde-fous)

- Ne pas changer la baseline ni les seuils ; ne pas optimiser sur les 42 trades.
- Pas de deep learning, pas de relance du meta-model, pas de chasse à l'AUC 0.90.
- Pas de veto dur tiré d'un warning sans preuve forte (anti sur-filtrage).
- Ne jamais toucher au holdout 2024 pour choisir un paramètre.
- Pas de bot réel ; pas de mélange avec prix local / stockage (PROJET 2 séparé).
- **Tout résultat négatif est documenté** (c'est un livrable, pas un échec).

---

## 6. Roadmap V60→V78 (réconciliée avec le travail déjà livré)

> ⚠️ Réconciliation : plusieurs tickets du programme correspondent à des modules **déjà livrés** cette
> session (V51–V60). On ne les ré-implémente pas ; on les marque et on se concentre sur le nouveau.

**Phase 1 — Données haute valeur**
- V60-intraday — basis intraday aligné — *data-gated, framework + probe* → **à faire (probe)**
- V61 — MATIF blé/maïs officiel — **DÉJÀ : `v52_matif_substitution.py`** (live OK, hist. forward)
- V62 — courbe EMA officielle / tension — **DÉJÀ : `v54_physical_tension.py`** (live OK, hist. forward)
- V63 — météo prévue extrêmes & révisions — **DÉJÀ (extrêmes) : `v51_weather_extremes.py`** ; *révisions = forward*

**Phase 2 — Diagnostic du signal**
- V64 — ADVERSE_RISK v2 (explained) → **à faire**
- V65 — CBOT rebound engine → **à faire**
- V66 — PHYSICAL_TENSION score — **DÉJÀ : `v54`** (intégré V56)
- V67 — TARGET_RECOMMENDATION v2 — **DÉJÀ : `v56_target_recommendation.py`**

**Phase 3 — Nouvelles cibles**
- V68 — basis compression buckets — **DÉJÀ : `v57_magnitude_buckets.py`**
- V69 — time-to-reversion / survival → **à faire (= V72 ci-dessous)**
- V70 — path classification CBOT-driven / EMA-driven / ADVERSE → **à faire (existe partiellement V32 `_classify_path`)**

**Phase 4 — Fondamentaux**
- V71 — EU physical balance drivers — *data-gated*
- V72 — survival (cf. V69) → **à faire**
- V73 — carte causale → **doc à faire**
- V74 — options / IV — *data-gated*

**Phase 5 — Validation forward**
- V75 — rapport mensuel forward — **DÉJÀ : `v59_monthly_forward_report.py`**
- V76 — proxy vs officiel à 40/90 j — *partiel, forward*
- V77 — synthèse indicateur — **partiel : `generate_daily_report` agrège déjà la pile**
- V78 — rapport de décision — *après accumulation forward*

---

## 7. Priorités concrètes immédiates (faisables MAINTENANT, sans nouvelle donnée)

1. **V64 — ADVERSE_RISK v2** : score enrichi et EXPLIQUÉ (basis_z tier + CBOT_SUPPORT + PHYSICAL_TENSION +
   résidu substitution + roll + crise + volatilité), règle-basé, validé descriptivement. Sert directement la
   grande question (anomalie vs justifiée).
2. **V65 — CBOT rebound engine** : OOF honnête de la capacité de rattrapage CBOT (rebound/drawdown), pour
   muscler CBOT_SUPPORT (le facteur pivot).
3. **V72/V69 — time-to-reversion (survival)** : Kaplan-Meier du retour vers z→0.5 / z→0, censuré 90 j, par
   régime → fournit l'HORIZON probable de compression (très utile au rapport).
4. **V70 — path classification** : formaliser CBOT-driven / EMA-driven / ADVERSE (étend V32) pour mesurer
   *par quel canal* la compression se produit.
5. **V73 — carte causale** (doc) : ancrer toutes les expériences sur un graphe.

Le reste (intraday, fondamentaux EU, options, révisions météo, track record) avance par **accumulation
forward** (GitHub Action) ou nouvelle donnée — pas par du code.

---

## 8. Limites méthodologiques & risques (relecture critique)

- **Petit n (42 trades, 7 ADVERSE)** : interdiction de fit ; tout score reste règle-basé ; les paliers
  gradués sont indicatifs, on privilégie les splits binaires robustes.
- **Leakage** : toute feature fondamentale/météo en `shift(1)` + z expandants/trailing ; OOF avec embargo
  (`tr[:-horizon]`) ; survival doit utiliser uniquement l'info connue à l'entrée.
- **Réalisé ≠ tradeable** : les analyses météo/intraday réalisées sont des BORNES explicatives ; l'edge réel
  suppose la donnée forward (prévision, intraday live).
- **Sur-optimisation** : ne comparer les variantes que sur OOF/forward, jamais sur le backtest in-sample ;
  ne pas multiplier les seuils.
- **Dépendances data** : V60-intraday, V71, V74 sont bloqués ; on livre le framework + verdict honnête.
- **GO / WATCHLIST / NO_GO** (critère commun) :
  - **GO / ADD_TO_PIPELINE** : améliore une métrique OOF/forward de façon stable ET interprétable, sans
    toucher la baseline.
  - **WATCHLIST** : signal plausible mais n trop faible / data-gated → à re-tester en forward.
  - **NO_GO** : pas d'amélioration robuste, ou non causal, ou exige de tordre la règle.

---

## 9. Livrables attendus de la phase

- Docs : ce fichier, `TICKETS_RECHERCHE_MAIS_V60_V78.md`, `CAUSAL_MAP_CORN_MARKET.md`,
  `ADVERSE_CASEBOOK_PRO.md` (V68 pro), `REVIEW_V60_V78.md` (synthèse finale).
- Code : modules V64, V65, V72, V70 (+ framework intraday), chacun avec tests + artefacts + entrée registre.
- Forward : journaux qui s'accumulent (signal officiel, MATIF, météo, révisions) pour V74/V75/V76/V78.
- **Critère de succès de la phase** : pas « AUC plus haute » mais « on sait dire, pour un signal donné, s'il
  est plutôt anomalie compressible ou prime justifiée, avec un objectif et un horizon motivés ».
