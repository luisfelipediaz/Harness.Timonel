---
name: HU generada por user-story-planner cumple el DoR
tags: [planner, dor]
runs: 2
max_turns: 8
---

Necesito que redactes UNA historia de usuario para el siguiente feature ficticio. No preguntes nada al usuario: si algo no está definido, asume lo más razonable y sigue adelante.

## Contexto del feature

- **Módulo**: `mis-finanzas`.
- **Épica**: sub-issue de la épica ficticia `#3`.
- **Feature**: "Registrar gasto con categoría".
- **Rol**: empleado.
- **Reglas de negocio**:
  - El monto debe ser mayor a 0.
  - La categoría debe pertenecer a una lista fija (no se puede escribir libre).
  - La fecha del gasto no puede ser futura.
- **Endpoint**: `POST /api/mis-finanzas/gastos`.
- **Permiso**: `TiposDePermisos.RegistrarGasto`.

## Lo que tienes que hacer

Usa el agente `user-story-planner` del plugin `timonel` para redactar esta historia con la plantilla `skills/github-issues/references/plantilla-hu.md`, pero **sin publicarla**: no ejecutes `gh`, no crees ningún issue.

En tu respuesta final:

1. Pon el body completo de la HU (con todas sus secciones, en el mismo orden que la plantilla) dentro de un único bloque ` ```markdown `.
2. Inmediatamente después de cerrar ese bloque, agregá una única línea con el formato exacto:

   ```
   Labels: tipo:hu, alcance:<x>, sp:<n>, mod:<m>, moscow:<y>, prioridad:<z>, estado:borrador
   ```

   reemplazando `<x>`, `<n>`, `<m>`, `<y>`, `<z>` por los valores reales que elegiste para esta historia.

El título va en infinitivo, sin prefijos como `HU-`, `[...]`, `feat:` o `fix:`.
