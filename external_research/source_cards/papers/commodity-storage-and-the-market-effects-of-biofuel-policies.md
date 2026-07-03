---
id: commodity-storage-and-the-market-effects-of-biofuel-policies
source_type: paper
title: Commodity Storage and the Market Effects of Biofuel Policies
priority: high
status: analyzed_2026-06-12
---
# Commodity Storage and the Market Effects of Biofuel Policies (Carter, Rausser, Smith 2017)

## 1. Référence

Carter, C.A., Rausser, G.C., Smith, A. (2017). American Journal of Agricultural Economics. Papier majeur (AJAE).

## 2. Sujet

Quantifier l'effet du mandat éthanol US (RFS) sur le prix du corn via un modèle de stockage rationnel : combien du niveau de prix 2006-2014 est attribuable à la demande éthanol PERMANENTE vs chocs transitoires.

## 3. Données

Prix corn, stocks, production éthanol, périodes pré/post mandat ; cadre d'équilibre stockage-prix avec anticipations.

## 4. Méthode

Modèle structurel de stockage compétitif : un choc de demande PERMANENT (mandat) élève le prix d'équilibre et modifie la fonction stocks→prix ; identification par la différence entre chocs anticipés/non-anticipés. Estimation ~30 % de hausse du prix corn attribuable au mandat (ordre de grandeur, à vérifier).

## 5. Résultats importants

- La relation stocks-to-use → prix N'EST PAS STABLE : elle se déplace quand un choc structurel de demande survient (mandat) — toute feature stocks→prix calibrée sur longue période mélange des régimes.
- Le stockage propage les chocs de demande permanents sur plusieurs années.

## 6. Apport pour notre étude

- **Avertissement méthodologique de premier ordre pour EXT024 et la feature stocks-to-use (H1 de PriceAnalysis)** : la relation doit être estimée en expandant avec prudence aux ruptures de régime (2006 mandat, 2020 COVID, 2022 Ukraine) — sinon le modèle apprend un mélange.
- Justifie une variable de régime de demande structurelle (part éthanol dans l'usage corn, lente) pour EXT031.

## 7. Hypothèses testables

- H1 (EXT031, descriptif/régime) : la sensibilité prix↔stocks-to-use estimée en roulant (10 ans) a-t-elle des ruptures aux dates de politique connues ? Si oui, dater les régimes ex ante (dates législatives) et conditionner EXT024.
- H2 : la part éthanol de l'usage corn (annuelle, datée publication WASDE) comme variable lente de régime du CBOT_SUPPORT_SCORE.

## 8. Risques et limites

Horizon long (mensuel/annuel) loin de nos H20-H90 ; identification structurelle débattue dans la littérature (réponses de Smith vs autres estimations) ; usage = contexte, jamais signal court.

## 9. EXT associées

EXT031 (principal), EXT024, EXT004.

## 10. Conclusion

**Priorité haute** comme garde-fou anti-mélange-de-régimes du bloc fondamental ; descriptif uniquement.
