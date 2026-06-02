# Review V122-V150

Statut : RESEARCH_ONLY_NOT_TRADING. Baseline figée. Holdout 2024 verrouillé.
Date : 2026-06-02. Modules V122-V135 implémentés, testés, ruff-clean, branchés.

---

## 1. Nouvelles découvertes (sur données réelles)

### V130 — La demi-vie de réversion RÉTRÉCIT avec l'extrême (découverte forte)
Demi-vie de réversion du basis_z par tier :

| Tier | Demi-vie |
|------|----------|
| MODERATE (1.0–1.5) | **8.3 j** |
| STRONG (1.5–2.0) | **4.9 j** |
| EXTREME (≥2.0) | **3.3 j** |

Plus la prime est extrême, **plus elle se résorbe vite**. Confirmé par le TAR : au-dessus du seuil z=1.5,
φ=0.857 (réversion rapide) ; en dessous, φ=0.974 (lente). Markov-switching identifie 2 régimes (un rapide
φ≈−0.32, un persistant φ≈0.98, demi-vie ~32 j). → **ADD_TO_HORIZON_ESTIMATE** : l'horizon de V27 peut être
affiné par tier (l'EXTREME se traite sur un horizon plus court que le MODERATE).

### V131 — Les signaux marginaux (z<1.2) sous-performent nettement
Sur les 42 trades : PnL des signaux **confirmés 14.14 €/t** vs **marginaux (z<1.2) 6.09 €/t**.
**20/42 signaux sont marginaux.** Attendre une confirmation (état WAIT_CONFIRMATION) est donc justifié —
cohérent avec « edge concentré à z élevé » (V15). Confirmés ≥ meilleur objectif fixe (z→0 12.83 / z→0.5
10.31). → **ADD_TO_INDICATOR** (états WATCH / WAIT_CONFIRMATION ajoutés sans toucher la baseline).

### V129 — Anatomie des compressions (catalogue ex-post)
29 épisodes de compression (pic z≥1.5 → chute ≥1.0 en ≤60 j), durée médiane **19 j** (≈ demi-vie 17 j) :

| Catalyseur | n |
|------------|---|
| CBOT_WEATHER | 9 |
| EU_BALANCE_UPDATE | 8 |
| CURVE_RELAXATION (roll) | 8 |
| UNKNOWN | 3 |
| CBOT_WASDE | 1 |

Seulement **10.3 % non attribué**. La compression se répartit ~équitablement entre **rattrapage CBOT**
(météo/rapports, ~34 %), **détente de la jambe EU** (~28 %) et **roll** (~28 %) — nuance la thèse « tout-CBOT »
de V21 : la jambe EU et le roll comptent autant que le CBOT pris isolément.

### V125 — La backwardation se détend (live)
Sur la courbe officielle accumulée, spread front-next **15.25 → 11.75 €/t (NARROWING)** : tension physique
encore HIGH mais en reflux → la prime commence à devenir plus compressible. Diagnostic dynamique que le
snapshot V109 seul ne donnait pas.

### V126 — Substitution liée au basis confirmée (proxy)
corr(ratio blé/maïs z, basis_z) = **+0.477** sur le master (proxy CBOT). Le ratio officiel EBM/EMA live
(0.914) s'accumule en forward ; l'historique officiel reste WAITING_DATA.

---

## 2. Erreurs corrigées / robustesse

- **Incohérence de révision (V122)** : le journal append-only refusait de réviser une date déjà loggée
  (`ALREADY_LOGGED`) alors que `latest.json` la recalculait → divergence de tier. Corrigé par une
  **politique de révision auditée** : statut PROVISIONAL/FINAL/REVISED + `revision_log` ; révision du jour
  courant uniquement, passé FINAL immuable (anti look-ahead). Cas 2026-06-01 STRONG-vs-EXTREME testé.
- **Gate de fraîcheur par couche (V123)** : le COT est hebdomadaire → un gate plat de 5 j le marquait à tort
  périmé. Gate par couche (COT = 10 j). Live : CONTEXT_COHERENT.
- **Markov-switching (V130)** : extraction des paramètres AR via `param_names` (l'accès par clé string
  échouait sur endog ndarray). Convergence non garantie → dégrade proprement.
- **Anti-leakage** : tous les diagnostics live (V125/V127) datés à l'émission, append-only ; classification
  d'événements (V129) strictement ex-post, jamais un feature.

---

## 3. Données encore manquantes

| Donnée | Statut | Conséquence |
|--------|--------|-------------|
| Historique officiel EMA profond | WATCHLIST (payant) | z reste `proxy_implied` ; PHYSICAL_TENSION non backtestable |
| Intraday CBOT historique | DATA_BLOCKED_PAID (V128) | basis aligné non backtestable → accumulation forward |
| Eurostat COMEXT (flux physiques) | DATA_BLOCKED | flux EU absents |
| Open-Meteo historical-forecast | PARTIAL (timeouts) | révisions de prévision best-effort (V127) |
| Calendrier WASDE exact | WATCHLIST (gratuit) | CBOT_WASDE proxy dans V129 |
| MARS / FranceAgriMer | PARTIAL | balance EU best-effort |

Plan complet : `docs/DATA_SOURCING_PLAN.md` (V134).

---

## 4. Modules ajoutés à l'indicateur (GO)

V122 (cohérence), V123 (fraîcheur), V124 (santé signal v2), V125 (courbe dynamique), V126 (substitution),
V130 (horizon par tier), V131 (reco objectif v3), V132 (**synthèse intégrée v3**), V133 (rapport mensuel v2).
Tous branchés dans le rapport quotidien et le collecteur. V132 est la **vue headline** : PREMIUM_STATE +
diagnostics frais (flaggés stale via V123) + objectif recommandé (règle figée V56) + horizon (V27×V130).

État live au 2026-06-02 : **SHORT_PREMIUM_STRONG** (basis 75.03 €/t, z 1.969), ADVERSE MEDIUM /
CBOT_SUPPORT MEDIUM / PHYSICAL_TENSION HIGH (courbe NARROWING) → **objectif recommandé z→0.5**, horizon ~23 j
(demi-vie tier STRONG 4.9 j).

## 5. Modules explicatifs / forward / rejetés

- **Explicatifs (gardés en doc, pas un signal live)** : V129 (catalyseurs), V134 (sourcing).
- **À mûrir en forward** : V127 (météo forecast — warning d'anticipation), accumulation courbe/MATIF/intraday.
- **WATCHLIST / bloqué** : V128 (intraday, payant). Aucun module rejeté pour dilution cette fois (la leçon
  V64 — ne pas diluer un diagnostic — a été respectée : V131/V132 sont des surcouches, pas des remplacements).

---

## 6. Décision (V135 checkpoint)

- L'indicateur reste **ANALYTIQUE** (research-only). **Paper-trading non justifié** tant que le forward
  officiel < 6 mois et que le z reste `proxy_implied`.
- Les briques décisionnelles **améliorent la décision** (objectif/horizon/santé/cohérence) sans toucher la
  règle d'entrée figée ni les seuils. Diagnostics = contexte, jamais un veto.

## 7. Prochaine roadmap (V136-V150, après mûrissement forward)

1. Accumuler le forward officiel jusqu'aux milestones 10/40/90 j (V124) puis ≥6 mois (V133) → premier bilan sérieux.
2. Brancher (gratuit) Open-Meteo historical (révisions V127) + USDA QuickStats/calendrier (attribution V129).
3. Re-décider PHYSICAL_TENSION/substitution quand l'historique officiel s'accumule (z rolling officiel, V125/V126).
4. Affiner l'horizon V27 par tier avec la demi-vie V130 (déjà mesurée), à valider en forward.

Tout reste **RESEARCH_ONLY_NOT_TRADING**.
