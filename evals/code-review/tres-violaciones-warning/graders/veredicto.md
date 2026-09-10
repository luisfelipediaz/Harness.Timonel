---
type: regex
weight: 2
flags: i
pattern: "veredicto:\\s*APROBADO CON OBSERVACIONES"
match: contains
target: last_message
---

Sin hallazgos CRITICO (el Gherkin se cumple) pero con warnings, el veredicto del YAML debe ser exactamente `APROBADO CON OBSERVACIONES`.
