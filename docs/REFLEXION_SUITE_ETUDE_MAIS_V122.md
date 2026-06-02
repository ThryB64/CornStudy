# Réflexion — Suite de l'étude maïs CBOT/Euronext EMA (V122-V150)

Statut global : **RESEARCH_ONLY_NOT_TRADING**. Baseline figée. Holdout 2024 verrouillé.
Date de rédaction : 2026-06-02.

---

## 1. État actuel de l'étude

L'étude est **techniquement mûre**. On ne cherche plus un modèle magique. L'objet est désormais
un **indicateur de prime EMA/CBOT** : research-grade, explicable, forward, accompagné de diagnostics
de contexte (tension physique, support CBOT, substitution blé/maïs, météo forecast, courbe officielle)
et d'un monitoring de signal actif.

Pile live opérationnelle (collecteur quotidien + GitHub Action) :

- **Signal** : `MaizePremiumIndicator` figé sur `basis_z` (journal officiel forward append-only, V27).
- **Contexte CBOT** : CBOT_SUPPORT v2 live (V107, ZC/ZW/ZS + COT managed-money CFTC) = **MEDIUM**.
- **ADVERSE_RISK** : reconstruit live (V108, basis = ZC=F+EUR/USD validé vs journal, err 0.4 €/t) = **MEDIUM**.
- **PHYSICAL_TENSION** : courbe EMA officielle live (V109, backwardation Q2026>X2026 +11.75 €/t) = **HIGH**.
- **Objectif recommandé** (V56) sur diagnostics frais : **z→0.5 prudent** (PHYSICAL_TENSION HIGH).
- Journaux forward : officiel (3 jours : 2026-05-29 → 2026-06-02), MATIF ratio, météo forecast.

Le journal officiel montre déjà une **dérive de tier saine** : 2026-05-29 EXTREME (z 2.056) → 06-01
EXTREME (z 2.039) → 06-02 STRONG (z 1.969). La prime commence à se comprimer.

---

## 2. Découvertes validées (rappel, ne pas re-tester)

1. **`basis_z > 1` reste le meilleur signal leading.** Asymétrie short ≫ long ; edge concentré z>2.
2. **Mean-reversion du NIVEAU** : `basis_z` stationnaire (ADF), demi-vie ≈ 17 j, AR(1) φ≈0.96.
   AR1 bat la marche aléatoire surtout à h5/h10 (V121) — c'est le **niveau** qu'on exploite.
3. **Le trigger journalier précis n'est PAS prédictible.** V106 : `trigger_score` est **inversé** —
   il reflète une compression **déjà commencée**, pas une compression future (REFLECTS_ONGOING_NOT_LEADING).
4. **Les variables exogènes n'aident pas vraiment OOS** sur le basis (V121) : in-sample oui, OOS non.
5. **La macro n'explique pas le basis** (V16, R² OOF négatif) : prime LOCALE européenne.
6. **Compression surtout CBOT-driven** : « short premium ≈ long CBOT relatif » (V21). CBOT_SUPPORT = pivot.
7. **ADVERSE = écartement, pas compression** : 100 % des pertes ; signature post-entrée MFE faible + durée longue (V82).
8. **Backwardation nearby ⇒ compression plus lente** : prime physiquement justifiée → objectif prudent (V30/V54/V109).
9. **Substitution blé/maïs LOCALE** : corr(ratio, basis)=+0.59 > corr(ratio, CBOT)=−0.46 (V41) — pas un artefact CBOT.
10. **La Niña haussier CBOT** +5.4 %/60j robuste ex-crise (V79) → composant CBOT_SUPPORT v2.
11. **Stress US réalisé ne prédit pas le CBOT** (price-in par anticipation, AUC 0.51, V45) → travailler la météo **forecast/forward**, pas réalisée.
12. **Mur de coûts** : edge survit jusqu'à ~2.5 €/t/leg hors crise ; au-delà, marginal.

---

## 3. Limites connues

- **n = 42 trades** sur l'historique : espace analytique épuisé. On **n'optimise plus** sur ces 42 trades.
- Le **z-score officiel** est encore `proxy_implied` (historique officiel < 40 jours → pas de z rolling officiel).
  Le proxy est **interdit en niveau absolu** mais **autorisé en z-score implied research-only**.
- **Courbe EMA officielle** : disponible en live (snapshot) mais **pas encore accumulée** → pas d'historique
  pour valider PHYSICAL_TENSION en backtest. Doit s'accumuler en forward (V125).
- **MATIF blé** : ratio live OK, historique aligné EMA encore **WAITING_DATA**.
- **Intraday CBOT** : historique payant → V128 reste probablement WATCHLIST/DATA_BLOCKED.
- **COMEXT (flux physiques EU)** : DS-045409 hors API de dissémination → DATA_BLOCKED documenté (V134).
- **Incohérence de révision** (cf. §5) : le journal append-only refuse de réviser une date déjà loggée
  alors que `latest.json` la recalcule → divergence de tier pour la même date. **Priorité V122.**

---

## 4. Pourquoi le trigger précis daily ne marche pas (et la conséquence)

Le retournement de la prime un jour J donné dépend d'un **catalyseur exogène** (WASDE, météo, COT,
news Ukraine, roll) dont la **date** n'est pas prévisible à partir des prix passés. V104-V106 le confirment :
tout score construit pour « anticiper » le trigger finit par **détecter une compression en cours**
(corrélation contemporaine), pas à la précéder. C'est cohérent avec l'efficience faible des marchés à terme.

**Conséquence méthodologique** : on **abandonne** la prédiction du timing exact. On exploite à la place
deux choses robustes :

- le **niveau** (basis_z extrême → réversion attendue, demi-vie ≈17 j) → fournit un **horizon**, pas une date ;
- le **contexte** (tension physique, support CBOT, substitution) → module l'**objectif** (z→0.5 vs z→0) et
  signale quand la prime est **justifiée** (ne pas attendre une compression complète).

---

## 5. Pourquoi travailler maintenant sur de nouvelles données leading

Les 42 trades sont saturés. Le seul gain marginal possible vient de **nouvelles données** qui sont
**leading** (catalyseurs en amont du retournement), pas de nouveaux découpages des mêmes prix :

- **Courbe officielle accumulée** (V125) : structure de courbe en temps réel = état physique du marché EU.
- **Météo forecast extrême + révisions** (V127) : la *révision* de prévision est un choc d'information leading.
- **Catalogue d'événements fondamentaux** (V129) : associer chaque retournement passé à son catalyseur
  → comprendre *ce qui* fait tourner la prime (explicatif), pas *quand* (non prédictible).
- **Substitution MATIF officielle** (V126) : signal de demande relative blé↔maïs en Europe.

L'objectif n'est PAS d'améliorer une AUC. C'est de **mieux distinguer** : prime excessive vs prime justifiée,
compression saine vs signal lent vs risque ADVERSE.

---

## 6. Roadmap V122-V150

| Bloc | Tickets | But |
|------|---------|-----|
| **Cohérence & live** | V122, V123, V124 | Révision auditée du journal, gate de fraîcheur, monitoring v2 |
| **Données contexte** | V125, V126, V127 | Courbe accumulée, substitution MATIF, météo forecast extrême |
| **Données leading** | V128, V129 | Intraday CBOT (probe), catalogue d'événements |
| **Économétrie** | V130 | Demi-vie par régime, TAR, Markov switching |
| **Décision** | V131, V132 | Reco objectif v3, synthèse indicateur v3 |
| **Reporting** | V133 | Rapport mensuel v2 |
| **Sourcing** | V134 | Plan des sources manquantes |
| **Checkpoint** | V135 | Bilan GO/WATCHLIST/NO_GO |

Réserve V136-V150 : suite forward (accumulation, milestones 10/40/90 j), pas d'implémentation tant que
le forward n'a pas mûri. **On code V122-V135 ; on laisse le forward remplir le reste.**

---

## 7. Risques de leakage (vigilance permanente)

- **Anti-leakage obligatoire** : `shift(1)` + z-scores expandants/trailing sur toutes les fondamentales.
- **Holdout 2024** : jamais utilisé pour choisir une règle/seuil. `assert_no_holdout` sur tout backtest.
- **Diagnostics LIVE forward** (V107/V108/V109/V125/V127) : calcul d'un état courant, PAS un backtest
  → `assert_no_holdout` ne s'applique pas (la fenêtre glissante inclut légitimement 2024 comme historique).
  Documenter explicitement à chaque module pour éviter la confusion.
- **Météo forecast** : datée à l'émission (issue_date), jamais réindexée a posteriori (anti-leakage).
- **Révision de settlement** (V122) : une révision ne doit jamais réécrire silencieusement le passé ;
  trace auditée obligatoire (revision_log) — sinon leakage de look-ahead dans le journal.
- **Événements (V129)** : la classification d'un retournement par catalyseur est **descriptive ex-post**,
  jamais un feature prédictif (sinon leakage du futur).

---

## 8. Dépendances data

| Source | Statut | Usage |
|--------|--------|-------|
| Yahoo ZC/ZW/ZS/CL/NG, EURUSD=X | ✅ OK (→2026-06) | CBOT_SUPPORT, basis reconstruit |
| CFTC f_disagg.txt (COT désagrégé) | ✅ OK (→2026-05-26) | CBOT_SUPPORT (managed-money) |
| Euronext EMA/EBM AJAX (settlement+OI) | ✅ OK (snapshot) | signal officiel, courbe, MATIF ratio |
| NOAA ONI ASCII | ✅ OK | ENSO / La Niña |
| Open-Meteo forecast | ✅ OK | météo forward US+EU |
| Open-Meteo historical-forecast | ⚠️ timeout | révisions de prévision (V127, best-effort) |
| Intraday CBOT historique | ❌ payant | V128 probe → WATCHLIST/DATA_BLOCKED |
| COMEXT DS-045409 | ❌ hors API | flux physiques EU → DATA_BLOCKED |
| EC MARS / FranceAgriMer / Eurostat | ⚠️ partiel | rendements/balance EU (best-effort) |
| DX=F | ❌ 404 | dollar index (substitut : EUR/USD) |

Règle : si une source manque → **DATA_BLOCKED** honnête + entrée dans le plan de sourcing (V134),
jamais un proxy déguisé en donnée officielle.

---

## 9. Critères GO / WATCHLIST / NO_GO

Appliqués à chaque module et au checkpoint V135 :

- **GO (ADD_TO_INDICATOR / ADD_TO_DAILY_REPORT)** : la brique
  (a) est calculable en live sans leakage,
  (b) améliore une DÉCISION (objectif, horizon, distinction justifiée/excessive) — pas seulement une métrique,
  (c) est robuste ex-crise et cohérente avec les découvertes §2,
  (d) ne touche pas la baseline.
- **WATCHLIST** : pertinent mais (données insuffisantes / forward trop court / robustesse non prouvée).
  On journalise en forward et on re-décide plus tard.
- **NO_GO (REJETÉ)** : n'améliore rien, ou dilue un diagnostic existant (cf. V64 : ADVERSE_RISK v2 dilue),
  ou n'est qu'explicatif sans valeur décisionnelle, ou risque de leakage.

Un module **explicatif** (comprendre *pourquoi*) est gardé en doc mais n'entre PAS dans l'indicateur
s'il n'aide pas une décision live.

---

## 10. Rappel final

L'objectif n'est **pas** un bot réel. C'est un **indicateur research professionnel**, explicable,
robuste en forward, capable de distinguer : **prime excessive · prime justifiée · compression saine ·
signal lent · risque ADVERSE**. Tout reste **RESEARCH_ONLY_NOT_TRADING**.
