# Étude du maïs CBOT & Euronext — synthèse maîtresse (point d'entrée unique)

Date : 2026-06-14. Ce document relie **tout** le parcours de l'étude et donne la conclusion
honnête de bout en bout. Pour le détail, suivre les liens.

## 1. La question de départ
Peut-on, avec des données **publiques gratuites**, prédire / aider à décider sur le cours du
maïs **CBOT** (tendance mondiale) puis **Euronext** (prime européenne via le basis) ?

## 2. Le parcours (étapes)
| Étape | Objet | Verdict / livrable |
|---|---|---|
| 1-2 | Audit + analyse de 12 repos, 131 fiches sources, 46 idées | base de recherche |
| 3 (P0) | Benchmarks RW, roll, WASDE vintage | RW imbattable ; vintage anti-fuite |
| 4 (P1) | Météo, WASDE, COT, courbe, éthanol, basis, crop condition | **aucun KEEP** ; 2 IMPROVE (WASDE s2u, Crop) |
| 5 (P2) | Modèles directionnels, volatilité, régimes, SHAP, stacking, DL | direction modeste + vol solide ; complexité rejetée |
| 5 bis | Correction fuite `target_date` (jours calendaires → lignes de marché) | tous verdicts survivent |
| 6 | Synthèse + décision stratégique | **Option B** : pivot prix → score de vente |
| 7 | Score de vente CBOT (intégration, holdout, backtest) | **FRAGILE** |
| 7 + revue | Corrections (HAR purge, cooldown, campagnes) | FRAGILE confirmé |
| **Viz** | **Indicateur Euronext visuel** (dashboard HTML) | **RESEARCH_ONLY** |

## 3. Les trois conclusions qui tiennent
1. **Le prix exact n'est pas prédictible** avec les données gratuites : la random walk est
   imbattable en RMSE (0/36 couples benchmark×horizon, DM p<0.10). → on a **abandonné la
   prévision de prix**.
2. **Il existe un signal directionnel modeste** à H40-H90 : Crop Condition (US) @ H90 et WASDE
   stocks-to-use @ H40, plus une **volatilité prévisible** (HAR/EGARCH) servant de gate de
   risque. C'est un **score de vente**, pas un modèle de prix.
3. **Ce signal est fragile** : en recherche, DM non significatif ; sur le holdout 2024+ il bat
   la random walk (DA 0.686, AUC 0.816) **mais pas une simple saisonnalité** ; le backtest
   dépend du cadrage. Sur **Euronext** (prix à ~97 % proxy), les recommandations ordonnent
   correctement les retours futurs (SELL_PARTIAL → −5.8 % H90, WAIT → +5.1 %) **mais** l'AUC
   hors échantillon est faible (0.561).

## 4. Les livrables
- **Score de vente CBOT** : `mais.indicator.cbot_sale_score*`, `config/cbot_sale_score.yaml`,
  CLI `mais sale-score --holdout`. Statut **FRAGILE**.
  → `docs/FINAL_CBOT_SALE_SCORE_STUDY.md` (+ PROTOCOL/LIMITS/USER_GUIDE/TECHNICAL_SUMMARY),
  `docs/FINAL_HOLDOUT_2024_VALIDATION.md`, `docs/FINAL_FARMER_DECISION_BACKTEST.md`,
  `docs/FINAL_CBOT_STUDY_CLOSURE.md`.
- **Indicateur Euronext visuel** : `mais.indicator.euronext_indicator_*`,
  `config/euronext_indicator.yaml`, CLI `mais euronext-indicator`, dashboard HTML interactif
  (Plotly, autonome). Statut **RESEARCH_ONLY**.
  → `docs/EURONEXT_DATA_AUDIT.md`, `docs/FINAL_EURONEXT_INDICATOR_REPORT.md`,
  `docs/FINAL_EURONEXT_INDICATOR_BACKTEST.md`, `docs/EURONEXT_INDICATOR_USER_GUIDE.md`.
- **Recherche externe** : `external_research/` (26 expériences EXT, matrices de verdicts).
  → `external_research/docs/step6_final_synthesis.md`.

## 5. Ce qui est gardé / rejeté / bloqué
- **Gardé** : Crop Condition @ H90, WASDE stocks-to-use @ H40, saison, volatilité HAR/EGARCH,
  régimes (confiance), pipeline vintage WASDE, hygiène de roll.
- **Rejeté** : météo réalisée, surprise WASDE proxy, COT, éthanol proxy, trend-following,
  stacking, deep learning.
- **Bloqué (données manquantes)** : courbe futures par maturité, basis / cash bids, OU
  mean-reversion, vraie surprise WASDE (consensus), météo prévue, options (vol implicite),
  satellite, **settlements officiels Euronext** (la série actuelle est à 97 % proxy).

## 6. Limites transverses (à ne pas oublier)
- Edge **modeste** et **dépendant du cadrage** (campagne, cooldown, horizon).
- **Régimes post-hoc** → confiance seulement.
- **Données figées** : CBOT → 2025-07-25, Euronext → 2026-05-20 (mais score CBOT figé au-delà,
  `score_stale`). Le dernier signal n'est pas exploitable en l'état.
- Score **CBOT** appliqué à **Euronext** : basis et EUR/USD non intégrés ; prix Euronext proxy.
- **Pas un bot, pas un conseil de vente opérationnel.** Aide à la décision, à valider en forward.

## 7. Comment relancer
```bash
python -m mais.cli sale-score --holdout      # score de vente CBOT + validation + backtest
python -m mais.cli euronext-indicator         # indicateur Euronext + dashboard HTML
# dashboard : artefacts/final_euronext_indicator/euronext_indicator_dashboard.html
```

## 8. Pour aller plus loin (seule voie de progrès)
1. **Mettre à jour les données** (CBOT, WASDE, Crop Condition, Euronext) jusqu'à aujourd'hui.
2. **Valider en forward** les scores sur plusieurs campagnes, sans retoucher les paramètres.
3. **Acquérir des données** : gratuites débloquantes (EUR/USD FRED, prévisions météo forward,
   exports USDA FAS) ; puis payantes (consensus WASDE, options/vol implicite, courbe par
   contrat, **settlements officiels Euronext**, prix physiques FOB).
Ne **pas** complexifier le modèle sur les données actuelles : le prochain palier viendra des
**données**, pas d'un modèle plus gros.

## 9. Bottom line
> L'étude ne valide pas la prédiction du prix du maïs. Elle livre un **indicateur d'aide à la
> vente direction/risque H40-H90**, **fragile** sur CBOT et **RESEARCH_ONLY** sur Euronext
> (données proxy), entièrement documenté, testé et visualisable. C'est une **conclusion de
> recherche honnête**, pas un modèle miracle — et une base saine pour une éventuelle phase de
> validation forward avec de meilleures données.
