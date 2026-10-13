#!/usr/bin/env python3
"""Sensor de una sola pregunta: ¿este comando invoca un push forzado real de `git`?

Lo consume la compuerta de push forzado de `hooks/hooks.json` (#316). Antes
decidia con un glob sobre el texto completo del comando
(`*'push'*'--force'*|*'push -f'*`), que atravesaba separadores de shell: un
`git push origin x && git worktree remove --force y` bloqueaba (falso positivo,
el `--force` es de OTRO segmento), y `git push -u -f` / `git -C . push -uf`
no bloqueaban (falso negativo). Este sensor decide por segmento, como
`scripts/detectar_commit.py` (#176), reutilizando SOLO los tres seams publicos
de `scripts/guard_integracion.py`: `segmentar()`, `clave_de_segmento()` y
`argumentos_de_segmento()`. No escribe un segundo parser ni toca privadas
(`heuristics/general/sensor-importa-no-reimplementa.md`).

Un segmento es push forzado si su clave es `("git", "push")` y algun argumento
es `--force`, `--force-with-lease`, `--force-with-lease=<...>` o un grupo de
banderas cortas (un solo `-` seguido de letras) que contiene `f` (`-f`, `-uf`,
`-fu`), o un refspec forzado: un argumento que empieza con `+` y tiene mas de un
caracter (`+rama`, `+HEAD:rama`; #325). NO cuentan `--force-if-includes` solo,
`--no-force`, `--forced` ni un `+` en otro segmento o subcomando.

Tres respuestas, nunca dos (`heuristics/general/sensor-declara-su-evidencia.md`):
`invoca_push_forzado(cmd)` devuelve `True`, `False` o `None` ("no se": no se
pudo tokenizar o hubo un error inesperado). Nunca se colapsa `None` en `False`.

CLI: lee el comando CRUDO por stdin.

    printf '%s' "$cmd" | python3 detectar_push_forzado.py; echo $?

Codigos de salida: 0 si invoca un push forzado, 1 si no, 3 no se (el guard
aplica entonces su respaldo: el glob de siempre).

Envoltorios (`bash -c`, `sudo`, `env`, `time`, `command`, `xargs`, `eval`,
`$(...)`, `{ ...; }`, `if ...; then`): `clave_de_segmento` no los reconoce y
devuelve `None`. Para esos segmentos el texto unido se parte en tokens (asi un
`bash -c 'git push -uf x'`, que llega como un token, tambien se parte): si
contiene `push` y algun token es una bandera de fuerza (`-f`, `-uf`, `--force`,
...), el sensor responde "si" (exit 0), porque el glob de respaldo de hooks.json
no ve las banderas cortas agrupadas (#327). Si no, y el texto casa con el glob de
respaldo, responde "no se" (exit 3) y el hook cae a ese glob, que bloquea. Un
segmento con clave conocida distinta de `git push` (p. ej. `git worktree`) nunca
da "no se". Un `git push` forzado reconocido en otro segmento sigue ganando con
"si". Falso positivo aceptado (fail-closed): `echo git push -uf x` bloquea. El
refspec `+` NO se busca en segmentos sin clave.

Limites declarados (aceptados, fail-closed): un heredoc cuyo contenido tenga
una linea que empiece con un push forzado real sigue dando "si", igual que el
sensor de commits; y `git push -o -f x` da "si" por exceso, porque el sensor no
distingue el valor de una opcion con argumento de una bandera (igual con un
valor que empiece con `+`, p. ej. `-o +x`).
"""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guard_integracion as gi  # noqa: E402

CLAVE_PUSH = ("git", "push")

# Reflejan, literalmente, el glob de respaldo de la compuerta en hooks/hooks.json
# (`*'push'*'--force'*|*'push -f'*`). Un segmento que el sensor no reconoce y que
# casa con alguno es "no se", no "no".
_PATRONES_DE_RESPALDO = ("*push*--force*", "*push -f*")

_BANDERAS_LARGAS_DE_FUERZA = ("--force", "--force-with-lease")

# Traduce la respuesta de `invoca_push_forzado` (True/False/None) al codigo de
# salida de la CLI. Lookup map en vez de una cadena de `if` (evitar-ifs.md).
_CODIGOS_DE_SALIDA = {True: 0, False: 1, None: 3}


def _es_bandera_de_fuerza(argumento: str) -> bool:
    if argumento in _BANDERAS_LARGAS_DE_FUERZA:
        return True
    if argumento.startswith("--force-with-lease="):
        return True
    es_grupo_corto = argumento.startswith("-") and not argumento.startswith("--")
    return es_grupo_corto and argumento[1:].isalpha() and "f" in argumento[1:]


def _es_refspec_forzado(argumento: str) -> bool:
    # `+rama` / `+HEAD:rama` reescribe la historia remota igual que `--force`.
    # No se distingue de una opcion con valor (`-o +x`): fail-closed (#325).
    return argumento.startswith("+") and len(argumento) > 1


def _casa_con_el_respaldo(segmento: list[str]) -> bool:
    texto = " ".join(segmento)
    return any(fnmatch.fnmatchcase(texto, patron) for patron in _PATRONES_DE_RESPALDO)


def _es_push_forzado_envuelto(segmento: list[str]) -> bool:
    # Segmento sin clave (`sudo`, `env`, `time`, `bash -c '...'`): se re-parte el
    # texto unido (un `bash -c 'git push -uf x'` llega como UN token) y se busca
    # `push` mas una bandera de fuerza, que el glob de respaldo no ve agrupada (#327).
    tokens = " ".join(segmento).split()
    return "push" in tokens and any(_es_bandera_de_fuerza(t) for t in tokens)


def invoca_push_forzado(cmd: str) -> bool | None:
    """Punto de entrada puro. True si algun segmento es un `git push` con una
    bandera de fuerza, False si ninguno lo es, None si no se pudo decidir."""
    try:
        segmentos = gi.segmentar(cmd)
    except Exception:
        return None
    if segmentos is None:
        return None
    try:
        sin_reconocer = False
        for segmento in segmentos:
            clave = gi.clave_de_segmento(segmento)
            if clave is None:
                if _es_push_forzado_envuelto(segmento):
                    return True
                sin_reconocer = sin_reconocer or _casa_con_el_respaldo(segmento)
                continue
            if clave != CLAVE_PUSH:
                continue
            if any(_es_bandera_de_fuerza(a) or _es_refspec_forzado(a) for a in gi.argumentos_de_segmento(segmento)):
                return True
        return None if sin_reconocer else False
    except Exception:
        return None


def main() -> int:
    try:
        cmd = sys.stdin.read()
        resultado = invoca_push_forzado(cmd)
    except Exception:
        resultado = None
    return _CODIGOS_DE_SALIDA.get(resultado, 3)


if __name__ == "__main__":
    sys.exit(main())
