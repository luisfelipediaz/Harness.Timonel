# Plantilla — issue `tipo:hu`

**Titulo**: `[verbo infinitivo] [que cosa]` (max 70 caracteres). Ej: `Persistir el ingreso de nomina con endpoint idempotente`.

**Labels obligatorios**: `tipo:hu`, `estado:borrador|listo`, `alcance:backend|frontend|full-stack`, `moscow:*`, `sp:*`, `prioridad:*`, `mod:<modulo>`.

**Padre**: sub-issue de su epica (`tipo:epica`).

## Body

````markdown
## Historia

**Como** [rol],
**quiero** [funcionalidad],
**para** [valor/beneficio].

## Criterios de aceptación

```gherkin
DADO QUE [contexto]
CUANDO [accion]
ENTONCES [resultado]
```

## INVEST

| Criterio      | Estado | Nota |
| ------------- | ------ | ---- |
| Independiente | ✅/⚠️  |      |
| Negociable    | ✅/⚠️  |      |
| Valiosa       | ✅/⚠️  |      |
| Estimable     | ✅/⚠️  |      |
| Small         | ✅/⚠️  |      |
| Testeable     | ✅/⚠️  |      |

## Ficha técnica

| Campo             | Valor                                                                          |
| ----------------- | ------------------------------------------------------------------------------ |
| Alcance           | Backend / Frontend / Full-stack                                                |
| App destino       | (solo si `frontends[]` del config tiene mas de una; nombre del `project`)      |
| Entidad principal | nombre de la entidad de dominio                                                |
| Tipo de operación | CRUD / Workflow (solicitud con aprobacion) / Consulta / Integracion / Refactor |
| Permiso requerido | nombre existente en TiposDePermisos, o 'NUEVO: nombreSugerido'                 |
| Módulo destino    | nombre del modulo existente o 'NUEVO: nombreSugerido'                          |

## Endpoints

- `METHOD /api/modulo/recurso` — descripcion breve
  - Request: `NombreRequest { campo: tipo }`
  - Response: `NombreResponse { campo: tipo }`
  - Errores: 400 (validacion), 404 (no encontrado)

(o `Ninguno`)

## Modelos compartidos

- `NombreEntidad { campo: string; campo2: number; campoOpcional?: boolean }`

(o `Ninguno`. Sin prefijo `I` en interfaces.)

## Notas técnicas

- Archivos a modificar: ...
- Consideraciones: ...

## Dependencias

Depende de #N
(o `Ninguna`)

## Tareas

- [ ] Contrato API aprobado
- [ ] Modelos compartidos
- [ ] Backend
- [ ] Frontend
- [ ] Consolidación (lint + tests)
- [ ] Code review
- [ ] Retrospectiva
- [ ] Definition of Done
- [ ] PR abierto
````

## Reglas

- La **Ficha técnica** siempre en tabla; los skills de implementacion la parsean.
- `Alcance` solo acepta `Backend`, `Frontend`, `Full-stack`. Si la historia es solo modelos compartidos, usar `Full-stack` con nota.
- El checklist es el mismo para HUs del propio plugin (`mod:plugin`): `Backend` = implementacion, `Frontend`/`Modelos compartidos` quedan SKIPPED.
- Las tareas que no apliquen al alcance se dejan sin marcar y el DoD las reporta como `SKIPPED` (ej: `Frontend` en una HU `alcance:backend`). No borrar lineas del checklist.
- `PR abierto` se marca en la Fase 8, **despues** del DoD: el item 8 de `verify-dod` la cuenta siempre como SKIPPED. Con `git.integracion: merge` (default en el plugin) queda sin marcar y `estado_historia` la trata como SKIPPED; con `pr` la marca flechodiezx al abrir el PR.
- `POR DEFINIR` en cualquier celda impide pasar a `estado:listo`.
- Calibracion de Story Points: 1 = config/texto/fix puntual; 2 = CRUD simple de una capa; 3 = feature small full-stack; 5 = feature medium con logica y store; 8 = feature compleja multi-capa (workflow + notificaciones); 13 = integracion externa + UI compleja; 21 = dividir.
