---
name: verify-dod
description: Valida la Definition of Done de una historia ejecutando una checklist de 11 items (PR abierto y mergeable, lint, tests, modelos, providers, rutas, checklist de tareas, retro, TODOs, code review), publica la tabla como comentario timonel:dod en el issue de GitHub y en el PR, y devuelve la decision final (DONE | fallas criticas | pendientes no bloqueantes). Usa como ultimo paso antes de cerrar el issue.
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
| `perfil` | `consumidor` (default) \| `plugin` |

**Perfil plugin**: items 5, 6 y 7 son `SKIPPED`; en el item 8 las tareas `Contrato API aprobado`, `Modelos compartidos` y `Frontend` cuentan como SKIPPED si no estan marcadas; item 3 usa `git diff --name-only --diff-filter=AM main...HEAD -- tests/`; `<rama-base>` es `main`. El item 11 **nunca** es SKIPPED: en el plugin tambien hay code review. El item 9 (retrospectiva) es **CRITICO** en este perfil: `retro_generada: no` → FAILED CRITICO (la retro no es opcional cuando el plugin se implementa a si mismo).

## Checklist

| # | Item | Criticidad | Verificacion |
| --- | --- | --- | --- |
| 1 | PR abierto y mergeable | CRITICO o NO critico segun motivo (D1-D7, #81) | `python3 PLUGIN_ROOT/scripts/pr_check.py <issue> --repo <repo> --base <rama-base>` — el sensor descubre el PR por la rama actual (nunca recibe una URL): PASSED si `ESTADO` empieza por PASSED; si no, FAILED con la `CRITICIDAD` y el `MOTIVO` que imprime (conflictos, check en rojo, draft, PR sin `Closes #N`, remote no soportado, etc.) |
| 2 | Lint pasa | CRITICO | `lint_resultado` |
| 3 | Tests unitarios creados | NO critico | `git diff --name-only --diff-filter=A <rama-base>...HEAD -- '*.spec.ts' \| grep <modulo>` → PASSED si hay; SKIPPED si `NO_SPECS` |
| 4 | Tests pasan | CRITICO | `tests_resultado` (SKIPPED si `NO_SPECS`) |
| 5 | Modelos compartidos | NO critico | `git diff --name-only <rama-base>...HEAD -- <modelos.path>` → PASSED si hay; SKIPPED si el alcance no los implica |
| 6 | Providers registrados | CRITICO si aplica | `providers_registrados` (`n-a` → SKIPPED) |
| 7 | Rutas registradas | CRITICO si aplica | `rutas_registradas` (`n-a` → SKIPPED) |
| 8 | Checklist de tareas completo | CRITICO | `tareas_completas`; verifica en el body: `gh issue view <issue> -R <repo> --json body -q .body \| awk '/^## Tareas/{f=1} f'` — las tareas no aplicables al alcance (ej. Frontend en `alcance:backend`) cuentan como SKIPPED; `PR abierto` debe estar **marcada** (el PR se abre en la Fase 6.5, antes del DoD, #80) — ya no cuenta como SKIPPED |
| 9 | Retrospectiva publicada | NO critico (CRITICO en perfil plugin) | `retro_generada`: `si` → PASSED; `no` → FAILED CRITICO en perfil plugin, FAILED NO critico en perfil consumidor |
| 10 | Sin TODOs criticos en archivos nuevos | NO critico | `git diff --name-only --diff-filter=A <rama-base>...HEAD \| xargs grep -l 'TODO'` → lista si hay (no bloquea) |
| 11 | Code review aprobado | CRITICO | `APROBADO`/`APROBADO CON OBSERVACIONES` → PASSED; `REQUIERE CAMBIOS`, `NO_GENERADO` o `SKIPPED` → FAILED CRITICO en `tipo:hu` y `tipo:hotfix` (sin autoevaluacion sin evaluador: nunca se degrada a NO critico) |

`<rama-base>` es la rama desde la que se creo `hu/N-slug` (normalmente `main` o `develop`; usa `git merge-base`).

## Decision final

- **DONE**: todos los CRITICO efectivos en PASSED o SKIPPED.
- **FALLAS_CRITICAS**: algun CRITICO efectivo FAILED (lista explicita).
- **PENDIENTES**: solo NO criticos FAILED (se reportan, no bloquean → equivale a DONE con pendientes).

## Publicar en el issue y en el PR

Comentario `<!-- timonel:dod -->` con el formato de `PLUGIN_ROOT/skills/github-issues/references/marcadores.md` (YAML: fecha, decision, `perfil: consumidor | plugin`; tabla de 11 filas; linea `Item 11 · veredicto: ...`; seccion Decisión final con fallas/pendientes). Valida con `python3 PLUGIN_ROOT/scripts/validar_marcador.py <archivo> --tipo dod` y luego `publicar_marcador <issue> dod <archivo>`.

Ademas, publica el **mismo cuerpo** como comentario en el PR que identifico `pr_check.py` (su `PR:` de salida): `gh pr comment <pr> -R <repo> --body-file <archivo>` (el mismo archivo ya validado). Si `pr_check.py` no identifico ningun PR (item 1 `FAILED`, `PR: n-a`), no hay donde publicar: reporta `DOD_PUBLICADO_EN_PR: n-a`.

Si la decision es `DONE` o `PENDIENTES`, marca `- [x] Definition of Done` en `## Tareas`. **No cierres el issue**: lo hace el orquestador.

## Reporte de salida

1. La tabla de 11 filas.
2. `Item 11 · veredicto: <valor>`.
3. `DECISION: DONE | FALLAS_CRITICAS | PENDIENTES` + lista.
4. `PR: <url o n-a>` y, si el item 1 fallo, `ITEM_1_MOTIVO: <motivo>`.
5. `DOD_PUBLICADO: si | no`.
6. `DOD_PUBLICADO_EN_PR: si | no | n-a`.
