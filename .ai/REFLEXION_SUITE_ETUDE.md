# Réflexion — Suite de l'étude prime EMA/CBOT

> **Document de travail vivant.** On ne travaille QUE sur ce fichier. Objectif : décider de la suite
> de l'étude — ce qu'il faut corriger, ce qu'il faut améliorer, et surtout quelles sont les prochaines
> étapes (recherches, expériences, sources de données). Rien d'autre n'est modifié.
>
> - **Créé le** : 2026-06-10
> - **Statut** : OUVERT — à enrichir / développer / amender à chaque session
> - **Mode** : réflexion conjointe. On liste, on argumente, on priorise. On ne code pas ici.
> - **Convention** : chaque nouvelle idée porte un identifiant (R# pour recherche, X# pour expérience,
>   D# pour donnée, T# pour ticket proposé) pour pouvoir y revenir et la trancher.

---

## Sommaire

- [Partie 0 — Méta : comment on travaille sur ce document](#partie-0--méta)
- [Partie 1 — Audit intégral (matériel d'entrée)](#partie-1--audit-intégral)
- [Partie 2 — Lecture critique de l'audit](#partie-2--lecture-critique-de-laudit)
- [Partie 3 — Nouveaux axes de recherche](#partie-3--nouveaux-axes-de-recherche)
- [Partie 4 — Nouvelles expériences à mener](#partie-4--nouvelles-expériences)
- [Partie 5 — Rigueur statistique anti-overfitting](#partie-5--rigueur-statistique)
- [Partie 6 — Nouvelles sources de données à explorer](#partie-6--nouvelles-sources-de-données)
- [Partie 7 — Backlog de tickets additionnels](#partie-7--backlog-de-tickets-additionnels)
- [Partie 8 — Questions ouvertes & pré-enregistrement](#partie-8--questions-ouvertes)
- [Partie 9 — Journal de réflexion](#partie-9--journal-de-réflexion)
- [Annexe A — Sources web à vérifier](#annexe-a--sources-web)

---

## Partie 0 — Méta

**Pourquoi ce document.** L'étude a un noyau économique solide (la prime EMA/CBOT élevée se compresse
souvent ; le module short-premium est la partie utile). La phase qui s'ouvre n'est plus « trouver le
signal » mais **durcir la vérité des données, séparer la réversion du niveau du timing du déclenchement,
et augmenter la puissance statistique sans tricher**. Ce fichier centralise la réflexion sur cette
phase.

**Règles de ce document.**
1. On n'efface pas une idée rejetée : on la marque `REJETÉ` avec la raison. La traçabilité des
   impasses vaut autant que les succès (cf. Granger rejeté OOF, fair-value rejetée V16, etc.).
2. Toute nouvelle expérience doit être **falsifiable** et déclarer à l'avance son critère
   d'acceptation/rejet (anti p-hacking).
3. Toute feature « leading » doit déclarer son **horodatage exact** ; sinon, lag d'une session.
4. On distingue partout **DESCRIPTIF** (IN_PROGRESS, ex-post) de **PRÉDICTIF** (START, ex-ante).

**Comment le faire grandir.** À chaque session : (a) on tranche une ou deux questions ouvertes de la
Partie 8, (b) on convertit les idées mûres (R#/X#) en tickets (Partie 7), (c) on consigne la décision
dans le Journal (Partie 9).

---

## Partie 1 — Audit intégral

> Reproduit intégralement, tel que fourni. C'est le matériau d'entrée de notre réflexion. Mes
> commentaires et compléments sont en Partie 2 et au-delà.

### Résumé exécutif

L'archive montre que l'étude n'est pas bloquée parce que le signal central serait faux. Elle est bloquée parce que le noyau économique est déjà trouvé, alors que les prochaines améliorations dépendent surtout de la qualité de vérité des données, de la discipline forward, et d'une meilleure séparation entre réversion du niveau et timing du déclenchement. Le cœur du projet reste cohérent : la prime EMA/CBOT élevée se compresse souvent, le module short-premium est la vraie partie utile, et l'objectif contextuel z→0.5 versus z→0 est une amélioration crédible sans toucher à la baseline figée.

L'état du dépôt est meilleur que ce que laissaient penser certains artefacts plus anciens. L'historique officiel forward a bien grandi : le dernier reports/daily/latest.json indique 9 jours officiels dans le journal, 90 snapshots de contrats dans official_daily.parquet, un journal MATIF blé/maïs rempli jusqu'au 10 juin 2026, et un journal météo forecast également alimenté jusqu'au 10 juin 2026. En revanche, cet enrichissement n'a pas été propagé de manière cohérente vers les artefacts premium de tête : data/premium/premium_daily_head.json, dashboard_v4.md, v133_monthly_v2.json et plusieurs synthèses restent bloqués au 2–3 juin. Il y a donc bien accumulation forward, mais pas encore une source de vérité unique et fraîche.

Le point le plus sensible de tout l'audit est méthodologique : plusieurs lignes du journal officiel ont été collectées le matin et ne portent pas les champs de session attendus (record_status, collected_at_paris, effective_session_date). Or le contrat maïs Euronext cote désormais jusqu'à 20:15 CET, tandis que le DSP reste fixé à 18:30 CET ; Euronext documente explicitement que l'extension d'horaires n'a pas changé l'heure de calcul du DSP. Si vous collectez avant 18:30 Paris, vous risquez d'embarquer un settlement non final ou un settlement de la veille avec une date d'en-tête du jour. C'est aujourd'hui le risque méthodologique numéro un du projet.

Deuxième conclusion forte : le projet a déjà démontré que le timing précis du début de compression est beaucoup plus dur que la réversion du niveau. L'artefact V106 est honnête et important : sur les jours basis_z>1, le score de trigger actuel est inversé. Il détecte plutôt une compression déjà en cours qu'un vrai départ futur. Cette découverte n'invalide pas le signal premium ; elle impose de reformuler la recherche. La prochaine étape ne doit pas être "faire un meilleur trigger opaque", mais séparer clairement deux problèmes :
(a) un score IN_PROGRESS descriptif,
(b) un score START réellement prédictif, fondé sur des variables horodatées et causales.

Troisième conclusion : le projet n'est pas condamné par le faible backfill officiel. Il reste un énorme champ d'exploration avec des sources gratuites déjà disponibles ou facilement intégrables : COMEXT Eurostat en bulk mensuel/annuel depuis janvier 1988, FranceAgriMer en open data pour les cotations céréales quotidiennes et des jeux de données maïs/Céré'Obs, JRC MARS pour les prévisions de rendement et conditions de culture, Open‑Meteo Historical Forecast et Previous Runs pour les révisions de prévisions, CFTC COT public, USDA WASDE calendar, et NOAA NOMADS pour GFS/GEFS gratuits.

Enfin, le meilleur plan d'acquisition payant est clair. La voie officielle la plus propre est Euronext Data Solutions : Web Services pour l'API historique JSON et NextHistory pour les résumés EOD via SFTP. Euronext présente explicitement ces services comme des moyens d'accéder à des données real-time, delayed and historical, et le contact opérationnel officiel est datasolutions@euronext.com. L'option la moins chère pour gagner rapidement quelques briques exploratoires, si les symboles sont effectivement disponibles, est Barchart Premier : l'offre publique affiche 29.95 USD/mois en mensuel et permet le téléchargement d'historiques sur les symboles publics transportés par la base Barchart ; mais cela reste non officiel, souvent en close/last plutôt qu'en settlement officiel, donc utile pour proxy / watchlist / intraday exploratoire, pas pour "sanctifier" le backtest.

### Audit de l'archive et verdict

L'état actuel de l'étude peut être résumé simplement : le fond économique est bon, la plomberie de vérité doit être durcie.

#### Ce qui ressort comme validé

Sur le bloc historique proxy/research, plusieurs résultats restent cohérents et utiles.

| Bloc | Verdict d'audit | Commentaire |
|---|---|---|
| Signal short premium | Validé | 42 occurrences historiques, win rate global autour de 81 %, PnL moyen 12.83 €/t, adverse rate 16.7 % dans les artefacts de robustesse. |
| Réversion du niveau du basis | Validé | V120 trouve un basis_z de niveau stationnaire, avec AR(1) φ≈0.9603 et demi‑vie ≈17.1 jours. |
| Objectif contextuel | Validé | V56 montre que la règle recommandée garde quasiment le PnL du z→0 tout en réduisant l'exposition moyenne. |
| Magnitude par classes | Validé | V57 est beaucoup plus crédible que la tentative de prédire un €/t exact. |
| Episode library | Validé | V82 convertit les 42 trades en bibliothèque de cas exploitable. |
| CBOT_SUPPORT rule-based | Validé avec réserve | V86 améliore légèrement la séparation sans modèle opaque. |
| Trigger "précis du départ" | Non validé | V105/V106 montrent que le timing précis reste faible et que le score actuel est inversé. |
| Courbe EMA officielle live | Validé en forward | V109 fonctionne, mais reste non-backtestable faute d'historique officiel long. |
| Ratio MATIF wheat/corn forward | Validé en forward | Le journal forward existe, mais l'historique sérieux reste trop court. |

La situation live la plus fraîche du dépôt n'est pas donnée par premium_daily_head.json, mais par reports/daily/latest.json du 10 juin 2026. Ce rapport montre un journal officiel porté à 9 jours, un dernier basis officiel à 72.59 €/t, basis_z_used = 1.778, signal_tier = SHORT_PREMIUM_STRONG, CBOT_SUPPORT v2 = MEDIUM, ADVERSE_RISK live = MEDIUM et PHYSICAL_TENSION live = HIGH. Cela veut dire que l'étude a continué à vivre en forward, mais que la couche premium de présentation n'a pas suivi.

#### Ce qui est objectivement incohérent aujourd'hui

Le dépôt contient plusieurs incohérences qu'il faut traiter avant de refaire de la science.

| Anomalie | Gravité | Constat d'audit | Conséquence |
|---|---|---|---|
| premium_daily_head.json et dashboard premium stales | Très haute | premium_daily_head.json et dashboard_v4.md restent datés du 2 juin, alors que reports/daily/latest.json est au 10 juin | Le produit "live" peut afficher un état faux ou périmé |
| Artefacts V42/V133 stales | Haute | Certains artefacts persistés disent encore n_days = 2 ou 3, alors que latest.json remonte 9 jours officiels | Confusion d'audit et risque de conclusions erronées |
| Journal officiel sans record_status | Très haute | Les lignes du journal ne portent ni record_status, ni collected_at_paris, ni effective_session_date | Impossible de distinguer FINAL / PROVISIONAL / REVISED |
| Captures matinales | Très haute | Plusieurs logged_at du journal sont le matin UTC, donc avant 18:30 Paris | Risque de faux changement de signal lié au timing |
| Trigger score inversé | Haute | V106 : NONE compresse plus souvent que CONFIRMED | La brique actuelle décrit l'avancement, pas le départ |
| Écart CBOT reconstruit ponctuel élevé | Moyenne | Le latest.json montre un abs_err = 2.77 €/t le 3 juin dans la validation de reconstruction live | Probable problème d'alignement CBOT/FX/session, à traiter |
| basis_z_official_rolling toujours nul | Normale | Le rolling z officiel n'est pas encore disponible | Le z live reste un proxy_implied, pas un z 100 % officiel |
| substitution_residual_z_live = null au 10 juin | Normale | Certaines briques contextuelles sont fraîches, d'autres partielles | Il faut afficher clairement les diagnostics désactivés |

Le risque le plus sérieux n'est donc pas "le signal historique est faux". Le risque le plus sérieux est : on pourrait interpréter comme signal économique ce qui n'est parfois qu'un artefact de session ou de fraîcheur.

### Choix final sur compression_start_date

Le dépôt a déjà fait le travail comparatif qu'il fallait : V104 compare cinq définitions du "début de compression".

| Définition | Idée | Couverture | Offset médian entrée→start | Lecture |
|---|---|---|---|---|
| A | basis_z baisse de 0.3 depuis le pic | 41 | 4 j | simple, scale-free, suffisamment tôt |
| B | basis baisse de 5 €/t | 41 | 9 j | trop tardif pour un vrai "start" |
| C | basis passe sous sa MA5 | 42 | 3 j | très réactif, bon Early Warning |
| D | 3 baisses sur 5 jours | 41 | 7 j | plus bruité |
| E | 25 % du chemin de compression est fait | 41 | 4 j | bon check descriptif, mais plus ex post |

Le dépôt a raison d'avoir retenu A comme définition primaire. C'est celle que je recommande aussi comme protocole final, avec la règle suivante :

```
compression_start_date_final = définition A
compression_start_early_warning = définition C
compression_start_robustness_band = [A, C, E]
```

Autrement dit :
A devient le label officiel des études et du reporting.
C sert de signal précoce mais non canonique.
E sert de contrôle de robustesse descriptif.

Ce choix est robuste, simple, défendable, et compatible avec une relecture économique.

### Correctifs immédiats et politique de vérité des données

La priorité n'est plus de lancer de nouveaux modèles. La priorité est de rendre la donnée juridiquement propre au sens méthodologique.

#### Correctifs à faire tout de suite

| Priorité | Action | Acceptation |
|---|---|---|
| P0 | Faire de reports/daily/latest.json ou de premium_daily_head.json l'unique source live autoritative | Un seul fichier est lu par le dashboard, le rapport, l'API et les visuels |
| P0 | Propager dans le journal V27 les champs record_status, collected_at_utc, collected_at_paris, effective_session_date | Chaque ligne est étiquetée PROVISIONAL, FINAL, SETTLING ou REVISED |
| P0 | Mettre en place une politique de révision append-only | Un même price_date peut exister en PROVISIONAL puis FINAL, jamais réécrit silencieusement |
| P0 | Gater toutes les synthèses premium sur FINAL par défaut | Aucun dashboard ne doit résumer un jour non final sans warning rouge |
| P1 | Ajouter cbot_close_date, eurusd_close_date, cbot_provider, fx_provider, contract_selection_rule | Toute reconstruction live devient audit-able |
| P1 | Rejouer V122/V123/V132/V145/V146/V147 sur la date la plus fraîche du journal | Les divergences de fraîcheur disparaissent |
| P1 | Ajouter un champ disabled_diagnostics partout | Si une composante est nulle ou absente, elle doit être explicitement neutralisée et visible |
| P2 | Formaliser l'écart entre curve_shape et curve_overall | Plus d'ambiguïté entre front-next et lecture globale de courbe |

#### Politique finale de session

La règle que je recommande est stricte et simple :

```
si capture < 18:30 Europe/Paris  -> PROVISIONAL
si 18:30 <= capture < 18:35      -> SETTLING
si capture >= 18:35              -> FINAL
si un FINAL existe déjà et qu'un nouveau snapshot diffère -> REVISED
```

Pour la UI et les rapports :

```
HEAD / dashboard / journal_summary :
- lire uniquement le dernier FINAL disponible ;
- si seul PROVISIONAL existe pour le jour courant, afficher "SESSION NON FINALE".
```

Cette règle est directement cohérente avec la documentation Euronext sur le contrat maïs et sur l'extension des horaires.

### Feuille de route priorisée V122–V150+

La bonne feuille de route n'est pas "encore plus de features". C'est une feuille de route en trois étages : hardening, leading data, recherche de déclenchement.

#### Matrice V122–V149 auditée

| Ticket | Statut constaté | Verdict d'audit | Action suivante |
|---|---|---|---|
| V122 consistency | Implémenté mais artefacts divergents | À rejouer | rejouer sur le journal 10 juin avec vérité de session |
| V123 freshness | Implémenté | À renforcer | imposer disabled_diagnostics et gate FINAL |
| V124 active monitoring | Implémenté | À garder | recalibrer sur 10/20/30 jours et jours FINALS |
| V125 curve accumulation | Implémenté | À garder | continuer forward, exposer spreads dans le head |
| V126 MATIF substitution | Implémenté | À garder | brancher le journal MATIF frais dans la synthèse live |
| V127 weather extremes | Partiellement vivant via journal | À compléter | construire la vraie revision tape et les labels lead-fixed |
| V128 intraday aligned probe | Watchlist | À accélérer | documenter les sources minute et les limites |
| V129 event library | Correct comme ex-post | À garder explicatif | enrichir avec horaires exacts USDA/MARS/FAM |
| V130 regime econometrics | Prometteur | À revalider | rerun après nettoyage start_date + FINAL-only |
| V131 target v3 | Intéressant | À garder | réévaluer sur journée finale seulement |
| V132 synthesis v3 | Fonctionne conceptuellement | À corriger | synchroniser avec latest live |
| V133 monthly report | Stale | À corriger | reconstruire mensuellement depuis le head unique |
| V134 sourcing plan | Bon | À mettre à jour | ajouter contacts/costs réels et plan d'email |
| V135 checkpoint | Existe | À rafraîchir | régénérer après cohérence live |
| V136 | Non stabilisé | Ouvert | intégrer dans le lot météo / revisions |
| V137 event dates | Bon ex-post | À garder | passer à calendrier exact |
| V138 horizon | Utile | À garder | enrichir par régimes et number-at-risk |
| V139 state machine | Bonne idée | À garder | l'alimenter uniquement via source live cohérente |
| V140 weather revision engine | Prévu | P1 | moteur de révisions lead-fixed |
| V141 curve forward validation | Prévu | P1 | valider front-next et Nov-Mar sur forward |
| V142 MATIF forward validation | Prévu | P1 | confirmer substitution en conditions live |
| V143 catalyst enrichment | Descriptif | Explanatory only | utile pour casebook, pas pour décision |
| V144 proxy-vs-official 10/40/90 | Prévu | P1 | activer à 10 puis 40 jours |
| V145 lifecycle report | Stale | À reconstruire | brancher source unique |
| V146 dashboard v4 | Stale | À reconstruire | consommer head unique |
| V147 milestone report | Existe | À garder | automatiser 10/40/90/180/365 jours |
| V148 decision checkpoint 40d | Trop tôt | Wait | à déclencher automatiquement |
| V149 multiview visuals | Utile | À reprendre | refaire avec CI, médiane, quantiles, n-at-risk |

#### Tickets nouveaux à ouvrir immédiatement

| Ticket | Priorité | Objet | Critère d'acceptation |
|---|---|---|---|
| V150 | P0 | Sessionized Official Journal | journal avec PROVISIONAL/FINAL/REVISED, tests d'invariants verts |
| V151 | P0 | Premium Head Single Source | plus aucune divergence entre head, dashboard, latest report |
| V152 | P1 | Compression Event Study 2.0 | event study A-aligné [-30,+90], bootstrap CI, médiane, quantiles, censure |
| V153 | P1 | START vs IN_PROGRESS Split | deux scores séparés avec confusion matrices et calibration |
| V154 | P1 | Spread Relaxation Module | front-next, Nov-Mar, curve narrowing disponibles live et backtestés proxy |
| V155 | P1 | Watchlist Tiers Frontier | matrice complète 0.5/0.75/1.0/1.25/1.5/2.0 avec profit/day, n, stop rate |
| V156 | P2 | Long-premium secondary dataset | dataset basis_z<-1 exploitable en module secondaire, jamais fusionné au short |
| V157 | P1 | Multi-contract basis variants | comparatif front / most-liquid / Nov / Mar avec mêmes règles de roll |
| V158 | P0 | Official Acquisition Package | mails, demandes CSV, champs exacts, contacts, budget |
| V159 | P0 | Reproducibility Test Pack | suite de tests d'intégrité et de no-lookahead verte |
| V160 | P2 | Synthetic event sampling | harvesting autour d'événements sans fuite d'étiquette |

La vraie priorité chronologique est : V150 → V151 → V152 → V153 → V154 → V158 → V159.

### Protocoles expérimentaux et jeux de tests

#### Refonte conceptuelle du bloc "trigger"

Le dépôt a déjà montré une chose essentielle : le score actuel n'est pas un score de déclenchement. Il faut donc changer la cible.

Je recommande les cibles suivantes :

```
START_h5   = le start A survient dans les 5 jours à venir, et n'a pas déjà commencé à t
START_h10  = idem sur 10 jours
START_h20  = idem sur 20 jours

INPROG_h5  = une compression additionnelle Δz >= 0.3 survient sous 5 jours
INPROG_h10 = idem sur 10 jours
```

Le score actuel V106 doit être renommé :

```
COMPRESSION_PROGRESS_SCORE
```

et non plus COMPRESSION_TRIGGER_SCORE.

Ensuite seulement, on construit un vrai START_TRIGGER_SCORE.

#### Protocole détaillé des expériences pré-compression

| Famille | Features autorisées à t | Cible | Métriques | OOS |
|---|---|---|---|---|
| CBOT intraday / overnight | gap vs settle J-1, move 30–60 min avant 18:30 Paris, retour depuis plus bas du jour | START_h5/h10 | AUC OOF, precision@k, lead-time | LOYO + embargo |
| CBOT techniques | cross SMA5/SMA20, close > MA5, RSI rebound depuis zone survendue | START_h5/h10/h20 | AUC OOF, calibration | LOYO |
| CBOT volume/OI | volume percentile, OI shock, volume×direction | START_h10 | AUC, lift vs base rate | LOYO |
| EMA exhaustion | wick proxy, close<open, failure to make new high, front contract reversal | START_h5 | precision@k, recall | OOS chronologique |
| Curve relaxation | Δ(front-next), Δ(Nov-Mar), passage forte backwardation → narrowing | START_h10/h20 | AUC, median lead-time | OOS chronologique |
| MATIF wheat/corn reversal | ratio 3d/5d reversal, z-score down, divergence with basis | START_h10/h20 | AUC, Brier, calibration | LOYO |
| Weather revisions US | Δjours >32°C, Δjours >35°C, Δ pluie lead 3/5/7, dispersion run | START_h5/h10 | AUC, precision@k | dates d'émission exactes |
| Weather revisions EU | mêmes variables sur zones UE | START_h10/h20 | AUC, lift, hazard shift | dates d'émission exactes |
| COT changes | ΔMM net %OI, short-covering, percentile extreme unwind | START_h20 | AUC épisode, lead-time | hebdo, lag publication |
| Event calendars | WASDE, Grain Stocks, Acreage, FranceAgriMer, MARS | START_h5/h10 | confusion matrix, precision au voisinage de l'événement | horaires exacts |

La règle absolue est : si l'horodatage exact n'est pas connu, on lagge d'une session. Aucun compromis.

#### Protocole final pour COMPRESSION_TRIGGER_SCORE

Le score doit être évalué sur deux univers distincts :

- panel quotidien : tous les jours où basis_z > 1
- panel épisode : les 42 épisodes / 41 starts datés

Sur le panel quotidien, il faut produire : confusion matrices, courbes de calibration, AUC OOF, precision@k, recall, détection "already started" versus "future start".

Le livrable doit obligatoirement contenir une table de ce type :

| Score | Univers | Cible | AUC OOF | Base rate | Verdict |
|---|---|---|---|---|---|
| Progress Score v1 | jours basis_z>1 | INPROG_h10 | 0.578 | 0.651 | descriptif seulement |
| Start Score v1 | jours basis_z>1 non déjà-started | START_h10 | à mesurer | à mesurer | accept / reject |
| Start Score logit baseline | épisodes | START_h10 | à mesurer | à mesurer | accept / reject |

#### ACTIVE_SIGNAL_HEALTH et survival

Le bloc ACTIVE_SIGNAL_HEALTH doit être définitionnel, pas "inspiré par le PnL".

| Horizon | HEALTHY | WATCH | ADVERSE_LIKE |
|---|---|---|---|
| Jour 10 | Δz <= -0.10 ou Δbasis <= -2 €/t | proche de 0 | widening net |
| Jour 20 | MFE >= 5 ou z<=0.5 | compression faible | MFE<3 + widening + tension haute |
| Jour 30 | compression visible et non censurée | lente mais vivante | chemin défavorable persistant |

Le survival doit être refait par régimes : tier de signal, CBOT_SUPPORT, PHYSICAL_TENSION, ADVERSE_RISK, SUBSTITUTION_SUPPORT.

Sorties obligatoires : Kaplan-Meier time_to_z0.5, Kaplan-Meier time_to_z0, tables number at risk, hazard plots, censure explicite.

#### Augmenter la taille d'échantillon sans baisser la qualité

Le dépôt a déjà une base utile avec V149, qui donne le compromis quantité/qualité selon le seuil basis_z.

| Seuil | n_signaux | taux d'atteinte z<=0.5 sous 90j | compression moyenne |
|---|---|---|---|
| 0.5 | 62 | 0.984 | 24.5 €/t |
| 0.75 | 52 | 0.962 | 25.1 €/t |
| 1.0 | 42 | 0.929 | 25.0 €/t |
| 1.25 | 33 | 0.909 | 24.7 €/t |
| 1.5 | 29 | 0.931 | 25.0 €/t |
| 2.0 | 18 | 1.000 | 27.8 €/t |

Mais V149 a raison de rappeler que ce taux est un best-case MFE-like, pas un PnL réalisé. Donc l'augmentation d'échantillon doit se faire en watchlists, pas en relâchant la baseline.

Recommandation opérationnelle :

```
Trade baseline inchangée : basis_z > 1.0
Watchlists :
- W0.75 = 0.75 <= z < 1.0 avec CBOT_SUPPORT>=MEDIUM et PHYSICAL_TENSION!=HIGH
- W0.50 = 0.50 <= z < 0.75 pour event-study/monitoring uniquement
Confirmed overlays :
- C1.25, C1.50, C2.00 pour demi-vie/régime
```

À cela s'ajoutent trois modules d'extension sans fuite : spread-based signals sur front-next et Nov-Mar, long-premium secondary dataset (basis_z<-1) séparé du short, multi-contract tests : front, most-liquid, Nov, Mar.

#### Jeux de tests reproductibles

| Test | Ce qu'il garantit |
|---|---|
| test_official_journal_has_session_fields | plus aucune ligne sans vérité de session |
| test_no_dashboard_reads_stale_artifact | UI et rapports consomment la source unique |
| test_cbot_eur_conversion_roundtrip | conversion cents/100 / EURUSD * 39.3679 stable |
| test_contract_selection_rule_explicit | front/most-liquid/nearby toujours documenté |
| test_trigger_labels_no_lookahead | un START_h10 n'utilise aucune variable postérieure à t |
| test_event_calendar_timestamp_policy | lag d'une session si l'horaire exact manque |
| test_start_date_A_C_E_consistency | A reste la référence et les sensibilités restent proches |
| test_official_vs_proxy_freshness_gate | pas de synthèse live si les couches sont déphasées |
| test_final_over_provisional_precedence | les vues premium lisent toujours le dernier FINAL |
| test_visuals_use_final_only_by_default | plus de visuel "live" contaminé par des PROVISIONAL |

### Plan d'acquisition de données et coûts

#### Sources gratuites et immédiatement actionnables

| Source | Ce qu'elle apporte | Accès | Coût | Verdict |
|---|---|---|---|---|
| Eurostat COMEXT | flux import/export mensuels et annuels, bulk CSV depuis janv. 1988 | bulk download Eurostat | 0 | GO |
| FranceAgriMer | cotations céréales françaises quotidiennes depuis 2001, datasets maïs/Céré'Obs/stocks/export | data.gouv / datasets FAM | 0 | GO |
| JRC MARS | bulletins mensuels de conditions de culture et prévisions de rendement UE | site JRC / AGRI4CAST | 0 | GO |
| Open‑Meteo Historical Forecast | série continue de prévisions archivées, couverture 2021/2022+ selon modèle | API publique | 0 | GO |
| Open‑Meteo Previous Runs | variables à lead fixe day1…day7, historiques majoritairement depuis janv. 2024, GFS T2m depuis mars 2021 | API publique | 0 | GO |
| CFTC COT disaggregated | managed money, OI, changements hebdo | CSV public CFTC | 0 | GO |
| USDA WASDE calendar | dates officielles de publication | site USDA | 0 | GO |
| NOAA NOMADS GFS/GEFS | forecast grids gratuits, filtre GRIB, accès GFS/GEFS | NOMADS | 0 | GO |

#### Sources payantes ou à devis

| Source | Produit utile pour vous | Coût public visible | Lecture budget |
|---|---|---|---|
| Euronext | Web Services historique JSON ; NextHistory EOD Summary SFTP | non publié, contact commercial | meilleure voie officielle, probablement pas "10 €" |
| Barchart | OnDemand getHistory / restricted session / APIs usage-based | devis | bonne voie proxy/intraday exploratoire |
| Barchart | Premier téléchargement historique sur symboles publics | 29.95 USD/mois ; 239.95 USD/an | option low-cost pour test rapide, non officielle |
| LSEG | DataScope Plus / Tick History | devis | vraisemblablement hors budget étudiant "léger" |
| CQG | historique + connectivité Euronext | devis | institutionnel, probablement hors budget étudiant léger |
| Bloomberg | terminal / enterprise data | devis | institutionnel, très probablement hors budget étudiant léger |

#### Ce qu'il faut demander en priorité

L'ordre optimal est le suivant :

**Premier choix : Euronext Data Solutions** — Demande officielle à datasolutions@euronext.com pour un one-off CSV/Excel de recherche étudiante, non commercial, non redistribué. Euronext documente Web Services et NextHistory comme voies d'accès aux données historiques, et son équipe Data Solutions est le point de contact naturel.

**Second choix : Barchart Solutions** — Demande à solutions@barchart.com pour un devis usage limité ou un one-off export, en précisant que vous ciblez un projet étudiant de fin d'année, non commercial, portant sur Euronext Corn EMA et MATIF Wheat EBM. Barchart expose officiellement getHistory, des historiques minute / EOD, et des services usage-based.

**Troisième choix : Barchart Premier** — Si le budget est extrêmement serré, testez un mois de Barchart Premier pour vérifier si les symboles utiles sont téléchargeables publiquement. C'est la seule voie "cheap" publique clairement visible. Elle n'est pas officielle, mais elle peut accélérer un prototype d'exploration.

#### Demande type recommandée

```
Objet : Demande de données historiques Euronext Corn / projet étudiant de recherche

Bonjour,

Je mène un projet étudiant de fin d'année consacré à l'étude de la prime entre le contrat maïs Euronext Paris (EMA) et le contrat corn CBOT.
L'objectif est strictement académique : recherche, statistiques, visualisations et comparaison de régimes de marché.
Il n'y a aucun usage commercial, aucune redistribution des données, et aucun usage de trading réel.

Je cherche idéalement un export historique quotidien (CSV/Excel) couvrant :
- Euronext Corn Futures (EMA, DPAR), toutes échéances listées et expirées si possible
- settlement, open, high, low, volume, open interest
- période souhaitée : 2014 à aujourd'hui
- si disponible également : Euronext Milling Wheat (EBM) sur la même période

Si un accès standard n'est pas adapté à un projet étudiant, un export ponctuel "one-off" ou un format simplifié serait déjà extrêmement utile.

Je peux bien entendu préciser le périmètre exact, les champs souhaités et signer un engagement d'usage académique / non redistribution.

Merci beaucoup pour votre aide,
[Nom]
[Établissement]
[Projet de recherche étudiant]
```

#### Plan intraday minimal viable

Le plan intraday ne doit pas partir sur de la data tick tout de suite. Il doit viser un minimum viable causal.

**Euronext public** — Le dépôt a déjà identifié deux appels utiles côté public :

```
# snapshot contrats actifs du jour
https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/EMA/DPAR

# historique de chart pour une maturité active
https://live.euronext.com/en/intraday_historical/settlements/getChartData/EMA-DPAR/max?fOrO=F&md=01-09-2026&cOrP=&sp=
```

Cela suffit pour : capturer les contrats actifs, sonder la profondeur historique réellement accessible pour les maturités encore actives, confirmer que le public n'expose pas un backfill profond expiré.

**Barchart** — L'API getHistory couvre tick, minute bars et EOD. Le site Barchart documente aussi un getRestrictedSessionHistory et précise dans sa FAQ des limites de pagination typiques, ainsi que le fait que le comportement de settlement/close peut dépendre du mode d'accès.

**Open‑Meteo** — Le plus rentable est d'utiliser : Historical Forecast API pour reconstruire le passé "forecast-like", Previous Runs API pour les révisions lead-fixes (day1..day7).

### Visuels et diagrammes à produire

#### Visuels prioritaires

| Visuel | Spécification minimale |
|---|---|
| Event study aligned start | t ∈ [-30,+90], moyenne + médiane + q25/q75 + bootstrap CI 95 %, nombre d'épisodes censurés |
| Survival regime charts | KM pour z→0.5 et z→0, avec number at risk, par tier et par régimes |
| Half-life heatmap | grille CBOT_SUPPORT × PHYSICAL_TENSION × ADVERSE_RISK |
| Threshold frontier | n_signaux, profit/day, mean pnl, stop rate, median days par seuil |
| Trigger diagnostics | calibration, confusion matrices, séparation START vs IN_PROGRESS |
| Vendor/source matrix | tableau comparatif sources/coûts/accès/risques |

#### Pipeline quotidien recommandé

```
Capture 17:55 Paris  -> Capture 18:35 Paris -> Capture 20:15 Paris
   -> Append journal avec status
   -> Rebuild premium_head unique
   -> Rebuild dashboard
   -> Rebuild monthly / lifecycle / milestones
   -> Run consistency + freshness
```

#### Timeline forward (jalons)

- **10 jours** : premier check technique proxy vs officiel ; premier health report final-only.
- **40 jours** : premier checkpoint sérieux ; premier survival utile sur le forward live.
- **90 jours** : premier audit proxy vs officiel crédible ; première relecture des scores de trigger.
- **180 jours** : première validation forward exploitable ; première lecture robuste des régimes live.
- **365 jours** : première vraie conclusion sur l'indicateur live ; éventuelle ouverture paper-trading research.

### Questions ouvertes et limites (de l'audit)

L'audit ne remet pas en cause la thèse centrale. Il montre plutôt que l'étude entre dans sa phase difficile : la partie "signal moyen" est largement faite, la partie "timing précis et qualité live" commence seulement.

Les limites ouvertes sont donc très claires. La première est l'absence de vérité de session persistée dans le journal actuel. La deuxième est l'absence de backfill officiel profond, qui empêche encore de sanctifier le z rolling officiel et le backtest des diagnostics de courbe. La troisième est que le timing du départ reste pour l'instant non démontré, et que le score actuel doit être requalifié comme score d'avancement. La quatrième est que plusieurs synthèses premium intégrées au dépôt sont stales par rapport au latest.json, ce qui empêche encore de considérer le produit comme un système live cohérent.

La conclusion stratégique est donc la suivante : ne touchez pas à la baseline ; n'essayez pas d'arracher plus de trades en abaissant le seuil comme si c'était un gain gratuit ; durcissez la vérité des données, séparez START et IN_PROGRESS, exploitez massivement les sources gratuites leading, et ouvrez en parallèle la demande officielle Euronext pour un export historique étudiant. C'est la route la plus sérieuse pour passer de "bonne étude prometteuse" à "indicateur research robuste et défendable".

---

## Partie 2 — Lecture critique de l'audit

> Mon évaluation de l'audit : ce qui est juste, ce que je nuance, ce qui manque. L'audit est de très
> bonne qualité et je le valide à ~90 %. Voici où j'ajoute de la valeur.

### 2.1 Points sur lesquels je suis pleinement d'accord

- **La hiérarchie « vérité des données avant nouveaux modèles ».** C'est correct et c'est la marque
  d'un projet mûr. Un score de plus n'a aucune valeur tant que `record_status` n'est pas dans le
  journal. P0 = session truth. Sans discussion.
- **La séparation START vs IN_PROGRESS.** C'est l'apport conceptuel le plus important de l'audit.
  V106 (score inversé) n'est pas un échec : c'est une **découverte de structure** — le marché
  price-in la compression en cours. Renommer en `COMPRESSION_PROGRESS_SCORE` est la bonne décision
  intellectuelle.
- **Choix A pour `compression_start_date`** avec bande [A,C,E]. Robuste, scale-free, défendable.
- **Watchlists au lieu d'abaisser la baseline.** Le tableau de seuils V149 est un piège classique :
  le taux d'atteinte z≤0.5 « best-case MFE » monte quand on baisse le seuil, mais c'est de
  l'illusion d'optique (plus de temps, plus de chemin → plus de chances de toucher). Garder
  baseline z>1.0 figée, étendre en watchlist : correct.

### 2.2 Ce que je nuance ou corrige

- **« Le noyau économique est déjà trouvé ».** À moitié vrai. Le noyau *statistique descriptif* est
  trouvé (le basis est stationnaire, demi-vie ~17j, il revient). Mais le **mécanisme causal** n'est
  PAS établi proprement : V16 a rejeté la fair-value macro, V35 a montré que le mécanisme de
  compression n'est pas prévisible, V21 dit que la compression vient surtout d'une HAUSSE CBOT
  relative. On a un fait stylisé robuste, pas une théorie. → voir R1 (modèle de parité physique) et
  R2 (cointégration/ECM) qui visent justement à fournir l'ancrage économique manquant.
- **« 42 occurrences, win rate 81 % ».** Le danger n°1 ici n'est pas dans l'audit : c'est le
  **multiple testing / data-snooping**. Le dépôt a exploré des dizaines de variantes (V3→V149). Avec
  42 trades et autant d'essais, un win rate de 81 % peut être en partie sur-ajusté à l'historique.
  L'audit ne mentionne PAS de correction pour essais multiples (White Reality Check, Hansen SPA,
  PBO, Deflated Sharpe). C'est le **principal angle mort de l'audit**. → toute la Partie 5.
- **AR(1) demi-vie 17.1j vs horizon trade réel 28.6j (V138).** L'audit garde « demi-vie 17j » comme
  validé mais V138 a trouvé que la demi-vie du *niveau* ≠ l'horizon du *trade* (×3). Il faut traiter
  ce désaccord frontalement, pas le laisser coexister. → X7.
- **Le backfill officiel.** L'audit a raison que ce n'est pas bloquant. Mais il sous-estime une
  voie : on PEUT reconstruire un proxy de settlement officiel long et défendable en croisant
  plusieurs sources gratuites (FranceAgriMer cotation rendu Rouen/Bordeaux, CBOT officiel, EUR/USD
  BCE) et en calibrant le proxy sur les 9+ jours officiels désormais disponibles. → R3, X8.

### 2.3 Ce qui manque dans l'audit (les vrais ajouts)

L'audit est excellent sur la **plomberie** et la **discipline forward**. Il est plus faible sur trois
fronts que je veux développer dans ce document :

1. **L'économie structurelle.** Aucun modèle de *parité d'import* (le maïs EU est importé : Black
   Sea, Brésil, Ukraine). La prime EMA/CBOT n'est pas un objet financier abstrait : c'est, à un coût
   de fret et un différentiel d'origine près, le prix du maïs rendu UE. Un modèle de parité donne une
   *fair value physique* du basis et donc une borne d'arbitrage — ce que V16 (fair value macro) n'a
   jamais testé. → R1.
2. **La rigueur statistique anti-overfitting.** Voir 2.2. → Partie 5.
3. **Les tests de falsification / placebo.** L'audit ne propose pas d'appliquer le même pipeline à
   des spreads non liés (colza Euronext vs canola ICE, blé MATIF vs blé CBOT) pour vérifier que
   l'edge n'est pas un artefact générique de mean-reversion de spread. → X5.

### 2.4 Verdict de la lecture critique

L'audit est un **excellent plan d'ingénierie et de discipline**. Ce document ajoute la **couche
scientifique** qui lui manque : ancrage économique (parité physique, cointégration), défense
anti-overfitting (essais multiples), et falsification (placebos). Les trois ensemble font passer le
projet de « pipeline propre » à « résultat publiable / soutenable ».

---

## Partie 3 — Nouveaux axes de recherche

> Chaque axe = un identifiant R#, une hypothèse, pourquoi c'est nouveau vs l'existant, et le livrable.
> Statut : `PROPOSÉ` tant qu'on n'a pas tranché ensemble.

### R1 — Modèle de parité d'import EU (fair value physique du basis) — `PROPOSÉ`

**Hypothèse.** Le maïs Euronext rendu UE est, à l'équilibre, borné par le coût de l'import marginal :
`prix_EU ≈ prix_origine_FOB (Black Sea / Brésil / US Gulf) + fret maritime + différentiel qualité/origine + marge logistique`.
La prime EMA/CBOT élevée correspond aux périodes où l'EU doit attirer / retenir de la marchandise
(tension physique), et se compresse quand l'import marginal redevient compétitif.

**Pourquoi c'est nouveau.** V16 a rejeté une fair-value *macro* (taux, FX, indices) — mais n'a jamais
testé une fair-value *physique* (parité d'import). C'est une hypothèse économique différente et bien
plus défendable agronomiquement. La mémoire projet note déjà « prime LOCALE pas artefact CBOT »
(V40/V41) et « basis~blé/maïs substitution » (V36) — la parité d'import est le cadre qui *unifie* ces
observations.

**Livrable.** Une série `import_parity_fair_value_eur_t` reconstruite à partir de sources gratuites
(FOB Black Sea/Brésil + Baltic freight proxy), et le **résidu** `basis_minus_parity` testé comme
prédicteur de compression. Si le résidu mean-reverte mieux que `basis_z` brut → ancrage économique
trouvé.

**Risque.** Données FOB Black Sea gratuites = rares et bruitées (souvent derrière paywall APK-Inform,
Refinitiv). Fallback : proxys via spreads observables + COMEXT prix unitaires d'import.

### R2 — Cointégration & modèle à correction d'erreur (VECM) EMA/CBOT — `PROPOSÉ`

**Hypothèse.** EMA(EUR) et CBOT(EUR) sont cointégrés ; le basis EST le terme de correction d'erreur.
Un VECM donne (a) la vitesse d'ajustement α (qui jambe corrige : EMA descend-il, ou CBOT monte-t-il ?
— relie V21), (b) une demi-vie *propre* du déséquilibre, (c) un test formel de la réversion.

**Pourquoi c'est nouveau.** Le dépôt a un AR(1) sur `basis_z` (V120) et a rejeté Granger OOF. Un VECM
est le bon outil : il ne teste pas une causalité directionnelle douteuse mais la **relation
d'équilibre de long terme** et la dynamique de retour. C'est l'écriture économétrique canonique de
« la prime revient ». Cela réconcilie aussi V120 (17j) et V138 (28j) : la demi-vie ECM se décompose
en correction par chaque jambe.

**Livrable.** Test Johansen (rang de cointégration), coefficients α/β, demi-vie d'ajustement,
décomposition variance de qui corrige. OOS : ré-estimation glissante, stabilité des coefficients.

**Garde-fou anti-leakage.** Estimation expanswindow, `shift(1)`, jamais de β estimé sur le futur.

### R3 — Proxy de settlement officiel long, calibré sur l'officiel récent — `PROPOSÉ`

**Hypothèse.** On peut bâtir une série de settlement EMA « quasi-officielle » 2014→aujourd'hui en
combinant les meilleurs proxys publics (FranceAgriMer rendu Rouen, close Barchart, etc.) puis en la
**calant** sur les 9+ jours de settlement officiel désormais collectés (et qui s'accumulent chaque
jour). Le biais proxy↔officiel est mesurable et corrigeable.

**Pourquoi c'est nouveau.** Aujourd'hui le backtest tourne sur proxy, le live sur officiel, et les
deux ne sont pas réconciliés statistiquement (V144 prévu mais pas activé). Avec l'accumulation
forward, on peut estimer la loi du biais et **propager l'incertitude** dans le backtest.

**Livrable.** `official_minus_proxy` : moyenne, écart-type, dépendance au régime/à la maturité ; un
backtest « proxy corrigé du biais + bande d'incertitude ».

### R4 — Détection de régime non supervisée (HMM / change-point) — `PROPOSÉ`

**Hypothèse.** Le début de compression est un **changement de régime** dans la dynamique du basis
(drift/vol). Des méthodes non supervisées — Markov-switching (HMM 2-3 états), changepoint bayésien
en ligne (BOCPD), PELT/binary segmentation — peuvent détecter le START sans étiquette, et servir de
*second avis* indépendant face au label A.

**Pourquoi c'est nouveau.** Tout le travail trigger est supervisé (on apprend le label A). Une méthode
non supervisée est un **test d'indépendance** : si HMM et label-A datent le même START, le START est
réel ; sinon, le label A est en partie arbitraire. C'est de la triangulation méthodologique.

**Livrable.** Comparaison des dates de bascule HMM/BOCPD vs label A (offset médian, accord). Hazard
de transition « HIGH→COMPRESSING » estimé. Branche éventuellement V130 (regime econometrics).

### R5 — Modèle de structure par terme de la courbe EMA (Schwartz-Smith / Nelson-Siegel) — `PROPOSÉ`

**Hypothèse.** La forme de la courbe EMA (backwardation nearby → contango) encode l'information
physique (tension de stock, convenience yield). Un modèle 2-facteurs (court terme + niveau
d'équilibre) à la Schwartz-Smith, ou un fit Nelson-Siegel des spreads, résume la courbe en 2-3
facteurs interprétables et backtestables.

**Pourquoi c'est nouveau.** Le dépôt suit `curve_shape`/`curve_overall` de façon ad hoc (et l'audit
note l'ambiguïté front-next vs global). Un modèle de structure par terme remplace ces étiquettes
floues par des **facteurs continus** (niveau, pente, courbure) directement utilisables comme features
de START_h10/h20 (famille « curve relaxation » de l'audit).

**Livrable.** Facteurs `curve_level / curve_slope / curve_curv` quotidiens (forward), corrélation au
convenience yield théorique (théorie du stockage), test comme prédicteurs de relâche de prime.

### R6 — Théorie du stockage & convenience yield comme variable explicative — `PROPOSÉ`

**Hypothèse.** La prime locale haute coïncide avec un convenience yield local élevé (stocks UE
tendus). Estimer le convenience yield depuis la courbe (R5) + le taux sans risque EUR, et le relier
aux bilans physiques (COMEXT, FranceAgriMer stocks, MARS rendements).

**Pourquoi c'est nouveau.** Donne le **chaînon manquant** entre la finance (courbe) et l'agro
(bilan). Si convenience yield ↑ ⇒ basis ↑ ⇒ compression quand le bilan se détend, on tient le
mécanisme économique que V35 cherchait sans le trouver (parce qu'il cherchait dans le prix, pas dans
le bilan).

**Livrable.** Série convenience yield ; régression bilan→CY→basis ; test de la chaîne causale en
expanding-window.

### R7 — Saisonnalité structurelle de la prime (récolte/soudure) — `PROPOSÉ`

**Hypothèse.** La prime EMA/CBOT a une saisonnalité forte : tension à la soudure UE (été), détente à
la récolte (automne, contrat Nov). Les 42 épisodes ne sont peut-être pas i.i.d. dans le temps : ils
se concentrent à certaines saisons.

**Pourquoi c'est nouveau.** V8 avait une « inversion saisonnière » FALSIFIÉE, mais c'était une
hypothèse précise (inversion), pas une cartographie saisonnière. Cartographier *quand* tombent les
starts (mois, phase du cycle cultural, contrat actif) est descriptif mais crucial pour ne pas
sur-vendre la généralité du signal.

**Livrable.** Distribution mensuelle des starts, des PnL, des adverse ; test si l'edge survit
hors-saison ; features Fourier saisonnières pour le trigger.

### R8 — Spread inter-bassins & substitution élargie (blé, orge, Black Sea) — `PROPOSÉ`

**Hypothèse.** La compression de la prime maïs est co-déterminée par le complexe céréales fourragères
EU (blé fourrager, orge) et par l'arrivée d'origines concurrentes. Le ratio MATIF blé/maïs (V126,
r=0.477) n'est qu'une porte d'entrée.

**Pourquoi c'est nouveau.** Élargit V36/V126 à un vrai *panier de substitution* (blé EBM, orge,
maïs Black Sea proxy) et teste si le résidu de substitution prédit la relâche de prime mieux qu'une
seule paire.

**Livrable.** `substitution_basket_z` ; comparaison à `wheat_corn_z` seul ; intégration watchlist.

### R9 — Quantification de l'incertitude bayésienne (petit échantillon) — `PROPOSÉ`

**Hypothèse.** Avec 42 épisodes, les point-estimates (win rate, PnL moyen, demi-vie) sont fragiles.
Un cadre bayésien hiérarchique (partial pooling par régime/saison) donne des intervalles crédibles
honnêtes et évite de sur-interpréter un sous-groupe à n=18.

**Pourquoi c'est nouveau.** Le dépôt fait du bootstrap (bien) mais pas de modèle génératif. Un
Weibull-AFT bayésien pour le time-to-reversion, avec pooling, donnerait survie + incertitude +
effets régime cohérents d'un coup, et résisterait mieux au petit n que des KM par sous-groupe.

**Livrable.** Postérieurs de demi-vie par régime, intervalles crédibles du win rate, comparaison aux
KM fréquentistes de l'audit.

### R10 — Cartographie causale formelle (DAG) & identifiabilité — `PROPOSÉ`

**Hypothèse.** Formaliser le DAG du marché (CBOT, FX, bilan EU, météo, courbe → basis → compression)
permet de dire *quelles* relations sont identifiables et lesquelles sont condamnées au confounding.

**Pourquoi c'est nouveau.** `docs/CAUSAL_MAP_CORN_MARKET.md` existe déjà mais en prose. Le passer en
DAG explicite (do-calculus léger) dirait par ex. pourquoi Granger échoue (confounding par CBOT) et
quels back-doors fermer pour estimer l'effet météo→prime proprement.

**Livrable.** DAG annoté ; liste des effets identifiables vs non-identifiables ; ce qui justifie le
lag-une-session comme stratégie d'identification minimale.

---

## Partie 4 — Nouvelles expériences

> Expériences concrètes, falsifiables, avec critère d'acceptation déclaré à l'avance. X# = expérience.
> Elles complètent les protocoles trigger de l'audit, elles ne les remplacent pas.

### X1 — Placebo sur spreads non liés — `PROPOSÉ`
**But.** Vérifier que l'edge short-premium n'est pas un artefact générique de « tout spread de basis
mean-reverte ».
**Protocole.** Appliquer EXACTEMENT le pipeline (entrée z>1, exit z→0.5, stop −20, mêmes coûts) à :
colza Euronext vs canola ICE, blé MATIF EBM vs blé CBOT, éventuellement sucre. 
**Critère.** Si les placebos donnent un edge similaire → le signal maïs n'est pas spécifique (mauvaise
nouvelle pour la thèse « prime locale maïs »). Si l'edge maïs domine nettement → spécificité
confirmée. **Déclaré avant** : on garde le résultat quel qu'il soit.

### X2 — Test d'essais multiples sur l'historique des variantes — `PROPOSÉ`
**But.** Mesurer combien du win rate 81 % survit à la correction pour data-snooping.
**Protocole.** Recenser les N variantes testées (seuils, exits, stops, features) ; appliquer White
Reality Check / Hansen SPA et calculer le Deflated Sharpe Ratio et la PBO (combinatorially purged).
**Critère.** Si Deflated Sharpe reste > 0 et PBO < 0.5 → l'edge survit. Sinon → on requalifie en
« exploratoire », honnêtement. (Détails Partie 5.)

### X3 — Reconstruction du biais proxy↔officiel — `PROPOSÉ`
**But.** Chiffrer R3.
**Protocole.** Sur tous les jours où officiel ET proxy existent (s'accumule), régresser
`official = a + b·proxy + régime` ; estimer biais & dispersion ; rejouer un backtest court avec proxy
corrigé.
**Critère.** Si |biais moyen| < ~1 €/t et stable → proxy validé pour sanctifier (partiellement) le
backtest. Si biais grand/instable → backtest reste exploratoire, priorité acquisition officielle.

### X4 — VECM EMA/CBOT & décomposition de qui corrige — `PROPOSÉ`
**But.** Chiffrer R2.
**Protocole.** Johansen sur (EMA_EUR, CBOT_EUR) expanding ; α/β ; part de correction attribuée à
chaque jambe ; demi-vie ECM vs AR(1) V120 vs horizon V138.
**Critère.** Si la jambe CBOT porte la majorité de la correction → confirme V21 (« short premium =
long CBOT relatif ») par une voie économétrique indépendante. Résout aussi le désaccord 17j/28j.

### X5 — HMM vs label A (triangulation du START) — `PROPOSÉ`
**But.** Chiffrer R4.
**Protocole.** HMM 2-3 états sur Δbasis & vol ; dater les bascules HIGH→COMPRESSING ; offset vs label
A.
**Critère.** Accord (offset médian ≤ ~3j sur ≥70 % des épisodes) → START réel et A bien posé.
Désaccord fort → label A à reconsidérer.

### X6 — Saisonnalité des starts & survie hors-saison — `PROPOSÉ`
**But.** Chiffrer R7.
**Protocole.** Histogramme mensuel des 41 starts ; split saison haute/basse ; rejouer l'edge sur
chaque sous-période.
**Critère.** Si l'edge n'existe qu'en une saison → le restreindre explicitement (filtre saison), ne
pas le vendre comme all-weather.

### X7 — Réconciliation demi-vie niveau (17j) vs horizon trade (28j) — `PROPOSÉ`
**But.** Trancher le désaccord V120/V138 noté en 2.2.
**Protocole.** Distinguer trois horizons : demi-vie AR(1) du z (niveau), temps médian jusqu'à z≤0.5
(objectif prudent), temps médian jusqu'à z≤0 (objectif full). Les mesurer sur les mêmes épisodes,
KM avec censure.
**Critère.** Produire UNE phrase canonique réconciliant les trois chiffres pour le rapport (ex :
« le z se relâche à demi-vie ~17j mais atteindre l'objectif prudent prend ~28j en médiane à cause de
la censure/des stops »).

### X8 — Stress-test coûts × slippage × roll sur l'edge — `PROPOSÉ`
**But.** Re-confirmer le « mur de coûts » avec un modèle d'exécution réaliste sur EMA illiquide.
**Protocole.** Grille de coûts tout compris (spread bid-ask back-month + slippage + roll) de 1 à 6
€/t/leg ; recalculer PnL net, win rate, profit/day par régime.
**Critère.** Identifier le coût-seuil où l'edge meurt par régime ; le publier comme contrainte
opérationnelle dure (relie V15/V13 « survit coût 5 hors crise »).

### X9 — Convenience yield depuis la courbe vs bilan physique — `PROPOSÉ`
**But.** Chiffrer R6.
**Protocole.** CY implicite (R5) ; régresser sur bilan EU (COMEXT net imports, FAM stocks, MARS
rendement) en expanding ; tester CY comme feature START.
**Critère.** Si bilan→CY→basis tient OOS → mécanisme économique documenté (gros apport rapport).

### X10 — Multi-contrat : front vs most-liquid vs Nov vs Mar — `PROPOSÉ`
**But.** Chiffrer V157 / robustesse au choix de contrat.
**Protocole.** Reconstruire le basis sur 4 définitions de contrat avec mêmes règles de roll ; rejouer
l'edge ; mesurer la sensibilité.
**Critère.** Si l'edge est stable across contrats → robuste. Si dépendant du choix → documenter le
choix comme hyperparamètre sensible (risque overfit).

---

## Partie 5 — Rigueur statistique

> L'angle mort de l'audit. Avec ~42 trades et des dizaines de variantes explorées (V3→V149), la
> question n'est plus « le win rate est-il haut » mais « combien survit à la correction pour essais
> multiples ». Sans cette partie, l'étude reste attaquable.

### 5.1 Le problème : data-snooping sur petit échantillon

On a (a) un petit n (42 épisodes, 18 au seuil 2.0), (b) un grand nombre d'hypothèses testées au fil
des versions, (c) des choix d'hyperparamètres (seuil, exit, stop) optimisés sur le même historique.
C'est le terrain de jeu exact du faux positif. Toute conclusion « validée » de l'audit doit passer ce
filtre avant d'être sanctifiée.

### 5.2 Boîte à outils à intégrer

| Outil | Ce qu'il corrige | Sortie attendue |
|---|---|---|
| **Deflated Sharpe Ratio** (Bailey–López de Prado) | Sharpe gonflé par le nombre d'essais et la non-normalité | un Sharpe « dégonflé » + p-value |
| **PBO — Probability of Backtest Overfitting** (CSCV) | probabilité que la config choisie soit la meilleure in-sample mais sous-médiane OOS | une proba ∈ [0,1] |
| **White Reality Check / Hansen SPA** | meilleure stratégie vs univers de stratégies, sous l'hypothèse nulle « pas d'edge » | p-value du data-snooping |
| **Purged + Embargoed K-Fold CV** (López de Prado) | leakage par chevauchement des labels (nos fenêtres [-30,+90] se chevauchent !) | folds propres, AUC OOF honnête |
| **Combinatorial Purged CV** | un seul split OOS = fragile | distribution de performances OOS |
| **Bootstrap par blocs (épisode)** | autocorrélation intra-épisode | CI honnêtes sur win rate / PnL |

> ⚠️ Point critique souvent oublié : nos labels d'event-study se **chevauchent dans le temps**
> (fenêtre +90j). Un K-fold naïf fuit. Le purging+embargo n'est pas optionnel ici, c'est obligatoire.

### 5.3 Protocole de « sanctification » d'un résultat

Avant de marquer un résultat `VALIDÉ` dans le rapport pro, il doit passer :
1. CV purgée+embargoed (pas de leakage de label chevauchant).
2. Deflated Sharpe > 0 en tenant compte du nombre d'essais déclarés.
3. PBO < 0.5.
4. Bootstrap par blocs : CI du win rate ne touche pas 0.5 (pour un binaire) / PnL CI > coûts.
5. Survie au placebo (X1) : l'edge maïs > edge des spreads témoins.

Un résultat qui échoue ≥2 de ces tests est requalifié `EXPLORATOIRE`, jamais `VALIDÉ`.

### 5.4 Pré-enregistrement (registered-report interne)

Pour la suite forward : **geler les hypothèses AVANT** de voir les nouveaux jours. Écrire dans ce
document, daté, la prédiction (ex : « START_h10 atteindra AUC OOF ≥ 0.60 ») puis la confronter au
forward. C'est la seule défense réelle contre le p-hacking sur les données qui s'accumulent. La
discipline forward de l'audit devient alors une *vraie* validation out-of-sample temporelle.

---

## Partie 6 — Nouvelles sources de données

> En plus de la liste de l'audit (COMEXT, FranceAgriMer, MARS, Open-Meteo, COT, WASDE, NOMADS), voici
> des sources/angles que l'audit n'a pas listés. D# = source de donnée.

### D1 — Prix unitaires d'import COMEXT (proxy parité) — `À ÉVALUER`
COMEXT donne valeur ET quantité par flux → **prix unitaire moyen d'import** du maïs par origine
(Ukraine, Brésil, Serbie…). Mensuel, laggé ~6-8 semaines, mais c'est un proxy gratuit de prix
d'origine pour R1 (parité). Nowcastable via FAM exports hebdo.

### D2 — Fret maritime / Baltic indices — `À ÉVALUER`
Pour R1 il faut un coût de fret. Baltic Dry / Panamax : niveaux gratuits parfois disponibles
(TradingEconomics, presse). Sinon proxy via prix énergie + distance. Brique du modèle de parité.

### D3 — Positionnement Euronext (MiFID II / ESMA position reports) — `À ÉVALUER`
L'équivalent EU du COT existe : rapports de positions hebdomadaires sur dérivés de matières premières
(ESMA / autorités nationales). Permettrait un COT *local* (positionnement sur EMA lui-même), bien
plus pertinent que le COT CBOT pour la jambe EU. À vérifier en disponibilité/qualité.

### D4 — JRC Combined Drought Indicator & SPEI — `À ÉVALUER`
Au-delà des prévisions MARS, le JRC publie un indicateur de sécheresse combiné et des cartes SPEI/
soil moisture. Variable physique directe de stress UE pour R6/R7, gratuite.

### D5 — US Drought Monitor & NOAA CPC — `À ÉVALUER`
Pour la jambe US : US Drought Monitor (hebdo), CPC outlooks. Complète Open-Meteo pour les « weather
revisions US » de l'audit, avec un signal de stress réalisé déjà agrégé.

### D6 — EUR/USD BCE (taux de référence officiel) — `À VÉRIFIER dans le dépôt`
La conversion CBOT→EUR dépend du FX. L'audit demande `fx_provider` explicite. Le **taux de référence
BCE quotidien (16h CET)** est gratuit, officiel, horodaté — idéal pour figer une règle FX auditable et
éliminer l'`abs_err=2.77` du 3 juin (probable désalignement FX/session).

### D7 — Ukraine/Black Sea export data (proxy origine) — `À ÉVALUER`
APK-Inform / UkrAgroConsult publient des prix FOB (souvent paywall) mais des agrégats gratuits
existent (presse spécialisée, rapports USDA FAS GAIN). Pour R1, même bruité, ça borne l'origine
marginale du maïs importé en UE.

### D8 — USDA FAS GAIN reports & PSD — `À ÉVALUER`
Rapports pays gratuits (production/export Ukraine, Brésil) + base PSD (Production, Supply &
Distribution) mondiale. Contexte bilan pour R1/R6.

> **Garde-fou commun à toutes ces sources** : chacune doit déclarer sa **date de publication réelle**
> (pas la date de référence de la donnée) pour respecter le lag-une-session. Une donnée mensuelle de
> mai publiée mi-juin ne peut PAS servir de feature au 1er juin.

---

## Partie 7 — Backlog de tickets additionnels

> En plus des V150–V160 de l'audit (qu'on reprend tels quels), voici les tickets que génèrent les
> Parties 3-6. À convertir vers `.ai/TICKETS.md` seulement quand on les aura tranchés ensemble.

| ID proposé | Prio | Objet | Issu de | Critère d'acceptation |
|---|---|---|---|---|
| T-PARITY (V161) | P1 | Modèle parité d'import EU + résidu basis | R1, D1, D2, D7, D8 | série fair-value reconstruite, résidu testé vs basis_z |
| T-VECM (V162) | P1 | Cointégration Johansen + ECM EMA/CBOT | R2, X4 | α/β/demi-vie ECM, décompo de qui corrige |
| T-PROXYBIAS (V163) | P1 | Biais proxy↔officiel calibré | R3, X3 | loi du biais, backtest proxy-corrigé |
| T-REGIME-HMM (V164) | P2 | START non supervisé (HMM/BOCPD) vs label A | R4, X5 | offset HMM↔A, hazard transition |
| T-CURVE-TS (V165) | P2 | Facteurs structure par terme (niveau/pente/courbure) | R5 | 3 facteurs forward + test comme features START |
| T-CONVYIELD (V166) | P2 | Convenience yield ↔ bilan physique | R6, X9, D4, D5 | chaîne bilan→CY→basis testée OOS |
| T-SEASON (V167) | P1 | Saisonnalité des starts & survie hors-saison | R7, X6 | distribution mensuelle, edge par saison |
| T-SUBBASKET (V168) | P2 | Panier de substitution élargi | R8 | substitution_basket_z vs wheat_corn_z |
| T-BAYES (V169) | P2 | Survie bayésienne hiérarchique | R9 | postérieurs demi-vie/win rate par régime |
| T-DAG (V170) | P3 | DAG causal formel & identifiabilité | R10 | DAG + liste effets identifiables |
| T-PLACEBO (V171) | **P0** | Placebo spreads non liés | X1 | edge maïs vs colza/blé témoins |
| T-OVERFIT (V172) | **P0** | Pack anti-overfitting (DSR/PBO/SPA/purged CV) | X2, Partie 5 | DSR, PBO, p-value SPA publiés |
| T-COSTGRID (V173) | P1 | Stress coûts×slippage×roll par régime | X8 | coût-seuil de mort de l'edge par régime |
| T-FX-BCE (V174) | P1 | Règle FX BCE officielle horodatée | D6 | abs_err reconstruction CBOT réduit |

**Priorité scientifique chronologique recommandée** (après le hardening P0 de l'audit V150/V151) :
`T-OVERFIT → T-PLACEBO → T-FX-BCE → T-VECM → T-PARITY → T-SEASON → T-PROXYBIAS → reste`.

Rationale : avant d'enrichir, **savoir ce qui survit** (overfit + placebo). Ensuite ancrer
économiquement (VECM + parité). Ensuite seulement, étendre.

---

## Partie 8 — Questions ouvertes

> Les décisions à trancher ENSEMBLE. Chaque question attend une réponse qu'on consignera au Journal.
> Format : Q# — question — options — (décision : ___).

- **Q1 — Priorité immédiate.** On commence par le hardening de l'audit (V150 session truth) ou par la
  défense scientifique (T-OVERFIT/T-PLACEBO) ? *Mon avis : V150 d'abord (sans données propres, les
  tests d'overfit testent du bruit), puis T-OVERFIT tout de suite après.* (décision : ___)

- **Q2 — Ambition du projet.** Cible finale = (a) indicateur research défendable / mémoire, (b)
  système live paper-trading, (c) publication / soutenance académique ? Ça change le curseur
  rigueur vs produit. (décision : ___)

- **Q3 — Acquisition officielle.** On envoie le mail Euronext Data Solutions maintenant (le délai de
  réponse est long, autant lancer tôt) ou on attend d'avoir le package V158 complet ? *Mon avis :
  envoyer une première prise de contact maintenant.* (décision : ___)

- **Q4 — Parité d'import (R1).** On l'attaque ? C'est l'apport économique le plus fort mais le plus
  data-intensive (fret + FOB origine). Vaut-il l'effort vs rester sur l'approche statistique pure ?
  (décision : ___)

- **Q5 — Budget data.** Y a-t-il un budget réel (même 30 USD/mois Barchart Premier) ou on reste 100 %
  gratuit ? Détermine X3/V157 (multi-contrat a besoin d'historique propre). (décision : ___)

- **Q6 — Périmètre forward.** On gèle des prédictions pré-enregistrées (Partie 5.4) dès cette
  session ? Si oui, lesquelles ? (décision : ___)

- **Q7 — Placebos (X1).** Quels spreads témoins sont accessibles dans nos données actuelles (colza ?
  blé MATIF on l'a déjà ; canola ICE ?) — détermine la faisabilité immédiate de T-PLACEBO.
  (décision : ___)

---

## Partie 8bis — Deuxième analyse externe & plan d'implémentation

> Deuxième audit reçu (2026-06-10), intégré et fusionné avec le premier. Il **confirme** la lecture
> (vérité de session + split START/IN_PROGRESS + défense overfitting = les 3 piliers manquants) et
> ajoute du matériel actionnable : pack d'audit dur, table vendeurs avec CME DataMine, Gantt, ER,
> e-mails. Je le retiens intégralement.

### 8bis.1 — Ce qu'on peut vraiment affirmer (niveaux de confiance)

| Bloc | Ce qu'on peut dire aujourd'hui | Confiance | Suite |
|---|---|---|---|
| Baseline `basis_z > 1` | « prime élevée puis compression fréquente » crédible | Élevé | garder inchangé, RESEARCH_ONLY |
| Event study / demi-vie / objectif z→0.5 | objectif prudent > prédiction €/t exacte | Élevé | objectif primaire |
| Score « trigger » actuel | ressemble à un score d'avancement, pas de départ | Élevé | renommer COMPRESSION_PROGRESS_SCORE |
| Historique officiel EMA | amélioré en forward, trop court pour sanctifier | Élevé | accumuler + modéliser proxy↔officiel |
| Artefacts live premium | head/dashboard/monthly désynchronisés | Élevé | forcer source unique |
| Conclusion causale forte | mécanisme pas formellement démontré | Moyen | parité d'import, VECM, courbe, convenience yield |
| Robustesse statistique | overfitting/multiple testing sous-traité | Moyen→élevé | DSR/PBO/SPA/placebos avant tout « validé » |

Formulation honnête : **le fait stylisé survit, la couche de preuve doit monter d'un cran.** On n'a
pas encore la chaîne complète « donnée propre → mécanisme causal → test OOS purgé → histoire
officielle suffisante ».

### 8bis.2 — Pack d'audit dur (à exécuter AVANT toute nouvelle conclusion)

| Test d'audit | Vérifie | PASS | FAIL | Artefact |
|---|---|---|---|---|
| session_alignment_audit | toute ligne officielle porte record_status + 3 timestamps | 100 % renseigné | ≥1 ligne orpheline | `artefacts/audit/session_alignment_report.json` |
| official_final_gate_audit | dashboards ne lisent jamais du non-FINAL par défaut | 0 lecture PROVISIONAL | 1 « live » non-final sans warning | `artefacts/audit/finality_gate_report.json` |
| cbot_eur_conversion_audit | conversion cents/bu → €/t traçable | round-trip < seuil | facteur/FX incohérent | `artefacts/audit/cbot_eur_roundtrip.json` |
| settlement_vs_close_audit | settlement officiel ≠ close/last proxy | mapping explicite | mélange silencieux | `artefacts/audit/settlement_close_matrix.csv` |
| proxy_vs_official_audit | biais & dispersion proxy↔officiel | biais stable, bande documentée | non-stationnaire / trop large | `artefacts/audit/proxy_official_bias.parquet` |
| zscore_recalc_audit | recalcul exact de basis_z sans fuite | identité numérique | décalage / dépend du futur | `artefacts/audit/zscore_recalc_check.json` |
| contract_selection_audit | règle de contrat explicite et stable | front/most-liquid/Nov/Mar documentés | règles implicites | `artefacts/audit/contract_selection_report.md` |
| event_timestamp_audit | events à l'heure réelle ou laggés +1 session | 100 % horodatés/laggés | « vu avant publication » | `artefacts/audit/event_timestamp_report.csv` |

**Règle impérative de vérité des données** : aucun rapport premium, aucune calibration, aucun visuel
« live » ne consomme directement la couche brute. Passage obligatoire par le journal sessionné, puis
vue FINAL par défaut.

### 8bis.3 — Table vendeurs consolidée (gratuit + payant, contacts vérifiés)

| Source | Apport | Couverture | Coût | Contact | Priorité |
|---|---|---|---|---|---|
| Open‑Meteo Historical Forecast | prévisions archivées continues | ~2022+ | 0 (non-commercial) | info@open-meteo.com | Très haute |
| Open‑Meteo Previous Runs | leads fixes day1..day7 (révisions) | 2024+ ; GFS T2m 2021+ | 0 | info@open-meteo.com | Très haute |
| NOAA NOMADS | GFS/GEFS 0.25°, ensembles | opérationnel/modèle | 0 | portail public | Très haute |
| CFTC COT disaggregated | positionnement hebdo (mardi, publié vendredi) | 2006+ | 0 | portail public | Très haute |
| FranceAgriMer Céré'Obs | état hebdo maïs grain | campagnes | 0 | contact.cereobs@franceagrimer.fr | Haute |
| FranceAgriMer filière/prix | prix, cotations, échanges FR | publications | 0 | site public | Haute |
| CE / JRC MARS / obs. céréales | prix, prod, commerce, agro-météo, rendements | séries + bulletins | 0 | portails publics | Haute |
| Euronext Web Services | données off. RT/différé/historique JSON-REST | offre commerciale | devis | **formulaire Web Services** (vérifié) ; datasolutions@euronext.com (à reconfirmer) | **Très haute** (sanctifier EMA) |
| Barchart OnDemand getHistory | tick/minute/EOD futures | profond/symbole | devis | solutions@barchart.com | Haute |
| CME DataMine | historique officiel CME/CBOT, settlements, MBO | jusqu'aux années 1970/produit | devis/one-off ou abo | CMEDataSales@cmegroup.com | Haute (jambe CBOT) |
| Barchart Premier | test low-cost téléchargeabilité symboles | symbole | ~29.95 USD/mois (à revérifier) | contact public | Moyenne |
| Bloomberg / LSEG campus | si licence école déjà payée | licence | marginal nul possible | à vérifier en interne | Haute si dispo |

**Ordre de bataille** : (1) brancher tout de suite le gratuit (Open‑Meteo, NOMADS, CFTC,
FranceAgriMer, JRC) — ça augmente le pouvoir explicatif sans toucher la baseline ; (2) voie officielle
Euronext pour sanctifier le backtest EMA (devis, pas self-service) ; (3) CME DataMine pour la jambe
CBOT si achat avant Euronext. **Pourquoi l'officiel EMA n'a pas backfillé seul** : les surfaces
publiques Euronext donnent des snapshots + un service commercial contractualisé, pas un bulk backfill
libre → normal que l'historique officiel ne grandisse qu'en forward quotidien.

### 8bis.4 — Portefeuille d'expériences GO (falsifiables, pré-enregistrées)

| Expérience | Features autorisées | Cibles | Métriques | Anti-leakage | Verdict GO |
|---|---|---|---|---|---|
| START vs IN_PROGRESS split | features à t | START_h5/10/20, INPROG_h5/10 | AUC, PR-AUC, Brier, calibration, lead-time | expanding + LOYO + embargo | si START bat clairement le base rate |
| Curve relaxation | front-next, Nov-Mar, pente/courbure | h10/h20 | AUC, median lead-time, lift | timestamps session exacts | si gain robuste vs baseline contextuelle |
| Weather revision tape | Open‑Meteo hist+previous runs + NOAA | h5/h10 | precision@k, AUC, uplift | lead-fixed only | si day1..day7 apportent du signal OOS |
| COT regime shift | ΔMM, %OI, unwind extrêmes | h20 | AUC, recall épisode, hazard shift | vendredi laggé | si amélioration stable, sinon explanatory |
| Event calendar exact | distance event, surprise si dispo | h5/h10 | confusion matrix, precision near-event | heure exacte ou lag+1 | si survit au clustering saisonnier |
| VECM EMA/CBOT | EMA_EUR, CBOT_EUR, spread | n/a | Johansen, α/β, demi-vie ECM | expanding | si relation stable/interprétable |
| Proxy↔officiel bias | proxy, officiel, contrat, régime | n/a | biais, RMSE, stabilité | append-only | si biais stable réutilisable |
| Placebo spreads | mêmes règles exactes sur témoins | mêmes horizons | edge relatif, SPA | même protocole | si maïs domine les placebos |
| Multiple testing pack | tous les essais recensés | n/a | DSR, PBO, SPA, Reality Check | purged CV + embargo | si signal survit à la déflation |
| Saison / contrat actif | mois, campagne, contrat, phase | n/a | hazard, KM, perf stratifiée | split temporel | si utile pour expliquer/limiter |

**Règle absolue** : si l'horodatage exact d'un event est inconnu → lag d'une session. Aucun compromis.

### 8bis.5 — Tests statistiques obligatoires (gate robustesse)

| Test | Rôle | GO |
|---|---|---|
| Purged CV + embargo | fuites par labels chevauchants | si toutes les variantes évaluées purgées |
| LOYO / expanding-window OOS | réaliste saison/année-régime | si conclusions survivent par année |
| Bootstrap par blocs | dépendance temporelle | si IC reste favorable |
| White Reality Check / Hansen SPA | recherche de « meilleure variante » | si la gagnante survit |
| Deflated Sharpe / PBO | Sharpe + sélection multi-essais | si DSR > 0 et PBO raisonnable |
| Placebos | falsification spécificité maïs | si maïs > témoins |

### 8bis.6 — Tickets exécutables V122–V150 (livrables, deps, tests, GO/NO-GO)

> Cette table durcit la matrice de la Partie 1 en tickets exécutables. Les tickets P0 (V150/V151) sont
> la fondation : tout le reste en dépend.

| Ticket | Prio | Objet | Deps | Livrable | Test unitaire | GO |
|---|---|---|---|---|---|---|
| V150 | **P0** | Sessionized Official Journal | — | journal append-only PROVISIONAL/FINAL/REVISED | test_official_journal_has_session_fields, test_final_over_provisional_precedence | 100 % lignes avec vérité de session |
| V151 | **P0** | Premium Head Single Source | V150 | head/dashboard/monthly = 1 source | test_single_source_truth_consistency | latest/head/dashboard concordent |
| V122 | P1 | Consistency refresh | V150 | cohérence sur journal à jour | test_official_vs_proxy_freshness_gate | plus de divergence de couche |
| V123 | P1 | Freshness hardening | V150,V151 | matrice fraîcheur + disabled_diagnostics | test_no_dashboard_reads_stale_artifact | toute vue live sait ce qui est stale |
| V132 | P1 | Synthesis v3 sync | V151 | synthèse sync latest | test_single_source_truth_consistency | concordance |
| V133 | P1 | Monthly report rebuild | V151 | mensuel depuis head unique | test_monthly_reads_head_only | plus de stale monthly |
| V144 | P1 | Proxy vs official 10/40/90 | V150 + accumulation | rapport biais proxy↔officiel | test_proxy_official_bias_model | biais modélisable |
| V145 | P1 | Lifecycle rebuild | V151 | lifecycle à jour | test_lifecycle_reads_single_source | plus de conflit latest |
| V146 | P1 | Dashboard v4 rebuild | V151 | dashboard refondu | test_dashboard_reads_head_only | 0 stale dependency |
| V147 | P1 | Milestone automate | V150,V151 | jalons 10/40/90/180/365 j | test_milestone_triggering | jalons auto fiables |
| V140 | P1 | Weather revision engine | Open‑Meteo | moteur révisions lead-fixed | test_revision_engine_no_future | aucune feature future |
| V141 | P1 | Curve forward validation | V125 | validation front-next/Nov-Mar | test_curve_forward_alignment | courbe améliore l'explication |
| V142 | P1 | MATIF forward validation | V126 | validation live substitution | test_substitution_feed_integrity | robustesse forward confirmée |
| V149 | P1 | Multiview visuals + CI | V152 | visuels bootstrap/quantiles | test_visuals_use_final_only_by_default | visuels robustes/lisibles |
| V152 | P1 | Compression Event Study 2.0 | V150 | event study A-aligné [-30,+90] | test_event_study_censoring | médiane/quantiles/CI/n-at-risk |
| V153 | P1 | START vs IN_PROGRESS split | V152 | deux scores séparés | test_trigger_labels_no_lookahead | START bat base rate ou rejet honnête |
| V124/V125/V126/V128/V129/V130/V131/V135/V136/V137/V138/V139/V143/V148 | P2/P3 | (voir matrice Partie 1) | V150/V151 | reruns FINAL-only | tests dédiés | survie au nettoyage |

**Tickets indispensables juste après V150** : V151 (source unique), V152 (event study 2.0), V153
(split), V158 (acquisition officielle). Plus importants que plusieurs P2/P3 anciens.

### 8bis.7 — Gantt & gates de phase

```
Phase Hardening vérité   : V150 -> V151 -> V122/V123/V132/V145/V146 sync
Phase Audit & QA         : V159 reproducibility pack -> V144 proxy↔officiel
Phase Science explicative: V152 event study 2.0 -> V153 split -> V141/V142 -> V140/V127 -> V130/V138
Phase Acquisition data   : V158 package -> contacts Euronext/Barchart/CME (en parallèle, tôt)
```

| Gate | Condition GO | Décision |
|---|---|---|
| Gate données | V150 + V151 + tests QA verts | reprise des expériences prédictives |
| Gate robustesse | placebos + multiple testing passés | maintien « signal robuste » |
| Gate achat officiel | devis acceptable ou accès école | sanctification EMA historique |
| Gate extension watchlists | pas de dégradation calibration/risque adverse | publication tiers analytiques |
| Gate conclusion mémoire | mécanisme + audit data + OOS purgé | conclusion forte soutenable |

### 8bis.8 — Checklist QA (porte d'entrée avant toute conclusion)

| Check | Test | Attendu |
|---|---|---|
| Champs de session obligatoires | test_official_journal_has_session_fields | 100 % non nuls |
| Priorité FINAL sur PROVISIONAL | test_final_over_provisional_precedence | toujours vrai |
| Dashboard sur source unique | test_dashboard_reads_head_only | toujours vrai |
| Conversion CBOT→€/t | test_cbot_eur_conversion_roundtrip | erreur < seuil |
| Règle de contrat explicite | test_contract_selection_rule_explicit | toujours vrai |
| Labels sans fuite | test_trigger_labels_no_lookahead | 0 violation |
| Horodatage des events | test_event_calendar_timestamp_policy | 100 % daté/laggé |
| Robustesse A/C/E | test_start_date_A_C_E_consistency | écarts bornés |
| Visuels FINAL-only | test_visuals_use_final_only_by_default | toujours vrai |
| Proxy↔officiel | test_proxy_official_bias_model | stable/documenté |

### 8bis.9 — Visuels-preuves (plus seulement illustratifs)

| Visuel | But | Spécification minimale |
|---|---|---|
| Event study 2.0 | trajectoire moyenne/médiane + hétérogénéité | moyenne+médiane+q25/75+bootstrap CI |
| KM time_to_z0.5 / z0 | horizons réels avec censure | courbe + number-at-risk + split régimes |
| Calibration START score | le score prédit ce qu'il annonce | déciles + fréquence observée |
| Heatmap mois × contrat actif | saisonnalité + dépendance contrat | nb épisodes + hit rate |
| Proxy vs officiel drift | biais et stabilité | scatter + bande RMSE + segmentation |
| Curve relaxation panel | front-next/Nov-Mar autour des starts | event window |
| Revision tape weather | day1..day7 et inflexions avant start | leads fixes, pas ex-post |
| Placebo comparison | falsifier l'artefact générique | maïs vs témoins même métrique |
| Multiple testing dashboard | rendre l'overfit visible | DSR/PBO/SPA + variants count |
| Audit freshness matrix | cohérence des couches live | sources × dates × statut |

### 8bis.10 — Modèle de données cible (ER)

```
OFFICIAL_JOURNAL(price_date, contract_code, settlement, open, high, low, volume, open_interest,
                 record_status, collected_at_utc, collected_at_paris, effective_session_date, provider)
CBOT_DAILY(trade_date, contract_code, settle_usd, provider)
FX_DAILY(fx_date, pair, ref_rate, provider)
WEATHER_RUN(issuance_time, model, lead_day, zone, variable_value)
EVENT_CALENDAR(event_time, event_name, source, timestamp_quality)
SIGNAL_FACT(signal_date, basis_eur_t, basis_z, baseline_flag, progress_state, start_label, regime)
  OFFICIAL_JOURNAL -> SIGNAL_FACT (feeds) ; CBOT_DAILY+FX_DAILY -> basis (converts)
  WEATHER_RUN/EVENT_CALENDAR -> features ; SIGNAL_FACT annoté par labels
```

### 8bis.11 — E-mails d'acquisition (prêts à envoyer)

Contacts : Euronext = **formulaire Web Services** (vérifié) en premier, datasolutions@euronext.com à
reconfirmer ; Barchart = solutions@barchart.com ; CME = CMEDataSales@cmegroup.com. Les modèles FR/EN
Euronext et FR/EN Barchart sont consignés dans le ticket **V158 (Official Acquisition Package)** —
voir `.ai/TICKETS_SUITE_ETUDE.md`. Le mail Euronext FR figure déjà en Partie 1 (§ Demande type).

### 8bis.12 — Séquence optimale sans ambiguïté

```
V150 vérité de session
  -> V151 source unique
  -> V122/V123/V132/V145/V146 resynchronisés
  -> V144 proxy↔officiel
  -> V152/V153 science du START
  -> pack placebos + multiple testing (T-OVERFIT/T-PLACEBO)
  -> demandes vendors (V158, en parallèle dès maintenant)
```

Cette séquence continue l'étude au maximum tout en réduisant le risque d'avancer sur des conclusions
fausses.

---

## Partie 9 — Journal de réflexion

> Trace datée des décisions, des arbitrages, des hypothèses gelées. On ajoute une entrée à chaque
> session de travail sur ce document.

### 2026-06-10 — Création

- Récupéré toutes les données du GitHub Action (journal officiel jusqu'au 10 juin, 9 jours, reports
  daily 06-02→06-10) via merge `origin/main` (8 commits locaux préservés, non poussés).
- Créé ce document. Intégré l'audit complet (Partie 1).
- Ajouté la lecture critique (Partie 2) : l'audit est validé à ~90 %. Trois angles morts identifiés
  et développés — **économie structurelle** (parité d'import R1, cointégration R2), **rigueur
  anti-overfitting** (Partie 5, le plus important), **falsification/placebo** (X1).
- Proposé 10 axes de recherche (R1–R10), 10 expériences falsifiables (X1–X10), 8 sources de données
  additionnelles (D1–D8), 14 tickets (V161–V174).
- **Recommandation forte** : avant d'enrichir le modèle, prouver ce qui survit (T-OVERFIT, T-PLACEBO)
  et ancrer économiquement (VECM, parité). Ne pas empiler des features de plus.
- **À trancher prochaine session** : les questions Q1–Q7 de la Partie 8.
- *Note technique* : recherches web (specs Euronext, parité, López de Prado) à refaire — service
  surchargé au moment de la rédaction. À compléter en Annexe A.

### 2026-06-10 — Deuxième analyse + début d'implémentation

- Intégré la 2e analyse externe (Partie 8bis) : pack d'audit dur avec chemins d'artefacts, table
  vendeurs consolidée (ajout **CME DataMine** pour la jambe CBOT + contacts vérifiés), portefeuille
  d'expériences GO, tickets exécutables V122-V150 avec tests/GO-NO-GO, Gantt + gates, ER, e-mails.
- Les deux audits **convergent** : 3 piliers manquants = vérité de session, split START/IN_PROGRESS,
  défense overfitting. Confiance renforcée dans la séquence V150→V151→…→placebos/multiple-testing.
- **Décision d'exécution** (Q1 tranchée implicitement) : on commence par la fondation P0 V150/V151 +
  pack d'audit, AVANT toute nouvelle science. Conforme aux deux audits.
- **Découverte d'implémentation** : les 9 lignes du journal officiel n'ont PAS de `record_status` —
  le code `stamp_timing` (commits locaux VNEXT) n'était **pas poussé**, donc le bot GitHub a tourné
  sur l'ancien code. 8/9 lignes sont des collectes du matin → **PROVISIONAL** (le risque n°1 des
  audits, matérialisé). `logged_at` (UTC) permet un backfill append-only du statut de session.
- Tickets exécutables écrits dans `.ai/TICKETS_SUITE_ETUDE.md`. Implémentation en cours :
  V150 (vérité de session) → pack audit → V151 (FINAL-gate) → V153 (rename PROGRESS_SCORE).

### 2026-06-10 — Implémentation fondation P0 (DONE, testée)

Fondation P0 livrée et **testée** (ruff clean, 182 tests verts, 0 régression) :

- **V150 — vérité de session** : `stamp_timing` désormais TOUJOURS appliqué dans le writer V27 (plus
  d'except silencieux) ; nouveau `mais/audit/session_backfill.py` qui rétro-remplit le statut de
  session des lignes existantes depuis `logged_at` (append-only, n'altère aucune valeur économique) ;
  loader `load_forward_journal(final_only=...)` + `latest_final_record()` ; politique REVISED (un
  PROVISIONAL peut devenir FINAL en nouvelle ligne, jamais réécrit). **Backfill exécuté sur le journal
  réel** : 9 lignes → 1 FINAL (05-29 soir) + 8 PROVISIONAL (collectes du matin). Le risque n°1 des
  audits est désormais matérialisé et visible.
- **V159 — pack d'audit** : `mais/audit/data_truth.py` (session_alignment, finality_gate,
  cbot_eur_roundtrip, contract_selection) → artefacts sous `artefacts/audit/`. Overall **PASS**.
  Conversion CBOT→€/t exacte (erreur max **0.008 €/t**, facteur 39.3679 bu/t confirmé).
- **V151 — source unique FINAL-gate** : le premium head expose un bloc `session_truth` + un
  `session_warning` quand le dernier jour est PROVISOIRE. Bloc de rapport enrichi (« X/Y jours FINAL »).
- **V153 — split START vs IN_PROGRESS** : `mais/research/v153_start_vs_inprogress.py` acte le
  renommage `COMPRESSION_PROGRESS_SCORE` (descriptif) et construit les labels START/INPROG **sans
  lookahead** (test de non-fuite vert). **Run réel** (5940 j, holdout respecté) :
  - START_h10 : base rate 0.125, **OOF AUC 0.549** → à peine > hasard.
  - INPROG_h10 : base rate 0.651, OOF AUC 0.521.
  - Verdict : `START_TIMING_REMAINS_HARD_DESCRIPTIVE_ONLY` — **confirme empiriquement** les deux
    audits : le timing du DÉPART n'est pas démontré, le score reste descriptif. Aucune fusion baseline.

**Reste à faire (prochaines sessions, ordre Partie 8bis.12)** : V144 proxy↔officiel, V152 event study
2.0, T-OVERFIT (DSR/PBO/SPA), T-PLACEBO, V162 VECM, V161 parité d'import, V167 saisonnalité,
V140/V127 weather revision engine, V158 acquisition (e-mails prêts). Push des commits (le bot tournera
alors avec le stamping → plus aucune ligne PROVISIONAL non étiquetée).

---

## Annexe A — Sources web

> À compléter quand le service de recherche répond. Objectif : ancrer avec des liens vérifiables les
> faits cités (horaires Euronext/DSP, parité d'import, méthodes López de Prado, calendriers USDA/MARS,
> contacts Euronext/Barchart). Chaque entrée : fait → URL → date de consultation.

- [ ] Euronext — horaires de cotation maïs (jusqu'à 20:15 CET) et confirmation DSP 18:30 CET inchangé.
- [ ] Euronext Data Solutions — Web Services / NextHistory / contact datasolutions@euronext.com.
- [ ] Barchart — Premier 29.95 USD/mois ; getHistory / OnDemand.
- [ ] López de Prado — Deflated Sharpe, PBO/CSCV, purged+embargoed CV (références).
- [ ] White Reality Check / Hansen SPA — références.
- [ ] Eurostat COMEXT — bulk download, prix unitaires d'import.
- [ ] FranceAgriMer / data.gouv — cotations céréales, Céré'Obs.
- [ ] JRC MARS / AGRI4CAST / Combined Drought Indicator.
- [ ] Open-Meteo — Historical Forecast & Previous Runs (leads day1..day7).
- [ ] CFTC COT, USDA WASDE calendar, NOAA NOMADS GFS/GEFS.
- [ ] BCE — taux de référence EUR/USD quotidien (16h CET).
