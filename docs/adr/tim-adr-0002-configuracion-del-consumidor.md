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
| `git.baseBranches` (opcional) | Ramas protegidas por el hook `PreToolUse` (default `["main","master","develop"]`): no se permite `git commit` directo durante el trabajo del harness |
| `git.protectBase` (opcional) | `true` (default) activa ese bloqueo; `false` lo desactiva en repos que commitean a main |
| `timonel.repo` (opcional) | Repo del plugin al que `cosechar_retro.py` envia las mejoras que apuntan al harness (default `luisfelipediaz/Harness.Timonel`) |

`/timonel:onboard` genera el archivo por inspección (`nx.json`, `tsconfig.base.json.paths`, `apps/*/project.json`, `git remote`) y pide confirmación. Los agentes lo leen al inicio y fallan con mensaje claro si falta.

Se nombra `timonel.config.json` y no `harness.config.json` para convivir con Mefisto en el mismo repo (el POC tiene ambos).

## Control de cambios

- 2026-09-10 (v0.4.0, #15 #13): se agregan `git.baseBranches`, `git.protectBase` y `timonel.repo`.

## Consecuencias

- Los agentes no contienen rutas del proyecto; un solo plugin sirve al Portal y al POC.
- El onboarding tiene un paso más, pero se ejecuta una vez por repo.
