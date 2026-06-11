# V166 — Convenience yield ↔ bilan physique (T-CONVYIELD, R6)

**Verdict : `CHAIN_NOT_SUPPORTED` sur l'historique proxy — avec UN maillon qui tient
(bilan→courbe, imports +0.33) et un test décisif reporté à la courbe officielle.**
RESEARCH_ONLY_NOT_TRADING, baseline intouchée.

## Hypothèse (R6)

Bilan UE tendu ⇒ convenience yield (CY) local élevé ⇒ basis haut ⇒ compression quand le bilan se
détend. Chaînon économique entre la courbe (finance) et le bilan (agro) que V35 cherchait dans le
prix sans le trouver.

## Méthode

Proxy CY = `ema_roll_yield_ann` (carry front→second annualisé par vrais DTE, >0 = backwardation).
Hypothèse taux EUR constant (série absente, σ du roll yield ≈ 7.6 pp/an domine). 3 maillons,
directions pré-déclarées, aucun fit. Module `src/mais/research/v166_convenience_yield.py`,
artefact `artefacts/v166/v166_convenience_yield.json`, 5 tests verts. **Limite majeure assumée :
courbe proxy CREUSE (348 jours hors holdout, ~15 % des dates).**

## Résultats

| Maillon | Attendu | Observé | Verdict |
|---|---|---|---|
| A. CY → basis_z (n=314 j) | corr > +0.2 | **−0.02** (h1 +0.21 / h2 −0.12, signe instable) | ÉCHOUE |
| B1. Imports COMEXT (lag 60 j) → CY (n=30 mois) | rho > +0.2 | **+0.33** | TIENT |
| B2. Anomalie prod FR (lag1) → CY (n=44 mois) | rho < −0.2 | −0.16 | échoue (bon sens, sous le seuil) |
| C. CY haut → compression h20 plus lente (45 j-signal) | split médian | **DÉGÉNÉRÉ : 0/45 jours-signal en backwardation dans le proxy** | non testable |

## Lecture honnête

1. **La chaîne complète n'est PAS démontrée sur le proxy** : le CY proxy n'explique pas le niveau
   du basis_z (maillon central échoue). Cohérent avec la litanie « prime LOCALE » (V16 macro,
   V41 substitution, V161 parité) — 4e candidat fair-value qui échoue.
2. **Mais le maillon physique amont existe** : les mois à gros imports UE ont des courbes plus
   tendues (+0.33, sens et seuil pré-déclarés OK) et l'anomalie de production va dans le bon sens
   (−0.16). Le bilan physique parle à la COURBE — c'est le basis qui ne suit pas le CY proxy.
3. **Le fait C-dégénéré est une découverte en creux** : sur 2010-2022 (proxy), AUCUN jour-signal
   (z≥1) n'avait de courbe en backwardation. Or le LIVE officiel 2026 montre backwardation + z 1.87
   simultanés — soit le proxy Barchart sous-échantillonne la backwardation (fragments de courbe),
   soit le régime 2026 est qualitativement différent. **Dans les deux cas, le test décisif
   CY→basis appartient à la courbe OFFICIELLE accumulée (V125), pas au proxy.**

## Suite

- Re-run quand `ema_curve_history.parquet` (officiel, 10 j au 2026-06-11) aura ≥150 sessions —
  même artefact, mêmes directions pré-déclarées, zéro degré de liberté ajouté.
- Ne pas citer « la backwardation justifie la prime » comme résultat historique : c'est une
  HYPOTHÈSE live (state machine) en attente du forward officiel.
- DATA_BLOCKED : taux EUR court (ajouter €STR/Euribor serait propre mais secondaire), stocks UE
  mensuels physiques.
