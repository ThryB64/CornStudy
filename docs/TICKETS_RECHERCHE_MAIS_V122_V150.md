# Tickets recherche maïs — V122 à V150

Statut : **RESEARCH_ONLY_NOT_TRADING**. Baseline figée. Holdout verrouillé.
Chaque ticket a été **relu en reviewer critique** (§ Review) avant codage.

Légende classe : `simple` · `moyen` · `complexe` · `critique`.

---

## V122 — Official journal consistency & revision policy `critique`

**Objectif.** Garantir que `latest.json`, `official_forward_journal`, la synthèse V99/V101 et le rapport
quotidien donnent le **même signal pour la même date**. Le journal V27 est append-only et **refuse** de
réviser une date déjà loggée (`ALREADY_LOGGED`), alors qu'un settlement révisé en intra-journée recalcule
un tier différent → divergence (ex. 2026-06-01 loggé EXTREME z 2.039 vs recalcul STRONG z 1.88).

**À faire.**
- Détecter les doublons de `price_date`.
- Gérer les corrections de settlement : politique de révision **auditée** (pas d'écrasement silencieux).
- Ajouter `record_status` ∈ {PROVISIONAL, FINAL, REVISED} et `revision_log` (liste old→new horodatée).
- Une date du **jour même** est PROVISIONAL et révisable ; une date passée (settlement définitif) est FINAL.
- Tester explicitement le cas 2026-06-01 STRONG vs EXTREME.

**Données.** `data/forward_journal/official_forward_journal.parquet/.jsonl` ; pas de réseau (logique pure).
**Leakage.** Aucun risque sur la révision *du jour courant* ; INTERDIT de réviser une date FINAL (look-ahead).
**Métriques.** n révisions, cohérence latest/journal (booléen), tier final par date.
**Livrables.** `v122_journal_consistency.py` + tests + artefact JSON + section doc.
**GO/NO_GO.** GO si LIVE_SIGNAL_CONSISTENT (toutes les couches concordent sur le dernier jour).

**Review critique.** ✔ Objectif clair, données locales, pas de leakage si FINAL immuable. Dépend de rien.
Risque : ne pas casser l'append-only existant → on encapsule (nouveau module qui *enveloppe* V27, sans
modifier `append_forward_journal`). Baseline inchangée. **Validé.**

---

## V123 — Data freshness & context coherence gate `moyen`

**Objectif.** Vérifier que toutes les couches du rapport sont fraîches et cohérentes dans le temps.

**À faire.** Collecter les `as_of` : `signal_as_of`, `cbot_as_of`, `ema_curve_as_of`, `matif_ratio_as_of`,
`weather_as_of`, `cot_as_of` ; calculer `context_lag_days` (max des retards vs signal). Si lag > 5 j sur une
couche → warning + **désactiver** le diagnostic concerné (ne pas l'afficher comme frais).

**Données.** Artefacts V107/V108/V109, journaux MATIF/météo, journal officiel. Pas de réseau (lecture).
**Leakage.** Aucun (méta-information de fraîcheur).
**Métriques.** lag par couche, n couches fraîches/désactivées, verdict CONTEXT_COHERENT.
**Livrables.** `v123_freshness_gate.py` + tests + artefact + doc.
**GO/NO_GO.** GO = CONTEXT_COHERENT (toutes couches ≤5j) ; sinon affiche dégradé honnête.

**Review critique.** ✔ Dépend de V122 (date de référence cohérente). Lecture seule. **Validé.**

---

## V124 — Active signal monitoring v2 `moyen`

**Objectif.** Suivre le signal vivant après l'entrée (étend V102 sans le casser).

**À faire.** `days_since_entry`, `compression_realized`, `MFE`, `MAE`, `distance_to_z05`, `distance_to_z0`,
status ∈ {HEALTHY, SLOW, DELAYED, ADVERSE_LIKE, TARGET_HIT}. Règles seuils 10/20/30 j (calibrées sur la
signature ADVERSE V82, pas optimisées sur PnL).

**Données.** Journal officiel (révisé V122). Lecture seule.
**Leakage.** Aucun (suivi forward d'un signal ouvert).
**Métriques.** status, distances, MFE/MAE en €/t.
**Livrables.** `v124_active_monitoring_v2.py` + tests + artefact + doc.
**GO/NO_GO.** ACTIVE_MONITORING_READY si statut calculable et cohérent sur l'épisode courant.

**Review critique.** ⚠ Risque de duplication avec V102 → on **réutilise** `_current_episode` de V102 et on
ajoute SLOW/DELAYED + seuils 10/20/30 explicites. Pas de seuil optimisé. **Validé après correction** (réutilisation V102).

---

## V125 — Official EMA curve accumulation & physical tension `moyen`

**Objectif.** Accumuler la courbe EMA officielle (snapshots quotidiens) et construire PHYSICAL_TENSION
sur des variables de structure stables.

**À faire.** Store append-only des snapshots de courbe ; variables : front-next, next1-next2, Nov-Mar,
contango/backwardation, volume, OI, most-liquid, roll. Sortie PHYSICAL_TENSION_LOW/MEDIUM/HIGH (réutilise
la logique V109, mais sur la courbe **accumulée** + persistance).

**Données.** `euronext_official_live.fetch_official_ema` (snapshot) → store `data/official_forward/ema_curve_history.parquet`.
**Leakage.** Snapshot daté du jour ; jamais réécrit. Append-only.
**Métriques.** spreads €/t, tier, n snapshots accumulés.
**Livrables.** `v125_curve_accumulation.py` + tests + artefact + doc.
**GO/NO_GO.** ADD_TO_DAILY_REPORT (déjà branché via V109 ; ici on ajoute l'accumulation + tendance du spread).

**Review critique.** ⚠ Recoupe V109. Distinction : V109 = snapshot live → tier ; V125 = **accumulation
historique** + tendance (le spread se creuse-t-il ?). On garde V109 pour le live, V125 pour la dynamique.
Pas de double-comptage dans le rapport. **Validé.**

---

## V126 — MATIF wheat/corn official substitution `moyen`

**Objectif.** Construire le vrai ratio Euronext Milling Wheat (EBM) / Euronext Corn (EMA) et tester sa
relation au basis / ADVERSE / objectif.

**À faire.** Réutiliser `euronext_milling_wheat` + `v52_matif_substitution` ; accumuler le journal forward ;
tester relation ratio↔basis (sur master pour l'historique, forward pour le live) ; relation à ADVERSE ;
impact objectif z→0.5 vs z→0.

**Données.** EBM + EMA officiels (live OK) ; historique aligné = WAITING_DATA.
**Leakage.** Ratio = z expandant ; shift(1) sur le master.
**Métriques.** corr(ratio, basis), séparation ADVERSE, n jours forward.
**Livrables.** `v126_matif_substitution_v2.py` + tests + artefact + doc.
**GO/NO_GO.** SUBSTITUTION_SIGNAL_READY si relation confirmée sur master + live ; sinon DATA_BLOCKED (historique).

**Review critique.** ⚠ Recoupe V40/V41/V52. Valeur ajoutée = ratio **officiel EBM/EMA** (pas ZW/ZC proxy)
+ journal forward dédié. Honnête sur WAITING_DATA historique. **Validé.**

---

## V127 — Weather forecast extremes & revisions `moyen`

**Objectif.** Collecter et tester la météo **forecast extrême** (pas les moyennes) + ses **révisions**.

**À faire.** Variables : jours >32°C, jours >35°C, déficit pluie, **révision pluie**, **révision température**,
stress phénologique, incertitude (spread d'ensemble). US → CBOT_SUPPORT ; Europe → PHYSICAL_TENSION/ADVERSE_RISK.

**Données.** Open-Meteo forecast (OK) ; historical-forecast pour révisions (timeout → best-effort).
**Leakage.** Datage à l'émission (issue_date), anti-leakage strict ; révision = Δ entre deux émissions.
**Métriques.** n jours extrêmes, magnitude révision, lien direction CBOT/EU (descriptif).
**Livrables.** `v127_weather_forecast_extremes.py` + tests + artefact + doc.
**GO/NO_GO.** WEATHER_WARNING_READY si forecast extrême collecté + journalisé ; révisions = DATA_BLOCKED si timeout.

**Review critique.** ⚠ Recoupe V45/V48/V51. Rappel V45 : stress **réalisé** ne prédit pas le CBOT. Ici on
reste sur le **forecast/forward** (anticipation) et on n'en fait qu'un **warning de contexte**, jamais un
prédicteur de timing. **Validé** (cadré comme warning, pas signal).

---

## V128 — Intraday CBOT aligned basis `moyen`

**Objectif.** Mesurer si l'alignement intraday (CBOT au moment du settlement Euronext ~14h30 Paris) réduit
le bruit du basis vs le close US (~20h Paris).

**À faire.** Probe de sources intraday CBOT ; si dispo : CBOT@settlement-EU, CBOT close US, move settlement→close ;
tests basis daily vs aligned (bruit, ADVERSE, compression J+1/J+3).

**Données.** Intraday CBOT historique = **payant** (Barchart/CQG/TT). Probe honnête.
**Leakage.** N/A (probe).
**Métriques.** réduction de variance du basis, si données.
**Livrables.** `v128_intraday_aligned_probe.py` + tests (probe offline) + artefact + doc.
**GO/NO_GO.** ADD_TO_PIPELINE si source gratuite trouvée ; sinon WATCHLIST/DATA_BLOCKED documenté.

**Review critique.** ⚠ Recoupe `intraday_aligned_basis.py` existant. Très probablement DATA_BLOCKED (payant).
On le traite comme **probe + entrée sourcing V134**, sans promettre de données. **Validé** (attente réaliste : WATCHLIST).

---

## V129 — Fundamental event catalyst library `moyen`

**Objectif.** Associer chaque **retournement** de la prime (compression/écartement) à un **catalyseur
fondamental** ex-post. Explicatif, jamais prédictif.

**À faire.** Détecter les retournements de basis_z sur le master ; pour chaque, chercher l'événement proche :
WASDE, COT, Crop Progress, EC MARS, FranceAgriMer, Eurostat, news Ukraine, météo extrême, roll. Classer :
CBOT_WEATHER, CBOT_WASDE, COT_SHORT_COVERING, EU_WEATHER_RELIEF, EU_BALANCE_UPDATE, CURVE_RELAXATION, UNKNOWN.

**Données.** Master + calendriers USDA/WASDE (si dispo), COT, météo. Best-effort sur calendriers.
**Leakage.** Classification **descriptive ex-post**, JAMAIS un feature prédictif (sinon look-ahead).
**Métriques.** répartition des classes, % UNKNOWN.
**Livrables.** `v129_event_catalyst_library.py` + tests + artefact `data/research/event_catalyst_library.parquet` + doc.
**GO/NO_GO.** EVENT_LIBRARY_READY si classification produite (même avec UNKNOWN majoritaire = honnête).

**Review critique.** ✔ Valeur explicative forte (comprendre *pourquoi* la prime tourne). Bien cadrer
« descriptif, pas un signal ». Calendriers WASDE peut-être indisponibles → fallback heuristique daté. **Validé.**

---

## V130 — Basis regime econometrics `complexe`

**Objectif.** Approfondir V120/V121 par **régimes** : la demi-vie de réversion dépend-elle du contexte ?

**À faire.** Demi-vie (AR1 φ→ ln2/−lnφ) conditionnelle à : tier, PHYSICAL_TENSION, CBOT_SUPPORT, ratio MATIF.
Modèle TAR (seuil sur basis_z) ; Markov switching simple (statsmodels MarkovRegression) si convergence.

**Données.** Master (basis_z + diagnostics). `assert_no_holdout`.
**Leakage.** Estimation in-sample ex-crise documentée ; pas de sélection de règle sur holdout.
**Métriques.** demi-vie par régime (j), AIC TAR vs AR1 linéaire, régimes Markov.
**Livrables.** `v130_basis_regime_econometrics.py` + tests + artefact + doc.
**GO/NO_GO.** ADD_TO_HORIZON_ESTIMATE si demi-vie diffère nettement par régime (affine l'horizon V27) ; sinon WATCHLIST.

**Review critique.** ⚠ Risque overfit (TAR/Markov sur série courte). Garde-fou : ex-crise, AIC vs modèle
simple, rejeter si gain marginal. Imports statsmodels en try/except. **Validé avec réserve overfit.**

---

## V131 — Target recommendation v3 `moyen`

**Objectif.** Étendre V56 : recommander WATCH / z→0.5 / z→0 / WAIT_CONFIRMATION.

**À faire.** Règle (aucun fit) :
- PHYSICAL_TENSION HIGH → z→0.5 ; CBOT_SUPPORT LOW → z→0.5 ; ADVERSE_RISK HIGH → z→0.5 ;
- CBOT_SUPPORT MED/HIGH + tension LOW + adverse LOW → z→0 ;
- signal naissant/ambigu → WATCH ou WAIT_CONFIRMATION ; sinon z→0.5.
Métriques : PnL, profit/jour, exposition, MAE, MFE, hit z→0.5, hit z→0.

**Données.** Master + diagnostics + trades pairés (V47). `assert_no_holdout`.
**Leakage.** Aucun fit ; règle interprétable.
**Livrables.** `v131_target_recommendation_v3.py` + tests + artefact + doc.
**GO/NO_GO.** ADD_TO_INDICATOR si ≥ aussi bon que V56 en PnL et meilleur en efficacité/exposition.

**Review critique.** ⚠ Recoupe V56. Valeur ajoutée = états WATCH/WAIT_CONFIRMATION (gestion du signal
naissant). Ne PAS remplacer V56 figé ; v3 = surcouche. **Validé.**

---

## V132 — Indicator synthesis v3 `complexe`

**Objectif.** Assembler l'indicateur **final** research en un objet unique.

**À faire.** Sortie : PREMIUM_STATE, basis_z, official/proxy status, ADVERSE_RISK, CBOT_SUPPORT,
PHYSICAL_TENSION, SUBSTITUTION_SUPPORT, WEATHER_WARNING, ACTIVE_SIGNAL_HEALTH, TARGET_RECOMMENDATION,
HORIZON_ESTIMATE, explanation, warnings, research_only. Combine V101(signal) + V107/108/109(contexte frais)
+ V124(santé) + V125(courbe) + V126(substitution) + V127(météo) + V130(horizon) + V131(reco).

**Données.** Artefacts des modules + journal. Lecture/orchestration.
**Leakage.** Aucun (assemblage de briques déjà validées).
**Livrables.** `v132_indicator_synthesis_v3.py` + tests + artefact `artefacts/v132/indicator_v3_latest.json` + doc.
**GO/NO_GO.** Toujours produit (c'est la vue intégrée) ; chaque champ flaggé frais/stale via V123.

**Review critique.** ✔ Cœur de la livraison. Dépend de tous les précédents → **dernier vrai assemblage**.
Doit dégrader proprement si une brique manque (champ = UNKNOWN/STALE). **Validé.**

---

## V133 — Monthly forward report v2 `simple`

**Objectif.** Rapport mensuel clair (étend V59).

**À faire.** jours officiels, signaux, cohérence latest/journal (V122), proxy vs officiel (V103), basis_z,
targets, MFE/MAE, weather, MATIF ratio, curve tension, état du signal actif.
**Livrables.** `v133_monthly_forward_report_v2.py` + tests + artefact markdown + doc.
**GO/NO_GO.** Produit le rapport ; pas de décision binaire.

**Review critique.** ✔ Reporting, faible risque. Réutilise V59/V103/V122/V124. **Validé.**

---

## V134 — Data sourcing plan for missing sources `simple`

**Objectif.** Documenter, pour chaque source manquante : disponibilité, coût probable, contraintes, accès API, statut.

**À faire.** Tableau structuré (code + doc) : Euronext Web Services, Bloomberg/LSEG/Barchart/CQG/TT,
Open-Meteo historical forecast, NOAA/GFS/GEFS, EC MARS, FranceAgriMer, Eurostat COMEXT, intraday CBOT.
**Livrables.** `v134_data_sourcing_plan.py` (génère JSON structuré) + tests + `docs` + artefact.
**GO/NO_GO.** DATA_SOURCE_PLAN_READY.

**Review critique.** ✔ Documentation structurée, pas de réseau requis. **Validé.**

---

## V135 — Decision checkpoint `moyen`

**Objectif.** Après V122-V134, statuer : ce qui améliore vraiment / ce qui est seulement explicatif /
ce qui est bloqué / ce qui doit continuer en forward / si un paper-trading research est justifié /
si l'indicateur reste uniquement analytique.

**Livrables.** `v135_decision_checkpoint.py` (agrège les verdicts) + `docs/REVIEW_V122_V150.md`.
**GO/NO_GO.** Produit le bilan ; recommandation explicite par module (GO/WATCHLIST/NO_GO).

**Review critique.** ✔ Synthèse finale. Dépend de tous. **Validé.**

---

## Ordre de dépendance (validé)

```
V122 (révision) ─┬─> V123 (fraîcheur) ─┐
                 ├─> V124 (monitoring) ─┤
V125 (courbe) ───┤                      ├─> V132 (synthèse v3) ─> V133 (rapport) ─> V135 (checkpoint)
V126 (MATIF) ────┤                      │
V127 (météo) ────┤                      │
V129 (events) ───┤                      │
V130 (économétrie) ─> V131 (reco v3) ───┘
V128 (intraday probe) ── indépendant (WATCHLIST attendu)
V134 (sourcing) ── indépendant
```

## Invariants (tous tickets)

- Baseline `MaizePremiumIndicator` figée ; seuils 1/1.5/2 inchangés ; stop −20/−25 ; statut RESEARCH_ONLY_NOT_TRADING.
- Diagnostics = **contexte, jamais un veto**.
- Aucun meta-model / deep learning / chasse à l'AUC. Aucune optimisation sur les 42 trades. Holdout intact.
- Imports optionnels en try/except ImportError. Pas de commentaire évident, pas de docstring multi-paragraphe inutile.
- Chaque module : code + tests + artefact JSON + doc + ruff + pytest ciblé + zéro régression.
