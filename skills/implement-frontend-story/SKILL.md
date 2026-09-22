---
name: implement-frontend-story
description: Implementa el frontend Angular de una historia de usuario a partir del body de un issue de GitHub (Timonel). Lee criterios, ficha tecnica y contrato API, explora solo el modulo afectado de la app destino y produce componentes standalone, servicio, store (NgRx Signal Store) y tests siguiendo las convenciones del consumidor.
---

Recibes del orquestador el body del issue, el contrato API a consumir, la lista de modelos compartidos ya commiteados, si el backend esta desplegado o no, y los valores de `CONFIG` (`app.project`, `app.path`, `app.routesFile`, `modelos.alias`, `stack.estado`). Si falta alguno, detente y pidelo. Siempre en espanol.

## Pasos

0. **Sincroniza tu worktree con la rama de la historia, solo si el orquestador te la indico**: naces de `origin/main`, nunca de esa rama (#122). El orquestador te pasa `RAMA_HISTORIA` en el prompt cuando ya la pusheo; que no te la pase no es un error, es una respuesta valida por su cuenta — no la trates como "la rama no existe". Cuatro casos, nunca dos:
   - **Te indico `RAMA_HISTORIA` y existe en el remoto, pero `origin/<RAMA_HISTORIA>` esta atrasada respecto de la rama local**: medilo antes de creerle al merge — `git fetch origin && git rev-list --left-right --count <RAMA_HISTORIA>...origin/<RAMA_HISTORIA>`; tu worktree comparte refs y objetos con el arbol principal, asi que la ref local es visible desde aca. Si el primer numero es > 0, la rama local tiene commits que el remoto no vio (nadie pusheo tras consolidar): **detente y reportalo en tu output, no sigas al paso 1**. Un `git merge --no-edit origin/<RAMA_HISTORIA>` en ese estado responde `Already up to date`, la misma cadena exacta que devuelve el no-op legitimo — no podes distinguir "no habia nada que traer" de "el remoto que consulte esta viejo", y eso es un **"no se"**, no un "no" (heuristica de `heuristics/general/*.md`: `sensor-declara-su-evidencia.md`). No implementes sobre codigo viejo.
   - **Te indico `RAMA_HISTORIA` y existe en el remoto**: `git fetch origin && git merge --no-edit origin/<RAMA_HISTORIA>` antes de leer nada (para una historia normal: `git merge --no-edit origin/hu/N-slug`). Sin este paso no vas a ver los modelos compartidos que el orquestador ya commiteo y pusheo en la Fase 2.
   - **Te indico `RAMA_HISTORIA` y no existe en el remoto, o el merge trae conflictos**: detente y reportalo en tu output; no sigas al paso 1.
   - **No te indico ninguna `RAMA_HISTORIA`**: no hay nada que sincronizar — tu worktree ya equivale a la base. Segui normalmente al paso 1 (es el camino normal de un hotfix nuevo de `flechodiezx-hotfix`, cuya rama `fix/N-<slug>` no se pushea salvo en reanudacion).

1. **Leer la spec**: criterios de aceptacion, UI, reglas, endpoints, necesidades de estado. Lee `CLAUDE.md` del consumidor: sus convenciones mandan.

2. **Explorar contexto (acotado)**: solo `<app.path>/src/app/<modulo>/`. Busca el componente o feature mas parecido y sigue sus patrones. No recorras todo el codebase.

3. **Implementar**:
   - Templates con `@if`, `@for`, `@switch` — nunca `*ngIf`/`*ngFor`/`*ngSwitch`. Nunca negar async pipes ni signals con `!`.
   - Componentes standalone; `@Input()`/`@Output()` o `input()`/`output()` tipados.
   - Observables: `async` pipe o `takeUntilDestroyed()`; sin arrays de `Subscription`.
   - Reactive forms tipados con `FormBuilder`.
   - Modelos desde `<modelos.alias>`; no redeclarar.
   - Backend no desplegado → servicio con `of()` del mismo tipo y `// TODO: Reemplazar con HTTP call real`.
   - Estado → skill `ngrx-signal-store` (`PLUGIN_ROOT/skills/ngrx-signal-store/SKILL.md`) salvo que `stack.estado` o `CLAUDE.md` indiquen otro patron (ej. NgRx clasico con facade).
   - **Estilos**: `references/ANGULAR-ESTILOS.md` de este skill. Clases utilitarias de `@sinco/angular` (`p-*`, `m-*`, `gap-*`, `row`, `column`, `col-s-12`, `color-text-primary`, `mat-body-1`…) antes que CSS propio; ≤3 propiedades custom → `style=""` inline; mas → `.scss` con `styleUrl`; mixins solo cuando las utilidades no alcanzan. Si el consumidor no usa `@sinco/*` (lo dice su `CLAUDE.md`), sigue su design system.

4. **Tests unitarios (obligatorio)**:
   - **Store** (`<modulo>.facade.spec.ts`): store real + servicio real + `HttpTestingController`; 1 test por action, 1 por selector, 1 happy path por effect. Helpers de `@sinco/utilidades-test-bitakora` si existen.
   - **Componentes** (opcional, bajo ROI): store real con `patchState`; solo verifican reaccion al estado.
   - Ejemplos completos en `ngrx-signal-store/references/ejemplo-completo.md`.
   - **No ejecutes `nx test`**.

5. **Verificacion fail-fast**: `nx lint <app.project>` (+ libs que hayas tocado). Maximo 2 intentos. Si persiste, detente y reporta el error exacto.

6. **Commit**: `git commit -m "feat(<modulo>): frontend #<issue> — <detalle>"`.

## Regla de alcance

No modifiques archivos fuera de tu tarea: solo los que la historia, el contrato y la investigacion (`timonel:investigacion`) indican. Si necesitas tocar algo mas (un modelo compartido, el modulo raiz, una ruta, una lib ajena), **no lo hagas**: documentalo en el output como pendiente para el orquestador. Si el plan es ambiguo, pregunta antes de asumir.

## Output (obligatorio)

- Archivos creados/modificados (incluidos `.spec.ts`)
- Rutas a registrar en `app.routesFile` (no lo edites tu), providers o imports
- Dependencias de API pendientes (mocks a reemplazar)
- Branch/worktree con los commits
- Si lint fallo: error exacto y lo intentado
