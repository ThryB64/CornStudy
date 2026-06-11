# TICKETS CONTINUATION V150-V165 — mapping et statuts

_2026-06-11 · RESEARCH_ONLY_NOT_TRADING_

**Avertissement de numérotation.** Le cadrage « continuation V150-V165 » utilise une numérotation qui
entre en collision avec le palier déjà exécuté du repo (`.ai/TICKETS_SUITE_ETUDE.md`, V150→V174, clôturé
le 2026-06-10). Ce document fait le mapping : pour chaque ticket du cadrage, où le travail existe
réellement, et ce qui restait à faire (exécuté ou data-gated). **Référence = numérotation repo.**

| Cadrage | Objet | Réalité repo | Statut |
|---|---|---|---|
| V150 sessionized journal | vérité de session, REVISED>FINAL>PROVISIONAL | **V150-repo** (`session_timing`, backfill, loader `final_only`) — validé en production le 06-10 | `DONE` |
| V151 premium head single source | head = source unique | **V151-repo** (`premium/head.py`, session_truth exposée) | `DONE` |
| V152 daily/monthly/dashboard sync | aucune divergence entre rapports | **V152-SYNC (cette session)** : le CI ne commitait ni `data/premium` ni `reports/monthly` ni les couches autoritatives → head/dashboard/monthly stale au 06-02 dans le repo. Corrigé : workflow commite tout, monthly V133 ajouté au daily, audit `mais/audit/single_source.py` (7 checks PASS), 5 tests, `docs/SINGLE_SOURCE_OF_TRUTH.md` | `DONE` |
| V153 START vs IN_PROGRESS | séparer prédiction du départ / reconnaissance | **V153-repo** : labels sans lookahead, START_h10 AUC OOF 0.549 → `START_TIMING_REMAINS_HARD_DESCRIPTIVE_ONLY` (rejet honnête, ne pas forcer) | `DONE (NO_GO START)` |
| V154 event study 2.0 | IC bootstrap, censure, médianes | **V152-repo** `v152_event_study_v2.py` : 63 épisodes, z médian 1.33→0.34 à +90 j, PNG + censure | `DONE` |
| V155 weather revision engine | révisions de prévision → canaux | **V140/V127-repo + cette session** : bug API corrigé (hourly), 25 296 lignes collectées (17 zones, 92 j), archive append-only committée, test exploratoire vs CBOT (n=62) → `PRELIMINARY_N_SMALL`, re-run à l'été | `DONE (data accumulating)` |
| V156 curve physical tension | courbe officielle → tension | **V125-repo** (accumulation, NARROWING) + V109. Facteurs multi-échéances (V165-repo) data-gated (f2 n=7) | `PARTIAL (data-gated)` |
| V157 MATIF wheat/corn | substitution | **V126-repo** (corr ratio↔basis 0.477, journal forward) + V36/V41 (corr +0.59, spécificité EU) | `DONE (forward validation en cours)` |
| V158 COT positioning | positionnement fonds | Historique : COT n'aide pas OOS (D-négatifs VNEXT) ; COT_SHORT_COVERING dans catalyseurs V143. Pas de nouveau moteur sans donnée nouvelle | `DONE (négatif documenté)` |
| V159 event catalyst library | catalyseurs | **V129/V137/V143-repo** : 29 épisodes attribués, classes CBOT_WEATHER/EU_BALANCE/CURVE_RELAX ~⅓, dates USDA | `DONE` |
| V160 robustness pack | anti-overfitting | **V171+V172-repo** : placebo (edge spécifique rang 1/6), DSR (ne survit pas à 50 essais), PBO 0.26 (robuste), SPA p≈0.06 → `FRAGILE_UNDER_MULTIPLICITY` honnête | `DONE` |
| V161 econometrics advanced | dynamique du basis | **V130 (demi-vies par régime) + V162-repo (VECM, ECM 14.5 j) + V164-repo (HMM) + V167-repo (saisonnalité)** | `DONE` |
| V162 signal tiers/watchlist | pré-signaux | **V175 (cette session)** : PRE_SIGNAL→signal 47 % (n=34, préavis médian 2 j), WATCHLIST→signal 19 %, aucun discriminant ex-ante robuste (artefact gap-jump corrigé). Doc `SIGNAL_TIERS_AND_WATCHLIST_REPORT.md` | `DONE (descriptif)` |
| V163 state machine | cycle de vie | **V139-V148-repo** : machine d'état dans le head (PRIME_*/COMPRESSION_*/TARGET_*), live COMPRESSION_HEALTHY | `DONE` |
| V164 research reporting | rapports lisibles | daily latest + dashboard v4 + lifecycle + monthly V133 (désormais quotidien) + jalons V147 (10/40/90) | `DONE` |
| V165 acquisition package | demandes externes | **V158-repo** `docs/ACQUISITION_PACKAGE.md` (e-mails Euronext/Barchart/CME prêts) — **envoi = action utilisateur** | `DONE (envoi pendant)` |

## Restent ouverts (data-gated / external)

| Ticket repo | Blocage | Débloque quand |
|---|---|---|
| V144 biais proxy↔officiel | pas d'overlap temporel | ≥40 j officiels (jalon V147) ou export historique |
| V165-repo facteurs de courbe | f2 quasi vide | accumulation V125 ou export Euronext |
| V161-repo parité d'import | FOB/fret absents | brancher COMEXT prix unitaires + Baltic (gratuit, à collecter) |
| V155 re-run | n=62 < 150 | archive météo couvre l'été 2026 (automatique, CI) |
| V158-repo e-mails | action externe | utilisateur envoie (`docs/ACQUISITION_PACKAGE.md`) |

## Règle de complétion appliquée

Aucun ticket marqué DONE sans : résultat reproductible (module + runner), artefact JSON, tests verts,
review (sections « artefact détecté/corrigé » des docs), verdict explicite — y compris les verdicts
négatifs (`NO_GO START`, `PRELIMINARY_N_SMALL`, `FRAGILE_UNDER_MULTIPLICITY`), conservés tels quels.
