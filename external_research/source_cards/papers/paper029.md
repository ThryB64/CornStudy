---
id: PAPER029
source_type: paper
title: Democratising Agricultural Commodity Price Forecasting - The AGRICAF Approach
priority: very_high
status: analyzed_2026-06-12
note: Zelingher et coll. (~2024-2025) — lignée des travaux Zelingher & Makowski sur le forecast du prix mondial du maïs par productions régionales. À confirmer au PDF.
---
# AGRICAF — ML explicable pour les prix agricoles (Zelingher et al.)

## 1. Référence

Zelingher, R. et coll. (~2024-2025). Democratising Agricultural Commodity Price Forecasting: The AGRICAF Approach. (Lignée : Zelingher, Makowski, Brunelle — sensibilité du prix mondial du maïs aux productions régionales.)

## 2. Sujet

Cadre ML explicable et reproductible pour prévoir les prix agricoles mensuels (maïs au cœur) à 1-12 mois, à partir de variables d'offre régionales (productions par grande région) et de l'explicabilité des contributions.

## 3. Données

Prix mensuels du maïs (référence mondiale), productions/anomalies régionales (US, Amérique du Sud, Europe, Chine...), horizons 1-12 mois, plusieurs décennies.

## 4. Méthode

Modèles d'arbres (RF/GBM) avec validation temporelle, explicabilité (importances/SHAP), comparaison aux baselines naïves ; accent sur l'accessibilité du cadre (open).

## 5. Résultats importants

- Les chocs de production des GROSSES régions (US d'abord) dominent la prévisibilité du prix mondial du maïs aux horizons 3-12 mois.
- Les modèles d'arbres battent les baselines aux horizons moyens, surtout en période de choc d'offre ; gain faible en régime calme.
- L'explicabilité montre des contributions stables et économiquement sensées (offre → prix).

## 6. Apport pour notre étude

- Pour EXT024 (benchmark offre/demande long horizon) : utiliser des variables d'OFFRE RÉGIONALE datées publication (WASDE world : production US/Brésil/Argentine/UE/Ukraine) plutôt que macro génériques — c'est le choix de variables validé par AGRICAF.
- L'angle UE/Ukraine est directement pertinent pour la prime EMA (V36 substitution blé/maïs, mer Noire).

## 7. Hypothèses testables

- H1 (EXT024) : anomalies de production WASDE par région (datées publication, z expandant) → direction CBOT H60-H252 vs RW : réplication AGRICAF simplifiée sur NOS séries.
- H2 : l'anomalie de production UE+Ukraine prédit-elle le NIVEAU de la prime EMA à H60+ ? (Premier test fondamental de la prime avec variables d'offre régionales — jamais fait en interne ; V16 n'avait testé que macro/FX/énergie.)

## 8. Risques et limites

Mensuel, horizons longs (peu d'observations indépendantes → significativité fragile) ; productions régionales = données annuelles révisées (utiliser les vintages WASDE, dépend EXT026) ; H2 est l'un des rares tests NOUVEAUX pour la prime — à protocoler soigneusement.

## 9. EXT associées

EXT024 (principal), EXT026, EXT014/EXT015 (explicabilité), EXT036.

## 10. Conclusion

**Priorité très haute** — la meilleure source du bloc ML : son apport n'est pas le modèle mais le CHOIX DE VARIABLES (offre régionale datée), qui ouvre un test inédit sur la prime (H2).
