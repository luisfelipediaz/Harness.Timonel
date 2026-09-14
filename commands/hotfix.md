---
description: "Implementa un hotfix (≤2 SP) desde un issue tipo:hotfix o una descripcion libre, en worktree aislado y con PR obligatorio, con DoD reducido."
argument-hint: "<numero-de-issue | descripcion del fix>"
model: haiku
---

Lanza el agente `flechodiezx-hotfix`. Comunicate en **espanol**.

## Pre-condiciones

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

## Lanzar

Invoca al agente `flechodiezx-hotfix` (`subagent_type: "timonel:flechodiezx-hotfix"`) con `$ARGUMENTS`:

- Solo digitos → Caso A (issue existente).
- Texto → Caso B (crea el issue `tipo:hotfix` antes de implementar).

Si `$ARGUMENTS` esta vacio: `Uso: /timonel:hotfix <numero-de-issue | descripcion>`.

## Reglas

- No implementes nada tu mismo.
- Si el agente redirige a `flechodiezx`, respeta la redireccion.
