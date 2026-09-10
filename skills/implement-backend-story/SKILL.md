---
name: implement-backend-story
description: Implementa el backend NestJS de una historia de usuario a partir del body de un issue de GitHub (Timonel). Lee la ficha tecnica y el contrato API, explora solo el modulo afectado y produce esquema, servicio, dominio, aplicacion, controller y tests siguiendo las convenciones del consumidor.
---

Recibes del orquestador el body del issue (historia + ficha tecnica), el contrato API aprobado, la lista de modelos compartidos ya commiteados y los valores de `CONFIG` (`api.path`, `api.project`, `modelos.alias`, `modelos.path`). Si falta alguno, detente y pidelo. Siempre en espanol.

## Pasos

1. **Leer la spec**: entidad, operaciones, reglas de negocio, permiso, endpoints (de la ficha y del contrato). Lee tambien `CLAUDE.md` del consumidor: sus convenciones mandan sobre las de este skill si difieren.

2. **Explorar contexto (acotado)**: solo `<api.path>/src/app/<modulo>/` y los modelos relacionados en `<modelos.path>`. Busca el modulo mas parecido como referencia. No recorras todo el codebase.

   **¿Extender `SolicitudesBaseAplicacion<T>` o aplicacion propia?** Extender cuando hay workflow de solicitud (crear → aprobar/rechazar → cancelar → ejecutar): vacaciones, ausencias, permisos, prestamos. No extender para CRUD simple o features sin aprobacion.

   **¿Discriminador de Mongoose o coleccion nueva?** Discriminador cuando la entidad es un tipo de `Solicitud`; coleccion nueva cuando tiene esquema independiente.

3. **Implementar en orden**: Esquema → Servicio (acceso a datos) → Dominio (validaciones) → Aplicacion (orquestacion) → Controller (`@AuditoriaApi`) → Module (providers/exports) → Tests.

4. **Tests unitarios (obligatorio)**: un `.spec.ts` por aplicacion y servicio creados. Aplicacion: mocks con `jest.fn()`, happy path + error por metodo publico. Servicio: `MongooseModule.forRoot()` con BD real (copia el patron de un `*.servicio.spec.ts` existente). **No ejecutes `nx test`**: el orquestador lo hace tras el merge.

5. **Reglas**: `Sesion` en todas las capas; `AuthorizationGuard<TiposDePermisos>` en todos los endpoints; `@AuditoriaApi` en cada metodo del controller; excepciones tipadas (`@sinco/excepciones`) desde dominio; `class-validator` en DTOs; integraciones externas con `*Development` + `useClass` condicional; importar modelos desde `<modelos.alias>`, nunca redeclararlos; sin `any`, sin `!` postfix, sin prefijo `I`.

6. **Verificacion fail-fast**: `nx lint <api.project>`. Maximo 2 intentos de correccion. Si persiste, **detente** y reporta el error exacto. No entres en loops.

7. **Commit**: `git add` de tus archivos y `git commit -m "feat(<modulo>): backend #<issue> — <detalle>"`.

## Regla de alcance

No modifiques archivos fuera de tu tarea: solo los que la historia, el contrato y la investigacion (`timonel:investigacion`) indican. Si necesitas tocar algo mas (un modelo compartido, el modulo raiz, una ruta, una lib ajena), **no lo hagas**: documentalo en el output como pendiente para el orquestador. Si el plan es ambiguo, pregunta antes de asumir.

## Output (obligatorio)

- Issue implementado (`#N titulo`)
- Archivos creados/modificados con rutas (incluidos `.spec.ts`)
- Providers/imports a registrar en `api.moduleFile` (no lo edites tu)
- Notas de migracion (BD, env vars)
- Branch/worktree en el que quedaron los commits
- Si lint fallo: error exacto y lo intentado
