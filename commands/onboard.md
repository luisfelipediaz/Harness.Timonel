---
description: "Genera .claude/timonel.config.json inspeccionando el monorepo Nx, habilita el plugin en settings.json y provisiona los labels de GitHub."
argument-hint: "[owner/repo-de-issues]"
model: sonnet
---

Configura Timonel en el repo consumidor actual. Comunicate en **espanol**. Sigue el skill `github-issues` para todo lo que toque GitHub.

## 0. Pre-condiciones

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "ERROR: no estas en un repositorio git"; exit 1; }
[ -f "$REPO_ROOT/.claude-plugin/plugin.json" ] && { echo "ERROR: este es el repo de un plugin, no un consumidor."; exit 1; }
[ -f "$REPO_ROOT/nx.json" ] || echo "AVISO: no hay nx.json; Timonel asume monorepo Nx. Continuo, pero revisa las rutas."
command -v gh >/dev/null && gh auth status >/dev/null 2>&1 || echo "AVISO: gh no autenticado; los labels se crearan despues."
PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ 2>/dev/null | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
```

Si ya existe `.claude/timonel.config.json`, muestralo y pregunta si regenerar o solo provisionar labels.

## 1. Inspeccionar el repo

- `projectName`: `basename "$REPO_ROOT"`.
- `github.repo`: `$ARGUMENTS` si viene; si no, `gh repo view --json nameWithOwner -q .nameWithOwner` (solo si el remote es GitHub). Si el remote es Azure DevOps u otro, **pregunta** al usuario que repo de GitHub alojara los issues. No inventes.
- `api`: proyecto Nx cuyo `project.json` tiene `@nx/nest` o cuyo `package.json` depende de `@nestjs/core` — normalmente `apps/api`. `moduleFile` = `<path>/src/app/app.module.ts` si existe.
- `frontends[]`: cada `apps/*/project.json` con executor Angular (`@angular-devkit/build-angular` o `@angular/build`). `routesFile` = el primero que exista de `src/app/app.routes.ts`, `src/app/app-routing.module.ts`.
- `modelos`: entrada de `tsconfig.base.json.compilerOptions.paths` que apunte a `libs/modelos*`; `alias` = clave, `path` = carpeta.
- `stack`: versiones de `@angular/core` y `@nestjs/core` en `package.json`; `estado` = `NgRx Signal Store` si depende de `@ngrx/signals`, `NgRx Store` si `@ngrx/store`, si no `sin store`.
- `modulos[]`: carpetas de primer nivel en `<api.path>/src/app/` que tengan `controllers/` o `*.module.ts` (kebab-case). Muestra la lista y deja que el usuario quite/agregue.
- `heuristicsDir`: `null`.

## 2. Confirmar y escribir

Muestra el JSON completo y pregunta "¿Escribo `.claude/timonel.config.json` con esto?". Con "si", escribelo (2 espacios de indentacion).

Luego asegura en `.claude/settings.json` (crear si no existe, sin borrar claves ajenas):

```json
{
  "extraKnownMarketplaces": {
    "luisfelipediaz-harness": { "source": { "source": "github", "repo": "luisfelipediaz/Harness.Timonel" } }
  },
  "enabledPlugins": { "timonel@luisfelipediaz-harness": true }
}
```

Agrega `.timonel/` a `.gitignore` si no esta.

## 3. Labels

```bash
"$PLUGIN_ROOT/scripts/setup-github-labels.sh"
```

Si `gh` no esta autenticado, indica el comando para correrlo despues. Pregunta si el repo de issues es nuevo y dedicado al backlog: en ese caso ofrece `--prune-defaults`.

## 4. Resumen

Reporta: ruta del config, repo de issues, apps detectadas, modulos, labels creados/actualizados, y los siguientes pasos: `/timonel:migrate` si hay `docs/user-stories/`, `/timonel:sdd` o `/timonel:plan` para empezar.

## Reglas

- No modifiques codigo del proyecto; solo `.claude/timonel.config.json`, `.claude/settings.json` y `.gitignore`.
- No adivines `github.repo` cuando el remote no es GitHub.
