---
name: verify-dod
description: Valida la Definition of Done de una historia ejecutando una checklist de 11 items (codigo commiteado, lint, tests, modelos, providers, rutas, checklist de tareas, retro, TODOs, code review), publica la tabla como comentario timonel:dod en el issue de GitHub y devuelve la decision final (DONE | fallas criticas | pendientes no bloqueantes). Usa como ultimo paso antes de cerrar el issue.
---

Ejecuta la checklist de DoD con los resultados acumulados de fases anteriores mas los pocos comandos `git`/`gh` que falten; publica la tabla en el issue. Siempre en espanol.

## Parametros de entrada

| Parametro | Valores |
| --- | --- |
| `issue`, `repo` | Numero y `owner/repo` |
| `modulo`, `alcance` | Del issue |
| `lint_resultado` | `PASSED` \| `FAILED` |
| `tests_resultado` | `PASSED` \| `FAILED` \| `NO_SPECS` |
| `providers_registrados`, `rutas_registradas` | `si` \| `no` \| `n-a` |
| `tareas_completas` | `si` \| `no` (todas las tareas aplicables de `## Tareas` marcadas) |
| `retro_generada` | `si` \| `no` |
| `veredicto_code_review` | `APROBADO` \| `APROBADO CON OBSERVACIONES` \| `REQUIERE CAMBIOS` \| `NO_GENERADO` |

## Checklist

| # | Item | Criticidad | Verificacion |
| --- | --- | --- | --- |
| 1 | Codigo commiteado | CRITICO | `git status --porcelain` vacio → PASSED |
| 2 | Lint pasa | CRITICO | `lint_resultado` |
| 3 | Tests unitarios creados | NO critico | `git diff --name-only --diff-filter=A <rama-base>...HEAD -- '*.spec.ts' \| grep <modulo>` → PASSED si hay; SKIPPED si `NO_SPECS` |
| 4 | Tests pasan | CRITICO | `tests_resultado` (SKIPPED si `NO_SPECS`) |
| 5 | Modelos compartidos | NO critico | `git diff --name-only <rama-base>...HEAD -- <modelos.path>` → PASSED si hay; SKIPPED si el alcance no los implica |
| 6 | Providers registrados | CRITICO si aplica | `providers_registrados` (`n-a` → SKIPPED) |
| 7 | Rutas registradas | CRITICO si aplica | `rutas_registradas` (`n-a` → SKIPPED) |
| 8 | Checklist de tareas completo | CRITICO | `tareas_completas`; verifica en el body: `gh issue view <issue> -R <repo> --json body -q .body \| awk '/^## Tareas/{f=1} f'` — las tareas no aplicables al alcance (ej. Frontend en `alcance:backend`) cuentan como SKIPPED |
| 9 | Retrospectiva publicada | NO critico | `retro_generada` |
| 10 | Sin TODOs criticos en archivos nuevos | NO critico | `git diff --name-only --diff-filter=A <rama-base>...HEAD \| xargs grep -l 'TODO'` → lista si hay (no bloquea) |
| 11 | Code review aprobado | CRITICO condicional | `APROBADO`/`APROBADO CON OBSERVACIONES` → PASSED; `REQUIERE CAMBIOS` → FAILED CRITICO; `NO_GENERADO` → FAILED NO critico |

`<rama-base>` es la rama desde la que se creo `hu/N-slug` (normalmente `main` o `develop`; usa `git merge-base`).

## Decision final

- **DONE**: todos los CRITICO efectivos en PASSED o SKIPPED.
- **FALLAS_CRITICAS**: algun CRITICO efectivo FAILED (lista explicita).
- **PENDIENTES**: solo NO criticos FAILED (se reportan, no bloquean → equivale a DONE con pendientes).

## Publicar en el issue

Comentario `<!-- timonel:dod -->` con el formato de `PLUGIN_ROOT/skills/github-issues/references/marcadores.md` (YAML: fecha, decision; tabla de 11 filas; linea `Item 11 · veredicto: ...`; seccion Decisión final con fallas/pendientes). Valida con `python3 PLUGIN_ROOT/scripts/validar_marcador.py <archivo> --tipo dod` y luego `publicar_marcador <issue> dod <archivo>`.

Si la decision es `DONE` o `PENDIENTES`, marca `- [x] Definition of Done` en `## Tareas`. **No cierres el issue**: lo hace el orquestador.

## Reporte de salida

1. La tabla de 11 filas.
2. `Item 11 · veredicto: <valor>`.
3. `DECISION: DONE | FALLAS_CRITICAS | PENDIENTES` + lista.
4. `DOD_PUBLICADO: si | no`.
