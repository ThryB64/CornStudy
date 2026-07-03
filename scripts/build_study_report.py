"""Génère l'ARBRE DE CHEMINEMENT complet de l'étude + l'inventaire + le graphe des tests
performants. Objectif : **tous** les fichiers de test/expérience (286 tests + 24 EXT) sont
rattachés à la question qu'ils ont servi à répondre, avec une analyse par couche
(question -> fichiers -> analyse des résultats -> question(s) suivante(s)). Rien n'est oublié
(rattachement par mot-clé + repli ; couverture vérifiée). Aucune description inventée : elle
vient de la docstring de chaque fichier.

Sorties :
- artefacts/rapport_etude/arbre_etude.html        : ARBRE flowchart (question bleue -> chips
                                                    fichiers : vert=exploitable, rouge=abandonné,
                                                    gris=test ; analyse + question(s) suivantes)
- docs/ARBRE_ETUDE.md                             : le même arbre en texte, avec TOUS les fichiers
- artefacts/rapport_etude/inventaire_tests.csv    : 1 ligne/fichier (+ question rattachée)
- artefacts/rapport_etude/tests_performants.html  : barres des tests aux bons résultats
"""
from __future__ import annotations

import ast
import csv
import json
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
EXT = ROOT / "external_research" / "experiments" / "external_tests"
OUT = ROOT / "artefacts" / "rapport_etude"
DOCS = ROOT / "docs"

# nettoyage des caractères "suspects IA" (em-dash, flèches, guillemets courbes, puces, emojis)
_SUS = [("—", " - "), ("–", "-"), ("→", "->"), ("←", "<-"),
        ("↑", ""), ("↓", ""), ("▼", ""), ("◆", ""), ("…", "..."),
        ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
        ("•", "-"), ("·", " - "), ("①", "1."), ("②", "2."),
        ("③", "3."), ("④", "4."), ("🔎", ""), ("📋", ""),
        ("✅", ""), ("❌", ""), ("⛔", ""), ("🔧", ""), ("🔵", ""),
        ("🟢", ""), ("🔴", ""), ("🟠", ""), ("≫", ">>"), ("≪", "<<"),
        ("×", "x"), ("≈", "~"), ("≥", ">="), ("≤", "<="),
        ("↔", "<->"), ("−", "-")]


def clean(s: str) -> str:
    for a, b in _SUS:
        s = s.replace(a, b)
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()

# --- verdict d'un fichier (couleur des chips) ---------------------------------
KEEP = ("crop_condition", "wasde_release", "wasde_world", "wasde_vintage", "har_realized",
        "garch", "volatility", "sale_score", "basis_reversion", "short_indicator",
        "short_realism", "structural_indicator", "composite_indicator", "mean_reversion_lab",
        "premium_indicator", "cbot_support", "adverse_risk", "adverse_path", "state_machine",
        "signal_tiers", "euronext_indicator", "var_supply_demand", "shap_feature",
        "regime_detection", "cbot_rebound", "target_recommendation", "indicator_synthesis",
        "indicator_visual", "indicator_multiview", "research_indicator", "hierarchical",
        "wasde_release_features", "crop_condition_report")
DEADEND = ("weather_crop", "weather_lags", "weather_deep", "weather_extremes", "extreme_weather",
           "weather_forecast", "weather_revision", "weather_basis", "weather_crop_stress",
           "cot_features", "cot_advanced", "ethanol", "crush", "surprise", "trend_following",
           "stacking", "deep_learning", "nbeatsx", "granger", "basis_explanation", "enso",
           "carbon", "placebo", "hazard", "overfit", "red_team", "multiple_testing",
           "intercommodity", "convenience_yield", "hmm", "bayes_survival", "causal_dag",
           "survival_reversion", "magnitude", "mechanism", "ou_mean")
BLOCKED = ("curve", "spot_futures", "transmission", "satellite", "manual_backfill",
           "continuous_series_probe", "comext", "dce_dalian", "franceagrimer", "intraday",
           "endpoint_probe", "history_probe", "contract_download", "ema_probe", "proxy_forward",
           "vecm", "basis_econometrics", "basis_forecast", "fx_bce")
INFRA = ("data_quality", "data_audit", "data_truth", "leakage", "calendar", "paths", "registry",
         "coherence", "forensic", "session", "purged_cv", "target_integrity", "import_parity",
         "official_automation", "official_proxy", "single_source", "settlement_alignment",
         "freshness", "journal_consistency", "feature_data_quality", "new_modules", "utils",
         "proxy_audit", "roll_audit", "data_status", "publication_calendar", "usda_release",
         "benchmark", "baseline", "random_walk")

# 5 catégories CLAIRES (au lieu d'un gris fourre-tout)
CHIP = {"gardé": "#2ca02c", "abandonné": "#d62728", "bloqué": "#e8943a",
        "outil": "#17a2b8", "exploration": "#6f86c4"}
CATLABEL = {
    "gardé": "GARDÉ (résultat exploitable)",
    "abandonné": "ABANDONNÉ (n'a rien donné)",
    "bloqué": "BLOQUÉ (données manquantes)",
    "outil": "OUTIL (audit / anti-fuite)",
    "exploration": "EXPLORATION (étape de cadrage)",
}
MARK = {"gardé": "[GARDÉ]", "abandonné": "[ABANDONNÉ]", "bloqué": "[BLOQUÉ]",
        "outil": "[OUTIL]", "exploration": "[EXPLORATION]"}


def verdict_of(name: str) -> str:
    n = name.lower()
    if any(k in n for k in DEADEND):
        return "abandonné"
    if any(k in n for k in BLOCKED):
        return "bloqué"
    if any(k in n for k in KEEP):
        return "gardé"
    if any(k in n for k in INFRA):
        return "outil"
    return "exploration"                # étape intermédiaire de cadrage (ni gardée ni rejetée)


# --- les questions (couches de l'arbre) ---------------------------------------
QUESTIONS = [
    ("Q-DATA", "Quelles données gratuites ai-je, et sont-elles PROPRES (anti-fuite) ?",
     "Ce qu'on retient : une découverte critique — la série WASDE interne exposait ses valeurs "
     "~8 jours AVANT publication (fuite), corrigée par un pipeline 'vintage' daté à la "
     "publication ; et la série Euronext brute sautait de ~10 €/t les jours de roll, corrigée "
     "par la série ajustée. On en déduit que, ces deux biais corrigés, la base est SAINE et "
     "qu'on peut modéliser sans 'voir le futur'. → Première vraie question : peut-on simplement "
     "prédire le prix ?"),
    ("Q1", "Peut-on PRÉDIRE le prix exact du maïs ?",
     "Résultat net : aucun des 36 couples (modèle × horizon) ne bat la random walk au test de "
     "Diebold-Mariano (p<0.10). On retient que le PRIX EXACT n'est pas prévisible en RMSE avec "
     "ces données — c'est un résultat solide, pas un échec de méthode. On en déduit qu'il faut "
     "CHANGER d'objectif : viser la DIRECTION (hausse/baisse) et expliquer la prime européenne "
     "via le BASIS, pas le niveau de prix. → La direction et le basis sont-ils modélisables ?"),
    ("Q2", "Peut-on prédire la DIRECTION et expliquer la prime Euronext via le basis ?",
     "On retient que CBOT et Euronext sont cointégrés et que la prime se compresse surtout "
     "quand le CBOT MONTE (la jambe CBOT pèse ~6× la jambe EMA) ; le résidu purement européen "
     "est faible. On en déduit que l'objet exploitable n'est pas le prix Euronext en soi mais "
     "le BASIS et sa dynamique. → Deux questions en découlent : le basis revient-il à la "
     "moyenne (Q3) ? qu'est-ce qui l'explique (Q4) ? — plus deux pistes de prédicteurs : "
     "météo (Q2b) et positionnement/demande (Q2c)."),
    ("Q3", "Le basis revient-il à la moyenne → signal de vente ?",
     "On retient une demi-vie de réversion de 17-47 jours, et qu'une règle 'vendre quand le "
     "basis est haut' survit aux coûts (~5 €/t) hors crise (+115), avec un edge concentré sur "
     "les extrêmes (z>2) ; l'indicateur structurel atteint AUC 0.66-0.69. On en déduit un "
     "signal de vente RÉEL mais MODESTE et asymétrique (short ≫ long). → Cela ouvre : que se "
     "passe-t-il quand ça tourne mal (Q5) ? et peut-on en faire un indicateur suivi (Q-LIVE) ?"),
    ("Q4", "Qu'est-ce qui EXPLIQUE le basis et la prime ? (macro, substitution, physique)",
     "On retient que la macro N'EXPLIQUE PAS le basis (R² hors échantillon −0.25), que la "
     "causalité de Granger est rejetée, et que la substitution blé/maïs n'est qu'un CONTEXTE "
     "(corr 0.60) ; MATIF et spot UE sont bloqués faute de données. On en déduit que la prime "
     "est LOCALE et peu explicable par les fondamentaux disponibles — donc on reste sur le "
     "basis lui-même + l'offre US, sans sur-interpréter. → Cul-de-sac partiel : ces "
     "explications ne deviennent pas des prédicteurs."),
    ("Q2b", "La MÉTÉO aide-t-elle à prédire ?",
     "On retient que la météo RÉALISÉE est déjà 'price-in' par anticipation (AUC 0.508 ≈ "
     "hasard) : quand on l'observe, le marché l'a déjà intégrée. La seule piste cohérente "
     "serait les RÉVISIONS de prévisions, mais l'archive disponible est trop courte. On en "
     "déduit qu'on ABANDONNE la météo comme prédicteur (on la garde comme contexte : un été "
     "de stress rend le basis moins compressible). → Cul-de-sac, sauf archive de prévisions future."),
    ("Q2c", "Le COT (positions) et l'ÉTHANOL (demande) aident-ils ?",
     "On retient qu'aucun n'aide hors échantillon : le COT Managed Money dégrade RMSE et DA à "
     "tous horizons, et sans vrais prix éthanol/DDG les proxys sont inutiles. On en déduit que "
     "ces deux dossiers sont CLOS avec les données actuelles. → Cul-de-sac."),
    ("Q5", "La compression ADVERSE est-elle prévisible ?",
     "On retient que l'ISSUE ADVERSE (la compression va-t-elle mal tourner ?) est prévisible "
     "(LOO AUC 0.72) à partir du niveau d'entrée et d'un basis bas, mais que le MÉCANISME (par "
     "quel chemin ?) ne l'est pas (AUC 0.48). On en déduit qu'on ne peut pas prédire COMMENT "
     "ça tourne mal, mais qu'on peut estimer le RISQUE a priori — donc viser un score de "
     "RISQUE plutôt qu'une prédiction. → Comment doser ce risque ?"),
    ("Q6", "Peut-on DOSER le risque (support CBOT, volatilité, drawdown) ?",
     "On retient que le support CBOT divise par 2 le risque ADVERSE et double le PnL, que la "
     "VOLATILITÉ se prévoit bien (HAR/EGARCH −24 % de RMSE vs random walk — un des résultats "
     "les plus solides de l'étude), et que le drawdown CBOT est prévisible (AUC 0.74). On en "
     "déduit de vraies briques de gestion du risque, à utiliser comme GATE (filtre) plutôt que "
     "comme signal de direction. → Tout ça tient-il dans un indicateur suivi dans le temps ?"),
    ("Q-LIVE", "Peut-on en faire un INDICATEUR suivi (forward, machine d'état, courbe) ?",
     "On retient un système forward fonctionnel et honnête (il se dégrade quand les données "
     "sont périmées), mais qui reste ANALYTIQUE : pas de paper-trading, beaucoup de pistes "
     "data-gated, et un edge toujours modeste. On en déduit qu'avant d'aller plus loin il faut "
     "REPARTIR DE ZÉRO et tester chaque famille proprement et systématiquement. → Famille par "
     "famille, qu'est-ce qui marche vraiment ?"),
    ("Q7", "Systématiquement (recherche externe EXT), quelles familles portent un signal ?",
     "On retient seulement 3 briques : Crop Condition @ H90 (AUC 0.724), WASDE stocks-to-use @ "
     "H40, et la volatilité (HAR/EGARCH). On rejette clairement trend-following (le maïs ne "
     "tend pas), stacking et deep learning (sur-apprennent), surprise WASDE et COT (rien hors "
     "échantillon). On en déduit que la PARCIMONIE gagne et que le seul signal directionnel "
     "réel est l'OFFRE US à horizon long. → Ces 3 briques survivent-elles hors échantillon ?"),
    ("Q8", "Survivent-ils au HOLDOUT 2024+ → un score de vente ?",
     "On retient que crop@H90 fait DA 0.686 / AUC 0.816 sur 2024+ et bat largement la random "
     "walk — c'est cohérent (2024 = grosse récolte → baisse). MAIS il ne bat PAS une simple "
     "saisonnalité (0.752), et le backtest dépend du cadrage. On en déduit un verdict honnête : "
     "FRAGILE — un repère utile, pas une preuve de robustesse. → À quoi ça ressemble sur le "
     "vrai marché Euronext ?"),
    ("Q9", "À quoi ressemble l'indicateur sur l'historique EURONEXT ?",
     "On retient que les recommandations ORDONNENT correctement les retours futurs (SELL_PARTIAL "
     "→ −5.8 % à 90 j, WAIT → +5.1 %), ce qui est visuellement convaincant. MAIS la "
     "discrimination hors échantillon est faible (AUC 0.561) et le prix Euronext disponible est "
     "à 97 % un proxy. On en déduit un verdict RESEARCH_ONLY : un outil de visualisation "
     "honnête, pas un conseil de vente opérationnel. → Conclusion de l'étude."),
]
QORDER = [q[0] for q in QUESTIONS]
QTEXT = {q[0]: q[1] for q in QUESTIONS}
QANALYSE = {q[0]: q[2] for q in QUESTIONS}

# texte d'intro de la couche (au-dessus des fichiers) : pourquoi cette question + comment on
# va y répondre (sans label, affiché directement)
QRESUME = {
    "Q-DATA": "Avant de modéliser quoi que ce soit, il faut savoir ce dont on dispose et si "
              "c'est fiable, car un signal calculé sur des données qui 'voient le futur' est "
              "faux. On rassemble donc ~12 sources publiques gratuites (CBOT, Euronext, WASDE, "
              "Crop Condition, météo, COT, éthanol, macro, exports) et on les AUDITE : dates de "
              "publication réelles, fuites éventuelles, artefacts de construction des séries "
              "continues. Concrètement on lance des tests d'intégrité, on reconstruit les "
              "rapports USDA en version 'vintage' et on vérifie les calendriers.",
    "Q1": "Pour savoir si le prix est seulement prévisible, on le confronte aux baselines "
          "triviales — random walk ('demain = aujourd'hui'), dérive, dérive saisonnière, prix "
          "des futures — sur le prix et le retour, à 4 horizons (5/20/40/90 j), avec un test de "
          "Diebold-Mariano. Pourquoi ces baselines : si on ne bat même pas la marche aléatoire, "
          "aucun modèle compliqué n'est justifié.",
    "Q2": "Puisque le prix exact échappe, on regarde la relation CBOT↔Euronext : sont-ils liés "
          "par un équilibre de long terme (cointégration) ? Peut-on décomposer le retour "
          "Euronext en part CBOT + prime locale ? On teste la cointégration de Johansen, la "
          "décomposition du retour et l'étude du résidu européen, pour voir si la prime/le "
          "basis est modélisable.",
    "Q3": "Si le basis revient à la moyenne, alors 'basis haut' = bon moment pour vendre. On "
          "mesure la demi-vie de réversion, on teste une règle 'vendre quand le basis est haut' "
          "avec des coûts réalistes et des règles de sortie, et on assemble des indicateurs "
          "structurels de vente à paliers.",
    "Q4": "Un signal qu'on ne comprend pas est fragile : on cherche ce qui EXPLIQUE le basis "
          "pour le solidifier — variables macro, causalité de Granger CBOT→prime, substitution "
          "blé/maïs, fondamentaux UE, change EUR/USD.",
    "Q2b": "La météo est le suspect n°1 pour le maïs, donc on la teste sous TOUTES ses formes — "
           "météo réalisée, anomalies, événements extrêmes, fenêtres agronomiques, et surtout "
           "la distinction réalisé vs PRÉVISIONS et leurs révisions — pour voir si elle anticipe "
           "les mouvements ou si le marché les a déjà intégrés.",
    "Q2c": "On teste les deux autres suspects classiques : le positionnement des spéculateurs "
           "(COT Managed Money — extrêmes, flux) et la demande éthanol/énergie (marge crush), "
           "pour voir s'ils donnent un signal directionnel.",
    "Q5": "Le short 'basis haut' a des pertes rares mais grosses (cas ADVERSE) : on cherche à "
          "savoir si on peut les PRÉVOIR. On distingue l'ISSUE (la compression va-t-elle mal "
          "tourner ?) du MÉCANISME (par quel chemin ?), car prévoir l'un ou l'autre n'a pas la "
          "même valeur.",
    "Q6": "Puisqu'on ne prédit pas le mécanisme, on construit des briques de RISQUE "
          "indépendantes de la direction — un 'support CBOT' qui protège la prime, la "
          "volatilité conditionnelle (HAR/EGARCH), un score de drawdown — pour filtrer les "
          "moments dangereux.",
    "Q-LIVE": "On industrialise pour voir si l'indicateur tient dans la durée : machine d'état "
              "de la prime, gates de fraîcheur des données, catalogue de catalyseurs, courbe "
              "officielle Euronext, dashboards et collecte automatisée — pour le suivre jour "
              "après jour sans tricher.",
    "Q7": "On repart de ZÉRO avec un protocole anti-fuite strict et on teste SYSTÉMATIQUEMENT "
          "24 familles externes (1 expérience EXT chacune : météo, WASDE, COT, courbe, éthanol, "
          "basis, crop condition, volatilité, régimes, et des modèles trend/stacking/deep "
          "learning) — pour trancher, famille par famille, ce qui marche.",
    "Q8": "On assemble les seules briques validées en un score de vente parcimonieux (régression "
          "logistique) et on l'éprouve UNE SEULE FOIS sur le holdout 2024+ jamais utilisé avant, "
          "contre la random walk ET une simple saisonnalité, pour un verdict honnête.",
    "Q9": "On applique le score CBOT à l'historique de prix Euronext et on le VISUALISE "
          "(dashboard interactif) pour voir si les recommandations auraient aidé à vendre, et "
          "à quel point le résultat est fiable.",
}

# données mobilisées par couche (pour la section "comment / quelles données" du détail)
QDATA = {
    "Q-DATA": "toutes les sources (prix CBOT, prix Euronext, rapports WASDE, Crop Condition NASS, "
              "météo Open-Meteo, positions COT, éthanol EIA, macro FRED, exports FAS) et les "
              "calendriers de publication USDA.",
    "Q1": "les prix CBOT et Euronext (séries continues), évalués à 4 horizons (5, 20, 40, 90 jours).",
    "Q2": "les prix CBOT et Euronext alignés (cointégration de Johansen, décomposition du retour).",
    "Q3": "le basis (Euronext converti en euros - CBOT) et sa dynamique, avec des coûts de "
          "transaction réalistes.",
    "Q4": "le basis plus des variables macro (FRED), les prix blé/maïs, des fondamentaux UE et "
          "le change EUR/USD.",
    "Q2b": "la météo réalisée et prévue (Open-Meteo), les anomalies, les fenêtres agronomiques "
           "et l'indice de sécheresse.",
    "Q2c": "les positions COT (CFTC, Managed Money) et la demande éthanol/énergie (EIA).",
    "Q5": "les trajectoires de la prime après l'entrée, le niveau d'entrée et un basis bas.",
    "Q6": "les retours CBOT (pour la volatilité), un indicateur de support CBOT et le drawdown.",
    "Q-LIVE": "les flux officiels Euronext, la courbe, les catalyseurs datés, les calendriers et "
              "la collecte automatisée.",
    "Q7": "la famille externe testée (météo, WASDE vintage, COT, courbe, éthanol, basis, Crop "
          "Condition, volatilité, regimes), avec un protocole anti-fuite strict.",
    "Q8": "Crop Condition + WASDE stocks-to-use + saisonnalite, cible = direction du retour CBOT, "
          "avec le holdout 2024+ jamais utilise avant.",
    "Q9": "l'historique de prix Euronext (97 % proxy) avec les scores CBOT alignes par date.",
}
# liens « découle de » pour dessiner le flux
QFROM = {"Q1": "Q-DATA", "Q2": "Q1", "Q3": "Q2", "Q4": "Q2", "Q2b": "Q2", "Q2c": "Q2",
         "Q5": "Q3", "Q6": "Q5", "Q-LIVE": "Q3", "Q7": "Q-LIVE", "Q8": "Q7", "Q9": "Q8"}

# overrides thématiques (1er match) — sinon repli par phase/EXT
OVERRIDES = [
    ("Q9", ("euronext_indicator",)),
    ("Q8", ("cbot_sale_score",)),
    ("Q1", ("benchmark", "baseline", "price_forecast", "price_cqr", "target_lab", "target_labs",
            "horizon_sweep", "model_zoo", "weekly_da", "cqr_v2", "roll_target_benchmark",
            "weekly_benchmark", "true_curve_benchmark", "storage_benchmark", "direction_benchmark")),
    ("Q2b", ("weather", "meteo", "openmeteo", "drought", "enso", "ec_mars", "forecast_revision",
             "crop_condition_phenology")),
    ("Q2c", ("cot", "ethanol", "eia", "carbon", "crush")),
    ("Q4", ("basis_explanation", "granger", "substitution", "intercommodity", "convenience",
            "macro", "fx_bce", "comext", "franceagrimer", "eu_fundamental", "eu_pressure",
            "wasde_world", "world_collector", "fas_export", "new_sources", "physical",
            "basis_econometrics", "basis_forecast", "vecm")),
    ("Q5", ("adverse", "hazard", "compression", "casebook", "rebound", "survival",
            "path_classification", "mechanism", "magnitude")),
    ("Q6", ("cbot_support", "drawdown", "roll_risk", "risk_regime", "volatility",
            "signal_quality", "cbot_risk")),
    ("Q7", ("deep_learning", "stacking", "dim_reduction", "meta_model", "hmm", "bayes",
            "causal", "placebo", "overfit", "multiple_testing", "red_team", "model_zoo",
            "feature_importance", "feature_selector", "seasonal_experts")),
    ("Q2", ("cointegration", "decomposition", "residual", "relative", "relation", "premium",
            "cross_market", "cross_data", "cross_target", "integration")),
    ("Q3", ("structural_indicator", "mean_reversion", "short_indicator", "short_realism",
            "basis_reversion", "basis_regimes", "indicator_synthesis", "indicator_visual",
            "indicator_multiview", "composite", "signal_tiers", "target_recommendation",
            "seasonal_premium", "seasonality", "market_discovery",
            "ema_basis", "storage", "abstention", "theoretical_backtest")),
    ("Q-LIVE", ("module_a", "consensus", "indicator_confidence", "confidence_p_correct")),
    ("Q2", ("final_report", "final_synthesis", "project_overview", "final_corn_study",
            "phase2_descriptive")),
    ("Q-LIVE", ("state_machine", "state_transition", "forward", "premium", "session", "curve",
                "official", "dashboard", "catalyst", "freshness", "monitoring", "active_signal",
                "milestone", "journal", "backfill", "continuous", "contract", "endpoint",
                "weekly_report", "weekly_maintenance", "monthly_forward", "data_sourcing",
                "decision_checkpoint", "matif", "single_source", "settlement", "import_parity",
                "event_study", "event_microstructure", "event_date", "live", "roll_season",
                "tape", "compression_event", "compression_start", "compression_trigger")),
]
PHASE_Q = {"1": "Q-DATA", "2": "Q2", "3": "Q3", "4": "Q-LIVE", "5": "Q-LIVE", "6": "Q-LIVE",
           "7": "Q8", "8": "Q9", "R": "Q7"}
EXT_Q = {"EXT025": "Q1", "EXT001": "Q2b", "EXT002": "Q2b", "EXT018": "Q2b", "EXT020": "Q2b",
         "EXT033": "Q2b", "EXT003": "Q2c", "EXT004": "Q2c", "EXT006": "Q-DATA",
         "EXT026": "Q-DATA", "EXT005": "Q-LIVE", "EXT013": "Q4", "EXT009": "Q6", "EXT010": "Q6"}


def phase_of(name: str) -> str:
    n = name.replace("test_", "")
    for k in range(150, 183):
        if n.startswith(f"v{k}"):
            return "6"
    for k in range(100, 150):
        if n.startswith(f"v{k}"):
            return "5"
    for k in range(22, 100):
        if n.startswith(f"v{k}_") or n.startswith(f"v{k}b") or n == f"v{k}":
            return "4"
    if any(n.startswith(f"v{k}") for k in range(6, 22)):
        return "3"
    return "1"


def assign_q(name: str, is_ext: bool) -> str:
    if is_ext:
        return EXT_Q.get(name.split("_")[0], "Q7")
    n = name.lower()
    for qid, kws in OVERRIDES:
        if any(k in n for k in kws):
            return qid
    if "ema" in n or n.startswith("test_euronext") or "basis" in n:
        return PHASE_Q.get(phase_of(name), "Q2")
    return PHASE_Q.get(phase_of(name), "Q-DATA")


def docline(path: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except Exception:
        doc = None
    if doc:
        return doc.strip().splitlines()[0][:160]
    return path.stem.replace("test_", "").replace("_", " ")


def full_doc(path: Path) -> str:
    """Docstring complète du module (ce qu'on fait / pourquoi / comment), nettoyée."""
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except Exception:
        doc = None
    return " ".join(doc.split())[:1200] if doc else ""


# résultats documentés des fichiers clés (substring du nom -> résultat & analyse)
RESULTS = {
    "EXT025": "La random walk bat toutes les baselines naïves (0/36 couples, DM p<0.10) : "
              "référence imbattable en RMSE pour tout le programme.",
    "EXT024": "En DIRECTION : crop@H90 DA 0.599→0.658 (corrigé 0.669), AUC 0.61→0.724, Brier "
              "amélioré, stable sur 2 moitiés. IMPROVE — le meilleur signal directionnel.",
    "EXT019": "Crop Condition good/excellent : +4.4 pts de DA à H90, stable, RMSE neutre. IMPROVE.",
    "EXT007": "Niveaux de bilan WASDE : +6.1 pts DA H20 stable, mais RMSE pire (non-stationnaire) "
              "→ ré-encoder en stocks-to-use. IMPROVE.",
    "EXT009": "EGARCH/GARCH : −24 % de RMSE de volatilité vs RW ; le filtre de vol neutralise le "
              "régime où le signal s'inverse. KEEP (risque).",
    "EXT010": "HAR bat la RW de vol et rolling-20 (RMSE/MAE/QLIKE) à tous les horizons (−23 % à "
              "H90). KEEP.",
    "EXT011": "Tous les signaux de tendance ont DA<0.5 (mom120 ~0.39) : le maïs ne tend pas. "
              "REJECT (negative control).",
    "EXT050": "Le stacking sur-apprend (1re moitié ≤0.5) et fait moins bien que la moyenne simple. "
              "REJECT — parcimonie>empilement.",
    "EXT016": "Deep learning (NBEATSx) non justifié vu l'edge faible ; sur-apprentissage attendu. "
              "NOT_WORTH_YET.",
    "EXT008": "Surprise WASDE (révisions M-M-1, sans consensus) : −16 pts DA. REJECT.",
    "EXT003": "COT Managed Money : dégrade RMSE et DA à tous horizons. REJECT.",
    "EXT004": "Sans vrais prix éthanol/DDG, les proxys dégradent RMSE et DA. REJECT.",
    "EXT005": "Pas de contrats CBOT par maturité (front-only) : courbe non testable. DATA_BLOCKED.",
    "EXT013": "Pas d'EUR/USD quotidien ni de spot UE : basis non reconstructible. DATA_BLOCKED.",
    "EXT012": "OU mean-reversion vise un basis stationnaire, bloqué (dépend EXT013). DATA_BLOCKED.",
    "EXT026": "Pipeline WASDE vintage validé (24/24) ; FUITE ~8 j détectée dans la série interne "
              "et corrigée. KEEP (infra anti-fuite).",
    "EXT006": "Série EMA brute : +10.2 €/t les jours de roll (6.6×), 27/68 flips de momentum ; la "
              "série ajustée corrige. IMPROVE (hygiène).",
    "EXT015": "Sélection train-only : s2u_z/pctile + cond_anom/dev5y/poor_vp stables 16/16 ans ; "
              "le logit top-6 bat le RF. KEEP (parcimonie validée).",
    "EXT017": "Régimes : signal fort en uptrend/low-vol/bilan extrême, nul en neutre. IMPROVE.",
    "cbot_sale_score": "Holdout 2024+ : crop@H90 DA 0.686 / AUC 0.816, bat la RW mais PAS une "
                       "simple saisonnalité (0.752). Score FRAGILE.",
    "euronext_indicator": "Sur Euronext (97 % proxy) : SELL_PARTIAL → −5.8 % à H90, WAIT → +5.1 % "
                          "(séparation correcte) mais OOS AUC 0.561. RESEARCH_ONLY.",
    "v9_structural": "Indicateur structurel hybride : cœur AUC 0.656 ; inversion saisonnière V8 "
                     "falsifiée.",
    "v10_market": "Modèle 2 variables (basis_z + saison) AUC 0.694 ; demi-vie du basis ~17 j ; "
                  "mur de coûts confirmé.",
    "v13_basis": "Short 'basis haut' survit au coût 5 €/t hors crise (+115) ; sortie z0/z0.5 bat "
                 "H40 ; asymétrie short≫long.",
    "v16_basis_explanation": "La macro n'explique PAS le basis (R² OOF −0.25) : prime locale ; "
                             "basis_z reste le meilleur. REJECT fair-value.",
    "granger": "Causalité de Granger rejetée hors échantillon : pas de lien exploitable.",
    "v45_weather": "Le stress météo US réalisé ne prédit pas le CBOT (AUC 0.508) : price-in.",
    "v32_adverse": "L'ISSUE ADVERSE est prévisible : LOO AUC 0.72 (niveau d'entrée + basis bas).",
    "v38_adverse": "Module ADVERSE_RISK règle-basé : risque monotone 0→18→25 %, PnL 27.6→11.5→5.0.",
    "v35_cbot": "Le MÉCANISME de compression n'est pas prévisible (AUC 0.48) : seul l'état initial l'est.",
    "v41_cbot_support": "Un support CBOT divise par 2 le risque ADVERSE et double le PnL.",
    "v23_cbot": "Risque de drawdown CBOT prévisible AUC 0.74 ; le filtre de régime est réfuté.",
    "v11_": "Le modèle 2 variables est promu par défaut ; le filtre de régime est rejeté en "
            "forward ; le short 'basis haut' reste robuste après coûts.",
    "v12_mean": "La sortie 'au niveau' bat l'horizon fixe H40 (réversion ~54 j) ; le short "
                "'basis haut' généralise hors échantillon ; l'abstention donne DA 0.78.",
    "v14_short": "Indicateur short-only assemblé ; réversion médiane 47 j ; proxy robuste ; "
                 "tendance à trop filtrer (over-gating).",
    "v15_short": "Stop -20, edge concentré sur z>2 ; portefeuille strict +116 (coût 5 €/t), hit "
                 "0.90 ; les variantes saison-aware et partielles sont rejetées.",
    "v17_research": "Indicateur à paliers ; walk-forward sobre hit 0.66, net +138 ; la sortie "
                    "z0.5 évite des pertes.",
    "v18_literature": "Revue de littérature et réplication des familles (théorie du stockage, "
                      "basis trading, convergence, WASDE, COT, météo) : confirme les priors.",
    "v19_cbot_weather": "Le CBOT prédit ses BAISSES mieux que ses hausses ; la météo réalisée "
                        "n'ajoute qu'un faible +0.07 sur la direction CBOT.",
    "v21_integration": "La prime se compresse surtout par HAUSSE du CBOT (69 % des cas) : "
                       "'short premium' revient à 'long CBOT relatif'. Rapport de synthèse écrit.",
    "v22_live": "Stabilisation live ; le gate de fraîcheur marque le signal périmé "
                "(UNCERTAIN_DATA_STALE) ; un retard de 221 jours a été détecté et traité.",
    "v24_data_forensic": "Audit de données PASS ; un rebuild de zéro reproduit 47 trades (hit "
                         "0.85, proche du master) ; conversions et contrats validés.",
    "v26_official": "Source Euronext OFFICIELLE débloquée : settlements réels ; basis officiel "
                    "+76 €/t = 99e percentile du proxy (les niveaux du proxy sont validés).",
    "v30_official": "Courbe officielle Euronext : backwardation sur le contrat proche.",
    "v36_physical": "Le basis covarie avec l'écart blé/maïs (r=0.60, substitution) mais le modele "
                    "ADVERSE associé est marqué sur-appris.",
    "v39_enrichment": "6 mini-experiences : en uptrend CBOT le risque ADVERSE est divise par 2 et "
                      "le PnL double ; l'ethanol et les stocks US pesent peu sur le basis EU.",
    "v40_substitution": "Spécificité EU : corr(ratio, basis)=+0.59 vs corr(ratio, CBOT)=-0.46 : "
                        "la prime est LOCALE, pas un artefact du CBOT.",
    "v44_mechanism": "Le mécanisme et la magnitude de la compression ne sont pas prévisibles.",
    "v106_compression": "Le hasard de timing de la compression a une AUC proche du taux de base : "
                        "non prévisible.",
    "v125_curve": "La courbe accumulée montre une backwardation qui se resserre (NARROWING).",
    "v126_matif": "Substitution avec le MATIF blé : corrélation 0.477.",
    "v129_event": "Catalogue de 29 catalyseurs (météo CBOT, balance UE, détente de courbe, ~1/3 "
                  "chacun ; 10 % inconnus).",
    "v130_basis_regime": "Découverte : la demi-vie du basis RÉTRÉCIT avec l'extrême (modéré 8.3 j "
                         "-> fort 4.9 j -> extrême 3.3 j).",
    "v131_target": "Découverte : les signaux marginaux (z<1.2) sous-performent nettement (gain "
                   "6.09 vs 14.14) -> on attend une confirmation.",
    "v138_horizon": "Resultat negatif : la demi-vie de NIVEAU n'est pas l'horizon de TRADE reel "
                    "(9.5 j analytique vs 28.6 j reel, facteur 3).",
    "v162_vecm": "VECM CBOT/EMA : la vitesse d'ajustement de l'EMA domine (formalise V21), mais le "
                 "volet spot physique reste bloque.",
    "v164_hmm": "Régimes par HMM : pas d'apport robuste hors échantillon.",
    "v169_bayes": "Survie bayesienne de la réversion : cadre probabiliste, sans gain net clair.",
    "v170_causal": "Graphe causal (DAG) : pas de lien causal exploitable robuste.",
    "v171_placebo": "Test placebo (contrôle négatif) : sert à valider que l'edge n'est pas du bruit.",
    "v172_overfit": "Audit de sur-apprentissage sur les trades : garde-fou méthodologique.",
    "v175_signal_tiers": "Etagement du signal en tiers (forts 47 % / faibles 19 % de la performance).",
    "ema_cbot_cointegration": "CBOT et Euronext sont cointégrés (Johansen) : un équilibre de long "
                              "terme existe.",
    "ema_decomposition": "Décomposition du retour Euronext : la part CBOT domine, le résidu "
                         "européen pur est faible.",
    "ema_return_decomposition": "Le retour Euronext est surtout du CBOT converti ; la prime locale "
                                "est secondaire.",
    "ema_residual": "Le résidu européen pur est faible et peu prévisible directement.",
    "ema_smart_baselines": "Même avec des baselines 'intelligentes', la random walk reste la "
                           "meilleure sur le prix Euronext.",
    "ema_volatility": "La volatilité Euronext est modélisable (utile pour le risque, pas le prix).",
    "ema_storage": "Étude économique du stockage (carry) : cadre théorique, peu exploitable seul.",
    "ema_event_study": "Event study autour des publications USDA : effet sur la vol, pas un "
                       "signal de direction en quotidien.",
    "ema_basis": "Le basis est formalisé comme l'objet central de l'étude Euronext.",
    "cointegration": "Relation de cointégration CBOT/Euronext confirmée.",
    "benchmark": "Tableau de référence des baselines : la random walk est la barre à battre.",
    "purged_cv": "Validation croisée purgée (embargo) : garantit l'absence de fuite temporelle.",
    "leakage": "Audit anti-fuite : vérifie qu'aucune feature ne 'voit le futur'.",
    "market_calendar": "Calendrier de marché (week-ends/feriés Euronext) pour dater proprement.",
    "single_source": "Source unique de vérité pour le head premium (évite les divergences).",
    "state_machine": "Machine d'état de la prime (justifiée/excessive x compression saine/"
                     "retardée/ADVERSE/cible).",
}
VERDICT_MEANING = {
    "gardé": "Le test a donné un gain réel et stable contre la baseline : il est retenu comme "
             "brique de l'étude (voir les chiffres ci-dessus s'ils sont documentés).",
    "abandonné": "Le test n'a pas battu la baseline / a dégradé les métriques hors échantillon : "
                 "la famille est écartée (gardée au mieux comme contexte ou contrôle négatif).",
    "bloqué": "Le test n'est pas réalisable en l'état faute de données (ex. pas de contrats CBOT "
              "par maturité, pas d'EUR/USD quotidien) : piste mise en attente.",
    "outil": "Ce fichier n'est pas un signal mais un garde-fou : il produit des données propres, "
             "un calendrier de publication ou un audit anti-fuite qui fiabilisent les autres tests.",
    "exploration": "Étape de cadrage (choix de la cible, de l'horizon, décomposition, baseline) : "
                   "elle prépare les tests décisifs sans verdict tranché en soi.",
}
CONCLU = {
    "gardé": "✅ Brique CONSERVÉE : résultat exploitable, repris dans la suite de l'étude.",
    "abandonné": "❌ ABANDONNÉ : pas de signal exploitable hors échantillon (au mieux un "
                 "contexte ou un contrôle négatif).",
    "bloqué": "⛔ BLOQUÉ : piste en attente faute de données ; à rouvrir avec de meilleures sources.",
    "outil": "🔧 Outil VALIDÉ : sécurise le reste de l'étude (anti-fuite, calendriers, séries propres).",
    "exploration": "🔵 Étape FRANCHIE : a aidé à cadrer/affiner ; pas un verdict en soi, mais une "
                   "marche vers la réponse.",
}


def result_text(name: str, verdict: str) -> str:
    low = name.lower()
    for key, txt in RESULTS.items():
        if key in low:
            return txt
    return VERDICT_MEANING[verdict]


def collect() -> list[dict]:
    rows = []
    for f in sorted(TESTS.glob("test_*.py")):
        rows.append({"fichier": f.name, "type": "test", "question": assign_q(f.name, False),
                     "verdict": verdict_of(f.name), "description": docline(f),
                     "detail_doc": full_doc(f)})
    for d in sorted(EXT.glob("EXT*")):
        readme = d / "README.md"
        full = " ".join(readme.read_text(encoding="utf-8").split())[:1200] if readme.exists() else ""
        desc = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()[:160] \
            if readme.exists() else d.name
        rows.append({"fichier": d.name, "type": "experience_EXT",
                     "question": assign_q(d.name, True), "verdict": verdict_of(d.name),
                     "description": desc, "detail_doc": full})
    return rows


# --- tests performants (métriques réelles, documentées) -----------------------
PERFORMANTS = [
    ("EXT025 random walk (référence)", "AUC", 0.50, "référence imbattable RMSE"),
    ("V9 indicateur structurel", "AUC", 0.656, "cœur basis+saison"),
    ("V10 modèle 2 variables", "AUC", 0.694, "basis_z + saison"),
    ("EXT024 crop@H90 (recherche)", "AUC", 0.724, "Crop Condition direction"),
    ("Score de vente crop@H90 (holdout 2024+)", "AUC", 0.816, "hors échantillon CBOT"),
    ("V23 risque drawdown CBOT", "AUC", 0.74, "risque, pas direction"),
    ("Indicateur Euronext SELL_PARTIAL", "précision baisse", 0.716, "le prix baisse après"),
    ("EXT024 crop@H90 (holdout)", "DA", 0.686, "direction H90"),
    ("Score wasde@H40 (holdout)", "DA", 0.705, "direction H40"),
    ("EXT019 crop condition", "DA", 0.66, "+4.4 pts H90"),
]
VOL_PERF = [("EXT010 HAR", -23.0), ("EXT009 EGARCH", -23.7)]


def build_perf_html():
    fig = go.Figure()
    for metric, color in (("AUC", "#1f77b4"), ("DA", "#2ca02c"),
                          ("précision baisse", "#d62728")):
        rows = [(n, v, note) for n, m, v, note in PERFORMANTS if m == metric]
        if rows:
            fig.add_trace(go.Bar(x=[v for _, v, _ in rows], y=[n for n, _, _ in rows],
                                 orientation="h", name=metric,
                                 text=[f"{v:.3f} - {note}" for _, v, note in rows],
                                 textposition="auto", marker_color=color))
    fig.add_vline(x=0.5, line_dash="dash", annotation_text="hasard (0.5)")
    fig.update_layout(title="Tests aux bons résultats (AUC / DA / précision ; >0.5 = mieux que le hasard)",
                      height=520, margin={"l": 280, "t": 50}, barmode="group")
    vol = go.Figure(go.Bar(x=[v for _, v in VOL_PERF], y=[n for n, _ in VOL_PERF],
                           orientation="h", marker_color="#9467bd",
                           text=[f"{v:.1f}%" for _, v in VOL_PERF], textposition="auto"))
    vol.update_layout(title="Volatilité : réduction du RMSE vs random walk (plus négatif = mieux)",
                      height=240, margin={"l": 280, "t": 50})
    divs = "".join(pio.to_html(f, include_plotlyjs=False, full_html=False) for f in (fig, vol))
    _page(OUT / "tests_performants.html", "Tests performants - étude maïs",
          "Les seuls résultats clairement au-dessus du hasard : direction long-horizon "
          "(Crop/WASDE) et risque (volatilité). Tout le reste a été abandonné.", divs)


# --- conclusion ---------------------------------------------------------------
CONCLUSION = [
    "Prédire le PRIX exact du maïs est impossible avec les données gratuites : la random walk "
    "reste imbattable en RMSE (aucun modèle sur 36 ne la bat, test de Diebold-Mariano).",
    "Ce qu'on sait DÉTECTER sur le CBOT avec fiabilité (même si ce n'est pas le prix) :",
    "La direction à 90 jours via la Crop Condition US : AUC 0.816 sur le holdout 2024+ (jamais "
    "vu avant), un résultat solide et économiquement cohérent (grosse récolte = prix qui baisse).",
    "La direction à 40 jours via le ratio stocks-sur-usage du WASDE : DA 0.705 sur le holdout 2024+.",
    "Le risque de drawdown du CBOT : prévisible, AUC 0.74 (on sait dire quand le risque monte).",
    "La volatilité : les modèles HAR et EGARCH battent la random walk de 24 % de RMSE, c'est le "
    "résultat le plus solide de l'étude.",
    "L'issue ADVERSE (quand une vente de prime va mal tourner) : prévisible a priori, AUC 0.72.",
    "Le seul signal directionnel réel est l'OFFRE US (Crop Condition, WASDE) à horizon long ; la "
    "parcimonie gagne : 2 variables (basis_z + saison) suffisent (AUC 0.694), les modèles "
    "complexes n'ajoutent rien.",
    "Ce qu'on garde sur l'EURONEXT et le basis :",
    "Le basis revient à la moyenne (demi-vie 17 a 47 jours) ; vendre quand le basis est haut "
    "survit aux coûts hors crise (+115) ; indicateur structurel de vente AUC 0.656 a 0.694.",
    "La prime se compresse surtout quand le CBOT monte (la jambe CBOT pèse 6 fois la jambe "
    "Euronext) : 'vendre la prime' revient à 'parier sur une hausse relative du CBOT'.",
    "L'avantage est ASYMÉTRIQUE : vendre une prime haute est robuste, le pari inverse (prime "
    "basse) ne l'est pas (short bien supérieur a long).",
    "Le support CBOT divise par 2 le risque ADVERSE et double le PnL ; et la réversion du basis "
    "est plus rapide quand le CBOT soutient (environ 29 jours vers z0, 87.5 % des cas).",
    "Caractérisation des épisodes de prime haute : les épisodes tirés par le CBOT gagnent presque "
    "toujours (gain moyen +22.7), ceux tirés par l'Euronext gagnent moins (+14), et les épisodes "
    "ADVERSE ne sont jamais vraiment profitables (excursion favorable 5.7, durée 60 jours) mais "
    "sont distinguables tôt.",
    "La sortie partielle (revenir vers z 0.5 au lieu de z 0) évite plusieurs pertes en queue, "
    "surtout en contexte défavorable.",
    "Les découvertes importantes de l'étude :",
    "La prime européenne est LOCALE : la macro ne l'explique pas (R² hors échantillon -0.25).",
    "Spécificité européenne : la prime corrèle avec le basis (+0.59) et PAS avec le CBOT (-0.46), "
    "ce qui prouve une prime locale et non un simple artefact du CBOT.",
    "La demi-vie du basis rétrécit quand l'écart est extrême (8.3 jours en régime modéré, 3.3 "
    "jours en régime extrême) : plus le basis est tendu, plus il revient vite.",
    "Les signaux marginaux (faible écart, z<1.2) sous-performent nettement les signaux forts "
    "(gain 6.1 contre 14.1).",
    "Le CBOT prédit mieux ses BAISSES que ses HAUSSES (asymétrie directionnelle).",
    "Le signal météo n'est pas dans la météo MOYENNE mais dans les EXTRÊMES prévus : un dôme de "
    "chaleur prévu en pollinisation corrèle +0.31 avec le rendement CBOT (extrême prévu = CBOT "
    "+1.6 % contre -2.3 % le reste du temps), conforme a la chute non-linéaire du rendement au-delà "
    "de 30-32 degrés.",
    "Le meilleur signal d'alerte ADVERSE est l'écart de prix blé/maïs (wheat_corn_z, AUC 0.653) ; "
    "la substitution blé/maïs reste un CONTEXTE (corr 0.60), pas un prédicteur direct.",
    "Ce qu'on pensait prévisible et qui ne l'est PAS (falsifié par les tests) :",
    "Le prix exact (random walk imbattable) et la météo réalisée (déjà 'price-in', AUC 0.508).",
    "Les surprises WASDE en quotidien, les positions COT et la demande éthanol : aucun signal "
    "hors échantillon.",
    "Le mécanisme de la compression de prime (AUC 0.48) et son timing par modèle de hasard.",
    "La demi-vie du NIVEAU n'est PAS l'horizon de décision : analytique environ 9.5 jours contre "
    "28.6 jours réels sur les trades (facteur 3), il faut recaler l'horizon sur le réel.",
    "Le trend-following (le maïs ne tend pas), le stacking et le deep learning (ils sur-apprennent).",
    "L'explication 'fair-value' du basis (causalité de Granger rejetée hors échantillon).",
    "L'inversion saisonnière supposée du basis n'a pas résisté en forward (falsifiée).",
    "L'avantage du basis EMA n'est pas aussi SPÉCIFIQUE qu'espéré : le test placebo le retrouve "
    "en partie sur des spreads témoins, donc prudence.",
    "Les stratégies actives portent un risque de SUR-AJUSTEMENT (mesures PSR, DSR, PBO), d'où le "
    "choix assumé de préférer le simple au complexe.",
    "Les limites et les coûts (honnêteté de l'étude) :",
    "Le mur des coûts : l'avantage net est mince et concentré sur les signaux extrêmes (z>2) ; il "
    "survit a des coûts d'environ 5 €/t hors crise mais s'efface au-delà et hors des régimes favorables.",
    "Le score de vente final est FRAGILE : sur le holdout 2024+ il bat la random walk (DA 0.686) "
    "mais ne bat PAS une simple saisonnalité (0.752) sur une fenêtre courte (environ 1.5 an), a "
    "reconfirmer en forward.",
    "L'indicateur Euronext est RESEARCH_ONLY : il ordonne bien les retours (vendre une partie = "
    "-5.8 % a 90 jours, attendre = +5.1 %) mais discrimine mal hors échantillon (AUC 0.561) et le "
    "prix Euronext disponible est a 97 % un proxy.",
    "Le système live reste ANALYTIQUE (pas de paper-trading) et beaucoup de pistes sont bloquées "
    "par la donnée payante : courbe officielle par maturité, MATIF blé, intraday, consensus d'analystes.",
    "Bilan : on ne prédit pas le prix, mais on détecte un risque de baisse à 90 jours avec "
    "environ 73 % de précision quand l'indicateur dit 'vendre une partie' ; ces signaux forts "
    "n'apparaissent qu'environ 1 fois par an (17 épisodes en 16 ans). C'est une aide a la "
    "decision de vente, pas une prevision de prix ni un robot de trading.",
]


# fiches RÉDIGÉES À LA MAIN (claires, directes) pour certains fichiers (override de l'auto)
CURATED = {
    # ---- Q1 : prédire le prix ? ------------------------------------------------
    "EXT025_random_walk_and_futures_price_benchmark": {
        "sous_question": "Un modèle arrive-t-il à prévoir le prix du maïs mieux que la règle de "
                         "référence la plus simple (le prix de demain = celui d'aujourd'hui) ?",
        "fait": "On répond à la question la plus fondamentale de toute l'étude : est-ce qu'un "
                "modèle, même élaboré, arrive à prévoir le prix du maïs mieux qu'une règle de "
                "référence très simple ? Cette règle s'appelle la marche aléatoire (random "
                "walk) : elle suppose que le prix de demain sera celui d'aujourd'hui. Si on "
                "n'arrive pas à la battre, c'est que le prix est imprévisible et qu'un modèle "
                "compliqué n'apporte rien.",
        "comment": "On prend l'historique des prix du maïs CBOT (Chicago) et Euronext de 2000 à "
                   "2023. Pour 4 horizons (5, 20, 40 et 90 jours de bourse), on compare "
                   "plusieurs prédicteurs simples : la marche aléatoire, la marche aléatoire "
                   "avec tendance saisonnière, le dernier retour, une moyenne mobile et le prix "
                   "des contrats à terme. On mesure l'erreur moyenne (RMSE) de chacun et on "
                   "utilise un test statistique (Diebold-Mariano) pour distinguer une vraie "
                   "différence d'une différence due au hasard. Aucun réglage n'est appris.",
        "resultats": "Le résultat est sans appel : sur les 36 combinaisons (9 prédicteurs x 4 "
                     "horizons), aucune ne bat la marche aléatoire de façon significative. "
                     "Autrement dit, 'le prix de demain = le prix d'aujourd'hui' est la "
                     "meilleure prévision possible. C'est cohérent avec la théorie des marchés "
                     "efficients : l'information connue est déjà dans le prix actuel.",
        "conclusion": "Le prix exact du maïs n'est pas prévisible avec ces données. Ce n'est "
                      "pas un échec de méthode mais un vrai résultat : il faut changer "
                      "d'objectif (la direction, le risque). Ce tableau devient la référence à "
                      "battre pour tous les tests suivants.",
    },
    "test_benchmark_canonical.py": {
        "sous_question": "Quelle référence simple tout modèle futur devra-t-il battre pour qu'on "
                         "le considère réellement utile ?",
        "fait": "On installe le banc d'essai officiel de l'étude : la liste figée des "
                "prédicteurs simples auxquels tout modèle futur devra se comparer. Le but est "
                "d'avoir une référence honnête et stable, pour ne jamais conclure qu'un modèle "
                "fonctionne sans point de comparaison.",
        "comment": "On code une suite de prédicteurs simples (marche aléatoire, dérive, dernier "
                   "retour, moyenne mobile, persistance saisonnière) et un protocole "
                   "d'évaluation unique : mêmes horizons, mêmes périodes, même mesure (erreur "
                   "RMSE et précision de direction), en walk-forward. Données : prix CBOT et "
                   "Euronext.",
        "resultats": "On obtient un tableau de référence reproductible. La marche aléatoire en "
                     "ressort comme la référence la plus difficile à battre ; les autres "
                     "servent de garde-fous. Ce tableau est ensuite cité par toutes les "
                     "expériences pour juger si elles apportent vraiment quelque chose.",
        "conclusion": "C'est un outil central de l'étude, pas un signal : il garantit que toute "
                      "affirmation du type 'mon modèle est bon' est mesurée contre une "
                      "référence solide.",
    },
    "test_ema_price_forecast.py": {
        "sous_question": "Le prix Euronext (en euros par tonne) est-il plus prévisible "
                         "directement que le prix CBOT ?",
        "fait": "On pose la même question côté Euronext (le maïs européen) : peut-on prévoir "
                "directement le prix futur en euros par tonne et faire mieux que les références "
                "simples ? On vérifie si le marché européen est plus prévisible que l'américain.",
        "comment": "On entraîne des modèles de prévision du prix sur l'historique Euronext, aux "
                   "mêmes horizons, et on les compare à la marche aléatoire avec la même mesure "
                   "d'erreur, en walk-forward. Données : série de prix Euronext continue.",
        "resultats": "Même conclusion qu'au CBOT : la marche aléatoire reste imbattable sur le "
                     "prix Euronext. Le marché européen n'est pas plus prévisible. La seule "
                     "piste intéressante n'est pas le prix mais le basis (l'écart Euronext "
                     "moins CBOT).",
        "conclusion": "Le prix Euronext n'est pas prévisible directement. Cela oriente la suite "
                      "de l'étude vers le basis et la prime européenne plutôt que vers le prix.",
    },
    # ---- Q-DATA : données propres et anti-fuite --------------------------------
    "EXT026_wasde_vintage_pipeline": {
        "sous_question": "Peut-on utiliser les rapports WASDE de l'USDA sans tricher, c'est-à-"
                         "dire en ne voyant chaque chiffre qu'à partir de sa vraie date de "
                         "publication ?",
        "fait": "On reconstruit un historique 'vintage' des rapports WASDE : pour chaque "
                "rapport, on garde la valeur telle qu'elle était publiée à l'époque, datée à sa "
                "vraie date de sortie. L'objectif est d'empêcher un modèle d'utiliser un chiffre "
                "avant qu'il ne soit réellement connu, ce qui fausserait tous les résultats.",
        "comment": "On analyse les archives officielles de l'USDA (textes bruts), on en extrait "
                   "les variables clés (stocks de fin, stocks-to-use, production, exports, prix) "
                   "et on attache à chacune sa date de publication réelle (plus un jour ouvré "
                   "pour la disponibilité). On contrôle en relisant 3 rapports anciens que les "
                   "valeurs correspondent bien à celles publiées à l'époque.",
        "resultats": "Le pipeline est validé (24 valeurs sur 24 retrouvées). Surtout, on "
                     "découvre que la série WASDE interne utilisée jusque-là exposait ses "
                     "valeurs environ 8 jours avant la publication réelle (143 rapports sur "
                     "160) : une fuite d'information qui rendait les tests trop optimistes.",
        "conclusion": "Brique gardée et essentielle : ce vintage devient la source WASDE unique "
                      "et anti-fuite de toute l'étude, et la fuite détectée est corrigée.",
    },
    "EXT006_roll_method_volume_based": {
        "sous_question": "Notre série de prix continue est-elle propre, ou la façon de raccorder "
                         "les contrats successifs crée-t-elle de faux mouvements de prix ?",
        "fait": "Un contrat à terme expire et on passe au suivant (le 'roll') ; mal fait, ce "
                "raccord crée un saut de prix artificiel qui n'est pas un vrai mouvement de "
                "marché. On vérifie si nos séries CBOT et Euronext souffrent de ce problème.",
        "comment": "On compare la série continue à une série raccordée proprement (sur le "
                   "contrat le plus échangé en volume) et on mesure les sauts de prix les jours "
                   "de roll par rapport aux jours normaux. Données : contrats individuels CBOT "
                   "et Euronext.",
        "resultats": "Côté CBOT, aucun artefact détecté : nos résultats sont sûrs. Côté "
                     "Euronext brut, un saut moyen de 10 euros/t les jours de roll (6,6 fois la "
                     "normale), qui inverse même le momentum dans 27 cas sur 68 ; la série "
                     "ajustée corrige ce défaut. La reconstruction propre sur le passé est "
                     "bloquée (on n'a que le contrat de tête en historique).",
        "conclusion": "On retient une règle d'hygiène : utiliser la série Euronext ajustée (ou "
                      "exclure les jours de roll), pour ne pas confondre un raccord technique "
                      "avec un signal.",
    },
    "test_data_quality.py": {
        "sous_question": "Nos données brutes sont-elles complètes et cohérentes (pas de trous, "
                         "de doublons ni de valeurs aberrantes) ?",
        "fait": "On vérifie la qualité de base de chaque source de données avant tout modèle : "
                "absence de doublons de dates, continuité des séries, valeurs dans des plages "
                "plausibles et types corrects.",
        "comment": "Des contrôles automatiques parcourent chaque fichier (prix, WASDE, météo, "
                   "COT...) et signalent toute anomalie : date dupliquée, trou anormal, prix "
                   "négatif ou hors plage.",
        "resultats": "Les sources passent les contrôles après nettoyage ; les anomalies "
                     "trouvées sont corrigées ou documentées.",
        "conclusion": "Outil de base : sans données propres, aucun modèle n'est fiable. C'est "
                      "la première étape obligatoire de l'étude.",
    },
    "test_data_truth_audit_v159.py": {
        "sous_question": "Les données qui alimentent réellement nos signaux sont-elles celles "
                         "qu'on croit (pas de version corrompue ou périmée) ?",
        "fait": "On met en place un pack d'audit de la 'vérité' des données : on vérifie que les "
                "valeurs effectivement utilisées par les signaux correspondent bien aux sources "
                "officielles attendues, à la bonne date.",
        "comment": "On recoupe les valeurs servant au calcul des signaux avec les fichiers "
                   "sources d'origine, on contrôle les dates et on signale tout écart "
                   "(valeur différente, date décalée, source inattendue).",
        "resultats": "L'audit confirme la cohérence après corrections, et sert de filet de "
                     "sécurité contre les régressions silencieuses (un fichier modifié sans "
                     "qu'on s'en aperçoive).",
        "conclusion": "Outil de contrôle : garantit que les conclusions reposent sur les vraies "
                      "données et pas sur une version altérée.",
    },
    "test_leakage_global.py": {
        "sous_question": "Est-ce qu'une de nos variables 'voit le futur' sans qu'on s'en rende "
                         "compte (fuite de données) ?",
        "fait": "On met en place une batterie de contrôles qui vérifient, sur tout le pipeline, "
                "qu'aucune information du futur ne se glisse dans les variables servant à "
                "prédire. C'est le garde-fou central contre la fuite de données, l'erreur la "
                "plus dangereuse en prévision.",
        "comment": "Pour chaque variable, on vérifie qu'elle n'est disponible qu'à partir de sa "
                   "date réelle, que les normalisations et sélections se font uniquement sur le "
                   "passé, et que les fenêtres glissantes n'incluent jamais de valeurs "
                   "postérieures. Le tout est automatisé en tests qui échouent si une fuite "
                   "apparaît.",
        "resultats": "Les contrôles passent et ont permis de détecter des fuites concrètes (par "
                     "exemple la série WASDE en avance). Tant qu'ils sont verts, on peut faire "
                     "confiance aux chiffres.",
        "conclusion": "Outil fondamental : il sécurise toutes les conclusions de l'étude. Un "
                      "résultat n'a de valeur que si ces contrôles passent.",
    },
    "test_leakage_calendar.py": {
        "sous_question": "Les données à date de publication (WASDE, Crop Condition, COT) sont-"
                         "elles bien utilisées seulement après leur sortie ?",
        "fait": "On vérifie spécifiquement le respect des calendriers de publication : chaque "
                "donnée datée (rapport WASDE, condition de culture, positions COT) ne doit "
                "entrer dans les variables qu'à partir de sa date de publication réelle.",
        "comment": "On confronte la date d'usage de chaque variable à son calendrier de "
                   "publication officiel (WASDE, NASS le lundi, COT le vendredi) et on signale "
                   "tout usage anticipé.",
        "resultats": "Les contrôles confirment que les données ne sont utilisées qu'après "
                     "publication (par exemple WASDE à publication plus un jour ouvré, COT au "
                     "vendredi et non au mardi des positions).",
        "conclusion": "Outil anti-fuite ciblé sur le calendrier : complète le contrôle global "
                      "et évite l'erreur classique d'utiliser un rapport avant sa sortie.",
    },
    "test_purged_cv.py": {
        "sous_question": "Comment évaluer un modèle dans le temps sans qu'il triche en "
                         "s'entraînant sur des données trop proches de ce qu'il doit prédire ?",
        "fait": "On met en place une validation croisée 'purgée avec embargo' : quand on teste "
                "sur une période, on retire de l'entraînement les jours trop proches qui se "
                "chevauchent avec la cible, pour éviter une fuite indirecte.",
        "comment": "Entre la fin de l'entraînement et le début du test, on impose un embargo "
                   "(un trou) proportionnel à l'horizon de prédiction, et on purge les exemples "
                   "dont la cible chevauche la période de test. C'est une méthode standard en "
                   "finance (Lopez de Prado).",
        "resultats": "On obtient une évaluation honnête des modèles, sans optimisme dû à un "
                     "chevauchement temporel. C'est le protocole d'évaluation utilisé ensuite "
                     "dans toute l'étude.",
        "conclusion": "Outil méthodologique : garantit que les performances mesurées sont "
                      "réalistes et reproductibles.",
    },
    "test_market_calendar.py": {
        "sous_question": "Comment distinguer un jour sans cotation normal (week-end, férié) "
                         "d'une vraie donnée manquante à signaler ?",
        "fait": "On construit le calendrier des jours de bourse Euronext (week-ends et fériés) "
                "pour ne pas confondre une fermeture normale du marché avec un trou de données.",
        "comment": "On code les règles de jours fériés Euronext et on les intègre au contrôle "
                   "de fraîcheur : un jour sans cotation qui est férié est normal, sinon c'est "
                   "une alerte.",
        "resultats": "Le calendrier évite de fausses alertes (par exemple les jours fériés de "
                     "fin mai) et fiabilise le suivi de fraîcheur des données.",
        "conclusion": "Outil de calendrier nécessaire au suivi propre des données et à un "
                      "indicateur qui ne s'affole pas un jour férié.",
    },
    "test_publication_calendar.py": {
        "sous_question": "À quelles dates exactes les rapports (WASDE, Crop Condition, COT) "
                         "sortent-ils, pour ne les utiliser qu'après ?",
        "fait": "On construit le calendrier des dates de publication des données à diffusion "
                "périodique, qui sert de base à toute la logique anti-fuite.",
        "comment": "On rassemble les dates officielles de publication (WASDE mensuel, NASS "
                   "hebdomadaire, COT hebdomadaire) et on les expose au pipeline pour dater "
                   "correctement la disponibilité de chaque variable.",
        "resultats": "Le calendrier fournit, pour chaque donnée, le moment précis où elle "
                     "devient utilisable, ce qui permet aux contrôles anti-fuite de fonctionner.",
        "conclusion": "Outil de référence : la brique de calendrier sur laquelle reposent les "
                      "tests de fuite.",
    },
    "test_usda_release_calendar.py": {
        "sous_question": "Connaît-on assez précisément les dates de publication de l'USDA, même "
                         "quand elles ne sont pas fournies, pour rester anti-fuite ?",
        "fait": "On construit (avec une approximation prudente quand la date exacte manque) le "
                "calendrier des publications USDA, afin de ne jamais utiliser un rapport avant "
                "sa sortie même en l'absence de date officielle.",
        "comment": "On combine les dates officielles disponibles et, à défaut, un repli "
                   "conservateur (par exemple le 12 du mois) qui retarde plutôt qu'avance la "
                   "disponibilité, pour rester du côté sûr.",
        "resultats": "On dispose d'un calendrier complet et prudent ; les quelques dates "
                     "approximées retardent la disponibilité, ce qui évite toute fuite.",
        "conclusion": "Outil : sécurise l'usage des données USDA même lorsque la date exacte "
                      "n'est pas connue.",
    },
    "test_ema_data_audit.py": {
        "sous_question": "Les données de prix Euronext sont-elles fiables et utilisables pour "
                         "l'étude ?",
        "fait": "On audite la qualité et la couverture des données de prix Euronext : période "
                "couverte, trous, doublons, et part de données réelles par rapport aux données "
                "approchées (proxy).",
        "comment": "On parcourt la série Euronext, on mesure la couverture temporelle, on "
                   "repère les trous et doublons, et on distingue les sources (officielles ou "
                   "proxy exploratoire).",
        "resultats": "L'audit montre une série utilisable mais en grande partie proxy "
                     "(exploratoire) sur le passé, ce qui limite la portée des conclusions "
                     "côté Euronext et impose de le signaler partout.",
        "conclusion": "Outil : fixe honnêtement ce que l'on peut et ne peut pas conclure avec "
                      "les données Euronext disponibles.",
    },
    "test_ema_data_audit_v2.py": {
        "sous_question": "La qualité des données Euronext tient-elle après mise à jour et "
                         "enrichissement des sources ?",
        "fait": "On reprend l'audit des données Euronext dans une version actualisée, pour "
                "vérifier que les ajouts et corrections de sources n'ont pas dégradé la qualité.",
        "comment": "Même protocole d'audit que la première version (couverture, trous, "
                   "doublons, part de proxy), appliqué au jeu de données mis à jour.",
        "resultats": "La qualité reste cohérente ; la dépendance au proxy persiste sur "
                     "l'historique, confirmant la limite déjà identifiée.",
        "conclusion": "Outil : confirme la fiabilité (et les limites) des données Euronext dans "
                      "leur version la plus récente.",
    },
    "test_ema_target_integrity.py": {
        "sous_question": "Les cibles à prédire côté Euronext sont-elles construites sans fuite "
                         "et sans erreur de décalage ?",
        "fait": "On vérifie l'intégrité des cibles (les valeurs futures que les modèles doivent "
                "prédire) : bon horizon, bonne date, et aucune information future qui aurait "
                "déteint sur les variables d'entrée.",
        "comment": "On contrôle que la cible à horizon h utilise bien la vraie ligne de marché "
                   "future (et non une date approximée), et qu'elle est strictement séparée "
                   "des variables connues à la date de décision.",
        "resultats": "Les cibles sont saines ; ce contrôle évite l'erreur subtile d'aligner une "
                     "cible sur une mauvaise date, qui gonflerait artificiellement les scores.",
        "conclusion": "Outil : assure que ce que les modèles 'apprennent à prédire' est correct "
                      "et honnête.",
    },
    "test_experiment_registry.py": {
        "sous_question": "Comment garder une trace fiable de toutes les expériences menées pour "
                         "ne pas se perdre ni se contredire ?",
        "fait": "On met en place un registre global des expériences : chaque test est "
                "enregistré avec son objectif, son statut et son verdict, pour garder une vue "
                "d'ensemble cohérente de l'étude.",
        "comment": "Un module centralise la liste des expériences et impose des règles "
                   "(identifiant unique, statut, dépendances), vérifiées par des tests.",
        "resultats": "On dispose d'un fil conducteur traçable : on sait ce qui a été testé, "
                     "avec quel résultat, ce qui évite de refaire ou de contredire un test "
                     "passé.",
        "conclusion": "Outil d'organisation : garantit la cohérence et la traçabilité de "
                      "l'ensemble de la démarche.",
    },
    "test_proxy_audit.py": {
        "sous_question": "Quand on remplace une donnée officielle par une donnée approchée "
                         "(proxy), à quel point se trompe-t-on ?",
        "fait": "On audite les données 'proxy' (approchées) utilisées faute de source "
                "officielle, pour mesurer leur écart aux vraies valeurs et savoir jusqu'où on "
                "peut leur faire confiance.",
        "comment": "On compare le proxy aux quelques valeurs officielles disponibles "
                   "(niveaux, percentiles) et on quantifie l'écart.",
        "resultats": "Les niveaux du proxy sont jugés globalement représentatifs (par exemple "
                     "le basis officiel tombe dans le haut de la distribution du proxy), mais "
                     "l'usage reste exploratoire et signalé comme tel.",
        "conclusion": "Outil : encadre honnêtement l'usage des données approchées et leurs "
                      "limites.",
    },
    "test_roll_audit.py": {
        "sous_question": "Les dates de roll (changement de contrat) sont-elles bien identifiées "
                         "et traitées dans nos séries ?",
        "fait": "On audite les jours de roll : on vérifie qu'ils sont correctement repérés et "
                "que les features de retour n'y intègrent pas le saut technique de raccord.",
        "comment": "On liste les dates de roll, on inspecte les retours autour de ces jours et "
                   "on vérifie que la série ajustée ou l'exclusion des rolls neutralise "
                   "l'artefact.",
        "resultats": "Les rolls sont identifiés et l'artefact est neutralisé sur la série "
                     "ajustée ; cela protège les indicateurs de basis d'un faux signal.",
        "conclusion": "Outil : complète l'hygiène de série (EXT006) en s'assurant que les rolls "
                      "ne polluent pas les signaux.",
    },
    "test_paths_ema.py": {
        "sous_question": "Les chemins des fichiers de données Euronext sont-ils définis de façon "
                         "centralisée et fiable ?",
        "fait": "On vérifie que tous les chemins de fichiers Euronext sont déclarés à un seul "
                "endroit (le module de configuration des chemins), pour éviter les références "
                "dispersées et les erreurs de fichier introuvable.",
        "comment": "Des tests s'assurent que chaque chemin attendu existe dans la configuration "
                   "centrale et pointe vers le bon emplacement.",
        "resultats": "Les chemins sont centralisés et cohérents, ce qui rend le pipeline "
                     "reproductible sur une autre machine.",
        "conclusion": "Outil d'infrastructure : évite les bugs de chemins et fiabilise "
                      "l'exécution de toute l'étude.",
    },
    "test_ema_utils.py": {
        "sous_question": "Dispose-t-on de fonctions de base fiables et testées pour manipuler "
                         "les données Euronext ?",
        "fait": "On teste les fonctions utilitaires communes au traitement Euronext (conversions, "
                "alignements de dates, agrégations), pour s'assurer qu'elles sont correctes.",
        "comment": "Chaque fonction utilitaire est couverte par des tests unitaires avec des "
                   "cas connus, pour vérifier qu'elle renvoie le bon résultat.",
        "resultats": "Les utilitaires passent leurs tests : les briques de base du traitement "
                     "Euronext sont sûres.",
        "conclusion": "Outil : socle technique fiable sur lequel reposent les traitements "
                      "Euronext.",
    },
    "test_ema_targets.py": {
        "sous_question": "Comment définir proprement ce qu'on cherche à prédire côté Euronext ?",
        "fait": "On construit les cibles Euronext (les valeurs futures à prédire, par exemple le "
                "retour à 20, 40 ou 90 jours) et on vérifie qu'elles sont correctement formées.",
        "comment": "On calcule les retours futurs à chaque horizon en utilisant la vraie ligne "
                   "de marché future, sans mélanger avec les variables connues à la date de "
                   "décision.",
        "resultats": "Les cibles sont bien définies et cohérentes avec les horizons étudiés, "
                     "prêtes à servir d'objectif aux modèles.",
        "conclusion": "Étape de préparation : sans cibles correctes, aucune évaluation de modèle "
                      "n'a de sens.",
    },
    "test_ema_features_pipeline.py": {
        "sous_question": "Comment construit-on proprement, et sans fuite, les variables "
                         "Euronext utilisées par les modèles ?",
        "fait": "On met en place le pipeline qui transforme les données brutes Euronext en "
                "variables exploitables (retours, volatilité, saison, etc.), de façon "
                "reproductible et anti-fuite.",
        "comment": "Le pipeline calcule chaque variable uniquement à partir d'informations "
                   "disponibles à la date considérée, normalise sur le passé, et produit un "
                   "tableau de features daté.",
        "resultats": "On obtient un jeu de variables propre et reproductible, base des "
                     "expériences Euronext.",
        "conclusion": "Étape de préparation : fournit des variables fiables, condition "
                      "nécessaire à toute modélisation honnête.",
    },
    "test_ema_data_quality_split.py": {
        "sous_question": "La qualité des données Euronext est-elle homogène dans le temps, ou "
                         "varie-t-elle entre l'ancienne période (proxy) et la récente "
                         "(officielle) ?",
        "fait": "On découpe l'historique Euronext par période et par source pour vérifier que la "
                "qualité ne change pas brutalement (ce qui biaiserait les comparaisons).",
        "comment": "On sépare les données selon leur origine et leur période, et on compare la "
                   "qualité (trous, niveaux, cohérence) entre les segments.",
        "resultats": "La qualité est correcte mais l'historique ancien repose surtout sur du "
                     "proxy, alors que le récent contient quelques données officielles : il "
                     "faut en tenir compte dans les conclusions.",
        "conclusion": "Outil : met en évidence l'hétérogénéité des données Euronext dans le "
                      "temps, à garder en tête.",
    },
    "test_ema_h90_stress_test.py": {
        "sous_question": "Les résultats Euronext tiennent-ils dans des conditions difficiles à "
                         "l'horizon long (90 jours) ?",
        "fait": "On soumet l'analyse à un test de résistance à l'horizon 90 jours : on vérifie "
                "que les conclusions ne s'effondrent pas sur les sous-périodes les plus dures.",
        "comment": "On rejoue l'évaluation à H90 sur des découpages exigeants et on observe la "
                   "stabilité des performances.",
        "resultats": "L'horizon 90 jours reste le plus informatif mais aussi le plus sensible : "
                     "les performances varient selon les périodes, ce qui confirme la prudence "
                     "à garder.",
        "conclusion": "Étape de robustesse : confirme que H90 est intéressant mais fragile, à "
                      "valider dans le temps.",
    },
    "test_euronext_ema_collector.py": {
        "sous_question": "Peut-on récupérer de façon fiable l'historique des contrats Euronext ?",
        "fait": "On teste le collecteur qui récupère les données de prix Euronext (par contrat), "
                "pour s'assurer qu'il fonctionne et renvoie des données exploitables.",
        "comment": "On exécute le collecteur en mode contrôlé (hors-ligne ou simulé) et on "
                   "vérifie le format, les dates et la cohérence des données récupérées.",
        "resultats": "Le collecteur fonctionne, mais l'historique réellement disponible en "
                     "officiel est limité ; une grande partie reste du proxy.",
        "conclusion": "Étape d'acquisition : fournit les données Euronext, en assumant leur "
                      "caractère partiellement proxy.",
    },
    "test_euronext_daily_collector.py": {
        "sous_question": "Peut-on collecter automatiquement le prix Euronext chaque jour pour un "
                         "suivi en continu ?",
        "fait": "On teste le collecteur quotidien Euronext, qui doit récupérer le prix du jour "
                "de façon automatique et fiable.",
        "comment": "On simule des exécutions quotidiennes et on vérifie que les données sont "
                   "bien datées, sans doublon ni trou non justifié.",
        "resultats": "La collecte quotidienne fonctionne en routine ; elle alimente le suivi "
                     "forward de l'indicateur.",
        "conclusion": "Outil d'acquisition : permet un suivi quotidien, sous réserve de la "
                      "qualité des sources disponibles.",
    },
    "test_euronext_evening_snapshots.py": {
        "sous_question": "Peut-on capturer de façon fiable le prix de clôture Euronext du soir ?",
        "fait": "On teste la capture du 'snapshot' de clôture du soir (le prix de règlement "
                "officiel), pour disposer d'une valeur stable de fin de journée.",
        "comment": "On valide la capture en mode hors-ligne et simulé, en vérifiant l'horaire, "
                   "la valeur et la robustesse aux jours fériés.",
        "resultats": "La capture du soir fonctionne et fournit un point de prix propre et daté "
                     "pour chaque séance.",
        "conclusion": "Outil d'acquisition : assure une valeur de clôture fiable pour le suivi.",
    },
    "test_euronext_features.py": {
        "sous_question": "Quelles variables exploitables peut-on tirer des données Euronext "
                         "(prix, courbe, échéances) ?",
        "fait": "On construit et on teste les variables dérivées des données Euronext (par "
                "exemple la forme de la courbe entre échéances), pour enrichir l'analyse.",
        "comment": "On calcule ces variables à partir des prix par contrat et on vérifie leur "
                   "cohérence et leur disponibilité dans le temps.",
        "resultats": "On obtient quelques variables Euronext utilisables, mais leur historique "
                     "est limité (courbe peu profonde), ce qui restreint leur usage.",
        "conclusion": "Étape de préparation : fournit des variables Euronext, dont la portée "
                      "reste limitée par la profondeur des données.",
    },
    "test_experiment_registry_v6.py": {
        "sous_question": "Le registre des expériences reste-t-il cohérent avec le programme de "
                         "consolidation (V6) ?",
        "fait": "On met à jour et on teste le registre des expériences pour la phase V6, afin de "
                "garder une trace fiable des nouveaux tests et de leurs verdicts.",
        "comment": "On vérifie que les nouvelles expériences sont bien enregistrées avec leur "
                   "identifiant, statut et résultat, sans collision ni doublon.",
        "resultats": "Le registre reste cohérent et à jour, ce qui préserve la traçabilité de "
                     "la démarche au fil des phases.",
        "conclusion": "Outil d'organisation : maintient une vue d'ensemble fiable des "
                      "expériences.",
    },
    "test_hierarchical_explanation.py": {
        "sous_question": "Peut-on attribuer clairement la performance et le risque à des "
                         "familles de variables, de façon hiérarchique ?",
        "fait": "On explique le comportement de l'indicateur en regroupant les variables par "
                "familles (marché, basis, saison, etc.) et en mesurant l'apport de chaque "
                "famille, du plus général au plus fin.",
        "comment": "On décompose la contribution des familles de variables de manière "
                   "hiérarchique, ce qui évite d'attribuer un effet à une variable isolée alors "
                   "qu'il vient d'un groupe.",
        "resultats": "On obtient une lecture claire de ce qui porte le signal (les familles "
                     "marché et basis dominent), utile pour comprendre et communiquer.",
        "conclusion": "Résultat gardé : fournit une explication structurée et honnête de "
                      "l'origine du signal.",
    },
    "test_asymmetric_module.py": {
        "sous_question": "Faut-il pénaliser différemment une erreur de hausse et une erreur de "
                         "baisse, puisqu'elles n'ont pas le même coût pour un vendeur ?",
        "fait": "On explore une évaluation asymétrique : pour un agriculteur qui vend, se "
                "tromper en ratant une baisse coûte plus cher que rater une hausse, donc on "
                "teste des scores qui pénalisent davantage les erreurs les plus coûteuses.",
        "comment": "On applique des fonctions de coût asymétriques à l'évaluation des signaux "
                   "et on regarde si cela change le classement des modèles ou des seuils.",
        "resultats": "L'asymétrie aide à orienter la décision vers la prudence (vendre) sans "
                     "créer de signal nouveau ; c'est un réglage de décision, pas une source de "
                     "prédiction.",
        "conclusion": "Étape de cadrage : utile pour calibrer la décision de vente, à intégrer "
                      "plus tard dans le score.",
    },
    "test_cli_ema.py": {
        "sous_question": "Peut-on lancer les traitements Euronext via une commande simple et "
                         "reproductible ?",
        "fait": "On teste l'interface en ligne de commande (CLI) qui permet de lancer les "
                "étapes Euronext (collecte, features, rapports) d'une façon simple et répétable.",
        "comment": "On exécute les commandes en mode contrôlé et on vérifie qu'elles "
                   "produisent les sorties attendues sans erreur.",
        "resultats": "Les commandes fonctionnent : l'étude Euronext est reproductible par de "
                     "simples appels en ligne de commande.",
        "conclusion": "Outil : rend l'étude facile à relancer et à automatiser.",
    },
    "test_barchart_ema_probe.py": {
        "sous_question": "Peut-on récupérer des prix Euronext fiables via le fournisseur "
                         "Barchart ?",
        "fait": "On teste l'accès aux données Euronext via Barchart, pour voir si cette source "
                "peut fournir un historique de prix exploitable.",
        "comment": "On sonde l'endpoint Barchart (en mode contrôlé) et on évalue la couverture "
                   "et la qualité des données renvoyées.",
        "resultats": "L'accès ne fournit qu'un historique partiel et surtout du proxy, "
                     "insuffisant pour une série officielle complète.",
        "conclusion": "Bloqué : la source Barchart ne suffit pas à obtenir un historique "
                      "Euronext officiel ; piste mise en attente.",
    },
    "test_euronext_history_probe.py": {
        "sous_question": "L'historique complet des contrats Euronext est-il accessible via les "
                         "endpoints publics ?",
        "fait": "On sonde les endpoints publics Euronext pour voir si on peut récupérer "
                "l'historique complet des contrats expirés.",
        "comment": "On teste les points d'accès (en mode hors-ligne et simulé) et on mesure ce "
                   "qu'ils renvoient réellement sur le passé.",
        "resultats": "Les endpoints publics ne donnent pas les contrats expirés sur "
                     "2014-2025 ; il manque un fichier historique manuel pour compléter.",
        "conclusion": "Bloqué : pas d'historique officiel complet par les endpoints publics ; "
                      "nécessite une source de données dédiée.",
    },
    "test_dce_dalian_collector.py": {
        "sous_question": "Le maïs chinois (bourse de Dalian) apporte-t-il une information utile "
                         "à notre étude ?",
        "fait": "On teste un collecteur pour le maïs de Dalian (Chine), afin d'évaluer si ce "
                "marché pourrait enrichir l'analyse.",
        "comment": "On sonde la source Dalian (en mode contrôlé) et on évalue la disponibilité "
                   "et la cohérence des données.",
        "resultats": "Les données ne sont pas suffisamment disponibles ou alignables pour être "
                     "exploitées ici ; la piste n'est pas creusée davantage.",
        "conclusion": "Bloqué : source Dalian non exploitable en l'état, mise en attente.",
    },
    "test_intraday_aligned_basis.py": {
        "sous_question": "Aligner le CBOT et l'Euronext à la même heure de la journée "
                         "améliore-t-il la mesure du basis ?",
        "fait": "On teste l'idée de comparer CBOT et Euronext à un même instant (intraday) "
                "plutôt qu'avec des clôtures décalées, pour mesurer le basis plus proprement.",
        "comment": "On reconstruit un basis aligné sur l'heure de règlement (avec des données "
                   "intraday simulées faute d'historique réel) et on compare à la mesure "
                   "classique.",
        "resultats": "L'idée est cohérente mais reste bloquée par l'absence d'historique "
                     "intraday réel : on ne peut pas la valider sur le passé.",
        "conclusion": "Bloqué : nécessiterait des données intraday historiques ; piste en "
                      "attente.",
    },
    # ---- Q1 (suite) : prédire le prix ? ---------------------------------------
    "test_benchmark_suite.py": {
        "sous_question": "Au-delà de la marche aléatoire, quels autres prédicteurs simples et "
                         "'professionnels' faut-il inclure dans la référence à battre ?",
        "fait": "On élargit le banc d'essai avec une gamme plus complète de prédicteurs de "
                "référence, des plus simples (naïfs) aux plus sérieux (professionnels), pour "
                "que la comparaison soit vraiment exigeante.",
        "comment": "On ajoute à la marche aléatoire d'autres références (dérive, moyennes, "
                   "persistance, modèle de marché) et on les évalue toutes avec le même "
                   "protocole et la même mesure d'erreur. Données : prix CBOT et Euronext.",
        "resultats": "La marche aléatoire reste la plus difficile à battre ; les références "
                     "plus sérieuses ne font pas mieux sur le prix.",
        "conclusion": "Outil : étoffe la référence pour qu'aucun modèle ne paraisse bon "
                      "uniquement parce que la barre était trop basse.",
    },
    "test_cbot_target_lab.py": {
        "sous_question": "Quelle est la bonne chose à prédire sur le CBOT (le prix, le retour, "
                         "la direction, un seuil) pour avoir une chance d'être utile ?",
        "fait": "On ouvre un laboratoire de cibles : au lieu de s'acharner sur le prix, on "
                "compare plusieurs objectifs de prédiction possibles sur le CBOT pour voir "
                "lesquels sont à la fois prévisibles et utiles.",
        "comment": "On construit différentes cibles (retour à plusieurs horizons, sens de la "
                   "variation, dépassement d'un seuil) et on mesure pour chacune sa "
                   "prévisibilité et son intérêt pratique.",
        "resultats": "Le prix et le retour exacts sont peu prévisibles ; les cibles de "
                     "DIRECTION à horizon long ressortent comme les plus prometteuses.",
        "conclusion": "Étape de cadrage : aide à choisir la cible et prépare le passage du "
                      "prix vers la direction.",
    },
    "test_ema_benchmark.py": {
        "sous_question": "Quelles sont les références simples à battre côté Euronext ?",
        "fait": "On établit le banc d'essai des prédicteurs simples sur le prix Euronext, "
                "équivalent de celui du CBOT.",
        "comment": "On applique les mêmes références (marche aléatoire, dérive, etc.) à la "
                   "série Euronext, avec le même protocole d'évaluation.",
        "resultats": "La marche aléatoire reste imbattable sur le prix Euronext.",
        "conclusion": "Outil : fixe la référence Euronext que tout modèle devra dépasser.",
    },
    "test_ema_cqr_v2.py": {
        "sous_question": "Si on ne peut pas prévoir le prix exact, peut-on au moins encadrer le "
                         "prix futur dans une fourchette fiable ?",
        "fait": "Plutôt qu'un prix unique, on cherche un intervalle de prix futur garanti à un "
                "certain niveau de confiance (régression quantile conforme, dite CQR).",
        "comment": "On calibre des bornes basse et haute sur le passé pour qu'elles contiennent "
                   "le vrai prix avec, par exemple, 90 % de probabilité, en walk-forward.",
        "resultats": "Les intervalles sont fiables (bonne couverture) mais larges, car le prix "
                     "est très incertain : c'est utile pour le risque, pas pour viser un prix "
                     "précis.",
        "conclusion": "Étape : on sait quantifier l'incertitude, mais on ne réduit pas "
                      "l'imprévisibilité du prix.",
    },
    "test_ema_direction_benchmark.py": {
        "sous_question": "Pour la DIRECTION (hausse ou baisse) du prix Euronext, quelle est la "
                         "référence simple à battre ?",
        "fait": "On établit la référence pour la prévision de la direction Euronext, et non du "
                "prix lui-même.",
        "comment": "On évalue des références directionnelles (taux de base, persistance du sens, "
                   "saison) en mesurant la précision de direction.",
        "resultats": "Prévoir la direction Euronext directement reste difficile : la référence "
                     "est proche du hasard, ce qui justifiera d'aller chercher des fondamentaux.",
        "conclusion": "Outil : fixe la barre pour les futurs signaux directionnels Euronext.",
    },
    "test_ema_direction_benchmarks_v2.py": {
        "sous_question": "La référence directionnelle Euronext tient-elle avec des prédicteurs "
                         "de comparaison plus complets ?",
        "fait": "On enrichit le benchmark directionnel Euronext avec des références "
                "supplémentaires, pour fiabiliser la barre à battre.",
        "comment": "On ajoute des baselines directionnelles et on réévalue avec le même "
                   "protocole.",
        "resultats": "Même conclusion : la direction Euronext n'est pas facilement prévisible "
                     "par des règles simples.",
        "conclusion": "Outil : consolide la référence directionnelle Euronext.",
    },
    "test_ema_price_cqr_study.py": {
        "sous_question": "Les fourchettes de prix Euronext sont-elles assez serrées pour aider "
                         "une décision ?",
        "fait": "On étudie en détail les intervalles de prix Euronext : leur largeur, leur "
                "fiabilité et leur utilité réelle pour décider.",
        "comment": "On mesure, à chaque horizon, la largeur des intervalles et la fréquence à "
                   "laquelle ils contiennent le vrai prix.",
        "resultats": "Les intervalles sont fiables mais larges, surtout à long horizon : ils "
                     "renseignent sur le risque plus que sur le niveau de prix.",
        "conclusion": "Étape : l'incertitude est mesurable mais grande ; le prix reste "
                      "imprévisible.",
    },
    "test_ema_roll_target_benchmark.py": {
        "sous_question": "La façon de définir la cible autour des changements de contrat (roll) "
                         "fausse-t-elle la mesure de prévisibilité Euronext ?",
        "fait": "On vérifie que la cible Euronext n'est pas contaminée par les sauts techniques "
                "des jours de roll, qui pourraient gonfler artificiellement la performance.",
        "comment": "On construit la cible sur la série ajustée (hors artefacts de roll) et on "
                   "compare au cas non corrigé.",
        "resultats": "Sans correction, les rolls gonflent certains retours ; sur la série "
                     "ajustée, la marche aléatoire reste la référence.",
        "conclusion": "Outil : garantit une cible Euronext propre pour des comparaisons justes.",
    },
    "test_ema_smart_baselines.py": {
        "sous_question": "Des références plus élaborées que la marche aléatoire arrivent-elles "
                         "enfin à la battre sur le prix Euronext ?",
        "fait": "On teste des prédicteurs de référence plus élaborés (combinaisons, moyennes "
                "adaptatives) pour voir s'ils dépassent la marche aléatoire.",
        "comment": "On construit ces prédicteurs et on les compare au tableau de référence avec "
                   "le même protocole.",
        "resultats": "Même ces références plus élaborées ne battent pas la marche aléatoire sur "
                     "le prix Euronext.",
        "conclusion": "Outil : renforce la conclusion que le prix Euronext n'est pas prévisible, "
                      "même avec des références plus astucieuses.",
    },
    "test_ema_target_lab_v5.py": {
        "sous_question": "Quelle cible Euronext choisir (prix, retour, direction, seuil) pour "
                         "maximiser l'utilité d'une prévision ?",
        "fait": "On ouvre un laboratoire de cibles côté Euronext, équivalent de celui du CBOT, "
                "pour choisir l'objectif de prédiction le plus pertinent.",
        "comment": "On compare la prévisibilité et l'utilité de plusieurs cibles Euronext avec "
                   "un protocole rigoureux.",
        "resultats": "Comme au CBOT, le prix exact est peu prévisible ; la direction à long "
                     "horizon et le risque sont les pistes utiles.",
        "conclusion": "Étape de cadrage : oriente vers la direction et le risque plutôt que le "
                      "prix.",
    },
    "test_ema_true_curve_benchmark.py": {
        "sous_question": "Avec une vraie courbe Euronext par échéance, pourrait-on mieux prévoir "
                         "que la marche aléatoire ?",
        "fait": "On voudrait utiliser la courbe complète des échéances Euronext (plusieurs "
                "contrats à la fois) comme prédicteur de référence.",
        "comment": "Cela nécessite l'historique de plusieurs contrats simultanés, qu'on tente "
                   "de reconstituer.",
        "resultats": "La courbe Euronext disponible est trop courte et peu profonde : le test "
                     "n'est pas réalisable sur le passé.",
        "conclusion": "Bloqué : il manque une vraie courbe historique par échéance.",
    },
    "test_ema_weekly_benchmark.py": {
        "sous_question": "À l'échelle hebdomadaire (et non quotidienne), le prix Euronext "
                         "devient-il plus prévisible ?",
        "fait": "On refait le banc d'essai en fréquence hebdomadaire, au cas où le bruit "
                "quotidien masquerait un signal plus lent.",
        "comment": "On agrège les prix en hebdomadaire et on compare les références avec le "
                   "même protocole.",
        "resultats": "Même en hebdomadaire, la marche aléatoire reste la référence : pas de "
                     "gain de prévisibilité.",
        "conclusion": "Outil : l'imprévisibilité du prix n'est pas un simple effet de la "
                      "fréquence quotidienne.",
    },
    "test_horizon_sweep.py": {
        "sous_question": "La prévisibilité du prix change-t-elle selon l'horizon (très court, "
                         "moyen, long) ?",
        "fait": "On balaie tous les horizons de prévision pour chercher une éventuelle fenêtre "
                "où le prix deviendrait prévisible.",
        "comment": "On évalue références et modèles sur une grille d'horizons, de quelques jours "
                   "à plusieurs mois.",
        "resultats": "À aucun horizon le prix exact n'est prévisible ; en revanche la DIRECTION "
                     "devient un peu plus exploitable à horizon long.",
        "conclusion": "Étape : confirme qu'il faut viser la direction à long horizon, pas le "
                      "prix.",
    },
    "test_model_zoo.py": {
        "sous_question": "Parmi un large éventail de modèles, y en a-t-il un qui bat enfin la "
                         "référence sur le prix ?",
        "fait": "On passe en revue un large ensemble de modèles (linéaires, arbres, etc.) pour "
                "vérifier si l'un d'eux dépasse la marche aléatoire sur le prix.",
        "comment": "On entraîne et compare plusieurs familles de modèles avec le même protocole "
                   "anti-fuite et la même mesure d'erreur.",
        "resultats": "Aucun modèle ne bat la marche aléatoire sur le prix ; les plus complexes "
                     "ont même tendance à sur-apprendre.",
        "conclusion": "Étape : confirme par la diversité des modèles que le prix n'est pas "
                      "prévisible, et plaide pour la parcimonie.",
    },
    "test_storage_benchmark_ema.py": {
        "sous_question": "La théorie économique du stockage (coût de portage) donne-t-elle une "
                         "meilleure prévision que la marche aléatoire ?",
        "fait": "On teste une référence fondée sur l'économie du stockage (la relation entre le "
                "prix et le coût de portage entre échéances).",
        "comment": "On construit une prévision basée sur ce coût de portage (carry) et on la "
                   "compare au tableau de référence.",
        "resultats": "La référence 'stockage' n'améliore pas la prévision du prix ; elle éclaire "
                     "surtout le basis, étudié plus loin.",
        "conclusion": "Outil : une référence économique de plus qui confirme l'imprévisibilité "
                      "du prix.",
    },
    "test_target_labs_v6.py": {
        "sous_question": "Quelle est la meilleure cible à prédire en consolidant tout ce qu'on a "
                         "appris (programme V6) ?",
        "fait": "On consolide les enseignements des phases précédentes en un laboratoire de "
                "cibles unifié, pour figer le bon objectif de prédiction.",
        "comment": "On compare les cibles candidates (direction H40/H90, seuils) avec un "
                   "protocole hors échantillon rigoureux.",
        "resultats": "Les cibles de direction à H40/H90 ressortent comme les plus exploitables ; "
                     "le prix reste hors d'atteinte.",
        "conclusion": "Étape : fige le choix de cible (direction à long horizon) pour la suite.",
    },
    "test_weekly_da.py": {
        "sous_question": "En mesurant la justesse de direction semaine par semaine, voit-on un "
                         "signal stable ?",
        "fait": "On suit la justesse de direction (la part de fois où l'on prédit le bon sens) "
                "semaine après semaine, pour repérer un éventuel signal régulier.",
        "comment": "On calcule cette justesse par semaine et on observe sa stabilité dans le "
                   "temps.",
        "resultats": "La justesse de direction est instable et proche du hasard à partir du "
                     "prix seul ; un signal stable n'apparaîtra qu'avec des fondamentaux.",
        "conclusion": "Étape : un signal directionnel existe peut-être, mais pas à partir du "
                      "prix seul.",
    },
    # ---- Q2 : direction et prime Euronext via le basis ------------------------
    "test_ema_cbot_cointegration.py": {
        "sous_question": "Le prix Euronext et le prix CBOT sont-ils liés par un équilibre de "
                         "long terme, ou évoluent-ils indépendamment ?",
        "fait": "On vérifie si Euronext et CBOT sont 'cointégrés', c'est-à-dire reliés par un "
                "équilibre durable autour duquel leur écart oscille (au lieu de partir chacun "
                "de leur côté).",
        "comment": "On applique le test de cointégration de Johansen aux deux séries de prix et "
                   "on estime la relation d'équilibre de long terme.",
        "resultats": "CBOT et Euronext sont bien cointégrés : leur écart (le basis) revient vers "
                     "un équilibre. C'est ce qui rend le basis intéressant à étudier.",
        "conclusion": "Étape clé : justifie d'étudier le basis (l'écart) plutôt que chaque prix "
                      "séparément.",
    },
    "test_ema_cbot_relationship.py": {
        "sous_question": "De quelle façon le prix Euronext suit-il le prix CBOT au quotidien ?",
        "fait": "On caractérise la relation entre Euronext et CBOT (qui mène l'autre, avec quel "
                "décalage, quelle force) pour comprendre la mécanique du couple.",
        "comment": "On mesure les corrélations, les décalages temporels et l'ampleur de la "
                   "transmission des mouvements CBOT vers Euronext.",
        "resultats": "Le CBOT mène très largement : l'essentiel des mouvements Euronext vient du "
                     "CBOT, la part proprement européenne est secondaire.",
        "conclusion": "Étape : confirme que le CBOT donne la tendance et que l'Euronext ajoute "
                      "surtout une prime locale.",
    },
    "test_ema_cbot_relation_v2.py": {
        "sous_question": "La relation CBOT->Euronext est-elle stable dans le temps ou "
                         "change-t-elle selon les périodes ?",
        "fait": "On reprend l'analyse de la relation CBOT/Euronext dans une version actualisée "
                "pour vérifier sa stabilité.",
        "comment": "On réestime la relation sur différentes sous-périodes et on observe si la "
                   "force du lien varie.",
        "resultats": "La domination du CBOT est confirmée et reste globalement stable ; les "
                     "écarts ponctuels correspondent à des tensions locales (la prime).",
        "conclusion": "Étape : consolide la mécanique CBOT (tendance) + prime locale.",
    },
    "test_cbot_cross_market_v6.py": {
        "sous_question": "D'autres marchés (blé, soja, marchés liés) aident-ils à prévoir le "
                         "CBOT maïs ?",
        "fait": "On teste si des marchés voisins (céréales et oléagineux liés) apportent une "
                "information utile pour la direction du maïs CBOT.",
        "comment": "On ajoute des variables issues de ces marchés croisés à un modèle "
                   "directionnel et on regarde si elles améliorent la prévision, hors "
                   "échantillon.",
        "resultats": "Les marchés croisés n'apportent pas de gain robuste hors échantillon pour "
                     "le maïs CBOT.",
        "conclusion": "Étape : les marchés liés sont un contexte, pas un prédicteur fiable du "
                      "maïs.",
    },
    "test_cross_target_oof_v6.py": {
        "sous_question": "Prédire plusieurs cibles à la fois (différents horizons/définitions) "
                         "renforce-t-il le signal ?",
        "fait": "On teste l'idée d'apprendre plusieurs cibles conjointement et de combiner leurs "
                "prédictions hors échantillon, pour voir si cela stabilise le signal.",
        "comment": "On génère des prédictions hors échantillon (OOF) sur plusieurs cibles et on "
                   "les croise, en évitant toute fuite.",
        "resultats": "La combinaison de cibles n'apporte pas de gain net clair ; elle ajoute "
                     "surtout de la complexité.",
        "conclusion": "Étape : confirme que la parcimonie vaut mieux que l'empilement de cibles.",
    },
    "test_ema_cross_data_interactions_v5.py": {
        "sous_question": "Les interactions entre sources de données (prix, courbe, fondamentaux) "
                         "révèlent-elles un signal caché côté Euronext ?",
        "fait": "On explore les interactions croisées entre plusieurs jeux de données Euronext "
                "pour détecter un effet combiné qui n'apparaîtrait pas variable par variable.",
        "comment": "On teste des croisements de variables et on mesure leur apport hors "
                   "échantillon.",
        "resultats": "Les interactions ne révèlent pas de signal robuste supplémentaire.",
        "conclusion": "Étape : pas de gain caché dans les interactions ; on reste sur les "
                      "signaux simples.",
    },
    "test_ema_decomposition.py": {
        "sous_question": "Peut-on séparer le mouvement du prix Euronext en une part venue du "
                         "CBOT et une part proprement européenne ?",
        "fait": "On décompose dynamiquement le prix Euronext en deux composantes : ce qui vient "
                "du CBOT (et du change) et ce qui est spécifique à l'Europe (la prime locale).",
        "comment": "On modélise la part expliquée par le CBOT converti et on isole le résidu "
                   "européen.",
        "resultats": "La part CBOT domine ; la composante proprement européenne est faible mais "
                     "réelle, et c'est elle qui porte l'intérêt de l'étude Euronext.",
        "conclusion": "Étape clé : recentre l'étude Euronext sur la composante locale (le basis "
                      "et la prime).",
    },
    "test_ema_decomposition_v2.py": {
        "sous_question": "La décomposition prix Euronext = part CBOT + prime locale tient-elle "
                         "avec une méthode plus fine ?",
        "fait": "On reprend la décomposition du prix Euronext dans une version améliorée pour "
                "fiabiliser la séparation des deux composantes.",
        "comment": "On affine l'estimation de la part CBOT et du résidu local, et on vérifie la "
                   "stabilité du découpage.",
        "resultats": "La conclusion tient : le CBOT explique l'essentiel, la prime locale est "
                     "secondaire mais c'est l'objet utile.",
        "conclusion": "Étape : consolide la décomposition qui guide toute la suite.",
    },
    "test_ema_return_decomposition.py": {
        "sous_question": "Au niveau des RETOURS (variations), combien vient du CBOT et combien "
                         "de la prime européenne ?",
        "fait": "On décompose le retour (la variation) Euronext en contribution CBOT et "
                "contribution locale, pour quantifier le poids de chacune.",
        "comment": "On attribue chaque variation Euronext à la part CBOT (convertie) et au "
                   "résidu européen, sur l'historique.",
        "resultats": "Le retour Euronext est surtout du CBOT converti ; la prime locale ne pèse "
                     "qu'une petite part des variations.",
        "conclusion": "Étape : chiffre le poids de la prime locale, faible mais c'est elle qui "
                      "distingue l'Europe.",
    },
    "test_ema_residual_study.py": {
        "sous_question": "La part proprement européenne (le résidu, une fois le CBOT retiré) "
                         "est-elle prévisible ?",
        "fait": "On étudie le résidu européen (ce qui reste du prix Euronext quand on a enlevé "
                "l'effet CBOT) pour voir s'il contient un signal exploitable.",
        "comment": "On isole le résidu et on teste s'il est prévisible par des variables "
                   "disponibles, hors échantillon.",
        "resultats": "Le résidu européen pur est faible et difficile à prévoir directement : il "
                     "n'y a pas de signal simple dedans.",
        "conclusion": "Étape : le résidu seul ne donne pas de signal ; l'intérêt est dans le "
                      "basis et sa dynamique.",
    },
    "test_ema_residual_eu_v2.py": {
        "sous_question": "Avec des fondamentaux européens, le résidu européen devient-il "
                         "prévisible ?",
        "fait": "On reprend l'étude du résidu européen en y ajoutant des fondamentaux propres à "
                "l'Europe, pour voir s'ils l'expliquent.",
        "comment": "On teste l'apport de variables fondamentales européennes à la prévision du "
                   "résidu, hors échantillon.",
        "resultats": "Les fondamentaux disponibles n'expliquent pas mieux le résidu : la prime "
                     "reste largement locale et peu modélisable.",
        "conclusion": "Étape : confirme que la prime européenne est locale et difficile à "
                      "expliquer avec les données actuelles.",
    },
    "test_ema_hierarchical_cbot_premium_v5.py": {
        "sous_question": "Peut-on décrire la prime Euronext comme un empilement (CBOT, puis "
                         "prime) et savoir laquelle agit ?",
        "fait": "On modélise la prime Euronext de façon hiérarchique : d'abord la grande "
                "tendance CBOT, puis la prime locale par-dessus, pour attribuer clairement "
                "chaque effet.",
        "comment": "On emboîte les niveaux (CBOT puis prime) et on mesure l'apport de chaque "
                   "niveau, du général au spécifique.",
        "resultats": "La lecture hiérarchique fonctionne : la tendance CBOT domine, et la prime "
                     "locale ajoute un effet identifiable et utile.",
        "conclusion": "Résultat gardé : fournit une description claire et exploitable de la "
                      "structure de la prime.",
    },
    "test_ema_premium_indicator.py": {
        "sous_question": "Peut-on construire un indicateur de la prime Euronext qui signale "
                         "quand elle est anormalement haute ou basse ?",
        "fait": "On construit un indicateur de prime (basis) qui repère quand l'écart "
                "Euronext/CBOT s'écarte de sa norme, point de départ d'un signal de vente.",
        "comment": "On normalise le basis (z-score sur le passé) et on en fait un indicateur "
                   "lisible signalant les extrêmes.",
        "resultats": "L'indicateur capture bien les moments de prime élevée, qui correspondent "
                     "souvent à de bons moments pour vendre par la suite.",
        "conclusion": "Résultat gardé : brique centrale de l'indicateur de vente lié au basis.",
    },
    "test_ema_premium_indicator_v2.py": {
        "sous_question": "L'indicateur de prime tient-il dans une version améliorée et plus "
                         "robuste ?",
        "fait": "On améliore l'indicateur de prime (calibration, robustesse) pour le rendre plus "
                "fiable en usage.",
        "comment": "On affine la normalisation et les seuils, et on vérifie la stabilité du "
                   "comportement.",
        "resultats": "La version améliorée conserve la qualité du signal tout en étant plus "
                     "robuste aux variations de données.",
        "conclusion": "Résultat gardé : version consolidée de l'indicateur de prime.",
    },
    "test_ema_premium_signal_compare.py": {
        "sous_question": "Parmi plusieurs façons de mesurer la prime, laquelle donne le signal "
                         "le plus fiable ?",
        "fait": "On compare différentes définitions du signal de prime pour retenir la plus "
                "robuste.",
        "comment": "On évalue plusieurs variantes (normalisation, fenêtre, seuils) sur le même "
                   "protocole et on compare leur qualité.",
        "resultats": "Une définition simple et robuste du basis normalisé ressort comme la "
                     "meilleure ; les variantes complexes n'ajoutent rien.",
        "conclusion": "Étape : fixe la meilleure définition du signal de prime (parcimonie).",
    },
    "test_premium_head.py": {
        "sous_question": "Dispose-t-on d'une source unique et fiable pour l'état courant de la "
                         "prime (le 'head') ?",
        "fait": "On met en place une source unique de vérité pour l'état le plus récent de la "
                "prime, afin que tous les outils lisent exactement la même valeur.",
        "comment": "On centralise le calcul de l'état courant de la prime et on le teste pour "
                   "éviter toute divergence entre modules.",
        "resultats": "L'état de la prime est cohérent partout, ce qui fiabilise le suivi et les "
                     "tableaux de bord.",
        "conclusion": "Outil : garantit une vue unique et cohérente de la prime.",
    },
    "test_ema_relative_study.py": {
        "sous_question": "Vendre l'Euronext RELATIVEMENT au CBOT (parier sur la prime) est-il "
                         "plus prévisible que prévoir chaque prix ?",
        "fait": "On étudie l'Euronext relativement au CBOT (c'est-à-dire la prime) pour voir si "
                "ce 'relatif' est plus exploitable que les prix pris isolément.",
        "comment": "On construit la série relative (prime) et on teste sa prévisibilité et son "
                   "intérêt comme signal.",
        "resultats": "Le relatif (la prime) est plus structuré que les prix bruts : c'est là "
                     "que se trouve l'information exploitable, pas dans le niveau de prix.",
        "conclusion": "Étape clé : recentre la stratégie sur la prime relative plutôt que sur "
                      "le prix.",
    },
    "test_ema_relative_backtest.py": {
        "sous_question": "Une stratégie qui vend la prime quand elle est haute aurait-elle été "
                         "rentable ?",
        "fait": "On teste, sur l'historique, une stratégie qui prend position sur la prime "
                "(vendre quand elle est élevée) pour mesurer si elle aurait gagné.",
        "comment": "On simule la stratégie avec des coûts réalistes et on mesure le gain, en "
                   "walk-forward.",
        "resultats": "Vendre la prime haute est rentable hors crise une fois les coûts pris en "
                     "compte, mais l'avantage est modeste et asymétrique.",
        "conclusion": "Étape : montre un edge réel mais modeste sur la prime, à confirmer.",
    },
    "test_ema_relative_backtest_v2.py": {
        "sous_question": "Cette stratégie sur la prime tient-elle avec des règles de sortie et "
                         "des coûts plus réalistes ?",
        "fait": "On améliore le backtest de la stratégie de prime (règles d'entrée/sortie, "
                "coûts) pour le rendre plus réaliste.",
        "comment": "On ajoute des sorties au retour à la moyenne et des coûts, et on réévalue.",
        "resultats": "Les sorties au retour vers la norme améliorent le résultat ; l'edge "
                     "subsiste mais reste sensible aux périodes de crise.",
        "conclusion": "Étape : affine la stratégie de prime et confirme sa fragilité en crise.",
    },
    "test_ema_relative_backtest_v3.py": {
        "sous_question": "La stratégie de prime résiste-t-elle à des coûts élevés et hors "
                         "périodes de crise ?",
        "fait": "On pousse le backtest de la prime à des coûts plus élevés et on isole les "
                "périodes hors crise pour tester sa robustesse.",
        "comment": "On fait varier les coûts et on sépare les régimes (normal vs crise).",
        "resultats": "Hors crise, la stratégie survit même à des coûts de l'ordre de 5 euros/t ; "
                     "en crise, elle peut subir de grosses pertes.",
        "conclusion": "Étape : l'edge de la prime est robuste hors crise mais vulnérable aux "
                      "chocs.",
    },
    "test_ema_relative_error_analysis.py": {
        "sous_question": "Quand la stratégie de prime se trompe, pourquoi se trompe-t-elle ?",
        "fait": "On analyse les erreurs de la stratégie de prime pour comprendre dans quels cas "
                "elle perd.",
        "comment": "On classe les pertes par contexte (niveau d'entrée, régime de marché, "
                   "saison) pour identifier les situations à risque.",
        "resultats": "Les grosses pertes arrivent surtout quand le CBOT monte fortement (la "
                     "prime se compresse par le haut) : un risque identifiable a priori.",
        "conclusion": "Étape : éclaire les conditions de perte, ce qui mènera au score de risque "
                      "ADVERSE.",
    },
    "test_ema_relative_error_archaeology_v2.py": {
        "sous_question": "En creusant l'historique des erreurs, peut-on remonter à la cause "
                         "profonde des pires pertes ?",
        "fait": "On mène une 'archéologie' des erreurs : on remonte le fil des pires épisodes de "
                "perte pour en comprendre l'origine commune.",
        "comment": "On reconstitue le déroulé des épisodes perdants et on cherche le facteur "
                   "déclencheur récurrent.",
        "resultats": "Les pires pertes partagent un schéma : une prime déjà basse à l'entrée "
                     "suivie d'une hausse du CBOT, ce qui devient un signal de prudence.",
        "conclusion": "Étape : isole le facteur de risque clé, réutilisé pour anticiper les cas "
                      "défavorables.",
    },
    "test_ema_relative_seasonality.py": {
        "sous_question": "La prime Euronext suit-elle un cycle saisonnier exploitable ?",
        "fait": "On cherche un motif saisonnier dans la prime (par exemple plus haute ou plus "
                "basse à certaines périodes de campagne).",
        "comment": "On moyenne la prime par période de l'année et on teste si le motif est "
                   "stable et exploitable.",
        "resultats": "Il existe une saisonnalité de la prime, utile comme contexte, mais "
                     "insuffisante seule pour un signal fiable.",
        "conclusion": "Étape : la saison aide à doser le signal de prime, sans le remplacer.",
    },
    "test_ema_seasonal_premium_regimes.py": {
        "sous_question": "La prime se comporte-t-elle différemment selon les régimes "
                         "saisonniers (récolte, soudure) ?",
        "fait": "On découpe l'année en régimes saisonniers pour voir si la prime et son signal "
                "changent de comportement selon la période.",
        "comment": "On compare le comportement de la prime entre régimes (par exemple avant "
                   "récolte vs après) et on évalue le signal dans chacun.",
        "resultats": "Le signal de prime est plus net dans certains régimes saisonniers que "
                     "dans d'autres, ce qui suggère de le conditionner à la saison.",
        "conclusion": "Étape : confirme l'intérêt de conditionner le signal de prime par la "
                      "saison.",
    },
    "test_v21_integration.py": {
        "sous_question": "Que se passe-t-il concrètement quand la prime se compresse : par quel "
                         "côté (CBOT ou Euronext) ?",
        "fait": "On intègre les briques précédentes pour expliquer le mécanisme de compression "
                "de la prime et savoir si elle se résorbe par le haut (CBOT) ou par le bas.",
        "comment": "On décompose les épisodes de compression et on mesure la part due à une "
                   "hausse du CBOT par rapport à une baisse de l'Euronext.",
        "resultats": "La prime se compresse surtout par une HAUSSE du CBOT (environ 69 % des "
                     "cas) : 'vendre la prime' revient en pratique à 'parier sur une hausse "
                     "relative du CBOT'.",
        "conclusion": "Résultat important : clarifie la nature économique du signal de prime.",
    },
    "test_v29_premium_risk_path.py": {
        "sous_question": "La prime et le risque de baisse (drawdown) sont-ils liés, et comment "
                         "la prime évolue-t-elle quand ça tourne mal ?",
        "fait": "On explore le lien entre la prime et le risque de baisse, et la trajectoire de "
                "la prime dans les épisodes défavorables.",
        "comment": "On croise l'indicateur de prime avec des mesures de drawdown et on observe "
                   "les trajectoires.",
        "resultats": "Une prime élevée va souvent de pair avec un risque de compression "
                     "défavorable ; la perte vient du chemin (trajectoire adverse), pas du "
                     "niveau seul.",
        "conclusion": "Étape : relie prime et risque, préparant la gestion du risque ADVERSE.",
    },
    "test_v49_long_premium_leg.py": {
        "sous_question": "La jambe inverse (parier sur une HAUSSE de la prime) est-elle aussi "
                         "exploitable que la vente de prime ?",
        "fait": "On teste la position symétrique (acheter la prime quand elle est basse) pour "
                "voir si elle est aussi intéressante que la vente.",
        "comment": "On simule cette jambe longue et on compare son résultat à la jambe courte.",
        "resultats": "La jambe longue est nettement moins favorable : l'edge est asymétrique, "
                     "concentré du côté de la vente de prime haute.",
        "conclusion": "Étape : confirme l'asymétrie, on se concentre sur la vente de prime.",
    },
    "test_ema_final_report.py": {
        "sous_question": "Quel bilan tire-t-on de l'étude Euronext à ce stade ?",
        "fait": "On rédige un rapport de synthèse qui rassemble les résultats de l'étude "
                "Euronext (relation CBOT, prime, signal) en un état des lieux clair.",
        "comment": "On consolide les chiffres et conclusions des analyses précédentes en un "
                   "document de référence.",
        "resultats": "Le bilan confirme : CBOT donne la tendance, la prime locale porte un "
                     "signal modeste, le prix Euronext n'est pas prévisible directement.",
        "conclusion": "Étape de synthèse : fixe l'état des connaissances Euronext à ce stade.",
    },
    "test_ema_final_report_v2.py": {
        "sous_question": "Le bilan Euronext tient-il après corrections et nouvelles analyses ?",
        "fait": "On met à jour le rapport de synthèse Euronext avec les corrections et résultats "
                "supplémentaires.",
        "comment": "On réintègre les analyses revues et on actualise les conclusions.",
        "resultats": "Les conclusions principales tiennent : la prime est l'objet utile, modeste "
                     "mais réel.",
        "conclusion": "Étape de synthèse : version actualisée du bilan Euronext.",
    },
    "test_ema_final_report_v3.py": {
        "sous_question": "Le bilan Euronext reste-t-il cohérent à mesure que l'étude avance ?",
        "fait": "On poursuit l'actualisation du rapport de synthèse Euronext (troisième "
                "version).",
        "comment": "On consolide les nouveaux éléments et on vérifie la cohérence d'ensemble.",
        "resultats": "Le récit reste stable : tendance CBOT, prime locale modeste, prix non "
                     "prévisible.",
        "conclusion": "Étape de synthèse : continuité du bilan Euronext.",
    },
    "test_ema_final_report_v4.py": {
        "sous_question": "Le bilan Euronext est-il prêt pour une synthèse finale ?",
        "fait": "On finalise le rapport de synthèse Euronext (quatrième version) avant la "
                "synthèse générale.",
        "comment": "On nettoie et on harmonise les conclusions pour préparer la version finale.",
        "resultats": "Le bilan est mûr et cohérent ; il peut servir de base à la synthèse "
                     "finale.",
        "conclusion": "Étape de synthèse : bilan Euronext quasi définitif.",
    },
    "test_ema_final_synthesis_v5.py": {
        "sous_question": "Quelle est la synthèse finale de l'étude Euronext ?",
        "fait": "On rédige la synthèse finale de tout le volet Euronext, qui résume ce que l'on "
                "sait et ce que l'on ne sait pas.",
        "comment": "On rassemble l'ensemble des résultats Euronext en un message clair et "
                   "honnête.",
        "resultats": "Synthèse : le prix Euronext n'est pas prévisible directement ; l'objet "
                     "utile est la prime, modeste mais réelle, à exploiter avec prudence.",
        "conclusion": "Étape de synthèse : clôt proprement le volet Euronext.",
    },
    "test_ema_project_overview.py": {
        "sous_question": "Quelle est la vue d'ensemble du projet Euronext (objectif, méthode, "
                         "périmètre) ?",
        "fait": "On documente la vue d'ensemble du projet Euronext : sa question, sa méthode et "
                "son périmètre, pour cadrer le travail.",
        "comment": "On décrit l'objectif (expliquer la prime et la transmission CBOT->EMA) et "
                   "les étapes prévues.",
        "resultats": "Le cadrage est posé : on cherche à expliquer le basis et le résidu "
                     "européen, pas à prévoir le prix Euronext.",
        "conclusion": "Étape de cadrage : fixe l'objectif et le périmètre du volet Euronext.",
    },
    "test_final_corn_study_v6.py": {
        "sous_question": "En rassemblant tout le programme (V6), quelle image globale de l'étude "
                         "du maïs obtient-on ?",
        "fait": "On consolide l'ensemble du programme dans une étude finale du maïs (phase V6), "
                "côté CBOT et Euronext.",
        "comment": "On réunit les résultats clés (benchmarks, cibles, prime, risque) en une vue "
                   "unifiée et reproductible.",
        "resultats": "L'image globale confirme la ligne directrice : prix non prévisible, "
                     "direction long horizon et risque exploitables modestement.",
        "conclusion": "Étape de synthèse : vue consolidée de l'étude au stade V6.",
    },
    "test_phase2_descriptive.py": {
        "sous_question": "Que disent les faits descriptifs (économiques) sur le maïs avant toute "
                         "modélisation ?",
        "fait": "On établit les faits descriptifs et économiques de base (saisonnalité, "
                "relations, ordres de grandeur) avant de chercher à modéliser.",
        "comment": "On produit des statistiques descriptives et des relations économiques "
                   "simples, documentées.",
        "resultats": "Les faits descriptifs cadrent le problème (rôle du CBOT, saisonnalité, "
                     "prime locale) et orientent les hypothèses à tester.",
        "conclusion": "Étape de cadrage : pose les faits économiques sur lesquels s'appuie la "
                      "suite.",
    },
    # ---- Q3 : le basis revient-il à la moyenne -> signal de vente -------------
    "test_ema_basis_formal.py": {
        "sous_question": "Comment définir proprement et de façon reproductible le basis "
                         "(l'écart Euronext/CBOT) ?",
        "fait": "On formalise la définition du basis : l'écart entre l'Euronext converti en "
                "dollars et le CBOT, calculé de la même manière partout.",
        "comment": "On pose la formule (conversion par le change, alignement des contrats) et "
                   "on la vérifie par des tests.",
        "resultats": "On obtient une définition propre et stable du basis, qui sert de base à "
                     "tous les signaux suivants.",
        "conclusion": "Étape : fixe la définition de référence du basis.",
    },
    "test_ema_basis_study.py": {
        "sous_question": "Quel est le comportement statistique du basis (niveaux habituels, "
                         "extrêmes) ?",
        "fait": "On étudie les propriétés du basis : ses niveaux typiques, sa distribution et la "
                "fréquence de ses extrêmes.",
        "comment": "On calcule les statistiques descriptives du basis et on identifie les seuils "
                   "d'extrême.",
        "resultats": "Le basis a des extrêmes identifiables, qui correspondent justement aux "
                     "moments intéressants pour vendre.",
        "conclusion": "Étape : caractérise le basis et ses seuils utiles.",
    },
    "test_ema_basis_v2.py": {
        "sous_question": "L'étude du basis tient-elle après mise à jour des données et de la "
                         "méthode ?",
        "fait": "On reprend l'étude du basis dans une version actualisée pour confirmer ses "
                "propriétés.",
        "comment": "On recalcule le basis sur des données mises à jour et on vérifie la "
                   "stabilité de sa distribution et de ses extrêmes.",
        "resultats": "Les propriétés du basis se confirment ; la définition reste valide.",
        "conclusion": "Étape : consolide le basis comme objet central de l'étude.",
    },
    "test_basis_regimes.py": {
        "sous_question": "Le basis se comporte-t-il différemment selon les régimes (extrême, "
                         "normal) ?",
        "fait": "On découpe le basis en régimes pour voir dans quels états du marché le signal "
                "de vente fonctionne le mieux.",
        "comment": "On définit des régimes de basis (niveau, volatilité) et on mesure le "
                   "comportement du signal dans chacun.",
        "resultats": "Le signal est net dans les régimes de basis extrême et faible en régime "
                     "normal.",
        "conclusion": "Étape : conforte l'idée de ne déclencher que sur les extrêmes du basis.",
    },
    "test_ema_storage_economic_study.py": {
        "sous_question": "La théorie économique du stockage explique-t-elle le niveau et la "
                         "réversion du basis ?",
        "fait": "On confronte le basis à la théorie du stockage (coût de portage, rendement de "
                "convenance) pour voir si elle l'explique.",
        "comment": "On compare le basis observé aux prédictions de la théorie du stockage.",
        "resultats": "La théorie éclaire la logique générale (le carry) mais n'explique pas "
                     "finement le basis local, qui garde une part spécifique.",
        "conclusion": "Étape : cadre théorique utile, mais le basis reste en partie local et "
                      "empirique.",
    },
    "test_ema_theoretical_backtests.py": {
        "sous_question": "Des stratégies fondées sur la théorie (convergence, carry) "
                         "auraient-elles été rentables ?",
        "fait": "On teste des stratégies inspirées de la théorie économique (convergence à "
                "l'échéance, portage) sur l'historique.",
        "comment": "On simule ces stratégies théoriques et on mesure leur résultat net.",
        "resultats": "Les stratégies théoriques offrent un cadre mais des résultats modestes ; "
                     "le signal pratique vient surtout du basis normalisé.",
        "conclusion": "Étape : la théorie inspire, mais le signal exploitable reste empirique.",
    },
    "test_storage_backtest.py": {
        "sous_question": "Une stratégie de portage (carry) entre échéances aurait-elle aidé ?",
        "fait": "On backteste une stratégie de portage entre échéances pour mesurer son apport.",
        "comment": "On simule des positions liées au carry et on mesure le résultat net.",
        "resultats": "Le carry seul n'apporte pas de gain robuste ; il sert surtout à comprendre "
                     "la structure des prix entre échéances.",
        "conclusion": "Étape : le carry est un éclairage, pas un signal de vente fiable.",
    },
    "test_v9_structural_indicator.py": {
        "sous_question": "Peut-on assembler un premier indicateur qui repère les bons moments de "
                         "vente à partir du basis et de la saison ?",
        "fait": "On assemble un premier indicateur structurel qui combine le niveau du basis et "
                "la saisonnalité pour signaler les moments favorables à la vente.",
        "comment": "On construit un score à partir de quelques variables robustes (basis "
                   "normalisé, saison) et on l'évalue en walk-forward sur la justesse de "
                   "direction.",
        "resultats": "L'indicateur atteint une AUC de 0.656 : un signal réel mais modeste. Au "
                     "passage, une hypothèse antérieure d'inversion saisonnière (V8) est "
                     "invalidée.",
        "conclusion": "Résultat gardé : premier indicateur structurel viable, base des versions "
                      "suivantes.",
    },
    "test_v10_market_discovery.py": {
        "sous_question": "À quelle vitesse le basis revient-il à la moyenne, et quel modèle "
                         "simple capte le mieux ce retour ?",
        "fait": "On explore en profondeur la dynamique du basis : sa vitesse de retour à la "
                "moyenne et le modèle le plus simple qui la capture.",
        "comment": "On estime la demi-vie de réversion et on compare des modèles parcimonieux "
                   "(1 à 2 variables) sur la prévision de direction.",
        "resultats": "La demi-vie du basis est d'environ 17 jours ; un modèle à 2 variables "
                     "(basis normalisé + saison) atteint une AUC de 0.694. Le mur des coûts est "
                     "confirmé et l'edge est plus net en tendance haussière du CBOT.",
        "conclusion": "Étape clé : fixe le modèle à 2 variables et la demi-vie du basis comme "
                      "socle.",
    },
    "test_v11_simplified_program.py": {
        "sous_question": "Quel programme discipliné (modèle, règles, coûts) ne garder que pour "
                         "ce qui tient hors échantillon ?",
        "fait": "On discipline l'approche : on choisit le modèle par défaut, on impose des "
                "coûts réalistes et on rejette ce qui ne tient pas en validation vers l'avant.",
        "comment": "On compare les variantes et on ne conserve que le modèle à 2 variables et "
                   "les règles robustes, validés en forward.",
        "resultats": "Le modèle à 2 variables est promu par défaut ; le filtre de régime est "
                     "rejeté en forward ; le short 'basis haut' reste robuste après coûts.",
        "conclusion": "Étape : fixe un programme sobre et honnête (parcimonie, coûts, "
                      "validation forward).",
    },
    "test_v12_mean_reversion_lab.py": {
        "sous_question": "Quelle règle de sortie tire le mieux parti du retour du basis à la "
                         "moyenne ?",
        "fait": "On compare des règles de sortie pour une position prise sur un basis extrême : "
                "sortir à un horizon fixe, ou sortir quand le basis est revenu vers sa norme.",
        "comment": "On teste 'sortir au niveau' (retour vers la moyenne) contre un horizon fixe "
                   "(par ex. 40 jours), avec validation forward et abstention si l'incertitude "
                   "est forte.",
        "resultats": "Sortir au retour vers la norme bat l'horizon fixe (réversion vers ~54 "
                     "jours) ; le short 'basis haut' généralise hors échantillon ; l'abstention "
                     "atteint une justesse de 0.78.",
        "conclusion": "Résultat gardé : la sortie au niveau et l'abstention deviennent des "
                      "règles clés.",
    },
    "test_v13_basis_reversion.py": {
        "sous_question": "Vendre quand le basis est haut survit-il aux coûts réels, et quelle "
                         "sortie est la meilleure ?",
        "fait": "On teste l'indicateur de réversion du basis en conditions réalistes : coûts de "
                "transaction et différentes règles de sortie.",
        "comment": "On simule la stratégie 'short basis haut' avec des coûts et plusieurs "
                   "sorties (au niveau, à z=0, à z=0.5), en séparant les périodes de crise.",
        "resultats": "Hors crise, la stratégie survit à un coût de 5 euros/t (+115) ; les "
                     "sorties z0/z0.5 battent l'horizon fixe ; l'edge est fortement asymétrique "
                     "(vente bien plus que achat).",
        "conclusion": "Résultat gardé : confirme un edge robuste hors crise et les bonnes règles "
                      "de sortie.",
    },
    "test_v14_short_indicator.py": {
        "sous_question": "Peut-on assembler un indicateur 'vente seulement' fiable, sans qu'il "
                         "se déclenche trop rarement ?",
        "fait": "On assemble un indicateur orienté vente uniquement (short basis haut) et on "
                "vérifie sa robustesse et sa fréquence de déclenchement.",
        "comment": "On construit l'indicateur, on mesure la demi-vie de réversion et on teste sa "
                   "robustesse sur le proxy ; on surveille s'il s'abstient trop.",
        "resultats": "L'indicateur est robuste (réversion médiane ~47 jours) mais a tendance à "
                     "trop filtrer (très peu de signaux en mode strict).",
        "conclusion": "Résultat gardé : indicateur de vente solide, à calibrer pour ne pas trop "
                      "s'abstenir.",
    },
    "test_v15_short_realism.py": {
        "sous_question": "En conditions vraiment réalistes (stop, taille, coûts), l'indicateur "
                         "de vente reste-t-il rentable ?",
        "fait": "On pousse le réalisme de l'indicateur de vente : ajout d'un stop, "
                "dimensionnement et coûts, pour voir s'il tient en pratique.",
        "comment": "On ajoute un stop (-20), on étudie où l'edge se concentre et on construit un "
                   "portefeuille avec coûts.",
        "resultats": "L'edge est concentré sur les signaux forts (z>2) ; le portefeuille strict "
                     "gagne +116 (coût 5) avec une justesse de 0.90 ; les variantes saison-aware "
                     "et ventes partielles sont rejetées.",
        "conclusion": "Résultat gardé : l'indicateur reste rentable en conditions réalistes, "
                      "surtout sur les signaux forts.",
    },
    "test_v17_research_indicator.py": {
        "sous_question": "Un indicateur à paliers (plusieurs niveaux de signal) améliore-t-il la "
                         "décision de vente ?",
        "fait": "On construit un indicateur de recherche à paliers, qui gradue le signal de "
                "vente selon la force du basis.",
        "comment": "On définit des paliers de signal et on évalue en walk-forward, avec des "
                   "règles de sortie.",
        "resultats": "L'indicateur à paliers obtient une justesse de 0.66 pour un gain net de "
                     "+138 ; la sortie à z=0.5 évite des pertes.",
        "conclusion": "Résultat gardé : la gradation par paliers et la sortie z0.5 améliorent le "
                      "résultat.",
    },
    "test_ema_abstention_filters.py": {
        "sous_question": "Quand vaut-il mieux NE PAS émettre de signal pour éviter de se "
                         "tromper ?",
        "fait": "On met en place des filtres d'abstention : l'indicateur se tait quand "
                "l'incertitude est trop forte, plutôt que de risquer un mauvais signal.",
        "comment": "On définit des conditions d'abstention (faible écart, données incertaines) "
                   "et on mesure l'effet sur la justesse.",
        "resultats": "S'abstenir dans les cas douteux augmente la justesse des signaux émis, au "
                     "prix d'une fréquence plus faible.",
        "conclusion": "Étape : l'abstention améliore la fiabilité, à condition de ne pas trop "
                      "filtrer.",
    },
    "test_v167_seasonality.py": {
        "sous_question": "Les départs de compression de la prime suivent-ils un calendrier "
                         "saisonnier ?",
        "fait": "On étudie si les moments où la prime commence à se compresser suivent un motif "
                "saisonnier.",
        "comment": "On date les départs de compression et on regarde leur répartition dans "
                   "l'année.",
        "resultats": "Il existe une saisonnalité des départs de compression, utile comme "
                     "contexte pour le timing de vente.",
        "conclusion": "Étape : la saison aide à anticiper les fenêtres de compression.",
    },
    "test_v175_signal_tiers.py": {
        "sous_question": "Faut-il distinguer des paliers de force de signal, et combien chaque "
                         "palier rapporte-t-il ?",
        "fait": "On classe les signaux en paliers (forts, faibles) pour voir si la performance "
                "se concentre sur les forts.",
        "comment": "On répartit les signaux par force et on mesure la performance de chaque "
                   "palier.",
        "resultats": "La performance se concentre sur les signaux forts (environ 47 %) tandis "
                     "que les faibles n'apportent que ~19 %.",
        "conclusion": "Résultat gardé : il faut privilégier les signaux forts.",
    },
    "test_v176_composite_indicator.py": {
        "sous_question": "Combiner plusieurs briques en un indicateur composite améliore-t-il la "
                         "décision ?",
        "fait": "On construit un indicateur composite qui combine plusieurs briques (basis, "
                "saison, contexte) et on teste sa cohérence.",
        "comment": "On assemble les composantes, on vérifie la causalité et on compare des "
                   "variantes.",
        "resultats": "Le composite est cohérent et lisible ; il regroupe les briques validées "
                     "sans ajouter de complexité inutile.",
        "conclusion": "Résultat gardé : un indicateur composite clair, fondé sur les briques "
                      "retenues.",
    },
    "test_v56_target_recommendation.py": {
        "sous_question": "Peut-on transformer le signal de basis en une recommandation d'action "
                         "simple et lisible ?",
        "fait": "On construit une première règle de recommandation (quoi faire) à partir du "
                "signal de basis.",
        "comment": "On relie la force du signal à une action recommandée et on teste sur "
                   "l'historique.",
        "resultats": "La règle donne des recommandations cohérentes avec la performance, base "
                     "des versions ultérieures.",
        "conclusion": "Résultat gardé : première règle de recommandation exploitable.",
    },
    "test_v131_target_recommendation_v3.py": {
        "sous_question": "Quelle recommandation (vendre / attendre / surveiller) donner selon la "
                         "force du signal ?",
        "fait": "On définit une règle de recommandation à plusieurs états (vendre, attendre, "
                "surveiller) selon la force du signal de basis.",
        "comment": "On associe des seuils de signal à des recommandations et on évalue leur "
                   "pertinence, notamment pour les signaux marginaux.",
        "resultats": "Les signaux marginaux (faible écart, z<1.2) sous-performent nettement "
                     "(gain 6.09 contre 14.14) : on les met en attente de confirmation.",
        "conclusion": "Résultat gardé : une règle de recommandation prudente, qui se méfie des "
                      "signaux faibles.",
    },
    "test_v77_indicator_synthesis.py": {
        "sous_question": "Peut-on résumer l'indicateur en un état global cohérent ?",
        "fait": "On assemble une synthèse de l'indicateur regroupant ses composantes en un état "
                "global.",
        "comment": "On combine les briques validées en un résumé unique et on le teste.",
        "resultats": "La synthèse est cohérente et reproductible ; elle sert de base aux "
                     "versions suivantes.",
        "conclusion": "Résultat gardé : première synthèse globale de l'indicateur.",
    },
    "test_v99_indicator_synthesis_v2.py": {
        "sous_question": "La synthèse de l'indicateur tient-elle dans une version améliorée ?",
        "fait": "On met à jour la synthèse de l'indicateur (version 2) pour la fiabiliser.",
        "comment": "On affine l'agrégation des composantes et on vérifie la cohérence.",
        "resultats": "La synthèse v2 conserve la clarté tout en étant plus robuste.",
        "conclusion": "Résultat gardé : version consolidée de la synthèse.",
    },
    "test_v132_indicator_synthesis_v3.py": {
        "sous_question": "Comment résumer l'état de l'indicateur en un message clair et à jour ?",
        "fait": "On produit une synthèse de l'indicateur (version 3) qui résume l'état du signal "
                "et la recommandation en tête de tableau.",
        "comment": "On agrège les composantes en un message de synthèse, qui se dégrade si les "
                   "données sont périmées.",
        "resultats": "La synthèse fournit un message clair et honnête, et signale d'elle-même "
                     "quand les données ne sont plus fraîches.",
        "conclusion": "Résultat gardé : la synthèse v3 rend l'indicateur lisible d'un coup "
                      "d'oeil.",
    },
    "test_v149_indicator_multiview.py": {
        "sous_question": "Peut-on présenter l'indicateur sous plusieurs vues pour mieux le "
                         "comprendre ?",
        "fait": "On construit une présentation multi-vues de l'indicateur, montrant à la fois "
                "Euronext, CBOT et les différents signaux.",
        "comment": "On génère des vues coordonnées qui éclairent le signal sous plusieurs "
                   "angles.",
        "resultats": "La présentation multi-vues facilite la lecture et le diagnostic du signal.",
        "conclusion": "Résultat gardé : une vue d'ensemble lisible de l'indicateur.",
    },
    "test_v83_indicator_visual.py": {
        "sous_question": "Comment visualiser clairement l'indicateur et ses déclenchements dans "
                         "le temps ?",
        "fait": "On génère les figures de l'indicateur pour visualiser le signal et ses "
                "déclenchements sur l'historique.",
        "comment": "On produit des graphiques (sans dépendre d'images externes) montrant le "
                   "signal au fil du temps.",
        "resultats": "Les visuels rendent le comportement de l'indicateur compréhensible et "
                     "vérifiable.",
        "conclusion": "Résultat gardé : support visuel de l'indicateur.",
    },
    "test_v18_literature_replication.py": {
        "sous_question": "Nos résultats sur le basis sont-ils cohérents avec la littérature "
                         "académique ?",
        "fait": "On réplique les grandes familles de résultats de la littérature (théorie du "
                "stockage, basis trading, convergence, WASDE, COT, météo) pour situer nos "
                "conclusions.",
        "comment": "On reproduit les approches publiées sur nos données et on compare aux "
                   "résultats attendus.",
        "resultats": "Nos conclusions sont cohérentes avec la littérature : le basis revient à "
                     "la moyenne, les fondamentaux sont faibles en quotidien.",
        "conclusion": "Étape : ancre l'étude dans l'état de l'art et confirme les hypothèses de "
                      "départ.",
    },
    "test_v6_coherence_audit.py": {
        "sous_question": "Les résultats restent-ils cohérents entre les différentes versions et "
                         "modules ?",
        "fait": "On audite la cohérence d'ensemble : on vérifie que les modules et les résultats "
                "ne se contredisent pas.",
        "comment": "On recoupe les sorties des différents modules et on signale toute "
                   "incohérence.",
        "resultats": "La cohérence est vérifiée après corrections, ce qui fiabilise l'ensemble.",
        "conclusion": "Outil : garantit que les briques de l'étude restent cohérentes entre "
                      "elles.",
    },
    "test_v7_feature_data_quality.py": {
        "sous_question": "Les variables utilisées par l'indicateur sont-elles de qualité "
                         "suffisante ?",
        "fait": "On calcule un score de qualité des variables (features) pour ne garder que "
                "celles qui sont fiables.",
        "comment": "On évalue chaque variable (couverture, stabilité, absence de fuite) et on "
                   "lui attribue un score.",
        "resultats": "Les variables faibles sont écartées ; l'indicateur ne s'appuie que sur des "
                     "variables de qualité.",
        "conclusion": "Outil : assure la qualité des variables d'entrée de l'indicateur.",
    },
    "test_v7_new_modules.py": {
        "sous_question": "Les nouveaux modules de l'infrastructure fonctionnent-ils "
                         "correctement ?",
        "fait": "On teste les nouveaux modules ajoutés au programme (briques d'infrastructure et "
                "de calcul).",
        "comment": "On vérifie par des tests que chaque nouveau module produit les sorties "
                   "attendues.",
        "resultats": "Les modules passent leurs tests : l'infrastructure est fiable.",
        "conclusion": "Outil : valide les briques techniques qui soutiennent l'indicateur.",
    },
    "test_v7_phase3_6.py": {
        "sous_question": "Les tickets des phases 3 à 6 du programme aboutissent-ils aux "
                         "résultats attendus ?",
        "fait": "On exécute et on vérifie les tickets des phases 3 à 6 du programme (analyses et "
                "modules variés).",
        "comment": "On déroule chaque ticket et on contrôle son résultat par rapport à "
                   "l'objectif.",
        "resultats": "Les phases avancent comme prévu et alimentent l'indicateur en briques "
                     "validées.",
        "conclusion": "Étape : fait progresser le programme vers un indicateur consolidé.",
    },
    # ---- Q4 : qu'est-ce qui explique le basis et la prime ---------------------
    "test_v16_basis_explanation.py": {
        "sous_question": "Les variables macro-économiques (taux, change, indices) "
                         "expliquent-elles le niveau du basis ?",
        "fait": "On teste si des variables macro expliquent le basis, autrement dit s'il a une "
                "'juste valeur' fondée sur l'économie générale.",
        "comment": "On relie le basis à des variables macro et on mesure leur pouvoir "
                   "explicatif hors échantillon.",
        "resultats": "La macro n'explique pas le basis (pouvoir explicatif négatif hors "
                     "échantillon, de l'ordre de -0.25) : le basis est une prime LOCALE ; le "
                     "basis normalisé reste le meilleur prédicteur.",
        "conclusion": "Abandonné : pas de 'juste valeur' macro du basis ; on s'en tient au "
                      "basis lui-même.",
    },
    "test_ema_granger_validation.py": {
        "sous_question": "Une variable précède-t-elle et 'cause-t-elle' statistiquement le basis "
                         "(au sens de Granger), de façon exploitable ?",
        "fait": "On teste la causalité de Granger pour voir si une variable précède de façon "
                "fiable les mouvements du basis.",
        "comment": "On applique le test de Granger entre des candidats explicatifs et le basis, "
                   "puis on valide hors échantillon.",
        "resultats": "La causalité de Granger est rejetée hors échantillon : aucun lien causal "
                     "exploitable n'est trouvé.",
        "conclusion": "Abandonné : pas de causalité robuste vers le basis.",
    },
    "test_v36_physical_eu.py": {
        "sous_question": "Des facteurs physiques européens (offre, substitution) expliquent-ils "
                         "la prime ?",
        "fait": "On explore des facteurs physiques européens (équilibre offre/demande, "
                "substitution blé/maïs) comme explication possible de la prime.",
        "comment": "On relie le basis à des indicateurs physiques européens et on mesure la "
                   "corrélation, avec un ancrage documentaire.",
        "resultats": "Le basis covarie avec l'écart blé/maïs (corrélation ~0.60, logique de "
                     "substitution), mais un modèle de risque associé se révèle sur-appris.",
        "conclusion": "Étape : la substitution est un contexte réel, mais pas un prédicteur "
                      "fiable en l'état.",
    },
    "test_v40_substitution_deep.py": {
        "sous_question": "La prime est-elle vraiment locale (européenne), ou n'est-ce qu'un "
                         "reflet du CBOT ?",
        "fait": "On approfondit la substitution blé/maïs pour trancher si la prime est "
                "spécifiquement européenne ou seulement un reflet du CBOT.",
        "comment": "On compare la corrélation du ratio de substitution avec le basis et avec le "
                   "CBOT.",
        "resultats": "Le ratio est corrélé positivement au basis (+0.59) et négativement au CBOT "
                     "(-0.46) : la prime est bien LOCALE, pas un artefact du CBOT.",
        "conclusion": "Étape importante : confirme le caractère local de la prime européenne.",
    },
    "test_v37_substitution_residual.py": {
        "sous_question": "Si on retire l'effet de substitution blé/maïs, que reste-t-il à "
                         "expliquer dans le basis ?",
        "fait": "On ajuste le basis de l'effet de substitution blé/maïs pour isoler la part "
                "restante.",
        "comment": "On retire la composante liée au blé et on étudie le résidu.",
        "resultats": "Une part du basis s'explique par la substitution, mais un résidu local "
                     "subsiste et reste difficile à expliquer.",
        "conclusion": "Étape : la substitution explique une partie, pas tout ; la prime garde "
                      "une part locale.",
    },
    "test_v52_matif_substitution.py": {
        "sous_question": "Le blé MATIF (marché à terme européen) aide-t-il à expliquer le basis "
                         "maïs ?",
        "fait": "On teste l'apport du blé MATIF à l'explication du basis maïs.",
        "comment": "On relie le basis maïs au blé MATIF, mais l'accès aux données MATIF est "
                   "limité.",
        "resultats": "La piste est cohérente mais limitée par les données (data-gated) : on ne "
                     "peut pas conclure pleinement.",
        "conclusion": "Étape : piste de substitution européenne intéressante mais limitée par "
                      "les données.",
    },
    "test_v126_matif_substitution_v2.py": {
        "sous_question": "Avec plus de données, le blé MATIF explique-t-il une part mesurable du "
                         "basis ?",
        "fait": "On reprend la substitution MATIF dans une version élargie pour mesurer son "
                "apport.",
        "comment": "On recalcule la corrélation entre le basis maïs et le blé MATIF sur des "
                   "données actualisées.",
        "resultats": "On observe une corrélation modérée (environ 0.477) : un lien réel mais "
                     "partiel.",
        "conclusion": "Étape : confirme un lien modéré, contexte utile sans être un signal fort.",
    },
    "test_v168_substitution_basket.py": {
        "sous_question": "Un panier de substitution élargi (plusieurs céréales) explique-t-il "
                         "mieux le basis que le blé seul ?",
        "fait": "On élargit la substitution à un panier de plusieurs produits pour voir s'il "
                "explique mieux le basis que le blé seul.",
        "comment": "On construit un panier de substitution et on compare son pouvoir explicatif "
                   "à celui du blé seul.",
        "resultats": "Le panier élargi n'apporte pas d'amélioration nette par rapport au blé "
                     "seul.",
        "conclusion": "Étape : le blé seul suffit comme contexte de substitution.",
    },
    "test_v166_convenience_yield.py": {
        "sous_question": "Le 'rendement de convenance' (lié à la tension des stocks) explique-t-"
                         "il le basis ?",
        "fait": "On teste si le rendement de convenance, dérivé de la chaîne de bilan (stocks "
                "tendus), explique le basis.",
        "comment": "On construit la chaîne bilan -> rendement de convenance -> basis et on "
                   "évalue le lien.",
        "resultats": "Le lien n'est pas robuste : le rendement de convenance n'explique pas le "
                     "basis de façon exploitable.",
        "conclusion": "Abandonné : pas d'explication fiable du basis par le rendement de "
                      "convenance.",
    },
    "test_v54_physical_tension.py": {
        "sous_question": "Un score de tension physique (offre/demande européenne) renseigne-t-il "
                         "sur le basis ?",
        "fait": "On construit un score de tension physique européenne pour voir s'il accompagne "
                "les mouvements du basis.",
        "comment": "On agrège des indicateurs de tension physique et on les compare au basis.",
        "resultats": "Le score de tension donne un contexte cohérent mais pas un signal "
                     "prédictif fiable.",
        "conclusion": "Étape : contexte utile, sans pouvoir prédictif net.",
    },
    "test_v80_intercommodity_spreads.py": {
        "sous_question": "Les écarts entre matières premières (maïs, blé, soja) prédisent-ils le "
                         "basis ou la direction ?",
        "fait": "On teste les écarts inter-commodités comme prédicteurs.",
        "comment": "On construit ces écarts et on mesure leur apport hors échantillon.",
        "resultats": "Les écarts inter-commodités n'apportent pas de signal robuste.",
        "conclusion": "Abandonné : pas de prédiction exploitable via les écarts inter-"
                      "commodités.",
    },
    "test_v120_basis_econometrics.py": {
        "sous_question": "Peut-on modéliser économétriquement le basis (cointégration, "
                         "correction d'erreur) sur des données propres ?",
        "fait": "On vise une analyse économétrique fine du basis (cointégration, modèle à "
                "correction d'erreur).",
        "comment": "Cela demande des séries longues et propres (spot, change) qui manquent.",
        "resultats": "L'analyse reste limitée faute de données quotidiennes adéquates : "
                     "conclusions partielles seulement.",
        "conclusion": "Bloqué : économétrie du basis limitée par les données disponibles.",
    },
    "test_v121_basis_forecast_model.py": {
        "sous_question": "Peut-on construire un modèle de prévision du basis lui-même ?",
        "fait": "On tente un modèle de prévision directe du basis.",
        "comment": "On construit un modèle prédictif du basis, qui dépend de séries propres "
                   "manquantes (change, spot).",
        "resultats": "La prévision du basis reste bloquée par l'absence de données quotidiennes "
                     "fiables.",
        "conclusion": "Bloqué : prévision du basis non aboutie faute de données.",
    },
    "test_v162_vecm.py": {
        "sous_question": "Dans un modèle à correction d'erreur (VECM), lequel de CBOT ou Euronext "
                         "s'ajuste vers l'équilibre ?",
        "fait": "On formalise la relation par un VECM pour mesurer la vitesse à laquelle chaque "
                "marché revient vers l'équilibre commun.",
        "comment": "On estime le VECM entre Euronext et CBOT et on lit les vitesses "
                   "d'ajustement.",
        "resultats": "La vitesse d'ajustement de l'Euronext domine (c'est l'Euronext qui revient "
                     "vers l'équilibre), mais le volet spot physique reste bloqué.",
        "conclusion": "Bloqué : formalisation utile mais incomplète faute de données spot.",
    },
    "test_v174_fx_bce.py": {
        "sous_question": "Quel taux de change EUR/USD utiliser, à la bonne heure, pour calculer "
                         "le basis sans fuite ?",
        "fait": "On met en place une règle de change EUR/USD horodatée (taux de référence de la "
                "BCE) pour convertir proprement Euronext et CBOT.",
        "comment": "On lit le taux BCE à l'heure de référence, hors ligne, pour dater "
                   "correctement la conversion.",
        "resultats": "La règle fonctionne sur la période récente, mais l'historique quotidien "
                     "complet du change manque pour reconstruire tout le basis.",
        "conclusion": "Bloqué : règle de change posée, mais historique EUR/USD insuffisant.",
    },
    "test_wasde_world.py": {
        "sous_question": "Les bilans mondiaux (WASDE Union européenne + Ukraine) éclairent-ils "
                         "la prime européenne ?",
        "fait": "On intègre les données de bilan mondial WASDE pour l'UE et l'Ukraine, sources "
                "clés de l'offre qui pèse sur le marché européen.",
        "comment": "On collecte et on structure les variables de bilan UE et Ukraine, datées à "
                   "leur publication.",
        "resultats": "Ces bilans fournissent un contexte d'offre régionale pertinent pour la "
                     "prime européenne, utilisable proprement.",
        "conclusion": "Résultat gardé : données de bilan UE/Ukraine utiles comme contexte "
                      "d'offre.",
    },
    "EXT013_basis_and_spot_futures_transmission": {
        "sous_question": "Comment le prix physique (spot) et le prix à terme se transmettent-ils "
                         "l'un à l'autre dans le basis ?",
        "fait": "On veut mesurer la transmission entre le prix physique (spot) et le prix à "
                "terme, qui forment le basis, pour en comprendre la dynamique.",
        "comment": "Cela nécessite un historique quotidien du change EUR/USD et un prix spot "
                   "européen quotidien, qu'on tente de réunir.",
        "resultats": "Le basis en euros/tonne n'est pas reconstructible faute d'EUR/USD "
                     "quotidien historique et de spot UE quotidien : le test n'est pas "
                     "réalisable.",
        "conclusion": "Bloqué : manque l'EUR/USD quotidien et le spot UE ; piste en attente de "
                      "données.",
    },
    "test_comext_and_eu_pressure.py": {
        "sous_question": "Les flux commerciaux européens (COMEXT) et la pression physique UE "
                         "expliquent-ils la prime ?",
        "fait": "On tente d'exploiter les données de commerce extérieur européen (COMEXT) pour "
                "mesurer la pression physique sur le marché européen.",
        "comment": "On récupère COMEXT au mieux et on construit un indicateur de tension, mais "
                   "la donnée est partielle et mensuelle.",
        "resultats": "COMEXT est trop partiel et peu fréquent (mensuel) pour un signal "
                     "quotidien : exploitation limitée.",
        "conclusion": "Bloqué : données COMEXT insuffisantes pour un signal exploitable.",
    },
    "test_franceagrimer.py": {
        "sous_question": "Les données FranceAgriMer / Agreste (offre et prix physiques français) "
                         "sont-elles exploitables ?",
        "fait": "On teste l'accès aux données FranceAgriMer / Agreste comme source de prix "
                "physiques et de bilan français.",
        "comment": "On sonde la disponibilité, la fréquence et la profondeur de ces données.",
        "resultats": "Les données ne sont pas disponibles à une fréquence et une profondeur "
                     "suffisantes pour l'étude quotidienne.",
        "conclusion": "Bloqué : source FranceAgriMer non exploitable en l'état.",
    },
    "test_eu_fundamentals_collector.py": {
        "sous_question": "Peut-on collecter automatiquement des fondamentaux européens pour "
                         "expliquer la prime ?",
        "fait": "On teste un collecteur de fondamentaux européens (bilans, production) pour "
                "alimenter l'explication de la prime.",
        "comment": "On exécute le collecteur en mode contrôlé et on vérifie le format et la "
                   "couverture.",
        "resultats": "Le collecteur fonctionne, mais les fondamentaux disponibles restent rares "
                     "et peu fréquents.",
        "conclusion": "Étape : on peut collecter, mais les fondamentaux européens restent "
                      "limités.",
    },
    "test_fas_exports.py": {
        "sous_question": "Les ventes à l'export américaines (USDA FAS) apportent-elles une "
                         "information utile ?",
        "fait": "On teste l'apport des données hebdomadaires de ventes export US (USDA FAS) à "
                "l'analyse.",
        "comment": "On collecte les ventes export et on regarde si elles éclairent la direction "
                   "ou le basis.",
        "resultats": "Les exports donnent un contexte de demande, sans signal prédictif net en "
                     "l'état.",
        "conclusion": "Étape : donnée gratuite utile en contexte, à creuser plus tard.",
    },
    "test_world_collector.py": {
        "sous_question": "Peut-on rassembler des données mondiales (bilans, régions) de façon "
                         "fiable ?",
        "fait": "On teste un collecteur de données mondiales (bilans par région) pour enrichir "
                "le contexte d'offre.",
        "comment": "On exécute le collecteur et on vérifie la cohérence des données "
                   "rassemblées.",
        "resultats": "La collecte mondiale fonctionne et alimente le contexte d'offre (UE, "
                     "Ukraine, etc.).",
        "conclusion": "Étape d'acquisition : fournit le contexte d'offre mondiale.",
    },
    "test_new_sources.py": {
        "sous_question": "De nouvelles sources gratuites pourraient-elles enrichir l'explication "
                         "de la prime ?",
        "fait": "On teste l'intégration de nouvelles sources de données candidates pour voir si "
                "elles apportent quelque chose.",
        "comment": "On branche ces sources, on vérifie leur qualité et on évalue leur apport "
                   "potentiel.",
        "resultats": "Les nouvelles sources sont souvent partielles ou peu fréquentes ; peu "
                     "apportent un signal exploitable.",
        "conclusion": "Étape : veille de sources, peu de gain immédiat mais utile pour préparer "
                      "la suite.",
    },
    # ---- Q2b : la météo aide-t-elle à prédire ? -------------------------------
    "test_v45_weather_crop_stress.py": {
        "sous_question": "Le stress météo réellement observé (chaleur, sécheresse) sur les zones "
                         "de culture américaines prédit-il la direction du CBOT ?",
        "fait": "On teste si le stress météo réalisé sur les régions de culture US anticipe les "
                "mouvements du CBOT.",
        "comment": "On construit des indices de stress (chaleur, déficit de pluie) sur les "
                   "fenêtres agronomiques et on mesure leur pouvoir prédictif sur la direction.",
        "resultats": "La météo réalisée ne prédit pas le CBOT (justesse ~0.508, proche du "
                     "hasard) : au moment où on l'observe, le marché l'a déjà intégrée.",
        "conclusion": "Abandonné comme prédicteur ; gardé comme contexte (un été de stress rend "
                      "le basis moins compressible).",
    },
    "EXT001_weather_crop_windows": {
        "sous_question": "Des fenêtres météo par stade de culture (semis, floraison) apportent-"
                         "elles un signal directionnel ?",
        "fait": "On agrège la météo par fenêtres agronomiques (selon le stade de la culture) "
                "pour capter les périodes sensibles.",
        "comment": "On construit des variables météo par stade et on les ajoute à un modèle "
                   "directionnel, sans fuite.",
        "resultats": "Ces fenêtres dégradent la prévision (erreur en hausse) et n'ajoutent rien "
                     "d'utile en direction.",
        "conclusion": "Abandonné : la météo réalisée par fenêtres ne porte pas de signal.",
    },
    "EXT002_weather_lags_and_anomalies": {
        "sous_question": "Des anomalies météo et leurs décalages dans le temps prédisent-ils "
                         "mieux la direction ?",
        "fait": "On teste des anomalies météo (écart à la normale) et leurs décalages comme "
                "prédicteurs.",
        "comment": "On calcule des anomalies glissantes et on mesure leur apport, hors "
                   "échantillon.",
        "resultats": "Gain ponctuel et instable, avec un pouvoir explicatif négatif : pas de "
                     "signal fiable.",
        "conclusion": "Abandonné : anomalies et décalages réalisés non exploitables.",
    },
    "EXT020_extreme_weather_events": {
        "sous_question": "Les événements météo extrêmes (canicule, sécheresse sévère) prédisent-"
                         "ils la direction ?",
        "fait": "On teste si les événements météo extrêmes apportent un signal directionnel "
                "fort.",
        "comment": "On repère les extrêmes et on mesure la direction du CBOT qui suit, sans "
                   "fuite.",
        "resultats": "Les extrêmes réalisés dégradent fortement la prévision (pouvoir explicatif "
                     "très négatif) : non prédictifs.",
        "conclusion": "Abandonné : les extrêmes réalisés sont déjà intégrés ; à garder en "
                      "contexte seulement.",
    },
    "test_v18_weather_deep.py": {
        "sous_question": "En creusant la météo sous tous ses angles, trouve-t-on un signal "
                         "caché ?",
        "fait": "On mène une exploration approfondie de la météo (multiples agrégations, zones, "
                "indicateurs).",
        "comment": "On teste de nombreuses variantes de variables météo et on mesure leur "
                   "apport.",
        "resultats": "Aucune variante de météo réalisée ne donne de signal robuste.",
        "conclusion": "Abandonné : confirme par l'exhaustivité que la météo réalisée ne prédit "
                      "pas.",
    },
    "test_v51_weather_extremes.py": {
        "sous_question": "Un laboratoire dédié aux extrêmes météo révèle-t-il un effet "
                         "exploitable ?",
        "fait": "On construit un laboratoire d'analyse des extrêmes météo pour isoler leur "
                "effet.",
        "comment": "On teste plusieurs définitions d'extrême et leur impact sur la direction.",
        "resultats": "Pas d'effet prédictif exploitable des extrêmes réalisés.",
        "conclusion": "Abandonné : les extrêmes réalisés restent du contexte, pas un signal.",
    },
    "test_v60_weather_basis_driver.py": {
        "sous_question": "La météo est-elle un moteur du basis (et pas seulement du prix) ?",
        "fait": "On teste si la météo explique ou prédit le basis (la prime), pas seulement le "
                "prix.",
        "comment": "On relie des indices météo au basis et on mesure le lien, sans fuite.",
        "resultats": "La météo réalisée n'est pas un moteur prédictif du basis ; au mieux elle "
                     "rend le basis moins compressible en été de stress (contexte).",
        "conclusion": "Abandonné comme prédicteur du basis ; effet de contexte seulement.",
    },
    "test_v19_cbot_weather.py": {
        "sous_question": "La météo aide-t-elle davantage à anticiper les BAISSES du CBOT que ses "
                         "hausses ?",
        "fait": "On installe un laboratoire de risque CBOT avec l'infrastructure météo, en "
                "regardant séparément les hausses et les baisses.",
        "comment": "On teste l'apport de la météo réalisée à la direction du CBOT, en "
                   "distinguant les deux sens.",
        "resultats": "Le CBOT prédit mieux ses baisses que ses hausses ; la météo réalisée "
                     "n'ajoute qu'un faible +0.07 sur la direction.",
        "conclusion": "Étape : apport météo marginal ; oriente vers la météo PRÉVUE plutôt que "
                      "réalisée.",
    },
    "test_v28_forecast_weather.py": {
        "sous_question": "La météo PRÉVUE (les prévisions), et non réalisée, contient-elle un "
                         "signal, sans fuite ?",
        "fait": "On étudie la météo PRÉVUE en respectant l'anti-fuite : on n'utilise que des "
                "prévisions disponibles AVANT la date de décision.",
        "comment": "On sépare strictement le réalisé du prévu et on teste si les prévisions "
                   "anticipent la direction.",
        "resultats": "La météo prévue est la seule voie cohérente, mais son exploitation est "
                     "limitée par la profondeur des archives de prévisions.",
        "conclusion": "Étape : ouvre la piste de la météo prévue, à creuser avec des archives "
                      "plus longues.",
    },
    "test_v48_weather_forecast_signal.py": {
        "sous_question": "Une prévision météo favorable ou défavorable se traduit-elle par un "
                         "signal directionnel ?",
        "fait": "On teste si le caractère favorable ou défavorable des prévisions météo donne un "
                "signal sur la direction.",
        "comment": "On classe les prévisions (favorable/défavorable) et on mesure la direction "
                   "qui suit.",
        "resultats": "Le signal est trop faible et instable pour être exploitable.",
        "conclusion": "Abandonné : le caractère des prévisions ne suffit pas à un signal fiable.",
    },
    "test_v127_weather_forecast_extremes.py": {
        "sous_question": "Les prévisions d'extrêmes météo et leurs révisions anticipent-elles le "
                         "marché ?",
        "fait": "On teste les prévisions d'événements extrêmes et leurs révisions comme signal "
                "anticipé.",
        "comment": "On suit les prévisions extrêmes et leurs mises à jour, en respectant "
                   "l'anti-fuite.",
        "resultats": "Pas de signal robuste : l'archive de prévisions est trop courte pour "
                     "conclure.",
        "conclusion": "Abandonné en l'état : nécessiterait une archive de prévisions plus "
                      "profonde.",
    },
    "test_v136_weather_revision_archive.py": {
        "sous_question": "Peut-on archiver les prévisions météo successives pour étudier leurs "
                         "révisions plus tard ?",
        "fait": "On met en place une archive des prévisions météo successives, pour pouvoir "
                "étudier leurs révisions dans le futur.",
        "comment": "On enregistre chaque prévision à mesure qu'elle sort, en gardant la trace "
                   "des mises à jour.",
        "resultats": "L'archive démarre mais reste trop courte pour un test concluant ; c'est un "
                     "investissement pour l'avenir.",
        "conclusion": "Abandonné pour l'instant : l'archive doit s'allonger avant de pouvoir "
                      "conclure.",
    },
    "test_v140_weather_revision_engine.py": {
        "sous_question": "Peut-on automatiser le calcul des révisions de prévisions météo en un "
                         "moteur dédié ?",
        "fait": "On construit un moteur qui calcule automatiquement les révisions de prévisions "
                "météo (différences entre prévisions successives).",
        "comment": "On code le moteur et on le teste sur l'archive disponible.",
        "resultats": "Le moteur fonctionne, mais l'archive trop courte ne permet pas encore de "
                     "valider un signal.",
        "conclusion": "Abandonné en l'état : outil prêt, données encore insuffisantes.",
    },
    "test_v155_weather_revision_validation.py": {
        "sous_question": "Les révisions de prévisions météo, une fois assez de données, donnent-"
                         "elles un signal ?",
        "fait": "On valide de façon exploratoire si les révisions de prévisions météo apportent "
                "un signal.",
        "comment": "On teste le lien entre les révisions de prévisions et la direction, sur les "
                   "données disponibles.",
        "resultats": "Résultat préliminaire négatif : pas de signal clair avec l'archive "
                     "actuelle.",
        "conclusion": "Abandonné pour l'instant : à reconfirmer quand l'archive sera plus "
                      "longue.",
    },
    "test_v79_enso_regime.py": {
        "sous_question": "Le régime climatique El Nino / La Nina (ENSO) influence-t-il le marché "
                         "de façon exploitable ?",
        "fait": "On teste si le régime climatique global ENSO (El Nino / La Nina) donne un "
                "signal sur le maïs.",
        "comment": "On relie l'indice ENSO aux mouvements du marché, par régime.",
        "resultats": "Pas de signal exploitable : l'effet ENSO est trop diffus et lent pour "
                     "notre horizon.",
        "conclusion": "Abandonné : ENSO sans pouvoir prédictif net.",
    },
    "test_enso.py": {
        "sous_question": "Peut-on récupérer et exploiter l'indice climatique ENSO ?",
        "fait": "On teste la collecte et l'usage de l'indice ENSO comme variable climatique.",
        "comment": "On récupère l'indice et on évalue son apport potentiel.",
        "resultats": "L'indice est disponible mais sans valeur prédictive utile (confirmé par "
                     "V79).",
        "conclusion": "Abandonné : ENSO non exploitable comme prédicteur.",
    },
    "EXT018_weather_risk_premium_new_crop": {
        "sous_question": "Le contrat de nouvelle récolte porte-t-il une prime de risque météo "
                         "qui se dissipe du printemps à la récolte ?",
        "fait": "On teste l'idée d'une prime de risque météo sur le contrat de nouvelle récolte, "
                "élevée au printemps (incertitude) puis se dissipant vers la récolte.",
        "comment": "On réplique l'analyse descriptive (à la Janzen) puis on teste un usage "
                   "prédictif conditionné au niveau de stress.",
        "resultats": "Le volet descriptif est confirmé (biais baissier avant récolte en année "
                     "normale, rally en année de stress), mais le volet prédictif échoue : le "
                     "stress n'est connu qu'en cours de saison, pas à l'avance.",
        "conclusion": "Partiel : phénomène réel mais non exploitable à l'avance faute de "
                      "connaître le stress ex ante.",
    },
    "test_crop_condition_phenology.py": {
        "sous_question": "L'état de la culture (good/excellent) au bon stade de développement "
                         "renseigne-t-il sur la direction à venir ?",
        "fait": "On relie l'état de la culture (condition good/excellent) à son stade de "
                "développement pour en faire un signal d'offre.",
        "comment": "On construit des variables de condition de culture datées à publication, en "
                   "tenant compte du stade (floraison, etc.).",
        "resultats": "La condition de culture porte un signal directionnel à long horizon : "
                     "c'est l'une des rares variables fondamentales utiles, confirmée plus tard "
                     "en recherche externe.",
        "conclusion": "Résultat gardé : la condition de culture est une brique du signal "
                      "directionnel.",
    },
    "test_forecast_revision_tape.py": {
        "sous_question": "Peut-on enregistrer en continu (un journal) les révisions de "
                         "prévisions au fil du temps ?",
        "fait": "On met en place un journal qui enregistre, jour après jour, les prévisions et "
                "leurs révisions, pour analyse ultérieure.",
        "comment": "On capture les prévisions successives en flux et on les horodate.",
        "resultats": "Le journal fonctionne et constitue la base de données nécessaire pour "
                     "étudier les révisions plus tard.",
        "conclusion": "Étape d'acquisition : prépare le terrain pour la seule voie météo "
                      "prédictive.",
    },
    "test_openmeteo_eu.py": {
        "sous_question": "Peut-on collecter la météo des zones de culture européennes "
                         "(Open-Meteo) ?",
        "fait": "On teste la collecte de la météo des zones agricoles européennes via "
                "Open-Meteo.",
        "comment": "On récupère les variables météo (température, pluie) sur les zones UE et on "
                   "vérifie la couverture.",
        "resultats": "La collecte fonctionne et fournit une météo européenne utilisable comme "
                     "contexte.",
        "conclusion": "Étape d'acquisition : météo européenne disponible (contexte).",
    },
    "test_openmeteo_previous_runs.py": {
        "sous_question": "Peut-on récupérer les anciennes versions des prévisions (previous "
                         "runs) pour reconstituer leurs révisions ?",
        "fait": "On teste la collecte des 'previous runs' d'Open-Meteo, c'est-à-dire les "
                "prévisions telles qu'elles étaient les jours précédents.",
        "comment": "On récupère les versions antérieures des prévisions pour reconstituer leur "
                   "évolution.",
        "resultats": "La récupération est possible et débloque partiellement l'étude des "
                     "révisions de prévisions.",
        "conclusion": "Étape d'acquisition : débloque une partie de l'archive de prévisions "
                      "nécessaire.",
    },
    "test_ec_mars.py": {
        "sous_question": "Les données agro-météo européennes officielles (EC MARS / Eurostat) "
                         "sont-elles exploitables ?",
        "fait": "On teste le collecteur des données agro-météorologiques européennes officielles "
                "(EC MARS via Eurostat).",
        "comment": "On sonde la disponibilité, la fréquence et la couverture de ces données.",
        "resultats": "Les données existent mais sont peu fréquentes et tardives : utiles en "
                     "contexte, pas pour un signal quotidien.",
        "conclusion": "Étape : source agro-météo européenne de contexte, peu adaptée au signal "
                      "quotidien.",
    },
    # ---- Q2c : le COT et l'éthanol aident-ils ? -------------------------------
    "EXT003_cot_features": {
        "sous_question": "Les positions des grands spéculateurs (COT Managed Money) donnent-"
                         "elles un signal directionnel ?",
        "fait": "On teste si les positions des grands spéculateurs (données COT détaillées) "
                "prédisent la direction du maïs.",
        "comment": "On construit des variables COT (positions nettes, flux, extrêmes), datées au "
                   "vendredi de publication, et on mesure leur apport hors échantillon.",
        "resultats": "Le COT dégrade la prévision (erreur et direction) à tous les horizons : "
                     "aucun signal de second ordre.",
        "conclusion": "Abandonné : dossier COT clos, pas de signal exploitable hors échantillon.",
    },
    "test_cot_advanced.py": {
        "sous_question": "En affinant les variables COT (catégories, ratios, concentration), "
                         "trouve-t-on un signal ?",
        "fait": "On approfondit l'analyse COT avec des variables plus fines (catégories de "
                "traders, concentration, ratios).",
        "comment": "On teste ces variables avancées, toujours en respectant la date de "
                   "publication du vendredi.",
        "resultats": "Même avec des variables avancées, le COT n'apporte pas de signal robuste.",
        "conclusion": "Abandonné : confirme l'absence de signal COT, même en version détaillée.",
    },
    "EXT004_ethanol_ddg_crush_spread": {
        "sous_question": "La marge de transformation (éthanol, DDG, maïs) éclaire-t-elle la "
                         "demande et la direction ?",
        "fait": "On teste si la marge de transformation du maïs en éthanol (avec les co-produits "
                "DDG) donne un signal sur la demande et la direction.",
        "comment": "Faute de vrais prix éthanol et DDG, on utilise des proxys (demande éthanol, "
                   "ratios énergie) et on mesure leur apport.",
        "resultats": "Sans vrais prix éthanol/DDG, les proxys dégradent la prévision : pas de "
                     "marge de transformation exploitable.",
        "conclusion": "Abandonné en l'état : nécessiterait de vrais prix éthanol et DDG.",
    },
    "test_eu_carbon.py": {
        "sous_question": "Le prix du carbone européen (ETS) et du gaz (TTF) influencent-ils le "
                         "marché du maïs ?",
        "fait": "On teste si le prix du CO2 européen (ETS) et du gaz (TTF) apportent une "
                "information utile (coûts de production, énergie).",
        "comment": "On collecte ces prix énergie/carbone et on regarde leur lien avec le maïs.",
        "resultats": "Pas de lien exploitable : ces prix énergie/carbone n'aident pas à prévoir "
                     "le maïs.",
        "conclusion": "Abandonné : énergie/carbone européens sans pouvoir prédictif net.",
    },
    # ---- Q5 : la compression ADVERSE est-elle prévisible ? --------------------
    "test_v32_adverse_path.py": {
        "sous_question": "Quand une position sur la prime risque de mal tourner (chemin "
                         "ADVERSE), peut-on le repérer dès l'entrée ?",
        "fait": "On cherche à détecter, dès l'entrée, les situations où la compression de prime "
                "va suivre un chemin défavorable (des pertes).",
        "comment": "On classe les épisodes selon leur issue (favorable ou ADVERSE) et on teste "
                   "si des variables connues à l'entrée (niveau, basis bas) prédisent l'issue, "
                   "en validation laissant un épisode de côté.",
        "resultats": "L'issue ADVERSE est prévisible (justesse AUC 0.72) à partir du niveau "
                     "d'entrée et d'un basis bas.",
        "conclusion": "Résultat gardé : on sait estimer a priori le risque qu'une vente de prime "
                      "tourne mal.",
    },
    "test_adverse_discriminator.py": {
        "sous_question": "Avec seulement l'information disponible à l'entrée, peut-on séparer les "
                         "bons des mauvais cas ?",
        "fait": "On construit un discriminant qui, à l'entrée uniquement (sans rien voir du "
                "futur), sépare les épisodes favorables des épisodes ADVERSE.",
        "comment": "On entraîne un classifieur sur des variables connues à l'entrée et on valide "
                   "en laissant des épisodes de côté.",
        "resultats": "Le discriminant sépare correctement les cas (cohérent avec l'AUC 0.72 de "
                     "V32), confirmant que le risque s'estime à l'avance.",
        "conclusion": "Étape : confirme qu'un score de risque à l'entrée est possible et fiable.",
    },
    "test_v38_adverse_risk.py": {
        "sous_question": "Peut-on transformer cette détection en un score de risque ADVERSE "
                         "simple et fiable ?",
        "fait": "On construit un module de score de risque ADVERSE fondé sur des règles (sans "
                "apprentissage), à partir des facteurs identifiés.",
        "comment": "On combine quelques règles (support CBOT, basis bas, substitution) en "
                   "paliers de risque, sans ajuster sur les données.",
        "resultats": "Le score donne des paliers de risque qui montent proprement (0 %, 18 %, "
                     "25 %) tandis que la performance décroît (27.6 -> 11.5 -> 5.0) ; la prime "
                     "'justifiée' est justement la plus exposée au risque ADVERSE.",
        "conclusion": "Résultat gardé : un score de risque ADVERSE clair, fondé sur des règles.",
    },
    "test_v64_adverse_risk_v2.py": {
        "sous_question": "Le score de risque ADVERSE tient-il dans une version améliorée ?",
        "fait": "On améliore le score de risque ADVERSE (calibration, facteurs) pour le rendre "
                "plus robuste.",
        "comment": "On affine les règles et on revalide la montée régulière des paliers de "
                   "risque.",
        "resultats": "La version 2 conserve des paliers de risque cohérents et robustes.",
        "conclusion": "Résultat gardé : version consolidée du score de risque ADVERSE.",
    },
    "test_v65_cbot_rebound_engine.py": {
        "sous_question": "Une hausse (rebond) du CBOT est-elle ce qui déclenche le plus souvent "
                         "une issue défavorable ?",
        "fait": "On construit un moteur qui suit les rebonds du CBOT, soupçonnés d'être à "
                "l'origine des pertes sur la prime.",
        "comment": "On relie les épisodes ADVERSE aux rebonds du CBOT et on mesure leur rôle.",
        "resultats": "Un rebond du CBOT est bien le principal déclencheur des issues "
                     "défavorables ; un support CBOT en sens inverse réduit fortement le risque.",
        "conclusion": "Résultat gardé : identifie le rebond CBOT comme moteur du risque, et le "
                      "support comme garde-fou.",
    },
    "test_v44_mechanism_magnitude.py": {
        "sous_question": "Peut-on prédire COMMENT (par quel mécanisme) et DE COMBIEN la prime va "
                         "se compresser ?",
        "fait": "On cherche à prédire le mécanisme précis et l'ampleur de la compression, au-"
                "delà de sa simple issue.",
        "comment": "On teste des modèles du chemin et de la magnitude de compression.",
        "resultats": "Ni le mécanisme ni la magnitude ne sont prévisibles (justesse proche du "
                     "hasard, ~0.48).",
        "conclusion": "Abandonné : on peut estimer le risque, pas le mécanisme ni l'ampleur.",
    },
    "test_hazard_compression.py": {
        "sous_question": "Peut-on prédire le MOMENT (le timing) où la compression va démarrer ?",
        "fait": "On teste un modèle de 'temps avant compression' (modèle de hasard) pour prédire "
                "quand elle commence.",
        "comment": "On modélise la durée avant le départ de compression et on évalue sa "
                   "précision.",
        "resultats": "Le modèle de hasard a une justesse proche du taux de base : le timing "
                     "n'est pas prévisible.",
        "conclusion": "Abandonné : le moment du départ de compression n'est pas prévisible.",
    },
    "test_v104_compression_start.py": {
        "sous_question": "Comment dater objectivement le DÉBUT d'une compression de prime ?",
        "fait": "On définit une règle objective pour repérer la date de début d'une compression "
                "de prime.",
        "comment": "On code un détecteur de début de compression et on le teste sur "
                   "l'historique.",
        "resultats": "On obtient une datation cohérente des débuts de compression, base des "
                     "études suivantes.",
        "conclusion": "Étape : fournit une définition claire du début de compression.",
    },
    "test_v105_compression_event_study.py": {
        "sous_question": "Que se passe-t-il autour du début d'une compression (prix, CBOT, "
                         "prime) ?",
        "fait": "On mène une étude d'événement autour des débuts de compression pour voir le "
                "comportement typique des prix.",
        "comment": "On aligne les épisodes sur leur date de début et on observe l'évolution "
                   "moyenne avant et après.",
        "resultats": "Autour du début de compression, le CBOT a plutôt tendance à baisser "
                     "légèrement (et non à monter) avant que la prime ne se compresse : la "
                     "narration est précisée.",
        "conclusion": "Étape : décrit le déroulé typique d'une compression, utile au diagnostic.",
    },
    "test_v106_compression_trigger.py": {
        "sous_question": "Existe-t-il un déclencheur identifiable juste avant une compression ?",
        "fait": "On cherche un déclencheur observable qui précéderait le début d'une "
                "compression.",
        "comment": "On teste plusieurs candidats déclencheurs et on mesure leur capacité à "
                   "anticiper.",
        "resultats": "Aucun déclencheur fiable n'anticipe le timing (cohérent avec l'échec du "
                     "modèle de hasard) : le risque s'estime sur l'état, pas sur un déclencheur.",
        "conclusion": "Étape : confirme qu'on estime le risque a priori, sans déclencheur "
                      "précis.",
    },
    "test_v70_path_classification.py": {
        "sous_question": "Peut-on classer les compressions selon leur canal (par le CBOT, par "
                         "l'Euronext) ?",
        "fait": "On classe les épisodes de compression selon le canal par lequel ils se "
                "produisent.",
        "comment": "On catégorise chaque épisode (hausse CBOT, baisse Euronext, mixte) et on en "
                   "mesure la fréquence.",
        "resultats": "La compression passe le plus souvent par une hausse du CBOT ; la "
                     "classification éclaire la nature du risque.",
        "conclusion": "Étape : caractérise les canaux de compression (surtout par le CBOT).",
    },
    "test_v50_adverse_casebook.py": {
        "sous_question": "Peut-on cataloguer les cas ADVERSE passés pour en tirer des "
                         "enseignements ?",
        "fait": "On constitue un recueil de cas des épisodes ADVERSE pour les étudier un par un.",
        "comment": "On documente chaque épisode défavorable (contexte, déclencheur, issue).",
        "resultats": "Le recueil met en évidence des schémas récurrents (prime basse suivie "
                     "d'une hausse du CBOT).",
        "conclusion": "Étape : base de cas utile pour comprendre et anticiper les pertes.",
    },
    "test_v58_casebook_enriched.py": {
        "sous_question": "Un recueil de cas enrichi confirme-t-il les schémas de perte ?",
        "fait": "On enrichit le recueil de cas ADVERSE avec plus de contexte et d'épisodes.",
        "comment": "On ajoute des variables de contexte à chaque cas et on cherche des "
                   "régularités.",
        "resultats": "Les schémas se confirment : les pertes viennent surtout d'une prime basse "
                     "suivie d'un rebond du CBOT.",
        "conclusion": "Étape : consolide la compréhension des cas ADVERSE.",
    },
    "test_v57_magnitude_buckets.py": {
        "sous_question": "Peut-on prédire dans quelle classe d'ampleur (petite, moyenne, grosse) "
                         "tombera la compression ?",
        "fait": "On range les compressions en classes d'ampleur et on teste si on peut prédire "
                "la classe.",
        "comment": "On définit des seuils d'ampleur et on évalue la prévisibilité de la classe.",
        "resultats": "La classe d'ampleur n'est pas prévisible de façon fiable.",
        "conclusion": "Abandonné : l'ampleur de la compression reste imprévisible.",
    },
    "test_v72_survival_reversion.py": {
        "sous_question": "Peut-on prédire le temps avant que la prime ne revienne à la normale "
                         "(réversion) ?",
        "fait": "On modélise le temps avant retour à la moyenne de la prime (analyse de survie).",
        "comment": "On applique une analyse de survie au temps de réversion.",
        "resultats": "Le temps exact de réversion n'est pas prévisible ; seule la tendance "
                     "générale (retour à la moyenne) est fiable.",
        "conclusion": "Abandonné : le timing précis de la réversion n'est pas prévisible.",
    },
    "test_v169_bayes_survival.py": {
        "sous_question": "Une approche bayésienne hiérarchique améliore-t-elle la prévision du "
                         "temps de réversion ?",
        "fait": "On teste une modélisation bayésienne hiérarchique de la survie et de la "
                "réversion.",
        "comment": "On échantillonne le modèle bayésien et on évalue ses prédictions.",
        "resultats": "Le cadre bayésien est élégant mais n'apporte pas de gain net sur le "
                     "timing.",
        "conclusion": "Abandonné : la complexité bayésienne n'aide pas ici.",
    },
    # ---- Q6 : doser le risque (volatilité, support, drawdown) -----------------
    "EXT009_garch_egarch_volatility": {
        "sous_question": "Peut-on prévoir la volatilité (le niveau d'agitation du marché) mieux "
                         "qu'une simple moyenne récente ?",
        "fait": "On teste des modèles de volatilité (GARCH, EGARCH, GJR) pour prévoir l'agitation "
                "à venir du marché, qui sert à gérer le risque.",
        "comment": "On estime ces modèles sur les retours CBOT, en réestimant uniquement sur le "
                   "passé, et on compare leur erreur à une référence simple (la volatilité "
                   "récente).",
        "resultats": "L'EGARCH bat la référence de 24 % d'erreur ; surtout, dans les périodes de "
                     "volatilité prévue très haute, le signal directionnel s'inverse, donc "
                     "filtrer ces périodes améliore les décisions.",
        "conclusion": "Résultat gardé : la volatilité se prévoit, ce qui fournit un filtre de "
                      "risque actionnable.",
    },
    "EXT010_har_realized_volatility": {
        "sous_question": "Un modèle simple de volatilité (HAR) suffit-il à bien prévoir le "
                         "risque ?",
        "fait": "On teste le modèle HAR, simple et sans réglage, qui combine la volatilité "
                "récente sur plusieurs fenêtres (semaine, mois, trimestre).",
        "comment": "On régresse la volatilité future sur les volatilités passées 5/22/66 jours, "
                   "en réestimant sur le passé.",
        "resultats": "Le HAR bat la référence de 23 % d'erreur à tous les horizons : simple et "
                     "robuste. Contrairement au prix, la volatilité se prévoit bien.",
        "conclusion": "Résultat gardé : le HAR est le modèle de volatilité de référence pour le "
                      "risque.",
    },
    "test_ema_volatility.py": {
        "sous_question": "La volatilité du prix Euronext est-elle modélisable de la même "
                         "manière ?",
        "fait": "On étudie la volatilité du prix Euronext pour disposer d'une mesure de risque "
                "côté européen.",
        "comment": "On applique les approches de volatilité (récente, HAR) à la série Euronext.",
        "resultats": "La volatilité Euronext se modélise bien, utile comme mesure de risque "
                     "(mais pas pour prévoir le prix).",
        "conclusion": "Résultat gardé : mesure de risque disponible côté Euronext.",
    },
    "test_ema_volatility_v2.py": {
        "sous_question": "La modélisation de la volatilité Euronext tient-elle dans une version "
                         "améliorée ?",
        "fait": "On met à jour l'analyse de la volatilité Euronext pour la fiabiliser.",
        "comment": "On affine l'estimation et on vérifie la stabilité des prévisions de "
                   "volatilité.",
        "resultats": "La version 2 confirme une volatilité Euronext bien modélisable.",
        "conclusion": "Résultat gardé : version consolidée de la volatilité Euronext.",
    },
    "test_v41_cbot_support.py": {
        "sous_question": "Un 'support CBOT' (signe que le CBOT soutient les prix) réduit-il le "
                         "risque de mauvaise issue ?",
        "fait": "On construit un score de support CBOT, censé indiquer quand le CBOT protège la "
                "position contre une issue défavorable.",
        "comment": "On définit un indicateur binaire robuste de support et on mesure son effet "
                   "sur le risque ADVERSE et la performance.",
        "resultats": "Quand le support CBOT est présent, le risque ADVERSE est divisé par 2 et "
                     "la performance double ; la version graduée est plus bruitée.",
        "conclusion": "Résultat gardé : le support CBOT est un garde-fou de risque efficace.",
    },
    "test_v86_cbot_support_v2.py": {
        "sous_question": "Le score de support CBOT tient-il dans une version améliorée ?",
        "fait": "On améliore le score de support CBOT (calibration, robustesse).",
        "comment": "On affine la définition du support et on revalide son effet protecteur.",
        "resultats": "La version 2 conserve l'effet protecteur du support CBOT.",
        "conclusion": "Résultat gardé : version consolidée du support CBOT.",
    },
    "test_v23_cbot_risk_regime.py": {
        "sous_question": "Peut-on prévoir le risque de forte baisse (drawdown) du CBOT, et un "
                         "filtre de régime aide-t-il ?",
        "fait": "On teste la prévisibilité du risque de baisse (drawdown) du CBOT et l'utilité "
                "d'un filtre de régime de marché.",
        "comment": "On modélise le risque de baisse et on teste un conditionnement par régime.",
        "resultats": "Le risque de drawdown CBOT est prévisible (justesse AUC 0.74), mais le "
                     "filtre de régime est réfuté (il n'améliore pas).",
        "conclusion": "Étape : on sait mesurer le risque de baisse, mais sans gain via les "
                      "régimes.",
    },
    "test_roll_risk.py": {
        "sous_question": "Faut-il tenir compte des jours de roll dans le modèle de prime pour ne "
                         "pas confondre risque et artefact ?",
        "fait": "On construit un modèle de prime 'conscient du roll', qui évite de prendre un "
                "saut de raccord de contrat pour un vrai risque.",
        "comment": "On intègre l'information de roll au modèle de prime et on mesure l'effet.",
        "resultats": "Tenir compte du roll évite de fausses alertes de risque liées aux raccords "
                     "de contrats.",
        "conclusion": "Étape : fiabilise la mesure de risque en neutralisant l'effet des rolls.",
    },
    "test_v43_signal_quality.py": {
        "sous_question": "Peut-on noter la QUALITÉ d'un signal (sa fiabilité attendue) avant de "
                         "l'utiliser ?",
        "fait": "On construit une matrice de qualité du signal, qui évalue à l'avance la "
                "fiabilité d'un signal selon le contexte.",
        "comment": "On croise des critères (force, régime, fraîcheur, cohérence) pour attribuer "
                   "un niveau de qualité à chaque signal.",
        "resultats": "La matrice permet de doser la confiance : les signaux de meilleure qualité "
                     "sont plus fiables, ce qui rejoint la logique de paliers.",
        "conclusion": "Étape : fournit une mesure de confiance utile pour pondérer les "
                      "décisions.",
    },
    "test_barchart_contract_download_probe.py": {
        "sous_question": "Peut-on télécharger l'historique contrat par contrat chez Barchart pour densifier la courbe ?",
        "fait": "On sonde l'accès au téléchargement des contrats individuels chez le fournisseur Barchart.",
        "comment": "On teste l'endpoint de téléchargement avec une requête contrôlée, sans dépendre du réseau pendant le test (sonde isolée).",
        "resultats": "L'accès gratuit ne fournit pas l'historique complet par contrat : la source reste verrouillée pour l'usage visé.",
        "conclusion": "Piste de données fermée : on ne peut pas densifier la courbe par cette voie gratuite.",
    },
    "test_confidence_p_correct.py": {
        "sous_question": "Peut-on attacher à chaque signal une probabilité honnête d'avoir raison ?",
        "fait": "On calcule une probabilité de réussite (p_correct) associée au signal, comme mesure de confiance.",
        "comment": "On calibre la probabilité sur l'historique disponible et on vérifie qu'elle reste bornée et cohérente.",
        "resultats": "La probabilité fournit une graduation de confiance utilisable, mais reste tributaire d'un échantillon réduit.",
        "conclusion": "Confiance chiffrée disponible pour pondérer la décision, à confirmer en forward.",
    },
    "test_consensus.py": {
        "sous_question": "Un consensus d'analystes avant rapport apporte-t-il l'information de surprise qui nous manque ?",
        "fait": "On teste l'intégration d'un consensus de prévisions comme variable de surprise.",
        "comment": "On compare le signal avec et sans la composante consensus, sur la base disponible.",
        "resultats": "Sans véritable consensus historique gratuit, l'apport reste théorique et non démontré.",
        "conclusion": "Voie intéressante mais dépendante des données : la vraie surprise reste payante.",
    },
    "test_consensus_real.py": {
        "sous_question": "Avec un consensus réel, la qualité du signal s'améliore-t-elle ?",
        "fait": "On rejoue la logique de consensus sur les données réelles accessibles.",
        "comment": "On branche la source réelle quand elle existe et on mesure l'effet sur la discrimination.",
        "resultats": "Les données réelles gratuites sont trop partielles pour conclure à un gain net.",
        "conclusion": "Confirme la limite : sans archive de consensus, l'effet n'est pas validable.",
    },
    "test_curve_sign_audit.py": {
        "sous_question": "Le signe de la courbe (contango ou backwardation) est-il mesuré sans erreur de convention ?",
        "fait": "On audite le calcul du signe de la structure de courbe.",
        "comment": "On vérifie les conventions de signe sur des cas connus et on contrôle les inversions possibles.",
        "resultats": "L'audit valide la logique, mais l'historique de courbe officiel manque pour exploiter le signal.",
        "conclusion": "Mesure fiabilisée, exploitation bloquée par l'absence de données de courbe.",
    },
    "test_curve_spreads.py": {
        "sous_question": "Les écarts entre maturités (spreads) portent-ils une information exploitable ?",
        "fait": "On construit les spreads de courbe entre contrats successifs.",
        "comment": "On assemble les écarts par maturité quand des cotations existent.",
        "resultats": "L'historique gratuit par contrat est insuffisant pour estimer un signal stable.",
        "conclusion": "Piste bloquée par la donnée : la courbe complète est payante.",
    },
    "test_ema_continuous_series.py": {
        "sous_question": "Peut-on construire une série EMA continue propre à partir de contrats successifs ?",
        "fait": "On assemble une série Euronext continue en raccordant les contrats.",
        "comment": "On applique des règles de raccord et on vérifie l'absence de sauts artificiels au changement de contrat.",
        "resultats": "La série continue est cohérente et utilisable comme support d'étude.",
        "conclusion": "Brique de données validée : support continu pour les analyses EMA.",
    },
    "test_ema_continuous_series_probe.py": {
        "sous_question": "La densité de cotations suffit-elle pour une série continue de qualité production ?",
        "fait": "On sonde la couverture réelle des cotations EMA dans le temps.",
        "comment": "On mesure les trous et la fréquence effective des points disponibles.",
        "resultats": "La couverture gratuite reste lacunaire, surtout sur l'historique ancien.",
        "conclusion": "Qualité production non atteinte : la densité de donnée bloque l'usage strict.",
    },
    "test_ema_contract_reference.py": {
        "sous_question": "Quel contrat de référence choisir à chaque date pour représenter le marché EMA ?",
        "fait": "On définit le contrat de référence (le plus liquide, le front) par date.",
        "comment": "On applique une règle de sélection et on vérifie sa stabilité aux dates de roll.",
        "resultats": "La règle donne une référence claire et reproductible.",
        "conclusion": "Convention de référence fixée pour toutes les études EMA.",
    },
    "test_ema_contracts.py": {
        "sous_question": "Sait-on lire et structurer proprement l'ensemble des contrats EMA ?",
        "fait": "On charge et on structure le catalogue des contrats Euronext.",
        "comment": "On valide les identifiants de maturité, les unités et la cohérence des champs.",
        "resultats": "Le catalogue est exploitable et cohérent.",
        "conclusion": "Socle contractuel EMA en place.",
    },
    "test_ema_contracts_rolls.py": {
        "sous_question": "Les changements de contrat (rolls) sont-ils gérés sans fausser la série ?",
        "fait": "On gère les dates de roll entre contrats successifs.",
        "comment": "On teste les règles de bascule et l'ajustement éventuel au raccord.",
        "resultats": "Les rolls sont neutralisés : aucun saut artificiel n'est injecté dans la série.",
        "conclusion": "Gestion des rolls validée, prérequis pour des mesures fiables.",
    },
    "test_ema_contracts_v2.py": {
        "sous_question": "Une seconde version du chargement des contrats est-elle plus robuste ?",
        "fait": "On éprouve une version revue du module de contrats EMA.",
        "comment": "On compare la robustesse aux cas limites par rapport à la première version.",
        "resultats": "La v2 couvre mieux les cas particuliers de format.",
        "conclusion": "Chargement contractuel consolidé.",
    },
    "test_ema_curve_ablation.py": {
        "sous_question": "Retirer la courbe dégrade-t-il le signal (la courbe apporte-t-elle vraiment quelque chose) ?",
        "fait": "On teste l'apport de la courbe par ablation (avec et sans).",
        "comment": "On compare la performance du signal en retirant la composante courbe.",
        "resultats": "L'historique de courbe est trop limité pour trancher proprement.",
        "conclusion": "Apport de la courbe non démontrable faute de données.",
    },
    "test_ema_event_study.py": {
        "sous_question": "Comment se comporte la prime EMA autour des grands mouvements ?",
        "fait": "On mène une event study autour des fortes variations EMA.",
        "comment": "On aligne les épisodes et on observe le comportement moyen avant et après.",
        "resultats": "Les grands mouvements montrent un profil typique cohérent avec la compression de prime.",
        "conclusion": "Description fiable du déroulé typique, sans capacité prédictive nouvelle.",
    },
    "test_ema_event_study_v2.py": {
        "sous_question": "Une event study mieux alignée confirme-t-elle le profil ?",
        "fait": "On reprend l'event study avec un alignement et des intervalles plus stricts.",
        "comment": "On améliore le point d'ancrage et on ajoute des bornes de confiance.",
        "resultats": "Le profil typique se confirme avec une incertitude mieux quantifiée.",
        "conclusion": "Confirme la description, qui reste descriptive.",
    },
    "test_ema_manual_backfill_validator.py": {
        "sous_question": "Un backfill manuel de l'historique EMA est-il vérifiable et fiable ?",
        "fait": "On valide un remplissage manuel de l'historique Euronext.",
        "comment": "On contrôle les valeurs saisies contre des invariants et des points de référence.",
        "resultats": "Le validateur détecte les incohérences, mais l'historique reste partiel.",
        "conclusion": "Outil de contrôle prêt, donnée encore incomplète.",
    },
    "test_euronext_backfill.py": {
        "sous_question": "Peut-on compléter automatiquement l'historique Euronext disponible ?",
        "fait": "On automatise un backfill des cotations Euronext accessibles.",
        "comment": "On collecte et on insère les points manquants en respectant l'ordre temporel.",
        "resultats": "Le backfill densifie la série sur les périodes couvertes.",
        "conclusion": "Brique de complétion en place, dans la limite des sources gratuites.",
    },
    "test_euronext_continuous.py": {
        "sous_question": "La série Euronext continue est-elle stable d'un bout à l'autre ?",
        "fait": "On vérifie la continuité de la série Euronext assemblée.",
        "comment": "On contrôle l'absence de discontinuités et la bonne progression temporelle.",
        "resultats": "La série est continue et exploitable.",
        "conclusion": "Support Euronext continu validé.",
    },
    "test_euronext_curve.py": {
        "sous_question": "Peut-on reconstruire la courbe Euronext par maturité ?",
        "fait": "On tente la reconstruction de la courbe EMA.",
        "comment": "On rassemble les cotations par maturité disponibles.",
        "resultats": "Les cotations gratuites par maturité sont trop rares pour une courbe fiable.",
        "conclusion": "Reconstruction bloquée par la donnée.",
    },
    "test_euronext_endpoint_probe.py": {
        "sous_question": "Les points d'accès Euronext fournissent-ils assez de données utiles ?",
        "fait": "On sonde les endpoints Euronext accessibles.",
        "comment": "On teste les réponses sans dépendre du réseau pendant le test.",
        "resultats": "Les endpoints gratuits renvoient une couverture limitée.",
        "conclusion": "Accès donnée insuffisant : piste contrainte.",
    },
    "test_event_microstructure.py": {
        "sous_question": "La microstructure autour des événements ajoute-t-elle de l'information ?",
        "fait": "On examine le comportement fin (microstructure) autour des événements, en mode hors ligne.",
        "comment": "On rejoue des journaux d'événements mockés et on observe la dynamique courte.",
        "resultats": "La microstructure éclaire le déroulé mais n'offre pas d'avance exploitable gratuitement.",
        "conclusion": "Descriptif : pas de signal exploitable supplémentaire.",
    },
    "test_event_study.py": {
        "sous_question": "Le comportement de la prime autour des événements est-il systématique ?",
        "fait": "On réalise une event study sur la prime (premium).",
        "comment": "On agrège les fenêtres autour des événements identifiés.",
        "resultats": "On retrouve un profil moyen cohérent, sans pouvoir prédictif additionnel.",
        "conclusion": "Confirme la description du mécanisme, pas une prévision.",
    },
    "test_forward_milestones.py": {
        "sous_question": "Peut-on jalonner le suivi forward pour décider quand reconfirmer ?",
        "fait": "On pose des jalons (milestones) et un checkpoint forward conditionné.",
        "comment": "On déclenche les vérifications seulement quand assez de jours forward sont accumulés.",
        "resultats": "Les jalons cadencent le suivi sans décision prématurée.",
        "conclusion": "Cadence de validation forward outillée, prudente par construction.",
    },
    "test_indicator_confidence.py": {
        "sous_question": "Peut-on exprimer la confiance de l'indicateur de façon lisible ?",
        "fait": "On calcule un niveau de confiance global de l'indicateur.",
        "comment": "On combine plusieurs critères de fiabilité en un score lisible.",
        "resultats": "La confiance globale est cohérente avec la qualité des entrées.",
        "conclusion": "Confiance affichable pour l'utilisateur, à pondérer selon les données.",
    },
    "test_module_a.py": {
        "sous_question": "Le module de décision live (module A) produit-il un signal cohérent ?",
        "fait": "On teste le module A qui assemble le signal live.",
        "comment": "On vérifie les sorties sur des entrées contrôlées et les cas de bord.",
        "resultats": "Le module produit un signal stable et reproductible.",
        "conclusion": "Cœur de décision live opérationnel sur le plan logique.",
    },
    "test_module_a_calibration.py": {
        "sous_question": "Le module A est-il bien calibré (ses probabilités tiennent-elles) ?",
        "fait": "On calibre les sorties du module A.",
        "comment": "On compare les probabilités annoncées aux fréquences réellement observées.",
        "resultats": "La calibration est raisonnable sur l'échantillon, à surveiller hors échantillon.",
        "conclusion": "Calibration acceptable, validation forward nécessaire.",
    },
    "test_module_a_data_status.py": {
        "sous_question": "Le module A sait-il dire si ses données sont fraîches et suffisantes ?",
        "fait": "On contrôle l'état des données vu par le module A.",
        "comment": "On vérifie les drapeaux de fraîcheur et de complétude avant production du signal.",
        "resultats": "Le module signale correctement les données périmées ou manquantes.",
        "conclusion": "Garde-fou de données en place : pas de signal sur données périmées.",
    },
    "test_official_automation.py": {
        "sous_question": "Peut-on automatiser la collecte officielle sans casser l'anti-leakage ?",
        "fait": "On teste l'automation officielle (calendrier, sessions, proxy ou officiel).",
        "comment": "On vérifie le calendrier de marché, les ajouts append-only et la séparation proxy / officiel.",
        "resultats": "La collecte s'automatise en respectant les sessions et l'ordre temporel.",
        "conclusion": "Industrialisation de la collecte validée, sans tricher sur le temps.",
    },
    "test_official_proxy_validation.py": {
        "sous_question": "Le proxy colle-t-il assez au prix officiel pour être fiable ?",
        "fait": "On valide le proxy contre l'officiel par jalons.",
        "comment": "On compare proxy et officiel sur des fenêtres et des seuils figés à l'avance.",
        "resultats": "La validation par jalons mesure l'écart et déclenche les alertes utiles.",
        "conclusion": "Cadre de validation proxy / officiel en place.",
    },
    "test_proxy_forward_quote.py": {
        "sous_question": "Peut-on obtenir une cotation forward proxy fiable du contrat front officiel ?",
        "fait": "On teste l'obtention d'une quote proxy forward du front officiel.",
        "comment": "On injecte la récupération en test (hors ligne) et on contrôle la valeur.",
        "resultats": "La quote proxy reste dépendante d'une source officielle non garantie gratuitement.",
        "conclusion": "Voie partiellement bloquée par la disponibilité de la donnée officielle.",
    },
    "test_roll_season_backtest_v6.py": {
        "sous_question": "La saison de roll a-t-elle un effet exploitable, sans piège de version ?",
        "fait": "On backteste l'effet saisonnier des rolls (version 6).",
        "comment": "On mesure le rendement conditionnel à la fenêtre de roll, en évitant le piège de registre de version.",
        "resultats": "L'effet est faible et fragile, sensible aux choix de version.",
        "conclusion": "Pas d'avantage robuste de saison de roll : prudence.",
    },
    "test_session_timing.py": {
        "sous_question": "Sait-on distinguer un prix provisoire d'un prix de clôture définitif ?",
        "fait": "On gère le timing de session (provisoire, définitif, settlement officiel).",
        "comment": "On teste les états successifs autour de l'heure de settlement officielle.",
        "resultats": "Les états provisoire et définitif sont correctement séparés.",
        "conclusion": "Brique anti-leakage temporelle clé : on n'utilise jamais un provisoire comme définitif.",
    },
    "test_session_truth_v150.py": {
        "sous_question": "Peut-on garantir la vérité de session (champs obligatoires, précédence) au backfill ?",
        "fait": "On valide la vérité de session lors du backfill.",
        "comment": "On contrôle les champs obligatoires et les règles de précédence des valeurs.",
        "resultats": "Le contrôle empêche d'écrire des valeurs incohérentes ou prioritaires à tort.",
        "conclusion": "Intégrité de session garantie, support fiable pour le forward.",
    },
    "test_single_source_v152.py": {
        "sous_question": "Toutes les sorties live partent-elles bien d'une source unique cohérente ?",
        "fait": "On vérifie la cohérence de la source unique premium (head, dashboard, lifecycle).",
        "comment": "On contrôle que les artefacts dérivés reflètent la même source sans divergence.",
        "resultats": "Les sorties restent synchronisées sur une seule source de vérité.",
        "conclusion": "Source unique garantie : pas de contradiction entre tableaux de bord.",
    },
    "test_state_machine.py": {
        "sous_question": "Peut-on résumer l'état du marché de prime par une machine d'état lisible ?",
        "fait": "On construit une machine d'état de la prime (justifiée ou excessive, croisée avec l'avancement de compression).",
        "comment": "On définit les états et les transitions à partir de critères par règles, intégrés au head live.",
        "resultats": "La machine produit un état clair et stable, utilisé en live (HEALTHY, JUSTIFIED).",
        "conclusion": "Livrable gardé : synthèse d'état lisible et reproductible pour la décision.",
    },
    "test_state_transitions.py": {
        "sous_question": "Les transitions entre états se font-elles sans information future et de façon cohérente ?",
        "fait": "On teste les transitions de la machine d'état.",
        "comment": "On vérifie l'enchaînement des états sans utiliser d'information future.",
        "resultats": "Les transitions respectent l'ordre temporel et restent cohérentes.",
        "conclusion": "Logique d'état validée, conforme à l'anti-leakage.",
    },
    "test_v101_official_synthesis_fix.py": {
        "sous_question": "La synthèse officielle live est-elle correcte après correction ?",
        "fait": "On valide un correctif de la synthèse officielle live.",
        "comment": "On rejoue un journal mocké hors ligne et on vérifie la synthèse produite.",
        "resultats": "La synthèse corrigée reflète fidèlement l'état officiel.",
        "conclusion": "Synthèse live fiabilisée.",
    },
    "test_v102_active_signal_monitoring.py": {
        "sous_question": "Peut-on suivre dynamiquement un signal actif dans le temps ?",
        "fait": "On suit l'évolution d'un signal actif (monitoring dynamique).",
        "comment": "On met à jour l'état du signal au fil des jours sur un journal mocké.",
        "resultats": "Le suivi reflète l'avancement et la santé du signal en continu.",
        "conclusion": "Suivi dynamique opérationnel.",
    },
    "test_v103_proxy_official_dashboard.py": {
        "sous_question": "Peut-on présenter clairement proxy et officiel côte à côte ?",
        "fait": "On construit un dashboard proxy / officiel.",
        "comment": "On assemble les deux vues en lecture seule, hors ligne.",
        "resultats": "Le tableau distingue lisiblement proxy et officiel.",
        "conclusion": "Visualisation proxy / officiel disponible.",
    },
    "test_v107_live_context_refresh.py": {
        "sous_question": "Le contexte live se rafraîchit-il proprement à chaque mise à jour ?",
        "fait": "On teste le rafraîchissement du contexte live.",
        "comment": "On simule fetch et journal mockés et on vérifie la mise à jour.",
        "resultats": "Le contexte se met à jour sans incohérence.",
        "conclusion": "Rafraîchissement live fiable.",
    },
    "test_v108_live_basis_reconstruction.py": {
        "sous_question": "Peut-on reconstruire le basis en live et en déduire le risque ADVERSE ?",
        "fait": "On reconstruit le basis live et le risque ADVERSE associé.",
        "comment": "On rejoue fetch et journaux mockés et on calcule le basis et le risque.",
        "resultats": "La reconstruction live reproduit le basis et un risque cohérent.",
        "conclusion": "Basis et risque disponibles en live, en lecture seule.",
    },
    "test_v109_ema_curve_live_tension.py": {
        "sous_question": "La courbe EMA officielle live signale-t-elle une tension physique ?",
        "fait": "On teste la lecture de tension physique depuis la courbe EMA officielle live.",
        "comment": "On rejoue une courbe officielle hors ligne et on en déduit l'état de tension.",
        "resultats": "La logique fonctionne mais dépend d'une courbe officielle rarement disponible gratuitement.",
        "conclusion": "Lecture de tension prête, exploitation bloquée par la donnée de courbe.",
    },
    "test_v122_journal_consistency.py": {
        "sous_question": "Le journal de signaux est-il cohérent et ses révisions sont-elles tracées honnêtement ?",
        "fait": "On vérifie la cohérence du journal et la politique de révision auditée (provisoire, final, révisé).",
        "comment": "On contrôle que chaque révision est justifiée, datée et conserve l'historique.",
        "resultats": "Les révisions restent traçables : aucune valeur passée n'est réécrite en silence.",
        "conclusion": "Journal auditable garanti, base honnête du suivi forward.",
    },
    "test_v123_freshness_gate.py": {
        "sous_question": "Peut-on bloquer un signal dès qu'une couche de données est périmée ?",
        "fait": "On pose un gate de fraîcheur sur le contexte, couche par couche.",
        "comment": "On vérifie l'âge de chaque source et on dégrade le signal si une couche est trop ancienne.",
        "resultats": "Le signal passe en état dégradé quand la fraîcheur n'est pas garantie.",
        "conclusion": "Garde-fou de fraîcheur en place : pas de signal sur données dépassées.",
    },
    "test_v124_active_monitoring_v2.py": {
        "sous_question": "Peut-on suivre la santé d'un signal actif par paliers d'avancement ?",
        "fait": "On suit l'état du signal actif avec des statuts par paliers (10, 20, 30 jours).",
        "comment": "On classe l'avancement du signal en paliers et on actualise son statut.",
        "resultats": "Le suivi montre clairement où en est le signal dans son cycle.",
        "conclusion": "Suivi de santé par paliers opérationnel.",
    },
    "test_v125_curve_accumulation.py": {
        "sous_question": "Peut-on accumuler la courbe EMA dans le temps pour lire une tendance de tension ?",
        "fait": "On accumule les observations de courbe officielle et on en suit la tendance de tension.",
        "comment": "On empile les relevés disponibles et on calcule une tendance hors ligne.",
        "resultats": "La logique fonctionne mais l'historique de courbe officiel reste trop rare.",
        "conclusion": "Tendance de tension prête, exploitation bloquée par la donnée.",
    },
    "test_v128_intraday_aligned_probe.py": {
        "sous_question": "Une donnée intraday alignée améliorerait-elle la lecture forward ?",
        "fait": "On sonde un probe intraday CBOT aligné et l'accumulation forward.",
        "comment": "On teste l'alignement temporel d'une donnée intraday hors ligne.",
        "resultats": "L'intraday réellement utile est payant : le probe confirme l'intérêt mais pas l'accès gratuit.",
        "conclusion": "Piste intraday bloquée par le coût de la donnée.",
    },
    "test_v129_event_catalyst_library.py": {
        "sous_question": "Peut-on cataloguer les catalyseurs passés des épisodes de prime ?",
        "fait": "On construit un catalogue de catalyseurs (détection d'épisodes et classification).",
        "comment": "On identifie les épisodes et on leur attribue une cause dominante.",
        "resultats": "Le catalogue répartit les épisodes entre météo CBOT, bilan EU et détente de courbe, avec une part inconnue.",
        "conclusion": "Bibliothèque descriptive utile pour comprendre les causes, pas pour prédire.",
    },
    "test_v130_basis_regime_econometrics.py": {
        "sous_question": "La vitesse de retour du basis dépend-elle de l'intensité de l'écart ?",
        "fait": "On étudie l'économétrie du basis par régimes (synthétique, statsmodels).",
        "comment": "On estime la demi-vie de retour selon le niveau d'extrême de l'écart.",
        "resultats": "La demi-vie rétrécit quand l'écart est plus extrême : le retour est plus rapide en cas d'excès marqué.",
        "conclusion": "Découverte gardée : le basis revient plus vite quand il est le plus tendu.",
    },
    "test_v133_monthly_forward_report_v2.py": {
        "sous_question": "Peut-on produire un rapport forward mensuel lisible et reproductible ?",
        "fait": "On génère un rapport forward mensuel (version 2).",
        "comment": "On assemble les éléments du mois en lecture seule, hors ligne.",
        "resultats": "Le rapport synthétise l'avancement du mois de façon claire.",
        "conclusion": "Reporting mensuel outillé.",
    },
    "test_v134_data_sourcing_plan.py": {
        "sous_question": "Quelles données faudrait-il acquérir pour progresser, et lesquelles sont gratuites ?",
        "fait": "On formalise un plan de sourcing des données (statique).",
        "comment": "On liste les sources, leur statut gratuit ou payant, et leur priorité.",
        "resultats": "Le plan distingue clairement ce qui débloquerait l'étude et ce qui reste payant.",
        "conclusion": "Feuille de route données posée.",
    },
    "test_v135_decision_checkpoint.py": {
        "sous_question": "A-t-on accumulé assez de forward pour passer en décision réelle ?",
        "fait": "On évalue un checkpoint décisionnel sur les artefacts disponibles.",
        "comment": "On vérifie les conditions d'accumulation avant tout passage en usage.",
        "resultats": "Le checkpoint reste en mode analytique : pas encore de bascule en décision réelle.",
        "conclusion": "Prudence maintenue : l'étude reste analytique tant que le forward est insuffisant.",
    },
    "test_v137_event_date_attribution.py": {
        "sous_question": "Peut-on attribuer les épisodes à des dates de rapports USDA précises ?",
        "fait": "On attribue les épisodes par dates de rapports USDA (synthétique).",
        "comment": "On rapproche chaque épisode de la date du rapport correspondant.",
        "resultats": "L'attribution affine le catalogue, mais le recoupement mensuel est en partie mécanique.",
        "conclusion": "Raffinement descriptif, à interpréter avec prudence.",
    },
    "test_v138_horizon_estimator.py": {
        "sous_question": "La demi-vie de retour du niveau donne-t-elle le bon horizon de décision ?",
        "fait": "On construit un estimateur d'horizon à partir de la demi-vie de retour.",
        "comment": "On compare l'horizon analytique de demi-vie à l'horizon réellement observé sur les trades.",
        "resultats": "L'horizon analytique sous-estime nettement l'horizon réel : un facteur d'ordre trois sépare les deux.",
        "conclusion": "Falsification : la demi-vie de niveau n'est pas l'horizon de décision, à recaler.",
    },
    "test_v141_v142_forward.py": {
        "sous_question": "Peut-on valider en forward seulement quand les conditions sont réunies ?",
        "fait": "On teste la validation forward gatée (via journal mocké).",
        "comment": "On déclenche la validation uniquement quand les seuils d'accumulation sont atteints.",
        "resultats": "La validation ne se lance pas prématurément.",
        "conclusion": "Validation forward conditionnée, prudente.",
    },
    "test_v141_v142_forward_validation.py": {
        "sous_question": "Les validateurs forward de courbe et de MATIF se déclenchent-ils correctement ?",
        "fait": "On teste les validateurs forward (courbe et MATIF), conditionnés.",
        "comment": "On vérifie le déclenchement gated et le respect des données disponibles.",
        "resultats": "Les validateurs respectent les conditions et restent en attente quand la donnée manque.",
        "conclusion": "Validateurs forward outillés, data-gated.",
    },
    "test_v143_v145_v146.py": {
        "sous_question": "Peut-on enrichir le contexte, suivre le cycle de vie et l'afficher proprement ?",
        "fait": "On teste l'enrichissement (V143), le cycle de vie (V145) et le dashboard v4 (V146).",
        "comment": "On vérifie l'assemblage de ces briques en lecture seule.",
        "resultats": "Les trois briques produisent un contexte enrichi, suivi et présentable.",
        "conclusion": "Couche de présentation et de suivi consolidée.",
    },
    "test_v152_event_study.py": {
        "sous_question": "Une event study plus rigoureuse confirme-t-elle le profil des épisodes ?",
        "fait": "On mène une event study 2.0 (alignée sur le début d'épisode, intervalle bootstrap, censure).",
        "comment": "On ancre les épisodes au démarrage et on quantifie l'incertitude par bootstrap.",
        "resultats": "Le profil se confirme avec une incertitude honnête et une gestion des épisodes non terminés.",
        "conclusion": "Description robuste, qui reste descriptive.",
    },
    "test_v153_start_vs_inprogress.py": {
        "sous_question": "Peut-on étiqueter le début et le cours d'un épisode sans regarder le futur ?",
        "fait": "On pose des labels START et IN_PROGRESS sans lookahead.",
        "comment": "On définit les étiquettes à partir de l'information disponible à l'instant présent seulement.",
        "resultats": "Les labels restent valides en temps réel, sans information future.",
        "conclusion": "Étiquetage conforme à l'anti-leakage.",
    },
    "test_v161_import_parity.py": {
        "sous_question": "Le décodeur d'imports COMEXT respecte-t-il la parité et le délai de publication ?",
        "fait": "On teste la parité d'import COMEXT (décodeur JSON-stat et lag de publication).",
        "comment": "On vérifie le décodage et l'application du retard réel de publication.",
        "resultats": "Le décodeur reproduit les valeurs attendues et respecte le délai de disponibilité.",
        "conclusion": "Source COMEXT intégrée proprement, avec son délai réel.",
    },
    "test_v173_cost_grid.py": {
        "sous_question": "A quel niveau de coûts l'avantage disparaît-il selon le régime ?",
        "fait": "On construit une grille coûts et slippage par régime (frame synthétique hors ligne).",
        "comment": "On balaye les niveaux de coûts et on regarde où le résultat passe sous zéro.",
        "resultats": "L'avantage net est sensible aux coûts et s'efface vite hors des régimes favorables.",
        "conclusion": "Confirme le mur des coûts : l'avantage net est mince et conditionnel.",
    },
    "test_v177_data_gated_reruns.py": {
        "sous_question": "Peut-on relancer une analyse seulement quand assez de données neuves sont là ?",
        "fait": "On teste des gates de re-run data-gated (accumulation sous le seuil, déclenchement au seuil).",
        "comment": "On vérifie les états d'accumulation et de déclenchement selon la donnée disponible.",
        "resultats": "Les re-runs se déclenchent au bon moment et restent en attente sinon.",
        "conclusion": "Re-runs maîtrisés, sans recalcul prématuré.",
    },
    "test_v178_official_validation.py": {
        "sous_question": "Le proxy passe-t-il la validation 40 jours contre l'officiel ?",
        "fait": "On valide le proxy contre l'officiel sur 40 jours (gate, paires, seuils figés).",
        "comment": "On apparie proxy et officiel et on applique des seuils fixés à l'avance.",
        "resultats": "La validation mesure l'écart sur la fenêtre et tranche selon les seuils.",
        "conclusion": "Cadre de validation 40 jours en place.",
    },
    "test_v179_active_signal_report.py": {
        "sous_question": "Peut-on produire un rapport de signal actif fiable en lecture seule ?",
        "fait": "On génère un rapport de signal actif (assemblage en lecture seule, markdown).",
        "comment": "On assemble l'état courant sans modifier les sources.",
        "resultats": "Le rapport restitue l'état du signal de façon stable et reproductible.",
        "conclusion": "Reporting de signal actif outillé.",
    },
    "test_v180_dashboard_v5.py": {
        "sous_question": "Peut-on distinguer clairement un signal de référence d'un signal confirmé ?",
        "fait": "On construit le dashboard v5 (référence contre confirmé, lecture seule).",
        "comment": "On présente côte à côte le signal de référence et sa version confirmée.",
        "resultats": "Le tableau distingue lisiblement les deux niveaux de confiance.",
        "conclusion": "Visualisation v5 disponible.",
    },
    "test_v181_weekly_maintenance.py": {
        "sous_question": "Peut-on automatiser les contrôles de maintenance hebdomadaire ?",
        "fait": "On teste la maintenance hebdomadaire (checks individuels et verdict global).",
        "comment": "On enchaîne les contrôles et on agrège un verdict d'ensemble.",
        "resultats": "La maintenance produit un état de santé clair chaque semaine.",
        "conclusion": "Routine de maintenance outillée.",
    },
    "test_v22_live_stabilization.py": {
        "sous_question": "Le pipeline live tient-il quand une source manque ou est périmée ?",
        "fait": "On teste la stabilisation live (gate de fraîcheur et classification des pièges).",
        "comment": "On simule des données manquantes ou périmées et on observe la dégradation.",
        "resultats": "Le pipeline passe en état prudent au lieu d'émettre un signal trompeur.",
        "conclusion": "Stabilité live assurée face aux données manquantes.",
    },
    "test_v24_data_forensic.py": {
        "sous_question": "Les données de base résistent-elles à un audit forensique ?",
        "fait": "On mène un audit forensique (logique sur données synthétiques et invariants).",
        "comment": "On vérifie des invariants attendus et la cohérence de bout en bout.",
        "resultats": "L'audit confirme la cohérence des données reconstruites.",
        "conclusion": "Intégrité des données validée.",
    },
    "test_v26_official_ema.py": {
        "sous_question": "Sait-on parser le settlement officiel Euronext et en valider les niveaux ?",
        "fait": "On teste le parser officiel Euronext et la validation des niveaux (hors ligne).",
        "comment": "On décode les settlements officiels et on compare les niveaux aux références.",
        "resultats": "Les niveaux officiels valident l'ordre de grandeur des niveaux proxy.",
        "conclusion": "Parser officiel validé, niveaux proxy confirmés.",
    },
    "test_v27_official_forward.py": {
        "sous_question": "Peut-on suivre le forward officiel en append-only sans réécrire le passé ?",
        "fait": "On teste le forward tracking officiel et le journal append-only.",
        "comment": "On vérifie que chaque ajout s'empile sans modifier les entrées passées.",
        "resultats": "Le journal officiel s'accumule proprement, sans réécriture.",
        "conclusion": "Suivi forward officiel honnête, append-only garanti.",
    },
    "test_v30_official_curve.py": {
        "sous_question": "Peut-on lire la structure de courbe officielle (contango ou backwardation) ?",
        "fait": "On teste la lecture de structure de courbe officielle.",
        "comment": "On décode les maturités officielles disponibles et on classe la structure.",
        "resultats": "La logique fonctionne mais l'historique de courbe officiel reste insuffisant.",
        "conclusion": "Lecture prête, exploitation bloquée par la donnée.",
    },
    "test_v31_forward_dashboard.py": {
        "sous_question": "Peut-on présenter le suivi forward de la prime dans un tableau de bord ?",
        "fait": "On construit un dashboard forward de la prime (hors ligne).",
        "comment": "On assemble l'historique forward en lecture seule.",
        "resultats": "Le tableau restitue le suivi forward de façon lisible.",
        "conclusion": "Visualisation forward disponible.",
    },
    "test_v35_cbot_engine.py": {
        "sous_question": "Le mécanisme de compression piloté par le CBOT est-il prévisible ?",
        "fait": "On teste un moteur de compression CBOT (hors ligne, master synthétique).",
        "comment": "On tente de prévoir le mécanisme de compression à partir des entrées disponibles.",
        "resultats": "La prévision du mécanisme reste au niveau du hasard : le moteur ne discrimine pas.",
        "conclusion": "Falsification : le mécanisme de compression n'est pas prévisible.",
    },
    "test_v39_enrichment.py": {
        "sous_question": "Des variables d'enrichissement améliorent-elles le signal de risque ?",
        "fait": "On lance un batch d'expériences d'enrichissement (hors ligne, master synthétique).",
        "comment": "On teste plusieurs variables candidates (tendance CBOT, COT, paliers, éthanol, stocks US).",
        "resultats": "Une tendance CBOT haussière divise le risque ADVERSE par deux, mais éthanol et stocks US apportent peu sur le basis EU.",
        "conclusion": "Quelques enrichissements utiles gardés, le reste confirme la prime locale.",
    },
    "test_v46_settlement_alignment.py": {
        "sous_question": "Les settlements CBOT et EMA sont-ils alignés sur les bonnes dates ?",
        "fait": "On teste l'alignement de settlement CBOT et EMA (hors ligne, master synthétique).",
        "comment": "On vérifie la correspondance temporelle des clôtures des deux marchés.",
        "resultats": "L'alignement évite de comparer des clôtures décalées.",
        "conclusion": "Alignement temporel validé, prérequis pour comparer les deux marchés.",
    },
    "test_v47_objective_choice.py": {
        "sous_question": "Faut-il viser un retour complet (z vers 0) ou partiel (z vers 0.5) ?",
        "fait": "On compare deux objectifs de sortie : retour à z vers 0.5 et retour à z vers 0.",
        "comment": "On évalue les deux cibles sur le master synthétique.",
        "resultats": "La sortie partielle évite des pertes en queue sans sacrifier l'essentiel du gain.",
        "conclusion": "Objectif partiel retenu comme défaut prudent.",
    },
    "test_v59_monthly_forward_report.py": {
        "sous_question": "Peut-on produire un premier rapport forward mensuel ?",
        "fait": "On génère un rapport forward mensuel (journaux synthétiques).",
        "comment": "On assemble l'activité du mois en lecture seule.",
        "resultats": "Le rapport synthétise l'avancement mensuel.",
        "conclusion": "Première version du reporting mensuel en place.",
    },
    "test_v71_eu_production_balance.py": {
        "sous_question": "Le bilan de production européen aide-t-il à expliquer le basis EU ?",
        "fait": "On construit un bilan physique EU à partir de la production EC MARS (fetch mocké).",
        "comment": "On rapproche la production européenne du comportement du basis.",
        "resultats": "Le bilan apporte un éclairage physique, sans pouvoir prédictif fort sur le basis.",
        "conclusion": "Contexte physique utile, pas un signal prédictif.",
    },
    "test_v71b_eu_production_locality.py": {
        "sous_question": "La localisation géographique de la production EU compte-t-elle pour le basis ?",
        "fait": "On teste la localité géographique de la production EU (hors ligne, fetch mocké).",
        "comment": "On distingue les zones de production et on regarde leur lien avec le basis.",
        "resultats": "La dimension locale confirme le caractère régional de la prime européenne.",
        "conclusion": "Renforce la thèse d'une prime locale, sans signal exploitable direct.",
    },
    "test_v81_robustness_audit.py": {
        "sous_question": "Les résultats tiennent-ils quand on perturbe les choix méthodologiques ?",
        "fait": "On mène un audit de robustesse (hors ligne).",
        "comment": "On fait varier les paramètres et les fenêtres et on observe la stabilité des conclusions.",
        "resultats": "Les conclusions principales résistent aux variations raisonnables.",
        "conclusion": "Robustesse confirmée sur les résultats clés.",
    },
    "test_v82_episode_library.py": {
        "sous_question": "Peut-on constituer une bibliothèque d'épisodes de référence ?",
        "fait": "On construit une bibliothèque d'épisodes (hors ligne, sans réseau).",
        "comment": "On répertorie les épisodes passés avec leurs caractéristiques.",
        "resultats": "La bibliothèque sert de référence pour comparer les épisodes futurs.",
        "conclusion": "Catalogue d'épisodes disponible pour l'analyse.",
    },
    "test_weekly_report.py": {
        "sous_question": "Peut-on produire un rapport hebdomadaire de suivi ?",
        "fait": "On génère un rapport hebdomadaire de suivi.",
        "comment": "On assemble l'état de la semaine en lecture seule.",
        "resultats": "Le rapport restitue l'activité de la semaine de façon claire.",
        "conclusion": "Reporting hebdomadaire outillé.",
    },
    "EXT005_futures_curve_spreads": {
        "sous_question": "Les spreads de courbe futures portent-ils une information de carry exploitable ?",
        "fait": "On explore les spreads de courbe futures et le carry.",
        "comment": "On assemble les écarts entre maturités quand des données existent.",
        "resultats": "L'historique de courbe nécessaire est bloqué : le carry n'est pas estimable proprement.",
        "conclusion": "Piste de carry bloquée par l'absence de données de courbe.",
    },
    "test_deep_learning.py": {
        "sous_question": "Un réseau de neurones profond bat-il les modèles simples sur ce problème ?",
        "fait": "On entraîne des modèles d'apprentissage profond sur les données disponibles.",
        "comment": "On compare leur erreur à celle de la random walk et des modèles simples.",
        "resultats": "Le réseau profond ne bat pas la random walk et se montre instable sur si peu de données.",
        "conclusion": "Abandonné : trop de paramètres pour trop peu de données, aucun gain.",
    },
    "test_dim_reduction.py": {
        "sous_question": "Réduire la dimension des variables aide-t-il le modèle ?",
        "fait": "On applique une réduction de dimension aux variables.",
        "comment": "On compare les performances avec et sans réduction.",
        "resultats": "La réduction ne change pas significativement le résultat.",
        "conclusion": "Pas de gain net : variable de confort, pas de levier.",
    },
    "test_ema_feature_importance.py": {
        "sous_question": "Quelles variables pèsent le plus dans la dynamique EMA ?",
        "fait": "On mesure l'importance des variables pour l'EMA.",
        "comment": "On classe les variables selon leur contribution au modèle.",
        "resultats": "Quelques variables de marché dominent, le reste apporte peu.",
        "conclusion": "Hiérarchie des variables clarifiée pour l'EMA.",
    },
    "test_ema_feature_importance_v2.py": {
        "sous_question": "Une mesure d'importance plus robuste confirme-t-elle le classement ?",
        "fait": "On reprend l'importance des variables EMA avec une méthode plus robuste.",
        "comment": "On recalcule l'importance et on compare au classement précédent.",
        "resultats": "Le classement se confirme dans l'ensemble.",
        "conclusion": "Importance des variables stabilisée.",
    },
    "test_ema_feature_selector.py": {
        "sous_question": "Peut-on sélectionner automatiquement un sous-ensemble utile de variables ?",
        "fait": "On teste un sélecteur de variables pour l'EMA.",
        "comment": "On retient les variables les plus informatives et on évalue le modèle réduit.",
        "resultats": "Le modèle réduit garde l'essentiel de la performance avec moins de variables.",
        "conclusion": "Sélection utile pour simplifier sans perdre.",
    },
    "test_ema_relative_feature_importance.py": {
        "sous_question": "L'importance relative des variables change-t-elle selon le contexte ?",
        "fait": "On mesure l'importance relative des variables EMA.",
        "comment": "On compare les contributions normalisées entre elles.",
        "resultats": "Les contributions relatives confirment la domination de quelques variables.",
        "conclusion": "Vue relative cohérente avec la vue absolue.",
    },
    "test_meta_model_premium_v6.py": {
        "sous_question": "Un méta-modèle combinant plusieurs signaux fait-il mieux sur la prime ?",
        "fait": "On teste un méta-modèle de prime (version 6).",
        "comment": "On combine plusieurs signaux et on évalue le résultat agrégé.",
        "resultats": "Le méta-modèle n'apporte pas de gain robuste sur la prime.",
        "conclusion": "Pas d'avantage net : la combinaison ne surpasse pas les briques simples.",
    },
    "test_multiple_testing.py": {
        "sous_question": "Combien de nos résultats survivent à la correction pour tests multiples ?",
        "fait": "On applique une correction pour tests multiples et un verrou de holdout.",
        "comment": "On ajuste les seuils de significativité au nombre d'essais menés.",
        "resultats": "Beaucoup d'effets apparents ne survivent pas à la correction.",
        "conclusion": "Discipline statistique appliquée : on écarte les résultats dus au hasard.",
    },
    "test_overfitting_v172.py": {
        "sous_question": "Nos stratégies sont-elles surajustées (PSR, DSR, PBO) ?",
        "fait": "On évalue le surajustement avec des mesures dédiées (PSR, DSR, PBO).",
        "comment": "On teste la probabilité que la performance vienne du hasard ou de l'optimisation.",
        "resultats": "Les mesures signalent un risque de surajustement élevé sur les stratégies complexes.",
        "conclusion": "Avertissement gardé : préférer le simple, se méfier des performances flatteuses.",
    },
    "test_red_team_validation.py": {
        "sous_question": "Une analyse adverse arrive-t-elle à casser nos conclusions ?",
        "fait": "On soumet les résultats à une validation en équipe adverse (red team).",
        "comment": "On cherche activement les failles et les biais des conclusions.",
        "resultats": "La revue adverse fragilise les résultats les plus optimistes.",
        "conclusion": "Conclusions recentrées sur ce qui résiste à la critique.",
    },
    "test_seasonal_experts.py": {
        "sous_question": "Des modèles saisonniers spécialisés améliorent-ils la prévision ?",
        "fait": "On teste des modèles saisonniers experts.",
        "comment": "On spécialise des modèles par saison et on compare au modèle global.",
        "resultats": "La saisonnalité aide modestement mais ne change pas l'ordre des conclusions.",
        "conclusion": "Apport saisonnier limité, déjà capté par les variables de saison.",
    },
    "test_stacking.py": {
        "sous_question": "Empiler plusieurs modèles (stacking) bat-il la random walk ?",
        "fait": "On teste un empilement de modèles (stacking).",
        "comment": "On combine les sorties de plusieurs modèles par un méta-apprenant.",
        "resultats": "Le stacking ne bat pas la random walk en erreur.",
        "conclusion": "Abandonné : la complexité n'apporte pas de gain prédictif.",
    },
    "test_v164_hmm.py": {
        "sous_question": "Un modèle de Markov caché identifie-t-il utilement le régime ou le début d'épisode ?",
        "fait": "On teste un HMM pour les régimes et la triangulation du début d'épisode.",
        "comment": "On estime les états cachés et on regarde leur valeur pour le timing.",
        "resultats": "Le HMM ne fournit pas de timing fiable du début d'épisode.",
        "conclusion": "Abandonné pour le timing : pas de gain par rapport aux règles simples.",
    },
    "test_v170_causal_dag.py": {
        "sous_question": "Un graphe causal clarifie-t-il les effets réels entre variables ?",
        "fait": "On construit un graphe causal et on applique la d-séparation et le critère back-door.",
        "comment": "On classe les effets et on cherche les chemins de confusion.",
        "resultats": "Le graphe structure le raisonnement mais ne débloque pas de prévision exploitable.",
        "conclusion": "Cadre causal utile à la compréhension, pas un levier prédictif.",
    },
    "test_v171_placebo.py": {
        "sous_question": "L'avantage du basis EMA est-il spécifique ou apparaît-il aussi sur des témoins ?",
        "fait": "On mène un test placebo : on compare l'avantage du basis EMA à des spreads témoins.",
        "comment": "On rejoue la même logique sur des séries témoins sans lien attendu.",
        "resultats": "Une partie de l'effet apparaît aussi sur les témoins, ce qui fragilise sa spécificité.",
        "conclusion": "Avertissement : l'avantage n'est pas aussi spécifique qu'espéré, prudence.",
    },
    "test_v172_overfit_on_trades.py": {
        "sous_question": "Les trades simulés résistent-ils au pack anti-surajustement ?",
        "fait": "On branche le pack anti-surajustement sur les trades simulés réels.",
        "comment": "On applique PSR, DSR et PBO directement aux résultats de trades.",
        "resultats": "Les mesures confirment un risque de surajustement sur les stratégies actives.",
        "conclusion": "Confirme la prudence : ne pas surinterpréter les backtests flatteurs.",
    },
    "EXT007_wasde_release_features": {
        "sous_question": "Les variables construites autour des publications WASDE aident-elles la direction ?",
        "fait": "On construit des variables à partir des dates de publication WASDE.",
        "comment": "On encode l'effet des publications et on teste leur apport directionnel.",
        "resultats": "Ces variables apportent un signal directionnel utile et robuste.",
        "conclusion": "Gardé : les publications WASDE nourrissent le score de direction.",
    },
    "EXT008_wasde_surprise_proxy": {
        "sous_question": "Un proxy de surprise WASDE sans consensus capte-t-il l'information ?",
        "fait": "On construit un proxy de surprise WASDE par les révisions, sans consensus.",
        "comment": "On approxime la surprise par les révisions successives faute de consensus.",
        "resultats": "Le proxy ne capte pas la vraie surprise et reste peu informatif.",
        "conclusion": "Abandonné : sans consensus, la surprise WASDE n'est pas reconstituable.",
    },
    "EXT011_trend_following_benchmark": {
        "sous_question": "Une stratégie de suivi de tendance bat-elle la référence ?",
        "fait": "On teste un benchmark de suivi de tendance.",
        "comment": "On compare son rendement net à la référence simple.",
        "resultats": "Le suivi de tendance ne bat pas la référence après coûts.",
        "conclusion": "Abandonné comme stratégie autonome.",
    },
    "EXT012_ou_mean_reversion_benchmark": {
        "sous_question": "Un modèle de retour à la moyenne (OU) apporte-t-il un avantage exploitable ?",
        "fait": "On teste un benchmark de retour à la moyenne de type Ornstein-Uhlenbeck.",
        "comment": "On calibre le modèle sur les données disponibles.",
        "resultats": "Les données nécessaires sont insuffisantes pour valider l'avantage.",
        "conclusion": "Bloqué par la donnée : avantage non démontrable.",
    },
    "EXT014_bayesian_model_averaging": {
        "sous_question": "Moyenner plusieurs modèles à la manière bayésienne stabilise-t-il la prévision ?",
        "fait": "On teste une moyenne de modèles de type bayésien.",
        "comment": "On pondère les modèles selon leur vraisemblance et on agrège.",
        "resultats": "La moyenne stabilise un peu mais n'apporte pas de gain décisif.",
        "conclusion": "Confort méthodologique, pas un levier de performance.",
    },
    "EXT015_shap_feature_selection": {
        "sous_question": "Une sélection de variables par importance (sur l'entraînement seul) est-elle propre et utile ?",
        "fait": "On sélectionne les variables par importance, calculée sur l'entraînement seulement.",
        "comment": "On classe les variables sans utiliser le test, pour éviter la fuite.",
        "resultats": "La sélection retient des variables pertinentes sans fuite de données.",
        "conclusion": "Gardé : méthode de sélection propre, intégrée au pipeline.",
    },
    "EXT016_nbeatsx_exogenous_model": {
        "sous_question": "Un modèle profond à variables exogènes (NBEATSx) bat-il la référence ?",
        "fait": "On teste le modèle NBEATSx avec variables exogènes.",
        "comment": "On compare son erreur à la random walk.",
        "resultats": "Le modèle ne bat pas la random walk et reste coûteux à entraîner.",
        "conclusion": "Abandonné : pas de gain face au modèle naïf.",
    },
    "EXT017_market_regime_detection": {
        "sous_question": "Peut-on détecter le régime de marché pour doser la confiance ?",
        "fait": "On détecte le régime de marché (calme ou tendu, haussier ou baissier).",
        "comment": "On classe les périodes en régimes à partir de la volatilité et de la tendance.",
        "resultats": "Les régimes aident à moduler la confiance accordée au signal.",
        "conclusion": "Gardé : utilisé pour pondérer la décision, pas pour prédire le prix.",
    },
    "EXT019_crop_condition_report_features": {
        "sous_question": "Les notes de condition des cultures aident-elles la direction à 90 jours ?",
        "fait": "On construit des variables à partir des rapports de condition des cultures.",
        "comment": "On encode l'évolution des conditions et on teste l'apport directionnel à H90.",
        "resultats": "Ces variables apportent un signal directionnel utile à horizon long.",
        "conclusion": "Gardé : pilier du score de direction à 90 jours.",
    },
    "EXT024_var_supply_demand_benchmark": {
        "sous_question": "Un modèle d'offre et de demande donne-t-il une bonne direction ?",
        "fait": "On teste un benchmark directionnel offre et demande.",
        "comment": "On relie les variables de bilan à la direction des prix.",
        "resultats": "Le benchmark fournit une direction utile et cohérente économiquement.",
        "conclusion": "Gardé : référence directionnelle économiquement fondée.",
    },
    "EXT050_model_stacking_ensemble": {
        "sous_question": "Un ensemble empilé de modèles surpasse-t-il les briques simples ?",
        "fait": "On teste un ensemble par empilement de modèles.",
        "comment": "On combine plusieurs modèles et on évalue l'ensemble.",
        "resultats": "L'ensemble ne surpasse pas durablement les briques simples.",
        "conclusion": "Abandonné : la complexité d'ensemble n'apporte pas de gain net.",
    },
    "test_cbot_sale_score.py": {
        "sous_question": "Le score de vente CBOT est-il configurable et reproductible ?",
        "fait": "On teste la configuration et la reproductibilité du score de vente CBOT.",
        "comment": "On vérifie que les mêmes entrées donnent les mêmes sorties et que la configuration est respectée.",
        "resultats": "Le score est reproductible et se paramètre proprement.",
        "conclusion": "Gardé : livrable final stable et reproductible.",
    },
    "test_cbot_sale_score_leakage.py": {
        "sous_question": "Le score de vente est-il garanti sans fuite de données future ?",
        "fait": "On teste l'anti-fuite du score de vente CBOT.",
        "comment": "On vérifie que les cibles et les variables respectent l'ordre temporel (shift et date cible corrects).",
        "resultats": "Aucune fuite détectée : le score n'utilise que l'information passée.",
        "conclusion": "Gardé : anti-leakage validé sur le livrable final.",
    },
    "test_cbot_sale_score_outputs.py": {
        "sous_question": "Les sorties du score (vente partielle, attente, risque élevé) sont-elles bien formées ?",
        "fait": "On teste les sorties du score de vente CBOT.",
        "comment": "On vérifie le format, les bornes et la cohérence des recommandations produites.",
        "resultats": "Les sorties sont bien formées et cohérentes (jamais de short ni de levier).",
        "conclusion": "Gardé : interface de sortie fiable pour l'utilisateur.",
    },
    "test_euronext_indicator.py": {
        "sous_question": "L'indicateur Euronext se charge-t-il proprement et sans fuite ?",
        "fait": "On teste le chargement, la date cible et l'anti-fuite de l'indicateur Euronext.",
        "comment": "On vérifie le calcul de la date cible et l'absence d'information future.",
        "resultats": "L'indicateur se charge correctement et respecte l'anti-leakage.",
        "conclusion": "Gardé : socle de l'indicateur Euronext validé.",
    },
    "test_euronext_indicator_backtest.py": {
        "sous_question": "Le backtest agricole Euronext reste-t-il réaliste (pas de short, vente totale bornée) ?",
        "fait": "On teste le backtest agricole de l'indicateur Euronext.",
        "comment": "On vérifie l'absence de short et d'achat, et que la vente cumulée reste bornée.",
        "resultats": "Le backtest respecte les contraintes d'un agriculteur réel.",
        "conclusion": "Gardé : backtest réaliste, sans comportement de trading interdit.",
    },
    "test_euronext_indicator_dashboard.py": {
        "sous_question": "Le dashboard Euronext est-il autonome et sans image générée ?",
        "fait": "On teste la génération du dashboard Euronext.",
        "comment": "On vérifie que le HTML est créé, autonome et sans image externe.",
        "resultats": "Le dashboard est autonome et interactif, sans image générée.",
        "conclusion": "Gardé : visualisation Euronext conforme à la demande.",
    },
}


# --- arbre flowchart HTML (chips cliquables + résumé/analyse par couche) -------
def _detail_html(r: dict) -> str:
    if r["fichier"] in CURATED:
        c = CURATED[r["fichier"]]
        sq = (f"<p class='sq'><b>Sous-question :</b> {clean(c['sous_question'])}</p>"
              if c.get("sous_question") else "")
        secs = (("1. Ce qu'on fait dans ce test", c["fait"]),
                ("2. Comment on l'a fait (méthode et données)", c["comment"]),
                ("3. Résultats et analyse", c["resultats"]),
                ("4. Conclusion du test", c["conclusion"]))
        inner = "".join(f"<p class='sec'>{t}</p>{clean(txt)}" for t, txt in secs)
        return (f"<h3>{r['fichier']}</h3>"
                f"<p class='vd'>{clean(CATLABEL[r['verdict']])}</p>{sq}{inner}")
    q = r["question"]
    cat = clean(CATLABEL[r["verdict"]])
    doc = clean(r.get("detail_doc") or r["description"] or "")
    # 1. Ce qu'on fait = 1re-2e phrase de la docstring (le but du test) ; sinon nom + objectif
    sentences = [s.strip() for s in doc.split(". ") if s.strip()]
    what = ". ".join(sentences[:2]) if sentences else clean(r["fichier"].replace("_", " "))
    if what and not what.endswith("."):
        what += "."
    how = ". ".join(sentences[2:]).strip()
    how = (how + (". " if how and not how.endswith(".") else " ")) if how else ""
    how += "Données mobilisées dans cette étape : " + clean(QDATA[q])
    res = clean(result_text(r["fichier"], r["verdict"]))
    conclu = clean(CONCLU[r["verdict"]])
    return (f"<h3>{r['fichier']}</h3>"
            f"<p class='vd'>{cat}</p>"
            f"<p class='sec'>1. Ce qu'on fait dans ce test</p>{what}"
            f"<p class='sec'>2. Comment on l'a fait (méthode et données)</p>{how}"
            f"<p class='sec'>3. Résultats et analyse</p>{res}"
            f"<p class='sec'>4. Conclusion du test</p>{conclu}")


def build_flowchart_html(rows: list[dict]):
    by_q: dict[str, list[dict]] = {q: [] for q in QORDER}
    for r in rows:
        by_q.setdefault(r["question"], []).append(r)
    details = {r["fichier"]: _detail_html(r) for r in rows}
    blocks = []
    for qid in QORDER:
        files = sorted(by_q.get(qid, []), key=lambda r: (r["verdict"], r["fichier"]))
        chips = "".join(
            f"<span class='chip' data-f=\"{r['fichier']}\" style='background:{CHIP[r['verdict']]}'>"
            f"{r['fichier']}</span>" for r in files)
        frm = f"<span class='from'>vient de {QFROM[qid]}</span>" if qid in QFROM else ""
        nkeep = sum(r["verdict"] == "gardé" for r in files)
        ndead = sum(r["verdict"] == "abandonné" for r in files)
        blocks.append(
            f"<div class='layer'><div class='qbox'>{frm}<b>{qid}</b> : {clean(QTEXT[qid])}"
            f"<span class='count'>{len(files)} fichiers, {nkeep} gardes, {ndead} abandonnes</span>"
            f"</div><div class='resume'>{clean(QRESUME[qid])}</div>"
            f"<div class='chips'>{chips}</div>"
            f"<div class='analyse'><b>Analyse :</b> {clean(QANALYSE[qid])}</div></div>")
    concl = "".join(
        f"<li class='h'>{clean(c)}</li>" if c.rstrip().endswith(":") else f"<li>{clean(c)}</li>"
        for c in CONCLUSION)
    legend = ("<span class='lg' style='background:#1f3b6f;color:#fff'>Question</span>"
              + "".join(f"<span class='lg' style='background:{CHIP[k]};color:#fff'>{CATLABEL[k]}</span>"
                        for k in ("gardé", "abandonné", "bloqué", "outil", "exploration"))
              + " &nbsp; <i>(cliquer un fichier pour son detail complet)</i>")
    style = """
    body{font-family:sans-serif;margin:20px;max-width:1180px;background:#f4f6f9}
    h1{text-align:center}.sub{text-align:center;color:#555}
    .qbox{background:#1f3b6f;color:#fff;padding:10px 14px;border-radius:8px;font-size:15px;position:relative}
    .from{position:absolute;right:12px;top:-9px;font-size:11px;background:#e8eaf0;color:#1f3b6f;
      padding:1px 6px;border-radius:6px}
    .count{float:right;font-size:11px;opacity:.9;font-weight:normal}
    .resume{background:#eef2fb;border-left:4px solid #5b7fc4;padding:6px 12px;margin:4px 0;font-size:13px}
    .analyse{background:#fff;border-left:4px solid #1f3b6f;padding:6px 12px;margin:4px 0;font-size:13px}
    .chips{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}
    .chip{color:#fff;font-size:10px;padding:2px 6px;border-radius:5px;cursor:pointer}
    .chip:hover{outline:2px solid #1f3b6f}
    .layer{margin:0 0 18px;padding-bottom:10px;border-bottom:1px dashed #c4ccd8}
    .lg{padding:3px 8px;border-radius:5px;margin-right:6px;font-size:12px;display:inline-block;margin-bottom:3px}
    .concl{background:#e7f6e7;border:2px solid #2ca02c;border-radius:10px;padding:12px 22px;margin-top:8px}
    .concl li.h{font-weight:bold;list-style:none;margin:10px 0 2px -22px;color:#176217}
    #panel{position:fixed;top:0;right:0;width:400px;max-width:92vw;height:100%;background:#fff;
      box-shadow:-2px 0 14px rgba(0,0,0,.25);padding:16px 18px;overflow:auto;transform:translateX(100%);
      transition:.25s;z-index:50;font-size:13px;line-height:1.45}
    #panel.open{transform:translateX(0)}#panel h3{margin:24px 0 6px;word-break:break-all;color:#1f3b6f}
    #panel .vd{color:#444;font-weight:bold}
    #panel .sec{font-weight:bold;color:#1f3b6f;margin:13px 0 2px;border-bottom:1px solid #e0e4ee}
    #panel .sq{background:#fff7e6;border-left:4px solid #e8943a;padding:7px 11px;margin:8px 0;font-style:italic}
    #close{position:absolute;top:8px;right:12px;border:none;background:#eee;
      border-radius:6px;padding:4px 10px;cursor:pointer}
    """
    script = ("const D=" + json.dumps(details, ensure_ascii=False) + ";"
              "function hide(){document.getElementById('panel').classList.remove('open');}"
              "document.addEventListener('DOMContentLoaded',function(){"
              "document.querySelectorAll('.chip').forEach(function(c){"
              "c.addEventListener('click',function(){"
              "document.getElementById('pbody').innerHTML=D[c.dataset.f]||c.dataset.f;"
              "document.getElementById('panel').classList.add('open');});});});")
    body = (f"<h1>Cheminement de l'étude</h1><p>{legend}</p>"
            + "".join(blocks)
            + f"<div class='concl'><b>Conclusion de l'étude</b><ul>{concl}</ul></div>"
            + "<div id='panel'><button id='close' onclick='hide()'>fermer</button>"
              "<div id='pbody'></div></div>")
    html = (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
            f"<title>Cheminement de l'étude</title><style>{style}</style></head>"
            f"<body>{body}<script>{script}</script></body></html>")
    (OUT / "arbre_etude.html").write_text(html, encoding="utf-8")


def write_ascii_doc(rows: list[dict]):
    by_q: dict[str, list[dict]] = {}
    for r in rows:
        by_q.setdefault(r["question"], []).append(r)
    legend = ", ".join(f"{MARK[k]} {clean(CATLABEL[k].split(' ', 1)[1])}" for k in MARK)
    lines = ["# Cheminement de l'étude maïs", "",
             f"Légende : {legend}. Tous les fichiers de l'étude sont rattachés à la question "
             f"qu'ils ont servi à répondre (aucun oublié). Version interactive (détail au clic) "
             f": `artefacts/rapport_etude/arbre_etude.html`.", ""]
    for qid in QORDER:
        files = sorted(by_q.get(qid, []), key=lambda r: (r["verdict"], r["fichier"]))
        frm = f"  (vient de {QFROM[qid]})" if qid in QFROM else ""
        lines.append(f"## {qid} : {clean(QTEXT[qid])}{frm}")
        lines.append(clean(QRESUME[qid]))
        lines.append(f"_{len(files)} fichiers :_")
        lines += [f"- {MARK[r['verdict']]} `{r['fichier']}` : {clean(r['description'])}"
                  for r in files]
        lines.append(f"Analyse : {clean(QANALYSE[qid])}")
        lines.append("")
    lines.append("## Conclusion de l'étude")
    lines += [f"- {clean(c)}" for c in CONCLUSION]
    (DOCS / "ARBRE_ETUDE.md").write_text("\n".join(lines), encoding="utf-8")


def _page(dest: Path, title: str, subtitle: str, body: str):
    html = (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{title}</title>"
            f"<script>{get_plotlyjs()}</script>"
            f"<style>body{{font-family:sans-serif;margin:24px;max-width:1200px}}</style></head>"
            f"<body><h1>{title}</h1><p>{subtitle}</p>{body}</body></html>")
    dest.write_text(html, encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = collect()
    # couverture : tout fichier doit avoir une question connue
    bad = [r["fichier"] for r in rows if r["question"] not in QORDER]
    assert not bad, f"fichiers sans question : {bad[:5]}"
    with (OUT / "inventaire_tests.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["fichier", "type", "question", "verdict", "description"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    build_flowchart_html(rows)
    write_ascii_doc(rows)
    build_perf_html()
    by_v: dict[str, int] = {}
    by_q: dict[str, int] = {}
    for r in rows:
        by_v[r["verdict"]] = by_v.get(r["verdict"], 0) + 1
        by_q[r["question"]] = by_q.get(r["question"], 0) + 1
    print(f"{len(rows)} fichiers tracés (aucun oublié)")
    print("par verdict:", by_v)
    print("par question:", {q: by_q.get(q, 0) for q in QORDER})


if __name__ == "__main__":
    main()
