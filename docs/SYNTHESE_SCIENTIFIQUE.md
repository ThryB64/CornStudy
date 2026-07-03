# Synthese scientifique - etude mais

## Verdict global

- Verdict global : on a de vrais signaux, mais pas le signal simple cherche au depart (monte / baisse demain).
- Au depart : peut-on predire directement si le mais va monter ou baisser ?
- Reponse de l'etude : le prix exact est tres difficile a prevoir et les modeles complexes ne battent pas les references simples. En revanche, certains risques et contextes sont bien plus previsibles : volatilite, risque de baisse, tension WASDE, Crop Condition, basis Euronext/CBOT, prime locale, episodes de compression.
- Donc on peut creer un indicateur, mais pas un indicateur magique 'demain ca monte'. Il faut un indicateur de risque directionnel SELECTIF qui sait dire : risque de baisse eleve, contexte haussier moyen terme, volatilite a venir, prime a vendre, ou signal incertain.
- La cle de credibilite : l'indicateur doit accepter de dire souvent JE NE SAIS PAS (mode UNCERTAIN obligatoire).

## Classification finale des 33 resultats

- Decouvertes validees : 14  |  Garde-fous methodologiques : 5  |  Limites importantes : 14
- Les anciennes 'pistes' ont ete tranchees : chacune est devenue une decouverte validee (test walk-forward concluant) ou une limite (validation impossible avec les donnees gratuites). Plus d'entre-deux.

Table complete : `artefacts/decouvertes/inventaire_decouvertes.csv`.

## 1. Decouvertes validees (le socle de l'etude)

### 01. Le prix exact n'est pas previsible (random walk imbattable)

Aucun des 36 couples (modele x horizon) ne bat 'le prix de demain = celui d'aujourd'hui'.

- Resultat : 0 / 36 couples battent la random walk (baseline random walk, periode 2000-2023, n 36 couples modele x horizon)
- Ce que ca demontre : Aucun modele (sur 36) ne bat la random walk sur le prix exact (test de Diebold-Mariano).
- Pourquoi ca a change l'etude : On arrete de vouloir predire le niveau du prix ; on reformule l'etude vers le risque, la direction et la volatilite.
- Consequence pour l'indicateur : L'indicateur ne predit jamais un prix : il qualifie un contexte de risque.
- CBOT : prix exact non previsible (RMSE) : aucun modele ne bat la random walk.
- Euronext : prix exact non previsible (RMSE) : meme conclusion sur l'Euronext.

![decouverte](01_random_walk_1_decouverte.png)

![courbes](01_random_walk_2_courbes.png)

### 04. Crop Condition US -> direction a 90 jours - AUC 0.816 (holdout)

La notation d'etat des cultures US donne la direction a 90 jours.

- Resultat : AUC 0.604 en walk-forward 2014-2025, IC95 [0.586 ; 0.622], positive sur 77% des annees (placebo 0.508) (baseline 0.5 (hasard), periode OOS 2014-2025, n 3050)
- Ce que ca demontre : La Crop Condition US donne une direction a 90 jours qui tient hors echantillon (walk-forward AUC 0.588, IC95 [0.568 ; 0.609], positive sur 75 % des annees).
- Pourquoi ca a change l'etude : Un fondamental d'offre US porte un vrai signal directionnel moyen terme, plus modeste que le holdout (0.816) mais robuste sur plusieurs annees.
- Consequence pour l'indicateur : Alimente les modules direction et risque de baisse (M1 / M2) a horizon long.
- CBOT : Crop Condition US : AUC 0.816 sur le holdout 2024+ (grosse recolte = baisse).
- Euronext : se transmet a l'Euronext qui suit le CBOT (direction baissiere en 2024).

![decouverte](04_crop_h90_1_decouverte.png)

![courbes](04_crop_h90_2_courbes.png)

### 06. La volatilite est previsible (HAR / EGARCH, -24 % de RMSE)

Les modeles HAR et EGARCH battent nettement la random walk sur la volatilite.

- Resultat : HAR -23 %, EGARCH -23.7 % (baseline random walk de variance, periode OOS 2014-2025, n 2787)
- Ce que ca demontre : La volatilite future est nettement plus previsible que le prix (revalidee en walk-forward : RMSE -15.1 % vs persistance).
- Pourquoi ca a change l'etude : Le risque a de la memoire : c'est une cible exploitable la ou le prix ne l'est pas.
- Consequence pour l'indicateur : Module M3 : regime de volatilite (calme / normal / volatil / extreme) qui module la confiance.
- CBOT : vol previsible : HAR -23 %, EGARCH -23.7 % de RMSE (resultat le plus solide).
- Euronext : meme persistance de volatilite sur l'Euronext (gate de risque).

![decouverte](06_volatilite_1_decouverte.png)

![courbes](06_volatilite_2_courbes.png)

### 07. Le risque de drawdown CBOT est previsible - AUC 0.74

On sait dire a l'avance quand le risque de forte baisse du CBOT monte.

- Resultat : AUC 0.74 (baseline 0.5, periode OOS 2014-2025, n 2845)
- Ce que ca demontre : Le risque de forte baisse du CBOT se detecte a l'avance (walk-forward : AUC 0.646, IC95 [0.627 ; 0.666], n=2845).
- Pourquoi ca a change l'etude : On peut estimer un risque de baisse sans predire le prix.
- Consequence pour l'indicateur : Module M1 (Downside Risk) : le coeur de l'indicateur.
- CBOT : risque de drawdown previsible AUC 0.74 (zones grisees = forts replis).
- Euronext : un repli CBOT entraine l'Euronext : utile comme filtre de risque.

![decouverte](07_drawdown_cbot_1_decouverte.png)

![courbes](07_drawdown_cbot_2_courbes.png)

### 09. Le basis revient a la moyenne (demi-vie 17 a 47 jours)

Apres un basis tres haut, l'ecart EMA-CBOT redescend : signal de vente.

- Resultat : demi-vie 17 a 47 j ; decroit de 2.27 vers 0.5 (baseline absence de reversion, periode 2010-2025, n 37 episodes (z>2))
- Ce que ca demontre : Apres un basis tres haut, l'ecart EMA-CBOT revient vers la moyenne (demi-vie 17 a 47 jours, event study).
- Pourquoi ca a change l'etude : La prime europeenne devient un objet exploitable (retour a la moyenne) la ou le prix ne l'est pas.
- Consequence pour l'indicateur : Module M4 (prime Euronext) : vendre la prime quand elle est anormalement haute.
- CBOT : le CBOT est l'ancre vers laquelle l'ecart revient.
- Euronext : le basis EMA-CBOT revient a la moyenne : vendre la prime quand elle est haute.

![decouverte](09_basis_reversion_1_decouverte.png)

![courbes](09_basis_reversion_2_courbes.png)

### 11. La prime se compresse surtout quand le CBOT MONTE (6x)

Vendre la prime revient a parier sur une hausse relative du CBOT.

- Resultat : jambe CBOT ~6x la jambe EMA (~69 %) (baseline parts egales, periode 2010-2025, n episodes de compression)
- Ce que ca demontre : La compression de prime vient surtout de la hausse du CBOT (jambe CBOT ~6x la jambe EMA).
- Pourquoi ca a change l'etude : Vendre la prime = parier sur un rattrapage du CBOT, pas sur une baisse de l'Euronext.
- Consequence pour l'indicateur : M4 conditionne la vente de prime au contexte CBOT (support).
- CBOT : la compression vient a ~69 % de la hausse CBOT (6x la jambe EMA).
- Euronext : la prime EMA se reduit surtout par le haut (CBOT), peu par l'Euronext lui-meme.

![decouverte](11_compression_cbot_1_decouverte.png)

![courbes](11_compression_cbot_2_courbes.png)

### 16. La prime europeenne est LOCALE : la macro ne l'explique pas (R2 -0.25)

Les variables macro n'expliquent pas le basis hors echantillon.

- Resultat : R2 -0.25 (la macro n'explique pas) (baseline moyenne (R2=0), periode multi, n OOF multi-annees)
- Ce que ca demontre : La macro globale n'explique pas le basis (R2 hors echantillon -0.25).
- Pourquoi ca a change l'etude : On evite d'empiler des variables macro inutiles pour expliquer la prime.
- Consequence pour l'indicateur : M4 reste parcimonieux (basis + saison + contexte CBOT).
- CBOT : le CBOT n'explique pas non plus la prime locale europeenne.
- Euronext : la prime EMA est une prime locale, pas un produit des fondamentaux mondiaux.

![decouverte](16_prime_locale_1_decouverte.png)

![courbes](16_prime_locale_2_courbes.png)

### 17. Specificite EU : la prime suit le basis (+0.59), pas le CBOT (-0.46)

La prime correle avec le basis local et non avec le niveau du CBOT.

- Resultat : corr(prime,basis)=+0.59 ; corr(prime,CBOT)=-0.46 (baseline 0, periode multi, n OOF multi-annees)
- Ce que ca demontre : La prime suit le basis local (+0.59) et pas le niveau CBOT (-0.46) ; a lire avec 'prime locale'.
- Pourquoi ca a change l'etude : Confirme que la prime est locale, pas un artefact du niveau CBOT.
- Consequence pour l'indicateur : M4 s'appuie sur le basis local, pas sur le niveau du CBOT.
- CBOT : la prime n'est pas un artefact du niveau CBOT (corr -0.46).
- Euronext : prime locale confirmee : elle vit avec le basis EMA-CBOT (+0.59).

![decouverte](17_specificity_1_decouverte.png)

![courbes](17_specificity_2_courbes.png)

### 19. Les signaux marginaux (z<1.2) sous-performent les signaux forts

Un faible ecart rapporte bien moins qu'un ecart franc.

- Resultat : marginal 6.1 vs fort 14.1 (baseline indistinct, periode 2010-2025, n OOF (confirme par la courbe de confiance de l'indicateur))
- Ce que ca demontre : Les signaux faibles valent moins que les signaux forts ; confirme par la courbe de confiance de l'indicateur (DA 0.65 -> 0.71 sur les signaux confiants).
- Pourquoi ca a change l'etude : L'indicateur ne doit pas parler tous les jours : il attend des signaux assez forts.
- Consequence pour l'indicateur : Mode UNCERTAIN obligatoire (abstention sur signal faible).
- CBOT : ne vendre la prime que sur des ecarts francs (z eleve).
- Euronext : les signaux EMA faibles rapportent ~2x moins : exiger un z eleve.

![decouverte](19_marginal_1_decouverte.png)

![courbes](19_marginal_2_courbes.png)

### 20. Le CBOT predit mieux ses BAISSES que ses HAUSSES

La predictabilite directionnelle est asymetrique du cote baissier.

- Resultat : baisses ~0.62 vs hausses ~0.50 (baseline 0.5, periode OOS 2014-2025, n 2845)
- Ce que ca demontre : Le CBOT se laisse mieux anticiper a la baisse qu'a la hausse (validation downside forte 2016-2021, faible 2022-2023).
- Pourquoi ca a change l'etude : L'indicateur doit etre d'abord un detecteur de risque de baisse, pas un predicteur de hausse.
- Consequence pour l'indicateur : M1 oriente baisse ; le module hausse (M2) reste prudent.
- CBOT : le signal d'offre US detecte surtout les baisses (recoltes).
- Euronext : utile pour la VENTE : on detecte mieux quand vendre que quand attendre.

![decouverte](20_cbot_drops_1_decouverte.png)

![courbes](20_cbot_drops_2_courbes.png)

### 22. Le meilleur flag ADVERSE est l'ecart de prix ble/mais

Le ratio ble/mais signale les ventes de prime qui vont mal tourner.

- Resultat : AUC 0.590 en walk-forward 2014-2025, IC95 [0.569 ; 0.610], positive sur 77% des annees (placebo 0.493) (baseline 0.5 (hasard), periode OOS 2014-2025, n 3080)
- Ce que ca demontre : L'ecart de prix ble/mais signale le risque de baisse du mais hors echantillon (walk-forward AUC 0.590, IC95 [0.571 ; 0.611], positive sur 75 % des annees).
- Pourquoi ca a change l'etude : Un signal de substitution simple aide a anticiper la baisse, la ou les modeles complexes echouent.
- Consequence pour l'indicateur : Entre dans le module M1 (Downside Risk) comme variable de contexte.
- CBOT : le ratio ble/mais est un contexte (corr 0.60), pas un predicteur direct.
- Euronext : il aide a ecarter les ventes de prime EMA a risque (AUC 0.653).

![decouverte](22_wheat_corn_1_decouverte.png)

![courbes](22_wheat_corn_2_courbes.png)

### 26. Trend-following, stacking et deep learning echouent

Le mais ne tend pas ; les modeles complexes sur-apprennent.

- Resultat : aucun gain net ; sur-apprentissage (baseline random walk / 2 vars, periode 2000-2023, n multi-modeles)
- Ce que ca demontre : Trend-following, stacking et deep learning ne battent pas les references simples (sur-apprentissage).
- Pourquoi ca a change l'etude : Le probleme n'est pas la puissance du modele mais la qualite du signal et la robustesse.
- Consequence pour l'indicateur : L'indicateur reste simple et parcimonieux (pas de boite noire).
- CBOT : aucun modele complexe ne bat la random walk sur le CBOT.
- Euronext : idem sur l'Euronext : 2 variables suffisent, le reste sur-apprend.

![decouverte](26_complex_models_1_decouverte.png)

![courbes](26_complex_models_2_courbes.png)

### 28. Les strategies actives sont a risque de sur-ajustement (PSR/DSR/PBO)

Les mesures dediees signalent un risque eleve de sur-ajustement.

- Resultat : risque de sur-ajustement eleve (baseline bruit / permutation, periode multi, n trades simules)
- Ce que ca demontre : Les strategies actives portent un risque de sur-ajustement (PSR / DSR / PBO) ; le placebo de l'indicateur le confirme (AUC 0.498).
- Pourquoi ca a change l'etude : On privilegie le simple et on teste systematiquement contre le hasard.
- Consequence pour l'indicateur : Tout module passe un placebo avant d'etre cru.
- CBOT : les performances actives sur le CBOT peuvent venir du hasard.
- Euronext : meme garde-fou cote Euronext : ne pas sur-interpreter les backtests.

![decouverte](28_overfit_1_decouverte.png)

![courbes](28_overfit_2_courbes.png)

### 33. La fusion des fondamentaux d'offre est le meilleur modele directionnel (H90)

Crop Condition + niveaux WASDE + ratio ble/mais combines battent chaque bloc isole pour predire la direction CBOT a 90 jours ; le marche seul ne predit rien.

- Resultat : AUC 0.626 en walk-forward 2014-2025, IC95 [0.606 ; 0.646], positive sur 69% des annees (placebo 0.511) (baseline 0.5 (hasard), periode OOS 2014-2025, n 3050)
- Ce que ca demontre : La fusion des fondamentaux d'offre (Crop Condition + niveaux WASDE + ratio ble/mais) est le meilleur modele directionnel de l'etude a 90 jours (walk-forward AUC 0.626, IC95 [0.607 ; 0.646], placebo 0.489) ; le marche seul ne predit rien (0.511) et ajouter le marche dilue (0.603).
- Pourquoi ca a change l'etude : Les trois familles d'offre portent une information complementaire ; les echecs sont lisibles (chocs demande / geopolitique : 2021, 2022) et l'abstention monte la DA de 0.63 a 0.78.
- Consequence pour l'indicateur : Candidat coeur direction CBOT long terme (au-dessus de crop_h90 seul), avec gate d'abstention |p-0.5| < 0.15.
- CBOT : fusion fondamentaux AUC 0.626 IC95 [0.607;0.646], placebo 0.489 ; echecs = chocs demande (2021, 2022) ; DA 0.63 -> 0.78 avec abstention.
- Euronext : meme lecture cote Euronext : signal d'offre moyen terme, pas un signal de prime.

![decouverte](33_direction_fusion_1_decouverte.png)

![courbes](33_direction_fusion_2_courbes.png)

## 2. Garde-fous methodologiques (resultats negatifs utiles)

### 23. La demi-vie du NIVEAU n'est PAS l'horizon de decision (x3)

L'horizon analytique sous-estime trois fois l'horizon reel des trades.

- Resultat : analytique 9.5 j vs reel 28.6 j (x3) (baseline egalite, periode 2010-2025, n trades)
- Interpretation : Caler l'horizon sur le reel ; ne pas choisir un horizon trop court.
- CBOT : caler l'horizon sur le reel (28.6 j), pas sur la demi-vie (9.5 j).
- Euronext : sur l'Euronext aussi : le retour prend ~3x plus longtemps que prevu.

![decouverte](23_halflife_horizon_1_decouverte.png)

![courbes](23_halflife_horizon_2_courbes.png)

### 24. La meteo realisee est deja 'price-in' (AUC 0.508)

Quand on observe la meteo, le marche l'a deja integree.

- Resultat : AUC 0.508 (hasard) (baseline 0.5, periode multi, n a produire (backlog))
- Interpretation : La meteo observee arrive trop tard (deja price-in) : ne pas l'utiliser comme predicteur.
- CBOT : la meteo moyenne realisee n'apporte aucun edge directionnel.
- Euronext : meme constat cote Euronext : pas de signal exploitable de la meteo realisee.

![decouverte](24_weather_priced_in_1_decouverte.png)

![courbes](24_weather_priced_in_2_courbes.png)

### 25. L'explication 'fair-value' du basis est rejetee (Granger)

La causalite de Granger est rejetee hors echantillon.

- Resultat : rejetee hors echantillon (baseline absence de causalite, periode multi, n a produire (backlog))
- Interpretation : Ne pas pretendre une fair-value stable : le basis se suffit a lui-meme.
- CBOT : pas de relation fair-value stable cote CBOT.
- Euronext : le basis EMA n'est pas reconstituable par une juste valeur : prime locale.

![decouverte](25_granger_1_decouverte.png)

![courbes](25_granger_2_courbes.png)

### 27. L'avantage du basis EMA n'est pas si specifique (placebo)

Le test placebo retrouve une partie de l'effet sur des spreads temoins.

- Resultat : effet partiel sur temoins (specificite limitee) (baseline cibles temoins, periode multi, n a etendre (backlog))
- Interpretation : L'edge n'est pas 100 % specifique : etendre le placebo (autres spreads, dates, cultures).
- CBOT : controle negatif : une partie de l'effet n'est pas specifique.
- Euronext : l'edge basis EMA doit etre pris avec prudence (pas 100 % specifique).

![decouverte](27_placebo_1_decouverte.png)

![courbes](27_placebo_2_courbes.png)

### 29. L'inversion saisonniere supposee du basis n'a pas resiste

Une saisonnalite inverse attendue a ete falsifiee en forward.

- Resultat : hypothese falsifiee en forward (baseline saisonnalite simple, periode forward, n a produire (backlog))
- Interpretation : Ne pas construire de regle sur cette hypothese ; garder la saisonnalite simple validee.
- CBOT : pas d'inversion saisonniere exploitable cote CBOT.
- Euronext : sur l'Euronext non plus : la saisonnalite reste celle, simple, deja validee.

![decouverte](29_seasonal_inversion_1_decouverte.png)

![courbes](29_seasonal_inversion_2_courbes.png)

## 3. Limites importantes (dont anciennes pistes non validees)

### 02. Indicateur structurel de vente (basis + saison) - AUC 0.656

Un indicateur a paliers fonde sur le basis et la saison atteint AUC 0.656.

- Resultat : AUC 0.656 (baseline 0.5, periode a produire (placebo + couts backlog), n a produire (backlog))
- Pourquoi c'est une limite (pas validee) : Indicateur de prime : valide seulement comme research-only (module M4) - ordonne les retours mais AUC hors echantillon 0.56 et prix EMA ~97 % proxy.
- CBOT : le basis nourrit l'indicateur via la transmission CBOT->EMA.
- Euronext : indicateur de vente de prime AUC 0.656 (basis_z + saison).

![decouverte](02_indicateur_v9_1_decouverte.png)

![courbes](02_indicateur_v9_2_courbes.png)

### 03. Modele a 2 variables (basis_z + saison) - AUC 0.694

Deux variables suffisent : la parcimonie bat les modeles complexes.

- Resultat : AUC 0.694 (baseline 0.5 + modeles complexes, periode a produire (placebo + couts backlog), n a produire (backlog))
- Pourquoi c'est une limite (pas validee) : Indicateur de prime (basis + saison) : meme limite research-only que M4 (proxy 97 %, couts non integres).
- CBOT : appuie sur le basis CBOT-EMA, pas sur des dizaines de variables.
- Euronext : AUC 0.694 avec seulement basis_z + saison : la simplicite gagne.

![decouverte](03_modele_2vars_1_decouverte.png)

![courbes](03_modele_2vars_2_courbes.png)

### 05. WASDE stocks-sur-usage -> direction a 40 jours - DA 0.705

Le ratio stocks-sur-usage du WASDE oriente la direction a 40 jours.

- Resultat : DA 0.705 (holdout) (baseline random walk 0.5, periode holdout 2024+, n a produire (par annee + IC backlog))
- Pourquoi c'est une limite (pas validee) : AUC 0.563 mais positive sur 46% des annees seulement (instable hors echantillon, sous le seuil de robustesse).
- CBOT : stocks US bas = marche tendu ; DA 0.705 a H40 sur le holdout.
- Euronext : l'Euronext herite de la direction US via la cointegration.

![decouverte](05_wasde_h40_1_decouverte.png)

![courbes](05_wasde_h40_2_courbes.png)

### 08. L'issue ADVERSE d'une vente de prime est previsible - AUC 0.72

On ne sait pas COMMENT ca tourne mal, mais on estime le RISQUE a l'entree.

- Resultat : issue 0.72 ; mecanisme 0.48 (baseline 0.5, periode 2010-2025, n 42 episodes (LOO))
- Pourquoi c'est une limite (pas validee) : Repose sur 42 episodes en validation LOO : trop peu d'observations pour elever au socle.
- CBOT : le risque d'echec se lit a l'entree (niveau + basis bas), AUC 0.72.
- Euronext : permet de filtrer les ventes de prime risquees sur l'Euronext.

![decouverte](08_adverse_predictable_1_decouverte.png)

![courbes](08_adverse_predictable_2_courbes.png)

### 10. Vendre quand le basis est haut survit aux couts (+115 hors crise)

La regle 'vendre la prime haute' reste gagnante apres couts, hors crise.

- Resultat : +115 hors crise ; edge sur z>2 (baseline 0 / buy-and-hold, periode hors crise, n episodes z>2)
- Pourquoi c'est une limite (pas validee) : Resultat +115 hors crise uniquement ; le PnL net fond avec les couts (brut +15.7 -> +5.7 a 5 EUR/t).
- CBOT : le pari = hausse relative du CBOT pendant la compression.
- Euronext : vendre une prime z>2 sur l'Euronext : +115 hors crise apres couts (~5 EUR/t).

![decouverte](10_sell_high_cost_1_decouverte.png)

![courbes](10_sell_high_cost_2_courbes.png)

### 12. Avantage asymetrique : vendre la prime haute bien plus que l'inverse

Le short de prime haute est robuste ; le pari inverse ne l'est pas.

- Resultat : short prime haute robuste ; long prime basse non (baseline symetrie, periode 2010-2025, n episodes)
- Pourquoi c'est une limite (pas validee) : Base sur la bibliotheque d'episodes (peu nombreux) ; a confirmer sur un echantillon plus large.
- CBOT : parier sur la baisse du CBOT (long prime) n'est pas robuste.
- Euronext : vendre une prime haute marche ; acheter une prime basse, non.

![decouverte](12_asymmetry_1_decouverte.png)

![courbes](12_asymmetry_2_courbes.png)

### 13. Le support CBOT divise par 2 le risque ADVERSE et double le PnL

Un CBOT qui soutient rend la compression plus sure et plus rapide.

- Resultat : risque ADVERSE /2, PnL x2, reversion ~29 j (87.5 %) (baseline sans support, periode 2010-2025, n 42 episodes)
- Pourquoi c'est une limite (pas validee) : 42 episodes et effet possiblement confondu avec le momentum : non isolable ici.
- CBOT : un CBOT haussier : risque ADVERSE /2, PnL x2, reversion ~29 j vers z0 (87.5 %).
- Euronext : les ventes de prime EMA reussissent surtout quand le CBOT soutient.

![decouverte](13_cbot_support_1_decouverte.png)

![courbes](13_cbot_support_2_courbes.png)

### 14. Trois familles d'episodes : CBOT_DRIVEN, EMA_DRIVEN, ADVERSE

Les episodes tires par le CBOT gagnent presque toujours ; les ADVERSE jamais vraiment.

- Resultat : CBOT_DRIVEN +22.7 (~100 % win) ; EMA +14 ; ADVERSE 5.7 (baseline indistinct, periode 2010-2025, n 42 episodes)
- Pourquoi c'est une limite (pas validee) : Resultat descriptif (typologie d'episodes), pas un signal predictif hors echantillon.
- CBOT : CBOT_DRIVEN : gain ~100 % du temps ; ADVERSE distinguables tot.
- Euronext : 42 episodes EMA : familles nettement separees des l'entree.

![decouverte](14_episodes_1_decouverte.png)

![courbes](14_episodes_2_courbes.png)

### 15. La sortie partielle (revenir vers z=0.5) sauve des pertes

Sortir a mi-chemin plutot qu'au retour complet evite les pertes en queue.

- Resultat : z=0.5 sauve des pertes (2010, 2013) (baseline sortie z=0, periode 2010-2025, n episodes)
- Pourquoi c'est une limite (pas validee) : Regle de strategie (objectif de sortie) non backtestee en walk-forward avec couts.
- CBOT : sortir tot evite d'attendre un retour complet qui n'arrive pas toujours.
- Euronext : exit partiel z=0.5 : defaut prudent sur les ventes de prime EMA.

![decouverte](15_exit_z05_1_decouverte.png)

![courbes](15_exit_z05_2_courbes.png)

### 18. La demi-vie du basis retrecit quand l'ecart est extreme

Plus le basis est tendu, plus il revient vite a la moyenne.

- Resultat : modere 8.3 j / fort 4.9 j / extreme 3.3 j (baseline demi-vie constante, periode 2010-2025, n par regime)
- Pourquoi c'est une limite (pas validee) : Resultat econometrique descriptif, non valide en forward comme signal.
- CBOT : le CBOT ramene l'ecart d'autant plus vite qu'il est extreme.
- Euronext : un basis EMA tres haut se resorbe en ~3 jours (vs ~8 en regime modere).

![decouverte](18_halflife_extreme_1_decouverte.png)

![courbes](18_halflife_extreme_2_courbes.png)

### 21. Le signal meteo est dans les EXTREMES prevus, pas dans la moyenne

Un dome de chaleur prevu en pollinisation deplace le prix ; la meteo moyenne non.

- Resultat : corr +0.31 ; extreme +1.6 % vs reste -2.3 % (baseline meteo moyenne (nulle), periode oracle (borne sup, non-tradeable), n episodes d'ete)
- Pourquoi c'est une limite (pas validee) : Resultat 'oracle' (sur meteo realisee, non-tradeable) ; exige une archive de previsions forward reelles.
- CBOT : pic de chaleur prevu : corr +0.31 avec le rendement CBOT.
- Euronext : un ete de stress rend la prime EMA moins compressible (contexte).

![decouverte](21_weather_extreme_1_decouverte.png)

![courbes](21_weather_extreme_2_courbes.png)

### 30. Le mur des couts : l'avantage net est mince et conditionnel

L'edge se concentre sur les extremes et s'efface vite avec les couts.

- Resultat : edge concentre sur z>2 ; s'efface au-dela de ~5 EUR/t (baseline cout nul, periode hors crise, n episodes z>2)
- Pourquoi c'est une limite (pas validee) : Toujours montrer brut / net / +2 / +5 EUR/t et crise / hors crise.
- CBOT : edge concentre sur z>2 ; au-dela de ~5 EUR/t, il disparait.
- Euronext : vendre la prime EMA n'est rentable que sur des signaux francs, hors crise.

![decouverte](30_cost_wall_1_decouverte.png)

![courbes](30_cost_wall_2_courbes.png)

### 31. Le score de vente final est FRAGILE

Il bat la random walk sur le holdout mais pas une simple saisonnalite.

- Resultat : DA 0.686 (> random walk) mais < saisonnalite 0.752 (baseline random walk 0.5 + saisonnalite 0.752, periode holdout 2024+ (~1.5 an), n fenetre courte)
- Pourquoi c'est une limite (pas validee) : Repere utile, pas une preuve : a reconfirmer en walk-forward multi-annees.
- CBOT : DA 0.686 > random walk mais < saisonnalite (0.752) : a reconfirmer.
- Euronext : sur l'Euronext : un repere utile, pas une preuve de robustesse.

![decouverte](31_fragile_1_decouverte.png)

![courbes](31_fragile_2_courbes.png)

### 32. L'indicateur Euronext est RESEARCH_ONLY

Il ordonne bien les retours mais discrimine mal hors echantillon (proxy 97 %).

- Resultat : ordonne (-5.8 % vs +5.1 %) mais AUC 0.561, prix 97 % proxy (baseline 0.5, periode hors echantillon, n a produire (backlog))
- Pourquoi c'est une limite (pas validee) : RESEARCH_ONLY tant que les vrais prix Euronext et couts ne sont pas propres.
- CBOT : le score vient du CBOT (basis et EUR/USD non integres).
- Euronext : ordonne les retours (vendre -5.8 %, attendre +5.1 %) mais AUC 0.561, prix 97 % proxy.

![decouverte](32_euronext_ro_1_decouverte.png)

![courbes](32_euronext_ro_2_courbes.png)

## Backlog restant

- Intervalles de confiance (bootstrap 95 %) sur chaque metrique forte (AUC 0.816, DA 0.705, AUC 0.74, 0.694, 0.72).
- Performance PAR ANNEE (DA / AUC / signal moyen) pour verifier que le resultat ne vient pas que de 2024.
- Calibration (Brier, courbe de fiabilite) : quand le modele dit 70 % de risque, la baisse arrive-t-elle ~70 % du temps ?
- Placebo etendu : autre spread, dates decalees, cible melangee, autre culture, annees hors signal.
- Couts et vrai prix : brut / net / +2 EUR/t / +5 EUR/t, crise vs hors crise ; vrais prix Euronext et base locale au lieu du proxy 97 %.
- Nombre d'observations et periode de test explicites pour chaque decouverte prometteuse.

## Phrase finale

L'etude montre que le prix exact du mais reste tres difficile a prevoir. En revanche, plusieurs composantes du risque sont partiellement previsibles : la volatilite, le risque de drawdown, les pressions fondamentales WASDE / Crop Condition et la compression de prime Euronext / CBOT. L'indicateur final doit donc etre concu comme un outil de detection de contextes favorables ou defavorables, avec un mode UNCERTAIN obligatoire, et non comme un modele de prevision parfaite du prix.
