---
description: "Migra un backlog en markdown (docs/user-stories del harness original) a GitHub Issues: epicas, HUs como sub-issues, cierres, retros y reviews como comentarios."
argument-hint: "[ruta docs/user-stories] [--apply]"
model: sonnet
---

Migra el backlog documental al repo de issues. Comunicate en **espanol**. **Dry-run por defecto**; solo `--apply` crea issues.

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ 2>/dev/null | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
DOCS=$(echo "$ARGUMENTS" | grep -oE '^[^ -][^ ]*' || echo docs/user-stories)
[ -f "$DOCS/BACKLOG.md" ] || { echo "ERROR: no existe $DOCS/BACKLOG.md"; exit 1; }
```

## 1. Dry-run siempre primero

```bash
python3 "$PLUGIN_ROOT/scripts/migrate_backlog.py" --docs "$DOCS"
```

Resume: epicas, HUs (abiertas / cerradas / obsoletas), `AVISO` de specs no encontradas (se crean con body minimo). Verifica que los labels existan (`"$PLUGIN_ROOT/scripts/setup-github-labels.sh"`).

## 2. Aplicar (solo si `$ARGUMENTS` contiene `--apply`)

Muestra el plan y pide confirmacion explicita: "Se crearan N epicas y M issues en <repo>. ¿Continuo?". Con "si":

```bash
python3 "$PLUGIN_ROOT/scripts/migrate_backlog.py" --docs "$DOCS" --apply
```

Es idempotente (busca `Id histórico: HU-XXX`); si se interrumpe, se puede relanzar.

## 3. Despues

Sugiere: revisar las HUs con body minimo, correr `/timonel:insights`, y mover `docs/user-stories/` a `docs/archivo/user-stories/` (o borrarlo) en un commit separado una vez validado. No lo hagas tu.

## Reglas

- Nunca `--apply` sin confirmacion explicita del usuario en esta sesion.
- No edites los markdown de origen.
