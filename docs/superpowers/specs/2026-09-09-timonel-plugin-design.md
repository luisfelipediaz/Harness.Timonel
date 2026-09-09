# Timonel — Diseño del plugin (extracción del harness SDD del Portal)

**Fecha:** 2026-09-09
**Estado:** Aprobado por diseño autónomo bajo `/goal`; supuestos marcados con ⚠️

## 1. Problema

El harness de desarrollo asistido de `Bitakora.MonoRepo.Portal` (4 agentes, 8 skills, 6 scripts Python) vive en `.claude/` de ese repo y:

1. Está acoplado al proyecto por strings hardcodeados (`apps/client`, `@bitakora.monorepo.portal/modelos`, `app-routing.module.ts`, "Angular 20 + NestJS 10"). La copia en `Bitakora.POC.Organigrama` diverge exactamente en esas rutas.
2. Persiste todo el estado en documentos markdown: `docs/user-stories/BACKLOG.md`, `hu-XXX.md`, `hu-XXX.retro.md`, `hu-XXX.review.md`, `completadas.md`, `refinamientos/`, y los SDD en `docs/especificaciones/`.
3. No es instalable: cada repo copia y adapta a mano.

## 2. Objetivo

Un **plugin de Claude Code** (`timonel`), publicado en `github.com/luisfelipediaz/Harness.Timonel` con su propio marketplace, instalable en cualquier monorepo Nx Angular + NestJS, donde **las HU, épicas, SDD, contratos API, reviews, retros y DoD viven en GitHub Issues**, no en archivos.

## 3. No objetivos

- GitHub Projects v2 (requiere scope `project`; overhead innecesario para el tamaño de equipo). Queda documentado como extensión futura.
- Integración con PRs de GitHub (los repos consumidores actuales están en Azure DevOps).
- Generalizar más allá de Nx + Angular + NestJS.

## 4. Arquitectura del plugin

```
timonel/
├── .claude-plugin/plugin.json          # name=timonel, version semver
├── .claude-plugin/marketplace.json     # name=luisfelipediaz-harness, source ./
├── agents/                             # orquestadores (opus)
│   ├── sdd-planner.md                  # NUEVO — SDD como issue padre
│   ├── user-story-planner.md           # épicas + HUs como sub-issues
│   ├── backlog-refiner.md              # mantiene issues abiertos
│   ├── story-executor.md               # 7 fases sobre un issue
│   └── hotfix-executor.md              # ≤2 SP sin worktrees
├── commands/                           # slash commands /timonel:*
│   ├── onboard.md   plan.md   sdd.md   refine.md   implement.md
│   ├── hotfix.md    draft.md  insights.md  backlog.md  migrate.md
├── skills/
│   ├── github-issues/                  # NUEVO — plantillas + recetas gh (fuente única)
│   ├── implement-backend-story/  implement-frontend-story/  consolidate-story/
│   ├── code-review/  generate-retro/  verify-dod/  retro-tools/  ngrx-signal-store/
├── scripts/
│   ├── _common.sh                      # load_timonel_config, resolve_plugin_root
│   ├── setup-github-labels.sh          # idempotente
│   ├── timonel_gh.py                   # wrapper gh + parsers de marcadores
│   ├── retro_query.py  retro_distill.py  review_query.py  review_distill.py
│   └── migrate_backlog.py              # docs/user-stories → issues (dry-run default)
├── heuristics/general/*.md  heuristics/angular/*.md
├── hooks/hooks.json                    # SessionStart: .timonel/.plugin-root
├── docs/adr/TIM-ADR-000N-*.md
├── tests/                              # unittest, stdlib puro
└── README.md  CLAUDE.md  CHANGELOG.md  LICENSE
```

## 5. Contrato con el consumidor: `.claude/timonel.config.json`

```json
{
  "projectName": "Bitakora.MonoRepo.Portal",
  "github": { "repo": "owner/repo-de-issues" },
  "stack": { "frontend": "Angular 21", "backend": "NestJS 10", "estado": "NgRx Signal Store" },
  "api": { "project": "api", "path": "apps/api", "moduleFile": "apps/api/src/app/app.module.ts" },
  "frontends": [
    { "project": "client", "path": "apps/client", "routesFile": "apps/client/src/app/app-routing.module.ts" }
  ],
  "modelos": { "alias": "@bitakora.monorepo.portal/modelos", "path": "libs/modelos" },
  "modulos": ["mis-finanzas", "vacaciones"],
  "heuristicsDir": null
}
```

- `github.repo` es el repo GitHub donde viven los issues. ⚠️ Puede diferir del remote del código (Portal y POC están en Azure DevOps).
- `frontends[]` admite varias apps (caso POC: `bitakora` y `mibitakora`). La HU declara la app destino en su Ficha Técnica cuando hay más de una.
- `modulos[]` alimenta los labels `mod:*`.
- `heuristicsDir` `null` → usa `heuristics/` del plugin; ruta → usa esa carpeta.
- `/timonel:onboard` genera el archivo leyendo `nx.json`, `tsconfig.base.json` (`paths`), `apps/*/project.json` y `git remote`, y luego corre `setup-github-labels.sh`.

Los agentes leen este archivo al inicio y **nunca** hardcodean rutas.

## 6. Modelo de datos en GitHub

### 6.1 Jerarquía (sub-issues nativos)

```
tipo:sdd  (issue)            ← Software Design Document
 └── tipo:epica (sub-issue)  ← épica
      └── tipo:hu (sub-issue) ← historia de usuario
```

Un SDD puede omitirse: una épica puede ser raíz. Una HU puede ser raíz solo si es `tipo:hotfix`. La relación se crea con la mutación GraphQL `addSubIssue` (verificada disponible). GitHub muestra el progreso de sub-issues en el padre automáticamente.

### 6.2 Identidad

El **número de issue** es el identificador. Se abandona `HU-XXX`. Títulos: `[verbo infinitivo] [qué cosa]`, sin prefijos. Las HU migradas conservan una línea `Id histórico: HU-097` al inicio del body.

### 6.3 Labels (facetas)

| Eje | Valores | Notas |
| --- | --- | --- |
| `tipo:` | `sdd`, `epica`, `hu`, `hotfix` | Exactamente uno |
| `estado:` | `borrador`, `listo`, `en-progreso` | Cerrado = done. Exactamente uno mientras está abierto |
| `alcance:` | `backend`, `frontend`, `full-stack` | Solo `hu`/`hotfix` |
| `moscow:` | `must`, `should`, `could`, `wont` | Solo `hu` |
| `sp:` | `1`, `2`, `3`, `5`, `8`, `13`, `21` | Solo `hu`/`hotfix` |
| `prioridad:` | `alta`, `media`, `baja` | Solo `hu` |
| `mod:` | uno por `modulos[]` del config | Módulo destino |
| `review:` | `aprobado`, `observaciones`, `requiere-cambios` | Lo pone `code-review` |
| `retro:` | `subestimado`, `preciso`, `sobreestimado` | Lo pone `generate-retro` |
| especiales | `bloqueado`, `bug`, `duplicada`, `obsoleta`, `insights` | |

`setup-github-labels.sh` los crea de forma idempotente (crea si falta, actualiza color/descripción si existe).

### 6.4 Body de la HU (plantilla en `skills/github-issues/references/plantilla-hu.md`)

Secciones fijas, en este orden (parseables por prefijo `## `):

1. `## Historia` — Como / quiero / para
2. `## Criterios de aceptación` — bloque ```gherkin
3. `## INVEST` — tabla
4. `## Ficha técnica` — tabla (Alcance, Entidad principal, Tipo de operación, Permiso requerido, Módulo destino, App destino si aplica)
5. `## Endpoints` — o `Ninguno`
6. `## Modelos compartidos` — o `Ninguno`
7. `## Notas técnicas` — opcional
8. `## Dependencias` — líneas `Depende de #N` o `Ninguna`
9. `## Tareas` — checklist que el executor mantiene:
   ```
   - [ ] Contrato API aprobado
   - [ ] Modelos compartidos
   - [ ] Backend
   - [ ] Frontend
   - [ ] Consolidación (lint + tests)
   - [ ] Code review
   - [ ] Retrospectiva
   - [ ] Definition of Done
   ```

MoSCoW, SP y prioridad van **solo en labels** (no se duplican en el body).

### 6.5 Body del SDD (plantilla `plantilla-sdd.md`)

Secciones tomadas de los SDD reales del Portal/POC: Resumen ejecutivo, Contexto y motivación, Alcance (in/out, módulos afectados), Requisitos funcionales (`RF-NN`), Requisitos no funcionales, Contrato de datos y API, Diseño de componentes / estado, Estrategia de pruebas, Riesgos y mitigaciones, Decisiones (tabla decisión / alternativas / razón), Dudas abiertas. Si el body supera 60.000 caracteres, las secciones 6–8 se publican como comentarios con marcador `<!-- timonel:sdd:seccion=N -->` y el body deja un índice.

### 6.6 Comentarios con marcadores (artefactos del ciclo)

Cada fase publica **un comentario** en la HU con un marcador HTML en la primera línea y un bloque YAML parseable:

| Marcador | Quién | Contenido |
| --- | --- | --- |
| `<!-- timonel:contrato-api -->` | story-executor F2 | Contrato aprobado por el usuario |
| `<!-- timonel:consolidacion -->` | consolidate-story | Reporte ARCHIVOS_*, LINT, TESTS |
| `<!-- timonel:review -->` | code-review | YAML (veredicto, criticos, warnings, bloquea_dod) + tabla de hallazgos |
| `<!-- timonel:retro -->` | generate-retro | YAML (estimado_sp, real_sp, precision) + 4 secciones |
| `<!-- timonel:dod -->` | verify-dod | Tabla de 11 items + decisión |
| `<!-- timonel:refinamiento -->` | backlog-refiner | Reporte del refinamiento (en la épica) |

Reglas: un marcador por tipo por issue; si se repite la fase, se **edita** el comentario existente (`gh api PATCH`) en vez de duplicar. Los scripts de `retro-tools` parsean estos comentarios.

### 6.7 Ciclo de vida de una HU

1. planner crea `tipo:hu` + `estado:borrador` (o `estado:listo` si cumple DoR) como sub-issue de su épica.
2. refiner puede dividir (crea sub-issues hermanas, edita la original), repriorizar (labels), marcar `duplicada`/`obsoleta` (label + cierre `not_planned`).
3. `/timonel:implement N`: valida DoR y `bloqueado` → `estado:en-progreso`, asignee = usuario `gh`, rama `hu/N-slug`; comentario contrato; sub-agentes; marca tareas; comentarios review/retro/dod; labels `review:*`, `retro:*`.
4. DoD `DONE` → `gh issue close N --reason completed`. Si hay fallas críticas queda abierto en `estado:en-progreso` con el comentario DoD explicando.

### 6.8 Insights

`retro_distill.py --publish` y `review_distill.py --publish` hacen upsert de un issue `insights` titulado `Insights destilados de retrospectivas` / `... de code reviews` (body reemplazado, pin sugerido). Sin `--publish` imprimen a stdout.

## 7. Cambios en agentes y skills (respecto al harness original)

- **Contexto**: cada agente abre con "Lee `.claude/timonel.config.json` y `CLAUDE.md` del consumidor" y usa `{config.*}` en lugar de rutas fijas.
- **Fuente**: donde decía "lee `hu-XXX.md`" ahora `gh issue view N --json title,body,labels,comments`.
- **Persistencia**: donde escribía archivos ahora publica comentarios/labels/cierres según §6.6.
- **DoD item 8** pasa de "marcada `[x]` en BACKLOG" a "checklist `## Tareas` completa e issue cerrable".
- **code-review** referencia heurísticas en `${PLUGIN_ROOT}/heuristics/` (o `heuristicsDir`).
- **story-executor** ya no lista el BACKLOG para elegir: si no recibe número, muestra `gh issue list --label tipo:hu --label estado:listo`.
- **hotfix-executor** caso B crea el issue `tipo:hotfix` (raíz) en vez de un archivo.
- **user-story-planner** crea épica primero y HUs como sub-issues; valida DoR antes de `estado:listo`.
- **sdd-planner** (nuevo): entrevista → SDD issue → propone épicas → delega HUs al planner.
- Skills de implementación reciben del orquestador el body del issue (sin cambios de fondo) y leen `config.frontends[]` para la app destino.

## 8. Migración del backlog existente

`scripts/migrate_backlog.py --docs docs/user-stories --repo owner/repo [--apply]`:

1. Parsea `BACKLOG.md`: épicas (`### Epica N: título`) y líneas `- [x|\ ] [HU-XXX](ruta): título — MoSCoW (N SP)`, incluidos tachados `~~` (obsoletas/reemplazadas).
2. Para cada HU localiza su spec: archivo individual o sección `## HU-XXX:` dentro de `completadas.md`.
3. Crea épicas (`tipo:epica`) y HUs como sub-issues con labels derivados (moscow, sp, alcance y módulo desde la Ficha Técnica, `mod:` si está en config).
4. Completadas → cierra `completed`; tachadas → `obsoleta` + cierre `not_planned`.
5. Si existe `.retro.md` / `.review.md` → comentario con marcador.
6. Reescribe `Dependencias: HU-XXX` → `Depende de #N` con el mapa HU→issue.
7. `--apply` ausente = dry-run que imprime el plan. Idempotente por `Id histórico: HU-XXX` (busca antes de crear).

## 9. Testing

- `tests/test_migrate_parse.py`: parseo de BACKLOG (incl. tachados), extracción de Ficha Técnica, HU en `completadas.md`, mapeo de labels.
- `tests/test_markers.py`: parseo de comentarios con marcador (retro y review) y frontmatter YAML plano.
- `tests/test_labels.sh`: `setup-github-labels.sh --dry-run` lista el conjunto completo esperado.
- Dogfooding: el repo `timonel` usa sus propios labels y un backlog real en issues; verificación manual de `addSubIssue` contra ese repo.

## 10. Instalación en el consumidor

```json
{
  "extraKnownMarketplaces": {
    "luisfelipediaz-harness": { "source": { "source": "github", "repo": "luisfelipediaz/Harness.Timonel" } }
  },
  "enabledPlugins": { "timonel@luisfelipediaz-harness": true }
}
```

Luego `/timonel:onboard`. El repo `timonel` se crea **privado** ⚠️ porque contiene convenciones internas de Sinco; el usuario decide si lo abre.

## 11. Portal

Rama local `harness/timonel-plugin` (sin push): elimina `.claude/agents/` y `.claude/skills/`, agrega `timonel.config.json` con `github.repo` placeholder ⚠️, habilita el plugin en `.claude/settings.json`, reescribe la sección "Workflow de Desarrollo (Harness)" de `CLAUDE.md`, ignora `.timonel/`. Los `docs/user-stories/` se conservan hasta correr `/timonel:migrate --apply` contra el repo de issues que se defina. `agente-actualizacion-*.md` no forman parte del harness y se quedan.
