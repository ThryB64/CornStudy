# Étape 7 — Rapport final d'exécution

Date : 2026-06-13. Clôture de l'étude. **Aucune nouvelle recherche, aucune famille rejetée
réintroduite, aucun modèle complexe, aucun tuning sur le holdout.**

## 1. Résumé
Intégration des seules briques validées (étapes 5 bis / 6) en un **score de vente / direction
/ risque CBOT H40-H90**, validé **une seule fois** sur le holdout 2024+, backtesté, testé,
documenté et branché à la CLI. **Verdict : FRAGILE.**

## 2. Fichiers créés
- Modules : `src/mais/indicator/cbot_sale_score{_features,_model,,_backtest,_report}.py`.
- Config : `config/cbot_sale_score.yaml`.
- Tests : `tests/test_cbot_sale_score.py`, `..._leakage.py`, `..._outputs.py`.
- Scripts/CLI : commande `mais sale-score` (+ `--holdout`, `--latest`), cible `make sale-score`.
- Docs : `STEP7_FINALIZATION_PLAN.md`, `STEP7_TEST_REPORT.md`, `FINAL_HOLDOUT_2024_VALIDATION.md`,
  `FINAL_FARMER_DECISION_BACKTEST.md`, `FINAL_CBOT_SALE_SCORE_{STUDY,PROTOCOL,LIMITS,USER_GUIDE,
  TECHNICAL_SUMMARY}.md`, `FINAL_CBOT_STUDY_CLOSURE.md`, ce rapport.
- Artefacts : `artefacts/final_cbot_sale_score/` (9 fichiers).

## 3. Fichiers modifiés
- `src/mais/cli.py` : ajout de la commande `sale-score` (additif).
- `Makefile` : cible `sale-score` (additif).
- `README.md` : sections « Résultat final » et « Données nécessaires ».
- `.ai/STATE.md` : entrée de clôture.
Aucune modification du modèle principal, des résultats externes, ni du holdout.

## 4. Tests lancés
```bash
pytest tests/test_cbot_sale_score*.py        # 13 passed
ruff check src/mais/indicator/cbot_sale_score*.py src/mais/cli.py tests/test_cbot_sale_score*.py
                                              # All checks passed
py_compile (5 modules + cli.py)               # OK
python -m mais.cli sale-score --holdout       # OK, verdict FRAGILE
```

## 5. Résultats holdout 2024+ (une fois)
| modèle | h | n | DA | AUC | vs majorité |
|---|---|---|---|---|---|
| score crop@H90 | 90 | 303 | 0.686 | 0.816 | +0.182 |
| score wasde@H40 | 40 | 353 | 0.705 | 0.709 | +0.184 |
| saison seule | 90 | 303 | 0.752 | 0.840 | +0.248 |
| marché seul | 90 | 303 | 0.752 | 0.878 | +0.248 |
| random walk | 90 | 303 | 0.495 | 0.500 | −0.010 |

Bat la random walk (+18 pts), cohérent ; **ne bat pas** la saisonnalité / le marché seul.
DA walk-forward pré-2024 (crop@H90) : 0.653.

## 6. Résultats backtest décisionnel (2024+, révisé)
Avec **cooldown 20 séances** et 3 découpages de campagne (artefacts `final_backtest_comparison.csv`) :
- **Année civile** : score 442.6, perd vs vente-récolte (−19.0), ≈ tiers (−0.3), bat DCA (+4.3)
  et attente (+3.9).
- **Sep-Aug** : score bat toutes les baselines (vs récolte +17.5, vs attente +44.1, gagne 2/2).
- **Oct-Sep** : mixte (vs DCA/attente positif, vs récolte/tiers négatif).
Le résultat **dépend du cadrage** et le cooldown réduit légèrement la performance (pas de free
lunch) → backtest **mitigé, non conclusif** (2 campagnes, 2025 incomplète).

## 7. Verdict final du score : **FRAGILE**
Justification : le holdout est **mitigé** (le score bat la random walk et est cohérent, mais
n'apporte pas de valeur démontrable au-dessus d'une simple saisonnalité ; fenêtre ~1,5 an,
backtest 2 ans instable). Conforme aux critères de l'étape 7. **Pas caché : documenté
honnêtement.** Le score reste un **indicateur d'aide à la décision**, pas un système de trading.

## 7bis. Corrections post-revue (2026-06-13)
1. **Fuite HAR corrigée** : `har_vol_forecast` purge désormais les fenêtres de vol dont la vraie
   date de fin `index[i+h]` tombe en holdout (helper `har_train_mask`). Effet sur le gate
   négligeable (0.1922 → 0.1923) ; métriques directionnelles inchangées. Nouveau test
   `test_har_vol_training_excludes_2024_targets`.
2. **Cooldown de vente** : `SELL_PARTIAL` espacé d'au moins `backtest.sell_cooldown_sessions`
   (défaut 20) séances — évite de liquider la récolte sur 4 jours consécutifs.
3. **Campagnes agricoles** : backtest étendu à `sep_aug` et `oct_sep` en plus de l'année civile ;
   comparaison windows × cooldown (`final_backtest_comparison.csv`).
4. **Tests** : 13 → **14** (ajout HAR). ruff toujours clean.
5. **Limites explicitées** : données arrêtées au 2025-07-25 (signal non à jour), score en
   CBOT ¢/bu non converti en prix ferme €/t.

## 8. Prochaines actions possibles
- **Mettre à jour les données** (CBOT, WASDE vintage, Crop Condition) jusqu'à aujourd'hui puis
  relancer `sale-score --latest` — le signal de juillet 2025 n'est pas exploitable en l'état.
- **Reconfirmer en forward** le score sur plusieurs campagnes (seule voie de validation réelle).
- Acquérir les données débloquantes (cf. §10) avant d'élargir.
- Ne pas complexifier le modèle sur les données actuelles.

## 9. Réponses aux 12 questions (résultat attendu R)
1. Conclusion : prix non prédictible ; signal directionnel/vol modeste → score de vente FRAGILE.
2. Prix abandonné car random walk imbattable en RMSE (0/36 DM).
3. Score : `cbot_sale_score_v1`, direction H40/H90 + risque vol + confiance.
4. Variables : Crop Condition (H90), WASDE stocks-to-use (H40), saison, vol HAR, régimes.
5. Calcul : logit L2 par horizon → `p_down`, gate vol, confiance régime → recommandation.
6. Holdout : DA 0.686 / AUC 0.816 (bat RW, pas la saisonnalité), n=303, ~1,5 an.
7. Aide à la vente : modeste — bat l'étalement régulier, perd vs vente précoce en marché baissier.
8. Limites : edge modeste, pas de gain vs saison, holdout court, régimes post-hoc.
9. Données manquantes : eurusd, courbe, basis, consensus WASDE, options, météo prévue, satellite.
10. Commande : `python -m mais.cli sale-score --holdout` (ou `make sale-score`).
11. Rapports : `docs/FINAL_CBOT_SALE_SCORE_*.md`, `docs/FINAL_*.md`, `artefacts/final_cbot_sale_score/final_report.md`.
12. Statut : **FRAGILE**.

## 10. Données à acheter / collecter
Priorité 1 : **EUR/USD quotidien** (FRED, gratuit), **archive prévisions météo forward**
(Open-Meteo, gratuit), **export flows** (USDA FAS, gratuit) ; **consensus analystes pré-WASDE**
et **options maïs (vol implicite)** (payant). Priorité 2-3 : contrats CBOT par maturité, prix
physiques FOB, satellite/NDVI, fournisseurs premium (Bloomberg/LSEG/Platts). Détail :
`external_research/docs/step6_missing_data_recommendations.md`.
