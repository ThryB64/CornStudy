# Étape 6 — Décision stratégique finale

Date : 2026-06-13. Trancher entre trois options, preuves à l'appui. Aucune intégration codée.

## Les trois options

- **Option A — Continuer la prédiction pure du prix.** Condition : modèles battent clairement
  la RW en RMSE/MAE, stables, logique économique.
- **Option B — Abandonner le prix, basculer vers un score de vente / risque / direction.**
  Condition : pas de gain RMSE, mais signal directionnel/régime/volatilité utile pour la
  décision agricole.
- **Option C — Stopper avec les données actuelles et chercher de nouvelles données.**
  Condition : aucun signal robuste, même direction/risque insuffisant.

## Décision : **OPTION B** (avec un volet C ciblé sur les familles bloquées)

### Justification
1. **Option A éliminée par les faits.** EXT025 : la random walk n'est battue par **aucun**
   des 36 couples benchmark×horizon (DM p<0.10) ; tous les fondamentaux **dégradent** le RMSE
   (WASDE niveaux jusqu'à +194 %, météo R² OOS jusqu'à −3,4). **La prédiction pure du prix
   n'est pas validée avec les données actuelles.**
2. **Option B soutenue par un signal réel, modeste et stable.** En cadrage **direction** :
   - Crop Condition @ H90 : **DA 0,669 / AUC 0,724 / Brier 0,218**, +6,6 pts vs marché, stable
     2 moitiés (0,632 / 0,707) — corrigé étape 5 bis, conclusion renforcée.
   - WASDE stocks-to-use : signal d'état d'offre lent, +6,1 pts DA H20, stable.
   - EXT015 : ces variables ressortent train-only **16/16 ans** (parcimonie validée).
   - **Volatilité** : HAR/EGARCH battent la RW de vol (−22 à −24 %) ; **filtre de vol**
     actionnable (écarte le régime où le signal s'inverse, DA 0,669 → 0,699).
   - **Régimes** : confiance modulable (fort en uptrend/low-vol/bilan extrême).
   Ces briques composent un **score de vente/direction/risque H40-H90** utile à une décision
   de **commercialisation agricole** (vendre / attendre / surveiller), pas à un trading rapide.
3. **Volet C ciblé, pas global.** Plusieurs familles à fort prior sont **DATA_BLOCKED**
   (courbe futures EXT005, basis/VECM EXT013, OU EXT012) ou bloquées par une donnée précise
   (consensus WASDE EXT008, prévisions météo forward EXT033). On ne « stoppe » pas tout : on
   **livre le score B** et on **source** ces données pour rouvrir les pistes bloquées.

### Preuves clés (corrigées)
| Brique | Preuve | Source |
|---|---|---|
| Prix non prédictible | RW 0/36 DM | EXT025 |
| Direction H90 | crop DA 0,669 / AUC 0,724, stable | EXT024 (corrigé) |
| Variables stables | top-6 16/16 ans > RF | EXT015 |
| Volatilité | HAR/EGARCH −22 à −24 % RMSE | EXT009/EXT010 |
| Gate de risque | filtre vol 0,669 → 0,699 | EXT009 |
| Parcimonie | stacking/DL sur-apprennent | EXT050/EXT016 |

### Risques et limites
- **Edge modeste** : DM non significatif, IC bootstrap chevauchant le marché seul → **score de
  confiance**, pas signal binaire fort. Ne pas surpromettre.
- **Régime post-hoc** (EXT017) : à valider en forward avant production.
- **Holdout 2024+ jamais utilisé** : la validation finale reste à faire (ticket projet, règle
  12) — c'est l'épreuve décisive avant toute mise en service.
- **Couverture partielle** : sans courbe/basis/options, une partie de l'information de marché
  reste hors de portée.

### Ce que B n'est PAS
Pas un bot de trading autonome. **Le signal peut être utile pour un indicateur d'aide à la
décision, pas pour un bot autonome.** Sortie = score + confiance + drapeau de risque.

## Prochaine étape recommandée
**Étape 7 = formaliser le score de vente H40-H90** (Crop Condition + WASDE stocks-to-use +
saison, conditionné régime, gaté vol HAR/EGARCH), en **walk-forward strict**, puis **valider
sur le holdout 2024+** (ticket projet humain, règle 12) et un **backtest décisionnel**
(vendre/attendre) coût-aware. En parallèle, **sourcer** eurusd quotidien, contrats CBOT par
maturité et archive de prévisions météo forward pour rouvrir EXT005/EXT012/EXT013/EXT033.
Détails dans `step6_integration_recommendation_for_step7.md`.
