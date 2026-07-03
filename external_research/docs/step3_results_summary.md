# Résumé des résultats — Étape 3 (P0)

Date : 2026-06-12. Périmètre exécuté : EXT025, EXT006, EXT026. Modèle principal, scripts d'entraînement et résultats internes **non touchés**. Tout est sous `external_research/experiments/external_tests/` et `external_research/results/external_tests/`.

## 1. Résumé général

| Expérience | Statut | Verdict |
|---|---|---|
| EXT025 benchmarks RW/futures | ✅ terminée | **KEEP** |
| EXT006 roll volume-based | ✅ terminée (volet reconstruction historique bloqué) | **IMPROVE** (+ DATA_BLOCKED sur la reconstruction) |
| EXT026 WASDE vintage | ✅ terminée | **KEEP** (+ **fuite détectée** dans les données internes) |

Fichiers produits : 6 scripts d'expérience + 17 fichiers de résultats (prédictions, métriques, DM-tests, dates de roll, dataset vintage, audits, rapports de validation, README de résultats) + `wasdeparser` cloné (MIT). Plan d'exécution : `step3_execution_plan.md`. Matrices mises à jour (`ideas_matrix.csv` statuts `done_step3`, `experiment_candidates.csv` + colonnes `verdict`/`next_action`).

## 2. EXT025 — Les benchmarks de base sont-ils solides ? OUI

- **La random walk est la baseline la plus difficile à battre à tous les horizons (H5→H90) sur les deux marchés** (CBOT 2000-2023, EMA 2010-2023). Aucun des 36 couples benchmark×horizon ne la bat (Diebold-Mariano, p<0.10) — réplication propre de Reeve & Vigfusson.
- RMSE de référence à battre (extraits) : CBOT H20 = 41,3 ¢/bu, H40 = 56,6 ; EMA H20 = 15,8 €/t, H40 = 22,2 (tableaux complets dans `metrics_ext025.csv`, par sous-période dans `comparison_ext025.csv`).
- RW+drift n'apporte jamais rien ; naive-last-return explose au-delà de H5 ; MA20 toujours pire que la RW.
- Limites : basis sans tableau (pas de série eurusd quotidienne identifiée dans `data/interim` — DATA_BLOCKED partiel documenté) ; « futures-as-forecast » impossible historiquement (pas de courbe profonde avant 2025) ; holdout 2024+ calculé mais jamais comparé (règle 12).
- **Règle de programme désormais en vigueur : tout EXT futur rapporte ses métriques face à ce tableau, DM-test à l'appui.**

## 3. EXT006 — La série continue maïs est-elle fiable ?

**CBOT (vendeur) : aucun artefact détecté** — les fenêtres de roll présumées (10 derniers jours de bourse avant H,K,N,U,Z) montrent des retours et gaps overnight équivalents voire plus calmes qu'ailleurs. Pas de remise en cause des résultats V9-V17 côté CBOT (réserve : sans identité de contrat, preuve indirecte seulement).

**EMA (front continu proxy) : artefacts réels et importants** :
- 69 rolls (≈4,2/an, règle implicite : 15 jours avant expiry), saut moyen **10,22 €/t** les jours de roll vs 1,54 €/t en temps normal (**6,6×**, Welch p<1e-6) ; p90 = 20,4 €/t, max = 97,5 €/t.
- **27/68 rolls font changer le signe du momentum 20j** sur la série raw (12/68 sur l'adjusted).
- La série `adjusted_price` du projet (back-adjustment) réduit l'artefact à 2,5× (non significatif) — elle existe et fonctionne.
- Échelle critique : 10 €/t ≈ le PnL moyen de nos trades basis. Si basis_z historique est calculé sur une série front raw, ~4 sauts/an du même ordre que l'edge passent dans la feature. Les protections V9/V13 (veto UNCERTAIN_ROLL, coût dynamique) atténuent en aval, pas en amont.
- Reconstruction historique volume-based : **DATA_BLOCKED** (l'historique 2010-2024 ne contient que le front). Prototype causal (volume J-1) opérationnel sur 2025-2026 : il diverge du front-par-expiry 45 % des jours (6,55 €/t d'écart moyen) — le front-par-expiry traîne sur un contrat moins liquide une partie du temps.
- **Actions** : (1) règle EXT — features de retour EMA sur `adjusted_price` ou hors jours de roll (`roll_dates.csv` fourni) ; (2) ticket projet séparé proposé — auditer quelle série alimente basis_z en amont ; (3) collecte multi-contrats continue pour un front volume-causal forward.

## 4. EXT026 — Les données WASDE sont-elles utilisables sans fuite ?

**Les données internes actuelles : NON. Le nouveau vintage : OUI.**

- **FUITE CONFIRMÉE** dans `data/interim/wasde.parquet` : sur 160 rapports à date de publication réelle connue, **143 (89 %) ont leurs valeurs visibles ~8 jours avant la publication** (expansion quotidienne calée sur le 1er du mois au lieu du ~10). Toute feature `wasde_*` interne était en avance d'information. Nuance : le NO_GO WASDE de V18 (sur la prime) reste valide — la fuite rendait le test optimiste et il était déjà négatif. Correction proposée (ticket projet, hors périmètre externe) : recaler sur `publication_date + 1 jour ouvré`.
- **Pipeline vintage construit** à partir de l'archive interne déjà présente (210 txt USDA Cornell) : `wasde_vintage_dataset.csv`, 207 rapports 2002-2025, valeurs telles que publiées, dates de publication réelles pour 77 % (links Cornell + calendrier USDA), fallback conservateur jour-12 pour 23 %, `available_from = publication + 1 jour ouvré`, variations M−M-1 prêtes (proxy surprise EXT008).
- **Validation : 24/24 valeurs retrouvées** dans les textes bruts sur 3 rapports historiques (été/automne/hiver) — VALIDATED.
- Variables prêtes pour EXT007/EXT008 : production, stocks (début/fin), stocks-to-use, exports, usage total/domestique, feed/residual, FSI, prix ferme + variations. Partielles : ethanol (87 %), surfaces/rendement (51 %, absents des rapports d'hiver par construction). `wasdeparser` (MIT) cloné en contre-vérification.

## 5. Décisions

- **EXT025 : KEEP** — tableau de référence en vigueur pour tout le programme.
- **EXT006 : IMPROVE** — série CBOT validée ; série EMA raw à ne plus utiliser telle quelle pour des features de retour (adjusted ou exclusion des rolls) ; reconstruction historique DATA_BLOCKED ; audit amont basis_z proposé en ticket projet.
- **EXT026 : KEEP** — vintage validé, source unique WASDE des EXT futurs ; fuite interne documentée avec correction proposée.

## 6. Recommandation pour l'étape 4 (P1) : **GO, avec deux préalables**

Les fondations sont en place : baselines de référence (EXT025), règles d'hygiène de série (EXT006), source WASDE anti-fuite (EXT026). Les expériences P1 peuvent être lancées :

| P1 | Prête ? | Conditions |
|---|---|---|
| EXT007 features rapports USDA | ✅ | utiliser exclusivement `wasde_vintage_dataset.csv` + calendrier élargi |
| EXT027 crop progress surprises | ✅ | données NASS QuickStats à collecter (API publique) |
| EXT018 prime météo new-crop | ⚠️ | nécessite les contrats Z CBOT par année — vérifier la disponibilité interne (sinon DATA_BLOCKED, données contrats CBOT absentes confirmées par EXT006) |
| EXT005 courbe / full carry | ⚠️ | côté CBOT : DATA_BLOCKED (pas de contrats) ; côté EMA : faisable sur la courbe accumulée 2025+ seulement — re-scoper avant lancement |

Préalables recommandés avant l'étape 4 : (1) validation humaine de ce rapport (notamment les deux découvertes : fuite WASDE interne et artefacts de roll EMA, qui méritent chacune un ticket projet correctif côté interne) ; (2) re-scoping de EXT018/EXT005 au vu de l'absence de contrats CBOT historiques (alternative : sourcer des contrats CBOT, ou réorienter EXT005 vers la courbe EMA).

Aucun code P1 n'a été écrit (règle respectée).
