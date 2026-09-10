---
name: investigar
description: Proceso de investigacion acotada en un monorepo Nx Angular + NestJS antes de implementar una historia — que buscar en el codebase (modulo afectado, modulo analogo, modelos compartidos, registro de providers/rutas, permisos, tests de referencia), que buscar en docs externas y como sintetizar en un reporte accionable con fuentes. Lo usa dora-exploradora; util tambien cuando el usuario pregunta "como esta hecho X en este repo".
---

# Investigar — proceso acotado

Objetivo: entregar en poco tiempo el **mapa minimo** para implementar sin inventar: donde va cada cosa, que patron copiar, que ya existe y que riesgos hay. Sin fuente (`ruta:linea` o URL) no hay hallazgo.

## 1. Orientacion (2 minutos)

- `.claude/timonel.config.json`: `api.path`, `frontends[].path/routesFile`, `modelos.path/alias`, `api.moduleFile`, `stack.estado`.
- `CLAUDE.md` del consumidor y su skill `*-estructura` si existe: capas, convenciones, guards, interceptores.
- Trabajo previo: `retro_query.py --modulo`, HUs cerradas del `mod:` y sus comentarios `timonel:investigacion`.

## 2. Que buscar en el codebase

Usa Glob/Grep con patrones, no lecturas completas. Acota al modulo afectado y a **un** modulo analogo (el mas parecido por tipo de operacion: CRUD simple, workflow de solicitud, consulta, integracion).

| Que | Donde / como | Para que |
| --- | --- | --- |
| Estructura del modulo | `<api.path>/src/app/<modulo>/**`, `<app.path>/src/app/<modulo>/**` | Carpetas por capa, naming |
| Modulo analogo | mismo tipo de operacion; `grep -rl "SolicitudesBaseAplicacion" <api.path>` para workflows | Patron a replicar |
| Modelos compartidos | `<modelos.path>/src/**`, barrel `index.ts` | Reutilizar interfaces, no duplicar |
| Registro backend | `<api.moduleFile>` (providers/imports), decoradores `@AuditoriaApi`, `AuthorizationGuard` | Puntos de registro y permisos |
| Registro frontend | `<routesFile>`, `*.routes.ts` (providers del store), guards `data.permisos` | Rutas lazy, permisos |
| Estado | `state/`, `signalStore(`, `withMethods`, `rxMethod`, facades | Patron de store vigente |
| Servicios HTTP | `*.service.ts`, `*.urls.ts`, interceptores | Convenciones de URL y errores |
| Esquemas | `esquemas/*.esquema.ts`, discriminadores, indices | Persistencia |
| Tests de referencia | `*.facade.spec.ts`, `*.aplicacion.spec.ts`, `*.servicio.spec.ts` | Patron de tests a copiar |
| Permisos | `TiposDePermisos`, `permisosAplicacion` | Nombre exacto del permiso |
| Estilos | clases `@sinco/angular`, `styleUrl` en componentes analogos | Regla ≤3 propiedades inline |

Si el config declara varias apps frontend, verifica en cual vive el modulo analogo y dilo.

## 3. Que buscar en documentacion externa

Solo cuando el codigo no lo muestra. Prioriza docs oficiales y cita la URL exacta:

- Angular (`angular.dev`): signals, control flow, `takeUntilDestroyed`, formularios tipados.
- NgRx Signals (`ngrx.io/guide/signals`): `signalStore`, `rxMethod`, `patchState`.
- NestJS (`docs.nestjs.com`): guards, pipes, `class-validator`, modulos.
- Mongoose: discriminadores, indices parciales, `findOneAndUpdate` upsert.
- Capacitor (`capacitorjs.com/docs`): plugins nativos si la HU toca movil.
- Microsoft Learn via MCP (`microsoft_docs_search`) si hay Azure/.NET involucrado.
- NuGet/npm: version, compatibilidad y licencia antes de proponer una dependencia nueva.

## 4. Como sintetizar

Formato del reporte: el de `dora-exploradora` (Archivos de referencia, Patrón a replicar, Contrato existente, Dependencias y puntos de registro, Documentación externa, Riesgos). Reglas:

- Maximo ~60 lineas; un hallazgo por linea con su fuente.
- Distingue **hecho** (lo vi en el codigo) de **recomendacion** (lo propongo).
- Si dos patrones conviven en el repo (ej. NgRx clasico y Signal Store), dilo y recomienda el que manda `CLAUDE.md`/`stack.estado`.
- Termina con las decisiones que **no** debe tomar Flecho solo (van al contrato API o al usuario).
