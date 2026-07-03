# Validation du parse WASDE vintage — 3 rapports historiques

Méthode : chaque valeur parsée doit apparaître textuellement dans le
fichier brut USDA (formats avec/sans séparateur de milliers testés).
Les valeurs vérifiées sont celles publiées À L'ÉPOQUE (vintage), pas
les valeurs révisées ultérieures.

## wasde2307.txt (été 2023-07)

| variable | valeur parsée | trouvée dans le brut |
|---|---|---|
| production | 15320.0 | ✅ |
| beginning_stocks | 1402.0 | ✅ |
| ending_stocks | 2262.0 | ✅ |
| exports | 2100.0 | ✅ |
| use_total | 14485.0 | ✅ |
| domestic_total | 12385.0 | ✅ |
| feed_and_residual | 5650.0 | ✅ |
| avg_farm_price | 4.8 | ✅ |

**Score : 8/8 valeurs retrouvées dans le brut.**

Extrait de la section corn du brut :

```
                  U.S. Feed Grain and Corn Supply and Use  1/
================================================================================
                               2021/22  2022/23 Est. 2023/24 Proj. 2023/24 Proj.
Item                                                           Jun           Jul
================================================================================
                                                 Million Acres
FEED GRAINS
Area Planted                     105.8         100.4        103.6*        106.8*
Area Harvested                    94.4          87.1         92.6*         95.6*

                                                 Metric Tons
Yield per Harvested Acre          4.21          4.11          4.34          4.23

                                               Million Metric Tons
Beginning Stocks                  34.0          37.6          39.4          38.0
Production                       397.5         358.2         401.7         404.2
Imports                            2.3           2.6           2.3           2.3
  Supply, Total                  433.8         398.3         443.5         444.5
Feed and Residual                148.6         141.6         147.3         147.6
Food, Seed & Industrial          177.1         174.4         176.5         176.6
  Domestic, Total                325.7         316.1         323.7         324.2
Exports                           70.5          44.3          59.4          59.9
  Use, Total                     396.2         360.3         383.1         384.1
Ending Stocks                     37.6          38.0          60.4          60.3

```

## wasde2311.txt (automne 2023-11)

| variable | valeur parsée | trouvée dans le brut |
|---|---|---|
| production | 15234.0 | ✅ |
| beginning_stocks | 1361.0 | ✅ |
| ending_stocks | 2156.0 | ✅ |
| exports | 2075.0 | ✅ |
| use_total | 14465.0 | ✅ |
| domestic_total | 12390.0 | ✅ |
| feed_and_residual | 5650.0 | ✅ |
| avg_farm_price | 4.85 | ✅ |

**Score : 8/8 valeurs retrouvées dans le brut.**

Extrait de la section corn du brut :

```
                  U.S. Feed Grain and Corn Supply and Use  1/
================================================================================
                               2021/22  2022/23 Est. 2023/24 Proj. 2023/24 Proj.
Item                                                           Oct           Nov
================================================================================
                                                 Million Acres
FEED GRAINS
Area Planted                     105.8         100.5         107.7         107.7
Area Harvested                    94.4          87.0          96.7          96.7

                                                 Metric Tons
Yield per Harvested Acre          4.21          4.11          4.10          4.13

                                               Million Metric Tons
Beginning Stocks                  34.0          37.6          37.0          37.0
Production                       397.5         357.8         396.6         400.0
Imports                            2.3           2.9           2.4           2.4
  Supply, Total                  433.8         398.3         436.0         439.4
Feed and Residual                148.7         144.2         146.0         147.0
Food, Seed & Industrial          177.0         172.1         175.9         176.5
  Domestic, Total                325.7         316.3         321.8         323.5
Exports                           70.5          45.0          57.8          58.4
  Use, Total                     396.2         361.3         379.6         381.9
Ending Stocks                     37.6          37.0          56.4          57.5

```

## wasde2401.txt (hiver/stocks 2024-01)

| variable | valeur parsée | trouvée dans le brut |
|---|---|---|
| production | 15342.0 | ✅ |
| beginning_stocks | 1360.0 | ✅ |
| ending_stocks | 2162.0 | ✅ |
| exports | 2100.0 | ✅ |
| use_total | 14565.0 | ✅ |
| domestic_total | 12465.0 | ✅ |
| feed_and_residual | 5675.0 | ✅ |
| avg_farm_price | 4.8 | ✅ |

**Score : 8/8 valeurs retrouvées dans le brut.**

Extrait de la section corn du brut :

```
                  U.S. Feed Grain and Corn Supply and Use  1/
================================================================================
                               2021/22  2022/23 Est. 2023/24 Proj. 2023/24 Proj.
Item                                                           Dec           Jan
================================================================================
                                                 Million Acres
FEED GRAINS
Area Planted                     105.5         100.0         107.7         107.5
Area Harvested                    94.1          86.6          96.7          96.0

                                                 Metric Tons
Yield per Harvested Acre          4.21          4.11          4.13          4.19

                                               Million Metric Tons
Beginning Stocks                  34.0          37.5          37.0          37.1
Production                       396.0         356.1         400.0         402.6
Imports                            2.3           2.9           2.4           2.4
  Supply, Total                  432.4         396.5         439.4         442.1
Feed and Residual                147.4         142.3         147.0         147.6
Food, Seed & Industrial          177.0         172.1         176.5         177.5
  Domestic, Total                324.4         314.4         323.5         325.1
Exports                           70.5          45.0          59.0          59.3
  Use, Total                     394.9         359.4         382.5         384.4
Ending Stocks                     37.5          37.1          56.9          57.7

```

## Synthèse

- wasde2307.txt : OK, 8/8
- wasde2311.txt : OK, 8/8
- wasde2401.txt : OK, 8/8

**Verdict de validation : VALIDATED**
