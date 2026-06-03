# Review critique des tickets VNEXT

Date : 2026-06-03. Reviewer : lead research engineer (red-team de mon propre backlog).
Objectif : pour chaque ticket — utile ? apporte vraiment ? duplication ? risque de fausser l'étude / faux
résultats ? reformuler / rejeter / fusionner ?

---

## Verdicts par ticket

### VN-A1 — Single source of truth + séparation legacy — **GARDER**
Utile et non dupliqué. Risque : tenter de *supprimer* le legacy farmer (perte d'historique). **Reformulation** :
ne rien supprimer ; isoler + bannière LEGACY + `premium_daily_head.json` autoritatif. Pas de risque de faux
résultat (étiquetage). **Priorité 1.**

### VN-A2 — Session timing PROVISIONAL/FINAL/REVISED — **GARDER (critique)**
Ne duplique PAS V122 : V122 a la *logique* de révision, A2 ajoute l'*estampillage à l'écriture* + champs de
temps. Risque : changer le passé du journal. **Garde-fou** : n'estampiller que les NOUVELLES lignes + un
backfill ponctuel non destructif des champs dérivables (effective_session_date à partir de logged_at) ;
jamais réécrire un settlement FINAL. **Priorité 1.**

### VN-A3 — Audit signe de courbe — **GARDER, léger**
Faible coût, vrai garde-fou. Aucun risque. Pourrait être fusionné avec A4 (un seul module d'audit de
couches), mais reste plus clair séparé.

### VN-A4 — quality_flag & fraîcheur — **GARDER**
Utile (faux low_liquidity). Risque : sur-corriger et masquer une vraie illiquidité. **Garde-fou** : utiliser
OI ET volume (low_liquidity seulement si OI ET volume bas), garder le flag visible.

### VN-A5 — CI / docs / restatuts — **GARDER, dégonfler**
Housekeeping. **Réalisme** : je ne peux pas exécuter une vraie CI ici ; je livre la note + le pin pyarrow
dans la doc, et j'applique les restatuts dans V134. Pas un module lourd. **EXPLANATORY_ONLY** de fait.

### VN-B1 — Réécrire narration trigger V105 — **GARDER (essentiel)**
Vérifié : chiffre CBOT pré-start −0.024 contredit « le CBOT monte ». Aucun risque, c'est une correction de
vérité. **Priorité haute.** Ne PAS toucher au verdict (NO_CLEAR_SINGLE_PRECURSOR, déjà honnête) — seulement
le texte explicatif.

### VN-B2 — Scan narration vs chiffres — **GARDER, BORNER**
Risque de sprawl (relire 100 artefacts). **Reformulation** : scan ciblé des artefacts research à
`interpretation` longue, produire une liste d'écarts, ne rien réécrire d'autre que ce qui est franchement
faux. EXPLANATORY_ONLY.

### VN-C1 — Probe Euronext historique — **GARDER**
Honnête (ne pas présumer). Attente réaliste = NO_PUBLIC_RANGE. Aucun risque.

### VN-C2 — COMEXT bulk — **GARDER, attente réaliste**
Risque : (a) time sink (fichiers lourds), (b) **faux signal de niveau confondu par la tendance** (cf. V71 :
les niveaux dérivent). **Garde-fou** : limiter à la série maïs UE, détrender en YoY (comme V71b), traiter en
mensuel shift(1). Si le bulk est inaccessible proprement → DATA_BLOCKED honnête, pas de bricolage.

### VN-C3 — Tension physique UE — **GARDER, WATCHLIST, dépend C2**
Risque identique (confond tendance). **Garde-fou** : détrend YoY, descriptif (durée/compression), pas d'AUC.
Honnête : probablement WATCHLIST (parsing MARS/FAM partiel).

### VN-C4 — Forecast revision tape (Previous-Runs) — **GARDER**
Distinct de V127 (émissions forward) et V136 (historical 1 lead) : Previous-Runs = lead-fixe multi-jours.
Risque : timeouts. **Garde-fou** : fenêtre courte, best-effort, DATA_BLOCKED propre. Anti-leakage par
construction (Δ entre runs datés).

### VN-C5 — Calendrier USDA exact — **FUSIONNER avec V137**
Ne pas créer un module concurrent : **étendre V137** avec un calendrier de dates exactes (collecteur dédié)
remplaçant l'approximation `_wasde_dates`. GO pour les dates statiques 2026 ; QuickStats live = WATCHLIST.

### VN-D1 — Hazard time-to-compression — **GARDER, RISQUE ÉLEVÉ, encadrer**
**Risque #1 de faux résultat** : produire une fausse « probabilité prédictive » overfittée, ou frôler
l'optimisation sur les mêmes données. **Garde-fous obligatoires** : panel = jours basis_z>1 (≈460 j, comme
V106), PAS les 42 trades ; walk-forward strict ; comparaison systématique à la **base rate** (V106 : 0.65) ;
Brier + calibration ; **verdict par défaut WATCHLIST** (V106 a déjà montré que le timing est dur). Si AUC ≈
base rate → l'écrire franchement. Ne jamais présenter comme un edge.

### VN-D2 — Transitions d'état — **GARDER mais CONSTRUIRE SUR V131**
Duplication partielle avec V131 (WATCH/WAIT_CONFIRMATION existent déjà). **Reformulation** : V_D2 étend la
taxonomie (EXTREME_STATIC, EARLY_RELAXATION, CBOT_CATCHUP, PHYSICAL_JUSTIFIED, ADVERSE_DRIFT) en réutilisant
les diagnostics existants ; descriptif, pas un nouveau classifieur. GO.

### VN-D3 — Discriminant bon vs ADVERSE — **GARDER, WATCHLIST**
Recoupe V82 (signature ADVERSE) et V64 (qui diluait). **Garde-fou** : se concentrer sur la séparation
post-entrée (MFE initiale, spread, CBOT_SUPPORT, révision), n petit → WATCHLIST, robustesse ex-crise exigée.
Ne pas re-tomber dans le piège V64 (empiler dilue).

### VN-D4 — Explication hiérarchique — **GARDER, EXPLANATORY_ONLY**
Utile pour défendre l'indicateur. Risque : multiple testing sur familles → fausse contribution. **Garde-fou** :
ablation walk-forward, pas de p-hacking, contribution = Δ métrique honnête. N'entre dans la décision que si
une famille améliore vraiment.

### VN-E1 — Capture du soir événements — **GARDER (levier #1 forward)**
Aucun risque de faux résultat (collecte). Risque opérationnel : scheduler. **Réalisme** : je livre le
collecteur + journal append-only + doc cron ; l'exécution réelle aux heures CET dépend d'un cron côté
utilisateur (je ne peux pas garantir l'horaire ici). PROVISIONAL/FINAL strict.

### VN-E2 — Microstructure événementielle — **GARDER, dépend E1 accumulé**
WATCHLIST tant que E1 n'a pas accumulé d'événements. Pas de risque (descriptif ex-post).

---

## Décisions de structure

- **Fusion** : VN-C5 → étend V137 (un seul chemin calendrier d'événements).
- **Construire sur l'existant** (pas dupliquer) : VN-D2 sur V131, VN-D3 sur V82/V64, VN-A2 sur V122.
- **Risque de faux résultat à encadrer strictement** : VN-D1 (hazard) — défaut WATCHLIST, base rate, walk-forward.
- **Confond-par-tendance** : VN-C2/C3 — détrend YoY obligatoire (leçon V71/V71b).
- **Bornage anti-sprawl** : VN-B2 (scan ciblé), VN-A5 (doc, pas module lourd).

## Ordre d'exécution validé

A1 → A2 → A3 → A4 → A5 → B1 → B2 → C1 → (C2 → C3) ∥ C4 ∥ C5(→V137) → E1 → D2 → D1 → D3 → D4 → E2.
Fermer A et B avant d'ouvrir C/D/E. Tout reste RESEARCH_ONLY_NOT_TRADING.
