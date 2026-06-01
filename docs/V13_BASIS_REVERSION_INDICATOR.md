# V13 — Indicateur de mean-reversion du basis

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v13_basis_reversion_indicator.py` · runner `run_v13.py` · tests (6 PASS)
**Artefacts** : `artefacts/v13/` (dynamic_exits, short_rule_strict, conformal_recalibration, basis_change_sign_models, long_short_separated, premium_journal.parquet)
**Données** : hors holdout 2024. Holdout verrouillé, jamais touché.

Suite V12, disciplinée et ciblée sur le basis. Thèse confirmée : la prime EMA/CBOT est une mean-reversion
du basis, surtout côté **compression** (basis haut → short premium). V13 affine l'exécution : sortie,
robustesse stricte de la règle, abstention conforme, signe, séparation long/short.

---

## V13-02 — Sorties dynamiques : H40 est dominé

Entrées short basis-haut (basis_z > 1), 42 trades non-overlap. Comparaison des règles de sortie :

| Sortie | PnL moyen €/t | hit | détention méd. (j) | profit/jour | net coût 3 |
|---|---:|---:|---:|---:|---:|
| H40 fixe | 10.9 | 0.74 | 40 | 0.255 | +205 |
| H50 | 8.1 | 0.69 | 50 | 0.157 | +89 |
| H60 | 7.9 | 0.76 | 60 | 0.128 | +79 |
| **z → 0.5** | 12.6 | **0.88** | **22.5** | **0.380** | +275 |
| **z → 0** | **15.9** | 0.86 | 39 | 0.268 | **+417** |
| z → 0, max 90j | 14.2 | 0.86 | 39 | 0.302 | +346 |
| z → 0, max 120j | 15.8 | 0.86 | 39 | 0.296 | +412 |
| stop-loss −10 | 2.2 | 0.45 | 16.5 | 0.067 | −161 |
| stop-loss −15 | 8.4 | 0.69 | 29.5 | 0.190 | +99 |
| stop-loss −20 | 12.7 | 0.81 | 36.5 | 0.245 | +282 |

**Découvertes** :
1. **H40 fixe est dominé** par les sorties au niveau sur presque toutes les métriques.
2. **z → 0.5 maximise le profit par jour** (0.380, hit 0.88, détention médiane 22.5j) → meilleure efficacité capital.
3. **z → 0 maximise le PnL total** (+417 net coût 3) ; **z → 0 plafonnée à 90j** est le meilleur compromis
   risque/rendement (+346, hit 0.86, plafonne les trades censurés).
4. **Les stop-loss serrés détruisent l'edge** : SL −10 → hit 0.45 (le bruit déclenche le stop ; MAE p90 ≈
   −18 à −22 €/t). Si stop-loss, **−20 minimum**.

Recommandation : sortie **z → 0.5** (efficacité) ou **z → 0 plafonnée 90j** (rendement), pas H40 fixe.

## V13-03 — Short basis-haut : la règle la plus robuste de l'étude

Règle `short si basis_z > 1`, sortie z → 0 (référence), 42 trades.

**Leave-one-crisis-out** (test de robustesse clé) :

| Exclusion | n | hit | net coût 5 €/t |
|---|---:|---:|---:|
| sans 2020 | 36 | 0.86 | +227 |
| sans 2021 | 40 | 0.85 | +220 |
| sans 2022 | 38 | 0.84 | +166 |
| **sans TOUTES les crises 2020-2022** | **30** | **0.83** | **+115** |

**Découverte majeure** : la règle short basis-haut **survit à un coût de 5 €/t/leg même en excluant toutes
les années de crise** (+115 €/t sur 30 trades hors-crise). C'est **le premier résultat de toute l'étude qui
survit au coût réaliste de 5 €/t avec un échantillon crédible** — et ce n'est **pas** un artefact de crise.
Verdict `SHORT_RULE_ROBUST`. Sortie z → 0 (net coût 5 +249) écrase H40 (+37).

**Réserves honnêtes** : trades **clusterisés** (seulement 3 années avec ≥5 trades → LOYO annuelle limitée),
règle sélectionnée a posteriori (V11-05/V12-B), et la sortie z → 0 est partiellement mécanique/optimiste.
À confirmer sur données EMA officielles avant tout claim.

## V13-01 — Abstention conforme recalibrée

Régression basis_change_h40 + intervalle conforme, abstention si l'intervalle exclut 0 :

| α | couverture (cible) | DA tous | DA conforme | n conforme |
|---|---:|---:|---:|---:|
| 0.10 | 0.829 (0.90) | 0.625 | **0.875** | 56 |
| 0.15 | 0.773 (0.85) | 0.625 | 0.867 | 90 |
| 0.20 | 0.713 (0.80) | 0.625 | 0.844 | 135 |

**Découverte** : l'abstention conforme est **robuste sur tous les α** (DA 0.84-0.88 vs 0.625 sans
abstention). **α = 0.10 est optimal** : meilleure DA (0.875) et couverture la plus proche de la cible
(0.829 vs 0.90). La sous-couverture résiduelle reflète la dérive temporelle (limite connue). Le combo
conforme × short basis-haut est trop rare (n ≤ 3) pour conclure. À intégrer dans l'indicateur (V14).

## V13-05 — Signe du basis_change : la simplicité gagne encore

| Modèle | AUC | balanced acc |
|---|---:|---:|
| **linéaire 2 vars (basis_z + month_cos)** | **0.685** | 0.599 |
| linéaire 4 vars | 0.666 | 0.609 |
| HistGB monotone 2 vars | 0.655 | 0.624 |
| avec basis_z² + interaction | 0.646 | 0.595 |
| HistGB monotone + interaction | 0.606 | 0.582 |
| isotonic sur basis_z seul | 0.458 | 0.477 |

**Découverte** : ajouter des **non-linéarités (z², interactions, HistGB monotone) DÉGRADE l'AUC**. Le
**linéaire 2 variables reste le meilleur** (0.685). C'est la troisième confirmation indépendante de la thèse
de simplicité (V10-F, V11-01, V13-05) : le signe du mouvement de prime est un phénomène **linéaire en
basis_z + saison**. Pas d'usine à gaz.

## V13-06 — Long/short séparés : asymétrie décisive

| Modèle | AUC | base rate |
|---|---:|---:|
| **Compression (basis haut → short)** | **0.656** | — |
| Rebond (basis bas → long) | 0.516 | — |

**Découverte** : le modèle de **compression (basis haut) est nettement prédictible (AUC 0.656)**, le modèle
de **rebond (basis bas) ne l'est presque pas (0.516 ≈ pile/face)**. L'asymétrie identifiée en V12 est
**confirmée et quantifiée**. Conséquence pour l'indicateur : **deux modèles distincts**, et le côté long
doit afficher une confiance bien plus basse (voire s'abstenir par défaut).

## V13-07 — Journal append-only opérationnel

`append_premium_journal` écrit le journal sans jamais réécrire l'existant (idempotent : un 2ᵉ appel ajoute
0 ligne). `data/.../premium_journal.parquet` prêt pour un cron quotidien (V14).

---

## Synthèse V13

| Question | Réponse V13 |
|---|---|
| Quand sortir ? | **z → 0.5** (efficacité) ou **z → 0 plafonné 90j** (rendement). Pas H40. SL ≥ −20 si stop. |
| La règle short tient-elle hors crise ? | **OUI** — +115 €/t net coût 5 hors 2020-2022. Robuste (réserve : clustering). |
| Meilleure abstention ? | Conforme **α = 0.10** (DA 0.875). |
| Non-linéarité utile ? | **Non** — linéaire 2 vars reste le meilleur (AUC 0.685). |
| Long ou short ? | **Short** (compression AUC 0.656) ≫ long (rebond 0.516). |

## Thèse mise à jour

> Le prix du maïs européen Euronext se comprend comme un prix mondial CBOT converti plus une prime
> européenne (basis). Cette prime suit une **mean-reversion linéaire en basis_z modulée par la saison**, et
> sa branche prédictible est la **compression d'un basis élevé**. La règle short basis-haut, sortie au
> niveau, survit aux coûts réalistes hors crise — premier résultat de l'étude à le faire — mais reste
> exploratoire (données proxy, clustering, sortie optimiste).

## Limites et suite V14

- Données EMA proxy → acquisition officielle = déblocage principal.
- Trades short clusterisés → forward réel (journal) requis pour un vrai track record.
- exit z → 0 optimiste → valider avec drawdown intermédiaire complet et coûts de portage.
- **V14** : indicateur **short-only** avec abstention conforme α=0.10 + sortie z→0(max 90j) + cost-aware,
  brancher le journal en cron, modèle de durée (survival) du temps de reversion, acquisition EMA officiel.

---

*V13 — 2026-05-31. On sait quand sortir, quel côté tient (short), comment s'abstenir, et que le linéaire*
*suffit. Première règle survivant à coût 5 hors crise. Recherche honnête, statut research-only maintenu.*
