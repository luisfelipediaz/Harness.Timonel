---
name: consolidate-story
description: Consolida e integra los worktrees de una historia implementada en paralelo (backend + frontend), registra providers y rutas en los archivos raiz que indica el config, marca las tareas en el issue de GitHub, publica el comentario timonel:consolidacion y verifica calidad con lint + tests. Usa cuando los sub-agentes de implementacion han terminado y necesitas mergear a la rama de la historia y dejar el codigo listo para review, retro y DoD.
---

Integra los branches de implementacion a la rama actual (`hu/N-slug`), registra lo que los sub-agentes no pudieron tocar, actualiza el issue y ejecuta verificacion fail-fast. Siempre en espanol.

## Parametros de entrada

| Parametro | Descripcion |
| --- | --- |
| `issue` | Numero del issue (ej: `42`) |
| `repo` | `owner/repo` de GitHub (config `github.repo`) |
| `modulo` | Modulo destino (ej: `mis-finanzas`) |
| `alcance` | `Backend` \| `Frontend` \| `Full-stack` |
| `app_destino` | `project` de la app frontend (de `frontends[]`), o `N/A` |
| `branch_worktree_backend` / `branch_worktree_frontend` | Branch de cada sub-agente, o `N/A` |
| `output_sub_agente_backend` / `output_sub_agente_frontend` | Resumen del output (archivos, providers/rutas a registrar) |
| `api_module_file`, `api_project` | `config.api.moduleFile`, `config.api.project` |
| `frontend_routes_file`, `frontend_project` | `routesFile` y `project` de la app destino |

Si falta alguno, detente y reporta cual.

## Fase A: Consolidacion

1. **Merge** solo de branches distintos de `N/A`:
   ```bash
   git merge <branch_worktree_backend>  --no-ff -m "feat(<modulo>): backend #<issue>"
   git merge <branch_worktree_frontend> --no-ff -m "feat(<modulo>): frontend #<issue>"
   ```
   Los worktrees tocan carpetas distintas; si hay conflictos, conserva ambas implementaciones. Si no puedes, detente y reporta los archivos.
2. **Providers** (si el alcance incluye Backend): agrega a `<api_module_file>` lo que documento el sub-agente backend.
3. **Rutas** (si incluye Frontend): agrega a `<frontend_routes_file>` las rutas lazy documentadas.
4. Commit: `git commit -am "chore(<modulo>): registrar providers/rutas #<issue>"` si hubo cambios.

## Fase B: Verificacion fail-fast

Si lint falla, **no** corras tests.

```bash
nx lint <api_project>        # si incluye Backend
nx lint <frontend_project>   # si incluye Frontend
nx test <api_project> --testFile=<modulo>        # solo si lint paso
nx test <frontend_project> --testFile=<modulo>   # solo si lint paso
```

Ante fallos: corrige directo (prettier → `npm run prettier`), maximo **2 intentos** por comando, commit `fix(<modulo>): <breve> #<issue>`. Si persiste, incluye el error exacto en el reporte y marca `FAILED`.

## Fase C: Actualizar el issue

Sigue el skill `github-issues` (`PLUGIN_ROOT/skills/github-issues/SKILL.md`):

1. Marca en `## Tareas`: `- [x] Consolidación (lint + tests)` solo si lint y tests son `PASSED` o `NO_SPECS`.
2. Publica `<!-- timonel:consolidacion -->` con el formato de `references/marcadores.md` (YAML: fecha, lint, tests, providers_registrados, rutas_registradas; secciones Archivos, Correcciones aplicadas, Pendientes y notas de migracion). Valida con `python3 PLUGIN_ROOT/scripts/validar_marcador.py <archivo> --tipo consolidacion` y luego `publicar_marcador` (edita si ya existe).

## Reporte de salida (obligatorio)

```
ARCHIVOS_BACKEND: [lista en <api.path>, o "N/A"]
ARCHIVOS_FRONTEND: [lista en <frontend.path>, o "N/A"]
MODELOS_COMPARTIDOS: [lista en <modelos.path>, o "N/A"]
PROVIDERS_REGISTRADOS: [si | no | n-a]
RUTAS_REGISTRADAS: [si | no | n-a]
TAREAS_MARCADAS: [si | no]
LINT_RESULTADO: [PASSED | FAILED | <error exacto>]
TESTS_RESULTADO: [PASSED | FAILED | NO_SPECS | <error exacto>]
ERRORES_CORREGIDOS: [descripcion breve, o "Ninguno"]
PENDIENTES: [lista, o "Ninguno"]
NOTAS_MIGRACION: [env vars, cambios de BD, o "Ninguno"]
```

## Manejo de errores

- Conflicto inesperado: no fuerces; detente y reporta.
- Branch inexistente: marca ese merge como fallido y sigue con el otro.
- Lint/test persiste tras 2 intentos: `FAILED` + error exacto; no sigas intentando.
- Fallo al publicar en GitHub: reporta igual el bloque completo; el orquestador reintenta la publicacion.
