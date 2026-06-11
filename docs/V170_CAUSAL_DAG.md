# V170 — DAG causal formel et identifiabilité (T-DAG, R10)

**Verdict : `DAG_FORMALIZED_EFFECTS_CLASSIFIED`** — la carte causale en prose
(`docs/CAUSAL_MAP_CORN_MARKET.md`) devient un DAG exécutable avec d-séparation (Bayes-ball) et
critère back-door. Module `src/mais/research/v170_causal_dag.py`, artefact
`artefacts/v170/v170_causal_dag.json`, 6 tests verts (chaîne/fourche/collider/back-door).
RESEARCH_ONLY_NOT_TRADING.

## Le DAG (encode les résultats ÉTABLIS, pas des hypothèses neuves)

```
U_GLOBAL_SHOCK (latent) ──→ CBOT          U_GLOBAL_SHOCK ──→ EMA
WEATHER_US ──→ CBOT     WASDE ──→ CBOT    COT_LAG(t-1) ──→ CBOT
WEATHER_EU ──→ U_EU_BALANCE (latent) ──→ {EMA, CURVE, IMPORTS_COMEXT}
WHEAT_EU ──→ EMA        U_LOCAL_PREMIUM (latent) ──→ EMA
{EMA, CBOT, FX} ──→ BASIS (déterministe)
BASIS ──→ COMPRESSION   CBOT ──→ COMPRESSION (V21/V105)
```

## Classification des effets (pré-déclarés)

| Effet | Statut | Ensemble d'ajustement |
|---|---|---|
| WEATHER_US → BASIS | IDENTIFIABLE | ∅ (météo exogène) — mais V45 : effet ≈ 0 car PRICE-IN |
| WEATHER_EU → BASIS | IDENTIFIABLE | ∅ (via bilan latent en médiateur) |
| CBOT → BASIS | IDENTIFIABLE | {EMA} (mécanique, trivial) |
| **CURVE → BASIS** | **NO_CAUSAL_PATH** | la courbe est un SYMPTÔME du bilan, pas une cause — toute corrélation courbe/basis passe par U_EU_BALANCE (confounding pur). Formalise pourquoi V166-A échoue sans invalider la courbe comme PROXY |
| WHEAT_EU → BASIS | IDENTIFIABLE | ∅ |
| COT_LAG → CBOT | IDENTIFIABLE | ∅ (convention t-1, publication vendredi) |
| **EMA → CBOT** | **NO_CAUSAL_PATH** | covariation = fourche latente U_GLOBAL_SHOCK |
| **BASIS → COMPRESSION** | IDENTIFIABLE | **{CBOT}** — pour estimer « le basis haut cause la compression », il FAUT contrôler la jambe CBOT (V21 : 6× la jambe EMA) |
| U_EU_BALANCE → BASIS | NOT_IDENTIFIABLE_LATENT | seuls ses proxies (COMEXT lag 60 j, FAM lag1, courbe) sont utilisables |

## Pourquoi Granger échoue (formalisé)

`EMA ⊥̸ CBOT` marginalement (vérifié par d-séparation) alors qu'AUCUN chemin causal ne relie
EMA→CBOT : la fourche latente `U_GLOBAL_SHOCK → {CBOT, EMA}` suffit. Ajoutez le lead-lag
d'agrégation horaire (clôture Euronext avant settlement CBOT) et on fabrique un « Granger
EMA→CBOT significatif » (p=0.0144, EXP-EMA-STUDY-02) sans causalité. **Le label
« Granger REJETÉ OOF » de l'étude est donc une conséquence STRUCTURELLE du DAG, pas un accident
d'échantillon.**

## Conséquences pratiques

1. **Toute étude courbe↔basis doit être lue comme proxy du bilan**, jamais comme effet de la
   courbe (V125 NARROWING = symptôme de détente, pas cause de compression).
2. **Les event studies de compression doivent stratifier par la jambe CBOT** (le back-door
   {CBOT} de BASIS→COMPRESSION) — c'est déjà la pratique V105/V129 (catalyseurs CBOT_DRIVEN vs
   EMA_DRIVEN), désormais justifiée formellement.
3. **L'effet météo US sur le basis est identifiable mais nul en pratique** (price-in V45) — le
   DAG dit « identifiable », les données disent « ≈ 0 » : c'est compatible, et c'est pour ça que
   la piste est passée aux RÉVISIONS de prévisions (V155, l'innovation non encore pricée).
4. **U_LOCAL_PREMIUM reste le nœud irréductible** : 4 candidats fair-value éliminés (V16 macro,
   V41 substitution seule, V161 parité d'import, V166 CY proxy). Le programme de données
   (stocks UE physiques, courbe officielle longue) vise à transformer ce latent en observé.
