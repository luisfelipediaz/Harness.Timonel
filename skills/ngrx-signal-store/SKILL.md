---
name: ngrx-signal-store
description: Expert in developing NgRx Signal Stores for Angular applications. Use this skill whenever the user asks to create, modify, extend, or review Angular state management code — including stores, state, effects, actions, selectors, or facades. Trigger on phrases like "crea el store", "agrega un effect", "nuevo módulo con estado", "refactoriza el store", "manejo de estado", "ngrx", "signal store", "withMethods", "rxMethod", "patchState", or any mention of NgRx in an Angular context. Also trigger proactively when the user shares Angular module code that lacks a store but clearly needs one.
---

# NgRx Signal Store

El patrón aprobado para gestión de estado es **`@ngrx/signals` Signal Store**. El store es el facade — no hay capa intermedia separada.

## Cuándo leer los archivos de referencia

- **Antes de crear cualquier store o capa de estado**: lee `references/arquitectura.md`
- **Para ver código completo de los 4 archivos**: lee `references/ejemplo-completo.md`

## Estructura de archivos

Cada módulo con estado tiene una carpeta `state/` con exactamente 4 archivos:

```
<modulo>/
├── <modulo>.model.ts          # Interface del estado aquí
├── <modulo>.facade.spec.ts    # Tests centralizados del store
├── <modulo>.routes.ts         # providers: [XxxStore, XxxService]
└── state/
    ├── index.ts               # signalStore() + initialState
    ├── actions.ts             # withMethods + patchState (síncronos)
    ├── selectors.ts           # withComputed + computed() (derivados)
    └── effects.ts             # withMethods + rxMethod (async)
```

## Convenciones que SIEMPRE se aplican

**Tipos del store parameter:**

- `withMethods`: `(store: SignalsOf<Partial<XxxState>>)`
- `withComputed`: `({ campo1, campo2 }: StateSignals<Partial<XxxState>>)`

El tipo `SignalsOf<T>` es un helper del proyecto:

```typescript
type SignalsOf<T extends Record<string, any>> = {
  [K in keyof T]: Signal<T[K]>;
} & WritableStateSource<T>;
```

**Inyección de dependencias**: siempre funcional (`inject()`) dentro de `withMethods`, nunca por constructor.

**Provisión en rutas**: el store se provee a nivel de ruta, no en root:

```typescript
providers: [XxxStore, XxxService];
```

**Consumo en componentes**: sin facade, el componente inyecta directamente:

```typescript
store = inject(XxxStore);
```

**Error handling**: `catchError(() => EMPTY)` — silencioso, sin re-throw.

**Self-referencing effects**: cuando un effect necesita llamar a otro del mismo store:

```typescript
const effects = { efectoA, efectoB };
return effects;
// Dentro de efectoB: effects.efectoA();
```

**Acceso a estado raíz (cross-module)**: inyectar el `Store` clásico solo para leer el estado global compartido:

```typescript
const storeAdmin = inject(Store<fromRootPrincipal.State>);
// En rxMethod:
concatLatestFrom(() => from(storeAdmin.select(fromRootPrincipal.detallesContrato)));
```

## Estrategia de testing

### Tests del store (`<modulo>.facade.spec.ts`)

Archivo centralizado que prueba el store completo como facade:

- Provee el store real + servicio real + `HttpTestingController` en TestBed
- **Actions**: llama al método síncrono, verifica que el estado cambió correctamente
- **Selectors**: dado un estado, verifica que el `computed` devuelve el valor derivado esperado
- **Effects**: dispara el effect, intercepta la petición HTTP con `HttpTestingController`, verifica que el estado se actualiza
- Usa `@sinco/utilidades-test-bitakora` para helpers y matchers custom
- Mínimo: 1 test por action + 1 test por selector + 1 test happy path por effect

### Tests de componentes (`*.component.spec.ts`)

- Proveen el store real pero fakean el estado con `patchState` antes de cada test
- NO prueban lógica del store — eso va en el `facade.spec.ts`
- Solo verifican que el componente reacciona correctamente al estado
