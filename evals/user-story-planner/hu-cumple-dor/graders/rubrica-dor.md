---
type: llm
weight: 1
---

Evaluá la HU devuelta por el agente contra TIM-ADR-0003 (Definition of Ready). Score 1.0 si se cumple todo lo siguiente; restá proporcionalmente por cada punto incumplido:

- El título está en infinitivo, sin prefijo `HU-`, `[`, `feat` ni `fix`.
- La sección `## Historia` sigue el formato **Como** / **quiero** / **para**.
- Hay al menos un escenario Gherkin bajo `## Criterios de aceptación`.
- La `## Ficha técnica` es una tabla con, como mínimo, `Alcance`, `Entidad principal`, `Tipo de operación`, `Permiso requerido` y `Módulo destino`.
- `## Endpoints` trae `Request`, `Response` y `Errores` por cada endpoint, o dice explícitamente `Ninguno`.
- `## Tareas` es el checklist estándar de 9 ítems de `plantilla-hu.md` (Contrato API aprobado, Modelos compartidos, Backend, Frontend, Consolidación, Code review, Retrospectiva, Definition of Done, PR abierto).
- Ninguna celda de ninguna tabla dice `POR DEFINIR`.
- El `sp:` elegido es un valor Fibonacci válido y no supera 13.
- El agente no ejecutó `gh` ni intentó crear ningún issue.

Devolvé 0 si falta el bloque ` ```markdown ` o la línea `Labels:`.
