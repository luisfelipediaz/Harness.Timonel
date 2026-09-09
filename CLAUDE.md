# CLAUDE.md — timonel

Plugin de Claude Code (`.claude-plugin/plugin.json`) que empaqueta el harness de planificación e implementación de historias para monorepos Nx Angular + NestJS con backlog en GitHub Issues.

## Principios

- Comunícate en **español**.
- Los agentes **no hardcodean rutas del consumidor**: todo sale de `.claude/timonel.config.json` (TIM-ADR-0002).
- La fuente de verdad del backlog es GitHub (TIM-ADR-0001). Ningún agente escribe HUs, SDD, retros o reviews como archivos en el consumidor.
- El formato de issues y comentarios vive en un solo lugar: `skills/github-issues/`. Los demás skills y agentes lo referencian, no lo duplican.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `agents/` | Orquestadores (opus): `sdd-planner`, `user-story-planner`, `backlog-refiner`, `story-executor`, `hotfix-executor` |
| `commands/` | Slash commands `/timonel:*` (lanzadores delgados, haiku/sonnet) |
| `skills/` | Skills de implementación y del ciclo + `github-issues` (plantillas/recetas) + `retro-tools` |
| `scripts/` | `_common.sh`, `setup-github-labels.sh`, `timonel_gh.py`, `retro_*.py`, `review_*.py`, `migrate_backlog.py` |
| `heuristics/` | Heurísticas de código que consume `code-review` |
| `hooks/` | `SessionStart` escribe `.timonel/.plugin-root`; `PostToolUse` loguea `gh issue *` |
| `docs/adr/` | `TIM-ADR-000N` decisiones del marco |
| `docs/superpowers/specs/` | Spec de diseño de la extracción |
| `tests/` | `unittest` stdlib; `python3 -m unittest discover -s tests` |

## Convenciones al editar el plugin

- Agentes: frontmatter `name`, `description`, `model`, `color`, `skills: [github-issues]`. Empiezan leyendo el config y resolviendo `PLUGIN_ROOT`.
- Commands: frontmatter `description`, `argument-hint`, `model`. No implementan: validan y lanzan al agente.
- Skills: frontmatter `name`, `description` (con cuándo usarlo). Parámetros de entrada en tabla; reporte de salida en bloque fijo.
- Cambios de formato de issue/comentario → actualizar `skills/github-issues/references/*.md`, `scripts/timonel_gh.py` y sus tests en el mismo commit.
- Versionado semver en `plugin.json` + entrada en `CHANGELOG.md`.
- Python: stdlib puro, sin `any`-equivalentes (`dict` tipados), lookup maps antes que cadenas de `if` (ver `heuristics/general/evitar-ifs.md`).

## Verificación antes de commit

```bash
python3 -m unittest discover -s tests
bash -n scripts/*.sh
jq . .claude-plugin/plugin.json .claude-plugin/marketplace.json hooks/hooks.json >/dev/null
```
