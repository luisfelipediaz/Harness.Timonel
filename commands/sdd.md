---
description: "Crea, actualiza o deriva epicas de un Software Design Document publicado como GitHub Issue (tipo:sdd)."
argument-hint: "[tema | #issue] [--derivar]"
model: haiku
---

Lanza el agente `sdd-planner`. Comunicate en **espanol**.

## Pre-condiciones

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

## Lanzar

Invoca al agente `sdd-planner` (`subagent_type: "timonel:sdd-planner"`) con `$ARGUMENTS`:

- Texto libre → modo **crear**.
- `#N` → modo **actualizar** (o **derivar** si viene `--derivar`).

## Reglas

- No redactes el SDD tu mismo.
- El agente publica solo tras aprobacion explicita del usuario.
