---
type: regex
flags: i
pattern: "(\\|[^\\n]*WARNING[^\\n]*\\bany\\b)|(\\|[^\\n]*\\bany\\b[^\\n]*WARNING)"
match: contains
target: last_message
---

`gastos: any[] = []` debe salir como hallazgo WARNING (heurística "No `any`" de `convenciones-bitakora.md`).
