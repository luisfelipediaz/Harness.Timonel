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
`-fu`). NO cuentan `--force-if-includes` solo, `--no-force`, `--forced` ni el
refspec `+rama` (fuera de alcance).

Tres respuestas, nunca dos (`heuristics/general/sensor-declara-su-evidencia.md`):
`invoca_push_forzado(cmd)` devuelve `True`, `False` o `None` ("no se": no se
pudo tokenizar o hubo un error inesperado). Nunca se colapsa `None` en `False`.

CLI: lee el comando CRUDO por stdin.

    printf '%s' "$cmd" | python3 detectar_push_forzado.py; echo $?

Codigos de salida: 0 si invoca un push forzado, 1 si no, 3 no se (el guard
aplica entonces su respaldo: el glob de siempre).

Limites declarados (aceptados, fail-closed): un heredoc cuyo contenido tenga
una linea que empiece con un push forzado real sigue dando "si", igual que el
sensor de commits; y `git push -o -f x` da "si" por exceso, porque el sensor no
distingue el valor de una opcion con argumento de una bandera. `eval` y
`bash -c` heredan el limite de `guard_integracion.py` (guard != sandbox).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guard_integracion as gi  # noqa: E402

CLAVE_PUSH = ("git", "push")

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
        for segmento in segmentos:
            if gi.clave_de_segmento(segmento) != CLAVE_PUSH:
                continue
            if any(_es_bandera_de_fuerza(a) for a in gi.argumentos_de_segmento(segmento)):
                return True
        return False
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
