# Synthèse Finale Euronext EMA

> EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.

## Verdict Global

Le pivot complet vers Euronext comme moteur directionnel principal n'est pas validé.

Euronext EMA est en revanche une extension très utile de l'étude maïs :

- prix européen réel exploitable pour un raisonnement métier ;
- basis CBOT/EMA statistiquement intéressant ;
- couche de traduction locale pour un rapport agriculteur français ;
- série harvest_nov utile pour le prix de récolte ;
- point de départ sérieux pour les décisions de stockage ;
- contexte de marché via Module A, à condition de libeller les proxies.

La bonne architecture actuelle est donc :

```text
CBOT + fondamentaux US/monde  -> moteur directionnel principal
EMA front / harvest_nov       -> prix local européen
Basis CBOT-EMA                -> signal relatif Europe vs monde
Stockage EMA                  -> décision métier à améliorer
Module A                      -> contexte lisible, pas signal autonome final
CQR EMA                       -> non exploitable en l'état pour promesse 90%
```

## Décisions

| Question | Verdict | Conclusion |
|---|---|---|
| Euronext direct comme cible directionnelle principale | NO_GO | DA/AUC insuffisants sur `y_up_h20_ema`. |
| CBOT comme moteur principal | GARDER | Le benchmark CBOT reste plus robuste. |
| Basis CBOT/EMA | GARDER | Mean reversion confirmée et meilleur signal EMA actuel. |
| Courbe Euronext complète | NON | Données trop sparse : 1.246 contrat/date en moyenne. |
| Stockage EMA | PROMETTEUR MAIS NO_GO | Oracle fort, modèles actuels trop instables. |
| Module A | GARDER COMME CONTEXTE | Utile, mais `missing/manual/proxy` doivent être visibles. |
| CQR prix EMA | NO_GO | Aucun intervalle n'atteint 88% de couverture empirique. |
| Source historique EMA | RECHERCHE SEULEMENT | `barchart_proxy_exploratory`, pas settlement officiel. |

## Ce Qui Est Solide

### Données EMA

L'infrastructure EMA est maintenant exploitable pour la recherche :

- 4 818 lignes contrats ;
- période 2010-01-04 à 2026-05-20 ;
- contrats H/M/Q/X utilisables ;
- 0 ligne F/Janvier dans les séries finales ;
- front/liquid raw et adjusted ;
- harvest_nov ;
- table de référence contrats ;
- canonicalisation des lignes Euronext officielles récentes.

La limite majeure reste la source historique : Barchart proxy web est une bonne source exploratoire, mais pas une source officielle de production.

### Roll Audit

Les roll gaps sont réels et importants :

- 69 rolls front ;
- gap moyen absolu 9.688 EUR/t ;
- gap max 54.250 EUR/t ;
- H20 traverse un roll dans 39.7% des fenêtres ;
- H40 dans 79.1% ;
- H60 dans 100%.

Conséquence : pour les rendements, momentum, volatilité et features techniques, utiliser `adjusted`. Pour les prix réels, stockage et rapport agriculteur, utiliser `raw`.

### Relation EMA/CBOT

EMA et CBOT EUR/t sont fortement liés en niveau :

- corrélation prix : 0.9409 ;
- corrélation rendements 1j : 0.3425 ;
- basis moyen : 37.23 EUR/t ;
- basis P05/P50/P95 : 8.50 / 37.86 / 62.50 EUR/t.

Le lead-lag est surtout contemporain. Les tests Granger exploratoires suggèrent un signal EMA -> CBOT à lag 1, mais ce n'est pas une preuve causale.

## Ce Qui Ne Marche Pas Encore

### Direction EMA Directe

Le benchmark pivot principal donne :

- `y_up_h20_ema` avec CBOT+EMA : DA 0.4673, AUC 0.5026 ;
- IC95 DA : [0.4432 ; 0.4902] ;
- hebdomadaire : DA 0.4638.

Les targets raw/adjusted/no-roll n'ont pas renversé le diagnostic :

- raw H20 : DA 0.4673 ;
- adjusted H20 : DA 0.4470 ;
- no-roll H20 : DA 0.4457.

Conclusion : l'échec du pivot EMA direct ne vient pas seulement des rolls.

### Courbe EMA

Il ne faut pas parler de vraie courbe Euronext complète pour l'instant :

- contrats moyens par date : 1.246 ;
- dates avec au moins 2 contrats : 14.9% ;
- dates avec au moins 3 contrats : 5.0% ;
- `ema_spread_f0_f1` non-null : 14.8% ;
- `ema_curve_slope_3` non-null : 5.0%.

Le bon libellé est : **EMA front/basis/liquidity features, with partial curve fragments**.

### Stockage

Le stockage automatique n'est pas validé :

- `always_store_3m` : -1.319 EUR/t ;
- `never_store` : 0.000 EUR/t ;
- oracle 3m : +8.660 EUR/t ;
- meilleur modèle économique : +0.005 EUR/t, années positives 3/8.

La décision stockage a donc un potentiel métier fort, mais les modèles actuels ne capturent pas encore ce potentiel.

### CQR Prix EMA

Les intervalles de prix ne sont pas fiables à 90% :

- meilleur H20 disponible : `cbot_converted`, coverage 79.2%, Winkler 160.2 ;
- meilleur H60 disponible : `cbot_converted`, coverage 80.4%, Winkler 199.8 ;
- CQR quantile selected H20 : coverage 75.0% ;
- CQR quantile selected H60 : coverage 73.0%.

Les années 2021-2022 cassent fortement la calibration. Il ne faut donc pas promettre de fourchette prix EMA 90% dans un rapport agriculteur.

## Le Signal Important : Basis

Le basis CBOT/EMA est le meilleur résultat Euronext actuel.

Quand le basis est très haut :

- H20 : basis change moyen -7.64 EUR/t ;
- reversion 70.4% ;
- EMA-CBOT return relatif moyen -0.0622.

Quand le basis est très bas :

- H20 : basis change moyen +6.06 EUR/t ;
- reversion 68.0% ;
- EMA-CBOT return relatif moyen +0.0725.

À H60, la reversion est encore plus marquée, mais l'interprétation doit rester prudente à cause des rolls.

Conclusion : le basis doit devenir un module explicite de l'indicateur, probablement sous forme de score de tension locale Europe vs monde.

## Module A

Le Module A doit rester un contexte interprétable, pas une preuve autonome.

Statut des 12 signaux :

- `real` : 4 ;
- `proxy` : 5 ;
- `manual` : 1 ;
- `missing` : 2.

Signaux à garder :

- `wasde_surprise` : priorité, DA hebdo 56.7%, poids 0.169 ;
- `bilan_mondial` ;
- `cot_positioning` ;
- `bilan_stocks_eu` comme proxy basis ;
- `brazil_supply_pressure` comme proxy.

Signaux à corriger :

- `china_demand` : missing dans la source active ;
- `export_pace_eu` : missing ;
- `futures_structure` : couverture 10.4%, à remplacer ou déclasser ;
- `ukraine_corridor` : manuel, à documenter explicitement.

Le point le plus important est méthodologique : les signaux proxy peuvent aider à expliquer, mais ne doivent pas être présentés comme données économiques réelles.

## Architecture Recommandée

### Moteur Directionnel

Conserver CBOT comme moteur principal :

- cible principale directionnelle : CBOT ;
- features : fondamentaux US/monde, WASDE, COT, météo, macro, EMA basis ;
- filtrage par confiance et stabilité annuelle.

### Couche Locale EMA

Utiliser EMA pour :

- traduire le prix en EUR/t européen ;
- suivre front raw ;
- suivre harvest_nov ;
- calculer basis CBOT/EMA ;
- alimenter stockage ;
- contextualiser le rapport agriculteur.

### Module Basis

Créer un module dédié :

```text
basis_zscore
extreme_high / extreme_low
expected_reversion_h20/h40
relative_tension_europe_vs_world
```

Ce module doit répondre à une question simple :

> Le Matif est-il anormalement cher ou bas par rapport au CBOT converti ?

### Module Stockage

Ne pas utiliser encore comme décision automatique.

Prochaine version :

- coûts de stockage locaux ;
- frais financiers ;
- risque qualité ;
- stratégie 1m/3m/6m ;
- marge de sécurité ;
- regret vs oracle ;
- stabilité par année.

### Module Prix / CQR

Ne pas publier de fourchette 90% tant que la calibration échoue.

Prochaine version :

- calibration séparée par régime ;
- volatilité locale EMA ;
- traitement explicite des années de choc ;
- intervalles plus conservateurs en stress market ;
- benchmark par période normale vs crise.

## Priorités De Suite

### P0 — Qualité Des Données

1. Obtenir une source officielle ou contractuelle : Barchart OnDemand/Premier, Euronext NextHistory/Web Services, LSEG/Refinitiv.
2. Remplacer `export_pace_eu` par une vraie source ou assumer son retrait.
3. Corriger `china_demand` : la colonne active est vide alors qu'un fallback WASDE existe.
4. Remplacer `futures_structure` par une vraie courbe multi-contrats ou le retirer des scores forts.

### P1 — Basis

1. Transformer l'étude mean reversion en module utilisable.
2. Tester seuils `basis_z > 2` et `< -2` en walk-forward.
3. Séparer effet EMA, effet CBOT, effet EUR/USD.
4. Ajouter un score de tension locale.

### P2 — Stockage

1. Refaire le benchmark stockage avec coûts locaux paramétrables.
2. Tester des seuils économiques plus stricts.
3. Évaluer gain moyen, pire année, regret et stabilité.
4. Ne pas piloter au DA seul.

### P3 — Direction EMA

Ne pas prioriser tant que le pivot reste NO_GO.

À reprendre seulement si :

- source EMA officielle confirmée ;
- targets directionnelles plus propres ;
- features Europe réelles ajoutées ;
- basis module stabilisé.

### P4 — Prix EMA CQR

À reprendre après :

- segmentation par régime ;
- calibration plus robuste ;
- stress years isolées ;
- meilleure volatilité locale.

## Conclusion

L'étude Euronext n'a pas validé le Matif comme moteur directionnel principal.

Elle a cependant apporté trois choses importantes :

1. Un prix européen réel pour traduire le signal.
2. Un signal de basis CBOT/EMA économiquement cohérent.
3. Une base pour raisonner en décision agricole, surtout stockage et harvest_nov.

La suite ne doit pas chercher à forcer Euronext à remplacer CBOT. La bonne direction est de construire un indicateur hybride :

```text
CBOT prédit le mouvement global.
EMA mesure la réalité locale européenne.
Le basis explique les divergences.
Le stockage transforme le signal en décision métier.
```

C'est plus robuste, plus honnête, et plus utile pour comprendre le cours du maïs.
