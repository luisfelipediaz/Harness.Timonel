# Changelog

## 0.3.0 — 2026-09-10

Épica #4. Incorpora lo rescatable del harness de `Cosmos.BuildingBlocks` y formaliza la gobernanza del plugin.

### Añadido

- Agente **`dora-exploradora`** (#7) y skill `investigar`: investigación acotada del código y docs antes del contrato API; publica `<!-- timonel:investigacion -->` y reutiliza investigaciones previas del módulo. Nueva Fase 1.5 en `flechodiezx` (y ligera en `flechodiezx-hotfix`); comando `/timonel:investigar`.
- Agente **`harness-auditor`** (#8) y comando `/timonel:audit`: clasifica artefactos y transiciones del flujo en HARNESS / SEMI / AD-HOC, persiste issue `harness-audit` y compara con el anterior. Label `harness-audit`.
- Sección **Harness engineering** obligatoria en la retro (#9): patrón repetitivo, proceso manual 2+, contexto faltante, error prevenible.
- Regla de alcance en `implement-backend-story` / `implement-frontend-story` (#9): no tocar archivos fuera de la tarea.
- **Gobernanza** (#5, TIM-ADR-0005): todo cambio del plugin nace en un issue del repo; `.githooks/commit-msg` + `scripts/install-git-hooks.sh` y hook `PreToolUse` bloquean commits sin `#N`. Los comandos funcionan dentro del repo del plugin usando `gh repo view` como repo de issues.

### Cambiado

- Ejecutores renombrados (#6): `story-executor` → **`flechodiezx`**, `hotfix-executor` → **`flechodiezx-hotfix`**.

## 0.2.0 — 2026-09-10

### Añadido

- Skill `interrogame` (rescatado de `Bitakora.MonoRepo.Portal` rama `feature/fal/notificaciones`): entrevista exhaustiva una pregunta a la vez con respuesta recomendada, con bloques A–J para diseño de software.
- `sdd-planner` precarga `interrogame`, explora el código antes de preguntar y lee el skill `*-estructura` del consumidor si existe.
- Plantilla de SDD ampliada a 15 secciones fusionando el agente `sdd-specs` del Portal (RF con actor/precondición/flujo, RNF en tabla, archivos nuevos por capa, seguridad, plan de despliegue, criterios de aceptación, dudas abiertas con responsable).

### Notas

- `portal-estructura` no entra al plugin: es específico del Portal y se restauró en su `.claude/skills/`.

## 0.1.0 — 2026-09-09

Extracción del harness SDD de `Bitakora.MonoRepo.Portal/.claude` como plugin (TIM-ADR-0004).

### Añadido

- Plugin `timonel` con marketplace propio (`luisfelipediaz-harness`).
- Backlog en GitHub Issues: jerarquía `tipo:sdd → tipo:epica → tipo:hu` con sub-issues nativos, labels facetados, comentarios con marcador para contrato API, consolidación, review, retro, DoD y refinamiento (TIM-ADR-0001).
- Configuración del consumidor `.claude/timonel.config.json` y comando `/timonel:onboard` (TIM-ADR-0002).
- Definition of Ready por tipo de issue y validación en `/timonel:implement` y `/timonel:hotfix` (TIM-ADR-0003).
- Agente nuevo `sdd-planner`: SDD como issue, versionado en el mismo issue, derivación de épicas.
- Comandos `sdd`, `plan`, `refine`, `draft`, `implement`, `hotfix`, `backlog`, `insights`, `migrate`.
- Skill `github-issues` con plantillas (HU, hotfix, épica, SDD), formato de marcadores y esquema de labels.
- Scripts `retro_query`, `retro_distill`, `review_query`, `review_distill` leyendo de GitHub; `--publish` hace upsert de issues `insights`.
- `migrate_backlog.py`: importa `docs/user-stories` (incluidas `completadas.md`, tachadas y retros/reviews) de forma idempotente.
- `setup-github-labels.sh` idempotente con `--dry-run` y `--prune-defaults`.
- Heurísticas de código incluidas en el plugin (`heuristics/`).
- Tests `unittest` para parsers, destilado y migración.

### Cambiado respecto al harness original

- Agentes y skills parametrizados por config (sin `apps/client`, alias ni `app-routing.module.ts` hardcodeados; soporte para varias apps frontend).
- `HU-XXX` reemplazado por el número de issue; MoSCoW/SP/prioridad pasan a labels.
- DoD item 8: "marcada en BACKLOG" → "checklist `## Tareas` completo"; DoD `DONE` cierra el issue.
- `code-review`, `generate-retro`, `verify-dod`, `consolidate-story` publican en el issue en vez de escribir archivos.
