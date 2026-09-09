## HU-098: Algoritmo de sincronizacion del ingreso de nomina desde liquidacion

**Como** empleado que abre el modulo mis-finanzas,
**quiero** que el frontend detecte automaticamente si el ingreso de nomina del periodo ya esta persistido y, cuando no lo este o este desactualizado, lo resuelva desde el store de liquidacion aplicando la regla del dominio,
**para** que el movimiento "Nomina del periodo" aparezca siempre en la lista sin intervencion manual y se sincronice con los cambios de la liquidacion correspondiente.

### Criterios de Aceptacion

```gherkin
DADO QUE el usuario entra a mis-finanzas y se dispara cargarDatos
CUANDO el backend responde con los movimientos del periodo
Y entre ellos viene un movimiento con esNomina=true
ENTONCES se compara su monto con el neto a pagar de la liquidacion que cumple la regla de mapping
Y se ejecuta upsert SOLO SI el monto difiere del persistido
Y no se ejecuta ningun POST adicional si los montos coinciden

DADO QUE el usuario entra a mis-finanzas y se dispara cargarDatos
CUANDO el backend responde con los movimientos del periodo
Y NO viene un movimiento con esNomina=true
ENTONCES el frontend busca la liquidacion aplicable en el store de liquidacion
Y si la liquidacion mostrada cumple la regla de mapping
ENTONCES dispara POST /mis-finanzas/ingreso-nomina/upsert con el neto a pagar, la fechaFinal y el mes/anio de mis-finanzas

DADO QUE la liquidacion mostrada en el store NO cumple la regla de mapping
CUANDO el algoritmo detecta que el mes de mis-finanzas corresponde a una liquidacion posterior a la mostrada
ENTONCES dispara obtenerLiquidacionEmpleadoPeriodoSiguiente hasta que se cumpla la regla
Y al cumplirse, dispara el upsert

DADO QUE la liquidacion mostrada en el store NO cumple la regla de mapping
CUANDO el algoritmo detecta que el mes de mis-finanzas corresponde a una liquidacion anterior a la mostrada
ENTONCES dispara obtenerLiquidacionEmpleadoPeriodoAnterior hasta que se cumpla la regla
Y al cumplirse, dispara el upsert

DADO QUE el algoritmo necesita avanzar hacia adelante pero tienePeriodoSiguiente=false en el store de liquidacion
CUANDO no hay liquidacion posterior disponible
ENTONCES toma la ultima liquidacion conocida (la actualmente mostrada) y dispara el upsert con su neto a pagar y fechaFinal
Y el mes/anio enviados al endpoint son los del mes actual de mis-finanzas (no los derivados de la liquidacion)

DADO QUE el algoritmo necesita retroceder pero tienePeriodoAnterior=false en el store de liquidacion
CUANDO no hay liquidacion previa disponible
ENTONCES toma la primera liquidacion conocida (la actualmente mostrada) y dispara el upsert con su neto a pagar y fechaFinal
Y el mes/anio enviados al endpoint son los del mes actual de mis-finanzas

DADO QUE la regla de mapping debe soportar cruce de año
CUANDO la liquidacion tiene fechaFinal = 31-dic-2025
ENTONCES se mapea a mis-finanzas mes=1 anio=2026 (y viceversa: mis-finanzas enero 2026 busca liquidacion de diciembre 2025)

DADO QUE el upsert exitoso retorna el movimiento persistido
CUANDO el POST responde 200 con el MovimientoFinanciero
ENTONCES se hace patch del store de mis-finanzas agregando o actualizando el movimiento en la lista sin necesidad de recargar

DADO QUE la navegacion del algoritmo en el store de liquidacion tiene side-effect
CUANDO termina la sincronizacion
ENTONCES el navegador de liquidacion queda posicionado en el periodo que resolvio la regla (o en el limite si hubo caso borde), y esto es comportamiento aceptado (opcion A decidida en descubrimiento)

DADO QUE el algoritmo no debe correr en bucle infinito
CUANDO detecta una condicion imposible (por ejemplo, el store de liquidacion retorna error o el dispatch no avanza)
ENTONCES aborta silenciosamente sin crear movimiento y loguea una traza unica para diagnostico (sin bloquear la carga del modulo)
```

### INVEST

| Criterio      | Estado | Nota                                                                                     |
| ------------- | ------ | ---------------------------------------------------------------------------------------- |
| Independiente | ⚠️     | Depende de HU-097 (endpoint) y se coordina con HU-099 (eliminacion del computed virtual) |
| Negociable    | ✅     | La ubicacion del algoritmo (effect vs store-method vs facade) puede decidirse en diseño  |
| Valiosa       | ✅     | Es el corazon de la epica: garantiza que el dato siempre este persistido y actualizado   |
| Estimable     | ✅     | Hay ambiguedad controlada en donde vive el algoritmo (effect) pero la logica es clara    |
| Small         | ✅     | Cabe en un sprint aunque requiere tests cuidadosos de casos borde                        |
| Testeable     | ✅     | Cada rama del arbol de decision es un caso de test                                       |

### Ficha Tecnica

| Campo             | Valor                                    |
| ----------------- | ---------------------------------------- |
| Alcance           | Frontend                                 |
| Entidad principal | MovimientoFinanciero (ingreso de nomina) |
| Tipo de operacion | Workflow (sincronizacion post-carga)     |
| Permiso requerido | portalMisFinanzas (ya existente)         |
| Modulo destino    | mis-finanzas                             |

### Endpoints sugeridos

Ninguno nuevo. Consume `POST /api/mis-finanzas/ingreso-nomina/upsert` creado en HU-097.

### Modelos compartidos

Ninguno nuevo. Usa `UpsertIngresoNominaRequest` y `MovimientoFinanciero` definidos en HU-097.

### Notas Tecnicas

- Archivos a modificar / crear:
  - `apps/client/src/app/mis-finanzas/mis-finanzas.service.ts` — metodo `upsertIngresoNomina(request: UpsertIngresoNominaRequest)` que llama el endpoint
  - `apps/client/src/app/mis-finanzas/state/effects.ts` (o archivo de effect dedicado tipo `sincronizar-ingreso-nomina.effect.ts`) — effect que escucha la finalizacion de `cargarMovimientos` y ejecuta el algoritmo
  - `apps/client/src/app/mis-finanzas/state/index.ts` — agregar action `sincronizarIngresoNomina` y un reducer minimal que haga patch del movimiento retornado
  - `apps/client/src/app/mis-finanzas/state/actions.ts` — nueva action
  - Utilidad nueva: `apps/client/src/app/mis-finanzas/utilidades/mapear-periodo-liquidacion.ts` — funcion pura `calcularMesMisFinanzasDesdeLiquidacion(fechaFinal: Date): { mes: number; anio: number }` que suma 1 mes a fechaFinal y retorna mes/anio, manejando cruce de año
  - Spec para la utilidad cubriendo: abril→mayo, dic-2025→ene-2026, febrero→marzo, etc.

- Regla de mapping formal (mis-finanzas.mes ↔ liquidacion.fechaFinal):

  ```
  mis-finanzas { mes, anio } === liquidacion.fechaFinal + 1 mes
  ```

  Implementacion: construir `new Date(fechaFinal); d.setMonth(d.getMonth() + 1); return { mes: d.getMonth()+1, anio: d.getFullYear() };` — el `setMonth` maneja el wrap a enero del año siguiente automaticamente.

- Algoritmo (pseudocodigo):

  ```
  tras cargarDatos exitoso:
    const periodoMF = { mes: store.mes(), anio: store.anio() };
    const nominaPersistida = movimientos().find(m => m.esNomina);
    const liquidacion = rootStore.selectSnapshot(getLiquidacion);

    if (!liquidacion) return; // sin liquidacion, nada que sincronizar

    const periodoLiquidacion = calcularMesMisFinanzasDesdeLiquidacion(liquidacion.fechaFinal);
    const cumpleRegla = periodoLiquidacion.mes === periodoMF.mes && periodoLiquidacion.anio === periodoMF.anio;

    if (cumpleRegla) {
      const monto = netoAPagar.valor;
      if (!nominaPersistida || nominaPersistida.monto !== monto) {
        upsert({ monto, fecha: liquidacion.fechaFinal, mes: periodoMF.mes, anio: periodoMF.anio });
      }
      return;
    }

    // no cumple regla: navegar
    const deltaMeses = calcularDelta(periodoLiquidacion, periodoMF); // positivo = avanzar, negativo = retroceder
    if (deltaMeses > 0) {
      if (tienePeriodoSiguiente()) {
        dispatch(obtenerLiquidacionEmpleadoPeriodoSiguiente());
        // esperar nuevo estado y re-ejecutar algoritmo
      } else {
        // caso borde adelante: usar la actualmente mostrada
        upsert({ monto: netoAPagar.valor, fecha: liquidacion.fechaFinal, mes: periodoMF.mes, anio: periodoMF.anio });
      }
    } else {
      if (tienePeriodoAnterior()) {
        dispatch(obtenerLiquidacionEmpleadoPeriodoAnterior());
        // esperar nuevo estado y re-ejecutar algoritmo
      } else {
        // caso borde atras: usar la actualmente mostrada
        upsert({ monto: netoAPagar.valor, fecha: liquidacion.fechaFinal, mes: periodoMF.mes, anio: periodoMF.anio });
      }
    }
  ```

- Consideraciones adicionales:
  - El re-dispatch del algoritmo tras la navegacion puede resolverse enlazando el effect a la misma action que recarga la liquidacion, o con un pequeño state machine (`sincronizandoNomina: 'idle' | 'buscando' | 'completado'`). El implementador puede elegir, siempre que quede testeable.
  - **Sin limite de iteraciones defensivo** (decidido en descubrimiento): el caso donde el delta es enorme no ocurre en la practica porque el store de liquidacion se inicializa cerca del mes actual.
  - **Sin flag esProvisional**: el estado se infiere por comparacion de monto. Si en una carga subsiguiente aparece la liquidacion "real" del mes y el monto coincide con el ya guardado (aproximacion), no se hace nada. Si difiere, se sobreescribe.
  - Side-effect en la navegacion del store de liquidacion: aceptado (opcion A). El navegador queda posicionado donde resolvio el algoritmo.
  - El effect debe correr **una sola vez** por cada `cargarDatos` completado, no en cada tick del store. Usar `first()` o una action explicita `cargarDatosCompletado`.
  - Si el response del upsert agrega un nuevo movimiento al store, el selector existente `ingresos` lo incluira automaticamente tras eliminar el computed virtual en HU-099.

**MoSCoW:** Should Have
**Story Points:** 8 — logica multi-paso con navegacion iterativa, dos casos borde simetricos, cruce de año y sincronizacion asincrona con el store de portal. Tests no triviales.
**Prioridad:** Alta
**Dependencias:** HU-097 (endpoint de upsert)
