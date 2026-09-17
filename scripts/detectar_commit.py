#!/usr/bin/env python3
"""Sensor de una sola pregunta: ¿este comando invoca un commit real de `git`?

Lo consumen los dos guards `PreToolUse`/`Bash` de commit de `hooks/hooks.json`
(#176): antes decidian "¿corro?" con una coincidencia de texto literal
contiguo (`case "$cmd" in *'git commit'*)`), compuerta con dos fallas
simetricas -- se activa con un `echo`/heredoc que solo NOMBRA la cadena
(falso positivo) y no se activa con `git -C <ruta> commit` (falso negativo),
porque entre `git` y `commit` queda `-C <ruta>`. Ambas evidenciadas en #174
y consolidadas en #176.

Reutiliza el tokenizador ya probado de `scripts/guard_integracion.py` via sus
DOS seams publicos: `segmentar()` (envuelve `_normalizar_separadores` +
`shlex.split` + `_partir_en_segmentos`) y `clave_de_segmento()` (que delega en
el parser interno que ya sabe saltar flags globales de `git`
-C/-c/--git-dir/etc., con valor pegado o separado, y descartar asignaciones
`VAR=valor` delante del programa) para reconocer el subcomando real de cada
segmento de un comando compuesto. NO se escribe un segundo parser, ni en shell
ni en Python (`heuristics/general/sensor-importa-no-reimplementa.md`), y
tampoco se llama a ninguna funcion privada de `guard_integracion.py`: los dos
seams publicos de arriba son el contrato completo entre ambos modulos.

Tres respuestas, nunca dos (`heuristics/general/ausencia-de-evidencia.md`):
`invoca_commit(cmd)` devuelve `True` (si invoca un commit real), `False` (no
invoca ninguno) o `None` ("no se": el comando no se pudo tokenizar -- p. ej.
una comilla sin cerrar -- o algo inesperado impidio decidir). El llamador
(el guard de `hooks.json`) NUNCA debe tratar `None` como `False`: un sensor
que no puede responder y que colapsara en "no" apagaria en silencio la
proteccion de TIM-ADR-0005 -- por eso la CLI usa un codigo de salida
DISTINTO para cada una de las tres respuestas, y `main()` atrapa cualquier
excepcion no prevista para que nunca escape como un traceback con exit code
1 (que el guard leeria, erroneamente, como "no invoca commit").

CLI: lee el comando CRUDO por stdin (no el payload JSON de un hook de Claude
Code: los entries de `hooks.json` ya consumieron stdin con `jq` para armar
`$cmd` antes de invocar este sensor).

    printf '%s' "$cmd" | python3 detectar_commit.py; echo $?

Codigos de salida:
    0   si invoca un commit real
    1   no invoca ningun commit
    3   no se -- el guard que lo invoca aplica su propio respaldo (la
        compuerta literal de hoy, `case "$cmd" in *'git commit'*)`) ante
        cualquier codigo que no sea 0 o 1 (sensor ausente, `python3`
        ausente, `shlex` invalido, version instalada vieja que no entiende
        esta CLI): ver el protocolo de invocacion en `hooks/hooks.json`.

Limite declarado (no es un olvido, ver contrato de cambio de #176): este
sensor tokeniza el comando, no lo ejecuta. Un heredoc cuyo CONTENIDO tenga
una linea que empiece con una invocacion real de commit (por ejemplo, un
bloque de codigo con `git -C /otro/repo commit -m "mensaje"` citado dentro
de un `cat > archivo <<'EOF' ... EOF`) sigue siendo, a nivel de tokens,
indistinguible de un commit real -- `invoca_commit` devuelve `True` igual
que si el commit fuera real. `eval` y `bash -c` heredan el mismo limite
declarado de `guard_integracion.py` (guard != sandbox): no se persigue la
evasion deliberada.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guard_integracion as gi  # noqa: E402

CLAVE_COMMIT = ("git", "commit")

# Traduce la respuesta de `invoca_commit` (True/False/None) al codigo de
# salida de la CLI. Lookup map en vez de una cadena de `if` (evitar-ifs.md).
_CODIGOS_DE_SALIDA = {True: 0, False: 1, None: 3}


def invoca_commit(cmd: str) -> bool | None:
    """Punto de entrada puro. Tres respuestas (ver docstring del modulo):
    True si algun segmento del comando invoca `git commit` como subcomando
    real, False si ninguno lo hace, None si no se pudo decidir (tokenizacion
    invalida o error inesperado)."""
    try:
        segmentos = gi.segmentar(cmd)
    except Exception:
        return None
    if segmentos is None:
        return None
    try:
        for segmento in segmentos:
            clave = gi.clave_de_segmento(segmento)
            if clave == CLAVE_COMMIT:
                return True
        return False
    except Exception:
        return None


def main() -> int:
    try:
        cmd = sys.stdin.read()
        resultado = invoca_commit(cmd)
    except Exception:
        resultado = None
    return _CODIGOS_DE_SALIDA.get(resultado, 3)


if __name__ == "__main__":
    sys.exit(main())
