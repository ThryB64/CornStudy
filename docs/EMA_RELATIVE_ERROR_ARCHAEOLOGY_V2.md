# EMA RELATIVE ERROR ARCHAEOLOGY V2

> Analyse des erreurs H40/H90 pour les signaux relatifs EMA/CBOT.

## Verdict

- H40 tag principal pires erreurs : `ROLL_ARTIFACT`
- H90 tag principal pires erreurs : `ROLL_ARTIFACT`
- H40 failed top20 principal : `ROLL_ARTIFACT`
- H90 failed top20 principal : `ROLL_ARTIFACT`
- Lecture : Use dominant tags to refine abstention filters and season/roll/crisis gates.

## H40

- OOF : 2408
- Erreurs : 868
- Failed top20 : 50

### Tags pires erreurs

- `ROLL_ARTIFACT` : 86
- `BASIS_EXTREME` : 56
- `CRISIS_PERIOD` : 54
- `UNKNOWN` : 6
- `CBOT_SHOCK` : 3
- `EU_PREMIUM_SHOCK` : 1

### Tags failed top20

- `ROLL_ARTIFACT` : 50
- `BASIS_EXTREME` : 34
- `CRISIS_PERIOD` : 33
- `CBOT_SHOCK` : 2
- `EU_PREMIUM_SHOCK` : 1

## H90

- OOF : 2358
- Erreurs : 731
- Failed top20 : 50

### Tags pires erreurs

- `ROLL_ARTIFACT` : 70
- `CRISIS_PERIOD` : 44
- `BASIS_EXTREME` : 29
- `UNKNOWN` : 19
- `CBOT_SHOCK` : 1

### Tags failed top20

- `ROLL_ARTIFACT` : 40
- `CRISIS_PERIOD` : 30
- `BASIS_EXTREME` : 23
- `CBOT_SHOCK` : 1
- `UNKNOWN` : 1
