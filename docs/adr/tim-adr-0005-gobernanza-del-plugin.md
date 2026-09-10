# TIM-ADR-0005: Gobernanza del plugin — todo cambio nace en un issue

**Fecha**: 2026-09-10
**Estado**: Aceptado

## Contexto

Timonel exige a sus consumidores que el backlog viva en GitHub Issues (TIM-ADR-0001), pero sus primeras dos versiones se construyeron sin registrar las decisiones en su propio repo. Un harness que no se aplica a si mismo pierde la propiedad "contexto acumulado": la razon de cada cambio queda en la cabeza de quien lo hizo o en un CHANGELOG sin discusion.

## Decisión

1. **Todo cambio del plugin se documenta primero en un issue de `luisfelipediaz/Harness.Timonel`** con el mismo esquema de labels del consumidor (`tipo:hu|hotfix|epica|sdd`, `mod:plugin`, `estado:*`, `sp:*`). Las versiones se agrupan en una epica `Timonel X.Y.0`.
2. **Todo commit referencia el issue** (`#N`). Lo exige el hook `.githooks/commit-msg`, activado con `scripts/install-git-hooks.sh` (`core.hooksPath`). Excepciones: merges, reverts, fixups.
3. **El plugin, cuando corre dentro de su propio repo, bloquea `git commit` sin `#N`** via hook `PreToolUse` de `hooks/hooks.json` (defensa en profundidad para sesiones de Claude Code).
4. **Cerrar el issue = entregar**: el commit o la release que lo resuelve comenta el issue y lo cierra; el CHANGELOG cita los `#N`.
5. Los comandos de Timonel (`/timonel:draft`, `/timonel:plan`, `/timonel:refine`, `/timonel:backlog`) funcionan dentro del repo del plugin usando `gh repo view` como `github.repo` cuando no hay `timonel.config.json`.

## Control de cambios

- 2026-09-10 (#27): el plugin se desarrolla con su propio flujo (perfil `plugin` de `flechodiezx`). `main` queda protegida tambien en el plugin: el trabajo va en ramas `hu/N-*` y se integra con `git merge --no-ff`; la release se etiqueta al cerrar la epica.

## Consecuencias

- Un clon nuevo debe correr `scripts/install-git-hooks.sh` una vez (documentado en README y CLAUDE.md).
- Los `harness-audit` del plugin pueden comparar issues cerrados por version.
- Un cambio trivial (typo) tambien requiere issue: se acepta el costo a cambio de la trazabilidad; `/timonel:draft` lo hace en un comando.
