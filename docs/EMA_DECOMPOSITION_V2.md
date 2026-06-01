# EMA DECOMPOSITION V2

> Source EMA exploratoire/proxy. Chaque bloc indique DESCRIPTIF ou PRÉDICTIF.

## DESCRIPTIF

Variables contemporaines : ΔEMA_t = β1 × ΔCBOT_t + β2 × Δbasis_t + résidu_t.
R² CBOT + basis : 0.936.
Gain basis : 0.724.

Ce bloc est descriptif, NON prédictif.

## PRÉDICTIF

Variables décalées shift(1), walk-forward OOF.
R² OOF H20 : -0.166.
Verdict : PREDICTIVE_NO_GO.

## Conclusion

La décomposition contemporaine explique EMA, mais la prédiction des retours EMA reste faible.