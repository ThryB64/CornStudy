# V16 — Explication économique du basis EMA/CBOT

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v16_basis_explanation.py` · runner `run_v16.py` · tests (3 PASS)
**Artefacts** : `artefacts/v16/` (basis_fair_value, curve_structure, basis_drivers)
**Données** : hors holdout 2024. Holdout verrouillé, jamais touché.

Suite V15. Question centrale : **peut-on expliquer économiquement pourquoi le basis est haut et quand il se
compresse ?** On teste des explications (fair value, structure de courbe, drivers), sans modèle opaque.

---

## V16-01 — Fair value du basis : ÉCHEC honnête, basis_z reste le meilleur

On construit `basis_fair` (OOF Ridge) = part « normale » du basis expliquée par saison + FX + énergie,
puis `mispricing = basis − basis_fair`, et on compare mispricing vs basis_z comme prédicteur de la
compression (`basis_change_h40 < 0`).

| | basis_z | mispricing |
|---|---:|---:|
| AUC compression | **0.670** | 0.636 |
| Règle short : n trades | 42 | 20 |
| hit rate | **0.857** | 0.75 |
| net coût 5 €/t | **+193** | +16 |

- **Fair value R² OOF = −0.25 (négatif)** : les fondamentaux macro **n'expliquent pas le basis** hors
  échantillon (pire que la moyenne).

**Découverte** : `mispricing` **ne bat pas** `basis_z` (`BASIS_Z_REMAINS_BEST`). Comme les fondamentaux
n'expliquent pas le basis, le « mispricing » n'est pas plus pur que la déviation statistique basis_z. La
**mean-reversion statistique de basis_z reste le meilleur signal**.

## V16-02 — Structure de courbe : inconcluant (données trop rares)

Hypothèse : basis haut + contango (surprix) se compresse mieux que basis haut + backwardation (tension durable).

- **Vraies features de courbe EMA** (contango/backwardation) : disponibles sur **332 obs seulement** ; en
  basis-haut, n=4 (contango) / n=0 (backwardation) → **insuffisant pour conclure**.
- **Proxy de tendance CBOT** (`curve_backwardation_proxy` = prix vs SMA252, *pas* une courbe pure) :
  la reversion short est plus forte quand le CBOT est **au-dessus de sa tendance** (n=19, hit 1.0, +298
  net coût 3) que sous sa tendance (n=29, hit 0.76, +113). Exploratoire, petit échantillon.

**Verdict** : `CURVE_STRUCTURE_EXPLORATORY`. La vraie structure de courbe EMA (front/next, roll yield)
nécessite la donnée Euronext officielle multi-échéances — limite de données, pas une conclusion négative.

## V16-03 — Drivers du basis : le basis est une prime locale, pas un spread macro

Régression OOF du basis sur les fondamentaux disponibles :

- **R² OOF = −0.25 (négatif)** : saison + FX + énergie **n'expliquent pas** le niveau du basis hors échantillon.
- Coefficients in-sample (descriptifs) les plus forts : `usd_index_close` (+8.3), `corn_gas_ratio` (−7.3),
  `eurusd` (+6.7), `gas_close` (+2.0) — associations réelles mais **qui ne généralisent pas**.

**Découverte structurante** : la prime européenne (basis) est une **anomalie locale idiosyncratique**, pas
un spread piloté par la macro mondiale (FX/énergie/saison). C'est l'explication profonde de toute la lignée :
- *pourquoi* la mean-reversion **statistique** de basis_z fonctionne (le basis revient vers sa propre moyenne,
  pas vers une « juste valeur » macro) ;
- *pourquoi* les **données EU spécifiques** sont le vrai levier pour l'expliquer fondamentalement.

Données manquantes (non jointes au dataset courant) → `WAITING_DATA` : EC MARS (rendement EU),
FranceAgriMer (bilans), Eurostat COMEXT (imports/exports), Ukraine exports / FOB, TTF gas EU, fret / BDI,
météo EU pondérée.

---

## Synthèse V16

| Question | Réponse |
|---|---|
| La macro (FX/énergie/saison) explique-t-elle le basis ? | **Non** (R² OOF −0.25). |
| Le mispricing fair-value bat-il basis_z ? | **Non** — basis_z reste le meilleur (AUC 0.67, +193 coût 5). |
| La structure de courbe départage-t-elle les compressions ? | **Indéterminé** — données EMA multi-échéances trop rares. |
| Qu'est-ce que le basis, alors ? | Une **prime locale idiosyncratique** à mean-reversion **statistique**. |

## Implication pour la lignée

V16 **renforce** la stratégie V13-V15 plutôt que de la remplacer : puisque le basis n'est pas un spread
macro, la bonne approche est bien la **mean-reversion statistique de basis_z** (short basis-haut, sortie
z→0, stop −20), et non un modèle fondamental. La complexité fondamentale a été testée et **rejetée
honnêtement**. Le seul vrai gain fondamental viendrait de **données EU spécifiques** (le déblocage n°1, déjà
identifié).

## Limites et suite V17

- Fundamentaux EU/Ukraine absents → `WAITING_DATA` (déblocage n°1, inchangé).
- Vraies features de courbe EMA trop rares → nécessitent la donnée Euronext officielle multi-échéances.
- **V17** (quand données disponibles) : EMA officiel + EC MARS + FranceAgriMer ; re-tester fair value et
  structure de courbe avec ces données ; sinon, accumuler le journal forward V14 et consolider le rapport
  research final de l'indicateur de prime.

---

*V16 — 2026-05-31. La macro n'explique pas le basis : c'est une prime locale à reversion statistique. La*
*fair-value fondamentale est rejetée honnêtement ; basis_z reste le cœur. Statut research-only maintenu.*
