# V121 — Modèle performant sur le basis : bat-il le naïf ? reste-t-il du bruit blanc ?

Session 2026-06-02. Suite de V120. Évaluation OUT-OF-SAMPLE walk-forward (OLS récursif causal, fenêtre
expandante, min 250 obs) de modèles prédisant `basis_z` à h=1/5/10. `RESEARCH_ONLY_NOT_TRADING`.

## Modèles
- **RW** marche aléatoire (prév = dernière valeur) · **MEAN** moyenne expandante · **AR1** `c+φ·bz_{t-1}` ·
  **ARIMAX** AR1 + exog laggés (CBOT ret, Δwheat/corn).

## Résultats OOS (n=2512)
| horizon | RMSE RW | RMSE AR1 | RMSE ARIMAX | skill AR1 vs RW | exog aide OOS | DA (Δ) |
|---|---:|---:|---:|---:|:--:|---:|
| h=1  | 0.352 | 0.349 | 0.349 | **+0.9 %** | non | 0.53 |
| h=5  | 0.749 | 0.718 | 0.720 | **+4.2 %** | non | 0.60 |
| h=10 | 0.963 | 0.899 | 0.902 | **+6.7 %** | non | 0.62 |

(MEAN ≈ 1.23 partout → la réversion instantanée totale est fausse ; la réversion GRADUELLE AR est correcte.)

## Conclusions
1. **Oui, il existe un modèle performant** : l'AR(1) de réversion **bat la marche aléatoire**, et l'avantage
   **croît avec l'horizon** (+0.9 % à h1 → **+6.7 % à h10**, précision directionnelle 0.53 → 0.62). C'est la
   signature attendue d'une série mean-reverting : plus on regarde loin, plus la réversion vers la moyenne est
   prévisible. Le **signal du NIVEAU est donc bien exploitable** (cohérent V120 : demi-vie ~17 j).
2. **Les variables explicatives n'ajoutent PAS de skill OOS** : ARIMAX ≈ AR1 (voire légèrement pire). Le gain
   in-sample de l'exog (V120, AIC 2012→1814) **ne généralise pas** — c'est de l'ajustement in-sample, pas un
   pouvoir prédictif réel. Leçon de discipline confirmée.
3. **Résidus OOS pas parfaitement blancs** (Ljung-Box rejette faiblement) : il reste une structure ténue
   non captée par un AR(1) linéaire, mais trop faible pour être exploitée proprement (cohérent V106/V120).

**Verdict `MODEL_BEATS_NAIVE_RESIDUALS_NOT_FULLY_WHITE`.**

## Synthèse de l'arc économétrique (V120 + V121)
Le basis_z est une série **mean-reverting** dont le meilleur prédicteur est **sa propre réversion de niveau**
(AR1), exploitable surtout à horizon de quelques semaines — ce qui valide pleinement la baseline `basis_z>1`
(vendre la prime haute et attendre la réversion ~17 j). En revanche, **ajouter des variables explicatives ou
chercher un timing fin jour-le-jour n'apporte pas de gain OOS robuste** : l'essentiel du signal est dans le
niveau, pas dans les variations. C'est la réponse complète à « peut-on avoir un modèle performant et ne
laisser que du bruit blanc ? » → modèle performant OUI (réversion), bruit blanc résiduel PRESQUE (structure
résiduelle faible et non exploitable), exog OOS NON.

Module `v121_basis_forecast_model.py`, tests 2 PASS, ruff PASS, artefact `artefacts/v121/`.
