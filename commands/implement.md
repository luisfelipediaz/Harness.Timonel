---
description: "Implementa una historia de usuario (issue tipo:hu) con el orquestador flechodiezx: contrato API, sub-agentes en worktrees, consolidacion, review, retro y DoD publicados en el issue."
argument-hint: "<numero-de-issue>"
model: haiku
---

Lanza el agente `flechodiezx` para el issue indicado. Comunicate en **espanol**.

## Entrada

`$ARGUMENTS` debe contener un numero de issue. Si esta vacio: `Uso: /timonel:implement <numero-de-issue>` y detente.

## Pre-validacion rapida

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
REPO=$(jq -r '.github.repo' .claude/timonel.config.json 2>/dev/null || gh repo view --json nameWithOwner -q .nameWithOwner)
gh issue view "$ARGUMENTS" -R "$REPO" --json number,title,state,labels -q '"#\(.number): \(.title) [\(.state)] :: \([.labels[].name]|join(", "))"'
```

- Si no existe o esta `CLOSED`, informa y detente.
- Si no tiene `tipo:hu`: si tiene `tipo:hotfix`, sugiere `/timonel:hotfix N`; si es `tipo:epica`/`tipo:sdd`, explica que no se implementan directamente.
- DoR con el sensor unico:
  ```bash
  PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ 2>/dev/null | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
  python3 "$PLUGIN_ROOT/scripts/dor_check.py" "$ARGUMENTS" --para implementar
  ```
  Si sale 1, muestra los faltantes tal cual y sugiere `/timonel:refine N`; no lances el agente.

## Lanzar

Invoca al agente `flechodiezx` (`subagent_type: "timonel:flechodiezx"`) con: `Implementa el issue #$ARGUMENTS`.

## Reglas

- No implementes nada tu mismo.
- El agente pide aprobacion del contrato API antes de tocar codigo; no la saltes.
