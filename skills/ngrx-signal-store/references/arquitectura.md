# Arquitectura del NgRx Signal Store

## Composición del signalStore()

El store se construye componiendo funciones de `@ngrx/signals`. El orden importa: cada capa puede acceder a lo definido antes de ella.

```typescript
export const XxxStore = signalStore(
  withState(initialState), // 1. Estado base — accesible en capas siguientes
  actionsStore, // 2. withMethods — mutaciones síncronas
  selectorsStore, // 3. withComputed — valores derivados (puede usar state + actions)
  effectsStore // 4. withMethods — operaciones async (puede usar todo lo anterior)
);
```

## Capa 1: Estado (state/index.ts)

Define el estado inicial y ensambla el store:

```typescript
import { signalStore, withState } from '@ngrx/signals';
import { XxxState } from '../xxx.model';
import { actionsStore } from './actions';
import { effectsStore } from './effects';
import { selectorsStore } from './selectors';

const initialState: XxxState = {
  isLoading: false,
  items: [],
  itemSeleccionado: null,
};

export const XxxStore = signalStore(withState(initialState), actionsStore, selectorsStore, effectsStore);
```

El estado inicial debe declararse con el tipo explícito para que TypeScript infiera bien las señales.

## Capa 2: Actions — mutaciones síncronas (state/actions.ts)

Usa `withMethods` + `patchState`. Cada método recibe el valor nuevo y actualiza el estado directamente:

```typescript
import { patchState, withMethods } from '@ngrx/signals';
import { SignalsOf } from '../app.model'; // helper del proyecto
import { XxxState } from '../xxx.model';

export const actionsStore = withMethods((state: SignalsOf<Partial<XxxState>>) => ({
  seleccionarItem: (itemSeleccionado: Item) => patchState(state, { itemSeleccionado }),
  limpiarSeleccion: () => patchState(state, { itemSeleccionado: null }),
}));
```

Regla: si la operación no hace I/O ni es asíncrona, va en `actions.ts`.

## Capa 3: Selectors — estado derivado (state/selectors.ts)

Usa `withComputed` + `computed()` de Angular. Los helpers de cálculo van como funciones planas debajo del export:

```typescript
import { computed } from '@angular/core';
import { StateSignals, withComputed } from '@ngrx/signals';
import { XxxState } from '../xxx.model';

export const selectorsStore = withComputed(({ items, filtro }: StateSignals<Partial<XxxState>>) => {
  const itemsFiltrados = computed(() => filtrarItems(items(), filtro()));
  return {
    itemsFiltrados,
    tieneItems: computed(() => !!itemsFiltrados().length),
    totalItems: computed(() => items().length),
  };
});

function filtrarItems(items: Item[], filtro: string): Item[] {
  if (!filtro) return items;
  return items.filter((i) => i.nombre.includes(filtro));
}
```

Los computed pueden referenciarse entre sí dentro del mismo `withComputed` (como `itemsFiltrados` arriba).

## Capa 4: Effects — operaciones async (state/effects.ts)

Usa `withMethods` + `rxMethod` de `@ngrx/signals/rxjs-interop`. La inyección de dependencias es funcional (`inject()` dentro de la factory):

```typescript
import { inject } from '@angular/core';
import { patchState, withMethods } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { catchError, EMPTY, pipe, switchMap, tap } from 'rxjs';
import { SignalsOf } from '../app.model';
import { XxxState } from '../xxx.model';
import { XxxService } from '../xxx.service';

export const effectsStore = withMethods((store: SignalsOf<Partial<XxxState>>) => {
  const service = inject(XxxService);

  const cargarItems = rxMethod<void>(
    pipe(
      tap(() => patchState(store, { isLoading: true })),
      switchMap(() =>
        service.obtenerItems().pipe(
          tap((items) => patchState(store, { items, isLoading: false })),
          catchError(() => EMPTY)
        )
      )
    )
  );

  const effects = { cargarItems };
  return effects;
});
```

### RxJS operators más usados en effects

| Caso                                          | Operator           |
| --------------------------------------------- | ------------------ |
| Cancelar petición anterior cuando llega nueva | `switchMap`        |
| Esperar a que termine antes de aceptar otra   | `exhaustMap`       |
| Encolar y ejecutar en orden                   | `concatMap`        |
| Necesitar el estado actual del store raíz     | `concatLatestFrom` |

### Patrón self-referencing

Cuando un effect necesita disparar otro del mismo store (ej. recargar lista tras guardar):

```typescript
const guardar = rxMethod<Item>(
  pipe(
    switchMap((item) =>
      service.guardar(item).pipe(
        tap(() => effects.cargarItems()), // llama al otro effect
        catchError(() => EMPTY)
      )
    )
  )
);

const effects = { cargarItems, guardar };
return effects;
```

La clave es declarar `const effects = { ... }` y retornarlo — eso permite la auto-referencia.

## Tipos helper

### SignalsOf<T>

Tipo que convierte cada propiedad del estado en una `Signal<T>` y habilita `WritableStateSource` para poder llamar `patchState`:

```typescript
type SignalsOf<T extends Record<string, any>> = {
  [K in keyof T]: Signal<T[K]>;
} & WritableStateSource<T>;
```

Se usa como tipo del parámetro `store` en `withMethods`.

### StateSignals<T>

Tipo de `@ngrx/signals` (importado directamente del paquete). Se usa en `withComputed` para desestructurar las señales del estado:

```typescript
({ campo1, campo2 }: StateSignals<Partial<XxxState>>) => { ... }
```

Ambos tipos se usan con `Partial<XxxState>` para que cada archivo de la carpeta `state/` sea independiente y no acoplado a la forma completa del estado.

## Acceso al estado raíz compartido

Si el módulo necesita datos del store raíz (información de sesión, contrato, empleado, etc.), se inyecta el store clásico solo como fuente de lectura:

```typescript
import { concatLatestFrom } from '@ngrx/operators';
import { Store } from '@ngrx/store';
import { from } from 'rxjs';
import * as fromRoot from '../../state'; // store raíz del proyecto

// Dentro de withMethods:
const storeRaiz = inject(Store<fromRoot.State>);

const cargarConContexto = rxMethod<void>(
  pipe(
    concatLatestFrom(() => from(storeRaiz.select(fromRoot.datosEmpleado))),
    switchMap(([, { idEmpleado }]) =>
      service.obtener(idEmpleado).pipe(
        tap((items) => patchState(store, { items })),
        catchError(() => EMPTY)
      )
    )
  )
);
```
