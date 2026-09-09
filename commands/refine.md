---
description: "Refina el backlog en GitHub Issues (dividir, repriorizar, deduplicar, completar fichas) con el agente backlog-refiner."
argument-hint: "[#epica | #issue ... | mod:<modulo> | todo] [--aplicar]"
model: haiku
---

Lanza el agente `backlog-refiner`. Comunicate en **espanol**.

## Pre-condiciones

```bash
[ -f .claude/timonel.config.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

## Lanzar

Invoca al agente `backlog-refiner` (`subagent_type: "timonel:backlog-refiner"`) con `$ARGUMENTS` como scope inicial. `--aplicar` → modo `aplicar`; si no, `solo-reporte`. Sin argumentos, el agente pregunta el scope.

## Reglas

- No refines nada tu mismo.
- El agente pide "si" por cada cambio incluso en modo aplicar.
