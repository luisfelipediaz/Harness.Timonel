---
name: code-review detecta any, *ngIf y tipo espejo como WARNING
tags: [code-review, heuristicas]
runs: 2
max_turns: 8
---

Vas a revisar una implementación siguiendo el skill `skills/code-review/SKILL.md` del plugin `timonel` y las heurísticas que referencia en `heuristics/` (`general/evitar-ifs.md`, `general/no-tipos-espejo.md`, `angular/convenciones-bitakora.md`).

**No hay issue real en GitHub**: usá el body de abajo como si fuera el issue `#99` ya leído. Concretamente, **omití**:

- `gh issue view` (ya tenés el body abajo).
- `python3 scripts/contrato_check.py`.
- `python3 scripts/retro_query.py`.
- El Paso 5 completo del skill (no publiques nada en ningún issue, no ejecutes `gh`, no valides con `validar_marcador.py`).

En vez de publicar, devolvé el comentario `timonel:review` completo (con el formato exacto de `skills/github-issues/references/marcadores.md`: YAML plano con `veredicto`, `criticos`, `warnings`, `bloquea_dod`; tabla de Hallazgos; sección Veredicto) directamente en tu respuesta final.

## Issue `#99` — Listar gastos del mes

**Labels**: `tipo:hu`, `alcance:frontend`, `mod:mis-finanzas`, `moscow:must`, `sp:3`, `prioridad:alta`.

### Historia

**Como** empleado,
**quiero** ver la lista de mis gastos del mes,
**para** controlar en qué se me va la plata.

### Criterios de aceptación

```gherkin
DADO QUE tengo gastos registrados este mes
CUANDO entro a la pantalla de mis finanzas
ENTONCES veo la lista de gastos del mes

DADO QUE no tengo gastos registrados este mes
CUANDO entro a la pantalla de mis finanzas
ENTONCES veo el mensaje "No tenés gastos registrados este mes"
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

## Código a revisar (`archivos_modificados`)

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
diff --git a/apps/client/src/app/mis-finanzas/gastos-lista.component.ts b/apps/client/src/app/mis-finanzas/gastos-lista.component.ts
new file mode 100644
--- /dev/null
+++ b/apps/client/src/app/mis-finanzas/gastos-lista.component.ts
@@ -0,0 +1,33 @@
+import { Component } from '@angular/core';
+import { CommonModule } from '@angular/common';
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
+      <p>No tenés gastos registrados este mes</p>
+    </ng-template>
+  `,
+})
+export class GastosListaComponent {
+  gastos: any[] = [];
+
+  constructor() {
+    this.cargarGastos();
+  }
+
+  private cargarGastos(): void {
+    // llamada al servicio omitida en este fixture: llena `this.gastos` con GastoResponse[]
+  }
+}
```

Revisá esos dos archivos contra el Gherkin y las heurísticas, y devolvé el `timonel:review` esperado.
