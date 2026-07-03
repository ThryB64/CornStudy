# Avancement de l'analyse des sources — Étape 2

Date : 2026-06-12

## Sources analysées (fiches remplies) : 25

### Repositories (9)

| Fiche | Source | Verdict |
|---|---|---|
| repo003 | mindymallory/PriceAnalysis | Cadre de référence — utiliser immédiatement |
| repo004 | mindymallory/RollFutures | À tester immédiatement (EXT006) |
| repo005 | NDelventhal/cot_reports | À tester immédiatement (EXT003, calendrier publication d'abord) |
| fdfoneill-wasdeparser | wasdeparser | À tester immédiatement (EXT026) — **repo à cloner** |
| repo001 | PrayusShrestha/crop-price-prediction | Inspiration (négative) seulement — déclassé |
| repo002 | squeeze-team/AgriJedi | Inspiration seulement (catalogue de sources EU) |
| repo006 | YavuzAkbay/Ornstein-Uhlenbeck | Plus tard (EXT012) |
| repo007 | chrism2671/PyTrendFollow | Plus tard (EXT011) |
| repo011 | cchallu/nbeatsx | Plus tard, conditionnel (EXT016) |

### Papers / rapports / mémoires (14)

| Fiche | Source | Verdict |
|---|---|---|
| paper003 | USDA ERS — public information | Très haute (EXT007/EXT008) |
| paper004 | Isengildina-Massa et al. — WASDE/NASS | Très haute (EXT007) |
| paper005 | Huang, Serra, Garcia — USDA électronique | Très haute (garde-fou réalisme) |
| what-do-we-know… | NCGA 2022 — précision/impact USDA | Haute (filtre EXT032) |
| the-value-of-usda-crop-progress… | Lehecka 2014 | Très haute (EXT027 — la plus actionnable) |
| weather-…-not-enough | Taylor 2010 | Haute (design 2 étages EXT041) |
| paper007 | Li, Hayes, Jacobs — weather premium | Très haute (EXT018, parallèle avec notre prime) |
| paper008 | Janzen — new-crop premium | Très haute (point d'entrée EXT018) |
| paper001 | Singh 2020 — météo/sol ML | Très haute (design features EXT001/002 ; PDF à récupérer) |
| corn-futures-…-weather-forecast-archive | CropProphet 2026 | Très haute pour l'idée, nulle pour les chiffres (EXT033) |
| paper015 | Hu, Mallory, Serra, Garcia — nearby/deferred | Très haute (EXT005) |
| paper017 | Mallory, Hayes, Irwin — corn/éthanol/stockage | Très haute (EXT004, H60+) |
| corn-crush-hedging… | Dahlgran & Gupta 2019 | Haute (confirme la prime locale, EXT029 descriptif) |
| commodity-storage-…-biofuel | Carter, Rausser, Smith 2017 | Haute (garde-fou régimes EXT031/EXT024) |
| distillers-grains… | Gertner 2021 | Moyenne-haute, data-gated DDG (EXT030) |
| paper016 | Penone et al. — transmission UE | Haute (EXT013/EXT044 — le plus proche de notre objet) |
| paper027 | Reeve & Vigfusson — RW benchmark | Très haute (EXT025 — à exécuter en premier) |
| paper002 | Brignoli et al. — ML grains | Haute (référence protocole) |
| paper029 | AGRICAF (Zelingher) | Très haute (choix de variables ; test inédit prime EXT043) |
| paper031 | Drachal — DMA/BMA | Haute (diagnostic EXT014) |
| paper009 | Musunuru et al. — GARCH corn | Haute (EXT009, inverse leverage) |
| paper020 | NBEATSx texte Dalian | Moyenne-haute (méthode SHAP-dans-le-split) |
| paper018 | Livre Price Analysis | Très haute (consolidée avec repo003) |

### Patents (2)

| Fiche | Source | Verdict |
|---|---|---|
| patent007 | US9087312B1 séchage/stockage | Plus tard (raffinement full carry EXT005) |
| patent010 | AU2011202458B8 basis futures | Inspiration seulement |

## Sources KEEP_CORE restantes (non encore fichées) : ~24

Par ordre de priorité résiduelle :
1. **Bloc événements complémentaire** : when-does-usda (2021), do-corn-options, exploring-calendar-WASDE, reaction-US-Brazil, simulating-crop-progress (Tsiboe 2023 — partiellement exploitée via la fiche Lehecka).
2. **Comparables corn** : cstainbrook-corn-futures-capstone, seemakanuri, helios-challenge, ccaspar-weather-commodities, facundoallia-calendar-spread, ai-driven-news (2026).
3. **Satellite** : can-satellite-data (Piette 2019), sentinel-2 — bloc 4, différé.
4. PAPER006 (consensus vol), PAPER011 (Halonen — exploité indirectement via EXT024), PAPER012/PAPER013 (extrêmes météo), PAPER014 (price discovery US).

Ces fiches seront remplies au fil de l'étape 3, quand l'EXT correspondant s'ouvre (protocole : une source à la fois, au moment où on en a besoin).

## KEEP_METHOD analysées : 7/22 (les plus utiles)

OU, PyTrendFollow, nbeatsx, Drachal, Musunuru, Brignoli (protocole), Wang NBEATSx-texte. Restantes (PAPER010/037/039/041/042, repos trend secondaires, CY-Bench, regime-bench…) : à ficher quand le bloc benchmark correspondant s'ouvre.

## Problèmes rencontrés

1. **PDF non disponibles localement** : les fiches papers seed sont fondées sur les abstracts du catalogue + la connaissance de la littérature publiée. Chaque fiche le signale en frontmatter (`note:`). Les chiffres précis sont marqués « à vérifier » — à confirmer sur les PDF avant toute citation dans le rapport professionnel. PDF prioritaires à récupérer : Singh 2020 (thèse), Brignoli et al., AGRICAF.
2. **wasdeparser non cloné** (découvert après la passe seed) — premier geste de l'étape 3.
3. **Doublons confirmés** (4) : fiches consolidées côté seed (PAPER001/007/015/016) ; les fiches découvertes correspondantes restent des templates vides à pointer vers le seed lors du prochain refresh du catalogue.
4. **Calendriers de publication manquants** (COT vendredi, USDA élargi) : prérequis durs identifiés, intégrés comme premières tâches des EXT003/EXT007.
