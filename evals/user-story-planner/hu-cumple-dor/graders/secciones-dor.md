---
type: regex
flags: ms
pattern: "## Historia.*## Criterios de aceptaci.*## Ficha t.*## Endpoints.*## Modelos compartidos.*## Dependencias.*## Tareas"
match: contains
target: last_message
---

Las siete secciones exigidas por `dor_check.py` para `tipo:hu` deben aparecer, en este orden, en la respuesta.
