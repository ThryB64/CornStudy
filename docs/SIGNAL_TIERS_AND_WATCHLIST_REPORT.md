# SIGNAL TIERS & WATCHLIST — V175

_2026-06-11 · RESEARCH_ONLY_NOT_TRADING · fenêtre proxy 2010-2025 (z 52w, proxy_implied)_

**La baseline ne change pas** : z>1 reste le seul signal ; 1.5/2.0 restent STRONG/EXTREME ; objectifs
z→0.5 / z→0 inchangés. V175 ajoute des **catégories d'étude** sous le seuil pour quantifier les phases
pré-signal : NORMAL (|z|<0.5), WATCHLIST (0.5≤z<0.75), PRE_SIGNAL (0.75≤z<1.0), BELOW_NORMAL (z≤−0.5).

Série quotidienne : `data/research/signal_tiers.parquet` (2 971 jours). Répartition : NORMAL 998,
BELOW_NORMAL 933, BASELINE 264, WATCHLIST 217, STRONG 208, EXTREME 185, PRE_SIGNAL 166.

## Question 1 — Les pré-signaux deviennent-ils des signaux ?

Épisodes d'upcross (entrée dans la bande par le bas, entry_z **strictement < cible**, lockout 10 j,
horizon 20 j, fizzle = retombe sous 0.5) :

| Transition | n | Escalade | Retombe | Délai médian si escalade |
|---|---|---|---|---|
| PRE_SIGNAL → z≥1 | 34 | **47 %** | 53 % | **2 j** |
| WATCHLIST → z≥1 | 57 | **19 %** | 81 % | 2 j |
| WATCHLIST → PRE_SIGNAL | 46 | 28 % | 72 % | 1 j |

Lecture : un pré-signal a ~1 chance sur 2 de devenir un signal sous 20 jours ; une watchlist ~1 sur 5.
**Le préavis utile est court (médiane 2 jours)** : quand la prime escalade, elle escalade vite.

## Question 2 — Qu'est-ce qui distingue ceux qui escaladent ? (résultat négatif important)

**Artefact détecté et corrigé** : sans le filtre de bande stricte, les « gap-jumps » (z saute de 0.7 à
1.2 en un jour) se classaient en escalade à 1 jour et rendaient `z_slope_5d` faussement très
significatif (p≈0.000). Après correction :

| Variable (médiane escalade vs retombe) | PRE→1.0 | WATCH→1.0 | WATCH→0.75 |
|---|---|---|---|
| z_slope_5d | 0.60 vs 0.48, p=0.33 | 0.64 vs 0.33, **p=0.02** (n=11) | p=0.34 |
| cbot_mom_20d | p=0.25 | p=0.19 | 0.069 vs −0.007, **p=0.02** (n=13) |
| ema_rel_strength_20d | p=0.36 | p=0.62 | p=0.31 |

Aucun discriminant robuste : les deux p<0.05 reposent sur n≤13 escaladeurs et ne sont pas cohérents
entre transitions (≈6 tests×3 transitions, attendu ~1 faux positif). **Verdict : on ne sait pas
prédire ex-ante quel pré-signal escaladera — cohérent avec V153 (START AUC 0.549) et V164 (le départ
est réel mais non prédictible).**

## Ce que V175 apporte quand même

1. **Priors quantifiés** pour la machine d'état : un état PRE_SIGNAL peut afficher « ~47 % d'escalade
   sous 20 j (proxy 2010-2025) » comme contexte descriptif — pas comme règle.
2. **Plus d'observations d'étude** : 166 jours PRE_SIGNAL + 217 WATCHLIST étiquetés pour les analyses
   futures (event studies, saisonnalité) sans toucher au signal principal.
3. **Discipline anti-artefact** : le filtre gap-jump est désormais documenté et testé
   (`test_gap_jump_entries_excluded`).

## Limites

Fenêtre proxy (le z officiel n'a que 9 jours) ; n petit par transition ; aucun test multi-variable
(volontaire : pas de modèle sur 34 épisodes). À re-runner sur z officiel rolling quand 40+ jours
officiels seront accumulés. Artefacts : `artefacts/v175/` (résultats + épisodes par transition).
