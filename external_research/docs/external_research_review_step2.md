# Revue structurée des sources — Étape 2

Date : 2026-06-12. Périmètre : sources KEEP_CORE analysées + principales KEEP_METHOD. Détails par source dans `source_cards/`.

## Bloc 1 — Fondamentaux maïs

### 1.1 USDA / WASDE / événements

**Ce que la littérature établit** (PAPER003, PAPER004, PAPER005, NCGA 2022) :
- Les rapports USDA restent market-moving malgré l'information privée ; la SURPRISE (vs attentes) est la variable, pas la valeur publiée.
- Hiérarchie d'impact corn : Grain Stocks (janvier), Prospective Plantings/Acreage, WASDE+Crop Production d'août-nov > rapports d'hiver. Notre veto WASDE V9 ignore Grain Stocks et Acreage — à élargir.
- L'ajustement est quasi immédiat (minutes) → en quotidien, l'annonce est un référentiel de fenêtres et de volatilité, PAS un trade.

**Ce que nous en faisons** : EXT026 (pipeline vintage, infra) → EXT007 (calendrier élargi × saison, event-study vol + drift post-rapport) → EXT008 (surprises proxy M−M-1). Rappel interne : WASDE déjà NO_GO sur la prime EMA (V18) — tout ce bloc cible le CBOT (PROJET2).

### 1.2 Crop progress / météo

**Ce que la littérature établit** (Lehecka 2014, Tsiboe 2023, Taylor 2010, Singh 2020, CropProphet 2026) :
- Les surprises de notation hebdo bougent le corn, surtout juillet-août, asymétriquement (détériorations > améliorations) ; incorporation rapide (mardi).
- Les notations RETARDENT sur le stress réel (Tmin pollinisation, déficit hydrique de remplissage) → la météo par STADE a une avance informationnelle potentielle.
- L'information météo de marché vit dans la RÉVISION de prévision, pas le réalisé — validation externe de notre V45/V136.

**Ce que nous en faisons** : EXT027 (surprises de condition — la feature la plus actionnable du programme : donnée publique, datée lundi 16h ET, mécanisme prouvé), EXT041 (test 2 étages météo→notation SANS marché d'abord), EXT001/EXT002 (fenêtres par stade, design Singh), EXT033 (révisions de prévision — data-gated par la profondeur de notre archive).

### 1.3 Prime météo new-crop — le parallèle avec notre étude

(PAPER007 Li-Hayes-Jacobs, PAPER008 Janzen.) Le contrat décembre porte une prime d'assurance qui se dissipe hors années de choc : structurellement identique à notre prime EMA (compression fréquente, ADVERSE rare et coûteux, V13-V15). EXT018 = réplication descriptive peu coûteuse ; EXT042 (nouveau) : nos deux primes sont-elles corrélées en été ? Si oui, une part de la « prime locale » V16 est une prime météo US importée.

### 1.4 Courbe / roll / nearby-deferred

(PAPER015 Hu et al., PriceAnalysis ch. 9 et 22, RollFutures, PATENT007.)
- Pour les stockables, la découverte de prix est partagée le long de la courbe, nearby dominant ; le spread nearby-deferred normalisé par le full carry est la lecture quantitative des stocks.
- La méthode de roll peut contaminer toute série continue ; la règle causale est : décision sur volume J-1.

**Ce que nous en faisons** : EXT006 (hygiène, protège tous les résultats), EXT005+EXT039 (distance au full carry → quantifie notre lecture V125 NARROWING).

### 1.5 COT

(cot_reports, PAPER022.) Le repo est propre (7 rapports, licence OK) mais ne fournit PAS la date de publication. Anti-fuite : positions mardi, publication vendredi. V18 a falsifié le net total ; les catégories Disaggregated (Managed Money extrêmes/flux, CIT) restent ouvertes → EXT003/EXT040, avec construction du calendrier de publication comme prérequis dur.

### 1.6 Éthanol / DDG / basis / prime locale

(PAPER017 Mallory-Hayes-Irwin, Dahlgran-Gupta, Gertner, Carter-Rausser-Smith, PATENT010.)
- La chaîne énergie→éthanol→corn tient aux horizons LONGS (marge crush = variable d'état, pas signal court) → EXT004 ciblé H60+.
- Le hedge crush varie par LOCALISATION : les primes locales persistent et ne sont pas arbitrées — confirmation indépendante de notre V16. → EXT029 descriptif (décomposition de variance, hedge ratio roulant EMA↔CBOT).
- La relation stocks→prix N'EST PAS STABLE entre régimes de politique (mandat éthanol) → garde-fou pour EXT024/EXT038.
- DDG : data-gated (inventaire AMS d'abord, EXT030).

### 1.7 Transmission UE — le papier le plus proche de notre objet

(PAPER016 Penone-Giampietri-Trestini 2022.) Spot UE cointégré aux futures, EMA = référence de proximité, CBOT = ancre, découplages locaux possibles. Donne : (a) le cadre VECM pour formaliser notre V21 (69 % de la compression par la jambe CBOT = vitesses d'ajustement asymétriques) → EXT044 ; (b) la preuve qu'un spot UE exploitable existe (pistes FranceAgriMer/Bologne) pour le volet physique de EXT013.

## Bloc 2 — Benchmarks

- **EXT025 (Reeve & Vigfusson)** : les futures battent rarement la RW ; chaque EXT doit rapporter {RW, RW+drift saisonnier, futures-as-forecast} + DM-test. **Premier code de l'étape 3.**
- **Vol (Musunuru GARCH ; HAR ; Samuelson PAPER042)** : GARCH(1,1) suffit pour le clustering ; asymétrie INVERSE des grains (chocs haussiers → vol) ; fusion EXT009+EXT010+EXT045 en une seule expérience de vol, au service des gates UNCERTAIN_VOL et de drawdown_risk V23.
- **Trend (PyTrendFollow)** : EWMAC(16,64)+vol targeting figé ex ante = plancher technique (EXT011) ; le trend CBOT est déjà un contexte prouvé chez nous (V39-E4).
- **OU (repo006)** : formalisation de la demi-vie V10 et de l'écart V138 (analytique vs trade réel ×3) — EXT012, calibration expandante stricte.

## Bloc 3 — ML avancé

- **AGRICAF (PAPER029)** — la meilleure source du bloc : son apport est le CHOIX DE VARIABLES (anomalies d'offre régionale datées publication), pas le modèle. Ouvre le test inédit EXT043 : l'anomalie UE+Ukraine explique-t-elle le niveau de notre prime H60+ ? (V16 n'avait testé que macro/FX/énergie.)
- **Brignoli et al. (PAPER002)** : référence de protocole comparatif (le DL gagne rarement hors échantillon contre des benchmarks bien spécifiés) — cadre obligatoire pour EXT016/EXT021.
- **Drachal (PAPER031)** : DMA — valeur diagnostique (inclusion probability par famille au cours du temps) > valeur prédictive → EXT014 comme outil de santé du signal (V124).
- **SHAP (PAPER032/PAPER020)** : la sélection se fait DANS chaque split train, jamais sur tout le dataset → EXT015 = 5e validation de la parcimonie 2 vars.
- **NBEATSx (repo011, MIT)** : le seul candidat DL propre si on en fait un ; verdict honnête attendu : REJECT ; conditionnel, dernier.

## Bloc 4 — Différé (documenté, non prioritaire)

Sentiment/news (attention > sentiment, GDELT horodaté — papier 2026 du catalogue), satellite/NDVI (Piette 2019, Sentinel-2 — archive absente chez nous), TSFM (mémorisation), microstructure intraday (hors données), options/vol implicite (chapitres PriceAnalysis en ligne + do-corn-options — données options à sourcer). Aucun EXT du bloc 4 n'est proposé pour l'étape 3.

## Convergences externes ↔ internes (à retenir)

1. La prime locale persistante existe ailleurs (crush par localisation) — notre V16 n'est pas une anomalie de protocole.
2. Le réalisé météo est pricé, l'info vit dans la révision de prévision — notre pivot V45→V136 est le bon.
3. La simplicité gagne hors échantillon (Brignoli, Reeve-Vigfusson) — notre V11 (2 vars) est aligné avec la littérature.
4. Le mécanisme « prime d'assurance qui se dissipe sauf événement » est documenté sur le corn US (new-crop) — notre objet a un jumeau publié.
5. Les relations fondamentales sont instables entre régimes de politique (Carter et al.) — nos prudences V31+ (fedfunds suspect) sont justifiées.
