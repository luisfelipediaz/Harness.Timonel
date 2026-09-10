---
type: regex
flags: i
pattern: "(\\|[^\\n]*WARNING[^\\n]*(espejo|GastoResponse))|(\\|[^\\n]*(espejo|GastoResponse)[^\\n]*WARNING)"
match: contains
target: last_message
---

`GastoResponse` copia campo a campo `Gasto` (tipo espejo, `heuristics/general/no-tipos-espejo.md`) y debe salir como hallazgo WARNING.
