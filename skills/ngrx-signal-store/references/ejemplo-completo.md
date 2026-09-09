# Ejemplo completo: módulo "productos"

Ejemplo de referencia para un módulo ficticio con estado, filtros y operaciones CRUD.

## Modelo de estado (productos.model.ts)

```typescript
export interface Producto {
  id: string;
  nombre: string;
  precio: number;
  activo: boolean;
}

export interface ProductosState {
  isLoading: boolean;
  productos: Producto[];
  productoSeleccionado: Producto | null;
  filtroNombre: string | null;
}

export interface FormularioProducto {
  nombre: string;
  precio: number;
}
```

## state/index.ts

```typescript
import { signalStore, withState } from '@ngrx/signals';
import { ProductosState } from '../productos.model';
import { actionsStore } from './actions';
import { effectsStore } from './effects';
import { selectorsStore } from './selectors';

const initialState: ProductosState = {
  isLoading: false,
  productos: [],
  productoSeleccionado: null,
  filtroNombre: null,
};

export const ProductosStore = signalStore(withState(initialState), actionsStore, selectorsStore, effectsStore);
```

## state/actions.ts

```typescript
import { patchState, withMethods } from '@ngrx/signals';
import { SignalsOf } from '../../app.model';
import { Producto, ProductosState } from '../productos.model';

export const actionsStore = withMethods((state: SignalsOf<Partial<ProductosState>>) => ({
  seleccionarProducto: (productoSeleccionado: Producto) => patchState(state, { productoSeleccionado }),
  limpiarSeleccion: () => patchState(state, { productoSeleccionado: null }),
  asignarFiltro: (filtroNombre: string) => patchState(state, { filtroNombre }),
}));
```

## state/selectors.ts

```typescript
import { computed } from '@angular/core';
import { StateSignals, withComputed } from '@ngrx/signals';
import { Producto, ProductosState } from '../productos.model';

export const selectorsStore = withComputed(({ productos, filtroNombre }: StateSignals<Partial<ProductosState>>) => {
  const productosFiltrados = computed(() => filtrarProductos(productos(), filtroNombre()));
  return {
    productosFiltrados,
    tieneProductos: computed(() => !!productosFiltrados().length),
    totalProductos: computed(() => productos().length),
  };
});

function filtrarProductos(productos: Producto[], filtro: string | null): Producto[] {
  if (!filtro) return productos;
  const filtroMinusc = filtro.toLowerCase();
  return productos.filter((p) => p.nombre.toLowerCase().includes(filtroMinusc));
}
```

## state/effects.ts

```typescript
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { patchState, withMethods } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { catchError, EMPTY, pipe, switchMap, tap } from 'rxjs';
import { SignalsOf } from '../../app.model';
import { FormularioProducto, ProductosState } from '../productos.model';
import { ProductosService } from '../productos.service';

export const effectsStore = withMethods((store: SignalsOf<Partial<ProductosState>>) => {
  const service = inject(ProductosService);
  const router = inject(Router);

  const cargarProductos = rxMethod<void>(
    pipe(
      tap(() => patchState(store, { isLoading: true })),
      switchMap(() =>
        service.obtenerProductos().pipe(
          tap((productos) => patchState(store, { productos, isLoading: false })),
          catchError(() => EMPTY)
        )
      )
    )
  );

  const guardarProducto = rxMethod<FormularioProducto>(
    pipe(
      switchMap((formulario) =>
        service.guardar(formulario).pipe(
          tap(() => {
            effects.cargarProductos();
            router.navigateByUrl('Productos');
          }),
          catchError(() => EMPTY)
        )
      )
    )
  );

  const eliminarProducto = rxMethod<string>(
    pipe(
      switchMap((id) =>
        service.eliminar(id).pipe(
          tap(() => effects.cargarProductos()),
          catchError(() => EMPTY)
        )
      )
    )
  );

  const effects = {
    cargarProductos,
    guardarProducto,
    eliminarProducto,
  };
  return effects;
});
```

## Registro en rutas (productos.routes.ts)

```typescript
import { Routes } from '@angular/router';
import { ProductosContainerComponent } from './productos-container/productos-container.component';
import { ProductosService } from './productos.service';
import { ProductosStore } from './state';

export const ProductosRoutes: Routes = [
  {
    path: '',
    component: ProductosContainerComponent,
    providers: [ProductosStore, ProductosService],
  },
];
```

## Consumo en componentes

El componente inyecta el store directamente. No hay facade separado.

```typescript
import { Component, inject, OnInit } from '@angular/core';
import { ProductosStore } from '../state';

@Component({
  selector: 'app-listado-productos',
  templateUrl: './listado-productos.component.html',
})
export class ListadoProductosComponent implements OnInit {
  store = inject(ProductosStore);

  ngOnInit(): void {
    this.store.cargarProductos();
  }
}
```

En el template, todas las señales se leen con `()`:

```html
@if (store.isLoading()) {
<app-spinner />
} @else if (store.tieneProductos()) { @for (producto of store.productosFiltrados(); track producto.id) {
<app-producto-card [producto]="producto" (seleccionar)="store.seleccionarProducto($event)" (eliminar)="store.eliminarProducto($event)" />
} } @else {
<p>No hay productos.</p>
}
```

## Tests del store (productos.facade.spec.ts)

Archivo centralizado que prueba actions, selectors y effects del store:

```typescript
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ProductosStore } from './state';
import { ProductosService } from './productos.service';
import { Producto } from './productos.model';

describe('ProductosStore (facade)', () => {
  let store: InstanceType<typeof ProductosStore>;
  let httpMock: HttpTestingController;

  const productosMock: Producto[] = [
    { id: '1', nombre: 'Producto A', precio: 100, activo: true },
    { id: '2', nombre: 'Producto B', precio: 200, activo: false },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), ProductosStore, ProductosService],
    });
    store = TestBed.inject(ProductosStore);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  // --- Actions ---

  it('debe asignar el filtro cuando se llama asignarFiltro', () => {
    store.asignarFiltro('buscado');
    expect(store.filtroNombre()).toBe('buscado');
  });

  it('debe seleccionar un producto', () => {
    store.seleccionarProducto(productosMock[0]);
    expect(store.productoSeleccionado()).toEqual(productosMock[0]);
  });

  it('debe limpiar la selección', () => {
    store.seleccionarProducto(productosMock[0]);
    store.limpiarSeleccion();
    expect(store.productoSeleccionado()).toBeNull();
  });

  // --- Selectors ---

  it('debe filtrar productos por nombre', () => {
    store.cargarProductos();
    httpMock.expectOne('/api/productos').flush(productosMock);

    store.asignarFiltro('Producto A');
    expect(store.productosFiltrados()).toEqual([productosMock[0]]);
  });

  it('debe indicar si tiene productos', () => {
    expect(store.tieneProductos()).toBe(false);

    store.cargarProductos();
    httpMock.expectOne('/api/productos').flush(productosMock);

    expect(store.tieneProductos()).toBe(true);
  });

  // --- Effects ---

  it('debe cargar productos y actualizar el estado', () => {
    store.cargarProductos();

    expect(store.isLoading()).toBe(true);

    httpMock.expectOne('/api/productos').flush(productosMock);

    expect(store.isLoading()).toBe(false);
    expect(store.productos()).toEqual(productosMock);
  });

  it('debe guardar un producto y recargar la lista', () => {
    const formulario = { nombre: 'Nuevo', precio: 300 };

    store.guardarProducto(formulario);

    httpMock.expectOne('/api/productos').flush({});
    httpMock.expectOne('/api/productos').flush(productosMock);

    expect(store.productos()).toEqual(productosMock);
  });

  it('debe eliminar un producto y recargar la lista', () => {
    store.eliminarProducto('1');

    httpMock.expectOne('/api/productos/1').flush({});
    httpMock.expectOne('/api/productos').flush([productosMock[1]]);

    expect(store.productos()).toEqual([productosMock[1]]);
  });
});
```

## Tests de componentes con estado fakeado (listado-productos.component.spec.ts)

Los component specs proveen el store real pero fakean el estado con `patchState` — no prueban lógica del store:

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { patchState } from '@ngrx/signals';
import { ProductosStore } from '../state';
import { ProductosService } from '../productos.service';
import { ListadoProductosComponent } from './listado-productos.component';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Producto } from '../productos.model';

describe('ListadoProductosComponent', () => {
  let component: ListadoProductosComponent;
  let fixture: ComponentFixture<ListadoProductosComponent>;
  let store: InstanceType<typeof ProductosStore>;

  const productosMock: Producto[] = [{ id: '1', nombre: 'Producto A', precio: 100, activo: true }];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ListadoProductosComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), ProductosStore, ProductosService],
    });
    store = TestBed.inject(ProductosStore);
    fixture = TestBed.createComponent(ListadoProductosComponent);
    component = fixture.componentInstance;
  });

  it('debe mostrar el listado cuando hay productos', () => {
    patchState(store, {
      productos: productosMock,
      isLoading: false,
    });
    fixture.detectChanges();

    const cards = fixture.nativeElement.querySelectorAll('app-producto-card');
    expect(cards.length).toBe(1);
  });

  it('debe mostrar spinner cuando está cargando', () => {
    patchState(store, { isLoading: true });
    fixture.detectChanges();

    const spinner = fixture.nativeElement.querySelector('app-spinner');
    expect(spinner).toBeTruthy();
  });

  it('debe mostrar mensaje vacío cuando no hay productos', () => {
    patchState(store, {
      productos: [],
      isLoading: false,
    });
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('No hay productos');
  });
});
```
