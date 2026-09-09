# TIM-ADR-0004: Extracción del harness como plugin de Claude Code

**Fecha**: 2026-09-09
**Estado**: Aceptado

## Contexto

El harness nació en `Bitakora.MonoRepo.Portal/.claude/` y se copió a `Bitakora.POC.Organigrama/.claude/`. Ya existía en la organización un precedente de harness empaquetado como plugin con marketplace propio (Mefisto, `augusto-romero-arango/eda-evsourcing-azure-harness`), cuya estructura y convenciones de instalación funcionan.

## Decisión

1. Repo propio `luisfelipediaz/Harness.Timonel` con `.claude-plugin/plugin.json` y `.claude-plugin/marketplace.json` (`source: "./"`), siguiendo el layout de Mefisto: `agents/`, `commands/`, `skills/`, `scripts/`, `hooks/`, `docs/adr/`.
2. Nombre `timonel`: quien gobierna el rumbo siguiendo la bitácora. Comandos bajo el namespace `/timonel:*`.
3. Los agentes resuelven la raíz del plugin con `.timonel/.plugin-root` (escrito por el hook `SessionStart`) y fallback por glob en `~/.claude/plugins/cache/*/timonel/*/`, porque las heurísticas y plantillas viven dentro del plugin y no en el consumidor.
4. Las heurísticas de código del autor (`~/.claude/heuristics`) se copian dentro del plugin como default para que el `code-review` funcione en cualquier máquina.
5. Versionado semver desde `0.1.0`; `CHANGELOG.md` por versión.
6. El repo se publica **privado**: incluye convenciones internas (`@sinco/*`, guards, auditoría).
7. En los consumidores se borran `.claude/agents` y `.claude/skills`; queda `.claude/timonel.config.json` y la habilitación en `.claude/settings.json`.

## Consecuencias

- Una sola fuente para Portal y POC; los fixes se propagan con `claude plugin update`.
- El plugin depende de `gh` (>= 2.60, sub-issues) y `jq` en la máquina del usuario.
- Los archivos `agente-actualizacion-*.md` del Portal no son parte del harness y no se mueven.
