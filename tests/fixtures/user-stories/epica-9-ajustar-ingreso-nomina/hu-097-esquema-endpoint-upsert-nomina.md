## HU-097: Persistir el ingreso de nomina como movimiento financiero con endpoint idempotente

**Como** empleado que usa el modulo mis-finanzas,
**quiero** que el "Ingreso de Nomina del periodo" se almacene en la base de datos de mis-finanzas y no se calcule al vuelo desde el store de liquidacion,
**para** que el movimiento sea la fuente unica de verdad, se entregue junto con el resto de movimientos al cargar la pagina y se pueda mantener actualizado cuando cambie la liquidacion correspondiente.

### Criterios de Aceptacion

```gherkin
DADO QUE el schema de MovimientoFinanciero hoy no distingue un ingreso de nomina de un ingreso manual
CUANDO se agrega el campo esNomina: boolean (default false) al schema y al modelo compartido
ENTONCES los movimientos nuevos pueden marcarse como ingreso de nomina y los existentes quedan con esNomina=false sin afectar queries actuales

DADO QUE puede existir a lo sumo un ingreso de nomina por empleado y periodo
CUANDO se crea el indice unico (contratoId, clienteId, mes, anio, esNomina=true) en la coleccion MovimientosFinancieros
ENTONCES un segundo insert con la misma llave es rechazado por el motor de Mongo y el upsert reutiliza el registro existente

DADO QUE el frontend necesita guardar o actualizar el ingreso de nomina resuelto por el algoritmo de sincronizacion (HU-098)
CUANDO llama POST /mis-finanzas/ingreso-nomina/upsert con monto, fecha, mes y anio
ENTONCES el backend hace upsert idempotente sobre la llave (contratoId, clienteId, mes, anio, esNomina=true) y retorna el movimiento resultante

DADO QUE el ingreso de nomina no debe ser editable ni eliminable por el usuario desde los endpoints CRUD normales
CUANDO se llama PUT /mis-finanzas/movimientos/:id o DELETE /mis-finanzas/movimientos/:id sobre un movimiento con esNomina=true
ENTONCES el backend responde 400 con mensaje explicito "Los movimientos de nomina no son editables ni eliminables" y no modifica el documento

DADO QUE la descripcion "Nomina del periodo" debe ser consistente en todas las creaciones
CUANDO el backend persiste el ingreso de nomina
ENTONCES fija descripcion = "Nomina del periodo", tipo = Ingreso, esNomina = true, confirmado = true, categoriaId = null (sin categoria) y fecha = la fecha enviada

DADO QUE el listado existente GET /mis-finanzas/movimientos ya incluye todos los movimientos del periodo
CUANDO el movimiento de nomina existe para ese mes/anio
ENTONCES se retorna junto con los demas movimientos sin requerir endpoints adicionales

DADO QUE los tests del servicio y aplicacion cubren el comportamiento actual
CUANDO se agregan los casos nuevos (upsert crea, upsert actualiza monto, bloqueo de PUT/DELETE sobre esNomina=true, listado incluye nomina)
ENTONCES todos los tests existentes siguen en verde y los nuevos pasan
```

### INVEST

| Criterio      | Estado | Nota                                                                              |
| ------------- | ------ | --------------------------------------------------------------------------------- |
| Independiente | ✅     | Solo backend; la HU-098 depende de esta pero esta no depende de nadie             |
| Negociable    | ✅     | Nombre de endpoint y mensajes de error pueden ajustarse                           |
| Valiosa       | ✅     | Habilita persistencia unificada del ingreso de nomina                             |
| Estimable     | ✅     | Capas bien definidas (schema, servicio, aplicacion, controller)                   |
| Small         | ✅     | Cabe en un sprint; cambio acotado a mis-finanzas                                  |
| Testeable     | ✅     | Casos de upsert, idempotencia y bloqueo de edicion son verificables en unit tests |

### Ficha Tecnica

| Campo             | Valor                            |
| ----------------- | -------------------------------- |
| Alcance           | Backend                          |
| Entidad principal | MovimientoFinanciero             |
| Tipo de operacion | CRUD (upsert idempotente)        |
| Permiso requerido | portalMisFinanzas (ya existente) |
| Modulo destino    | mis-finanzas                     |

### Endpoints sugeridos

- `POST /api/mis-finanzas/ingreso-nomina/upsert` — crea o actualiza el ingreso de nomina del periodo (idempotente por `(contratoId, clienteId, mes, anio)`)
  - Request: `UpsertIngresoNominaRequest { monto: number; fecha: string; mes: number; anio: number }`
  - Response: `MovimientoFinanciero` (el movimiento persistido, con `esNomina: true`)
  - Errores: 400 (validacion: `mes` fuera de 1-12, `monto` negativo, `fecha` invalida), 401 (sin auth)

### Modelos compartidos

Actualizaciones a `libs/modelos/src/lib/mis-finanzas/mis-finanzas.model.ts`:

- `MovimientoFinanciero` — agregar campo `esNomina: boolean`
- `MovimientoPersistencia` — agregar campo `esNomina: boolean`
- Nuevo: `UpsertIngresoNominaRequest { monto: number; fecha: string; mes: number; anio: number }`

Nota: **NO se agrega `esProvisional`**. El algoritmo del frontend (HU-098) resuelve el estado por comparacion de monto en cada carga, haciendo innecesario guardar ese flag.

### Notas Tecnicas

- Archivos a modificar:
  - `libs/modelos/src/lib/mis-finanzas/mis-finanzas.model.ts` — agregar `esNomina` y `UpsertIngresoNominaRequest`
  - `apps/api/src/app/mis-finanzas/esquemas/movimiento-financiero.esquema.ts` — agregar campo + indice unico parcial `(contratoId, clienteId, mes, anio, esNomina)` filtrando `esNomina: true`
  - `apps/api/src/app/mis-finanzas/servicios/movimientos-finanzas.servicio.ts` — metodo `upsertIngresoNomina(datos, sesion)`
  - `apps/api/src/app/mis-finanzas/aplicaciones/movimientos-finanzas.aplicacion.ts` — metodo publico `upsertIngresoNomina`, guardas en `actualizarMovimiento` y `eliminarMovimiento` para rechazar `esNomina=true`
  - `apps/api/src/app/mis-finanzas/controllers/movimientos-finanzas.controller.ts` — handler `POST /ingreso-nomina/upsert` con `@AuditoriaApi`
  - Specs correspondientes en cada capa
- Consideraciones adicionales:
  - El indice unico debe ser **parcial** (`partialFilterExpression: { esNomina: true }`) para no afectar los ingresos/gastos manuales.
  - El upsert debe usar `findOneAndUpdate` con `upsert: true` y filtrar por `(contratoId, clienteId, mes, anio, esNomina: true)` para garantizar unicidad.
  - No crear categoria "Nomina" nueva: el movimiento se guarda con `categoriaId: null`. El usuario descarto cambios de UI y las pipes de categoria ya manejan el caso nulo (HU-094).
  - `confirmado: true` porque el ingreso ya fue pagado/devengado (no requiere confirmacion manual del usuario).
  - Reusar `validarPeriodoMensual(mes)` existente en las validaciones de entrada.
  - El metodo `listarMovimientosPorPeriodo` del servicio no requiere cambios: al no filtrar por `esNomina`, el ingreso de nomina se retorna automaticamente junto con los demas.

**MoSCoW:** Should Have
**Story Points:** 5 — CRUD simple con idempotencia + 2 guardas de negocio + cambios en 3 capas. Sin logica de negocio compleja.
**Prioridad:** Alta
**Dependencias:** Ninguna (es fundacional para HU-098 y HU-099)
