---
description: "Planifica epicas e historias de usuario como GitHub Issues con el agente user-story-planner."
argument-hint: "[contexto libre | #sdd | #epica]"
model: haiku
---

Lanza el agente `user-story-planner` para planificar historias del repo consumidor actual. Comunicate en **espanol**.

## Pre-condiciones

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

## Lanzar

Invoca al agente `user-story-planner` (Agent tool, `subagent_type: "timonel:user-story-planner"`) pasando `$ARGUMENTS` como mensaje inicial. Si `$ARGUMENTS` referencia un issue (`#N`), indicale que lo lea primero: si es `tipo:sdd` derive las HUs de sus epicas; si es `tipo:epica` planifique HUs solo para esa epica.

## Reglas

- No planifiques nada tu mismo: lanza al agente y presenta su resultado.
- El agente pide confirmacion antes de crear issues; no la saltes.
