---
id: weather-and-corn-crop-condition-reports-are-not-enough
source_type: paper
title: Weather and corn - Crop condition reports are not enough
priority: high
status: analyzed_2026-06-12
---
# Weather and corn: Crop condition reports are not enough (Taylor 2010)

## 1. Référence

Taylor, E. (2010). Proceedings of the Integrated Crop Management Conference, Iowa State. Article agronomique court.

## 2. Sujet

Limites des notations de condition : elles réagissent avec RETARD au stress (un maïs noté « good » peut déjà avoir un potentiel de rendement entamé par un stress hydrique précoce ou des nuits chaudes).

## 3. Données

Observations agronomiques Iowa/Corn Belt : notations vs rendements finaux, variables météo critiques (températures nocturnes en pollinisation, déficit hydrique en remplissage).

## 4. Méthode

Analyse agronomique descriptive (pas d'économétrie).

## 5. Résultats importants

- Les notations sous-estiment les dégâts tant qu'ils ne sont pas VISIBLES ; les températures nocturnes élevées pendant la pollinisation et le déficit hydrique de juillet dégradent le rendement avant la notation.
- La météo brute par stade contient donc de l'information EN AVANCE sur les notations.

## 6. Apport pour notre étude

- Justifie de tester météo-par-stade (EXT001) EN PLUS des surprises de notation (EXT027) : si Taylor a raison, la météo de stade critique doit précéder les révisions de notation → feature « condition implicite − condition notée » comme proxy d'info en retard.
- Variables précises à inclure : T° nocturnes (Tmin) en pollinisation, bilan hydrique en remplissage — pas seulement Tmax/précipitations moyennes.

## 7. Hypothèses testables

- H1 : un indice de stress par stade (GDD, Tmin pollinisation, déficit P-ET en remplissage, pondéré par État producteur) PRÉDIT la surprise de notation du lundi suivant (test interne sans marché — si ça échoue, l'avance informationnelle n'existe pas).
- H2 : si H1 passe : ce même indice prédit-il la direction CBOT H5-H20 AVANT que la notation ne l'incorpore ?

## 8. Risques et limites

Pas un papier de marché (aucun test prix) ; vieilli (2010) — les modèles privés ont pu combler ce retard depuis (V45 : le réalisé est largement pricé) ; US-centré.

## 9. EXT associées

EXT001, EXT002, EXT027 (chaîne logique : météo de stade → surprise de notation → prix).

## 10. Conclusion

**Priorité haute** comme justification du design en deux étages de EXT001/EXT027 (météo → notation → prix), pas comme source de résultat.
