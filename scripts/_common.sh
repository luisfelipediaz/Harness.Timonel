#!/usr/bin/env bash
# _common.sh --- Funciones compartidas por los scripts de Timonel.
#
# Uso: source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
# No invocar directamente (prefijo _ = sourceable).

# resolve_plugin_root
#
# Exporta TIMONEL_PLUGIN_ROOT. Orden: CLAUDE_PLUGIN_ROOT (si Claude Code lo
# inyecta) -> .timonel/.plugin-root (escrito por el hook SessionStart) ->
# glob sobre el cache de marketplaces tomando la version mas reciente ->
# la carpeta padre de este script (cuando se corre desde el repo del plugin).
resolve_plugin_root() {
    local candidate="${CLAUDE_PLUGIN_ROOT:-}"
    if [ -z "$candidate" ] && [ -f .timonel/.plugin-root ]; then
        candidate="$(cat .timonel/.plugin-root)"
    fi
    if [ -z "$candidate" ]; then
        candidate="$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ 2>/dev/null | sort -V | tail -1)"
    fi
    if [ -z "$candidate" ]; then
        candidate="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
    fi
    export TIMONEL_PLUGIN_ROOT="${candidate%/}"
}

# load_timonel_config [config_path]
#
# Carga .claude/timonel.config.json del consumidor y exporta TIMONEL_*.
# Retorna 1 con mensaje claro si falta el archivo, jq o github.repo.
load_timonel_config() {
    local config="${1:-.claude/timonel.config.json}"

    if ! command -v jq >/dev/null 2>&1; then
        echo "ERROR: jq no esta instalado. Requerido para leer $config" >&2
        return 1
    fi
    if [ ! -f "$config" ]; then
        echo "ERROR: no se encontro $config" >&2
        echo "  Ejecuta /timonel:onboard en la raiz del repo consumidor para generarlo." >&2
        return 1
    fi

    export TIMONEL_CONFIG_PATH="$config"
    export TIMONEL_PROJECT_NAME="$(jq -r '.projectName // ""' "$config")"
    export TIMONEL_REPO="$(jq -r '.github.repo // ""' "$config")"
    export TIMONEL_API_PROJECT="$(jq -r '.api.project // ""' "$config")"
    export TIMONEL_API_PATH="$(jq -r '.api.path // ""' "$config")"
    export TIMONEL_API_MODULE_FILE="$(jq -r '.api.moduleFile // ""' "$config")"
    export TIMONEL_FRONTEND_PROJECTS="$(jq -r '[.frontends[]?.project] | join(" ")' "$config")"
    export TIMONEL_MODELOS_ALIAS="$(jq -r '.modelos.alias // ""' "$config")"
    export TIMONEL_MODELOS_PATH="$(jq -r '.modelos.path // ""' "$config")"
    export TIMONEL_MODULOS="$(jq -r '[.modulos[]?] | join(" ")' "$config")"
    export TIMONEL_HEURISTICS_DIR="$(jq -r '.heuristicsDir // ""' "$config")"

    if [ -z "$TIMONEL_REPO" ] || [ "$TIMONEL_REPO" = "null" ]; then
        echo "ERROR: $config no declara github.repo (owner/repo donde viven los issues)" >&2
        return 1
    fi
    case "$TIMONEL_REPO" in
        */*) ;;
        *) echo "ERROR: github.repo debe tener la forma owner/repo (recibido: $TIMONEL_REPO)" >&2; return 1 ;;
    esac
}

# require_gh
#
# Verifica gh autenticado. Retorna 1 con instrucciones si no.
require_gh() {
    if ! command -v gh >/dev/null 2>&1; then
        echo "ERROR: gh (GitHub CLI) no esta instalado. https://cli.github.com" >&2
        return 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
        echo "ERROR: gh no esta autenticado. Ejecuta: gh auth login" >&2
        return 1
    fi
}
