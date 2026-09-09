---
description: "Muestra el estado del backlog en GitHub Issues agrupado por epica (progreso, listas, en progreso, bloqueadas)."
argument-hint: "[#epica | mod:<modulo>]"
model: haiku
---

Muestra el backlog del repo consumidor. Comunicate en **espanol**. Solo lectura.

```bash
[ -f .claude/timonel.config.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
REPO=$(jq -r '.github.repo' .claude/timonel.config.json)
```

## Sin argumentos

1. Epicas abiertas con progreso de sub-issues:

```bash
gh api graphql -f query='query($o:String!,$r:String!){ repository(owner:$o,name:$r){ issues(first:50,states:OPEN,labels:["tipo:epica"],orderBy:{field:CREATED_AT,direction:ASC}){ nodes{ number title subIssuesSummary{ total completed percentCompleted } } } } }' -f o="${REPO%/*}" -f r="${REPO#*/}" -q '.data.repository.issues.nodes[] | "#\(.number) \(.title) — \(.subIssuesSummary.completed)/\(.subIssuesSummary.total) (\(.subIssuesSummary.percentCompleted)%)"'
```

2. HUs por estado (conteo y lista corta):

```bash
for e in listo en-progreso borrador; do echo "== estado:$e"; gh issue list -R "$REPO" --label tipo:hu --label "estado:$e" --state open --limit 100 --json number,title,labels -q '.[] | "#\(.number) \(.title) [\([.labels[].name | select(startswith("sp:") or startswith("mod:"))] | join(" "))]"'; done
echo "== bloqueadas"; gh issue list -R "$REPO" --label bloqueado --state open --json number,title -q '.[] | "#\(.number) \(.title)"'
```

3. Hotfixes abiertos y SDD abiertos (una linea cada uno).

## Con `#N` (epica)

Lista sus sub-issues con estado, labels `sp:`/`estado:`/`review:` y el ultimo refinamiento (`<!-- timonel:refinamiento -->`) si existe.

## Con `mod:<m>`

`gh issue list -R "$REPO" --label "mod:<m>" --state open ...` agrupado por `estado:`.

Presenta en tablas markdown compactas. No modifiques nada.
