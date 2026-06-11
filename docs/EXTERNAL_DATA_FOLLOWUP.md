# V182 — Suivi des demandes de données externes

_Phase de validation forward · mis à jour à la main à chaque événement (envoi, réponse, devis) ·
les e-mails prêts à l'envoi sont dans `docs/ACQUISITION_PACKAGE.md` (V158)._

## Tableau de suivi

| # | Destinataire | Objet | Mail prêt | Envoyé le | Réponse | Coût annoncé | Faisabilité | Décision |
|---|---|---|---|---|---|---|---|---|
| 1 | Euronext Web Services / NextHistory | EMA toutes échéances 2014→, daily OHLC + settlement + volume + OI, contrats expirés inclus ; Milling Wheat EBM idem | ✅ (FR §4 + EN §5) | — | — | — | la seule source OFFICIELLE des contrats expirés | **À ENVOYER (action utilisateur)** |
| 2 | Barchart | historique XB par contrat + intraday autour de la clôture Euronext | ✅ (EN §6) | — | — | — | proxy déjà utilisé en exploratoire ; l'export propre lèverait la réserve « page web » | À ENVOYER (priorité 2) |
| 3 | CME DataMine | settlements officiels ZC + intraday fenêtre 17:30-20:15 CET | ✅ (EN §7) | — | — | — | jambe CBOT déjà couverte par yfinance+BCE (V174 écart max 0.19 €/t) → utile, non bloquant | À ENVOYER (priorité 3) |
| 4 | École (Bloomberg/LSEG/CQG) | accès terminal pour export ponctuel EMA/EBM historique | demande orale/mail libre | — | — | 0 € (accès académique) | dépend de l'établissement ; débloquerait #1 sans frais | À DEMANDER en parallèle |

## Ce que chaque réponse débloque (impact recherche)

| Source | Débloque immédiatement |
|---|---|
| Euronext historique (#1/#4) | V144 (biais proxy↔officiel sur 10+ ans), V165/V166 (courbe multi-échéances longue), V168-MATIF (substitution EBM/EMA historique), requalification de TOUT l'historique exploratoire en officiel |
| Barchart export (#2) | nettoyage de la réserve `barchart_proxy_exploratory` (settlement explicite), intraday V128 |
| CME DataMine (#3) | settlement ZC officiel (remplace yfinance), microstructure de la fenêtre Euronext |

## Règles de décision (figées)

- **Coût 0-50 €/mois étudiant** : accepter si ça débloque la colonne « Débloque » ci-dessus.
- **Coût > 50 €/mois** : refuser par défaut — l'étude continue sur forward officiel gratuit
  (l'accumulation V125/V52/V140 rend les données payantes de moins en moins nécessaires avec le temps).
- **Pas de réponse sous 3 semaines** : une relance, puis statut `NO_RESPONSE` et on continue sans.
- Aucune donnée payante ne conditionne le live : le pipeline quotidien est 100 % gratuit.

## Journal des événements

| Date | Événement |
|---|---|
| 2026-06-10 | E-mails rédigés (V158, `docs/ACQUISITION_PACKAGE.md`) |
| 2026-06-11 | Tracker V182 créé ; envoi = action utilisateur (aucun envoi automatique) |

_RESEARCH_ONLY_NOT_TRADING._
