# Plan de validation forward — phase de consolidation

_2026-06-11 · L'exploration historique est CLOSE (sessions 1-5 : tous les tickets exécutables sont
DONE, le reste est data-gated avec déclencheurs automatiques V177). La preuve appartient
désormais au forward officiel. RESEARCH_ONLY_NOT_TRADING, baseline z>1 figée._

## 1. Ce qu'on attend des 40 jours officiels (≈ fin juillet 2026)

Le jalon 40 (V147) débloque trois choses, **toutes automatiques** :

1. **z officiel rolling** (V144 STAGE_40) : le z passe de `proxy_implied` à un z calculé sur la
   fenêtre officielle elle-même. Attendu : |z_officiel − z_proxy| < 0.3 (concordance V144).
2. **Validation des paires proxy↔officiel** (V178, seuils FIGÉS le 2026-06-11) : ~30-40 paires
   quotidiennes sur LE MÊME contrat. Verdict selon MAE prix, biais, tier agreement.
3. **Validations forward courbe/MATIF** (V141/V142, gate 40 j) : corr(spread officiel, basis),
   corr(ratio EBM/EMA, basis) sur fenêtre officielle.

Ce que 40 jours NE donnent PAS : une validation de l'edge (il faut des épisodes complets), une
distribution crédible du basis officiel (90 j+), un test météo (V155 attend l'été, gate n≥150).

## 2. Ce qu'on attend des 90 jours (≈ mi-octobre 2026)

- **V144 STAGE_90** : comparaison de DISTRIBUTION proxy vs officiel (niveaux, vol, autocorrélation
  du basis) — c'est le vrai verdict sur la transposabilité de l'historique exploratoire.
- **Premier épisode complet en officiel** : le signal actif (entré 2026-05-29, médiane attendue
  ~23-38 j) sera résolu — première fiche de trade 100 % officielle (entrée, chemin, MFE/MAE,
  sortie z0.5 ou ADVERSE).
- **V166-officiel approche son gate** (150 sessions ≈ début 2027) ; V155-été aura tourné
  (l'archive météo atteint n=150 vers août).
- Début de la **revalidation V176** : le score composite est-il monotone aussi sur l'officiel ?
  (lecture descriptive, n minuscule, aucun verdict avant 6-12 mois).

## 3. Si le proxy est VALIDÉ (V178 PROXY_VALIDATED + V144 concordance)

- L'historique 2010-2025 (Barchart exploratoire) gagne le statut de **série de travail légitime** :
  les ~42 trades historiques, les paliers V130/V173, le composite V176 se citent avec la réserve
  réduite « proxy validé sur N paires, biais B €/t ».
- Le head documente `official_proxy_status: proxy_validated_at_40d` ; le z rolling officiel
  devient la lecture primaire, le proxy reste l'historique long.
- AUCUN changement de baseline, de seuils, ni de statut (toujours pas de trading) — la validation
  réduit l'incertitude de MESURE, pas le risque de stratégie.

## 4. Si le proxy est INVALIDÉ (V178 PROXY_INVALID)

- Tout l'historique quantitatif (PnL, hit rates, paliers de coût) est requalifié
  **ORDRE-DE-GRANDEUR SEULEMENT** ; le rapport maître reçoit un bandeau en tête de §5/§7.
- Le live continue SANS interruption : le journal officiel est la seule vérité depuis 2026-05-29,
  et l'indicateur (machine d'état, tiers, monitoring) fonctionne nativement sur l'officiel.
- Le modèle de biais V144 tente une CORRECTION (si le biais est stable/affine, le proxy reste
  utilisable corrigé) ; sinon, la priorité de V182 passe à MAXIMALE (mail Euronext = seul moyen
  de reconstruire un historique officiel).
- Les conclusions QUALITATIVES survivent (mean-reversion du basis, prime locale, asymétrie
  short>long, START non prédictible) : elles reposent sur la structure, pas sur 2 €/t près.

## 5. Si le signal actif devient ADVERSE (V124 ADVERSE_LIKE : MFE < 5 €/t après 20 j, ou MAE qui s'étend)

- **On documente, on ne « gère » pas** (pas de trading) : fiche d'épisode complète (chemin, contexte
  d'entrée EXTREME z 2.06, backwardation, catalyseurs) ajoutée à la librairie V82 — ce serait le
  8e ADVERSE sur 43, précieux PARCE QUE observé en officiel.
- Vérifier la cohérence avec les signatures connues : entrée z>2 (V15-02 : censurés plus extrêmes),
  prime PHYSICALLY_JUSTIFIED + backwardation (hypothèse V166 live : compression plus lente).
  Si l'ADVERSE arrive avec courbe TENDUE, c'est un point POUR l'hypothèse courbe — le noter.
- La machine d'état passe ADVERSE_LIKE, objectif z→0.5 inchangé, stop analytique −20 €/t
  documenté ; le rapport mensuel V133 raconte l'épisode honnêtement.

## 6. Si le signal atteint z→0.5

- TARGET_Z05_HIT dans la machine d'état ; fiche d'épisode officielle complète (durée réelle vs
  horizon ~23-38 j prédit, compression €/t, chemin) — **premier cycle entier prédiction→résolution
  en données officielles**, c'est le livrable n°1 de la phase forward.
- Comparer la durée réalisée aux postérieurs V169 (médiane EXTREME 47 j [29-82]) : un point de
  calibration des intervalles crédibles.
- Après résolution : retour WATCHLIST/NORMAL, le monitoring V124 s'éteint tout seul, on attend le
  prochain signal SANS rien forcer (1.6-2.3 signaux/an attendus).

## 7. Expériences relancées SEULEMENT avec données nouvelles (gates V177, protocoles figés)

| Expérience | Gate (auto) | État 2026-06-11 |
|---|---|---|
| V166-officiel (CY→basis sur courbe officielle) | ≥150 sessions courbe | 10/150 |
| V168-MATIF (substitution EBM/EMA vs blé CBOT) | ≥150 obs journal MATIF | 9/150 |
| V155-été (révisions météo → CBOT) | ≥150 j archive (saison de stress) | 93/150 (~août) |
| V144/V178 (biais proxy↔officiel) | 40 j officiels | 10/40 (~fin juillet) |
| V165 (facteurs de structure par terme) | courbe officielle multi-échéances accumulée | avec V125 |
| Réouvertures interdites sans donnée neuve | — | panier CBOT (V168), fair-values (V16/V161/V166), timing START (V153/V164/V175), inversion saisonnière (V8) |

## 8. La routine (qui fait quoi, automatiquement)

- **Quotidien (CI)** : collecte officielle → journal sessionisé → couches → head → machine d'état →
  dashboards v4/v5 → monitoring V124 → rapport signal actif V179 → quotes proxy V144-DATA →
  gates V177 → validation V178 → audit single_source. Zéro intervention.
- **Hebdomadaire (CI, samedi)** : maintenance V181 (santé CI/head/archives/tests critiques +
  jalons) → `reports/weekly/maintenance_latest.md`.
- **Mensuel (déjà en place)** : rapport V133.
- **Humain** : envoyer les e-mails V158 (tracker `docs/EXTERNAL_DATA_FOLLOWUP.md`), lire le
  dashboard v5, décider sur devis éventuels.

_Aucune promesse de performance. Le but des 40/90 jours est de VALIDER LA MESURE, pas de
prouver un edge : l'edge ne se jugera que sur des épisodes complets accumulés (6-12 mois)._
