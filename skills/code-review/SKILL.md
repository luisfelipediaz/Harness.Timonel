---
name: code-review
description: Revisa el codigo implementado contra los criterios de aceptacion del issue de GitHub, clasifica hallazgos por severidad (CRITICO | WARNING) y publica el review como comentario timonel:review en el issue con su label review:*. Usa como Fase 5.5 del story-executor (y Fase 3 del hotfix-executor), tras consolidate-story y antes de generate-retro. El veredicto bloquea el DoD cuando hay hallazgos criticos.
---

Revisa la implementacion de una historia contra su issue y las convenciones del proyecto, clasifica cada hallazgo por severidad y publica el review en el issue. Siempre en espanol.

## Parametros de entrada

| Parametro | Descripcion |
| --- | --- |
| `issue` | Numero del issue |
| `repo` | `owner/repo` |
| `modulo` | Modulo destino |
| `alcance` | `Backend` \| `Frontend` \| `Full-stack` |
| `archivos_modificados` | Lista consolidada (ARCHIVOS_BACKEND + ARCHIVOS_FRONTEND + MODELOS_COMPARTIDOS) |
| `plugin_root` | Raiz absoluta del plugin (para heuristicas y plantillas) |

Si falta alguno, detente y reporta.

## Paso 1: Cargar contexto

En paralelo:

- **Issue**: `gh issue view <issue> -R <repo> --json title,body,labels,comments`. Extrae Gherkin, Ficha tecnica, Tipo de operacion.
- **Retro previa** del modulo: `python3 <plugin_root>/scripts/retro_query.py --modulo <modulo> --seccion "Errores recurrentes"`.
- **CLAUDE.md** del consumidor.
- **Heuristicas**: `HEUR=$(jq -r '.heuristicsDir // empty' .claude/timonel.config.json); HEUR="${HEUR:-<plugin_root>/heuristics}"` → lee `general/evitar-ifs.md`, `general/no-tipos-espejo.md`, `angular/usar-pipes-existentes.md` (las que existan).
- **Formato**: `<plugin_root>/skills/github-issues/references/marcadores.md`, seccion `timonel:review`.

Si el issue no declara Gherkin verificable, registra WARNING tipo `Gherkin` "issue no declara criterios Gherkin verificables" y continua.

## Paso 2: Localizar el codigo

`archivos_modificados` es la lista autorizada. Complementa con `git diff <rama-base>...HEAD --name-only` si hace falta. No audites el resto del repo.

## Paso 3: Revision con severidad

- **CRITICO**: un criterio Gherkin no se cumple en el codigo, o un test que lo cubre directamente falla, o falta el unico test que lo verificaria.
- **WARNING**: todo lo demas.

### 3.1 Gherkin (`Gherkin`)
Por cada escenario, busca la logica concreta que lo implementa. No cumplido → CRITICO.

### 3.2 Ficha tecnica (`Ficha`)
Endpoints (rutas/metodos coinciden; controllers con decoradores), Permisos (`AuthorizationGuard<TiposDePermisos>` correcto), Auditoria (`@AuditoriaApi`), Modelos (compartidos desde `modelos.alias`, no redeclarados), Sesion propagada controller → aplicacion → servicio. WARNING salvo que rompa un Gherkin.

### 3.3 Convenciones (`Convención`)
No `any`; no `!` postfix; kebab-case; control flow nuevo (`@if/@for/@switch`); no negar async pipes; standalone; controllers solo delegan; imports limpios; printWidth 80; sin prefijo `I`. Todo WARNING. Agrega las reglas propias del `CLAUDE.md` del consumidor.

### 3.4 Heuristicas (`Heurística`)
`evitar-ifs`, `no-tipos-espejo`, `usar-pipes-existentes`. Omite las que no esten en disco. WARNING.

### 3.5 Tests (`Tests`)
`.spec.ts` para codigo nuevo; cubren los Gherkin; usa `TESTS_RESULTADO` de consolidacion (no re-ejecutes salvo duda). Faltantes no directos de Gherkin → WARNING; directos → CRITICO con tipo `Gherkin`.

### 3.6 Retro previa
Si un error recurrente documentado se repite, registralo (WARNING salvo que viole un Gherkin).

## Paso 4: Veredicto

`APROBADO` (0/0) · `APROBADO CON OBSERVACIONES` (0 criticos, ≥1 warning) · `REQUIERE CAMBIOS` (≥1 critico). `BLOQUEA_DOD = si` solo con `REQUIERE CAMBIOS`.

## Paso 5: Publicar en el issue

1. Escribe el comentario con el formato exacto `timonel:review` de `marcadores.md` (YAML plano + Resumen + tabla Hallazgos + Veredicto + Pasos sugeridos si aplica) en un archivo temporal.
2. `publicar_marcador <issue> review <archivo>` (receta del skill `github-issues`: edita si ya existe).
3. Label exclusivo: `cambiar_label_exclusivo <issue> review <aprobado|observaciones|requiere-cambios>`.
4. Marca `- [x] Code review` en `## Tareas`.
5. **No hagas commit** de nada.

## Reporte de salida (obligatorio)

```
VEREDICTO: APROBADO | APROBADO CON OBSERVACIONES | REQUIERE CAMBIOS
HALLAZGOS_CRITICOS: <n>
HALLAZGOS_WARNING: <n>
REVIEW_PUBLICADO: si | no
BLOQUEA_DOD: si | no
RESUMEN: <1-2 lineas>
```

## Manejo de errores

- Issue no legible → `VEREDICTO: NO_GENERADO` + `MOTIVO`. No inventes la spec.
- Fallo al publicar → devuelve igual el bloque con conteos y el cuerpo del review en tu respuesta, `REVIEW_PUBLICADO: no`.
- Review previo existente → se sobreescribe (el codigo cambio).
