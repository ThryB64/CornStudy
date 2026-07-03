# Guide utilisateur — indicateur Euronext de vente / risque

Version : `euronext_indicator_v1`. Date : 2026-06-13. **Aide à la décision de vente, pas une
prévision de prix ni un bot.** ⚠️ Le prix Euronext utilisé est à **~97 % un proxy**
(cf. `EURONEXT_DATA_AUDIT.md`) : tout est **illustratif**, verdict **RESEARCH_ONLY**.

## 1. Lancer
```bash
python -m mais.cli euronext-indicator
# ou
make euronext-indicator
```
(Le module applique le score de vente CBOT à l'historique de prix Euronext et régénère tous
les fichiers.)

## 2. Où trouver les résultats
Dans `artefacts/final_euronext_indicator/` :
- **`euronext_indicator_dashboard.html`** — dashboard interactif (à ouvrir dans un navigateur).
- `euronext_indicator_history.csv` — historique complet (prix + scores + retours futurs).
- `euronext_indicator_latest.json` — dernier signal.
- `euronext_indicator_metrics.csv` — métriques par horizon + par recommandation.
- `euronext_backtest_{decisions,summary,by_campaign}.csv` — backtest agricole.
- `euronext_indicator_feature_dictionary.csv` — dictionnaire des colonnes.

Rapports : `docs/FINAL_EURONEXT_INDICATOR_REPORT.md`, `docs/FINAL_EURONEXT_INDICATOR_BACKTEST.md`.

## 3. Lire le dashboard HTML
10 graphiques interactifs (zoom, survol, légende cliquable) :
1. **Prix Euronext + recommandations** — points colorés (rouge=SELL_PARTIAL, vert=WAIT,
   gris=WATCH, orange=RISK_HIGH). Regarder si les rouges précèdent des baisses.
2. Score global de vente (= risque de baisse H90) avec seuils.
3. Risque de baisse H90.
4. Composantes (WASDE, Crop, Volatilité, Régime, Confiance).
5-6. Retour Euronext futur moyen après chaque recommandation.
7. Matrice de confusion directionnelle H90.
8. Table des derniers signaux.
9. Backtest agricole (prix moyen & écarts aux baselines).
10. Résultat par campagne (calendar / Sep-Aug / Oct-Sep).

## 4. Lire les recommandations
| Décision | Sens |
|---|---|
| **SELL_PARTIAL** | risque de baisse H90 + confiance correcte → vendre une fraction |
| **WAIT** | pas de risque baissier (hausse probable) → attendre |
| **WATCH** | signal faible/contradictoire → surveiller |
| **RISK_HIGH** | volatilité prévue très élevée → prudence, signal peu fiable |
| **NO_SIGNAL** | données insuffisantes |

Jamais de `BUY` ni de `SHORT`.

## 5. Lire les scores
- `downside_risk_h90` : probabilité de **baisse** à ~90 séances (cœur du signal de vente).
- `confidence_score` : 0-1, fiabilité (cohérence H40/H90, régime, vol).
- `volatility_risk_score` : 0-1, niveau de risque de volatilité (percentile gelé ≤2023).
- `final_sale_score` : pression de vente globale (= `downside_risk_h90`).
- `score_stale` : **1 = score CBOT figé** (au-delà de la fin des données CBOT, 2025-07-25) →
  signal **non à jour**, ne pas l'utiliser tel quel.

## 6. Ce qu'il ne faut PAS faire
- Ne pas vendre **toute** la récolte sur un seul signal.
- Ne pas l'utiliser comme **bot** automatique.
- Ne pas ignorer le **prix local** ni le **basis** (le score est CBOT, pas votre prix ferme).
- Ne pas ignorer vos **besoins de trésorerie** ni vos contraintes de stockage.
- Ne pas oublier que les données sont un **proxy** et le signal **fragile** (RESEARCH_ONLY).
