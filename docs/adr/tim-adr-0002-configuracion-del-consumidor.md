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
| `git.protectBase` (opcional) | **Deprecado e ignorado desde v0.6.0** (#85): el hook de commits bloquea siempre la rama base, sin leer este flag. Se deprecó porque `guard_integracion.py` (#82) ya bloqueaba el `push`/`merge`/PR a la base aunque `protectBase: false` permitiera comitear ahí en local — la "salida" llevaba a commits locales impublicables, una incoherencia entre dos guards, no una opción útil |
| `git.integracion` (opcional) | Unico valor valido: `"pr"` (default y unica via desde v0.6.0) abre PR en la Fase 6.5, antes del DoD (GitHub con `gh`, Azure DevOps con `az repos`). `"merge"` queda **deprecado e ignorado** desde v0.6.0: ya no existe camino de merge directo a la rama base, ni en el consumidor ni en el propio plugin |
| `timonel.repo` (opcional) | Repo del plugin al que `cosechar_retro.py` envia las mejoras que apuntan al harness (default `luisfelipediaz/Harness.Timonel`) |

`/timonel:onboard` genera el archivo por inspección (`nx.json`, `tsconfig.base.json.paths`, `apps/*/project.json`, `git remote`) y pide confirmación. Los agentes lo leen al inicio y fallan con mensaje claro si falta.

Se nombra `timonel.config.json` y no `harness.config.json` para convivir con Mefisto en el mismo repo (el POC tiene ambos).

## Control de cambios

- 2026-09-10 (v0.4.0, #15 #13): se agregan `git.baseBranches`, `git.protectBase` y `timonel.repo`.
- 2026-09-10 (v0.5.0, #31): se agrega `git.integracion`.
- 2026-09-11 (v0.6.0, #80): `git.integracion` pasa a tener un unico valor valido, `"pr"`; `"merge"` queda deprecado e ignorado — el PR es la unica via de integracion, tambien en el perfil plugin.
- 2026-09-15 (v0.6.0, #85): `git.protectBase` pasa a estar deprecado e ignorado; el guard de commits bloquea la rama base incondicionalmente, alineado con `guard_integracion.py`.

## Consecuencias

- Los agentes no contienen rutas del proyecto; un solo plugin sirve al Portal y al POC.
- El onboarding tiene un paso más, pero se ejecuta una vez por repo.
