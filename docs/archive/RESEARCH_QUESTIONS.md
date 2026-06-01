# Questions de recherche — Étude professionnelle du maïs

## Question centrale

> **Quels facteurs expliquent le prix du maïs CBOT, et peut-on utiliser ces facteurs pour prévoir son évolution à J+5, J+10, J+20 et J+30 afin d'améliorer les décisions de vente des agriculteurs ?**

Cette question est claire, professionnelle, défendable devant un comité scientifique ou un partenaire agricole.

---

## Questions de recherche secondaires

### Q1 — Quels facteurs expliquent le prix du maïs ?

**Hypothèse centrale :**
Le prix du maïs CBOT est déterminé par l'intersection de plusieurs forces : le bilan physique offre/demande (WASDE), les conditions de production en cours (météo, crop progress), la demande dérivée (éthanol, exports), la compétitivité internationale (dollar, Brésil), et le positionnement spéculatif (COT).

**Variables à tester :**

| Famille | Variables |
|---|---|
| Marché | Futures, volume, OI, spreads, basis |
| Météo | Température, précipitations, GDD, stress hydrique |
| WASDE | Stocks-to-use, ending stocks, supply, yield, prix ferme |
| Production | Crop progress, crop condition, Drought Monitor |
| Éthanol | Production, stocks, marges, gasoline |
| Exports | Export sales, shipments, inspections, China demand |
| Macro | Dollar (DXY), taux Fed, inflation, pétrole |
| COT | Managed money net, commercial net, OI extrêmes |
| Basis | Local cash price, Gulf basis, ethanol plant basis |
| Saisonnalité | Fourier, saisons agronomiques, calendrier USDA |

**Méthode de réponse :**
- Ablation study par famille : retirer une famille et mesurer le Δ RMSE out-of-sample
- SHAP global par famille sur LightGBM
- Stabilité de l'importance dans le temps (walk-forward sur splits)

---

### Q2 — Les facteurs ont-ils le même poids selon l'horizon ?

**Hypothèse :**

| Horizon | Facteurs dominants attendus |
|---|---|
| J+5 | Momentum prix, surprises WASDE récentes, COT, basis |
| J+10 | Météo, volatilité, export sales, éthanol |
| J+20 | Stocks, crop condition, weather stress, macro |
| J+30 | Fondamentaux WASDE, production monde, dollar, exports annuels |

**Méthode de réponse :**
- Produire une matrice importance × horizon
- Comparer les SHAP rankings pour chaque horizon
- Tester si un modèle entraîné sur J+20 donne de bonnes prédictions J+5 (effet horizon cross-training)

**Indicateur de succès :**
La matrice montre des profils différents statistiquement significatifs entre J+5 et J+30.

---

### Q3 — Les facteurs changent-ils selon la période de l'année ?

**Hypothèse :**

| Saison agronomique | Facteurs dominants |
|---|---|
| Semis (avril-mai) | Superficie, météo précoce, conditions de semis |
| Croissance (juin-juillet) | Météo (chaleur, sécheresse), Crop Condition |
| Pollinisation (mi-juillet–août) | Stress thermique critique, GDD |
| Récolte (sept-oct) | Crop Progress, yield final, stocks nouveaux |
| Post-récolte (nov-mars) | Stocks, exports, éthanol, compétitivité monde |

**Méthode de réponse :**
- Entraîner des modèles par saison agronomique et comparer les importances
- Tester des termes d'interaction saison × facteur dans Ridge pour capturer effets non-linéaires
- Comparer les performances du modèle global vs modèles par saison

**Indicateur de succès :**
Les importances SHAP montrent des profils saisonniers distincts sur au moins 2 familles de facteurs.

---

### Q4 — Les facteurs changent-ils selon le régime de marché ?

**Régimes identifiés :**

| Régime | Définition |
|---|---|
| Haussier (bull) | Tendance positive, volatilité modérée, stocks bas |
| Baissier (bear) | Tendance négative, stocks élevés, dollar fort |
| Neutre (range) | Oscillation sans tendance claire |
| Stress météo | Volatilité élevée pendant la saison de croissance |
| Post-WASDE | Réaction aux rapports USDA dans les 3 jours suivants |

**Hypothèses :**
- En marché tendu (stocks bas), une mauvaise météo a plus d'impact marginal.
- En stocks élevés, la météo compte moins.
- En dollar fort, les exports pèsent plus dans la direction baissière.
- En régime haussier, le COT (managed money) amplifie les mouvements.

**Méthode de réponse :**
- Markov-switching 3 états pour identifier les régimes (implémenté dans `_build_regimes()`)
- SHAP conditionnel par régime
- Tester des interactions régime × facteur dans le métamodèle

---

### Q5 — Les modèles battent-ils des baselines simples ?

**Règle impérative :** un modèle ML n'est utile que s'il bat des références testées et documentées.

**Baselines à tester :**

| Baseline | Définition | Justification |
|---|---|---|
| Zéro return | Prédit aucun changement | Référence minimale |
| Historical mean | Moyenne des retours historiques | Référence statistique |
| Seasonal naive | Retour moyen du même mois/semaine | Capture saisonnalité |
| Momentum simple | Signe du retour sur les 20 derniers jours | Règle simple de trend-following |
| Mean reversion | Inverse du retour récent | Règle simple de contrarian |

**Métriques de comparaison :**

| Métrique | Justification |
|---|---|
| RMSE | Erreur quadratique standard |
| MAE | Robuste aux extrêmes |
| DA (Directional Accuracy) | Pertinent pour la décision SELL/STORE |
| R² out-of-sample | Proportion de variance expliquée |
| Hit ratio sur seuils 1% / 3% | Détection de gros mouvements |

**Indicateur de succès :**
Le meilleur modèle bat toutes les baselines sur au moins 3 métriques pour au moins 2 horizons.

---

### Q6 — Le système améliore-t-il réellement la rentabilité agricole ?

**C'est la question finale et la plus importante.**

Un modèle qui bat les baselines statistiques mais ne génère pas de gain économique n'est pas utile.

**Métriques économiques cibles :**

| Métrique | Interprétation |
|---|---|
| Revenu moyen $/bu | Prix moyen de vente obtenu |
| Revenu moyen $/acre | Revenu total en tenant compte des volumes |
| Gain % vs vente récolte | Amélioration vs stratégie la plus simple |
| Gain % vs vente mensuelle | Amélioration vs stratégie régulière |
| % années où le système gagne | Fiabilité |
| Pire année (drawdown) | Risque |
| Distance au prix maximum annuel | Capture du prix optimal |
| Regret vs perfect hindsight | Métrique synthétique clé |

**Métrique principale retenue :**

```
regret_t = prix_maximum_annuel_t - prix_obtenu_stratégie_t

capture_rate_t = prix_obtenu_stratégie_t / prix_maximum_annuel_t

capture_rate_moyen = moyenne sur toutes les années du backtest
```

**Interprétation cible :**

> "Notre système capture en moyenne 82 % du prix maximum annuel, contre 68 % pour la vente récolte et 74 % pour la vente mensuelle."

Cette phrase est le résultat final visé.

---

## Cadre expérimental global

### Période de données

| Période | Usage |
|---|---|
| 2000–2014 | Entraînement initial (14 ans) |
| 2015–2020 | Walk-forward test + calibration |
| 2021–2025 | Validation finale out-of-sample |

### Protocole walk-forward

- Train initial : 8 ans minimum
- Embargo : égal à l'horizon
- Step : 21 jours
- Recalibration : à chaque step
- Anti-leakage : `shift(1)` sur toutes les sources fondamentales

### Condition de publication des résultats

Un résultat n'est reporté dans le rapport final que si :
1. Il est obtenu en walk-forward out-of-sample.
2. Il n'y a aucune fuite de données (audit automatique passé).
3. Il bat au minimum la baseline "zéro return" sur RMSE.
4. La période de test est d'au moins 3 ans.
