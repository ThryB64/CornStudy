# Backtest décisionnel agriculteur — score de vente CBOT

Date : 2026-06-13 (révisé après revue). Backtest **simple**, pas un bot de trading. On simule
un agriculteur qui détient 1 unité de récolte au début d'une **campagne de commercialisation**
et doit tout vendre avant la fin. `SELL_PARTIAL` vend une fraction (33 %) **avec un cooldown**
(≥ N séances entre deux ventes, pour ne pas liquider toute la récolte sur des signaux
consécutifs) ; le solde est vendu au dernier jour. **Jamais de short, de levier ni de rachat.**

## Corrections apportées (revue)
- **Cooldown entre ventes** : sans cooldown, le score pouvait vendre ~100 % en 4 jours
  consécutifs (févr. 2024). On impose désormais un cooldown configurable (`backtest.
  sell_cooldown_sessions`, défaut **20 séances**) ; comparaison cooldown 0 vs 20.
- **Plusieurs découpages de campagne** : année civile (`calendar`), campagne **Sep-Aug** (année
  culturale US), campagne **Oct-Sep** (récolte → stockage) — au lieu de l'année civile seule.

## Stratégies comparées
score (33 % par `SELL_PARTIAL` avec cooldown) · sell_all_start (100 % au 1er jour ≈ récolte) ·
sell_thirds (1/3 début, +60, +120 séances) · monthly_dca (1/12 par mois) · wait_year_end.

## Résultats (holdout 2024+, artefacts `final_backtest_comparison.csv` / `..._by_window.csv`)
Δ = prix moyen score − baseline (¢/bu ; **>0 = score meilleur**) ; « gagne » = campagnes
gagnées / total.

| campagne | cooldown | n | prix score | Δ récolte | Δ tiers | Δ DCA | Δ attente | gagne (réc./tiers/DCA/att.) |
|---|---|---|---|---|---|---|---|---|
| calendar | 0 | 2 | 447.64 | −13.98 | +4.73 | +9.34 | +8.89 | 1/2, 1/2, 1/2, 1/2 |
| calendar | 20 | 2 | 442.63 | −18.99 | **−0.28** | +4.33 | +3.88 | 0/2, 1/2, 1/2, 1/2 |
| sep_aug | 0 | 2 | 447.64 | +22.52 | +11.39 | +14.11 | +49.14 | 1/2, 1/2, 1/2, **2/2** |
| sep_aug | 20 | 2 | 442.63 | +17.51 | +6.38 | +9.10 | +44.13 | 1/2, 1/2, 2/2, **2/2** |
| oct_sep | 0 | 2 | 447.64 | +1.27 | +2.35 | +13.81 | +25.77 | 1/2, 1/2, 1/2, 1/2 |
| oct_sep | 20 | 2 | 442.63 | −3.74 | −2.66 | +8.81 | +20.76 | 1/2, 1/2, 2/2, 2/2 |

## Lecture honnête
1. **Le découpage de campagne change beaucoup le résultat.** En **année civile**, le score
   perd contre la vente précoce (−14 à −19) car 2024 a chuté de façon quasi monotone (vendre
   tout en janvier était optimal). En **Sep-Aug**, le score bat toutes les baselines (jusqu'à
   +49 vs attente) car le « début de campagne » (septembre) n'était pas le point bas. **Cette
   sensibilité au cadrage est elle-même un signe de fragilité** : on ne peut pas conclure à une
   performance robuste.
2. **Le cooldown réduit légèrement la performance** (447.6 → 442.6) : en marché baissier,
   étaler les ventes rapproche du prix moyen et réduit l'avantage de vendre tôt. C'est plus
   **réaliste** pour un agriculteur, mais **pas un gain** — pas de free lunch.
3. **Échantillon minuscule** : **2 campagnes**, 2025 incomplète (données → 2025-07-25), année
   civile ≠ campagne agricole réelle. Aucune conclusion statistique possible.

## Conclusion
**Le score est informatif mais pas validé comme stratégie de vente.** Selon le cadrage il bat
ou perd contre les baselines ; le cooldown ne crée pas d'avantage ; l'échantillon est trop
court. Cohérent avec le verdict **FRAGILE**. À reconfirmer sur **plusieurs campagnes en
forward**, avec une fenêtre de commercialisation agricole et une conversion en prix ferme, avant
tout usage opérationnel.
