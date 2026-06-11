# AUDIT DE CONTINUATION — Étude Maïs EMA/CBOT

_Date : 2026-06-10 · Statut global : RESEARCH_ONLY_NOT_TRADING · Baseline figée (z>1 SHORT_PREMIUM, paliers 1/1.5/2, objectifs z→0.5 / z→0)._

Cet audit répond au cadrage « continuation V150-V165 ». **Constat central : le palier V150-V174 du repo
(`.ai/TICKETS_SUITE_ETUDE.md`), clôturé le 2026-06-10, couvre déjà l'essentiel du cadrage demandé, sous
une numérotation différente.** Le mapping exact est dans `docs/TICKETS_CONTINUATION_ETUDE_V150_V165.md`.

## 1. État actuel exact

- **Live** : journal officiel forward = 9 jours de marché (2026-05-29 → 2026-06-10), 10 enregistrements
  (7 PROVISIONAL, 2 REVISED, 1 FINAL). Dernier jour = REVISED (le bot du soir 21:07 UTC upgrade le
  PROVISIONAL du matin — politique V150 validée en production).
- **Signal live** : SHORT_PREMIUM_STRONG, basis officiel 73.5 €/t, z 1.849 (proxy_implied), état machine
  COMPRESSION_HEALTHY, nature PRIME_PHYSICALLY_JUSTIFIED, objectif z→0.5, horizon ~29 j.
- **Infrastructure** : single source `data/premium/premium_daily_head.json` (V151), machine d'état V139,
  dashboard v4, lifecycle, jalons (prochain : 10 jours officiels), GitHub Actions daily collect.
- **Connaissance** : ~170 tickets V* exécutés depuis le 2026-05-31. Bilan robustesse triangulé (voir §5-7).

## 2. Données disponibles

| Source | État | Détail |
|---|---|---|
| Journal officiel EMA (settlement Euronext) | ✅ forward | 9 jours, append-only, sessionisé V150 |
| Proxy EMA Barchart (historique) | ✅ | 2010→2025-07, exploratoire, PROXY_FORBIDDEN en benchmark |
| CBOT corn (continu + EUR/t) | ✅ | roundtrip audité (err max 0.008 €/t, V159) |
| Courbe EMA officielle (front/next) | ✅ forward | `ema_curve_history.parquet`, accumulation V125 |
| MATIF blé/maïs ratio | ✅ forward | journal V126, corr(ratio, basis)=0.477 |
| Météo forecast (journal forward) | ✅ forward | `weather_forecast_journal.jsonl` US+EU |
| Météo previous-runs (révisions lead-fixe) | ⚠️ collecteur codé | **réseau désormais disponible — collecte à lancer (cette session)** |
| COT CFTC | ✅ historique | lag publication géré ; n'aide pas OOS (D-négatif VNEXT) |
| EUR/USD, TTF, ETS | ✅ | yfinance |
| Eurostat/COMEXT flux | ⚠️ PARTIAL | requalifié PARTIAL (VNEXT) ; prix unitaires non branchés |
| FOB Black Sea / Brésil + fret | ❌ | paywall — bloque V161 parité d'import |
| Historique officiel Euronext long (2014+) | ❌ | demandes prêtes (`docs/ACQUISITION_PACKAGE.md`), envoi utilisateur |
| Intraday CBOT historique | ❌ | payant, WATCHLIST (V128) |

## 3. Données manquantes (impact)

1. Historique officiel EMA long → z-score reste **proxy_implied** ; jalon 40 j (validation staged V144) non atteint (9 j).
2. Overlap proxy↔officiel → modèle de biais V144 impossible avant ~40 jours officiels.
3. FOB/fret → parité d'import V161 bloquée.
4. Intraday CBOT → probe V128 reste WATCHLIST.
5. Profondeur de courbe officielle (f2+) → facteurs de structure par terme (V165-repo) data-gated.

## 4. Expériences déjà faites (familles)

Mean-reversion basis (V10-V17), explication macro du basis (V16 : R² OOF −0.25, prime LOCALE),
ADVERSE_RISK règle-basé (V38-V41), météo réalisée (V45 : price-in, AUC 0.508), catalyseurs (V129/V137/V143),
demi-vies par régime (V130 : MOD 8.3j/STR 4.9j/EXT 3.3j), machine d'état (V139-V148), event study 2.0
(V152-repo : 63 épisodes, z médian 1.33→0.34 à +90j), START vs IN_PROGRESS (V153-repo), VECM (V162-repo),
HMM (V164-repo), saisonnalité des départs (V167-repo), placebos (V171-repo), anti-overfitting DSR/PBO/SPA
(V172-repo), audits vérité de données (V159-repo).

## 5. Conclusions solides

1. **Cointégration EMA/CBOT** (EG p=7.3e-7 ; Johansen V162-repo β=[1,−0.96]) ; **les 2 jambes corrigent ~50/50** (α_ema −0.020 / α_cbot +0.019), demi-vie ECM 14.5 j — nuance la lecture V21 « tout-CBOT ».
2. **Mean-reversion du basis_z confirmée** (V10 AR(1) φ=0.96 ; event study : compression médiane ~1.0 z en 90 j sur 63 épisodes) ; demi-vie rétrécit avec l'extrême (V130).
3. **Edge spécifique au basis EMA/CBOT** (V171 : Sharpe/trade 0.94, rang 1/6 vs témoins ≤0.37).
4. **Sélection de seuil robuste** (PBO 0.26, V172).
5. **La prime est LOCALE** : la macro ne l'explique pas (V16), corr(wheat/corn, basis)=+0.59 vs corr(ratio, CBOT)=−0.46 (V41).
6. **Vérité de session** : journal sessionisé, REVISED>FINAL>PROVISIONAL, validé en production (V150).
7. Compression historique surtout par hausse CBOT (V21/V105 : CBOT baisse −0.024 avant, puis rattrape), mais correction symétrique en cointégration (V162) — les deux lectures coexistent (horizons différents).

## 6. Conclusions fragiles

1. **Taille de l'edge après multiplicité** : Deflated Sharpe NE survit PAS à 50 essais (0.11) ; SPA p≈0.060 → `FRAGILE_UNDER_MULTIPLICITY`. L'edge est réel/spécifique mais PETIT.
2. **z-score proxy_implied** : niveaux validés (officiel +76 €/t = 99e pctl proxy) mais la calibration fine attend 40 j officiels.
3. **Horizon analytique ≠ horizon trade** (V138 : 9.5 j vs 28.6 j réels, calage ×3) — WATCHLIST.
4. **Catalyseurs** : attribution ex-post, overlap mensuel quasi mécanique avec dates USDA (V137).
5. Saisonnalité des départs (pic août) : edge survit hors-saison, mais n=63 épisodes.

## 7. Conclusions rejetées / requalifiées (à ne PAS rouvrir sans donnée nouvelle)

- Timing du départ de compression **non prédictible ex-ante** (V153-repo : START_h10 AUC OOF 0.549) — mais le label START est RÉEL (V164-repo HMM : 85 % de coïncidence) → le score actuel est DESCRIPTIF (IN_PROGRESS), renommé `COMPRESSION_PROGRESS_SCORE`.
- Inversion saisonnière V8 : FALSIFIÉE OOF (V9).
- H90 : réfuté (V10). Filtre régime : rejeté forward (V11). Fair-value macro du basis : rejetée (V16).
- Météo réalisée → CBOT : pas de signal (V45, AUC 0.508). COT OOS : n'aide pas (VNEXT D-négatifs).
- Hazard timing : AUC ≈ base rate (V106/VNEXT).
- Mécanisme de compression non prévisible (V35 AUC 0.48).

## 8. Artefacts stale / incohérents (TROUVÉS PAR CET AUDIT)

| Artefact | État au début de session | Cause |
|---|---|---|
| `data/premium/premium_daily_head.json` | **stale 06-02** (journal au 06-10) | workflow CI ne commite pas `data/premium/` |
| `data/premium/dashboard_v4.md`, `lifecycle.md` | stale 06-02 | idem |
| `reports/monthly/latest.md` | stale 06-02 | monthly pas dans le daily script ni commité |
| `artefacts/v122/v132/v123` locaux | stale 06-02 | régénérés en CI mais non commités |
| v122/v123 locaux après resync | INCONSISTENT/DEGRADED | couches contextuelles (v99/v101, cbot/cot) réseau-dépendantes non commitées |

**Correctif appliqué (cette session)** : resync local exécuté (head 06-10 = état CI), workflow corrigé pour
commiter les artefacts canoniques. Voir `docs/SINGLE_SOURCE_OF_TRUTH.md`.

## 9. Risques de leakage (gardés sous contrôle)

- `shift(1)` + z-scores expandants sur toutes les fondamentales (règle projet) ; audit `make audit` future_dep=0.
- COT : utilisable seulement après publication du vendredi (géré).
- Météo : seules les **prévisions datées par issue_date** sont utilisables (V127/V136) ; l'archive API ne donne qu'un lead → previous-runs requis pour les révisions (collecteur lead-fixe V140-DATA).
- Labels START/INPROG : test de non-fuite vert (V153-repo).
- Risque résiduel : toute étude sur épisodes (n=42-63) reste vulnérable au survivorship des définitions d'épisode — d'où placebos + PBO maintenus dans la boucle.

## 10. Risques de sur-optimisation

- 42 trades / 63 épisodes = petits échantillons. Défense actuelle : PBO 0.26, DSR honnête (ne survit pas),
  SPA borderline, placebo rang 1/6. **Toute nouvelle règle doit passer par ce pack (V172-repo) avant claim.**
- Interdits maintenus : pas de réoptimisation des seuils de la baseline, holdout intouché, pas de deep learning opaque.
- Recensement exhaustif des variantes testées (pour corriger DSR du vrai nombre d'essais) : reste à tenir à jour.

## 11. Priorités de recherche (ordre recommandé)

1. **P0 — Source unique vraiment unique** : le CI doit commiter head/dashboard/monthly/couches autoritatives (fait cette session) ; test de cohérence automatisé.
2. **P1 — Météo previous-runs** : réseau désormais OK → collecter les révisions lead-fixe US+EU, brancher le revision engine (V140), tester révisions → CBOT/START/IN_PROGRESS. Résultat négatif acceptable et attendu (V153).
3. **P1 — Signal tiers / pré-signaux** (0.5≤z<1) : escalade pré-signal→signal, délais, variables — sans toucher la baseline.
4. **P1 — Accumulation forward** : jalon 10 j (imminent), puis 40 j → V144 biais proxy↔officiel, z-score officiel rolling.
5. **P1 — COMEXT prix unitaires + Baltic** (gratuits) → débloquer V161 parité d'import.
6. **External — envoi des e-mails d'acquisition** (`docs/ACQUISITION_PACKAGE.md`) : action utilisateur.
7. **P2 — Facteurs de courbe multi-échéances** : attendre l'accumulation officielle (V125 forward).

_Vérifications de cet audit : head/latest/dashboard relus en session, chaîne premium resynchronisée
localement (V122→V146), réseau Open-Meteo testé (200), journal sessionisé relu (9 jours, REVISED final)._
