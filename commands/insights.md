---
description: "Destila retros y code reviews del backlog y publica/actualiza los issues de insights (label insights)."
argument-hint: "[--solo-retro | --solo-review] [--no-publicar]"
model: haiku
---

Genera los insights destilados del backlog. Comunicate en **espanol**.

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ 2>/dev/null | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
S="$PLUGIN_ROOT/scripts"
```

Segun `$ARGUMENTS`:

- Sin `--solo-review`: `python3 "$S/retro_distill.py" --publish` (sin `--publish` si viene `--no-publicar`).
- Sin `--solo-retro`: `python3 "$S/review_distill.py" --publish` (idem).
- Siempre: `python3 "$S/metricas_flujo.py" --publish` (issue "Métricas de flujo": cobertura de artefactos, review a la primera, precision, lead time, backlog por estado).

Si publico, pinnea los issues (`gh issue pin N -R "$REPO"`; ignora el error si ya estan pinneados o si hay mas de 3 pins).

Reporta los `#N` actualizados y las 3 lineas mas relevantes de cada reporte (errores recurrentes con mas ocurrencias, tendencia de estimacion, archivo mas problematico, % de HUs cerradas sin retro/review).
