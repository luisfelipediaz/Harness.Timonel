# Convenciones de código Bitákora (Angular + NestJS) — catálogo

Reglas que `code-review` verifica cuando el `CLAUDE.md` del consumidor no las redefine. **El `CLAUDE.md` y `.claude/rules/` del consumidor mandan**: si contradicen algo de aquí, gana el consumidor. Movidas desde el skill `code-review` (issue #21) para que el skill no acumule reglas de un proyecto concreto.

| Regla | Qué buscar | Severidad |
| --- | --- | --- |
| No `any` | `: any`, `as any` en archivos nuevos/modificados | WARNING |
| No `!` postfix | Non-null assertions en TS | WARNING |
| kebab-case | Nombres de archivos y carpetas nuevos | WARNING |
| Nuevo control flow Angular | `@if`/`@for`/`@switch`; nunca `*ngIf`/`*ngFor`/`*ngSwitch` | WARNING |
| No negar async pipes ni signals | `!(obs \| async)`, `=== false` con async, `!signal()` en templates | WARNING |
| Standalone | Componentes nuevos standalone | WARNING |
| Capas backend | Controllers solo delegan a Aplicación; sin lógica | WARNING |
| Imports limpios | Sin imports sin usar | WARNING |
| Líneas cortas | Prettier `printWidth` 80 | WARNING |
| Sin prefijo `I` | `FooResponse`, no `IFooResponse` | WARNING |
| `Sesion` propagada | controller → aplicación → servicio | WARNING (CRITICO si rompe un Gherkin) |
| `AuthorizationGuard<TiposDePermisos>` | En todos los endpoints, con el permiso de la ficha | WARNING (CRITICO si rompe un Gherkin) |
| `@AuditoriaApi` | En cada método del controller | WARNING |
| Modelos compartidos | Importados desde `modelos.alias`, no redeclarados | WARNING |
| Estilos | Clases utilitarias `@sinco/angular` antes que CSS propio; ≤3 propiedades inline; `.scss` solo si más | WARNING |
| Sin logs | No `console.log` ni loggers nuevos salvo pedido explícito | WARNING |
