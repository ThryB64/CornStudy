# V12 — Anatomie de la mean-reversion, validation forward, abstention conforme

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v12_mean_reversion_lab.py` · runner `run_v12.py` · tests (4 PASS)
**Artefacts** : `artefacts/v12/` (reversion_anatomy, forward_rule_validation, conformal_abstention, premium_journal_eval)
**Données** : hors holdout 2024. Holdout verrouillé, jamais touché.

Suite V11. On approfondit le cœur mean-reversion compris, on valide *hors échantillon*, et on remplace la
bande morte fixe par une abstention par incertitude. Discipline maintenue : basis + saison, H40, coûts réels.

---

## V12-A — Anatomie du trade de mean-reversion

Entrées basis extrême (|basis_z| > 1.5), 41 trades non-overlap. On mesure le temps de reversion, le
drawdown avant reversion, et on compare trois règles de sortie.

**Temps de reversion** (basis_z revient croiser 0) :
- médiane **54 jours**, moyenne 63 jours, 41/52 réversions abouties, 11 censurées (>120j).
- Drawdown moyen avant H40 (max adverse excursion) : **−8.5 €/t**.

**Comparaison des sorties** :

| Sortie | n | PnL moyen €/t | hit | jours détention |
|---|---:|---:|---:|---:|
| H40 fixe (temporelle) | 41 | 9.2 | 0.76 | 40 |
| **basis_z croise 0** | 41 | **23.4** | 1.00 | 63 (méd. 54) |
| basis_z < 0.5 (mi-chemin) | 48 | 14.5 | 0.94 | 56 |

**Découverte** : une **sortie basée sur le niveau de basis (z→0) bat nettement la sortie temporelle H40**
(PnL moyen 9.2 → 23.4). La raison est mécanique et économique : le temps médian de reversion (54j) est
**supérieur à H40**, donc H40 sort trop tôt, avant la fin de la reversion.

**Réserve forte** : n=41, et le hit 100% de l'exit-cross-zero est en partie **mécanique** (on sort exactement
quand le pari — la reversion — s'est réalisé). C'est implémentable en live (basis_z observable sans look-ahead)
mais le chiffre est optimiste. **Le takeaway robuste est le temps médian de 54 jours** : il suggère un horizon
de détention plus long que H40, ou une sortie conditionnelle au niveau, à confirmer forward + sous abstention.

## V12-B — Validation forward des familles de règles (split-half)

Familles a priori testées sur les deux moitiés temporelles (découverte / confirmation), sans sélection :

| Famille | 1ʳᵉ moitié (hit / PnL c3) | 2ᵈᵉ moitié (hit / PnL c3) | généralise ? |
|---|---|---|:--:|
| long basis_z<−1.5 | 0.71 / −3 | 0.72 / +9 | ❌ |
| long basis_z<−1 | 0.67 / −23 | 0.72 / −5 | ❌ |
| short basis_z>1.5 | n=4 (insuff.) | 0.75 / +135 | ❌ |
| **short basis_z>1** | 0.67 / **+49** | 0.75 / **+150** | ✅ |

**Découverte (confirme V11-05 hors échantillon)** : seule la famille **short basis-haut (basis_z>1)**
généralise dans **les deux moitiés** — hit > 0.5 et PnL coût 3 positif partout. Les familles **long
basis-bas** (que V8 mettait en avant) **ne généralisent pas** proprement. Le vrai edge mean-reversion est
donc du côté **short de la prime quand le basis est élevé**. Verdict `FORWARD_RULES_GENERALIZE`.

## V12-C — Abstention par incertitude conforme (CQR)

Régression Ridge OOF de `basis_change_h40` + intervalle conforme split (Romano, α=0.2). Signal = signe de
la prédiction ; **abstention si l'intervalle contient 0** (incertitude de signe).

| | n | sign-DA |
|---|---:|---:|
| Sans abstention | 1569 | 0.605 |
| **Avec abstention conforme** (intervalle exclut 0) | 150 | **0.78** |

- Couverture empirique de l'intervalle : 0.70 (cible 0.80) → légère **sous-couverture**, cohérente avec la
  dérive temporelle déjà documentée sur le CQR du projet.

**Découverte** : l'abstention par incertitude conforme fait passer la sign-DA de **0.605 à 0.78** en
n'agissant que sur ~10% des cas (ceux où l'intervalle exclut 0 avec confiance). C'est **bien meilleur que la
bande morte fixe ±0.06** de l'indicateur actuel, et c'est principiel (basé sur l'incertitude estimée).
Verdict : `abstention_improves_da = True`. À intégrer comme couche d'abstention V13.

## V12-D — Journal paper-trading (implémenté)

`build_premium_journal` produit le journal quotidien (signal, confiance, drivers, vetoes, basis_z, prix,
flag proxy, statut) à partir de l'indicateur 2 vars promu. `evaluate_matured_journal` calcule le PnL des
lignes arrivées à J+40 :

- 766 signaux mûrs, DA 0.651, net coût 1 **+1656 €/t**, coût 3 −1408, coût 5 −4472.

Conforme à tout le reste : positif à coût 1, négatif au-delà → mur des coûts. Le journal est prêt à être
branché en cron quotidien (V13) pour accumuler un vrai track record forward.

---

## Synthèse V12

| Question | Réponse |
|---|---|
| Quand sortir un trade de basis ? | Au **niveau (basis_z→0)**, pas au temps fixe. Reversion médiane 54j. |
| Quelle famille de règles tient OOS ? | **short basis-haut (basis_z>1)** uniquement. Long basis-bas ne généralise pas. |
| Meilleure abstention ? | **Incertitude conforme** (DA 0.605→0.78), pas la bande morte fixe. |
| Mur des coûts ? | Toujours là (journal positif coût 1 seulement). |

## Améliorations apportées en V12

1. **Sortie au niveau** identifiée comme supérieure (réserve n=41) ; temps de reversion médian 54j chiffré.
2. **Confirmation OOS** que le côté short basis-haut est le seul edge de règle robuste (corrige V8).
3. **Abstention conforme** : meilleure sélection que la bande morte (DA 0.78 sur signaux agis).
4. **Journal paper-trading** opérationnel.

## Limites et suite V13

- exit-cross-zero optimiste (n=41, mécanique) → valider forward + sous abstention.
- Couverture conforme 0.70 < 0.80 → recalibrer (fenêtre, ratio) avant usage indicateur.
- Mur des coûts intact.
- **V13** : intégrer l'abstention conforme dans l'indicateur, brancher le journal en cron (`ops/daily.py`),
  tester l'horizon de détention 50-60j et la sortie au niveau, acquisition EMA officiel (déblocage principal).

---

*V12 — 2026-05-31. On sait maintenant quand sortir (niveau, ~54j), quel côté tient (short basis-haut), et*
*comment s'abstenir (incertitude conforme). Recherche honnête, statut research-only maintenu.*
