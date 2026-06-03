# Réflexion VNEXT — Audit intégral et stratégie de suite (maïs CBOT / Euronext EMA)

Date : 2026-06-03. Statut : **RESEARCH_ONLY_NOT_TRADING**. Baseline d'entrée `basis_z` figée.
Rédigé en lead research engineer, sur inspection réelle du dépôt (pas de mémoire). Deux passes.

---

## 0. Thèse de l'audit en une phrase

L'étude n'est plus bloquée par manque d'idées ; elle est bloquée par **trois dettes** —
(1) la vérité des **dates/sessions**, (2) la **confusion de périmètre** premium vs legacy, (3) l'**accès à
l'historique officiel** — et le gain marginal ne viendra plus d'un modèle sur les 42 trades, mais d'un
**changement de régime de recherche** : sécuriser les données, ouvrir les vraies sources leading, et passer
d'une logique binaire rare à une logique de **transitions d'état et de probabilités conditionnelles**.

---

## 1. État réel de l'étude (vérifié)

- **Cœur** : indicateur de prime EMA/CBOT, thèse de **réversion du niveau** de `basis_z` (ADF stationnaire,
  demi-vie ≈17 j, AR1 bat la marche aléatoire OOS à h5/h10 — V120/V121).
- **Asymétrie short ≫ long** crédible ; edge concentré à z élevé (V15, reconfirmé V131 : marginaux z<1.2 = 6.09 €/t
  vs confirmés 14.14).
- **Couche diagnostics de contexte** : ADVERSE_RISK (V38/V108), CBOT_SUPPORT (V41/V86/V107),
  PHYSICAL_TENSION (V54/V109/V125), substitution (V52/V126), météo (V45/V127), objectif (V56/V131).
- **Forward officiel** : journal append-only V27 (3 jours : 2026-05-29 → 06-02), snapshots de courbe accumulés.
- **Synthèse** : indicateur v3 (V132) + cohérence (V122) + fraîcheur (V123) + checkpoint (V135).
- **Live au 2026-06-02** : SHORT_PREMIUM_STRONG (z 1.969), ADVERSE MEDIUM / CBOT_SUPPORT MEDIUM /
  PHYSICAL_TENSION HIGH (courbe NARROWING) → objectif recommandé z→0.5.

C'est un produit research qui commence à être sérieux. Mais l'historique officiel est minuscule, le « quand »
de la compression reste partiel, et le dépôt mélange deux projets.

---

## 2. Ce qui est SOLIDE (faits démontrés)

1. **Réversion du niveau** : stationnarité + demi-vie ≈17 j, AR1 > RW OOS (V120/V121). Robuste.
2. **Asymétrie short** et **edge concentré à z élevé** (V15/V81/V131), stable ex-crise (V81 : 80% win,
   +11.2 €/t hors 2020-2022, LOYO positif).
3. **Compression = surtout rattrapage CBOT** mais **pas uniquement** : V129 mesure 9 CBOT_WEATHER / 8 EU_BALANCE
   / 8 CURVE_RELAXATION (roll) sur 29 épisodes → la jambe EU et le roll comptent chacun ~⅓.
4. **Demi-vie conditionnelle au tier** (V130) : MODERATE 8.3 / STRONG 4.9 / EXTREME 3.3 j ; TAR confirme
   (φ>1.5 = 0.857 rapide vs φ<1.5 = 0.974). Découverte récente, plausible.
5. **Reconstruction du basis live** validée (V108, erreur 0.4 €/t vs journal officiel).
6. **Substitution LOCALE** : corr(ratio blé/maïs, basis) > corr(ratio, CBOT) (V41/V126) — prime européenne.

## 3. Ce qui reste FRAGILE

- **n historique = 42 trades / 29 épisodes** : toute statistique conditionnelle est faiblement puissante.
- **z-score officiel = `proxy_implied`** (historique officiel < 40 j) : les NIVEAUX absolus ne sont pas
  encore validables sur données officielles, seulement les z.
- **PHYSICAL_TENSION** : pas backtestable (courbe officielle pas encore accumulée) — vit en forward.
- **V130 demi-vie par tier** : prometteur mais n petit + risque overfit TAR/Markov → à confirmer en forward.
- **ENSO / production EU** : signaux macro à ~12-13 épisodes indépendants → puissance ≪ n_jours.

## 4. Ce qui est potentiellement FAUX (red-team — vérifié)

- **CONTRADICTION TRIGGER V105** : l'interprétation enregistrée affirme « *si le CBOT monte (et plus pour les
  CBOT_DRIVEN) avant que le basis baisse, c'est le précurseur central* », **alors que ses propres chiffres
  mesurent CBOT pré-start = −0.0241** (et CBOT_DRIVEN = −0.0145) sur t-10→t-1. **Le CBOT BAISSE légèrement
  avant le début de compression, il ne monte pas.** V106 a d'ailleurs trouvé le score INVERSÉ
  (`REFLECTS_ONGOING_NOT_LEADING`), cohérent avec les chiffres, pas avec la narration V105. → **À réécrire
  honnêtement** (ticket B). C'est de l'extrapolation narrative, pas un fait.
- Risque général : d'autres `interpretation` peuvent « raconter » plus que ce que mesure l'artefact. À
  re-scanner systématiquement (ticket B).

## 5. Ce qui est STALE / incohérent

- **Fraîcheur hétérogène des couches** : `latest.json`, V99, V101, V122, V132 ne sont pas tous au même
  `as_of` à un instant donné (V122 le signale déjà via `stale_layers`, mais il n'y a pas de **single source
  of truth** explicite). Un lecteur peut croire que tous parlent du « dernier état ».
- **Pas de `record_status` persistant** dans le journal V27 : il n'a que `price_date` + `logged_at` +
  `status`(constante). La logique PROVISIONAL/FINAL/REVISED de V122 existe mais **n'est pas estampillée à
  l'écriture**. Pas de `collected_at_paris` ni `effective_session_date`.

## 6. Ce qui est LEGACY (pollue la lisibilité)

- **`src/mais/ops/daily.py` + `mais daily-run` (cli)** : pipeline farmer/cash (`farmer_backtest`,
  features→targets→audit→factors→train/study/backtest, décisions agriculteur) — **un autre projet** que
  l'indicateur premium. Le chemin premium propre est `scripts/run_daily_collect.py` + V132.
- `src/mais/decision/` (rules/backtest SELL_NOW), `farmer_backtest.py`, `asymmetric_module.py` : legacy.
- **À séparer** : pas supprimer (historique de l'étude), mais isoler et marquer LEGACY / hors périmètre
  premium ; le « head » premium ne doit jamais afficher de SELL_NOW agriculteur.

## 7. Ce qui est DATA_BLOCKED — à requalifier (sources officielles)

| Source | Statut actuel | Statut corrigé | Raison |
|--------|---------------|----------------|--------|
| **Eurostat COMEXT** | DATA_BLOCKED | **PARTIAL_BEST_EFFORT** | Bulk download CSV mensuel/annuel depuis 1988 existe (pas une petite API, mais récupérable) |
| **Open-Meteo Previous-Runs** | non utilisé | **ACTIONABLE** | séries lead-fixe 1-7 j depuis 2024 → vraies révisions multi-lead (V136 ne pouvait pas) |
| **Open-Meteo Historical Forecast** | PARTIAL | PARTIAL (confirmé) | archive depuis 2021/2022, 1 lead |
| **USDA WASDE / NASS QuickStats** | WATCHLIST | **ACTIONABLE** | dates officielles 2026 + QuickStats API (clé gratuite) |
| **CFTC Disaggregated** | OK | OK | historiques annuels depuis 2009 |
| **Euronext historique officiel** | WATCHLIST | WATCHLIST (à prouver) | Web Services / NextHistory / CFTS = vraies voies ; l'endpoint AJAX public n'est PAS prouvé donner de l'historique |
| **Euronext extension horaires** | non exploité | **ACTIONABLE (forward)** | trading EMA jusqu'à 20:15 CET depuis 2026-04-13, DSP reste 18:30 CET → event mode du soir possible sans intraday payant |

## 8. Contrainte temporelle critique (fondatrice de toute la suite)

Le **Daily Settlement Price des commodités Euronext est fixé à 18:30 CET** (inchangé malgré l'extension du
trading à 20:15 CET le 2026-04-13). Donc :
- **toute collecte avant 18:30 CET = PROVISIONAL** (reprend potentiellement le settlement de la veille avec
  une date d'en-tête du jour courant → **faux changement de signal possible**) ;
- **collecte après ~18:35 CET = FINAL**.
- Règle stricte à imposer : journal PROVISIONAL avant 18:30, FINAL après 18:35, **jamais de mélange
  silencieux**. C'est le risque méthodologique #1 (un changement de tier/spread peut venir d'un horodatage,
  pas d'une réalité économique).

## 9. Ce qu'il faut ROUVRIR

1. **Session timing** de bout en bout (ticket A) : `collected_at_utc`, `collected_at_paris`,
   `effective_session_date`, `record_status`, `cbot_close_date`, `eurusd_close_date` + invariants.
2. **Trigger/event-study V105** (ticket B) : réécrire la conclusion conforme aux chiffres.
3. **COMEXT** (ticket C) : requalifier + tenter le bulk download.
4. **Single source of truth** premium (ticket A) : un `premium_daily_head.json` autoritatif ; les autres
   couches s'y réfèrent ou sont marquées STALE / LEGACY / REPORTING_ONLY.

## 10. Points VÉRIFIÉS qui ne sont PAS des blocages (honnêteté)

- **Environnement Parquet** : `pyarrow 24.0.0` présent ici → les tests Parquet passent (suite complète exit
  0). La note « env casse sur Parquet » ne s'applique pas à cette machine ; à fixer côté **CI** (épingler
  pyarrow) pour distinguer erreurs logiques d'erreurs d'environnement, mais ce n'est pas un bug logique.
- **eurusd mal étiqueté** : déjà corrigé (V25-01 relabel, invariant). Clos.
- **Conversion €/t** : `cents/100 / EURUSD * 39.3679` (1 t = 39.3679 bu maïs) — cohérent, validé V108 (err 0.4 €/t).

---

## 11. Stratégie de suite — programme en trois phases

### Phase I — Hardening du noyau (sécuriser la vérité)
Sortir un **mini-produit premium propre**, séparé du legacy farmer :
`premium_daily_head.json`, `premium_monthly_report.md`, `premium_forward_journal`, doc de périmètre unique.
Fermer : séparation premium/legacy, session timing PROVISIONAL/FINAL/REVISED, cohérence des dates, signe de
courbe, fraîcheur (single source of truth), quality_flag, docs mois de contrat, restatuts de sources, CI Parquet.
**Ne pas ouvrir de nouvelle piste tant que ces points ne sont pas fermés.**

### Phase II — Données qui expliquent la prime justifiée (leading)
1. **EU physical pressure** : indice mensuel→nowcast (COMEXT flux + FranceAgriMer bilans + MARS rendements)
   pour distinguer « prime haute justifiée » vs « prime haute fragile ».
2. **Forecast revision tape** : Δ jour-sur-jour des jours >32°C à lead 3, Δ cumul pluie lead 5, écart
   run-précédent/run-courant (Open-Meteo Previous-Runs), dispersion inter-modèles, surprise vs climatologie.
3. **Event microstructure forward** : snapshots publics du soir (17:55/18:05/18:20/18:35/19:00/20:15 CET) les
   jours WASDE/Grain Stocks/Acreage/appels d'offres/chocs météo → base événementielle EMA (front, spread,
   OI, bid/ask) + réaction CBOT. **C'est le levier #1 pour le « quand ça commence à se comprimer ».**
4. **Event tape exact** : passer V129 du proxy narratif à l'horodatage exact (USDA + COT + MARS/FAM).

### Phase III — Changement de modèle (pas un ajout de features)
1. **Hazard / time-to-compression-start** : P(compression démarre dans 5/10/20 j), covariables strictement
   causales (niveau, vitesse de spread, distance au report, révisions météo, COT, substitution, roll, tension UE).
2. **Transitions d'état** : remplacer NO_SIGNAL/MODERATE/STRONG/EXTREME par des trajectoires —
   EXTREME_STATIC, EXTREME_EARLY_RELAXATION, STRONG_CBOT_CATCHUP, STRONG_PHYSICAL_JUSTIFIED,
   WAIT_CONFIRMATION, ADVERSE_DRIFT (plus de signaux exploitables sans baisser brutalement les seuils).
3. **Discriminant bon short vs ADVERSE** post-entrée (MFE initiale faible, spread qui ne se détend pas,
   CBOT_SUPPORT qui se renforce, révision météo défavorable, ratio blé/maïs qui se tend).
4. **Explication hiérarchique par familles** (CBOT, météo anticipée, tension EMA, substitution, balance UE,
   calendrier) → contribution marginale de chaque famille sur 3 cibles : P(compression), temps→z0.5, risque ADVERSE.

---

## 12. Risques de leakage (permanents)

- `shift(1)` + z expandants/trailing sur toute fondamentale ; holdout 2024 jamais touché pour choisir une règle.
- Diagnostics LIVE forward (calcul d'état courant) ≠ backtest → `assert_no_holdout` ne s'y applique pas, mais
  documenté à chaque module.
- Météo/event : datage à l'émission/au timestamp exact, jamais réindexé a posteriori.
- Hazard/transitions : covariables strictement antérieures à t ; cible = futur ; pas de mélange.
- Event mode du soir : snapshots PROVISIONAL clairement marqués, FINAL seulement après 18:35 CET.

## 13. Critères GO / WATCHLIST / DATA_BLOCKED / EXPLANATORY_ONLY

- **GO** : calculable live sans leakage, améliore une DÉCISION (objectif/horizon/distinction justifiée/excessive),
  robuste ex-crise, baseline intacte.
- **WATCHLIST** : pertinent mais données insuffisantes / forward trop court / robustesse non prouvée.
- **DATA_BLOCKED** : source indisponible (documenter la voie officielle).
- **EXPLANATORY_ONLY** : éclaire le POURQUOI, n'entre pas dans la décision live.

## 14. Règle stratégique de fond

**Ne plus optimiser sur les vieux trades. Construire des données forward qui rendent visible la mécanique du
retournement.** C'est la seule façon de sortir du plateau sans sur-ajuster. Tout reste
**RESEARCH_ONLY_NOT_TRADING**.
