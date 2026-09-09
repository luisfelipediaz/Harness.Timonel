# Backlog: Mis Finanzas — Modulo de Finanzas Personales

Creado: 2026-03-30
Objetivo: Permitir a los empleados gestionar sus finanzas personales combinando el neto a pagar de liquidacion con el registro manual de gastos, ingresos adicionales, presupuestos y deudas de tarjeta de credito, centralizando todo en una sola aplicacion.
Usuarios: Todos los empleados que usan miBitakora
Total Story Points: 244

## Estructura de archivos

Las historias completadas se consolidan en un solo `completadas.md` por epica.
Las historias pendientes se mantienen como archivos individuales.

```
docs/user-stories/
├── BACKLOG.md                          (este archivo — indice)
├── epica-1-infraestructura/            completadas.md (HU-001 a HU-003)
├── epica-2-gestion-ingresos/           completadas.md (HU-004, HU-005, HU-074)
├── epica-3-gestion-gastos/             completadas.md + HU-011 pendiente
├── epica-4-presupuesto-alertas/        HU-012 a HU-015 pendientes
├── epica-5-mejora-ux/                  completadas.md + 9 pendientes
├── epica-6-refactorizacion/            completadas.md + 3 pendientes
├── epica-7-limpieza-dependencias/      completadas.md + 2 pendientes
├── epica-8-ingresos-recurrentes/       completadas.md (HU-076 a HU-084)
├── epica-9-ajustar-ingreso-nomina/     HU-097 a HU-099 pendientes
├── epica-10-gestos-nativos/            HU-100 a HU-102 pendientes
```

## Progreso

### Epica 1: Infraestructura del Modulo Mis Finanzas

- [x] [HU-001](epica-1-infraestructura/completadas.md): Estructura base del modulo Angular + API — Must Have (8 SP)
- [x] [HU-002](epica-1-infraestructura/completadas.md): Esquema MongoDB para movimientos financieros — Must Have (5 SP)
- [x] [HU-003](epica-1-infraestructura/completadas.md): Dashboard principal con balance mensual — Must Have (8 SP)

### Epica 2: Gestion de Ingresos

- [x] ~~[HU-004](epica-2-gestion-ingresos/completadas.md): Ingreso salarial automatico desde datos de nomina~~ — Reemplazada por HU-054
- [x] [HU-005](epica-2-gestion-ingresos/completadas.md): Registro manual de ingresos adicionales — Must Have (5 SP)
- [x] [HU-074](epica-2-gestion-ingresos/completadas.md): Mostrar ingreso de nomina como item en lista de ingresos — Must Have (5 SP)

### Epica 3: Gestion de Gastos

- [x] [HU-007](epica-3-gestion-gastos/completadas.md): Registro manual de gastos con categoria — Must Have (5 SP)
- [x] [HU-008](epica-3-gestion-gastos/completadas.md): Gestion de categorias personalizables — Must Have (5 SP)
- [x] [HU-010](epica-3-gestion-gastos/completadas.md): Gastos fijos y recurrentes con auto-registro mensual — Should Have (8 SP)
- [ ] [HU-011](epica-3-gestion-gastos/hu-011-deuda-tarjeta-credito.md): Gestion de deuda de tarjeta de credito — Should Have (8 SP)

### Epica 4: Presupuesto y Alertas

- [ ] [HU-012](epica-4-presupuesto-alertas/hu-012-presupuesto-mensual-categoria.md): Definir presupuesto mensual por categoria — Should Have (8 SP)
- [ ] [HU-013](epica-4-presupuesto-alertas/hu-013-progreso-presupuesto-vs-gasto.md): Visualizacion de progreso presupuesto vs gasto real — Should Have (5 SP)
- [ ] [HU-014](epica-4-presupuesto-alertas/hu-014-alertas-presupuesto.md): Alertas cuando el gasto se acerca al presupuesto — Could Have (5 SP)
- [ ] [HU-015](epica-4-presupuesto-alertas/hu-015-resumen-historico.md): Resumen historico mes a mes — Could Have (5 SP)

### Epica 5: Mejora de Experiencia de Usuario (UX)

- [x] [HU-027](epica-5-mejora-ux/completadas.md): Marcar gastos recurrentes como pagados en el dashboard — Must Have (8 SP)
- [ ] [HU-016](epica-5-mejora-ux/hu-016-grafico-donut.md): Grafico donut de distribucion de gastos por categoria — Could Have (5 SP)
- [ ] [HU-017](epica-5-mejora-ux/hu-017-tendencia-financiera.md): Indicador de tendencia financiera vs mes anterior — Should Have (3 SP)
- [x] [HU-018](epica-5-mejora-ux/completadas.md): Colores de categoria en listas de movimientos — Must Have (2 SP)
- [x] [HU-020](epica-5-mejora-ux/completadas.md): Confirmacion en acciones destructivas — Must Have (2 SP)
- [ ] [HU-022](epica-5-mejora-ux/hu-022-filtros-listas.md): Filtros en listas de movimientos — Should Have (5 SP)
- [ ] [HU-023](epica-5-mejora-ux/hu-023-onboarding-guiado.md): Onboarding guiado para nuevos usuarios — Should Have (5 SP)
- [ ] [HU-024](epica-5-mejora-ux/hu-024-micro-animaciones.md): Micro-animaciones y feedback visual en acciones — Could Have (8 SP)
- [x] [HU-066](epica-5-mejora-ux/completadas.md): Spike — Planificar mejoras de diseno del modulo Mis Finanzas — Should Have (2 SP)
- [x] [HU-067](epica-5-mejora-ux/completadas.md): Tipografia hero para montos — Must Have (3 SP)
- [ ] [HU-068](epica-5-mejora-ux/hu-068-identidad-visual-header.md): Identidad visual del header del modulo — Should Have (5 SP)
- [x] [HU-069](epica-5-mejora-ux/completadas.md): Rediseno del dialog de movimiento — Should Have (5 SP)
- [ ] [HU-070](epica-5-mejora-ux/hu-070-empty-states-ilustrados.md): Empty states ilustrados — Could Have (3 SP)
- [x] [HU-071](epica-5-mejora-ux/completadas.md): Jerarquia visual de cards — Should Have (2 SP)
- [x] [HU-075](epica-5-mejora-ux/completadas.md): Rediseno del dialog de gasto recurrente (alinear con HU-069) — Should Have (3 SP)
- [ ] [HU-092](epica-5-mejora-ux/hu-092-fix-keyboard-ios-dark-mode.md): Fix barra negra entre contenido y teclado en iOS dark mode — Must Have (2 SP)

### Epica 6: Refactorizacion y Deuda Tecnica

- [x] [HU-028](epica-6-refactorizacion/completadas.md): Reemplazar mock service con llamadas HTTP reales — Must Have (5 SP)
- [x] [HU-029](epica-6-refactorizacion/completadas.md): Extraer validacion de categoria como metodo reutilizable en API — Must Have (2 SP)
- [x] [HU-030](epica-6-refactorizacion/completadas.md): Corregir N+1 query en listado de gastos recurrentes — Must Have (3 SP)
- [x] [HU-031](epica-6-refactorizacion/completadas.md): Extraer utilidad de rango de fechas mensual — Should Have (1 SP)
- [x] [HU-032](epica-6-refactorizacion/completadas.md): Agregar indices de base de datos a MovimientosFinancieros — Should Have (1 SP)
- [x] [HU-033](epica-6-refactorizacion/completadas.md): Unificar dialogs de gasto e ingreso en un solo componente — Must Have (3 SP)
- [x] [HU-034](epica-6-refactorizacion/completadas.md): Unificar dialogs de confirmacion de eliminacion — Should Have (2 SP)
- [x] [HU-035](epica-6-refactorizacion/completadas.md): Crear pipe de categoria para lookups en templates — Should Have (2 SP)
- [x] [HU-036](epica-6-refactorizacion/completadas.md): Corregir race condition en effect marcarGastoPagado — Must Have (1 SP)
- [ ] [HU-037](epica-6-refactorizacion/hu-037-validacion-periodo-dtos.md): Mover validacion de periodo a DTO con class-validator — Should Have (1 SP)
- [x] [HU-038](epica-6-refactorizacion/completadas.md): Descomponer metodo ejecutarRecurrentesPendientes — Could Have (2 SP)
- [x] [HU-039](epica-6-refactorizacion/completadas.md): Extraer validacion de nombre unico de categoria — Should Have (1 SP)
- [x] [HU-040](epica-6-refactorizacion/completadas.md): Agregar tests unitarios para NgRx state del client — Must Have (8 SP)
- [x] [HU-041](epica-6-refactorizacion/completadas.md): Extraer constantes de iconos y colores de categorias — Could Have (1 SP)
- [x] [HU-047](epica-6-refactorizacion/completadas.md): Corregir cambiarPeriodo para que recargue gastos — Must Have (1 SP)
- [x] [HU-048](epica-6-refactorizacion/completadas.md): Mover providers de NgRx a la ruta padre de mis-finanzas — Must Have (2 SP)
- [ ] [HU-049](epica-6-refactorizacion/hu-049-date-nivel-modulo.md): Reemplazar Date estatica a nivel de modulo por calculo en tiempo de ejecucion — Should Have (1 SP)
- [x] [HU-050](epica-6-refactorizacion/completadas.md): Reducir duplicacion en reducer y effects NgRx con helpers genericos — Could Have (5 SP)
- [x] [HU-051](epica-6-refactorizacion/completadas.md): Extraer componente reutilizable de card de categoria — Should Have (2 SP)
- [x] [HU-052](epica-6-refactorizacion/completadas.md): Consolidar clases CSS utilitarias duplicadas en archivo compartido — Could Have (1 SP)
- [x] [HU-053](epica-6-refactorizacion/completadas.md): Eliminar codigo muerto del modulo mis-finanzas — Should Have (2 SP)
- [x] [HU-054](epica-6-refactorizacion/completadas.md): Eliminar sincronizacion de salario y usar neto a pagar de liquidacion — Must Have (8 SP)
- [x] [HU-055](epica-6-refactorizacion/completadas.md): Unificar CRUD de ingreso y gasto en metodos genericos — Must Have (3 SP)
- [x] [HU-056](epica-6-refactorizacion/completadas.md): Extraer utilidad de actualizacion parcial — Should Have (2 SP)
- [x] [HU-057](epica-6-refactorizacion/completadas.md): Eliminar side-effect de inicializacion en listarCategorias — Should Have (2 SP)
- [x] [HU-058](epica-6-refactorizacion/completadas.md): Parametrizar validarCategoriaParaTipo por tipo esperado — Must Have (2 SP)
- [ ] [HU-059](epica-6-refactorizacion/hu-059-mover-mappers-a-aplicacion.md): Mover mappers de servicio a capa de aplicacion — Should Have (2 SP)
- [x] [HU-060](epica-6-refactorizacion/completadas.md): Extraer MisFinanzasModule del AppModule — Should Have (3 SP)
- [x] [HU-061](epica-6-refactorizacion/completadas.md): Centralizar type aliases de documentos y helper ObjectId — Could Have (1 SP)
- [x] [HU-062](epica-6-refactorizacion/completadas.md): Reemplazar actualizacion pesimista por optimista en ingresos y gastos — Should Have (5 SP)
- [x] [HU-063](epica-6-refactorizacion/completadas.md): Dividir effects NgRx por dominio en archivos separados — Must Have (3 SP)
- [x] [HU-064](epica-6-refactorizacion/completadas.md): Extraer handlers del reducer por dominio en archivos separados — Should Have (3 SP)
- [x] [HU-065](epica-6-refactorizacion/completadas.md): Separar template y estilos inline de CategoriaDialogComponent — Should Have (1 SP)
- [x] [HU-073](epica-6-refactorizacion/completadas.md): Migrar colores hardcoded a CSS variables — Must Have (2 SP)
- [x] [HU-093](epica-6-refactorizacion/completadas.md): Agregar periodo (mes/anio) a MovimientoFinanciero y refactorizar queries — Must Have (8 SP)
- [x] [HU-094](epica-6-refactorizacion/completadas.md): Hacer fecha opcional en movimientos financieros — Should Have (3 SP)
- [x] [HU-095](epica-6-refactorizacion/completadas.md): Hacer diaRecurrencia opcional en recurrentes — Should Have (3 SP)
- [x] [HU-096](epica-6-refactorizacion/completadas.md): Eliminar Response Models innecesarios — Should Have (3 SP)

### Epica 7: Limpieza de Dependencias y Salud del Proyecto

- [x] [HU-043](epica-7-limpieza-dependencias/completadas.md): Eliminar dependencias npm no usadas del package.json — Must Have (3 SP)
- [x] [HU-044](epica-7-limpieza-dependencias/completadas.md): Habilitar regla ESLint de imports no usados en client y corregir violaciones — Must Have (5 SP)
- [ ] [HU-045](epica-7-limpieza-dependencias/hu-045-auditoria-seguridad-npm.md): Ejecutar auditoria de seguridad npm y remediar vulnerabilidades — Should Have (3 SP)
- [ ] [HU-046](epica-7-limpieza-dependencias/hu-046-depcheck-ci.md): Integrar depcheck en CI para prevenir futuras dependencias no usadas — Could Have (3 SP)

### Epica 8: Ingresos Recurrentes

- [x] [HU-076](epica-8-ingresos-recurrentes/completadas.md): Renombrar campo `pagado` a `confirmado` en todo el modulo — Must Have (3 SP)
- [x] [HU-077](epica-8-ingresos-recurrentes/completadas.md): Modelos compartidos para ingresos recurrentes — Must Have (2 SP)
- [x] [HU-078](epica-8-ingresos-recurrentes/completadas.md): Esquema Mongoose y servicio de datos para ingresos recurrentes — Must Have (3 SP)
- [x] [HU-079](epica-8-ingresos-recurrentes/completadas.md): Logica de negocio (aplicacion) CRUD de ingresos recurrentes — Must Have (3 SP)
- [x] [HU-080](epica-8-ingresos-recurrentes/completadas.md): Endpoints REST CRUD para ingresos recurrentes — Must Have (2 SP)
- [x] [HU-081](epica-8-ingresos-recurrentes/completadas.md): Registro mensual genera gastos e ingresos recurrentes — Must Have (5 SP)
- [x] [HU-082](epica-8-ingresos-recurrentes/completadas.md): NgRx State Management para ingresos recurrentes — Must Have (5 SP)
- [x] [HU-083](epica-8-ingresos-recurrentes/completadas.md): Renombrar ruta y reestructurar pagina con dos secciones — Must Have (5 SP)
- [x] [HU-084](epica-8-ingresos-recurrentes/completadas.md): Dialog crear/editar ingreso recurrente — Must Have (3 SP)

### Epica 9: Ajustar Ingreso de Nomina a Periodos de Liquidacion

- [x] [HU-097](epica-9-ajustar-ingreso-nomina/hu-097-esquema-endpoint-upsert-nomina.md): Persistir el ingreso de nomina como movimiento financiero con endpoint idempotente — Should Have (5 SP)
- [x] [HU-098](epica-9-ajustar-ingreso-nomina/hu-098-algoritmo-sincronizacion-frontend.md): Algoritmo de sincronizacion del ingreso de nomina desde liquidacion — Should Have (8 SP)
- [x] [HU-099](epica-9-ajustar-ingreso-nomina/hu-099-eliminar-calculo-virtual-nomina.md): Eliminar el calculo virtual del ingreso de nomina y consolidar la fuente unica — Should Have (3 SP)

### Epica 10: Gestos Nativos en Mis Finanzas (iOS/Android via Capacitor)

- [ ] [HU-100](epica-10-gestos-nativos/hu-100-swipe-horizontal-cambiar-mes.md): Swipe horizontal nativo para cambiar de mes en Mis Finanzas — Should Have (5 SP)
- [ ] [HU-101](epica-10-gestos-nativos/hu-101-pull-to-refresh-dashboard.md): Pull-to-refresh nativo en el dashboard de Mis Finanzas — Should Have (5 SP)
- [ ] [HU-102](epica-10-gestos-nativos/hu-102-haptic-feedback-acciones-criticas.md): Haptic feedback en acciones criticas de Mis Finanzas — Should Have (3 SP)

> Marca con `[x]` conforme se implemente cada historia.

## Resumen

| Categoria   | Cantidad | Story Points |
| ----------- | -------- | ------------ |
| Must Have   | 34       | 127          |
| Should Have | 34       | 119          |
| Could Have  | 10       | 36           |
| Won't Have  | 0        | —            |
| **Total**   | **77**   | **282**      |

## Definicion de Ready (DoR)

- [ ] La historia tiene formato correcto (rol, funcionalidad, valor)
- [ ] Los criterios de aceptacion son claros y verificables
- [ ] La historia esta estimada en Story Points
- [ ] No hay bloqueos ni dependencias sin resolver
- [ ] El equipo entiende la historia y puede implementarla en un sprint

## Definicion de Done (DoD)

- [ ] Codigo implementado y funcionando
- [ ] Tests unitarios escritos y pasando
- [ ] Lint sin errores (`nx lint client` / `nx lint api`)
- [ ] Code review aprobado
- [ ] QA validado contra criterios de aceptacion
- [ ] Sin regresiones en funcionalidad existente
- [ ] Documentacion actualizada si aplica

## Notas Tecnicas

- **Client**: Angular 20, modulo lazy-loaded, NgRx store con facade, componentes standalone donde aplique
- **API**: NestJS 10, patron Controller > Aplicacion > Dominio > Servicio > Esquema
- **Base de datos**: MongoDB con Mongoose, coleccion propia para finanzas personales
- **Look & Feel**: Diseno minimalista y funcional — balance + lista unica de movimientos + botones de accion en cards. Sin decoraciones innecesarias.
- **Privacidad**: Los datos financieros personales son visibles unicamente para el empleado propietario
- **Permisos**: Nuevo permiso en `permisosAplicacion` para el modulo Mis Finanzas
