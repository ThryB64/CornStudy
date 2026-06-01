# V39-ENRICH — Batch d'expériences d'enrichissement

Session 2026-06-01 (suite V38). Six expériences pour comprendre QUAND le short premium marche/échoue,
chacune pouvant conclure par un négatif honnête. Aucun nouveau modèle, aucune touche à la règle figée.
Anti-leakage (shift(1) + z expandant) sur tout driver fondamental. Holdout verrouillé.
`RESEARCH_ONLY_NOT_TRADING`. Module `src/mais/research/v39_enrichment.py`, tests (2 PASS), artefacts
`artefacts/v39_enrich/`.

## E1 — Durée de reversion par palier ADVERSE_RISK & saison

| palier | n | médiane (j) | reverted | stoppé | censuré |
|---|---:|---:|---:|---:|---:|
| LOW | 5 | 60.0 | 0.80 | **0.00** | 0.20 |
| MEDIUM | 33 | 31.0 | 0.70 | 0.09 | 0.21 |
| HIGH | 4 | 61.5 | 0.75 | **0.25** | 0.00 |

→ HIGH met **plus longtemps ET se fait stopper 1 fois sur 4** ; LOW (prime extrême) prend du temps mais
revient toujours sans stop. Renforce l'objectif prudent en HIGH (coût de portage + tail). Saison :
juil-août revertit le mieux (0.81), avr-juin le moins (0.56, le plus rapide 29 j).

## E2 — Robustesse aux coûts + risque de queue par palier (DÉCOUVERTE pratique)

| palier | n | PnL **net** (coût×2) | net>0 | pire MAE | %stoppé |
|---|---:|---:|---:|---:|---:|
| LOW | 5 | **+16.0** | 0.60 | −17.0 | 0.00 |
| MEDIUM | 33 | +4.9 | 0.67 | −27.0 | 0.09 |
| HIGH | 4 | **−2.0** | 0.50 | −23.4 | 0.25 |

→ **Le palier HIGH ne survit PAS au coût** (PnL net négatif). `high_tier_survives_cost = False`. C'est un
argument fort et chiffré pour la prudence en HIGH — mais **contexte, pas un veto** (n=4). Valide
pratiquement le palier ADVERSE_RISK de V38.

## E4 — Conditionnement par tendance CBOT (DÉCOUVERTE forte)

La compression est CBOT-driven (V35) : entrer quand le CBOT est **déjà au-dessus de sa SMA50** change tout.

| à l'entrée | n | taux ADVERSE | win | PnL |
|---|---:|---:|---:|---:|
| CBOT uptrend | 19 | **10.5 %** | 0.895 | **18.1** |
| CBOT downtrend | 23 | 21.7 % | 0.739 | 8.4 |

→ `uptrend_reduces_adverse = True`. Entrer en uptrend CBOT **divise l'ADVERSE par ~2 et double le PnL**.
Économiquement cohérent : la prime se comprime par rattrapage CBOT, donc un CBOT déjà porteur favorise la
compression. Cohérent V10 (« edge en uptrend ») et V35 (CBOT-driven). **Candidat n°1** pour enrichir
ADVERSE_RISK — APRÈS confirmation forward (pas de fold maintenant, n=42, discipline anti-overfit).

## E6 — Positionnement spéculatif COT (DÉCOUVERTE convergente)

| managed money net (entrée) | n | taux ADVERSE | PnL |
|---|---:|---:|---:|
| net long élevé | 17 | **11.8 %** | 14.2 |
| net long bas | 17 | 23.5 % | 7.5 |

→ `mm_positioning_discriminant_for_adverse = True`. Quand les spéculateurs sont nets acheteurs, l'ADVERSE
est ~2× plus rare. **Même direction qu'E4** : un CBOT soutenu (tendance + positionnement) = compression
fiable. Renforce la thèse centrale « short premium ≈ long CBOT relatif ». Contexte, pas veto (n=34).

## E3 — Demande éthanol US (NÉGATIF honnête sur le basis EU)

`corr(éthanol_z, basis) = 0.169` (faible) ; `corr(éthanol_z, CBOT) = −0.331` (modérée, phénomène US) ;
compression conditionnelle 0.229 vs 0.270 (non discriminant). → `ETHANOL_WEAK_DRIVER_OF_EU_BASIS`. La
demande éthanol touche le CBOT (US), pas la prime européenne.

## E5 — Théorie du stockage : bilan US stocks-to-use (NÉGATIF honnête)

`corr(s2u_z, basis) = 0.168` (faible) ; compression 0.149 vs 0.171 (non discriminant). →
`US_BALANCE_WEAK_DRIVER_OF_EU_BASIS`. Le bilan US n'explique pas la prime EU — cohérent avec V16 (la macro
n'explique pas le basis) et la thèse de la **prime locale européenne**.

## Synthèse

- **Découvertes** : (E4) entrer en uptrend CBOT divise l'ADVERSE par 2 + double le PnL ; (E6) positionnement
  spéculatif net long → ADVERSE 2× plus rare → **les deux confirment que la prime se comprime quand le CBOT
  est porteur** (« short premium ≈ long CBOT relatif »). (E2) le palier HIGH de V38 ne survit pas au coût.
- **Négatifs honnêtes** : éthanol (E3) et bilan US stocks-to-use (E5) sont des drivers US, faibles sur la
  prime EU → renforce la thèse de la prime locale (V16).
- **Discipline** : E4/E6 sont des candidats à folder dans ADVERSE_RISK, mais SEULEMENT après confirmation
  forward (n=42). Aucune touche à la règle figée. Tout descriptif.
