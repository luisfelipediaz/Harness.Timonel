#!/usr/bin/env bash
# install-git-hooks.sh --- Activa los git hooks versionados del repo de Timonel (.githooks/).
# Uso: scripts/install-git-hooks.sh   (una vez por clon)
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
[ -f "$ROOT/.claude-plugin/plugin.json" ] || { echo "ERROR: ejecutar dentro del repo de Timonel" >&2; exit 1; }
chmod +x "$ROOT"/.githooks/*
git -C "$ROOT" config core.hooksPath .githooks
echo "core.hooksPath=.githooks — commit-msg exige referenciar un issue (#N)."
