---
id: PAPER016
source_type: paper
title: Futures-spot price transmission in EU corn markets
priority: high
status: analyzed_2026-06-12
note: Penone, Giampietri, Trestini (2022). Doublon découvert à fusionner.
---
# Transmission futures-spot dans les marchés maïs UE (Penone, Giampietri, Trestini 2022)

## 1. Référence

Penone, C., Giampietri, E., Trestini, S. (2022). Futures-spot price transmission in EU corn markets. Agribusiness (à confirmer).

## 2. Sujet

Le prix spot du maïs européen (Italie notamment) est-il piloté par le CBOT, par Euronext (EMA), ou par des facteurs locaux ? Cointégration et vitesse d'ajustement.

## 3. Données

Spot maïs UE (places italiennes type Bologne), futures EMA Euronext, futures CBOT, hebdomadaire/mensuel, 2010s.

## 4. Méthode

Tests de cointégration (Johansen), VECM avec vitesses d'ajustement, éventuellement asymétries (TVECM).

## 5. Résultats importants

- Le spot UE est cointégré avec les futures ; **EMA joue le rôle de référence de proximité** mais le CBOT reste l'ancre globale ; l'ajustement du spot vers l'équilibre est lent (semaines).
- Des périodes de DÉCOUPLAGE existent (crises locales) où le spot UE s'écarte durablement — cohérent avec notre prime locale V16.

## 6. Apport pour notre étude

- C'est LE papier publié le plus proche de notre objet (relation CBOT↔EMA↔physique EU). Sa structure VECM donne le cadre formel de notre découverte V21 (la prime se comprime surtout par hausse CBOT : dans un VECM, ça se lit dans les vitesses d'ajustement — l'EMA s'ajuste au CBOT, pas l'inverse).
- **Données** : il prouve qu'un spot UE exploitable existe (places italiennes) — piste pour notre WAITING_DATA « physiques EU ».

## 7. Hypothèses testables

- H1 (EXT013) : VECM {CBOT, EMA} sur nos données officielles : la vitesse d'ajustement de l'EMA vers l'équilibre est-elle significativement plus grande que celle du CBOT (formalisation de V21, 69 % compression par jambe CBOT) ?
- H2 : ajouter un spot UE (si sourçable : Bologne/FranceAgriMer) → la prime EMA-spot local et la prime EMA-CBOT sont-elles distinctes ? (Sépare « prime Euronext » de « prime physique ».)

## 8. Risques et limites

Fréquence hebdo/mensuelle (pas du H20 quotidien) ; données spot UE payantes ou semi-publiques (FranceAgriMer = piste gratuite) ; cointégration = long terme, à ne pas survendre en signal court.

## 9. EXT associées

EXT013 (principal), EXT036, EXT012.

## 10. Conclusion

**Priorité haute** — formalisation publiée de notre V21 + piste concrète de données spot UE. EXT013 dépend de ces données (DATA_BLOCKED partiel sinon, le volet H1 CBOT↔EMA est faisable dès maintenant).
