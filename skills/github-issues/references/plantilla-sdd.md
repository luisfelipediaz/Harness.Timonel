# Plantilla — issue `tipo:sdd` (Software Design Document)

**Titulo**: `SDD — [feature o modificacion]`. Ej: `SDD — Marcación de turnos con captura de ubicación`.

**Labels**: `tipo:sdd`, `mod:<modulo>` (recomendado), `estado:borrador|listo`.

**Padre**: ninguno. **Hijos**: epicas (`tipo:epica`) derivadas.

Estructura fusionada de los SDD reales del Portal (`docs/especificaciones/`), del agente `sdd-specs` del Portal y del POC. Las secciones numeradas son fijas; una seccion que no aplica se deja con una linea `No aplica: <motivo>` (no se borra, para que el indice sea estable). El contenido escala con la complejidad.

## Body

````markdown
**Versión:** 1.0 · **Fecha:** YYYY-MM-DD · **Autor:** [git config user.name] · **Estado:** Borrador | Aprobado | Implementado
**Stack detectado:** [de `.claude/timonel.config.json` y del codigo real]
**Historial:**
- YYYY-MM-DD v1.0: version inicial

## 1. Resumen ejecutivo

[Que se construye, por que y que valor entrega. Maximo 5 lineas.]

## 2. Contexto y motivación

[Problema, antecedentes, evidencia del codigo actual (citar `ruta:linea`), referencias a issues (#N).]

## 3. Alcance

### 3.1 Proyectos y módulos afectados

| Proyecto | Tipo de cambio | Descripción |
| --- | --- | --- |
| `apps/api` | Nuevo módulo / extensión | ... |
| `apps/<app>` | Nuevo feature | ... |
| `libs/modelos` | Nuevas interfaces | ... |

### 3.2 Fuera de alcance

- ...

## 4. Requisitos funcionales

### RF-001 — [Nombre]

- **Actor:**
- **Precondición:**
- **Flujo principal:**
  1. ...
- **Flujos alternativos / errores:**
- **Postcondición:**

[Repetir RF-00N.]

## 5. Requisitos no funcionales

| ID | Categoría | Descripción | Criterio de aceptación |
| --- | --- | --- | --- |
| RNF-001 | Rendimiento | ... | ... |
| RNF-002 | Seguridad | ... | ... |

## 6. Decisiones de diseño

| # | Decisión | Alternativas consideradas | Razón |
| --- | --- | --- | --- |
| D-1 | ... | ... | ... |

## 7. Contrato de datos y API

### 7.1 Interfaces compartidas (`modelos.alias`, sin prefijo `I`, sin `any`)

```typescript
export interface NombreEntidad { campo: tipo; }
```

### 7.2 Esquemas / persistencia

[Esquema Mongoose nuevo o modificado; si es discriminador de la coleccion base; indices; migraciones.]

### 7.3 Endpoints

#### `[MÉTODO] /api/<modulo>/<recurso>`

- **Descripción:**
- **Auth:** `AuthorizationGuard<TiposDePermisos>` + permiso
- **Sesión:** campos de `Sesion` que consume
- **Request / Response:** bloques `typescript`
- **Errores:** tabla codigo → condicion

## 8. Diseño de componentes y estado

### 8.1 Backend — flujo por capas y archivos nuevos

```
Controller (@AuditoriaApi) → Aplicacion → Dominio → Servicio → Esquema
```

| Ruta | Clase | Capa | Responsabilidad |
| --- | --- | --- | --- |

Cambios en modulos existentes (providers, swaps `*Development`).

### 8.2 Frontend — containers, componentes, estado, rutas

| Ruta | Clase | Tipo | Responsabilidad |
| --- | --- | --- | --- |

- **Estado:** store raiz vs store del modulo; forma del estado; metodos/effects.
- **HTTP:** llamadas nuevas y cadena de interceptores.
- **Rutas y permisos:** ruta lazy, `data.permisos`, cadena de guards.
- **Estados de UI:** loading/skeleton, empty state, errores.
- **Flujo de datos:** `Componente → Facade/Store → HTTP → API` (```mermaid opcional).

## 9. Estrategia de pruebas

| Capa | Tipo | Herramienta | Cobertura objetivo |
| --- | --- | --- | --- |

**Escenarios críticos:**
- [ ] ...

## 10. Seguridad y permisos

Autenticación, autorización (permisos concretos), multi-tenancy (campos de `Sesion`), validación de inputs, datos sensibles, auditoría.

## 11. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
| --- | --- | --- | --- |

## 12. Plan de despliegue

1. [orden api/client, migraciones, feature flags, Capacitor sync si aplica]

**Retrocompatibilidad:** Sí/No — [explicacion]

## 13. Criterios de aceptación

- [ ] [Criterio verificable 1]
- [ ] Tests y lint en verde en los proyectos afectados

## 14. Épicas propuestas

- [ ] [Nombre de epica 1] — [1 linea]

(Al crearlas como sub-issues, reemplazar cada linea por `- [ ] #N`.)

## 15. Dudas abiertas

| # | Pregunta | Responsable | Estado |
| --- | --- | --- | --- |
| DA-1 | ... | ... | Pendiente / Resuelta YYYY-MM-DD: ... |
````

## Tamaño

El body admite 65.536 caracteres. Si el SDD lo supera, dejar en el body 1–6 y 13–15, y publicar 7–12 como comentarios que empiecen con `<!-- timonel:sdd:seccion=N -->` (uno por seccion), agregando en el body un indice `## Secciones en comentarios` con links.

## Versionado

Cada cambio relevante agrega una linea al `**Historial:**` (`- 2026-07-21 v1.2: resuelta DA-1, agrega RF-009`) y actualiza `**Versión:**`. No se crean issues nuevos por version.
