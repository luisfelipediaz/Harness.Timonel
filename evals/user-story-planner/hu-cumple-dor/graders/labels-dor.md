---
type: regex
flags: im
pattern: "^Labels:.*tipo:hu.*alcance:(backend|frontend|full-stack).*sp:(1|2|3|5|8|13).*mod:[a-z0-9-]+.*moscow:(must|should|could|wont).*prioridad:(alta|media|baja)"
match: contains
target: last_message
---

La línea `Labels:` debe traer los seis labels obligatorios de una `tipo:hu`, con valores válidos.
