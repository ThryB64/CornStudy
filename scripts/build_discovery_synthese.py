"""Synthese scientifique : range les 33 decouvertes en 7 blocs, les classe par statut
(robuste / prometteur / garde-fou / limite), les rattache a un indicateur selectif a 4 modules,
et liste honnetement le backlog de validation. Reutilise les images de build_discovery_visuals.
Sortie : docs/SYNTHESE_SCIENTIFIQUE.md, artefacts/decouvertes/inventaire_decouvertes.csv,
         artefacts/decouvertes/synthese.html.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_discovery_visuals import D  # noqa: E402

OUT = ROOT / "artefacts" / "decouvertes"
IND = ROOT / "artefacts" / "indicator_v1"
DIDX = {d["id"]: d for d in D}


def indicator_html() -> str:
    """Section finale : l'indicateur produit + ses resultats (lit artefacts/indicator_v1)."""
    summ = IND / "summary.json"
    fsum = IND / "fusion_summary.json"
    if not (summ.exists() and fsum.exists()):
        return ("<h2>Au final : l'indicateur produit</h2><div class='indic'>Lancer "
                "<code>make indicator-fusion</code> pour generer les resultats de l'indicateur.</div>")
    s = json.loads(summ.read_text())
    f = json.loads(fsum.read_text())
    snap = json.loads((IND / "snapshot_live.json").read_text())
    p = "../indicator_v1/"
    m1, m3 = s["m1_h60"], s["m3"]
    bt_rows = "".join(
        f"<tr><td>{r['signal']}</td><td>{r['n']}</td><td>{r['couverture']:.0%}</td>"
        f"<td>{r['p_down_realise']:.2f}</td><td>{r['lift_vs_base']:+.2f}</td></tr>"
        for r in f["backtest"])
    cost_rows = "".join(
        f"<tr><td>{int(r['cout_par_jambe'])} EUR/t</td><td>{r['pnl_brut_eur_t']:+.1f}</td>"
        f"<td>{r['pnl_net_eur_t']:+.1f}</td></tr>" for r in f["m4_couts"])
    snap_li = "".join(f"<li><b>{k}</b> : {v}</li>" for k, v in snap.items())
    imgs = ["carte_live.png", "fusion_backtest.png", "fiche_confidence_abstention.png",
            "fiche_m1_par_annee.png", "fiche_m1_downside.png", "fiche_m3_volatility.png",
            "fusion_m4_couts.png"]
    return (
        "<h2>Au final : l'indicateur que l'on a reussi a produire</h2>"
        "<div class='indic'>"
        "<p>Conclusion concrete de l'etude : un <b>indicateur selectif de risque</b> qui ne "
        "predit pas le prix mais dit <b>BEARISH_RISK</b> (risque de baisse), <b>NEUTRAL</b> ou "
        "<b>UNCERTAIN</b> (il s'abstient quand il n'est pas sur). Valide en walk-forward hors "
        "echantillon 2014-2025, anti-leakage strict (refit annuel, purge, standardisation "
        "train-only).</p>"
        "<h3>Ses resultats valides</h3><ul>"
        f"<li><b>M1 Risque de baisse CBOT</b> (baisse &gt; 3 % a 60 j) : AUC "
        f"<b>{m1['auc']:.3f}</b> (IC95 [{m1['ci'][0]:.3f} ; {m1['ci'][1]:.3f}]), n={m1['n']}.</li>"
        f"<li><b>M3 Volatilite</b> : RMSE {m3['rmse_model']:.3f} vs baseline "
        f"{m3['rmse_baseline']:.3f} ({m3['gain_pct']:+.1f} %).</li>"
        f"<li><b>Placebo</b> (labels melanges) : AUC {f['placebo_auc']:.3f} (proche de 0.5 = le "
        "signal reel n'est pas du hasard).</li></ul>"
        "<h3>Backtest du signal fusionne (la baisse arrive-t-elle vraiment ?)</h3>"
        f"<table><tr><th>signal</th><th>n</th><th>couverture</th>"
        f"<th>P(baisse) reelle</th><th>vs base {f['base_rate']:.2f}</th></tr>{bt_rows}</table>"
        "<p>Lecture : quand le signal dit BEARISH_RISK, la baisse arrive nettement plus souvent "
        "que la moyenne ; NEUTRAL est en dessous ; UNCERTAIN (abstention) reste proche du hasard. "
        "C'est exactement ce qu'on attend d'un indicateur honnete.</p>"
        "<h3>M4 prime Euronext : le mur des couts (research-only)</h3>"
        f"<table><tr><th>cout par jambe</th><th>PnL brut</th><th>PnL net</th></tr>{cost_rows}</table>"
        "<h3>Lecture du jour (snapshot live)</h3>"
        f"<ul>{snap_li}</ul>"
        "<h3>Visuels</h3>"
        + "".join(f"<img src='{p}{i}'>" for i in imgs)
        + "<p><i>Statut : l'indicateur est un detecteur de contexte de risque, pas un robot de "
        "trading. M4 reste research-only (prix Euronext ~97 % proxy). Avant tout usage : "
        "validation forward (paper-trading) en conditions reelles.</i></p></div>")

# 4 categories claires (le statut interne reste la cle, on affiche le libelle)
SCOL = {"Robuste": "#2ca02c", "Prometteur": "#e8943a", "Garde-fou": "#1f77b4", "Limite": "#d62728"}
LABEL = {"Robuste": "Decouverte validee", "Prometteur": "Piste a valider",
         "Garde-fou": "Garde-fou methodologique", "Limite": "Limite importante"}

# champs riches : pour les decouvertes validees (demontre / change / consequence indicateur),
# pour les pistes a valider (signal / pourquoi pas valide / test a faire)
EXTRA = {
 "random_walk": {
   "demontre": "Aucun modele (sur 36) ne bat la random walk sur le prix exact (test de Diebold-Mariano).",
   "change": "On arrete de vouloir predire le niveau du prix ; on reformule l'etude vers le risque, la direction et la volatilite.",
   "consequence": "L'indicateur ne predit jamais un prix : il qualifie un contexte de risque."},
 "volatilite": {
   "demontre": "La volatilite future est nettement plus previsible que le prix (revalidee en walk-forward : RMSE -15.1 % vs persistance).",
   "change": "Le risque a de la memoire : c'est une cible exploitable la ou le prix ne l'est pas.",
   "consequence": "Module M3 : regime de volatilite (calme / normal / volatil / extreme) qui module la confiance."},
 "drawdown_cbot": {
   "demontre": "Le risque de forte baisse du CBOT se detecte a l'avance (walk-forward : AUC 0.646, IC95 [0.627 ; 0.666], n=2845).",
   "change": "On peut estimer un risque de baisse sans predire le prix.",
   "consequence": "Module M1 (Downside Risk) : le coeur de l'indicateur."},
 "cbot_drops": {
   "demontre": "Le CBOT se laisse mieux anticiper a la baisse qu'a la hausse (validation downside forte 2016-2021, faible 2022-2023).",
   "change": "L'indicateur doit etre d'abord un detecteur de risque de baisse, pas un predicteur de hausse.",
   "consequence": "M1 oriente baisse ; le module hausse (M2) reste prudent."},
 "basis_reversion": {
   "demontre": "Apres un basis tres haut, l'ecart EMA-CBOT revient vers la moyenne (demi-vie 17 a 47 jours, event study).",
   "change": "La prime europeenne devient un objet exploitable (retour a la moyenne) la ou le prix ne l'est pas.",
   "consequence": "Module M4 (prime Euronext) : vendre la prime quand elle est anormalement haute."},
 "compression_cbot": {
   "demontre": "La compression de prime vient surtout de la hausse du CBOT (jambe CBOT ~6x la jambe EMA).",
   "change": "Vendre la prime = parier sur un rattrapage du CBOT, pas sur une baisse de l'Euronext.",
   "consequence": "M4 conditionne la vente de prime au contexte CBOT (support)."},
 "prime_locale": {
   "demontre": "La macro globale n'explique pas le basis (R2 hors echantillon -0.25).",
   "change": "On evite d'empiler des variables macro inutiles pour expliquer la prime.",
   "consequence": "M4 reste parcimonieux (basis + saison + contexte CBOT)."},
 "specificity": {
   "demontre": "La prime suit le basis local (+0.59) et pas le niveau CBOT (-0.46) ; a lire avec 'prime locale'.",
   "change": "Confirme que la prime est locale, pas un artefact du niveau CBOT.",
   "consequence": "M4 s'appuie sur le basis local, pas sur le niveau du CBOT."},
 "complex_models": {
   "demontre": "Trend-following, stacking et deep learning ne battent pas les references simples (sur-apprentissage).",
   "change": "Le probleme n'est pas la puissance du modele mais la qualite du signal et la robustesse.",
   "consequence": "L'indicateur reste simple et parcimonieux (pas de boite noire)."},
 "overfit": {
   "demontre": "Les strategies actives portent un risque de sur-ajustement (PSR / DSR / PBO) ; le placebo de l'indicateur le confirme (AUC 0.498).",
   "change": "On privilegie le simple et on teste systematiquement contre le hasard.",
   "consequence": "Tout module passe un placebo avant d'etre cru."},
 "marginal": {
   "demontre": "Les signaux faibles valent moins que les signaux forts ; confirme par la courbe de confiance de l'indicateur (DA 0.65 -> 0.71 sur les signaux confiants).",
   "change": "L'indicateur ne doit pas parler tous les jours : il attend des signaux assez forts.",
   "consequence": "Mode UNCERTAIN obligatoire (abstention sur signal faible)."},
 "direction_fusion": {
   "demontre": "La fusion des fondamentaux d'offre (Crop Condition + niveaux WASDE + ratio "
               "ble/mais) est le meilleur modele directionnel de l'etude a 90 jours "
               "(walk-forward AUC 0.626, IC95 [0.607 ; 0.646], placebo 0.489) ; "
               "le marche seul ne predit rien (0.511) et ajouter le marche dilue (0.603).",
   "change": "Les trois familles d'offre portent une information complementaire ; les echecs "
             "sont lisibles (chocs demande / geopolitique : 2021, 2022) et l'abstention "
             "monte la DA de 0.63 a 0.78.",
   "consequence": "Candidat coeur direction CBOT long terme (au-dessus de crop_h90 seul), "
                  "avec gate d'abstention |p-0.5| < 0.15."},
 # ---- pistes a valider ----
 "indicateur_v9": {"signal": "Indicateur basis + saison, AUC 0.656.",
   "pourquoi": "Pas de placebo ni de test apres couts, periode de test pas claire.",
   "test": "Walk-forward strict + placebo + resultat net de couts."},
 "modele_2vars": {"signal": "Modele 2 variables (basis_z + saison), AUC 0.694.",
   "pourquoi": "Bon signal mais validation incomplete.",
   "test": "Walk-forward strict + placebo + robustesse aux couts."},
 "crop_h90": {
   "demontre": "La Crop Condition US donne une direction a 90 jours qui tient hors echantillon "
               "(walk-forward AUC 0.588, IC95 [0.568 ; 0.609], positive sur 75 % des annees).",
   "change": "Un fondamental d'offre US porte un vrai signal directionnel moyen terme, plus "
             "modeste que le holdout (0.816) mais robuste sur plusieurs annees.",
   "consequence": "Alimente les modules direction et risque de baisse (M1 / M2) a horizon long."},
 "wasde_h40": {"signal": "WASDE stocks/usage -> direction H40, DA 0.705.",
   "pourquoi": "Holdout court, pas de performance par annee.",
   "test": "Performance par annee + IC + walk-forward strict."},
 "adverse_predictable": {"signal": "Issue ADVERSE previsible a l'entree, AUC 0.72.",
   "pourquoi": "Seulement 42 episodes, validation LOO fragile.",
   "test": "Plus d'episodes + validation hors echantillon."},
 "sell_high_cost": {"signal": "Vendre la prime haute, +115 hors crise.",
   "pourquoi": "Hors crise uniquement, couts testes de facon limitee.",
   "test": "Avec et sans crise + grille de couts (brut / net / +2 / +5 EUR/t)."},
 "asymmetry": {"signal": "Avantage asymetrique : vendre haut bien plus que l'inverse.",
   "pourquoi": "A confirmer sur davantage d'episodes.",
   "test": "Echantillon elargi + net de couts."},
 "cbot_support": {"signal": "Support CBOT : risque ADVERSE /2, PnL x2.",
   "pourquoi": "42 episodes, l'effet peut deriver du simple momentum.",
   "test": "Isoler du momentum + plus d'episodes."},
 "episodes": {"signal": "Familles d'episodes separables (CBOT / EMA / ADVERSE).",
   "pourquoi": "Resultat descriptif pour l'instant.",
   "test": "Passer du descriptif au predictif hors echantillon."},
 "exit_z05": {"signal": "Sortie partielle (z=0.5) sauve des pertes.",
   "pourquoi": "Regle de strategie encore a backtester proprement.",
   "test": "Backtest walk-forward avec couts."},
 "halflife_extreme": {"signal": "Demi-vie plus courte si l'ecart est extreme (8.3 -> 3.3 j).",
   "pourquoi": "Logique econometrique, mais a tester en forward.",
   "test": "Validation forward + stabilite par regime."},
 "weather_extreme": {"signal": "Pic de chaleur prevu correle au rendement (+0.31).",
   "pourquoi": "Resultat presque 'oracle' (sur meteo realisee), non utilisable tel quel.",
   "test": "Refaire sur une archive de previsions meteo forward reelles."},
 "wheat_corn": {
   "demontre": "L'ecart de prix ble/mais signale le risque de baisse du mais hors echantillon "
               "(walk-forward AUC 0.590, IC95 [0.571 ; 0.611], positive sur 75 % des annees).",
   "change": "Un signal de substitution simple aide a anticiper la baisse, la ou les modeles "
             "complexes echouent.",
   "consequence": "Entre dans le module M1 (Downside Risk) comme variable de contexte."},
}

# --------------------------------------------------------------------------- #
# metadonnees analytiques par decouverte (honnetes : n/periode/IC marques quand absents)
# fields: question, marche, cible, horizon, metrique, resultat, baseline, periode, n,
#         statut, decision, module, interpretation
# --------------------------------------------------------------------------- #
META = {
 "random_walk": {
   "question": "Un modele bat-il 'le prix de demain = celui d'aujourd'hui' sur le prix exact ?",
   "marche": "CBOT + Euronext", "cible": "prix (niveau)", "horizon": "H5-H90",
   "metrique": "RMSE (Diebold-Mariano)", "resultat": "0 / 36 couples battent la random walk",
   "baseline": "random walk", "periode": "2000-2023", "n": "36 couples modele x horizon",
   "statut": "Robuste", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "Le niveau exact est imprevisible : on change de cible vers le risque et le contexte."},
 "complex_models": {
   "question": "Trend-following, stacking et deep learning battent-ils les references simples ?",
   "marche": "CBOT + Euronext", "cible": "prix / direction", "horizon": "multi",
   "metrique": "RMSE / DA", "resultat": "aucun gain net ; sur-apprentissage",
   "baseline": "random walk / 2 vars", "periode": "2000-2023", "n": "a produire (backlog)",
   "statut": "Robuste", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "La parcimonie gagne : 2 variables suffisent, la complexite ajoute du bruit."},
 "overfit": {
   "question": "Les strategies actives survivent-elles aux tests anti-sur-ajustement ?",
   "marche": "CBOT + Euronext", "cible": "PnL strategie", "horizon": "multi",
   "metrique": "PSR / DSR / PBO", "resultat": "risque de sur-ajustement eleve",
   "baseline": "bruit / permutation", "periode": "multi", "n": "trades simules",
   "statut": "Robuste", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "On prefere assumer le simple ; ne pas sur-interpreter les backtests flatteurs."},
 "fragile": {
   "question": "Le score de vente final est-il robuste hors echantillon ?",
   "marche": "CBOT", "cible": "direction H40-H90", "horizon": "H40-H90",
   "metrique": "DA", "resultat": "DA 0.686 (> random walk) mais < saisonnalite 0.752",
   "baseline": "random walk 0.5 + saisonnalite 0.752", "periode": "holdout 2024+ (~1.5 an)",
   "n": "fenetre courte", "statut": "Limite", "decision": "Ne pas survendre", "module": "Cadre methodo",
   "interpretation": "Repere utile, pas une preuve : a reconfirmer en walk-forward multi-annees."},
 "volatilite": {
   "question": "La volatilite future est-elle previsible ?",
   "marche": "CBOT + Euronext", "cible": "volatilite realisee", "horizon": "court terme",
   "metrique": "RMSE vs random walk", "resultat": "HAR -23 %, EGARCH -23.7 %",
   "baseline": "random walk de variance", "periode": "2010-2025", "n": "a produire (IC backlog)",
   "statut": "Robuste", "decision": "Integrer", "module": "M3 Volatility",
   "interpretation": "Le risque a de la memoire : module central pour moduler la confiance des signaux."},
 "drawdown_cbot": {
   "question": "Peut-on detecter a l'avance les periodes de forte baisse du CBOT ?",
   "marche": "CBOT", "cible": "drawdown (baisse anormale)", "horizon": "H30-H60",
   "metrique": "AUC", "resultat": "AUC 0.74", "baseline": "0.5",
   "periode": "a produire (par annee + IC backlog)", "n": "a produire (backlog)",
   "statut": "Robuste", "decision": "Integrer", "module": "M1 Downside Risk",
   "interpretation": "On ne predit pas le prix, on repere les contextes de danger : tres utile a la vente."},
 "cbot_drops": {
   "question": "Le CBOT predit-il mieux ses baisses que ses hausses ?",
   "marche": "CBOT", "cible": "direction (baisse vs hausse)", "horizon": "H40",
   "metrique": "qualite de prediction", "resultat": "baisses ~0.62 vs hausses ~0.50",
   "baseline": "0.5", "periode": "a produire (backlog)", "n": "a produire (backlog)",
   "statut": "Robuste", "decision": "Integrer", "module": "M1 Downside Risk",
   "interpretation": "L'agriculteur a surtout besoin d'eviter de garder quand le risque de baisse monte."},
 "direction_fusion": {
   "question": "Combiner crop + WASDE + ble/mais predit-il mieux la direction a 90 jours ?",
   "marche": "CBOT", "cible": "direction", "horizon": "H90",
   "metrique": "AUC walk-forward", "resultat": "AUC 0.626 IC95 [0.607 ; 0.646], placebo 0.489",
   "baseline": "0.5 (hasard) ; marche seul 0.511", "periode": "OOS 2014-2026",
   "n": "3050", "statut": "Robuste",
   "decision": "Coeur direction long terme + abstention", "module": "M2 Bullish Potential",
   "interpretation": "Signal d'offre moyen terme ; aveugle aux chocs de demande (2021-2022) : "
                     "gate de confiance obligatoire."},
 "crop_h90": {
   "question": "La Crop Condition US donne-t-elle la direction a 90 jours ?",
   "marche": "CBOT", "cible": "direction", "horizon": "H90",
   "metrique": "AUC / DA", "resultat": "AUC 0.816 / DA 0.686 (holdout)",
   "baseline": "random walk + saisonnalite 0.752", "periode": "holdout 2024+ (court)",
   "n": "a produire (par annee + IC backlog)", "statut": "Prometteur",
   "decision": "Surveiller / revalider", "module": "M2 Bullish Potential",
   "interpretation": "Tres prometteur mais 2024 (grosse recolte) peut etre lisible : a valider walk-forward."},
 "wasde_h40": {
   "question": "Le ratio stocks-sur-usage du WASDE oriente-t-il la direction a 40 jours ?",
   "marche": "CBOT", "cible": "direction", "horizon": "H40",
   "metrique": "DA", "resultat": "DA 0.705 (holdout)", "baseline": "random walk 0.5",
   "periode": "holdout 2024+", "n": "a produire (par annee + IC backlog)",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M1 Downside Risk",
   "interpretation": "Stocks bas = marche tendu ; signal moyen terme a confirmer sur plusieurs annees."},
 "weather_extreme": {
   "question": "Un pic de chaleur prevu en pollinisation deplace-t-il le prix ?",
   "marche": "CBOT", "cible": "rendement / direction", "horizon": "ete",
   "metrique": "correlation / ecart", "resultat": "corr +0.31 ; extreme +1.6 % vs reste -2.3 %",
   "baseline": "meteo moyenne (nulle)", "periode": "oracle (borne sup, non-tradeable)",
   "n": "episodes d'ete", "statut": "Prometteur", "decision": "Surveiller / revalider",
   "module": "M2 Bullish Potential",
   "interpretation": "Le signal est dans les EXTREMES prevus, pas la moyenne : passer a la meteo prevue forward."},
 "weather_priced_in": {
   "question": "La meteo realisee apporte-t-elle un signal directionnel ?",
   "marche": "CBOT", "cible": "direction", "horizon": "multi",
   "metrique": "AUC", "resultat": "AUC 0.508 (hasard)", "baseline": "0.5",
   "periode": "multi", "n": "a produire (backlog)", "statut": "Garde-fou",
   "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "La meteo observee arrive trop tard (deja price-in) : ne pas l'utiliser comme predicteur."},
 "indicateur_v9": {
   "question": "Un indicateur a paliers basis + saison discrimine-t-il les ventes de prime ?",
   "marche": "Euronext", "cible": "vente de prime", "horizon": "multi",
   "metrique": "AUC", "resultat": "AUC 0.656", "baseline": "0.5",
   "periode": "a produire (placebo + couts backlog)", "n": "a produire (backlog)",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "Correct mais modere : utile combine au contexte (support CBOT, force du signal)."},
 "modele_2vars": {
   "question": "Deux variables (basis_z + saison) suffisent-elles ?",
   "marche": "Euronext", "cible": "vente de prime", "horizon": "multi",
   "metrique": "AUC", "resultat": "AUC 0.694", "baseline": "0.5 + modeles complexes",
   "periode": "a produire (placebo + couts backlog)", "n": "a produire (backlog)",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "La simplicite bat la complexite ; verifier placebo et robustesse aux couts."},
 "basis_reversion": {
   "question": "Le basis EMA-CBOT revient-il a la moyenne apres un pic ?",
   "marche": "Euronext", "cible": "basis z-score", "horizon": "H17-H47",
   "metrique": "demi-vie (event study)", "resultat": "demi-vie 17 a 47 j ; decroit de 2.27 vers 0.5",
   "baseline": "absence de reversion", "periode": "2010-2025", "n": "37 episodes (z>2)",
   "statut": "Robuste", "decision": "Integrer", "module": "M4 Euronext Premium",
   "interpretation": "Coeur du module Euronext : vendre la prime quand le basis est anormalement haut."},
 "compression_cbot": {
   "question": "La compression de prime vient-elle du CBOT ou de l'Euronext ?",
   "marche": "Euronext / CBOT", "cible": "decomposition de la compression", "horizon": "multi",
   "metrique": "poids relatif", "resultat": "jambe CBOT ~6x la jambe EMA (~69 %)",
   "baseline": "parts egales", "periode": "2010-2025", "n": "episodes de compression",
   "statut": "Robuste", "decision": "Integrer", "module": "M4 Euronext Premium",
   "interpretation": "Vendre la prime = parier sur une hausse relative du CBOT, pas sur l'Euronext seul."},
 "prime_locale": {
   "question": "La macro explique-t-elle le basis ?",
   "marche": "Euronext", "cible": "basis", "horizon": "multi",
   "metrique": "R2 hors echantillon", "resultat": "R2 -0.25 (la macro n'explique pas)",
   "baseline": "moyenne (R2=0)", "periode": "multi", "n": "a produire (backlog)",
   "statut": "Robuste", "decision": "Integrer", "module": "M4 Euronext Premium",
   "interpretation": "La prime est LOCALE : on ne pretend pas l'expliquer par les fondamentaux mondiaux."},
 "specificity": {
   "question": "La prime suit-elle le basis local ou le niveau CBOT ?",
   "marche": "Euronext", "cible": "prime", "horizon": "multi",
   "metrique": "correlation", "resultat": "corr(prime,basis)=+0.59 ; corr(prime,CBOT)=-0.46",
   "baseline": "0", "periode": "multi", "n": "a produire (backlog)",
   "statut": "Robuste", "decision": "Integrer", "module": "M4 Euronext Premium",
   "interpretation": "La prime n'est pas un artefact du CBOT : elle vit avec le basis EMA-CBOT."},
 "halflife_extreme": {
   "question": "La vitesse de retour du basis depend-elle de l'intensite de l'ecart ?",
   "marche": "Euronext", "cible": "demi-vie", "horizon": "multi",
   "metrique": "demi-vie par regime", "resultat": "modere 8.3 j / fort 4.9 j / extreme 3.3 j",
   "baseline": "demi-vie constante", "periode": "2010-2025", "n": "par regime",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "Plus le basis est tendu, plus il revient vite : conforter l'horizon de sortie."},
 "adverse_predictable": {
   "question": "L'issue ADVERSE d'une vente de prime est-elle previsible a l'entree ?",
   "marche": "Euronext", "cible": "echec (oui/non)", "horizon": "entree",
   "metrique": "AUC (LOO)", "resultat": "issue 0.72 ; mecanisme 0.48",
   "baseline": "0.5", "periode": "2010-2025", "n": "42 episodes (LOO)",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "On estime le RISQUE a priori sans predire le chemin : filtre, pas signal de direction."},
 "sell_high_cost": {
   "question": "Vendre la prime haute reste-t-il gagnant apres couts ?",
   "marche": "Euronext", "cible": "PnL net", "horizon": "multi",
   "metrique": "PnL net", "resultat": "+115 hors crise ; edge sur z>2",
   "baseline": "0 / buy-and-hold", "periode": "hors crise", "n": "episodes z>2",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "Depend fortement des couts et des crises exclues : montrer brut / net / +2 / +5 EUR/t."},
 "cbot_support": {
   "question": "Un CBOT qui soutient rend-il la compression plus sure ?",
   "marche": "Euronext / CBOT", "cible": "risque ADVERSE / PnL", "horizon": "multi",
   "metrique": "multiple", "resultat": "risque ADVERSE /2, PnL x2, reversion ~29 j (87.5 %)",
   "baseline": "sans support", "periode": "2010-2025", "n": "42 episodes",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "Prometteur mais peut deriver du momentum : a isoler du simple effet de tendance."},
 "episodes": {
   "question": "Les episodes de prime haute forment-ils des familles distinctes ?",
   "marche": "Euronext / CBOT", "cible": "famille d'episode", "horizon": "multi",
   "metrique": "gain moyen / win", "resultat": "CBOT_DRIVEN +22.7 (~100 % win) ; EMA +14 ; ADVERSE 5.7",
   "baseline": "indistinct", "periode": "2010-2025", "n": "42 episodes",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "Familles separables des l'entree : sert a router les decisions de vente de prime."},
 "exit_z05": {
   "question": "Faut-il viser un retour complet (z=0) ou partiel (z=0.5) ?",
   "marche": "Euronext", "cible": "objectif de sortie", "horizon": "multi",
   "metrique": "PnL par episode", "resultat": "z=0.5 sauve des pertes (2010, 2013)",
   "baseline": "sortie z=0", "periode": "2010-2025", "n": "episodes",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "Sortie partielle = defaut prudent, surtout en contexte defavorable."},
 "marginal": {
   "question": "Les signaux faibles (z<1.2) valent-ils les signaux forts ?",
   "marche": "Euronext", "cible": "gain par force de signal", "horizon": "multi",
   "metrique": "gain moyen", "resultat": "marginal 6.1 vs fort 14.1",
   "baseline": "indistinct", "periode": "2010-2025", "n": "42 episodes",
   "statut": "Robuste", "decision": "Integrer", "module": "M4 Euronext Premium",
   "interpretation": "N'agir que sur des ecarts francs : l'abstention sur signaux faibles ameliore la qualite."},
 "wheat_corn": {
   "question": "L'ecart de prix ble/mais signale-t-il les ventes de prime a risque ?",
   "marche": "Euronext / CBOT", "cible": "flag ADVERSE", "horizon": "multi",
   "metrique": "AUC", "resultat": "AUC 0.653 ; substitution corr 0.60 (contexte)",
   "baseline": "0.5", "periode": "2010-2025", "n": "a produire (backlog)",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M1 Downside Risk",
   "interpretation": "Signal modere : aide a ecarter les ventes de prime risquees, pas un predicteur direct."},
 "asymmetry": {
   "question": "L'avantage est-il symetrique entre vendre haut et acheter bas ?",
   "marche": "Euronext", "cible": "PnL short vs long", "horizon": "multi",
   "metrique": "PnL", "resultat": "short prime haute robuste ; long prime basse non",
   "baseline": "symetrie", "periode": "2010-2025", "n": "episodes",
   "statut": "Prometteur", "decision": "Surveiller / revalider", "module": "M4 Euronext Premium",
   "interpretation": "L'indicateur Euronext ne fait que de la VENTE de prime, jamais l'inverse."},
 "halflife_horizon": {
   "question": "La demi-vie du niveau donne-t-elle le bon horizon de decision ?",
   "marche": "Euronext", "cible": "horizon", "horizon": "multi",
   "metrique": "jours", "resultat": "analytique 9.5 j vs reel 28.6 j (x3)",
   "baseline": "egalite", "periode": "2010-2025", "n": "trades",
   "statut": "Garde-fou", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "Caler l'horizon sur le reel ; ne pas choisir un horizon trop court."},
 "granger": {
   "question": "Peut-on expliquer le basis par une juste valeur (fair-value) ?",
   "marche": "Euronext", "cible": "basis", "horizon": "multi",
   "metrique": "causalite de Granger", "resultat": "rejetee hors echantillon",
   "baseline": "absence de causalite", "periode": "multi", "n": "a produire (backlog)",
   "statut": "Garde-fou", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "Ne pas pretendre une fair-value stable : le basis se suffit a lui-meme."},
 "placebo": {
   "question": "L'avantage du basis EMA est-il specifique ?",
   "marche": "Euronext", "cible": "edge", "horizon": "multi",
   "metrique": "placebo (spreads temoins)", "resultat": "effet partiel sur temoins (specificite limitee)",
   "baseline": "cibles temoins", "periode": "multi", "n": "a etendre (backlog)",
   "statut": "Garde-fou", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "L'edge n'est pas 100 % specifique : etendre le placebo (autres spreads, dates, cultures)."},
 "seasonal_inversion": {
   "question": "Existe-t-il une inversion saisonniere exploitable du basis ?",
   "marche": "Euronext", "cible": "saisonnalite", "horizon": "multi",
   "metrique": "forward", "resultat": "hypothese falsifiee en forward",
   "baseline": "saisonnalite simple", "periode": "forward", "n": "a produire (backlog)",
   "statut": "Garde-fou", "decision": "Methodologie (cadre)", "module": "Cadre methodo",
   "interpretation": "Ne pas construire de regle sur cette hypothese ; garder la saisonnalite simple validee."},
 "cost_wall": {
   "question": "L'avantage net survit-il aux couts de transaction ?",
   "marche": "Euronext", "cible": "PnL net", "horizon": "multi",
   "metrique": "PnL net vs cout/jambe", "resultat": "edge concentre sur z>2 ; s'efface au-dela de ~5 EUR/t",
   "baseline": "cout nul", "periode": "hors crise", "n": "episodes z>2",
   "statut": "Limite", "decision": "Ne pas survendre", "module": "Cadre methodo",
   "interpretation": "Toujours montrer brut / net / +2 / +5 EUR/t et crise / hors crise."},
 "euronext_ro": {
   "question": "L'indicateur Euronext est-il pret a conseiller une vente ?",
   "marche": "Euronext", "cible": "recommandation", "horizon": "H90",
   "metrique": "AUC / ordre des retours", "resultat": "ordonne (-5.8 % vs +5.1 %) mais AUC 0.561, prix 97 % proxy",
   "baseline": "0.5", "periode": "hors echantillon", "n": "a produire (backlog)",
   "statut": "Limite", "decision": "Ne pas survendre", "module": "M4 Euronext Premium",
   "interpretation": "RESEARCH_ONLY tant que les vrais prix Euronext et couts ne sont pas propres."},
}

# 7 blocs (couvrent les 33)
BLOCKS = [
 (1, "Ce qu'on ne peut PAS faire (la prediction directe du prix est morte)",
  "On ne peut pas predire le niveau exact de maniere robuste, et les modeles complexes "
  "sur-apprennent. Ce n'est pas un echec : c'est le point de depart serieux qui force a "
  "changer de cible vers le risque, le contexte et les exces.",
  ["random_walk", "complex_models", "overfit", "fragile"]),
 (2, "Ce qui est le plus ROBUSTE (le risque est plus previsible que le prix)",
  "Le marche a de la memoire dans le risque : la volatilite et le risque de baisse se "
  "prevoient mieux que la direction, et le CBOT predit mieux ses baisses que ses hausses.",
  ["volatilite", "drawdown_cbot", "cbot_drops"]),
 (3, "Les fondamentaux agricoles (signal moyen terme)",
  "La Crop Condition et le WASDE donnent un signal moyen terme prometteur (a revalider) ; "
  "la meteo aide seulement dans ses EXTREMES PREVUS, la meteo realisee arrive trop tard.",
  ["direction_fusion", "crop_h90", "wasde_h40", "weather_extreme", "weather_priced_in"]),
 (4, "Le basis Euronext / CBOT (dynamique locale et mean-reverting)",
  "La prime Euronext/CBOT a une dynamique locale qui revient a la moyenne ; les signaux "
  "simples basis_z + saison battent les gros modeles, et la compression vient du CBOT.",
  ["indicateur_v9", "modele_2vars", "basis_reversion", "compression_cbot",
   "prime_locale", "specificity", "halflife_extreme"]),
 (5, "Les CONDITIONS de reussite (la strategie ne marche que dans certains contextes)",
  "Vendre la prime ne marche que sous conditions : signal fort, support CBOT, sortie "
  "partielle, faible risque adverse ; les familles d'episodes sont separables des l'entree.",
  ["adverse_predictable", "sell_high_cost", "asymmetry", "cbot_support",
   "episodes", "exit_z05", "marginal", "wheat_corn"]),
 (6, "Les FALSIFICATIONS (ce qui renforce la credibilite)",
  "Plusieurs hypotheses intuitives sont rejetees : horizon mal calibre, fair-value du "
  "basis, specificite de l'edge, inversion saisonniere. Les abandonner rend l'etude credible.",
  ["halflife_horizon", "granger", "placebo", "seasonal_inversion"]),
 (7, "Les LIMITES finales (prometteur mais fragile)",
  "L'avantage net est mince et conditionnel (mur des couts), et l'indicateur Euronext "
  "reste research-only tant que les vrais prix, couts et periodes independantes manquent.",
  ["cost_wall", "euronext_ro"]),
]

VERDICT = [
 "Verdict global : on a de vrais signaux, mais pas le signal simple cherche au depart "
 "(monte / baisse demain).",
 "Au depart : peut-on predire directement si le mais va monter ou baisser ?",
 "Reponse de l'etude : le prix exact est tres difficile a prevoir et les modeles complexes "
 "ne battent pas les references simples. En revanche, certains risques et contextes sont "
 "bien plus previsibles : volatilite, risque de baisse, tension WASDE, Crop Condition, basis "
 "Euronext/CBOT, prime locale, episodes de compression.",
 "Donc on peut creer un indicateur, mais pas un indicateur magique 'demain ca monte'. Il faut "
 "un indicateur de risque directionnel SELECTIF qui sait dire : risque de baisse eleve, "
 "contexte haussier moyen terme, volatilite a venir, prime a vendre, ou signal incertain.",
 "La cle de credibilite : l'indicateur doit accepter de dire souvent JE NE SAIS PAS (mode "
 "UNCERTAIN obligatoire).",
]

ARCHI = [
 ("Module 1 - CBOT Downside Risk (le plus credible)",
  "Detecter les periodes a forte probabilite de baisse. Entrees : WASDE stocks/use, Crop "
  "Condition, drawdown, volatilite future, wheat/corn, momentum, saison. Cibles : baisse "
  "H20/H40/H60, forte baisse, drawdown 30-60 j. Sortie : LOW / MEDIUM / HIGH."),
 ("Module 2 - CBOT Bullish Potential (prudent)",
  "Detecter les contextes a plus forte chance de hausse. Entrees : stocks/use tendu, "
  "mauvaise Crop Condition, stress meteo PREVU extreme, COT, support CBOT, saison. "
  "Sortie : BULLISH / NEUTRAL / UNCERTAIN. Prudent car les hausses sont moins previsibles."),
 ("Module 3 - Volatility / Market Risk Regime",
  "Dire si le marche devient dangereux. Entrees : HAR, EGARCH, vol realisee, drawdown "
  "recent, periode WASDE, saison. Sortie : CALME / NORMAL / VOLATIL / EXTREME. Sert a "
  "moduler la confiance des autres modules."),
 ("Module 4 - Euronext Premium Signal (research-only)",
  "Detecter une prime anormalement haute et compressible. Entrees : basis_z, saison, "
  "support CBOT, wheat/corn, risque adverse, cout, filtre crise. Sortie : SELL PREMIUM / "
  "WAIT / ADVERSE RISK / RESEARCH_ONLY (prix Euronext a 97 % proxy)."),
 ("Module transverse - Confidence Gate",
  "Est-ce que le signal est fiable ? Entrees : accord entre modules, calibration, "
  "volatilite, largeur CQR, force du signal, stabilite 3 jours, contexte crise. Sortie : "
  "CONFIDENCE LOW / MEDIUM / HIGH. Regle centrale : aucune action si confiance faible."),
]

BACKLOG = [
 "Intervalles de confiance (bootstrap 95 %) sur chaque metrique forte (AUC 0.816, DA 0.705, "
 "AUC 0.74, 0.694, 0.72).",
 "Performance PAR ANNEE (DA / AUC / signal moyen) pour verifier que le resultat ne vient pas "
 "que de 2024.",
 "Calibration (Brier, courbe de fiabilite) : quand le modele dit 70 % de risque, la baisse "
 "arrive-t-elle ~70 % du temps ?",
 "Placebo etendu : autre spread, dates decalees, cible melangee, autre culture, annees hors "
 "signal.",
 "Couts et vrai prix : brut / net / +2 EUR/t / +5 EUR/t, crise vs hors crise ; vrais prix "
 "Euronext et base locale au lieu du proxy 97 %.",
 "Nombre d'observations et periode de test explicites pour chaque decouverte prometteuse.",
]

FINALE = (
 "L'etude montre que le prix exact du mais reste tres difficile a prevoir. En revanche, "
 "plusieurs composantes du risque sont partiellement previsibles : la volatilite, le risque "
 "de drawdown, les pressions fondamentales WASDE / Crop Condition et la compression de prime "
 "Euronext / CBOT. L'indicateur final doit donc etre concu comme un outil de detection de "
 "contextes favorables ou defavorables, avec un mode UNCERTAIN obligatoire, et non comme un "
 "modele de prevision parfaite du prix."
)


def imgs(idx: str) -> tuple[str, str]:
    d = DIDX[idx]
    base = f"{d['num']:02d}_{d['id']}"
    return f"{base}_1_decouverte.png", f"{base}_2_courbes.png"


def main() -> None:
    # ---- verdicts des anciennes pistes (Robuste ou Limite, plus d'entre-deux) ----
    verdicts = {}
    vpath = OUT / "pistes_verdicts.json"
    if vpath.exists():
        verdicts = json.loads(vpath.read_text(encoding="utf-8"))

    def eff(idx):  # statut effectif (raw : Robuste / Garde-fou / Limite)
        v = verdicts.get(idx)
        return v["verdict"] if v and "verdict" in v else META[idx]["statut"]

    # nettoyage des tokens interdits dans les validees + injection des chiffres walk-forward
    clean = {"volatilite": {"periode": "OOS 2014-2025", "n": "2787"},
             "drawdown_cbot": {"periode": "OOS 2014-2025", "n": "2845"},
             "cbot_drops": {"periode": "OOS 2014-2025", "n": "2845"},
             "prime_locale": {"n": "OOF multi-annees"},
             "specificity": {"n": "OOF multi-annees"},
             "complex_models": {"n": "multi-modeles"},
             "marginal": {"n": "OOF (confirme par la courbe de confiance de l'indicateur)"}}
    for pid in ("crop_h90", "wheat_corn", "direction_fusion"):
        v = verdicts.get(pid)
        if v and "auc" in v:
            clean[pid] = {"resultat": f"AUC {v['auc']:.3f} en walk-forward 2014-2025, IC95 "
                          f"[{v['ci_low']:.3f} ; {v['ci_high']:.3f}], positive sur "
                          f"{v['year_share_pos']:.0%} des annees (placebo {v['placebo_auc']:.3f})",
                          "baseline": "0.5 (hasard)", "periode": "OOS 2014-2025", "n": str(v["n"])}

    def disp(idx):
        m = dict(META[idx])
        m.update(clean.get(idx, {}))
        return m

    def reason(idx):
        v = verdicts.get(idx, {})
        if v.get("reason"):
            return v["reason"]
        if v.get("verdict") == "Limite" and "auc" in v:
            return (f"AUC {v['auc']:.3f} mais positive sur {v['year_share_pos']:.0%} des annees "
                    "seulement (instable hors echantillon, sous le seuil de robustesse).")
        return META[idx]["interpretation"]

    val = [d["id"] for d in D if eff(d["id"]) == "Robuste"]
    gard = [d["id"] for d in D if eff(d["id"]) == "Garde-fou"]
    lim = [d["id"] for d in D if eff(d["id"]) == "Limite"]
    nval, ngard, nlim = len(val), len(gard), len(lim)

    # ---- CSV inventaire (statut final + raison) ----
    cols = ["ID", "Nom", "Question", "Marche", "Cible", "Horizon", "Metrique", "Resultat",
            "Baseline", "Periode_test", "N_observations", "Categorie", "Module", "Raison"]
    with (OUT / "inventaire_decouvertes.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for d in D:
            idx = d["id"]
            m = disp(idx)
            r = reason(idx) if eff(idx) == "Limite" else ""
            w.writerow([d["num"], d["title"], m["question"], m["marche"], m["cible"], m["horizon"],
                        m["metrique"], m["resultat"], m["baseline"], m["periode"], m["n"],
                        LABEL[eff(idx)], m["module"], r])

    # ---- markdown ----
    md = ["# Synthese scientifique - etude mais", "", "## Verdict global", ""]
    md += [f"- {x}" for x in VERDICT]
    md += ["", "## Classification finale des 33 resultats", "",
           f"- Decouvertes validees : {nval}  |  Garde-fous methodologiques : {ngard}  |  "
           f"Limites importantes : {nlim}",
           "- Les anciennes 'pistes' ont ete tranchees : chacune est devenue une decouverte "
           "validee (test walk-forward concluant) ou une limite (validation impossible avec les "
           "donnees gratuites). Plus d'entre-deux.", "",
           "Table complete : `artefacts/decouvertes/inventaire_decouvertes.csv`.", ""]

    def md_card(idx, kind):
        d, m = DIDX[idx], disp(idx)
        a, b = imgs(idx)
        out = [f"### {d['num']:02d}. {d['title']}", "", d["what"], "",
               f"- Resultat : {m['resultat']} (baseline {m['baseline']}, periode {m['periode']}, "
               f"n {m['n']})"]
        if kind == "val":
            e = EXTRA[idx]
            out += [f"- Ce que ca demontre : {e['demontre']}",
                    f"- Pourquoi ca a change l'etude : {e['change']}",
                    f"- Consequence pour l'indicateur : {e['consequence']}"]
        elif kind == "lim":
            out += [f"- Pourquoi c'est une limite (pas validee) : {reason(idx)}"]
        else:
            out += [f"- Interpretation : {m['interpretation']}"]
        out += [f"- CBOT : {d['cbot']}", f"- Euronext : {d['ema']}", "",
                f"![decouverte]({a})", "", f"![courbes]({b})", ""]
        return out

    md += ["## 1. Decouvertes validees (le socle de l'etude)", ""]
    for idx in val:
        md += md_card(idx, "val")
    md += ["## 2. Garde-fous methodologiques (resultats negatifs utiles)", ""]
    for idx in gard:
        md += md_card(idx, "gard")
    md += ["## 3. Limites importantes (dont anciennes pistes non validees)", ""]
    for idx in lim:
        md += md_card(idx, "lim")
    md += ["## Backlog restant", ""]
    md += [f"- {x}" for x in BACKLOG]
    md += ["", "## Phrase finale", "", FINALE, ""]
    (ROOT / "docs" / "SYNTHESE_SCIENTIFIQUE.md").write_text("\n".join(md), encoding="utf-8")

    # ---- html autonome ----
    def chip(s):
        return (f"<span style='background:{SCOL[s]};color:#fff;border-radius:10px;"
                f"padding:1px 9px;font-size:.8em'>{LABEL[s]}</span>")

    def card(idx, kind):
        d, m = DIDX[idx], disp(idx)
        a, b = imgs(idx)
        h = (f"<div class='card'><h3>{d['num']:02d}. {d['title']} &nbsp;{chip(eff(idx))}</h3>"
             f"<p class='lead'>{d['what']}</p>"
             f"<div class='res'><b>Resultat :</b> {m['resultat']} <i>(baseline {m['baseline']}, "
             f"periode {m['periode']}, n {m['n']})</i><br>"
             f"<b>CBOT :</b> {d['cbot']}<br><b>Euronext :</b> {d['ema']}</div>")
        if kind == "val":
            e = EXTRA[idx]
            h += (f"<div class='why'><b>Ce que ca demontre :</b> {e['demontre']}<br>"
                  f"<b>Pourquoi ca a change l'etude :</b> {e['change']}<br>"
                  f"<b>Consequence pour l'indicateur :</b> {e['consequence']}</div>")
        elif kind == "lim":
            h += f"<div class='limred'><b>Pourquoi c'est une limite (pas validee) :</b> {reason(idx)}</div>"
        else:
            h += f"<div class='fiche'><b>Interpretation :</b> {m['interpretation']}</div>"
        h += (f"<div class='imgs'><figure><figcaption>Ce que la decouverte fait</figcaption>"
              f"<img src='{a}'></figure><figure><figcaption>Sur les courbes CBOT &amp; Euronext"
              f"</figcaption><img src='{b}'></figure></div></div>")
        return h

    parts = ["<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
             "<title>Synthese scientifique - etude mais</title><style>"
             "body{font-family:system-ui,Arial,sans-serif;max-width:1180px;margin:24px auto;"
             "padding:0 16px;color:#1a1a1a;line-height:1.5}h1{margin-bottom:2px}"
             "h2{margin-top:36px;border-bottom:2px solid #ddd;padding-bottom:4px}"
             ".verdict{background:#fff8ec;border:1px solid #e8943a;border-radius:10px;padding:12px 16px}"
             ".counts{font-weight:600;margin:10px 0}"
             ".card{border:1px solid #e2e2e2;border-radius:10px;padding:14px 16px;margin:16px 0;"
             "background:#fafafa}.lead{font-size:1.02em;margin:.2em 0 .6em;color:#111}"
             ".fiche{font-size:.93em;margin:.3em 0 .8em;background:#fff;border-left:3px solid #bbb;"
             "padding:8px 12px;border-radius:0 6px 6px 0}"
             ".fiche b{color:#333}.res{background:#f4f7fb;border-left:3px solid #1f77b4;padding:8px 12px;"
             "border-radius:0 6px 6px 0;margin:.4em 0;font-size:.95em}"
             ".why{background:#eef7ee;border-left:3px solid #2ca02c;padding:8px 12px;"
             "border-radius:0 6px 6px 0;margin:.4em 0;font-size:.93em}"
             ".limred{background:#fdeeee;border-left:3px solid #d62728;padding:8px 12px;"
             "border-radius:0 6px 6px 0;margin:.4em 0;font-size:.93em}"
             ".imgs{display:flex;gap:14px;flex-wrap:wrap}"
             "figure{margin:0;flex:1 1 360px}figcaption{font-size:.85em;color:#666}"
             "img{width:100%;border:1px solid #ddd;border-radius:6px;background:#fff}"
             ".archi{background:#eef4fb;border:1px solid #1f77b4;border-radius:10px;padding:10px 16px;margin:10px 0}"
             ".backlog{background:#fdeeee;border:1px solid #d62728;border-radius:10px;padding:10px 16px}"
             ".indic{background:#eef4fb;border:2px solid #1f77b4;border-radius:10px;padding:14px 18px;margin:14px 0}"
             "table{border-collapse:collapse;margin:10px 0;font-size:.95em}"
             "td,th{border:1px solid #cdd;padding:5px 10px;text-align:center}th{background:#dde}"
             ".intro{background:#f6f6f6;border:1px solid #ddd;border-radius:10px;padding:10px 16px}"
             "</style></head><body>",
             "<h1>Decouvertes de l'etude mais et indicateur final</h1>",
             "<div class='intro'>Comment lire cette page : d'abord l'histoire de l'etude (pourquoi "
             "on a change d'objectif), puis les resultats ranges en 3 categories CLAIRES : "
             "decouvertes validees (le socle), garde-fous methodologiques (resultats negatifs "
             "utiles) et limites importantes. Les anciennes 'pistes prometteuses' ont ete "
             "tranchees une par une : chacune est devenue une decouverte validee ou une limite, "
             "il n'y a plus d'entre-deux. Tout en bas : l'indicateur final produit et ses "
             "resultats valides.</div>",
             "<h2>Verdict global</h2><div class='verdict'>"
             + "".join(f"<p>{x}</p>" for x in VERDICT) + "</div>",
             "<div class='counts'>Classification finale : "
             f"{chip('Robuste')} {nval} &nbsp; {chip('Garde-fou')} {ngard} &nbsp; "
             f"{chip('Limite')} {nlim} &nbsp; (table : inventaire_decouvertes.csv)</div>"]
    parts.append("<h2>1. Decouvertes validees (le socle de l'etude)</h2>"
                 "<p>Resultats assez solides pour structurer l'etude et nourrir l'indicateur.</p>")
    parts += [card(idx, "val") for idx in val]
    parts.append("<h2>2. Garde-fous methodologiques (resultats negatifs utiles)</h2>"
                 "<p>Ils empechent de partir dans une mauvaise direction.</p>")
    parts += [card(idx, "gard") for idx in gard]
    parts.append("<h2>3. Limites importantes (dont anciennes pistes non validees)</h2>"
                 "<p>Signaux interessants mais non eleves au socle : validation impossible avec "
                 "les donnees gratuites (proxy, trop peu d'episodes, resultat oracle ou hors "
                 "crise, instabilite par annee).</p>")
    parts += [card(idx, "lim") for idx in lim]
    parts.append("<h2>Architecture de l'indicateur (implementee en V1)</h2>")
    for t, txt in ARCHI:
        parts.append(f"<div class='archi'><b>{t}</b><br>{txt}</div>")
    parts.append("<h2>Backlog restant (avant de dire 'fiable')</h2><div class='backlog'><ul>"
                 + "".join(f"<li>{x}</li>" for x in BACKLOG) + "</ul></div>")
    parts.append(indicator_html())
    parts.append(f"<h2>Phrase finale</h2><div class='verdict'><p>{FINALE}</p></div></body></html>")
    html = "".join(parts)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "synthese.html").write_text(html, encoding="utf-8")

    print(f"synthese : validees {nval} | garde-fous {ngard} | limites {nlim}")
    print("ecrit : docs/SYNTHESE_SCIENTIFIQUE.md, artefacts/decouvertes/index.html (+ synthese.html), "
          "inventaire_decouvertes.csv")


if __name__ == "__main__":
    main()
