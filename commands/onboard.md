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
- `git`: `{ "baseBranches": [<rama por defecto de `gh repo view` o `main`, mas `develop` si existe>], "protectBase": true, "integracion": "pr" }`. `protectBase` va fijo en `true`: desde v0.6.0 el hook de commits bloquea siempre la rama base y el flag esta deprecado e ignorado (TIM-ADR-0002); no preguntes por el. `integracion` tambien va fijo, sin preguntar: `"pr"` es el unico valor valido desde v0.6.0 (`"merge"` deprecado e ignorado).
- Detecta el tipo de remote con `python3 "$PLUGIN_ROOT/scripts/integracion.py" --tipo-remote`; si es `azure-devops` y falta `az`, avisa que la Fase 6.5 mostrará el comando en vez de ejecutarlo.
- `timonel`: `{ "repo": "luisfelipediaz/Harness.Timonel" }`.

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

## 2.5. Proteccion de rama (GitHub)

Solo si `github.repo` resuelve a un remote de GitHub y `gh` esta autenticado. Con Azure DevOps u otro remote, salta este paso (no hay receta equivalente todavia).

Muestra el comando exacto, con los **cuatro** campos top-level que la API exige (los cuatro aceptan `null`, pero omitir uno da 422):

```bash
gh api -X PUT "repos/${github_repo}/branches/${base}/protection" --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null
}
EOF
```

Explica en una linea que `required_approving_review_count: 0` exige PR pero permite que el propio dueno del repo mergee sus PRs trabajando solo, y ofrece subir a `1` si el repo es de varias personas.

Pregunta "¿Activo la proteccion de rama en `${base}`?". Solo con un "si" explicito lo corres.

- "no" → deja el comando impreso en el resumen (paso 4) para correrlo despues. No falla el onboarding.
- `gh api` devuelve **403** → el usuario no tiene permiso de admin sobre el repo. Muestra un mensaje claro (falta permiso de admin; pedile a quien lo tenga que corra el comando) y deja el comando en el resumen. No falla el onboarding.
- Aplica sin error → **no confies solo en el exit code**: releé con `gh api "repos/${github_repo}/branches/${base}/protection"` y confirma en el resumen que `enforce_admins.enabled` es `true` y que `required_pull_request_reviews` quedo escrito.

## 2.6. Convencion de integracion en `CLAUDE.md` del consumidor

Si el repo tiene `CLAUDE.md` y no contiene ya la convencion de integracion, muestra el diff de agregar esta linea a su seccion de convenciones (crea la seccion si no existe) y pregunta "¿Agrego esta linea a `CLAUDE.md`?":

```
Todo cambio entra por PR; la rama base no recibe commits directos.
```

Solo con un "si" explicito la escribis. Si `CLAUDE.md` no existe, no lo crees: crearlo entero excede el alcance de este comando.

## 3. Labels

```bash
"$PLUGIN_ROOT/scripts/setup-github-labels.sh"
```

Si `gh` no esta autenticado, indica el comando para correrlo despues. Pregunta si el repo de issues es nuevo y dedicado al backlog: en ese caso ofrece `--prune-defaults`.

## 4. Resumen

Reporta: ruta del config, repo de issues, apps detectadas, modulos, labels creados/actualizados, si la proteccion de rama quedo activada/pendiente (con el comando `gh api .../protection` completo si quedo pendiente, paso 2.5), si la linea de convencion se agrego a `CLAUDE.md` (paso 2.6), y los siguientes pasos: `/timonel:migrate` si hay `docs/user-stories/`, `/timonel:sdd` o `/timonel:plan` para empezar.

## Reglas

- No modifiques codigo del proyecto; solo `.claude/timonel.config.json`, `.claude/settings.json`, `.gitignore` y, previo diff y confirmacion explicita, la linea de convencion de integracion en `CLAUDE.md` (paso 2.6) — ninguna otra edicion de `CLAUDE.md`.
- No adivines `github.repo` cuando el remote no es GitHub.
- Nunca ejecutes `gh api .../protection` sin un "si" explicito del usuario en esta sesion.
