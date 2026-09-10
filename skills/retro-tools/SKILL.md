---
name: retro-tools
description: Herramientas de retrospectiva y code review sobre el backlog en GitHub Issues. Consulta y destila las retros (comentarios timonel:retro) y los reviews (timonel:review) sin gastar tokens, y publica los insights en issues dedicados. Usa antes de planificar o implementar en un modulo, o cuando quieras destilar insights acumulados.
---

Scripts Python (stdlib + `gh`) en `PLUGIN_ROOT/scripts/`. Todos leen `github.repo` de `.claude/timonel.config.json`; `--repo owner/repo` lo sobreescribe.

```bash
PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
S="$PLUGIN_ROOT/scripts"
```

## Retros (`<!-- timonel:retro -->`)

```bash
python3 "$S/retro_query.py" --modulo mis-finanzas
python3 "$S/retro_query.py" --epica 12                    # HUs hijas del issue #12
python3 "$S/retro_query.py" --issue 42
python3 "$S/retro_query.py" --seccion "Errores recurrentes"
python3 "$S/retro_distill.py"                              # reporte a stdout
python3 "$S/retro_distill.py" --publish                    # upsert issue "Insights destilados de retrospectivas" (label insights)
```

El destilado incluye calibracion de estimaciones por modulo/alcance, errores recurrentes (2+), patrones candidatos a convencion (2+) y todas las mejoras sugeridas.

## Reviews (`<!-- timonel:review -->`)

```bash
python3 "$S/review_query.py" --modulo mis-finanzas
python3 "$S/review_query.py" --severidad CRITICO
python3 "$S/review_query.py" --tipo Heuristica
python3 "$S/review_query.py" --veredicto "REQUIERE CAMBIOS"   # o --solo-bloqueantes
python3 "$S/review_distill.py" [--publish]                     # issue "Insights destilados de code reviews"
```

`--severidad` y `--tipo` filtran hallazgos dentro de cada review; `--modulo`, `--epica`, `--issue`, `--veredicto` filtran reviews completos.

## Formato fuente

Los comentarios con marcador se describen en `PLUGIN_ROOT/skills/github-issues/references/marcadores.md`. `modulo` y `alcance` se toman del YAML del comentario y, si faltan, de los labels `mod:*` / `alcance:*` del issue. Filtrar por `--epica` usa los sub-issues nativos del issue padre.

## Uso recomendado

- `user-story-planner` y `flechodiezx` consultan `retro_query.py --modulo` antes de estimar o definir el contrato.
- `backlog-refiner` consulta `review_query.py --solo-bloqueantes` para repriorizar con evidencia.
- `/timonel:insights` corre ambos `--publish` y pinnea los issues resultantes.
