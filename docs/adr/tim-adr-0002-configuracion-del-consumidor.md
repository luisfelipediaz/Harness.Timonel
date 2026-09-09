# TIM-ADR-0002: Parametrización del consumidor vía `.claude/timonel.config.json`

**Fecha**: 2026-09-09
**Estado**: Aceptado

## Contexto

Los agentes del harness original decían literalmente `apps/client`, `@bitakora.monorepo.portal/modelos`, `app-routing.module.ts`, "Angular 20 + NestJS 10". Al copiar el harness al POC Organigrama hubo que editar seis archivos para cambiar solo esas rutas (dos apps frontend, otro alias, `app.routes.ts`). Un plugin no puede editarse por consumidor.

## Decisión

Todo dato específico del proyecto vive en `.claude/timonel.config.json` del consumidor:

| Campo | Uso |
| --- | --- |
| `projectName` | Contexto en prompts |
| `github.repo` | Repo `owner/repo` donde viven los issues (`gh -R`) |
| `stack.frontend`, `stack.backend`, `stack.estado` | Contexto en prompts y en la ficha técnica |
| `api.project`, `api.path`, `api.moduleFile` | `nx lint <project>`, exploración acotada, registro de providers |
| `frontends[].project/path/routesFile` | Igual que api, por app. Si hay más de una, la HU declara "App destino" |
| `modelos.alias`, `modelos.path` | Import de modelos compartidos y ubicación |
| `modulos[]` | Labels `mod:*` y validación del módulo destino |
| `heuristicsDir` | `null` → `heuristics/` del plugin; ruta → carpeta propia |

`/timonel:onboard` genera el archivo por inspección (`nx.json`, `tsconfig.base.json.paths`, `apps/*/project.json`, `git remote`) y pide confirmación. Los agentes lo leen al inicio y fallan con mensaje claro si falta.

Se nombra `timonel.config.json` y no `harness.config.json` para convivir con Mefisto en el mismo repo (el POC tiene ambos).

## Consecuencias

- Los agentes no contienen rutas del proyecto; un solo plugin sirve al Portal y al POC.
- El onboarding tiene un paso más, pero se ejecuta una vez por repo.
