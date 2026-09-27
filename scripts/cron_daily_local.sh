#!/usr/bin/env bash
# Collecte locale quotidienne (cron horaire) : une seule exécution réussie par jour,
# attente du réseau (le PC sort souvent de veille sans wifi), rattrapage si le PC était éteint.
set -u
cd "$(dirname "$0")/.." || exit 1
STAMP_DIR=logs/.daily_stamps
mkdir -p "$STAMP_DIR"
TODAY=$(date +%F)
[ -f "$STAMP_DIR/$TODAY" ] && exit 0
exec 9>logs/.daily.lock
flock -n 9 || exit 0

for _ in $(seq 1 20); do
  curl -s -m 10 -o /dev/null https://query1.finance.yahoo.com && break
  sleep 30
done
curl -s -m 10 -o /dev/null https://query1.finance.yahoo.com || { echo "$(date -Is) réseau indisponible, report" ; exit 0; }

set -a; [ -f .env ] && . ./.env; set +a
venv/bin/python -m mais.cli daily-run --collect
STATUS=$(venv/bin/python -c "import json;print(json.load(open('artefacts/daily/daily_status.json')).get('overall_status',''))" 2>/dev/null)
echo "$(date -Is) daily-run status=$STATUS"
[ "$STATUS" != "FAIL" ] && [ -n "$STATUS" ] && touch "$STAMP_DIR/$TODAY"
exit 0
