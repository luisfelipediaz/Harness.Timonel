# timonel

> Repositorio: `luisfelipediaz/Harness.Timonel` · Plugin de Claude Code: `timonel` · Marketplace: `luisfelipediaz-harness`

Harness opinionado de [Claude Code](https://code.claude.com/docs/en/plugins) para monorepos **Nx + Angular + NestJS**. Planifica SDD, épicas e historias de usuario **como GitHub Issues**, las implementa con sub-agentes en worktrees paralelos, y publica contrato API, code review, retrospectiva y Definition of Done en el mismo issue.

## El nombre

El timonel gobierna el rumbo siguiendo la bitácora. Aquí la bitácora es el backlog en GitHub; Timonel es quien lo lleva desde la idea hasta el issue cerrado.

## Qué incluye

- **Comandos** `/timonel:*`: `onboard`, `sdd`, `plan`, `refine`, `draft`, `investigar`, `implement`, `hotfix`, `backlog`, `insights`, `audit`, `migrate`.
- **Agentes**: `sdd-planner`, `user-story-planner`, `backlog-refiner`, `dora-exploradora` (investiga), `flechodiezx` (ejecuta historias), `flechodiezx-hotfix`, `harness-auditor`.
- **Skills**: `github-issues` (plantillas + recetas `gh`), `implement-backend-story`, `implement-frontend-story`, `consolidate-story`, `code-review`, `generate-retro`, `verify-dod`, `retro-tools`, `ngrx-signal-store`, `interrogame`, `investigar`.
- **Scripts** (stdlib + `gh`): labels idempotentes, query/destilado de retros y reviews, migración de backlog markdown.
- **Heurísticas** de código (`evitar-ifs`, `no-tipos-espejo`, `usar-pipes-existentes`) usadas por el code review.
- **ADRs** `TIM-ADR-0001..0004` en `docs/adr/`.

## Stack supuesto en el consumidor

Nx · Angular 20+ (standalone, signals) · NestJS 10+ con Mongoose · NgRx Signal Store (u otro store declarado en config) · `gh` ≥ 2.60 y `jq` instalados · un repo de GitHub para los issues (puede ser distinto del remote del código).

## Instalación

### 1. `.claude/settings.json` del repo consumidor

```json
{
  "extraKnownMarketplaces": {
    "luisfelipediaz-harness": {
      "source": { "source": "github", "repo": "luisfelipediaz/Harness.Timonel" }
    }
  },
  "enabledPlugins": { "timonel@luisfelipediaz-harness": true },
  "permissions": {
    "allow": ["Bash(gh:*)", "Bash(git:*)", "Bash(nx:*)", "Bash(npx nx:*)", "Bash(python3:*)"]
  }
}
```

### 2. Instalar desde Claude Code

```
/plugin marketplace add luisfelipediaz/Harness.Timonel
/plugin install timonel@luisfelipediaz-harness
```

Instala con scope `user` si vas a usar `flechodiezx` (los worktrees hermanos no cargan plugins de scope `project`).

### 3. Configurar el consumidor

```
/timonel:onboard [owner/repo-de-issues]
```

Genera `.claude/timonel.config.json` inspeccionando `nx.json`, `tsconfig.base.json` y `apps/*/project.json`, y provisiona los labels en el repo de issues:

```json
{
  "projectName": "Bitakora.MonoRepo.Portal",
  "github": { "repo": "owner/repo" },
  "stack": { "frontend": "Angular 21", "backend": "NestJS 10", "estado": "NgRx Signal Store" },
  "api": { "project": "api", "path": "apps/api", "moduleFile": "apps/api/src/app/app.module.ts" },
  "frontends": [{ "project": "client", "path": "apps/client", "routesFile": "apps/client/src/app/app-routing.module.ts" }],
  "modelos": { "alias": "@bitakora.monorepo.portal/modelos", "path": "libs/modelos" },
  "modulos": ["mis-finanzas", "vacaciones"],
  "heuristicsDir": null
}
```

## Flujo

```
/timonel:sdd "tema"        → issue tipo:sdd (diseño) ──┐
/timonel:plan #sdd          → épicas (sub-issues) → HUs (sub-issues, DoR)
/timonel:draft "idea"       → HU borrador rápido
/timonel:refine #epica      → dividir / repriorizar / deduplicar / completar
/timonel:investigar #hu     → Dora publica hallazgos (archivos de referencia, patrón, riesgos)
/timonel:implement #hu      → investigación → contrato API → backend ∥ frontend (worktrees) → consolidación → review → retro → DoD → close
/timonel:hotfix #n | "fix"  → un sub-agente, sin worktree, DoD reducido
/timonel:backlog            → estado por épica
/timonel:insights           → issues "Insights destilados" (retros / reviews)
/timonel:audit              → issue harness-audit (madurez del harness, gaps priorizados)
/timonel:migrate --apply    → importa docs/user-stories del harness original
```

Todo queda en el issue: labels facetados (`tipo:`, `estado:`, `alcance:`, `moscow:`, `sp:`, `prioridad:`, `mod:`, `review:`, `retro:`), checklist `## Tareas`, y comentarios con marcador (`<!-- timonel:contrato-api -->`, `consolidacion`, `review`, `retro`, `dod`, `refinamiento`). Ver `skills/github-issues/references/`.

## Desarrollo del plugin

```bash
scripts/install-git-hooks.sh                    # una vez por clon: commit-msg exige #issue
python3 -m unittest discover -s tests          # parsers, destilado, migración
scripts/setup-github-labels.sh --repo o/r --dry-run
```

**Todo cambio nace en un issue de este repo y el commit lo referencia** (TIM-ADR-0005). El propio repo usa sus labels, épicas por versión e issues como backlog; `/timonel:draft`, `/timonel:plan`, `/timonel:backlog` y `/timonel:audit plugin` funcionan aquí sin `timonel.config.json`.

## Licencia

Uso interno. Ver `LICENSE`.
