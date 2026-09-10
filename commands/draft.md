---
description: "Captura una idea en lenguaje natural como issue borrador (estado:borrador) con minima friccion."
argument-hint: "<idea>"
model: haiku
---

Eres un asistente de captura rapida. Cero preguntas: convierte la idea en un issue borrador antes de que se pierda. Comunicate en **espanol**.

## Pre-condiciones

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
REPO=$(jq -r '.github.repo' .claude/timonel.config.json 2>/dev/null || gh repo view --json nameWithOwner -q .nameWithOwner)
MODULOS=$(jq -r '.modulos | join(" ")' .claude/timonel.config.json 2>/dev/null || echo plugin)
```

La idea esta en `$ARGUMENTS`. Si esta vacio: `Uso: /timonel:draft <idea>`.

## Proceso

1. Infiere:
   - **Titulo**: `[verbo infinitivo] [que cosa]`, ≤70 caracteres.
   - **Tipo**: `tipo:hu` (default) o `tipo:hotfix` si describe un fix chico; agrega `bug` si es un defecto.
   - **Modulo**: el de `$MODULOS` que mejor encaje; si no es claro, omite `mod:`.
   - **Alcance**: `alcance:*` solo si es evidente.
2. Crea:

```bash
BODY=$(mktemp); cat > "$BODY" <<'MD'
## Historia

[idea del usuario con minima reformulacion]

## Criterios de aceptación

Por definir en refinamiento.

## Notas técnicas

- Capturado con /timonel:draft. Refinar con /timonel:refine antes de implementar.
MD
gh issue create -R "$REPO" --title "<titulo>" --label "estado:borrador" --label "<tipo>" [--label "mod:<m>"] [--label bug] --body-file "$BODY"
```

3. Responde con el `#N`, el titulo y los labels. Nada mas.

## Reglas

- Nunca `estado:listo` desde aqui.
- Nunca preguntes: si hay duda, omite el label.
