# EXT004 — Résultats : crush éthanol / énergie

**Verdict : REJECT (sur proxys disponibles).** Data status : **PARTIAL_DATA**.

## Données
Disponibles : EIA éthanol production + stocks (hebdo vendredi, publié mercredi →
`available = Date + 5 j`) ; pétrole et gaz quotidiens ; corn_close.
**Absents** : prix éthanol (CME/EIA), DDG, soybean meal → **ni vraie marge crush, ni
ratio corn/éthanol**. On teste donc des proxys : demande éthanol (production/stocks z)
et ratios énergie-corn (oil/corn, gas/corn). Variable d'état lente (fiche EXT004 : H60+).

## Résultats (BASE vs BASE+FAMILLE)

| H | ΔRMSE % | ΔDA | DM p |
|---|---|---|---|
| 5 | +1.7 % | +0.004 | 0.042 |
| 20 | +12.1 % | −0.009 | 0.0005 |
| 40 | +18.3 % | −0.009 | 0.008 |
| 90 | +36.8 % | −0.097 | 0.046 |

## Lecture
Les proxys de demande éthanol et les ratios énergie-corn **dégradent RMSE et DA** à
moyen/long horizon (significatif dans le mauvais sens). Aucun apport sur la direction
CBOT. Conforme à V39-E3/E5 (l'éthanol était déjà faible sur la prime EU).

## Conclusion
**REJECT** sur les proxys testables, **PARTIAL_DATA** sur la famille complète : sans prix
éthanol ni DDG, la vraie marge crush n'est pas constructible. La marge crush reste
théoriquement une variable de demande structurelle (H60+) ; pour la tester réellement il
faut sourcer un prix éthanol (CME/EIA) et idéalement DDG (USDA AMS). En l'état, pas de
signal. Action étape 5 : sourcer prix éthanol avant de rouvrir ; ne pas reprendre les
proxys énergie tels quels.
