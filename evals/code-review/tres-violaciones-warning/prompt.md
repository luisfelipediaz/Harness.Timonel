---
name: code-review detecta any, *ngIf y tipo espejo como WARNING
tags: [code-review, heuristicas]
runs: 2
max_turns: 12
---

Vas a revisar una implementación siguiendo el skill `skills/code-review/SKILL.md` del plugin `timonel`.

Las heurísticas **se descubren por glob**, como indica el Paso 1 del skill: no hay una lista de nombres que leer. Para este caso, trata al consumidor como si su `.claude/timonel.config.json` declarara `stack.frontend: "Angular 21"` y `heuristicsDir: null`; el alcance del issue es `Frontend`, así que el glob del Paso 1 debe traerte **`heuristics/general/*.md` más `heuristics/angular/*.md`**. Aplicá todas las que ese glob traiga a disco.

**No hay issue real en GitHub**: usa el body de abajo como si fuera el issue `#99` ya leído. Concretamente, **omite**:

- `gh issue view` (ya tienes el body abajo).
- `python3 scripts/contrato_check.py`.
- `python3 scripts/retro_query.py`.
- El Paso 5 completo del skill (no publiques nada en ningún issue, no ejecutes `gh`, no valides con `validar_marcador.py`).

En vez de publicar, devuelve el comentario `timonel:review` completo (con el formato exacto de `skills/github-issues/references/marcadores.md`: YAML plano con `veredicto`, `criticos`, `warnings`, `bloquea_dod`; tabla de Hallazgos; sección Veredicto) directamente en tu respuesta final.

## Issue `#99` — Listar gastos del mes

**Labels**: `tipo:hu`, `alcance:frontend`, `mod:mis-finanzas`, `moscow:must`, `sp:3`, `prioridad:alta`.

### Historia

**Como** empleado,
**quiero** ver la lista de mis gastos del mes,
**para** controlar en qué se va mi dinero.

### Criterios de aceptación

```gherkin
DADO QUE tengo gastos registrados este mes
CUANDO entro a la pantalla de mis finanzas
ENTONCES veo la lista de gastos del mes

DADO QUE no tengo gastos registrados este mes
CUANDO entro a la pantalla de mis finanzas
ENTONCES veo el mensaje "No tienes gastos registrados este mes"
```

### Ficha técnica

| Campo             | Valor                              |
| ----------------- | ----------------------------------- |
| Alcance           | Frontend                            |
| Entidad principal | Gasto                               |
| Tipo de operación | Consulta                            |
| Permiso requerido | TiposDePermisos.VerGastos           |
| Módulo destino    | mis-finanzas                        |

### Endpoints

- `GET /api/mis-finanzas/gastos` — ya existe, este cambio solo lo consume desde el frontend.

### Notas técnicas

- `GastosListaComponent` se monta en la ruta ya existente de `mis-finanzas`; el archivo de rutas no cambia y no es parte del alcance de esta historia.

## Código a revisar (`archivos_modificados`)

Resultado de consolidación ya disponible: `TESTS_RESULTADO: PASSED` (el spec de abajo corre y pasa), `LINT_RESULTADO: PASSED`. No re-ejecutes tests.

```diff
diff --git a/libs/modelos/src/gasto.ts b/libs/modelos/src/gasto.ts
new file mode 100644
--- /dev/null
+++ b/libs/modelos/src/gasto.ts
@@ -0,0 +1,6 @@
+export interface Gasto {
+  id: string;
+  fecha: string;
+  monto: number;
+  categoria: string;
+}
diff --git a/apps/client/src/app/mis-finanzas/gastos.service.ts b/apps/client/src/app/mis-finanzas/gastos.service.ts
new file mode 100644
--- /dev/null
+++ b/apps/client/src/app/mis-finanzas/gastos.service.ts
@@ -0,0 +1,14 @@
+import { HttpClient } from '@angular/common/http';
+import { inject, Injectable } from '@angular/core';
+import { Observable } from 'rxjs';
+import { Gasto } from '@bitakora/modelos';
+
+@Injectable({ providedIn: 'root' })
+export class GastosService {
+  private readonly http = inject(HttpClient);
+  private readonly url = '/api/mis-finanzas/gastos';
+
+  listarDelMes(): Observable<Gasto[]> {
+    return this.http.get<Gasto[]>(this.url);
+  }
+}
diff --git a/apps/client/src/app/mis-finanzas/gastos-lista.component.ts b/apps/client/src/app/mis-finanzas/gastos-lista.component.ts
new file mode 100644
--- /dev/null
+++ b/apps/client/src/app/mis-finanzas/gastos-lista.component.ts
@@ -0,0 +1,35 @@
+import { Component, inject, OnInit } from '@angular/core';
+import { CommonModule } from '@angular/common';
+import { GastosService } from './gastos.service';
+
+interface GastoResponse {
+  id: string;
+  fecha: string;
+  monto: number;
+  categoria: string;
+}
+
+@Component({
+  selector: 'app-gastos-lista',
+  standalone: true,
+  imports: [CommonModule],
+  template: `
+    <ul *ngIf="gastos.length; else vacio">
+      <li *ngFor="let g of gastos">{{ g.categoria }} - {{ g.monto }}</li>
+    </ul>
+    <ng-template #vacio>
+      <p>No tienes gastos registrados este mes</p>
+    </ng-template>
+  `,
+})
+export class GastosListaComponent implements OnInit {
+  private readonly gastosService = inject(GastosService);
+
+  gastos: any[] = [];
+
+  ngOnInit(): void {
+    this.gastosService.listarDelMes().subscribe((gastos: GastoResponse[]) => {
+      this.gastos = gastos;
+    });
+  }
+}
diff --git a/apps/client/src/app/mis-finanzas/gastos-lista.component.spec.ts b/apps/client/src/app/mis-finanzas/gastos-lista.component.spec.ts
new file mode 100644
--- /dev/null
+++ b/apps/client/src/app/mis-finanzas/gastos-lista.component.spec.ts
@@ -0,0 +1,36 @@
+import { ComponentFixture, TestBed } from '@angular/core/testing';
+import { of } from 'rxjs';
+import { Gasto } from '@bitakora/modelos';
+import { GastosListaComponent } from './gastos-lista.component';
+import { GastosService } from './gastos.service';
+
+describe('GastosListaComponent', () => {
+  let fixture: ComponentFixture<GastosListaComponent>;
+  const gastosService = { listarDelMes: jest.fn() };
+
+  async function crear(gastos: Gasto[]): Promise<void> {
+    gastosService.listarDelMes.mockReturnValue(of(gastos));
+    await TestBed.configureTestingModule({
+      imports: [GastosListaComponent],
+      providers: [{ provide: GastosService, useValue: gastosService }],
+    }).compileComponents();
+    fixture = TestBed.createComponent(GastosListaComponent);
+    fixture.detectChanges();
+  }
+
+  it('muestra la lista de gastos del mes cuando hay gastos registrados', async () => {
+    await crear([
+      { id: '1', fecha: '2026-09-01', monto: 120, categoria: 'Transporte' },
+      { id: '2', fecha: '2026-09-03', monto: 80, categoria: 'Comida' },
+    ]);
+    const items = fixture.nativeElement.querySelectorAll('li');
+    expect(items.length).toBe(2);
+    expect(items[0].textContent).toContain('Transporte');
+  });
+
+  it('muestra el mensaje de vacío cuando no hay gastos registrados', async () => {
+    await crear([]);
+    expect(fixture.nativeElement.querySelector('li')).toBeNull();
+    expect(fixture.nativeElement.textContent).toContain('No tienes gastos registrados este mes');
+  });
+});
```
Revisa esos cuatro archivos contra el Gherkin y las heurísticas, y devuelve el `timonel:review` esperado.
