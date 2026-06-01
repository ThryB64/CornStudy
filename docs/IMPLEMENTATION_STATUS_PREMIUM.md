# État réel d'implémentation — arc de recherche « prime EMA/CBOT » (V8 → V79)

Table de référence maintenue de l'étude du basis/prime maïs Euronext EMA vs CBOT. Statut honnête par brique.
`RESEARCH_ONLY_NOT_TRADING`, baseline figée (`basis_z>1 → SHORT_PREMIUM`), holdout 2024 verrouillé, aucun fit
sur les 42 trades. Mise à jour : 2026-06-01.

**Légende** : ✅ validé/implémenté · ⚠️ partiel/explicatif · ❌ rejeté (négatif documenté) · 🔁 forward
(accumulation) · ⛔ data-gated.

## 1. Cœur — signal & règle figée
| Brique | Statut | Note |
|---|---|---|
| Baseline `basis_z>1 → SHORT_PREMIUM` (tiers MOD/STRONG/EXTREME) | ✅ | Figée, jamais optimisée sur 42 trades |
| Objectifs z→0.5 (prudent) / z→0 (complet), stop −20/−25 | ✅ | Indicatifs, research |
| Asymétrie short ≫ long premium | ✅ | V49 : 12.8 vs 8.2 €/t |
| Compression du basis haut (réversion) | ✅ | demi-vie ~17–54 j ; V12/V13 |
| **Robustesse de l'edge (V81)** | ✅ | LOYO PnL min +10.9 ; **hors crise 80% win / +11.2 €/t** ; survit coût 5 €/t (+7.8) ; aucune année > 23% du PnL → `EDGE_STABLE_NOT_DRIVEN_BY_ONE_YEAR` |

## 2. Mécanisme (le « pourquoi »)
| Brique | Statut | Résultat |
|---|---|---|
| Canal de compression (V70) | ✅ | CBOT_DRIVEN 45% (win 100%, +22.7) > EMA_DRIVEN 31% > ADVERSE 17% |
| CBOT porteur = pivot | ✅ | Compression + forte/complète/rapide ; CBOT_DRIVEN ↑ avec support |
| Time-to-reversion (V72, Kaplan-Meier) | ✅ | médiane 22 j→z0.5, 42 j→z0 ; HIGH support 29 j |
| Magnitude en classes (V57) | ✅ | MFE médiane 18→44 €/t avec CBOT_SUPPORT |
| Lead-lag CBOT→EMA / non-sync settlement (V44/V46) | ⚠️ | non-sync réel, non corrigeable en live |

## 3. Diagnostics (contexte, jamais des vetos)
| Brique | Statut | Note |
|---|---|---|
| ADVERSE_RISK v1 (V38) | ✅ | 3 signaux focalisés = meilleur séparateur |
| ADVERSE_RISK v2 (V64) | ⚠️ | couche EXPLICATION ; empiler dilue la séparation (négatif honnête) |
| CBOT_SUPPORT règle-basé (V41) | ✅ | pivot ; modèle OOF ne fait pas mieux |
| CBOT rebound engine (V65) | ❌ | direction CBOT non prédictible OOF (AUC ≤ 0.54) |
| PHYSICAL_TENSION courbe EMA (V54) | ⚠️🔁 | live-usable ; validation historique data-gated |
| SIGNAL_QUALITY (V43) | ✅ | ADVERSE_RISK × CBOT_SUPPORT |
| Objectif recommandé (V56) | ✅ | risk-efficient : −7.2 j d'exposition à PnL égal |
| Casebook ADVERSE (V50/V58) | ✅ | warning aurait flaggé prudent sur 5/7 pertes |
| Synthèse indicateur (V77) | ✅ | objet unique + bloc daily report |

## 4. Drivers / explication du basis
| Brique | Statut | Résultat |
|---|---|---|
| Substitution blé/maïs (V36/V37/V40) | ✅ | r~0.60, EU-spécifique |
| Ratio MATIF blé/maïs officiel (V52) | ⚠️🔁 | live OK (0.914) ; historique snapshot-only → forward |
| Macro (TTF, USD, éthanol) → basis (V16) | ❌ | R² OOF ≈ −0.25 |
| Production EU annuelle (V71) | ⚠️ | niveaux confondus par tendance ; compression ↓ en année rare |
| Localité géographique FR vs UE (V71b) | ⚠️ | détrendé : France driver le plus local (−0.174 vs −0.091) |
| Prime LOCALE (synthèse) | ✅ | ni macro, ni météo US, ni ENSO ne portent le basis directement |

## 5. Météo & climat
| Brique | Statut | Résultat |
|---|---|---|
| Météo réalisée moyenne → CBOT (V45) | ❌ | price-in (AUC 0.51) |
| Oracle météo moyenne (V48) | ❌ | AUC 0.49 même parfaite |
| Extrêmes météo (V51) | ⚠️ | queue réelle (+2.4%/10j) mais ANTICIPÉE ; persistance > intensité |
| Météo US → basis (V60) | ❌ | pas un driver (prime locale) |
| ENSO / La Niña → CBOT (V79) | ⚠️🔁 | **meilleur signal macro** : La Niña +5.4%/60j, robuste ex-crise ; WATCHLIST |
| Journal météo forward (pic + persistance) | 🔁 | V45, s'accumule via Action |

## 6. Données officielles & forward
| Brique | Statut | Note |
|---|---|---|
| EMA officiel Euronext (settlement) | ✅🔁 | snapshot append-only (V26/V27) |
| Calendrier de marché Euronext (V42) | ✅ | week-end/fériés, gate de fraîcheur |
| Journal signal forward (V27) | 🔁 | 2 jours, SHORT_PREMIUM_EXTREME |
| Journal MATIF (V52) / météo (V45) | 🔁 | append-only, GitHub Action |
| Rapport mensuel forward (V59) | ✅🔁 | THIN_DATA, se densifie 3/6/12 mois |
| Proxy vs officiel 40/90 j (V76) | 🔁 | à l'accumulation |
| Basis intraday aligné (V60-intraday) | ⛔ | bruit ~0.43 €/t mesuré ; backtest 2014+ indisponible |

## 7. Data-gated / non implémenté
| Brique | Statut | Raison |
|---|---|---|
| MARS rendements intra-campagne | ⛔ | bulletins PDF non parsés (vraie donnée EU manquante) |
| EU imports / Ukraine FOB (COMEXT) | ⛔ | **probé 2026-06-01** : `DS-045409` renvoie « not available for dissemination » → COMEXT hors API SDMX (bulk-download séparé). Confirmé inaccessible ici |
| Spreads inter-commodités (corn/soy, crude/corn, gas, corn/wheat) (V80) | ⚠️ | corn/wheat le plus lié au CBOT (−0.20), liens au basis tous <0.05 → canal CBOT, pas basis |
| Options / IV CBOT (V74) | ⛔ | pas de source |
| Archive révisions prévisions météo | ⛔ | Open-Meteo historical-forecast time-out |
| Décision finale (V78) | 🔁 | après 3–6 mois de forward |

## Conclusion d'étape
Le **mécanisme est cartographié et chiffré** : basis haut → compression surtout par rattrapage **CBOT-driven**
(V70), d'autant plus forte/rapide/complète que le CBOT est porté (V57/V72), horizon ~22 j (prudent)/~42 j
(complet). Les **échecs** = CBOT non porteur / prime modérée (V50/V58). La **prime est locale** (ni macro, ni
météo US, ni ENSO ne la portent ; substitution feed et offre **française** l'éclairent). Le **climat ENSO** est
le meilleur biais directionnel macro sur le **CBOT** (La Niña haussier, robuste ex-crise), pas sur le basis.
Aucun module n'est tradeable : statut research maintenu. La suite est **forward + données EU/officielles**,
pas de nouveaux modèles sur les mêmes 42 trades (sur-ajustement interdit).
