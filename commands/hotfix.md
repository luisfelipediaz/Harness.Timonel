---
description: "Implementa un hotfix (≤2 SP) desde un issue tipo:hotfix o una descripcion libre, sin worktrees y con DoD reducido."
argument-hint: "<numero-de-issue | descripcion del fix>"
model: haiku
---

Lanza el agente `hotfix-executor`. Comunicate en **espanol**.

## Pre-condiciones

```bash
[ -f .claude/timonel.config.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

## Lanzar

Invoca al agente `hotfix-executor` (`subagent_type: "timonel:hotfix-executor"`) con `$ARGUMENTS`:

- Solo digitos → Caso A (issue existente).
- Texto → Caso B (crea el issue `tipo:hotfix` antes de implementar).

Si `$ARGUMENTS` esta vacio: `Uso: /timonel:hotfix <numero-de-issue | descripcion>`.

## Reglas

- No implementes nada tu mismo.
- Si el agente redirige a `story-executor`, respeta la redireccion.
