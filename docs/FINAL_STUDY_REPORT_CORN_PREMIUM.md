# Rapport research final — Prime maïs Euronext/CBOT (étude V9 → V21)

**Date** : 2026-05-31 · **Statut global** : `RESEARCH_ONLY_NOT_TRADING`.
Capstone consolidant la lignée V9→V21. Holdout 2024 jamais utilisé (verrouillé physiquement).

---

## 1. Thèse finale

> Le maïs européen Euronext (EMA MATIF) **ne se prédit pas** comme une série directionnelle brute. Il se
> comprend comme le **prix mondial CBOT** (converti en EUR/t) **plus une prime locale (le basis EMA/CBOT)**.
> Cette prime suit une **mean-reversion statistique** (demi-vie ~17 j). Le signal exploitable est la
> **compression d'un basis élevé**. Et — découverte V21 — cette compression se réalise **surtout par une
> hausse du CBOT**, pas par une baisse de l'EMA : le « short premium » est en grande partie un
> **« long CBOT relatif »**.

Le mécanisme relève de familles **connues** (théorie du stockage, basis trading, convergence, mean-reversion
des spreads). La **contribution propre** est l'application précise EMA/CBOT, la démonstration que ni la macro,
ni WASDE/COT, ni le ML, ni les modèles complexes ne battent la règle simple, et la décomposition du chemin
de compression.

## 2. La règle (indicateur research)

- **Entrée** : short premium si `basis_z > 1` (paliers MODERATE 1-1.5 / STRONG 1.5-2 / EXTREME ≥2).
- **Sortie** : prudente `basis_z → 0.5` (efficacité) ou complète `basis_z → 0` (rendement), plafond ~90 j.
- **Stop** : ~ −20/−25 €/t (un stop serré −10 détruit l'edge).
- **Warnings (pas vetoes)** : roll, vol, data quality (+ météo en contexte, CBOT en contexte).

## 3. Résultats consolidés (hors holdout)

| Métrique | Valeur |
|---|---|
| Cœur structurel (modèle 2 vars basis_z + month_cos) | AUC OOF 0.694, ECE 0.059 |
| Demi-vie de mean-reversion du basis | ~17 j (8.5 j modéré, 13.2 j extrême) |
| Walk-forward 1-trade-à-la-fois (stop −20, coût dynamique) | 32 trades, hit 0.66, net +138 €/t, DD −40, 9/14 ans+ |
| Backtest portfolio strict (coût 5 €/t) | 29 trades, hit 0.90, +116 €/t, DD −27 |
| Survie hors crises (coût 5) | +115 €/t (n=30) — pas un artefact de crise |
| Paliers | EXTREME PnL 29.9 €/t · STRONG win 1.0 · MODERATE 7.3 |
| Chemin de compression | **69% via hausse CBOT** ; jambe CBOT 6× la jambe EMA |
| Red team / permutation | signal cœur p≈0.01 (réel) |

## 4. Ce qui est SOLIDE (validé, répété)

1. EMA brut ≠ bonne cible ; **basis EMA/CBOT** = bonne cible.
2. Basis **mean-reverting** (économétrie AR1/OU, demi-vie 17 j).
3. Côté **short basis-haut** robuste ; long basis-bas fragile (asymétrie décisive 0.656 vs 0.516).
4. **Sortie au niveau** (z→0/0.5) > sortie temporelle fixe H40.
5. **Simplicité gagne** : 2 vars battent 6 vars et tout modèle complexe (4 confirmations indépendantes).
6. **La macro n'explique pas le basis** (fair value R² OOF −0.25) → prime **locale idiosyncratique**.
7. **Aucune famille de littérature** (WASDE, COT, inter-commodités, courbe) ne bat `basis_z + saison`.
8. **CBOT** : prédit ses **baisses** (drawdown 8% h40 AUC 0.725), pas ses hausses ; **météo réalisée
   améliore sa direction (+0.07)**.
9. **Compression surtout via hausse CBOT** (V21) → reframing du signal.

## 5. Ce qui est PROMETTEUR mais fragile / WATCHLIST

- **Météo** : ↑stress → basis haut **moins compressible** (33% vs 68%) — confirme la théorie du stockage,
  mais effet trade non confirmé (n petit). WATCHLIST.
- **Météo PRÉVUE** (révisions de forecast) : infra + anti-leakage posés ; **archive à collecter**
  (devrait battre le réalisé, et est exploitable car connue à l'avance). Meilleure piste data restante.
- Signaux STRONG/EXTREME : forts mais petits échantillons.
- Sortie z→0 : optimiste (mécanique partielle).

## 6. Ce qui est REJETÉ (honnêtement)

Meta-model V6 (overfit), H90 (réfuté), EMA up/down brut, fair value fondamentale, COT×météo short-covering,
WASDE comme prédicteur OOF, ML complexe, sur-filtrage / over-gating, météo sur les rallyes.

## 7. Bloqueurs (pourquoi research-only)

1. **Donnée EMA = proxy** `barchart_proxy_exploratory` (déblocage n°1 : EMA officiel Euronext).
2. **Pipeline live** à fiabiliser (fraîcheur, collecteurs en erreur/STUB).
3. **Mur des coûts** : edge net positif jusqu'à ~3-4 €/t/leg, fragile à 5.
4. **Track forward** non encore accumulé (journal prêt).
5. **Courbe EMA multi-échéances** et **physiques EU** (MARS, FranceAgriMer, Ukraine, TTF) absentes.

## 8. Architecture de l'indicateur cible (research)

```
Signal de prime (V17)        : NO_SIGNAL / MODERATE / STRONG / EXTREME / UNCERTAIN_{ROLL,VOL,DATA}
+ Contexte CBOT (V21)        : UPTREND / NEUTRAL / BULLISH_WEATHER / RISK_OFF ; drawdown_risk low/med/high
+ Chemin probable (V21)      : compression via CBOT-up / via EMA-down / mixte
+ Objectifs                  : prudent z→0.5 / complet z→0 ; stop −20 ; horizon médian saison
+ Risque                     : non-reversion (élevé si z>2), météo (basis justifié), roll/vol/data
= Sortie research, statut RESEARCH_ONLY_NOT_TRADING
```

## 9. Roadmap restante

- **Données (déblocage)** : EMA officiel + courbe multi-échéances + archive météo prévue (US/EU) + physiques EU.
- **V22 paper trading** : journal forward append-only (prêt) sur 6-12 mois ; backtest vs forward.
- **Indicateur** : reste **figé** tant qu'aucune famille n'obtient `ADD_TO_INDICATOR` robuste.
- **Pas de bot réel** avant données officielles + paper trading + coûts réels validés.

## 10. Verdict final

> L'étude a produit un **indicateur research professionnel, simple, explicable et honnête** d'une **anomalie
> structurelle réelle** : la prime Euronext/CBOT se compresse quand elle est trop élevée, principalement par
> rattrapage du CBOT mondial. Le mécanisme est cohérent avec la littérature ; la règle résiste à toutes les
> tentatives de complexification. Ce **n'est pas encore** un système de trading réel (proxy EMA, coûts, pas
> de forward long), mais c'est une **base solide** pour un indicateur d'analyse pro et un paper trading sérieux.

---

### Index des phases

V9 indicateur structurel · V10 découvertes (demi-vie, simplicité, H40, mur coûts, régime) · V11 modèle 2 vars
promu · V12 mean-reversion lab (exit niveau, conforme) · V13 short strict (survit coût5 hors crise) ·
V14 short-only + survival + robustesse proxy · V15 réalisme (stop, sizing, portfolio strict) · V16 la macro
n'explique pas le basis · V17 indicateur à paliers + walk-forward + fiches · V18-LIT revue + réplication
(rien ne bat basis_z) + météo deep (33% vs 68%) · V19 CBOT (baisses prévisibles, météo→direction) + infra
météo prévue · V21 intégration + **chemin de compression (CBOT-up)**.

*Rapport final — 2026-05-31. Research-only. Holdout 2024 réservé.*
