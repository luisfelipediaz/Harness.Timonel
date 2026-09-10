---
name: github-issues
description: Fuente unica de como Timonel representa el backlog en GitHub Issues — jerarquia SDD → epica → HU con sub-issues, labels facetados, plantillas de body, comentarios con marcador (contrato API, consolidacion, review, retro, DoD, refinamiento) y las recetas `gh` exactas para crearlos, editarlos y consultarlos. Usar siempre que un agente o skill de Timonel deba leer o escribir un issue, un sub-issue, un label o un comentario del ciclo de vida de una historia.
---

# GitHub Issues en Timonel

Todo el estado de planificacion y del ciclo de una historia vive en GitHub (TIM-ADR-0001). Este skill es la unica referencia de formato y de comandos. Los agentes **no** improvisan formatos: copian las plantillas de `references/` y usan las recetas de este archivo.

## Repo destino

Siempre lee el repo desde el config del consumidor y pasalo explicito a `gh`:

```bash
REPO=$(jq -r '.github.repo' .claude/timonel.config.json 2>/dev/null)
# Dentro del repo del plugin Timonel (TIM-ADR-0005) el backlog es el propio repo:
[ -n "$REPO" ] && [ "$REPO" != "null" ] || { [ -f .claude-plugin/plugin.json ] && REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner); }
[ -n "$REPO" ] && [ "$REPO" != "null" ] || { echo "ERROR: falta github.repo en .claude/timonel.config.json — ejecuta /timonel:onboard"; exit 1; }
```

Usa `gh <cmd> -R "$REPO"` en **todos** los comandos. El remote del codigo puede ser otro (Azure DevOps).

## Plantillas (`references/`)

| Archivo | Uso |
| --- | --- |
| `plantilla-hu.md` | Body de una historia de usuario (`tipo:hu`) |
| `plantilla-hotfix.md` | Body de un hotfix (`tipo:hotfix`) |
| `plantilla-epica.md` | Body de una epica (`tipo:epica`) |
| `plantilla-sdd.md` | Body de un SDD (`tipo:sdd`) |
| `marcadores.md` | Formato exacto de los comentarios con marcador (contrato API, consolidacion, review, retro, DoD, refinamiento) |
| `labels.md` | Esquema completo de labels con colores y significado |

Lee la plantilla que corresponda antes de crear o editar un issue. Las secciones `## ` son un contrato: los scripts y el DoR (TIM-ADR-0003) las buscan por prefijo.

## Recetas

### Crear un issue con body desde archivo

Escribe el body en un archivo temporal y usa `--body-file` (evita problemas de escapado con backticks y `$`):

```bash
BODY=$(mktemp)
cat > "$BODY" <<'MD'
...contenido segun plantilla...
MD
NUM=$(gh issue create -R "$REPO" --title "Registrar gasto con categoria" \
  --label "tipo:hu" --label "estado:borrador" --label "alcance:full-stack" \
  --label "moscow:must" --label "sp:5" --label "prioridad:alta" --label "mod:mis-finanzas" \
  --body-file "$BODY" --json number -q .number 2>/dev/null \
  || gh issue create -R "$REPO" --title "..." --label ... --body-file "$BODY" | grep -oE '[0-9]+$')
echo "Creado #$NUM"
```

Si `gh issue create --json` no esta disponible en tu version, la URL que imprime termina en el numero: usa el `grep` del fallback.

### Vincular como sub-issue (padre ← hijo)

```bash
# ids globales (node_id) del padre y del hijo
PARENT_ID=$(gh issue view "$PARENT" -R "$REPO" --json id -q .id)
CHILD_ID=$(gh issue view "$CHILD" -R "$REPO" --json id -q .id)
gh api graphql -f query='
  mutation($p:ID!,$c:ID!){ addSubIssue(input:{issueId:$p, subIssueId:$c}){ issue{ number } subIssue{ number } } }' \
  -f p="$PARENT_ID" -f c="$CHILD_ID" -q '.data.addSubIssue.subIssue.number'
```

Si el hijo ya tiene otro padre y debe moverse, agrega `replaceParent:true` al input.

### Listar hijos de un padre y consultar el padre de un issue

```bash
gh api graphql -f query='
  query($o:String!,$r:String!,$n:Int!){ repository(owner:$o,name:$r){ issue(number:$n){
    subIssues(first:100){ nodes{ number title state labels(first:20){ nodes{ name } } } } } } }' \
  -f o="${REPO%/*}" -f r="${REPO#*/}" -F n="$PARENT" \
  -q '.data.repository.issue.subIssues.nodes[] | "#\(.number) [\(.state)] \(.title) :: \([.labels.nodes[].name]|join(","))"'

gh api graphql -f query='
  query($o:String!,$r:String!,$n:Int!){ repository(owner:$o,name:$r){ issue(number:$n){ parent{ number title } } } }' \
  -f o="${REPO%/*}" -f r="${REPO#*/}" -F n="$CHILD" -q '.data.repository.issue.parent'
```

### Leer un issue completo (body + labels + comentarios)

```bash
gh issue view "$NUM" -R "$REPO" --json number,title,state,body,labels,assignees,comments \
  --jq '{number,title,state,labels:[.labels[].name],assignees:[.assignees[].login],body,comments:[.comments[]|{id,body,createdAt}]}'
```

### Cambiar estado (labels exclusivos)

Los ejes `estado:`, `review:` y `retro:` son exclusivos: quita el anterior antes de poner el nuevo.

```bash
cambiar_label_exclusivo() { # $1 issue, $2 prefijo (ej: estado), $3 valor nuevo
  local actuales; actuales=$(gh issue view "$1" -R "$REPO" --json labels -q '[.labels[].name | select(startswith("'"$2"':"))] | join(",")')
  [ -n "$actuales" ] && gh issue edit "$1" -R "$REPO" --remove-label "$actuales"
  gh issue edit "$1" -R "$REPO" --add-label "$2:$3"
}
cambiar_label_exclusivo "$NUM" estado en-progreso
```

### Marcar tareas del checklist `## Tareas`

Edita el body reemplazando la linea exacta:

```bash
BODY=$(gh issue view "$NUM" -R "$REPO" --json body -q .body)
NUEVO=$(printf '%s\n' "$BODY" | sed 's/^- \[ \] Backend$/- [x] Backend/')
gh issue edit "$NUM" -R "$REPO" --body "$NUEVO"
```

Nunca reescribas otras secciones del body al marcar tareas.

### Publicar o actualizar un comentario con marcador

Un marcador por tipo por issue. Busca primero; si existe, edita; si no, crea.

```bash
publicar_marcador() { # $1 issue, $2 marcador (ej: review), $3 archivo con el cuerpo (debe empezar con <!-- timonel:$2 -->)
  local cid
  cid=$(gh api "repos/$REPO/issues/$1/comments" --paginate \
        -q '[.[] | select(.body | startswith("<!-- timonel:'"$2"' -->"))] | last | .id // empty')
  if [ -n "$cid" ]; then
    gh api -X PATCH "repos/$REPO/issues/comments/$cid" -F body=@"$3" -q .id
  else
    gh api -X POST "repos/$REPO/issues/$1/comments" -F body=@"$3" -q .id
  fi
}
```

### Cerrar

```bash
gh issue close "$NUM" -R "$REPO" --reason completed   --comment "DoD: DONE. Ver comentario timonel:dod."
gh issue close "$NUM" -R "$REPO" --reason "not planned" --comment "Obsoleta: reemplazada por #123."
```

### Listar backlog

```bash
gh issue list -R "$REPO" --label tipo:hu --label estado:listo --state open --limit 200 \
  --json number,title,labels -q '.[] | "#\(.number) \(.title) :: \([.labels[].name | select(startswith("sp:") or startswith("moscow:") or startswith("mod:"))] | join(" "))"'
```

### Dependencias y bloqueo

En `## Dependencias` solo se aceptan lineas `Depende de #N` (una por linea) o `Ninguna`. Para saber si un issue esta bloqueado:

```bash
gh issue view "$NUM" -R "$REPO" --json body -q .body \
  | awk '/^## Dependencias/{f=1;next} /^## /{f=0} f' | grep -oE 'Depende de #[0-9]+' | grep -oE '[0-9]+' \
  | while read -r d; do echo "#$d $(gh issue view "$d" -R "$REPO" --json state -q .state)"; done
```

Si alguna dependencia esta `OPEN`, el issue lleva label `bloqueado`; cuando todas cierran, quitalo.

## Reglas

1. Siempre `-R "$REPO"`. Nunca asumas el repo del `cwd`.
2. Body por `--body-file`; nunca inline con comillas.
3. No dupliques informacion de labels en el body (MoSCoW, SP, prioridad solo en labels).
4. Un comentario por marcador; edita en vez de repetir. **Valida siempre antes de publicar**: `python3 "$PLUGIN_ROOT/scripts/validar_marcador.py" <archivo>` (sensor de formato; sale 1 con la lista de problemas).
5. Antes de crear un label que falte, corre `scripts/setup-github-labels.sh` del plugin (idempotente) en vez de `gh label create` ad hoc.
6. Titulos en infinitivo, sin prefijos ni numeros.
