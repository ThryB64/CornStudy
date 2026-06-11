# VECM EMA/CBOT — VERDICT CANONIQUE UNIQUE

_2026-06-11 · RESEARCH_ONLY_NOT_TRADING · règle : ce document prime sur toute mention antérieure._

## D'où venait la contradiction

Deux runs du même module (`v162_vecm_cointegration.py`, Johansen + VECM sur EMA et CBOT en EUR/t,
niveaux quotidiens, holdout 2024 exclu) avaient produit des chiffres différents :

| Run | Fenêtre | α_ema | α_cbot | Part EMA | Demi-vie ECM |
|---|---|---|---|---|---|
| artefact commité (ancien) | n=600 jours (fenêtre courte/récente) | −0.0407 | +0.0153 | **72.7 %** | 12.1 j |
| run canonique (2026-06-11) | **n=2 806 jours (tout l'overlap 2010-2025)** | −0.0200 | +0.0188 | **51.6 %** | 14.5 j |

Ce n'était pas un bug : **la part de correction dépend de la fenêtre**. Le test de stabilité du module
le dit lui-même (`stable_corrector: false` — les deux moitiés chronologiques ne désignent pas la même
jambe).

## VERDICT CANONIQUE (la seule conclusion officielle)

1. **Cointégration EMA/CBOT : CONFIRMÉE et robuste** (Johansen rang ≥ 1 sur toutes les fenêtres
   testées ; cohérent Engle-Granger p=7.3e-7 de l'étude NB-EMA). Le basis est bien un terme de
   correction d'erreur — c'est le fondement structurel de la baseline.
2. **Demi-vie du déséquilibre : ~12-15 jours de bourse** (12.1 sur fenêtre courte, 14.5 sur échantillon
   complet). Robuste, et cohérente avec l'AR(1) du basis_z (~17-19.5 j, V120/V161) ; l'horizon de trade
   réalisé reste plus long (~28 j, V138) car niveau ≠ trajectoire.
3. **Part de correction par jambe : PAS UN FAIT STABLE — ne plus la citer comme un chiffre unique.**
   - Échantillon complet 15 ans : **symétrique (~52/48)** — les deux jambes corrigent.
   - Fenêtre récente (600 j) : la jambe **EMA corrige davantage (~73/27)**.
   - Épisodes historiques de compression (V21/V105) : souvent **CBOT-driven** (rattrapage CBOT).
   - Lecture canonique : **« qui corrige » est régime-dépendant**. Sur longue période c'est partagé ;
     dans le régime récent c'est plutôt l'EMA qui revient vers l'équilibre ; pendant certains épisodes
     c'est le CBOT qui rattrape. Les trois observations sont vraies à leur échelle et ne se contredisent
     pas.

## Règles d'usage

- Tout document doit citer : « cointégration confirmée, demi-vie ECM ~12-15 j, correction partagée et
  régime-dépendante (52/48 sur 15 ans ; EMA dominante sur la fenêtre récente) ».
- L'artefact canonique est le run **échantillon complet** (`artefacts/v162/v162_vecm.json`, n=2 806).
  Une part par fenêtre courte peut être citée UNIQUEMENT comme diagnostic de régime, jamais comme LA
  conclusion.
- Implication indicateur : ne pas prédire la jambe qui bougera (non stable) ; suivre la compression du
  basis lui-même (ce que fait la machine d'état) et qualifier le contexte CBOT (V176 cbot_support).
