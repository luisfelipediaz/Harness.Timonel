# Epica 1: Infraestructura del Modulo Mis Finanzas — Historias Completadas

---

## HU-001: Estructura base del modulo Angular + API

**Como** empleado,
**quiero** acceder a un nuevo modulo "Mis Finanzas" desde el menu de navegacion,
**para** tener un espacio dedicado donde gestionar mis finanzas personales.

### Criterios de Aceptacion

```gherkin
DADO QUE el empleado esta autenticado y tiene permisos para el modulo Mis Finanzas
CUANDO navega al menu principal
ENTONCES ve la opcion "Mis Finanzas" en el menu de navegacion

DADO QUE el empleado hace clic en "Mis Finanzas"
CUANDO se carga el modulo
ENTONCES se muestra la vista principal del modulo sin errores
  Y la URL cambia a /MisFinanzas

DADO QUE el empleado no tiene permisos para el modulo Mis Finanzas
CUANDO intenta acceder a /MisFinanzas directamente
ENTONCES es redirigido segun el comportamiento del LicenciaGuard existente

DADO QUE el modulo se carga por primera vez
CUANDO Angular resuelve la ruta
ENTONCES el modulo se carga via lazy-loading (loadChildren)
```

### Alcance Tecnico

**Client (Angular 20):**

- Nuevo modulo `mis-finanzas/` en `apps/client/src/app/` con routing lazy-loaded
- Usar **standalone routes** con `mis-finanzas.routes.ts` (mismo patron que `prestamos.routes.ts`, `beneficios.routes.ts`, `incapacidades.routes.ts`)
- `MisFinanzasFacade` como capa de abstraccion del store
- NgRx state: `MisFinanzasState` con actions, reducer, effects, selectors
- Registro en `app-routing.module.ts` con `loadChildren: () => import('./mis-finanzas/mis-finanzas.routes')`
- Guards: `AuthGuard`, `ContratoGuard`, `LicenciaGuard` con `data: { permisos: [permisosAplicacion.portalMisFinanzas] }`

**API (NestJS 10):**

- Nuevo modulo `mis-finanzas/` en `apps/api/src/app/` con estructura:
  - `controllers/mis-finanzas.controller.ts`
  - `aplicaciones/mis-finanzas.aplicacion.ts`
  - `servicios/mis-finanzas.servicio.ts`
  - `esquemas/` (se define en HU-002)
- Registro en `AppModule`
- Guard `AuthorizationGuard` aplicado

### INVEST

| Criterio      | Estado | Nota                                 |
| ------------- | ------ | ------------------------------------ |
| Independiente | ✅     | No depende de otras HU               |
| Negociable    | ✅     | Detalles de implementacion flexibles |
| Valiosa       | ✅     | Habilita todo el modulo              |
| Estimable     | ✅     | Patron bien conocido en el repo      |
| Small         | ✅     | Cabe en un sprint                    |
| Testeable     | ✅     | Verificable con navegacion y carga   |

### Ficha Tecnica

| Campo               | Valor                                                           |
| ------------------- | --------------------------------------------------------------- |
| Alcance             | Full-stack                                                      |
| Entidad principal   | MisFinanzas (modulo)                                            |
| Tipo de operacion   | Infraestructura                                                 |
| Endpoints sugeridos | GET /api/mis-finanzas/health — verificar que el modulo responde |
| Modelos compartidos | Ninguno en esta historia (se definen en HU-002)                 |
| Permiso requerido   | NUEVO: portalMisFinanzas                                        |
| Modulo destino      | NUEVO: mis-finanzas                                             |

**MoSCoW:** Must Have
**Story Points:** 8 — Involucra client + API + store + routing + permisos, pero es patron repetido
**Prioridad:** Alta
**Dependencias:** Ninguna (es la base de todo)

---

## HU-002: Esquema MongoDB para movimientos financieros

**Como** sistema,
**quiero** tener un esquema de base de datos que soporte movimientos financieros (ingresos, gastos, recurrentes, deudas),
**para** persistir toda la informacion financiera del empleado de forma estructurada.

### Criterios de Aceptacion

```gherkin
DADO QUE el sistema necesita almacenar un movimiento financiero
CUANDO se crea un nuevo registro
ENTONCES se persiste con: tipo (ingreso/gasto), monto, categoria, fecha, descripcion, esRecurrente, esFijo, contratoId, clienteId

DADO QUE se crea un ingreso de tipo salarial
CUANDO se persiste en la base de datos
ENTONCES el campo origenSalarial es true
  Y se vincula al periodo de nomina correspondiente

DADO QUE se crea un gasto asociado a tarjeta de credito
CUANDO se persiste en la base de datos
ENTONCES se vincula a la tarjeta de credito correspondiente (tarjetaCreditoId)

DADO QUE se consultan movimientos de un empleado
CUANDO otro empleado intenta acceder a esos datos
ENTONCES el sistema rechaza la consulta (filtro por contrato + cliente)

DADO QUE se crea una categoria personalizada
CUANDO se persiste
ENTONCES se almacena con: nombre, icono, color, contratoId, clienteId, esPredeterminada
```

### Esquemas Propuestos

**Coleccion `MovimientosFinancieros`:**

- `tipo`: enum ['ingreso', 'gasto']
- `monto`: Number (required)
- `descripcion`: String
- `categoria`: ObjectId (ref CategoriaFinanciera)
- `fecha`: Date (required)
- `esRecurrente`: Boolean (default false)
- `esFijo`: Boolean (default false)
- `diaRecurrencia`: Number (1-31, para recurrentes)
- `origenSalarial`: Boolean (default false)
- `periodoNominaId`: Number (opcional, para ingresos salariales)
- `tarjetaCreditoId`: ObjectId (opcional, ref TarjetaCredito)
- `contratoId`: Number (required, multi-tenancy)
- `clienteId`: String (required, multi-tenancy)

**Coleccion `CategoriasFinancieras`:**

- `nombre`: String (required)
- `icono`: String
- `color`: String
- `esPredeterminada`: Boolean (default false)
- `tipo`: enum ['ingreso', 'gasto', 'ambos']
- `contratoId`: Number (nullable para predeterminadas globales)
- `clienteId`: String (nullable para predeterminadas globales)

**Coleccion `TarjetasCredito`:**

- `nombre`: String (required, ej: "Visa Bancolombia")
- `ultimosDigitos`: String (4 digitos)
- `fechaCorte`: Number (dia del mes)
- `cupoTotal`: Number
- `saldoActual`: Number
- `cuotaMinima`: Number
- `contratoId`: Number (required)
- `clienteId`: String (required)

**Coleccion `PresupuestosMensuales`:**

- `mes`: Number (1-12)
- `anio`: Number
- `categoria`: ObjectId (ref CategoriaFinanciera)
- `montoPresupuestado`: Number
- `contratoId`: Number (required)
- `clienteId`: String (required)

### INVEST

| Criterio      | Estado | Nota                                          |
| ------------- | ------ | --------------------------------------------- |
| Independiente | ⚠️     | Se implementa junto con HU-001 en la practica |
| Negociable    | ✅     | Estructura de esquemas puede ajustarse        |
| Valiosa       | ✅     | Sin persistencia no hay modulo                |
| Estimable     | ✅     | Esquemas Mongoose bien conocidos              |
| Small         | ✅     | Solo esquemas + servicio base                 |
| Testeable     | ✅     | Tests de integracion con MongoDB              |

### Ficha Tecnica

| Campo               | Valor                                                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Alcance             | Backend                                                                                                                     |
| Entidad principal   | MovimientoFinanciero, CategoriaFinanciera, TarjetaCredito, PresupuestoMensual                                               |
| Tipo de operacion   | CRUD                                                                                                                        |
| Endpoints sugeridos | Ninguno directo (esquemas consumidos por otros endpoints)                                                                   |
| Modelos compartidos | IMovimientoFinanciero, ICategoriaFinanciera, ITarjetaCredito, IPresupuestoMensual — en `libs/modelos/src/lib/mis-finanzas/` |
| Permiso requerido   | NUEVO: portalMisFinanzas                                                                                                    |
| Modulo destino      | NUEVO: mis-finanzas                                                                                                         |

**MoSCoW:** Must Have
**Story Points:** 5 — Esquemas Mongoose con patron conocido, sin logica compleja
**Prioridad:** Alta
**Dependencias:** HU-001 (modulo API debe existir)

---

## HU-003: Dashboard principal con balance mensual

**Como** empleado,
**quiero** ver un resumen de mi situacion financiera del mes actual al entrar a Mis Finanzas,
**para** saber rapidamente cuanto he ganado, cuanto he gastado y cuanto me queda disponible.

### Criterios de Aceptacion

```gherkin
DADO QUE el empleado accede al modulo Mis Finanzas
CUANDO se carga el dashboard principal
ENTONCES ve un resumen con:
  - Total de ingresos del mes
  - Total de gastos del mes
  - Balance disponible (ingresos - gastos)
  Y los montos se muestran en formato de moneda colombiana (COP)

DADO QUE el empleado tiene ingresos salariales y manuales
CUANDO ve el total de ingresos
ENTONCES el monto incluye tanto el salario como los ingresos adicionales registrados

DADO QUE el empleado no tiene movimientos en el mes actual
CUANDO ve el dashboard
ENTONCES los totales muestran $0
  Y se muestra un mensaje invitando a registrar su primer movimiento

DADO QUE el empleado tiene gastos que superan sus ingresos
CUANDO ve el balance disponible
ENTONCES el balance se muestra en rojo/negativo

DADO QUE el dashboard se carga
CUANDO el empleado ve la interfaz
ENTONCES el look and feel es consistente con el modulo de volantes de pago (cards Material, iconos, tipografia)
  Y se muestra el mes actual con opcion de navegar a meses anteriores
```

### Diseno de Interfaz

Reutilizar el patron visual de `liquidacion-shell`:

- **Header** con titulo "Mis Finanzas" e imagen ilustrativa
- **Card de resumen** superior: Ingresos | Gastos | Balance (3 columnas o cards)
- **Navegacion de periodo** similar a `app-liquidacion-periodo` (mes anterior / mes siguiente)
- **Secciones** debajo del resumen: accesos rapidos a ingresos, gastos, presupuesto

### INVEST

| Criterio      | Estado | Nota                                         |
| ------------- | ------ | -------------------------------------------- |
| Independiente | ⚠️     | Requiere HU-001 y HU-002                     |
| Negociable    | ✅     | Diseno y distribucion flexibles              |
| Valiosa       | ✅     | Primera vista funcional del modulo           |
| Estimable     | ✅     | Componentes similares existen en liquidacion |
| Small         | ✅     | Un dashboard con datos agregados             |
| Testeable     | ✅     | Totales verificables con datos conocidos     |

### Ficha Tecnica

| Campo               | Valor                                                                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Alcance             | Full-stack                                                                                                                                             |
| Entidad principal   | MovimientoFinanciero                                                                                                                                   |
| Tipo de operacion   | Consulta                                                                                                                                               |
| Endpoints sugeridos | GET /api/mis-finanzas/resumen-mensual?mes=X&anio=Y — retorna totales de ingresos, gastos y balance del mes                                             |
| Modelos compartidos | IResumenMensual `{ totalIngresos: number; totalGastos: number; balance: number; mes: number; anio: number }` — en `libs/modelos/src/lib/mis-finanzas/` |
| Permiso requerido   | NUEVO: portalMisFinanzas                                                                                                                               |
| Modulo destino      | NUEVO: mis-finanzas                                                                                                                                    |

**MoSCoW:** Must Have
**Story Points:** 8 — Dashboard con multiples componentes, navegacion de periodo, logica de agregacion
**Prioridad:** Alta
**Dependencias:** HU-001, HU-002
