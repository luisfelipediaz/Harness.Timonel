#!/usr/bin/env python3
"""Bloquea comandos que crean integracion nueva sin pasar por PR (epica #79, #82).

La politica de integracion por PR (TIM-ADR-0005, #80) dice que el merge a la
rama base lo hace un humano al aprobar el PR. Este script es el guard
`PreToolUse` que la hace cumplir: bloquea `git push` a la rama base, `git
merge`/`git pull` que integrarian algo que nadie reviso estando parado en la
rama base, y `gh pr merge` siempre.

Criterio de frontera (no confundir con "en que rama estoy parado"): un comando
NO se juzga por la rama actual sino por si PUEDE CREAR INTEGRACION NUEVA.
  - `push`: el destino del refspec, no la rama actual. `git push -u origin
    hu/N-slug` (Fase 6.5, abre el PR) nunca se bloquea.
  - `merge`/`pull` estando en una rama base: se permite SOLO si la ref es
    vacia o el equivalente remoto de esa misma base (`origin/<base>`, `@{u}`,
    `@{upstream}`, o `origin <base>` en `pull`). `--ff-only` por si solo NO
    alcanza: `git merge --ff-only hu/N-x` en `main` es el agujero de la HU
    #30 y sigue bloqueado.
  - `gh pr merge`: siempre bloqueado, el merge del PR es de un humano.

Uso (stdin = payload de un hook PreToolUse de Claude Code):
    echo '{"tool_input": {"command": "git push origin main"}}' | python3 guard_integracion.py

Sale 2 con el mensaje en stderr si bloquea, 0 si lo permite. Ante cualquier
error inesperado (JSON invalido, `shlex` invalido, `git`/config ilegibles)
sale 0: fail-open deliberado, preferible que se cuele un merge -reversible-
a que el harness se trabe. La unica proteccion incondicional (no fail-open)
es `git push --force`, y esa vive inline en `hooks/hooks.json`, no aqui.
"""

from __future__ import annotations

import datetime
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

PREFIJO = "[timonel] Bloqueado: "

# Refs que solo pueden adelantar la copia local a lo ya publicado y revisado.
REFS_DE_SINCRONIA = {"", "@{u}", "@{upstream}"}

CONFIG_CONSUMIDOR = Path(".claude/timonel.config.json")
BASES_POR_DEFECTO = ["main", "master", "develop"]

EVENTS_LOG = Path(".timonel/events.log")

# Asignacion de variable de entorno delante del programa (`GIT_DIR=.git git ...`).
_RE_ASIGNACION_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _es_flag(token: str) -> bool:
    return token.startswith("-")


def _tokens_no_flag(tokens: list[str]) -> list[str]:
    return [t for t in tokens if not _es_flag(t)]


def _es_ref_segura(ref: str, base: str) -> bool:
    return ref in REFS_DE_SINCRONIA or ref == f"origin/{base}"


def _normalizar_referencia_destino(ref: str) -> str:
    """`refs/heads/<x>` y `<x>` son el mismo destino para `git push`; normaliza antes
    de comparar contra `bases` (si no, `hu/x:refs/heads/main` evade el guard aunque
    `hu/x:main` sí bloquee)."""
    prefijo = "refs/heads/"
    return ref[len(prefijo):] if ref.startswith(prefijo) else ref


def _registrar_fail_open(motivo: str) -> None:
    """Deja rastro de un fail-open en `.timonel/events.log`, mismo estilo que ya
    escriben los hooks `PostToolUse` de `hooks/hooks.json` (hora + evento). Nunca debe
    hacer fallar el guard: si el directorio no existe o no se puede escribir, sigue."""
    try:
        EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        with EVENTS_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{hora} guard-integracion-fail-open {motivo}\n")
    except Exception:
        pass


def _mensaje_push(base: str) -> str:
    return (
        f"{PREFIJO}push directo a la rama base '{base}' no esta permitido. "
        "Trabaja en la rama de la historia y publica con "
        "`git push -u origin hu/<issue>-<slug>`; el merge a "
        f"'{base}' lo hace un humano al aprobar el PR (epica #79)."
    )


def _mensaje_integracion_en_base(base: str) -> str:
    return (
        f"{PREFIJO}en la rama base '{base}' no se permite crear integracion "
        "nueva (TIM-ADR-0005, epica #79/#80). Para sincronizar tu copia "
        f"local si podes: `git merge --ff-only origin/{base}` (o `git pull "
        "--ff-only`)."
    )


def _mensaje_gh_pr_merge() -> str:
    return (
        f"{PREFIJO}gh pr merge esta bloqueado. El merge del PR lo hace un "
        "humano desde la web de GitHub o una terminal fuera de Claude "
        "(epica #79)."
    )


def _destino_push(resto: list[str], rama: str) -> str:
    """resto = tokens luego de `push`. Devuelve la rama remota destino."""
    no_flags = _tokens_no_flag(resto)
    if not no_flags:
        return rama  # sin remoto ni refspec: empuja la rama actual a su upstream
    _remoto, *refspecs = no_flags
    if not refspecs:
        return rama  # remoto explicito sin refspec: idem
    refspec = refspecs[0]
    if refspec == "HEAD":
        return rama
    if ":" in refspec:
        _, _, destino = refspec.partition(":")
        destino = destino or rama
    else:
        destino = refspec
    return _normalizar_referencia_destino(destino)


def _revisar_push(resto: list[str], rama: str, bases: list[str]) -> str | None:
    destino = _destino_push(resto, rama)
    return _mensaje_push(destino) if destino in bases else None


def _revisar_merge(resto: list[str], rama: str, bases: list[str]) -> str | None:
    if any(f in resto for f in ("--abort", "--continue", "--quit")):
        return None  # no integra nada nuevo
    if rama not in bases:
        return None  # el criterio de frontera solo aplica parado en una base
    ff_only = "--ff-only" in resto
    refs = _tokens_no_flag(resto)
    ref = refs[0] if refs else ""
    if ff_only and _es_ref_segura(ref, rama):
        return None
    return _mensaje_integracion_en_base(rama)


def _revisar_pull(resto: list[str], rama: str, bases: list[str]) -> str | None:
    if rama not in bases:
        return None
    ff_only = "--ff-only" in resto
    no_flags = _tokens_no_flag(resto)
    if len(no_flags) >= 2:
        remoto, rama_remota = no_flags[0], no_flags[1]
        ref_efectiva = f"{remoto}/{rama_remota}"
    else:
        ref_efectiva = ""  # sin refspec, o solo remoto sin rama: se asume seguro
    if ff_only and _es_ref_segura(ref_efectiva, rama):
        return None
    return _mensaje_integracion_en_base(rama)


def _rama_tras_checkout(resto: list[str], rama_actual: str) -> str:
    no_flags = _tokens_no_flag(resto)
    return no_flags[-1] if no_flags else rama_actual


def _manejar_push(resto, rama, bases):
    return _revisar_push(resto, rama, bases), rama


def _manejar_merge(resto, rama, bases):
    return _revisar_merge(resto, rama, bases), rama


def _manejar_pull(resto, rama, bases):
    return _revisar_pull(resto, rama, bases), rama


def _manejar_checkout(resto, rama, bases):  # noqa: ARG001 - firma uniforme para el lookup map
    return None, _rama_tras_checkout(resto, rama)


def _manejar_gh_pr_merge(resto, rama, bases):  # noqa: ARG001 - firma uniforme para el lookup map
    return _mensaje_gh_pr_merge(), rama


# Lookup map: subcomando -> manejador(resto_tras_subcomando, rama, bases) -> (mensaje|None, rama_siguiente)
MANEJADORES = {
    ("git", "push"): _manejar_push,
    ("git", "merge"): _manejar_merge,
    ("git", "pull"): _manejar_pull,
    ("git", "checkout"): _manejar_checkout,
    ("git", "switch"): _manejar_checkout,
    ("gh", "pr", "merge"): _manejar_gh_pr_merge,
}

SEPARADORES_DE_SEGMENTO = {"&&", "||", ";"}

# Flags globales de `git` que van ANTES del subcomando y que hay que saltear para
# no confundir su argumento (o el propio flag) con el subcomando real.
_FLAGS_GLOBALES_GIT_CON_VALOR = {"-C", "--git-dir", "--work-tree"}


def _descartar_asignaciones_env(segmento: list[str]) -> list[str]:
    """`GIT_DIR=.git git push ...`: descarta los tokens `NOMBRE=valor` que preceden
    al programa real, tal como lo haria el shell al armar el entorno del comando."""
    i = 0
    while i < len(segmento) and _RE_ASIGNACION_ENV.match(segmento[i]):
        i += 1
    return segmento[i:]


def _indice_subcomando_git(segmento: list[str]) -> int | None:
    """Salta flags globales de `git` (`-C <path>`, `--git-dir[=valor]`,
    `--work-tree[=valor]`) y devuelve el indice del subcomando real, o None si no
    hay ninguno (p. ej. `git` solo, o `git -C` sin subcomando)."""
    i = 1
    n = len(segmento)
    while i < n:
        token = segmento[i]
        if token in _FLAGS_GLOBALES_GIT_CON_VALOR:
            i += 2
            continue
        if any(token.startswith(f"{flag}=") for flag in _FLAGS_GLOBALES_GIT_CON_VALOR):
            i += 1
            continue
        return i
    return None


def _clave_y_resto(segmento: list[str]) -> tuple[tuple[str, ...] | None, list[str]]:
    segmento = _descartar_asignaciones_env(segmento)
    if not segmento:
        return None, []
    programa = segmento[0]
    if programa == "git":
        idx = _indice_subcomando_git(segmento)
        if idx is None:
            return None, []
        return ("git", segmento[idx]), segmento[idx + 1:]
    if programa == "gh" and len(segmento) >= 3 and segmento[1] == "pr":
        return ("gh", "pr", segmento[2]), segmento[3:]
    return None, []


def _normalizar_separadores(cmd: str) -> str:
    """Inserta espacios alrededor de `;`, `&&`, `||` para que salgan como tokens
    propios de `shlex.split`, sin tocar lo que este dentro de comillas simples o
    dobles (si no, `git commit -m "fix; ver #82"` perderia la comilla de cierre y
    `shlex` fallaria: un fail-open silencioso y evadible a proposito)."""
    resultado: list[str] = []
    comilla: str | None = None
    i = 0
    n = len(cmd)
    while i < n:
        ch = cmd[i]
        if comilla:
            resultado.append(ch)
            if ch == comilla:
                comilla = None
            i += 1
            continue
        if ch in ("'", '"'):
            comilla = ch
            resultado.append(ch)
            i += 1
            continue
        dos = cmd[i:i + 2]
        if dos in ("&&", "||"):
            resultado.append(f" {dos} ")
            i += 2
            continue
        if ch == ";":
            resultado.append(" ; ")
            i += 1
            continue
        resultado.append(ch)
        i += 1
    return "".join(resultado)


def _partir_en_segmentos(tokens: list[str]) -> list[list[str]]:
    """Parte en `&&`/`||`/`;` para que un comando compuesto no evada el guard."""
    segmentos: list[list[str]] = [[]]
    for token in tokens:
        if token in SEPARADORES_DE_SEGMENTO:
            segmentos.append([])
        else:
            segmentos[-1].append(token)
    return [s for s in segmentos if s]


def decidir(cmd: str, rama: str, bases: list[str]) -> str | None:
    """Punto de entrada puro. `rama` es la rama actual real; se simula su avance
    entre segmentos (`git checkout <base> && ...`) para que el compuesto no evada
    el guard. Devuelve el mensaje de bloqueo, o None si el comando se permite."""
    try:
        tokens = shlex.split(_normalizar_separadores(cmd), posix=True)
    except ValueError:
        _registrar_fail_open("shlex-invalido")
        return None  # shlex invalido (comillas sin cerrar, etc.): fail-open
    try:
        rama_actual = rama
        for segmento in _partir_en_segmentos(tokens):
            clave, resto = _clave_y_resto(segmento)
            manejador = MANEJADORES.get(clave)
            if manejador is None:
                continue
            mensaje, rama_actual = manejador(resto, rama_actual, bases)
            if mensaje:
                return mensaje
        return None
    except Exception:
        _registrar_fail_open("error-inesperado")
        return None  # error inesperado: fail-open


def _rama_git_actual() -> str:
    resultado = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=False
    )
    return resultado.stdout.strip()


def _bases_configuradas() -> list[str]:
    if CONFIG_CONSUMIDOR.exists():
        try:
            config = json.loads(CONFIG_CONSUMIDOR.read_text(encoding="utf-8"))
            bases = config.get("git", {}).get("baseBranches")
            if bases:
                return list(bases)
        except (OSError, ValueError):
            pass
    return list(BASES_POR_DEFECTO)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        cmd = payload.get("tool_input", {}).get("command", "")
        mensaje = decidir(cmd, _rama_git_actual(), _bases_configuradas())
    except Exception:
        _registrar_fail_open("payload-o-entorno-invalido")
        return 0  # payload roto o entorno inesperado: fail-open
    if mensaje:
        print(mensaje, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
