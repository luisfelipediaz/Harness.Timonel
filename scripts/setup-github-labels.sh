#!/usr/bin/env bash
# setup-github-labels.sh --- Provisiona el esquema de labels de Timonel (TIM-ADR-0001).
#
# Uso:
#   scripts/setup-github-labels.sh [--repo owner/repo] [--modulos "a b c"] [--dry-run] [--prune-defaults]
#
# Sin --repo lee github.repo de .claude/timonel.config.json; sin --modulos lee modulos[].
# Idempotente: crea el label si falta y actualiza color/descripcion si existe.
# --prune-defaults elimina los labels default de GitHub (solo repos nuevos de backlog).
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

REPO=""
MODULOS=""
DRY_RUN=0
PRUNE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --repo) REPO="$2"; shift 2 ;;
        --modulos) MODULOS="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --prune-defaults) PRUNE=1; shift ;;
        -h|--help) sed -n 2,10p "$0"; exit 0 ;;
        *) echo "Argumento desconocido: $1" >&2; exit 2 ;;
    esac
done

if [ -z "$REPO" ] || [ -z "$MODULOS" ]; then
    if load_timonel_config 2>/dev/null; then
        [ -n "$REPO" ] || REPO="$TIMONEL_REPO"
        [ -n "$MODULOS" ] || MODULOS="$TIMONEL_MODULOS"
    fi
fi
[ -n "$REPO" ] || { echo "ERROR: indica --repo owner/repo o crea .claude/timonel.config.json" >&2; exit 1; }

# name|color|description  (fuente: skills/github-issues/references/labels.md)
labels_base() {
cat <<'EOF'
tipo:sdd|5319E7|Software Design Document; padre de epicas
tipo:epica|3E4B9E|Epica; padre de historias
tipo:hu|0052CC|Historia de usuario implementable por flechodiezx
tipo:hotfix|1D76DB|Cambio <=2 SP sin ceremonia completa
estado:borrador|EDEDED|Capturado, no cumple DoR
estado:listo|0E8A16|Cumple DoR; puede implementarse
estado:en-progreso|FBCA04|En implementacion
estado:en-revision|1D76DB|PR abierto, pendiente de merge humano
alcance:backend|C2E0C6|Solo API
alcance:frontend|BFD4F2|Solo cliente
alcance:full-stack|D4C5F9|API + cliente
moscow:must|B60205|Must Have
moscow:should|D93F0B|Should Have
moscow:could|FBCA04|Could Have
moscow:wont|CCCCCC|Wont Have (por ahora)
sp:1|F9D0C4|1 story point
sp:2|F9D0C4|2 story points
sp:3|F9D0C4|3 story points
sp:5|F9D0C4|5 story points
sp:8|F9D0C4|8 story points
sp:13|F9D0C4|13 story points
sp:21|F9D0C4|21 story points (dividir)
prioridad:alta|E11D21|Prioridad de negocio alta
prioridad:media|EB6420|Prioridad de negocio media
prioridad:baja|FEF2C0|Prioridad de negocio baja
review:aprobado|0E8A16|Code review sin hallazgos
review:observaciones|FBCA04|Aprobado con warnings
review:requiere-cambios|B60205|Hallazgos criticos; bloquea DoD
retro:preciso|C5DEF5|SP real = estimado
retro:subestimado|F9D0C4|SP real > estimado
retro:sobreestimado|D4E7D4|SP real < estimado
bloqueado|000000|Alguna dependencia abierta
bug|D73A4A|Corrige un defecto (ortogonal a tipo:)
duplicada|CFD3D7|Duplicada de otra HU
obsoleta|CFD3D7|Reemplazada o ya no aplica
insights|5319E7|Insights destilados (retro/review)
harness-audit|0E8A16|Auditoria de madurez del harness
EOF
}
LABELS="$(labels_base)"
for m in $MODULOS; do
    LABELS="$LABELS"$'\n'"mod:$m|006B75|Modulo destino: $m"
done

if [ "$DRY_RUN" = 1 ]; then
    echo "Repo: $REPO"
    printf '%s\n' "$LABELS" | awk -F'|' '{ printf "%-26s %s  %s\n", $1, $2, $3 }'
    exit 0
fi

require_gh

EXISTING=$(gh label list -R "$REPO" --limit 300 --json name -q '.[].name')
created=0; updated=0
while IFS='|' read -r name color desc; do
    [ -n "$name" ] || continue
    if printf '%s\n' "$EXISTING" | grep -qxF "$name"; then
        gh label edit "$name" -R "$REPO" --color "$color" --description "$desc" >/dev/null
        updated=$((updated + 1))
    else
        gh label create "$name" -R "$REPO" --color "$color" --description "$desc" >/dev/null
        created=$((created + 1))
    fi
done <<< "$LABELS"

if [ "$PRUNE" = 1 ]; then
    for d in "documentation" "duplicate" "enhancement" "good first issue" "help wanted" "invalid" "question" "wontfix"; do
        if printf '%s\n' "$EXISTING" | grep -qxF "$d"; then
            gh label delete "$d" -R "$REPO" --yes >/dev/null && echo "eliminado default: $d"
        fi
    done
fi

echo "Labels en $REPO: $created creados, $updated actualizados."
