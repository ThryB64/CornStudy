# EXT001 — Weather crop windows

Météo réalisée agrégée par fenêtres agronomiques (semis avr-mai, végétatif juin,
pollinisation juillet, remplissage août, récolte sept-oct), pondérée production,
en anomalies standardisées (climatologie expandante, années passées seulement).

- `run_EXT001.py` — construit les features et appelle le harnais commun.
- Sources : Singh ; Li-Hayes-Jacobs ; Janzen ; Filimon ; Lee.
- Anti-fuite : réalisé décalé J+1, poids d'État figés 2000-2007, climatologie par
  day-of-year n'utilisant que les années antérieures.

Cible : log-retour CBOT t→t+h (H5/H20/H40/H90). BASE = marché seul.
Verdict : **REJECT** (voir `results/.../README_results.md`).
