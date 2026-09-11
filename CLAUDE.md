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
| `agents/` | `sdd-planner`, `user-story-planner`, `backlog-refiner`, `harness-auditor` (opus); `flechodiezx`, `flechodiezx-hotfix` (opus, orquestan); `dora-exploradora` (sonnet, investiga) |
| `commands/` | Slash commands `/timonel:*` (lanzadores delgados, haiku/sonnet) |
| `skills/` | Skills de implementación y del ciclo + `github-issues` (plantillas/recetas) + `retro-tools` |
| `scripts/` | `_common.sh`, `setup-github-labels.sh`, `install-git-hooks.sh`, `timonel_gh.py`, `retro_query.py`, `retro_distill.py`, `review_query.py`, `review_distill.py`, `metricas_flujo.py`, `migrate_backlog.py`, y los sensores `dor_check.py`, `validar_marcador.py`, `estado_historia.py`, `contrato_check.py`, `cosechar_retro.py`, `smoke_harness.py`, `eval_dor.py`, `integracion.py` |
| `heuristics/` | Heurísticas de código que consume `code-review` |
| `evals/` | Casos `prompt.md` + `graders/*.md` para `claude plugin eval`, uno por agente/skill (`evals/<agente-o-skill>/<caso>/`) |
| `hooks/` | `SessionStart`: `.timonel/.plugin-root`, aviso de config faltante, aviso de versión nueva. `PreToolUse`: issue obligatorio en commits del plugin; en consumidores protege ramas base, bloquea `push --force`, exige `#N` en ramas `hu/`. `PostToolUse`: loguea `gh issue *` y avisa al editar archivos raíz (`modelos.path`, `moduleFile`, `routesFile`) |
| `docs/adr/` | `TIM-ADR-000N` decisiones del marco |
| `docs/superpowers/specs/` | Spec de diseño de la extracción |
| `.github/workflows/ci.yml` | CI: unittest, `bash -n`, `jq`, labels dry-run, `#issue` en commits de PR |
| `tests/` | `unittest` stdlib; `python3 -m unittest discover -s tests` |

## Gobernanza (TIM-ADR-0005)

- **Todo cambio nace en un issue de este repo** (`tipo:hu|hotfix`, `mod:plugin`, agrupado en la épica de la versión). Capturalo con `/timonel:draft` o `gh issue create -R luisfelipediaz/Harness.Timonel`.
- **Todo commit referencia el issue** (`#N`). Lo exige `.githooks/commit-msg` (activar con `scripts/install-git-hooks.sh`) y el hook `PreToolUse` del plugin cuando corre en este repo.
- **El plugin se desarrolla con Timonel** (#27): `/timonel:implement #N` detecta el perfil `plugin` (sin nx): rama `hu/N-*`, Dora, contrato de cambio, sub-agente con `implement-plugin-change`, consolidación (unittest, `bash -n`, `jq`, línea en CHANGELOG), review, retro (+ cosecha), PR abierto con `integracion.py` antes del DoD, y DoD. El hook bloquea `git commit` en `main`.
- Al cerrar la épica de la versión: `git tag vX.Y.Z` + `gh release create`; CHANGELOG pasa de "en desarrollo" a la fecha; se cierran los issues con el comentario de DoD.

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
claude plugin eval . --no-publish   # early access: si responde "currently in early access", deja los casos y sigue
```
