---
type: regex
flags: i
pattern: "(\\|[^\\n]*WARNING[^\\n]*\\*ngIf)|(\\|[^\\n]*\\*ngIf[^\\n]*WARNING)"
match: contains
target: last_message
---

El template con `*ngIf` (control flow viejo de Angular) debe salir como hallazgo WARNING.
