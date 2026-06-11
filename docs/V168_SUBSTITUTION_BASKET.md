# V168 — Panier de substitution élargi (T-SUBBASKET, R8)

**Verdict : `NO_GO_WHEAT_SUFFICIENT` — le ratio blé/maïs SEUL bat le panier élargi sur les 3 tests.**
Résultat négatif conservé. Baseline z>1 intouchée. RESEARCH_ONLY_NOT_TRADING.

## Hypothèse testée (R8)

La prime EMA serait co-déterminée par tout le complexe céréales fourragères (blé, avoine, soja),
pas seulement le blé. Un panier équipondéré de ratios CBOT (blé/maïs + avoine/maïs + soja/maïs,
z expandant identique à V38, poids figés ex-ante, aucune optimisation) devrait battre
`wheat_corn_z` seul.

## Protocole (pré-déclaré avant lecture)

3 tests à périmètre identique contre l'incumbent `wheat_corn_z` (V36/V41) ; GO si le panier gagne
≥2 tests avec marge (corr +0.03, AUC +0.02, rho +0.05) ; NO_GO si 0 ; WATCHLIST sinon.
Holdout 2024 exclu. Module `src/mais/research/v168_substitution_basket.py`,
artefact `artefacts/v168/v168_substitution_basket.json`, 5 tests verts.

## Résultats (5 820 jours, 42 épisodes V82 dont 7 ADVERSE)

| Test | Panier | Blé seul | Gagnant |
|---|---|---|---|
| A. corr(basis, z) niveau | 0.539 (h1 0.553 / h2 0.462) | **0.587** (h1 0.524 / h2 0.588, plus stable) | Blé |
| B. AUC ADVERSE à l'entrée | 0.665 | 0.653 (recalculé = 0.653 stocké V82 ✓) | Panier mais **sous la marge** (+0.012 < +0.02) |
| C. rho(z entrée, jours→z0.5), n=37 non censurés | −0.01 | **0.204** | Blé |

## Lecture économique

- La substitution qui soutient la prime maïs EU passe par le **blé** (fourrager/meunier), pas par
  l'avoine ni le soja : diluer le ratio blé/maïs avec d'autres ratios **dégrade** l'explication du
  niveau ET la lecture de vitesse. 4e confirmation de la leçon « empiler dilue » (V64, V13-05, VNEXT).
- Le léger gain ADVERSE du panier (+0.012) est dans le bruit à n=42 — ne pas le sur-interpréter.
- Cross-check de cohérence : l'AUC blé recalculé depuis le master = exactement la valeur stockée
  dans la librairie V82 (0.653) → la chaîne épisodes/features est intègre.

## Ce qui reste ouvert

- **MATIF EBM/EMA forward** : 9 observations au journal (V52/V126) — le vrai test « substitution
  EUROPÉENNE » rejoindra le panier à ≥150 obs (`FORWARD_ACCUMULATING`).
- **DATA_BLOCKED** : orge (aucune série gratuite), maïs Black Sea (BCD illiquide/payant).
- Ne pas rouvrir le panier CBOT sans donnée nouvelle (orge ou Black Sea réels).
