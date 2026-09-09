---
description: "Implementa una historia de usuario (issue tipo:hu) con el orquestador story-executor: contrato API, sub-agentes en worktrees, consolidacion, review, retro y DoD publicados en el issue."
argument-hint: "<numero-de-issue>"
model: haiku
---

Lanza el agente `story-executor` para el issue indicado. Comunicate en **espanol**.

## Entrada

`$ARGUMENTS` debe contener un numero de issue. Si esta vacio: `Uso: /timonel:implement <numero-de-issue>` y detente.

## Pre-validacion rapida

```bash
[ -f .claude/timonel.config.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
REPO=$(jq -r '.github.repo' .claude/timonel.config.json)
gh issue view "$ARGUMENTS" -R "$REPO" --json number,title,state,labels -q '"#\(.number): \(.title) [\(.state)] :: \([.labels[].name]|join(", "))"'
```

- Si no existe o esta `CLOSED`, informa y detente.
- Si no tiene `tipo:hu`: si tiene `tipo:hotfix`, sugiere `/timonel:hotfix N`; si es `tipo:epica`/`tipo:sdd`, explica que no se implementan directamente.
- Si no tiene `estado:listo`, muestra los labels y sugiere `/timonel:refine N` (el agente valida el DoR completo igual).

## Lanzar

Invoca al agente `story-executor` (`subagent_type: "timonel:story-executor"`) con: `Implementa el issue #$ARGUMENTS`.

## Reglas

- No implementes nada tu mismo.
- El agente pide aprobacion del contrato API antes de tocar codigo; no la saltes.
