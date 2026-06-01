# V18-LIT — Résultats de la réplication de littérature

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v18_literature_replication.py` · runner `run_v18_lit.py` · tests (4 PASS)
**Artefacts** : `artefacts/v18/` (storage, basis_convergence, event_study_wasde, cot, weather, commodity, options, replication_summary)
**Docs liés** : `LITERATURE_REVIEW_MAIS_CBOT_EURONEXT.md`, `LITERATURE_TO_EXPERIMENTS_MATRIX.md`.

On a répliqué les grandes familles de littérature (théorie du stockage, convergence, event studies, COT,
météo, inter-commodités, options) et testé chacune contre la baseline `basis_z + month_cos` pour prédire la
**compression du basis** (`basis_change_h40 < 0`), en OOF strict. Règle : on n'intègre une famille que si
`delta AUC > +0.02` robuste.

---

## Matrice des verdicts

Baseline (basis_z + month_cos) AUC de compression = **0.6845**.

| Famille | cols ajoutées | AUC augmentée | delta AUC | Verdict |
|---|---|---:|---:|---|
| **Météo / crop stress** | heat38c, rain_deficit, GDD, drought | **0.7005** | **+0.016** | **WATCHLIST** |
| Convergence (économétrie) | — | — | — | KEEP_AS_EXPLANATION |
| Théorie du stockage (courbe) | slope, contango, roll yield, OI | 0.292 | −0.393 | NO_GO (données rares) |
| WASDE event study | surprises stocks/prod/exports | 0.667 | −0.018 | NO_GO |
| COT positioning | mm_net/long/short pct | 0.600 | −0.084 | NO_GO |
| Inter-commodités | corn/soy, /wheat, /oil, /gas | 0.583 | −0.101 | NO_GO |
| Options / volatilité implicite | — | — | — | DATA_BLOCKED |

**Aucune famille n'atteint `ADD_TO_INDICATOR`.** L'indicateur reste **basis_z + saison**.

---

## Lecture famille par famille

### Météo / crop stress — `WATCHLIST` (seul gain positif)
Ajouter le stress physique US (chaleur 38°C, déficit de pluie 14j, GDD cumulés, drought) fait passer l'AUC
de compression de 0.6845 à **0.7005** (+0.016). Économiquement cohérent avec la **théorie du stockage** : le
stress de rendement crée une tension physique qui peut **justifier** un basis élevé (donc moins compressible).
Gain réel mais sous le seuil +0.02 → **WATCHLIST**, à approfondir (météo comme *warning « basis justifié »*
plutôt que comme prédicteur direct).

### Convergence (économétrie) — `KEEP_AS_EXPLANATION`
Demi-vie de mean-reversion du basis_z :
- **globale 17.3 j** (cohérent avec V10) ;
- **basis modéré (|z|≤1.5) : 8.5 j** (reversion rapide) ;
- **basis extrême (|z|>1.5) : 13.2 j** (reversion plus lente) ;
- régime vol : ~13-14 j (peu sensible à la vol).
**Implication** : le basis extrême revient **plus lentement** → justifie un **plafond de détention plus long
pour les entrées extrêmes** (z>2), cohérent avec le risque de censure observé en V15. Pas un nouveau signal,
mais une calibration de sortie.

### WASDE & COT — `NO_GO` (confirme que la prime est locale)
Les surprises WASDE (−0.018) et le positionnement COT (−0.084) **n'améliorent pas** la prédiction de la
compression de la prime EU. C'est la **confirmation par réplication de la conclusion V16** : les fondamentaux
et le positionnement **US** pilotent le **CBOT**, pas la **prime européenne** (locale). Ces variables restent
utiles pour le contexte CBOT, pas pour le signal de prime.

### Théorie du stockage (courbe) & inter-commodités — `NO_GO`
Courbe EMA : données trop rares (~332 obs) → l'augmentation détruit l'échantillon OOF (NO_GO **de données**,
pas de fond). Inter-commodités : ajoutent du bruit (−0.10). Le ratio corn/soy etc. ne renseigne pas la prime
EU spécifiquement.

### Options / IV — `DATA_BLOCKED`
Pas de volatilité implicite CBOT corn dans le dataset (les `y_skew_*` sont des cibles, pas des inputs).

---

## Conclusion V18-LIT

1. **Notre règle simple résiste à la confrontation à la littérature.** Aucune famille connue (stockage,
   WASDE, COT, inter-commodités) ne bat `basis_z + saison` pour prédire la compression. La parcimonie est
   confirmée une 4ᵉ fois (après V10-F, V11-01, V13-05).
2. **La météo est la seule piste à creuser** (théorie du stockage appliquée au stress physique) — WATCHLIST.
3. **La prime EU est locale** : réplication des event studies US (WASDE/COT) → pas d'apport, comme V16.
4. **L'économétrie de convergence** calibre les sorties : plafond plus long pour les basis extrêmes (13j vs
   8.5j de demi-vie).
5. Le mécanisme (théorie du stockage / basis trading / convergence) est **connu** ; notre application EMA/CBOT
   et l'absence d'apport des données US **renforcent** la spécificité locale de la prime.

## Décisions d'intégration (aucune modif indicateur sans ADD robuste)

- `ADD_TO_INDICATOR` : **aucun**.
- `WATCHLIST` : météo → V18-WEATHER deep-dive (warning « basis justifié par stress »).
- `KEEP_AS_EXPLANATION` : convergence (calibration sortie extrême), lead-lag, régimes.
- `NO_GO` : WASDE, COT, inter-commodités, courbe (données), ML (déjà établi).
- `DATA_BLOCKED` : options/IV.
- `WAITING_DATA` : EMA officiel, courbe multi-échéances, physiques EU (MARS/FranceAgriMer/COMEXT/Ukraine/TTF).

## Suite

- **V18-WEATHER-DEEP** : approfondir la météo comme warning « basis justifié / non-compressible » (éviter de
  shorter une prime soutenue par un vrai stress de rendement) — tester sur les trades perdants/censurés.
- **V18-DATA** (`WAITING_DATA`) : EMA officiel + courbe multi-échéances → re-tester théorie du stockage
  proprement (le seul NO_GO qui est *de données*, pas de fond).
- L'indicateur V17 reste **inchangé** : basis_z + saison + sortie z→0/0.5 + warnings.

---

*V18-LIT — 2026-05-31. La littérature confirme : la règle simple basis_z + saison n'est battue par aucune*
*famille connue. Seule la météo (théorie du stockage) est à surveiller. La prime reste locale. Research-only.*
