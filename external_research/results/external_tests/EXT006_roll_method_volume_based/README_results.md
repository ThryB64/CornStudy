# EXT006 — Résultats : méthode de roll et artefacts de série continue

Date : 2026-06-12. Scripts : `external_research/experiments/external_tests/EXT006_roll_method_volume_based/{run,evaluate}_ext006.py`.

## Verdict : **IMPROVE** (artefacts réels et quantifiés ; reconstruction historique volume-based DATA_BLOCKED)

## Réponses aux questions posées

### 1. La méthode actuelle crée-t-elle des artefacts ?

**OUI, sur la jambe EMA — et ils sont gros.** Sur `ema_front_continuous_raw` (2010-2026, 69 rolls, ~4,2/an, règle implicite : roll à 15 jours de l'expiry) :

- |Δprix| moyen les jours de roll : **10,22 €/t** vs 1,54 €/t les jours normaux (**ratio 6,6**, Welch t=4.83, p<1e-6).
- p90 du saut de roll : 20,4 €/t ; maximum : 97,5 €/t.
- **27/68 rolls font changer de signe le momentum 20j** sur la série raw (12/68 sur l'adjusted).
- La série `ema_front_continuous_adjusted` (back-adjustment par différence, colonne `adjusted_price`) réduit fortement l'artefact : 3,85 €/t les jours de roll (ratio 2,5, p=0.19 non significatif).

**Échelle critique** : 10 €/t de saut de contrat est l'ordre de grandeur du PnL moyen de nos trades basis (9-30 €/t, V13-V15) et des seuils de la machine d'état. Tout calcul de basis, de retour ou de momentum fait sur la série EMA **raw** autour d'un jour de roll mélange mouvement de marché et spread calendaire.

Sur le CBOT vendeur : **AUCUN artefact détecté** dans les fenêtres de roll présumées (10 derniers jours de bourse avant les mois H,K,N,U,Z) — |logret| 1,25 % en fenêtre vs 1,29 % hors fenêtre, gaps overnight plus PETITS en fenêtre. La série vendeur est vraisemblablement déjà lissée/ajustée au roll. Pas de signal d'alerte (mais pas d'identité de contrat pour le prouver formellement).

### 2. La méthode volume-based change-t-elle les rendements ?

Le prototype causal (volume J-1, segment multi-contrats 2025-2026, 252 jours) diverge du front-par-expiry **45 % des jours** (contrat différent), avec un écart de prix moyen de **6,55 €/t** quand ils divergent, et 8 rolls déclenchés par le volume. Le front-par-expiry reste donc une partie du temps sur un contrat qui n'est plus le plus liquide. La reconstruction HISTORIQUE volume-based est impossible : l'historique 2010-2024 ne contient que le front (1,09 contrat/date) — **DATA_BLOCKED** documenté.

### 3. La différence remet-elle en question les anciens résultats ?

**Partiellement — à vérifier par un ticket projet séparé** (hors périmètre externe) :
- Si basis_z historique est calculé sur une série EMA de type front raw : ~4 sauts de ~10 €/t par an passent dans le basis, soit une contamination potentielle des z-scores les mois de roll. Les protections existantes (veto `UNCERTAIN_ROLL` V9, coût dynamique en mois de roll V13) **atténuent en aval** mais ne corrigent pas la feature en amont.
- Les résultats CBOT (V9-V17 utilisent corn_close vendeur) ne montrent pas d'artefact détectable — pas de remise en cause.

### 4. La méthode volume-based doit-elle devenir la référence ?

Pour l'HISTORIQUE : non (impossible, données front-only). Pour le FUTUR : oui en accumulation — la courbe multi-contrats collectée depuis 2025 permet de maintenir en parallèle un front volume-causal (le prototype tourne) ; dans 12-18 mois, on aura une série comparée suffisante. Pour l'historique, la recommandation est : **utiliser `adjusted_price` (ou exclure/flagger les 69 jours de roll) pour toute feature de retour/momentum EMA** dans les EXT futurs.

## Recommandations (sans toucher au modèle principal)

1. **EXT futurs** : toute feature de retour EMA utilise `adjusted_price` ou exclut les jours de roll (`roll_dates.csv` fourni, 69 dates).
2. **Ticket projet séparé proposé** : auditer quelle série alimente exactement basis_z dans le pipeline principal et si les jours de roll y sont neutralisés en amont (et non seulement vetotés en aval).
3. **Acquisition** : continuer la collecte multi-contrats (déjà en place depuis 2025) ; envisager une source contrats CBOT historiques si un EXT courbe CBOT (EXT005) l'exige.

## Fichiers produits

`continuous_current.csv` (front raw + flags roll), `continuous_volume_roll.csv` (prototype causal 2025+), `roll_dates.csv` (69 rolls : contrats, DTE, sauts), `roll_artifacts_metrics.csv`, `roll_artifacts_metrics_detailed.csv`, `roll_comparison_metrics.csv`.

## Anti-fuite

Décision de roll du prototype sur volumes J-1 mémorisés uniquement ; roll forcé à DTE≤3 (règle fixe non optimisée) ; aucun paramètre ajusté sur la série ; CSV de RollFutures non utilisés (méthode seulement).
