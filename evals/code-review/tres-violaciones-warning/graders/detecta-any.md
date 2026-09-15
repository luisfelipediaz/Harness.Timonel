---
type: regex
flags: i
pattern: "(\\|[^\\n]*WARNING[^\\n]*\\bany\\b)|(\\|[^\\n]*\\bany\\b[^\\n]*WARNING)"
match: contains
target: last_message
---

`gastos: any[] = []` debe salir como hallazgo WARNING. La regla "No `any`" vive en el catálogo de convenciones del stack (`heuristics/angular/convenciones-bitakora.md`, H1 terminado en ` — catálogo`), que el skill revisa en §3.3 como hallazgo `Convención`.
