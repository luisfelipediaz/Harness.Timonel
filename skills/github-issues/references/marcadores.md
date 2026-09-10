# Comentarios con marcador

Cada fase del ciclo publica **un** comentario en el issue de la HU cuya primera linea es el marcador. Los scripts de `retro-tools` (`scripts/timonel_gh.py`) localizan el comentario por ese prefijo y parsean el bloque ```yaml que sigue. Si la fase se repite, se **edita** el mismo comentario (receta `publicar_marcador` en `SKILL.md`).

Formato general:

````markdown
<!-- timonel:<tipo> -->
## <Titulo humano>

```yaml
clave: valor
```

<cuerpo markdown>
````

El YAML es **plano** (clave: valor, sin anidar, sin listas): se parsea con `partition(":")`.

---

## `timonel:investigacion` — dora-exploradora, Fase 1.5

Formato completo en `agents/dora-exploradora.md`. YAML: `fecha`, `modulo`, `alcance`, `reutiliza_investigacion_de`. Secciones `### Archivos de referencia`, `### Patrón a replicar`, `### Contrato existente relacionado`, `### Dependencias y puntos de registro`, `### Documentación externa`, `### Riesgos y consideraciones`. Una por issue; se edita si se repite.

---

## `timonel:contrato-api` — flechodiezx, Fase 2

````markdown
<!-- timonel:contrato-api -->
## Contrato API aprobado

```yaml
fecha: 2026-09-09
backend_desplegado: si | no
```

### Modelos compartidos (`libs/modelos/...`)

- `NombreEntidad { ... }`

### Endpoints

```
Metodo: POST
Ruta:   /api/<modulo>/<recurso>
Auth:   Bearer token + Portal-Auth-Type header
Permiso: TiposDePermisos.<PERMISO>
Request body: { ... }
Response:     { ... }
Errores esperados: 400, 403, 404, 409
```
````

---

## `timonel:consolidacion` — consolidate-story

````markdown
<!-- timonel:consolidacion -->
## Consolidación

```yaml
fecha: 2026-09-09
lint: PASSED | FAILED
tests: PASSED | FAILED | NO_SPECS
providers_registrados: si | no | n-a
rutas_registradas: si | no | n-a
```

### Archivos

- Backend: `apps/api/...`
- Frontend: `apps/client/...`
- Modelos: `libs/modelos/...`

### Correcciones aplicadas

- ...

### Pendientes y notas de migración

- ...
````

---

## `timonel:review` — code-review

Ademas del comentario, poner label exclusivo `review:aprobado | review:observaciones | review:requiere-cambios`.

````markdown
<!-- timonel:review -->
## Code review

```yaml
fecha: 2026-09-09
veredicto: APROBADO | APROBADO CON OBSERVACIONES | REQUIERE CAMBIOS
criticos: 0
warnings: 2
alcance: Backend | Frontend | Full-stack
modulo: mis-finanzas
bloquea_dod: si | no
```

### Resumen

1-2 lineas.

### Hallazgos

| #   | Tipo       | Severidad | Archivo:Línea                 | Descripción | Sugerencia |
| --- | ---------- | --------- | ----------------------------- | ----------- | ---------- |
| 1   | Gherkin    | CRITICO   | apps/client/.../x.ts:142      | ...         | ...        |

(Si no hay: `Sin hallazgos.`)

### Veredicto

**APROBADO CON OBSERVACIONES** — 0 CRITICO, 2 WARNING. [justificacion]

### Pasos sugeridos (solo si REQUIERE CAMBIOS)

- ...
````

Tipos validos: `Gherkin | Ficha | Convención | Heurística | Tests`. Severidades: `CRITICO | WARNING`. Reglas de severidad: CRITICO solo si un criterio Gherkin no se cumple o un test que lo cubre falla; todo lo demas WARNING.

---

## `timonel:retro` — generate-retro

Ademas del comentario, poner label exclusivo `retro:subestimado | retro:preciso | retro:sobreestimado`.

````markdown
<!-- timonel:retro -->
## Retrospectiva

```yaml
fecha: 2026-09-09
estimado_sp: 8
real_sp: 13
precision_estimacion: sobreestimado | preciso | subestimado
alcance: Frontend
modulo: mis-finanzas
```

### Desviaciones

- ...

### Errores recurrentes

- ...

### Patrones descubiertos

- ...

### Mejoras sugeridas

- ...
````

Maximo 3-5 bullets por seccion; `- Ninguno` si no aplica. Los scripts leen las secciones `### ` por nombre exacto. La retro incluye ademas `### Harness engineering` con las 4 preguntas (patron repetitivo, proceso manual 2+, contexto faltante, error prevenible).

---

## `timonel:dod` — verify-dod

````markdown
<!-- timonel:dod -->
## Definition of Done

```yaml
fecha: 2026-09-09
decision: DONE | FALLAS_CRITICAS | PENDIENTES
perfil: consumidor | plugin
```

| #   | Item                              | Estado  |
| --- | --------------------------------- | ------- |
| 1   | Código commiteado                 | PASSED  |
| 2   | Lint pasa                         | PASSED  |
| 3   | Tests unitarios creados           | PASSED  |
| 4   | Tests pasan                       | PASSED  |
| 5   | Modelos compartidos               | SKIPPED |
| 6   | Providers registrados             | PASSED  |
| 7   | Rutas registradas                 | SKIPPED |
| 8   | Checklist de tareas completo      | PASSED  |
| 9   | Retrospectiva publicada           | PASSED  |
| 10  | Sin TODOs críticos                | PASSED  |
| 11  | Code review aprobado              | PASSED  |

Item 11 · veredicto: APROBADO CON OBSERVACIONES

### Decisión final

**DONE** — [o lista de fallas criticas / pendientes no bloqueantes]
````

---

## `timonel:harness-audit` — harness-auditor (issue propio con label `harness-audit`)

Formato completo en `agents/harness-auditor.md`. YAML: `fecha`, `alcance`, `harness`, `semi`, `adhoc`, `score`, `auditoria_anterior`. Un issue por auditoria (historial), nunca se edita el anterior.

---

## `timonel:refinamiento` — backlog-refiner (en la epica)

````markdown
<!-- timonel:refinamiento -->
## Refinamiento — 2026-09-09

```yaml
fecha: 2026-09-09
modo: solo-reporte | aplicar
problemas_detectados: 4
cambios_aplicados: 2
```

### Resumen
### Propuestas
### Cambios aplicados
### Cambios NO aplicados
### Siguiente revisión sugerida
````

Si la epica recibe varios refinamientos, este marcador es la excepcion: se **agrega** un comentario nuevo por refinamiento (historial), nunca se edita el anterior.
