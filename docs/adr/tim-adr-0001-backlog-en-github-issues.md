# TIM-ADR-0001: Backlog, SDD y artefactos del ciclo en GitHub Issues

**Fecha**: 2026-09-09
**Estado**: Aceptado

## Contexto

El harness original persistía todo en markdown dentro del repo: `docs/user-stories/BACKLOG.md` como índice, un archivo por HU, `completadas.md` por épica, `.retro.md` y `.review.md` junto a la spec, y los SDD en `docs/especificaciones/`. Eso obligaba a mantener a mano el índice, generaba conflictos de merge en `BACKLOG.md`, mezclaba estado de gestión con código en los PR y no daba visibilidad de progreso ni dependencias fuera del editor.

## Decisión

1. **El issue es la HU.** El número del issue es el identificador; se abandona `HU-XXX`. Título `[verbo infinitivo] [qué cosa]`. Las HU migradas conservan `Id histórico: HU-XXX` en el body.
2. **Jerarquía con sub-issues nativos**: `tipo:sdd` → `tipo:epica` → `tipo:hu`. Se crea con la mutación GraphQL `addSubIssue`. GitHub calcula el progreso del padre.
3. **Labels facetados** en lugar de campos en el body: `tipo:`, `estado:`, `alcance:`, `moscow:`, `sp:`, `prioridad:`, `mod:`, `review:`, `retro:` y especiales (`bloqueado`, `bug`, `duplicada`, `obsoleta`, `insights`). Un script idempotente los provisiona.
4. **Artefactos del ciclo como comentarios con marcador** (`<!-- timonel:review -->`, `<!-- timonel:retro -->`, `<!-- timonel:dod -->`, `<!-- timonel:contrato-api -->`, `<!-- timonel:consolidacion -->`, `<!-- timonel:refinamiento -->`), con un bloque YAML plano parseable. Un marcador por tipo por issue: si la fase se repite, se edita el comentario.
5. **Cierre = done.** El DoD `DONE` cierra el issue con `completed`; obsoletas y duplicadas se cierran con `not_planned`.
6. **Sin GitHub Projects.** El token habitual no trae scope `project` y el tamaño del equipo no justifica el tablero. Queda como extensión opt-in.
7. **El repo de issues es configurable** (`github.repo`) y puede no ser el remote del código: los consumidores actuales viven en Azure DevOps.

## Consecuencias

- Los scripts de `retro-tools` leen de `gh` y no del filesystem.
- Las HU dejan de viajar en los PR del código; la trazabilidad se hace con `#N` en commits y ramas `hu/N-slug`.
- Cada consumidor necesita `gh` autenticado con scope `repo` y un repo GitHub para issues.
- El límite de 65.536 caracteres por body obliga a partir SDD grandes en comentarios indexados.
