# Revue de littérature — Maïs CBOT / Euronext, basis, stockage, convergence

**Date** : 2026-05-31 · **Statut** : référence pour la phase V18-LIT (réplication + intégration).

But : situer notre découverte (compression de la prime EMA/CBOT quand le basis est élevé) dans la
littérature, et définir quelles familles d'études répliquer et tester contre notre baseline `basis_z`.

> **Avertissement honnête** : ce document résume des familles de travaux et des concepts **établis**. Les
> auteurs/années cités sont des références séminales bien connues, mais les **chiffres exacts** de chaque
> papier doivent être vérifiés sur les sources primaires avant tout claim. On ne cite ici aucune valeur
> numérique tirée d'un papier précis ; on décrit les mécanismes et la méthode à répliquer chez nous.

---

## Positionnement de notre découverte

Notre résultat — *quand la prime Euronext maïs vs CBOT converti en EUR (le basis) devient anormalement
élevée, elle tend à se compresser* — relève de trois familles connues :
1. **Théorie du stockage** (le basis / la structure de courbe reflète stocks, portage, convenience yield) ;
2. **Basis trading / relative value / convergence trading** (un écart lié revient vers son équilibre) ;
3. **Mean-reversion des spreads de commodités**.

Le **mécanisme est connu**. Ce qui est **spécifique à notre étude** : l'application précise au spread
**EMA MATIF / CBOT EUR/t**, avec entrée `basis_z>1`, sortie dynamique sur le retour du basis (z→0 / z→0.5),
coûts dynamiques, roll risk, data quality, paliers et journal forward. C'est une **contribution pratique**,
pas une nouvelle théorie.

---

## Familles d'études

### 1. Théorie du stockage (Working 1949 ; Kaldor 1939 ; Brennan 1958 ; Telser ; Fama-French 1987)
**Idée** : les prix futures intègrent stocks, coût de portage, financement et **convenience yield**. Stocks
abondants → contango ; stocks tendus → backwardation. Le basis n'est pas qu'une anticipation, c'est un état
physique.
**À répliquer** : structure de courbe EMA (contango/backwardation, pente, spread front-next, roll yield, OI)
et lien avec la compressibilité d'un basis élevé.
**Hypothèse testable** : basis haut + contango = surprix compressible ; basis haut + backwardation = tension
physique durable (moins compressible).

### 2. Modèles de prix mean-reverting des commodités (Schwartz 1997 ; Gibson-Schwartz 1990)
**Idée** : les prix/spreads de commodités suivent souvent un processus de retour à la moyenne
(Ornstein-Uhlenbeck), parfois à deux facteurs (prix + convenience yield stochastique).
**À répliquer** : AR(1)/OU sur basis_z → demi-vie ; modèles à seuil (threshold AR) ; régime-switching
(reversion plus rapide en régime tendu) ; demi-vie dynamique.
**Lien projet** : justifie et calibre nos sorties (z→0, z→0.5, plafond temps).

### 3. Basis trading / convergence / relative value
**Idée** : prendre des positions opposées sur deux actifs liés pour capter la convergence du basis.
**À répliquer** : vitesse de convergence, sortie au niveau de basis, stop, time-stop, coûts de portage et
d'exécution, non-overlap. **C'est exactement notre cadre** ; on le formalise comme une étude de convergence.

### 4. (Non-)convergence des futures grains (Garcia-Irwin-Smith ; Aulerich-Irwin-Garcia ; Hranaiova-Tomek)
**Idée** : futures et physique ne convergent pas toujours parfaitement à maturité (certificats de livraison,
coûts de stockage stochastiques, options de timing/livraison). D'où des épisodes de **non-convergence**.
**À répliquer** : analyse des **trades censurés / échecs de reversion**, rôle des fenêtres de roll, crises,
faible liquidité, tension physique. → des **warnings** (ne pas shorter une prime justifiée).

### 5. Price discovery sur les contrats futures (Garbade-Silber 1983 ; Hasbrouck 1995 info share ; Yang-Bessler-Leatham)
**Idée** : la découverte des prix se concentre sur certains contrats/échéances ; la part baisse quand le
volume relatif du contrat proche s'effondre avant expiration.
**À répliquer** : front vs liquid vs deferred (Nov/Mar), part de volume/OI, DTE, fenêtre de roll → **quel
contrat EMA porte le basis le plus fiable**, réduire les faux signaux de roll.

### 6. Lead-lag CBOT ↔ Euronext (intégration des marchés mondiaux du grain)
**Idée** : les marchés liés sont co-intégrés ; le marché dominant (CBOT, mondial) mène, le suiveur (EMA)
s'ajuste avec retard et bruit local.
**À répliquer** : co-intégration, ECM, Granger, part d'ajustement → confirme « CBOT mène, EMA = CBOT + prime
locale » (déjà observé V1-V8 ; à consolider).

### 7. Event studies USDA/WASDE (Garcia-Irwin ; Adjemian ; Isengildina-Massa)
**Idée** : WASDE, Grain Stocks, Acreage, Crop Progress, Export Sales déplacent significativement le prix ;
les **surprises** (réalisé − attendu) portent l'information.
**À répliquer** : event study sur CBOT return, EMA return, **basis_change** et probabilité de compression.
**Question** : les annonces US expliquent-elles seulement CBOT, ou aussi la compression de la prime EU ?

### 8. Positionnement COT (Working's T ; Sanders-Irwin ; de Roon-Nijman-Veld)
**Idée** : le positionnement des fonds (managed money) et le hedging pressure sont liés aux primes de risque
et aux retournements (short covering / crowding).
**À répliquer** : percentiles COT, crowding, interaction COT × basis_z → un basis haut est-il plus
dangereux à shorter quand les fonds sont déjà très positionnés ?

### 9. Météo / crop condition / rendement (Tannura-Irwin-Good ; Schlenker-Roberts)
**Idée** : le stress de rendement (chaleur, déficit hydrique, GDD) est un driver fondamental du prix et des
primes physiques.
**À répliquer** : GDD, heat days, déficit pluie, drought, crop condition US ; (EU MARS quand dispo) →
distinguer un basis haut **justifié par stress physique** d'un basis haut **anormal/compressible**.

### 10. Inter-commodités / complexe du grain (corn-soy ratio, corn-wheat, énergie, éthanol)
**Idée** : le maïs est lié au soja (substitution surfaces), au blé (alimentation animale), au pétrole/gaz
(éthanol, intrants) ; les spreads inter-commodités portent un contexte.
**À répliquer** : corn/soy, corn/wheat, corn/oil, marge éthanol, corn/gas, engrais → contexte de compression.

### 11. Carry / roll yield / structure de terme (Erb-Harvey ; Gorton-Rouwenhorst ; Koijen et al. carry)
**Idée** : le carry (roll yield) prédit en partie les rendements futures de commodités.
**À répliquer** : roll yield EMA, carry front-next → contexte de la prime (limité par données de courbe).

### 12. Options / volatilité implicite (skew, term structure)
**Idée** : le marché d'options anticipe risques et asymétries (skew put/call, term structure de vol).
**À répliquer** : IV CBOT corn, skew, risk-reversal → anticipation des compressions/chocs.
**Statut data** : **non disponible** dans le dataset courant → `DATA_BLOCKED`.

### 13. Machine learning sur prix agricoles
**Idée** : RF/GBM/LGBM, régularisé, quantile, conformal pour prévoir prix/direction.
**À répliquer** : déjà fait extensivement (V3-V13). **Contrainte stricte** : le ML doit battre la règle
simple `basis_z + saison` ; sinon rejeté. Résultat établi chez nous : il ne la bat pas (V10-V13).

### 14. Séries temporelles classiques (ARIMA/SARIMAX/GARCH) et régimes (Markov-switching)
**Idée** : modèles linéaires saisonniers + volatilité conditionnelle ; régimes bull/range/bear.
**À répliquer** : déjà fait (ETUDE-11/12, V7). Réutilisé comme baseline et contexte de régime.

### 15. Études Europe spécifiques (MATIF, FranceAgriMer, EC MARS, Eurostat COMEXT, Ukraine)
**Idée** : la prime européenne dépend de l'offre/demande physique EU, des flux d'import/export, de
l'Ukraine, de l'énergie EU (TTF), du fret.
**Statut data** : majoritairement **non joint** au dataset courant → `WAITING_DATA` (déblocage n°1).

---

## Ce que la littérature nous dit pour l'indicateur

1. Notre signal est un **convergence trade sur un basis mean-reverting** — théoriquement fondé.
2. La **structure de courbe** (théorie du stockage) devrait distinguer basis compressible vs durable → à tester.
3. La **non-convergence** explique nos échecs → des **warnings** (pas vetoes).
4. Les **annonces, COT, météo, inter-commodités** sont des **contextes** candidats : à n'intégrer que s'ils
   améliorent l'OOF au-delà de `basis_z`.
5. Le **ML** ne doit pas remplacer la règle simple (déjà établi).

La phase V18-LIT réplique ces familles et leur attribue un verdict :
`ADD_TO_INDICATOR` / `KEEP_AS_EXPLANATION` / `WATCHLIST` / `NO_GO` / `DATA_BLOCKED`.

---

*Revue de littérature — 2026-05-31. Mécanisme connu (stockage / basis / convergence) ; application EMA/CBOT*
*précise spécifique. Réplication structurée par familles, intégration seulement si gain OOF robuste.*
