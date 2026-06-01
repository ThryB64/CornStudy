# EMA RESIDUAL EU V2

> Résidu européen OOF. Source EMA exploratoire/proxy.

## Méthode

OOF coefficients by crop year: ΔEMA_t - (β1_train×ΔCBOT_t + β2_train×Δbasis_t)

## Chocs

- Événements 2σ : 106
- Événements 3σ : 46
- Écart-type résiduel : 0.0044

## Attribution

Les familles météo EU, Ukraine, EUR/USD direct, TTF/ETS direct et MARS mensuel sont marquées manquantes si elles ne sont pas présentes dans le master features.

## Verdict

Le catalogue de chocs est exploitable pour analyse événementielle, mais la prédiction des chocs résiduels reste expérimentale.