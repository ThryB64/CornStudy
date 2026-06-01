# Pipeline quotidien — Production

## Objectif

Chaque jour (jour de bourse ouvert), le système doit mettre à jour automatiquement les données, recalculer les prédictions, et produire un rapport pour l'agriculteur.

---

## Vue d'ensemble du pipeline

```
Chaque matin (6h-7h) :

1. COLLECT      — Nouvelles données disponibles
2. VALIDATE     — Qualité et fraîcheur des données
3. FEATURES     — Mise à jour features.parquet (incrément)
4. FACTORS      — Mise à jour factors.parquet
5. PREDICT      — Prédictions J+5/J+10/J+20/J+30
6. REGIMES      — Détection régime actuel
7. CQR          — Intervalles calibrés
8. SHAP         — Explication locale du jour
9. DECISION     — Recommandation SELL/STORE/WAIT
10. SNAPSHOT    — Sauvegarde état du jour
11. REPORT      — Rapport quotidien Markdown
12. VALIDATE_PAST — Comparer prédictions passées avec réalité
```

---

## Étape 1 — Collecte quotidienne

**Commande :** `make daily` ou `mais ops daily`

**Sources mises à jour chaque jour :**

| Source | Fréquence | Heure dispo | Action |
|---|---|---|---|
| Prix CBOT | Quotidien | 18h30 ET veille | `mais collect yfinance` |
| Météo Corn Belt | Quotidien | 6h | `mais collect openmeteo` |
| Dollar, pétrole | Quotidien | 18h30 ET veille | Inclus dans yfinance |

**Sources mises à jour selon calendrier :**

| Source | Fréquence | Publication | Action |
|---|---|---|---|
| Export Sales USDA | Hebdo (jeudi 8h30 ET) | Jeudi | `mais collect fas` |
| EIA Éthanol | Hebdo (mercredi 10h30 ET) | Mercredi | `mais collect eia` |
| CFTC COT | Hebdo (vendredi 15h30 ET) | Vendredi | `mais collect cot` |
| Crop Progress | Hebdo (lundi 16h ET, saison) | Lundi | `mais collect nass-crop` |
| Drought Monitor | Hebdo (jeudi) | Jeudi | `mais collect drought` |
| WASDE | Mensuel (8h30 ET) | Mardi ou jeudi | `mais collect wasde` |
| FRED | Mensuel | Variable | `mais collect fred` |

**Règle de scheduling :** le pipeline quotidien doit détecter automatiquement si une source hebdomadaire/mensuelle est dûe et la collecter. Pas de collecte inutile si les données n'ont pas changé.

---

## Étape 2 — Validation des données

**Vérifications obligatoires avant de continuer :**

```python
validation_checks = [
    "prix CBOT disponible pour hier",
    "pas de gap > 3 jours dans les prix",
    "météo disponible pour les 10 derniers états Corn Belt",
    "anti-leakage audit pass (corrélation |r| < 0.97 sur toutes features)",
    "pas de features entièrement NaN",
]
```

Si une vérification échoue :
- Log warning avec détail
- Continuer avec les données disponibles (pas de blocage si non critique)
- Alerter si le prix CBOT est manquant (critique)

---

## Étape 3–4 — Mise à jour features et facteurs

**Mode incrémental :** ne recalculer que pour les nouvelles dates.

```python
# Si features.parquet existe et est récent
last_feature_date = features_df["Date"].max()
new_data = collect_since(last_feature_date)
if new_data.empty:
    log.info("features_up_to_date")
else:
    new_features = build_features_incremental(new_data)
    features_df = pd.concat([features_df, new_features])
    write_parquet(features_df, FEATURES_PARQUET)
```

**Mode complet :** `make features` rebuilt tout depuis les données brutes.

---

## Étape 5–8 — Prédictions, régimes, intervalles, SHAP

**Ces étapes utilisent les modèles entraînés dans la dernière étude.**

```python
from mais.meta.stacking import load_stacking_model
from mais.meta.cqr import CQRModel

stacker = load_stacking_model()  # modèle entraîné en mémoire
today_features = get_today_features()

# Prédictions
preds = {}
for horizon in [5, 10, 20, 30]:
    preds[horizon] = stacker.predict(today_features, horizon=horizon)

# Intervalles CQR
cqr = CQRModel.load()
intervals = cqr.predict_intervals(today_features)

# Régime
regime = get_current_regime()

# SHAP local
shap_explanation = explain_today(today_features, stacker)
```

**Les modèles ne sont pas ré-entraînés chaque jour.** Ils sont ré-entraînés lors du `make study` hebdomadaire ou mensuel.

---

## Étape 9 — Décision SELL/STORE/WAIT

**Inputs de la décision :**

| Input | Valeur exemple |
|---|---|
| `pred_return_h20` | +0.031 (hausse de 3.1% attendue à J+20) |
| `interval_q10_h20` | -0.018 (pessimiste : -1.8%) |
| `interval_q90_h20` | +0.079 (optimiste : +7.9%) |
| `regime` | "bull" |
| `realized_vol_60d` | 0.22 (22% annualisé) |
| `days_to_wasde` | 8 (rapport USDA dans 8 jours) |

**Règles de décision (config/decision.yaml) :**

```yaml
sell:
  condition: "pred_return_h20 < -0.02 OR (regime == 'bear' AND pred_return_h5 < -0.01)"
  fraction: 0.5

store:
  condition: "pred_return_h20 > 0.03 AND interval_q10_h20 > 0.0"
  fraction: 1.0

wait:
  condition: "default"
  fraction: 0.0
```

---

## Étape 10 — Snapshot quotidien

```python
snapshot = {
    "date": today,
    "price_cbot": current_price,
    "regime": regime,
    "predictions": {
        "h5": preds[5], "h10": preds[10], "h20": preds[20], "h30": preds[30]
    },
    "intervals": {
        "h20_q10": intervals["q_lo"]["h20"],
        "h20_q90": intervals["q_hi"]["h20"],
    },
    "shap_top3_up": shap_explanation["top_positive"][:3],
    "shap_top3_down": shap_explanation["top_negative"][:3],
    "decision": decision,
    "confidence": confidence_score,
}
write_json(snapshot, f"data/snapshots/{today}.json")
```

---

## Étape 11 — Rapport quotidien

**Format du rapport (`data/reports/YYYY-MM-DD.md`) :**

```markdown
# Rapport maïs — 2026-05-09

## Prix et régime
- Prix CBOT clôture : 4.19 $/bu
- Régime actuel : range (probabilité bull : 28%, bear : 19%, range : 53%)

## Prédictions
| Horizon | Retour attendu | Intervalle 90% | Confiance |
|---|---|---|---|
| J+5 | +0.8% | [-1.2%, +2.9%] | Faible |
| J+10 | +1.4% | [-0.8%, +3.7%] | Moyenne |
| J+20 | +2.1% | [-0.5%, +4.8%] | Moyenne |
| J+30 | +3.5% | [+0.2%, +6.9%] | Haute |

## Facteurs dominants aujourd'hui
🔴 Baissiers : dollar fort (+0.8σ DXY), exports faibles cette semaine
🟢 Haussiers : stress météo Iowa (+1.2σ chaleur), stocks/use bas

## Décision recommandée
**ATTENDRE** — L'incertitude reste élevée à J+5/J+10. Signal J+30 positif.
- Vendre à J+30 si signal confirmé la semaine prochaine.

## Performance des prédictions passées
- Prédiction J+20 du 2026-04-19 : attendu +1.8%, réalisé +2.3% ✅ DA correcte
- Prédiction J+30 du 2026-04-09 : attendu +0.5%, réalisé -1.1% ❌ DA incorrecte
```

---

## Étape 12 — Validation des prédictions passées

À chaque jour t, vérifier les prédictions passées dont l'horizon est atteint :

```python
past_snapshots = load_snapshots_older_than(days=30)
for snapshot in past_snapshots:
    if snapshot["date"] + timedelta(days=snapshot["horizon"]) <= today:
        actual_return = compute_actual_return(snapshot["date"], snapshot["horizon"])
        append_performance_record(snapshot, actual_return)
```

Ce suivi permet de mesurer la performance en temps réel et de détecter une dégradation du modèle (model drift).

---

## Planification automatique

### Cron recommandé

```cron
# Tous les jours ouvrés à 7h00
0 7 * * 1-5 cd /home/cytech/Desktop/Etude\ Mais && make daily >> logs/daily_$(date +\%Y\%m\%d).log 2>&1

# Rebuild complet chaque dimanche à 2h00
0 2 * * 0 cd /home/cytech/Desktop/Etude\ Mais && make study >> logs/study_$(date +\%Y\%m\%d).log 2>&1
```

### Makefile cible `make daily`

```makefile
.PHONY: daily
daily:
    $(PY) -m mais.ops.daily
    @echo "Daily pipeline complete: $$(date)"
```

---

## Alertes et monitoring

**Seuils d'alerte :**

| Condition | Niveau | Action |
|---|---|---|
| Prix CBOT absent | Critique | Arrêt pipeline |
| Anti-leakage échoue | Critique | Arrêt pipeline |
| Météo > 3 jours manquante | Warning | Continuer sans météo |
| WASDE non mis à jour après J+3 | Warning | Log |
| Prédiction DA < 45% sur 30 derniers jours | Warning | Email |
| CQR couverture < 80% sur 30 derniers jours | Warning | Email |
