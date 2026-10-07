---
name: implement-backend-story
description: Implementa el backend NestJS de una historia de usuario a partir del body de un issue de GitHub (Timonel). Lee la ficha tecnica y el contrato API, explora solo el modulo afectado y produce esquema, servicio, dominio, aplicacion, controller y tests siguiendo las convenciones del consumidor.
---

Recibes del orquestador el body del issue (historia + ficha tecnica), el contrato API aprobado, la lista de modelos compartidos ya commiteados y los valores de `CONFIG` (`api.path`, `api.project`, `modelos.alias`, `modelos.path`). Si falta alguno, detente y pidelo. Siempre en espanol.

## Pasos

0. **Sincroniza tu worktree con la rama de la historia, solo si el orquestador te la indico**: naces de `origin/main`, nunca de esa rama (#122). El orquestador te pasa `RAMA_HISTORIA` en el prompt cuando ya la pusheo; que no te la pase no es un error, es una respuesta valida por su cuenta — no la trates como "la rama no existe". Cuatro casos, nunca dos:
   - **Te indico `RAMA_HISTORIA` y existe en el remoto, pero `origin/<RAMA_HISTORIA>` esta atrasada respecto de la rama local**: medilo antes de creerle al merge — `git fetch origin && git rev-list --left-right --count <RAMA_HISTORIA>...origin/<RAMA_HISTORIA>`; tu worktree comparte refs y objetos con el arbol principal, asi que la ref local es visible desde aca. Si el primer numero es > 0, la rama local tiene commits que el remoto no vio (nadie pusheo tras consolidar): **detente y reportalo en tu output, no sigas al paso 1**. Un `git merge --no-edit origin/<RAMA_HISTORIA>` en ese estado responde `Already up to date`, la misma cadena exacta que devuelve el no-op legitimo — no podes distinguir "no habia nada que traer" de "el remoto que consulte esta viejo", y eso es un **"no se"**, no un "no" (heuristica de `heuristics/general/*.md`: `sensor-declara-su-evidencia.md`). No implementes sobre codigo viejo.
   - **Te indico `RAMA_HISTORIA` y existe en el remoto**: `git fetch origin && git merge --no-edit origin/<RAMA_HISTORIA>` antes de leer nada (para una historia normal: `git merge --no-edit origin/hu/N-slug`). Sin este paso no vas a ver los modelos compartidos que el orquestador ya commiteo y pusheo en la Fase 2.
   - **Te indico `RAMA_HISTORIA` y no existe en el remoto, o el merge trae conflictos**: detente y reportalo en tu output; no sigas al paso 1.
   - **No te indico ninguna `RAMA_HISTORIA`**: no hay nada que sincronizar — tu worktree ya equivale a la base. Segui normalmente al paso 1 (es el camino normal de un hotfix nuevo de `flechodiezx-hotfix`, cuya rama `fix/N-<slug>` no se pushea salvo en reanudacion).

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
