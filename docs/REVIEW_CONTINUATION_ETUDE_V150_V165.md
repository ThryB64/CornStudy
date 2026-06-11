# REVIEW — Continuation de l'étude (session 2026-06-11)

_Périmètre : audit de continuation + V152-SYNC + V140-DATA/V155 météo + V175 tiers.
Voir `docs/TICKETS_CONTINUATION_ETUDE_V150_V165.md` pour le mapping complet avec le palier V150-V174._

## 1. Ce qui a été corrigé

- **Artefacts live stale (P0)** : le repo servait un head/dashboard/monthly du 06-02 alors que le
  journal officiel était au 06-10 — le CI régénérait ces fichiers à chaque run sans les commiter.
  Corrigé : workflow commite `data/premium`, `reports/monthly`, couches autoritatives `artefacts/v99
  v101 v107 v109 v122 v123 v124 v132 state_machine` ; monthly V133 ajouté au daily ; resync local fait.
- **Audit de cohérence automatisé** : `mais/audit/single_source.py` (7 checks, PASS), branché en fin de
  daily, artefact `artefacts/audit/single_source_report.json`. 5 tests dédiés.
- **Collecteur previous-runs cassé en réel** : l'API n'expose `_previous_dayN` qu'en horaire (400 sur
  daily). Fetch hourly + agrégation par date de validité. Constat impossible offline — premier lancement réseau.
- **Sémantique `zones={}`** : retombait sur toutes les zones (`zones or default`) — bug masqué hors-ligne,
  corrigé (`if zones is None`).
- **Artefact statistique dans l'étude tiers** : les gap-jumps (z saute la cible le jour d'entrée)
  rendaient `z_slope_5d` faussement discriminant (p≈0.000 → p=0.33 après filtre de bande stricte).

## 2-3. Ce qui a été ajouté / nouvelles données

- **Archive de révisions météo lead-fixe** : `data/weather/forecast_revisions.parquet` — 25 296 lignes,
  17 zones (10 US + 7 EU), validités 2026-03-11→2026-06-11, leads 0..7, anti-leakage par issue_date.
  **Append quotidien par le CI** (fenêtre API 92 j → l'accumulation est la seule voie vers un historique long).
- **Série des paliers** : `data/research/signal_tiers.parquet` (2 971 jours étiquetés NORMAL→EXTREME).
- Modules : `audit/single_source.py`, `research/v155_weather_revision_validation.py`,
  `research/v175_signal_tiers.py` + 12 tests neufs (tous verts).

## 4. Nouvelles découvertes

1. **PRE_SIGNAL → signal : 47 % sous 20 j (n=34), préavis médian 2 jours** ; WATCHLIST → signal : 19 %.
   Quand la prime escalade, elle escalade vite — la zone 0.75-1.0 est une rampe courte, pas un plateau.
2. **Aucun discriminant ex-ante robuste de l'escalade** (après correction d'artefact) — troisième
   triangulation du « timing non prédictible » (avec V153 AUC 0.549 et V164 HMM).
3. **Révisions météo US printemps → CBOT : rien de significatif** (rho ≤0.15, n=62) — attendu hors
   saison de stress ; le test devient informatif en juillet-août.

## 5-6. Résultats améliorés / encore faibles

- Améliorés : cohérence live (7/7 PASS), infrastructure météo révisions opérationnelle de bout en bout.
- Faibles : START timing (confirmé difficile, 3 angles) ; météo-révisions (n insuffisant) ; z officiel
  toujours proxy_implied (9 j officiels, jalon 10 j imminent, 40 j pour V144).

## 7-8. Hypothèses rejetées / renforcées

- Rejetées : « la pente du z discrimine les pré-signaux qui escaladent » (artefact gap-jump) ;
  « les révisions météo de printemps portent déjà un signal CBOT ».
- Renforcées : « le départ de compression est réel mais non prédictible ex-ante » (V153+V164+V175) ;
  « la valeur de l'indicateur est dans l'état présent + monitoring, pas dans le timing anticipé ».

## 9-11. Modules : indicateur / explicatifs / data-gated

- **Pour l'indicateur** : single_source audit (qualité), priors V175 comme contexte descriptif de la
  machine d'état (« PRE_SIGNAL ≈ 47 % d'escalade sous 20 j, proxy 2010-2025 »).
- **Explicatifs seulement** : V155 (en attente de n), épisodes V175 par transition.
- **Data-gated** : V144 (40 j officiels), V165-repo (courbe multi-échéances), V161-repo (FOB/fret),
  re-run V155 (été). External : envoi e-mails acquisition (utilisateur).

## 12. Priorités suivantes

1. Laisser tourner le CI (head désormais commité ; archive météo s'épaissit seule).
2. Jalon 10 j officiels (imminent) puis 40 j → V144 biais proxy↔officiel + z officiel rolling.
3. COMEXT prix unitaires + Baltic (gratuits) → parité d'import V161-repo.
4. Re-run V155 quand l'archive couvre juillet-août 2026 (ou n≥150).
5. Envoi des e-mails d'acquisition (action utilisateur, tout est prêt).

## Session 2 (même jour) — exécution intégrale des tickets restants

- **V174 FX-BCE (GO)** : taux de référence BCE collecté (SDMX gratuit, archive committée) ; publié
  14:15 CET = connu avant le DSP 18:30 CET → règle FX horodatée sans fuite. Écart vs la règle yfinance
  actuelle : max 0.19 €/t (PASS, borné) ; audit quotidien branché.
- **V173 grille de coûts (descriptif)** : sur les 42 trades réels, coût de mort global **5 €/t/jambe**
  (slippage 0.5). L'edge survit à 8 €/t en EXTREME (brut 29.9 €/t), en été jul_aug (20.4) et en CBOT
  above_trend (20.4) ; il meurt à 1-3 €/t en apr_jun, MODERATE et below_trend. Triangule V167 (été) et
  V10-E (uptrend) sans toucher la baseline.
- **V161 parité d'import (NO_GO honnête)** : prix unitaires COMEXT collectés (366 mois, 2015→2026-02,
  UA/BR/extra-UE, lag publication 60 j). **corr(basis, parité d'import) = 0.089** ; le résidu
  basis−parité ne mean-reverte pas mieux que basis_z (20.4 vs 19.5 j). **La prime EMA n'est pas un coût
  d'import : 3e confirmation de la prime LOCALE** (après V16 macro et V41 substitution).
- **V144 débloqué côté données** : Barchart répond toujours → quote proxy quotidienne du même contrat
  que le front officiel (1re paire 06-10 : proxy 216.5 = officiel 216.5). Le modèle de biais démarre à
  ~40 paires (fin juillet 2026).
- **V141/V142** : machinerie de validation forward courbe/MATIF branchée au daily, gate honnête 40 jours
  FINAL (actuel : ACCUMULATING_2_DAYS) — mûrit automatiquement.
- Restent ouverts : V165 (courbe multi-échéances, data-gated), V166/V168/V169/V170 (P2/P3), re-run V155
  (été), envoi e-mails V158 (utilisateur).

## 13. Statut final

**INDICATOR_ANALYTIC** (inchangé) : l'indicateur est analytique et auditable, PAS paper-trading-ready
(checkpoint V135/V148 maintenu : edge réel/spécifique mais petit après multiplicité, z proxy_implied,
forward 9 j). Statut global : **RESEARCH_ONLY_NOT_TRADING**. Baseline figée, holdout intouché, aucun
artefact historique supprimé.
