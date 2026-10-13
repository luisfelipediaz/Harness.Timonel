#!/usr/bin/env python3
"""Mutacion de un literal en una copia del repo: cuantos tests lo notan.

Quien verifica una invariante "por mutacion" quita (o mueve fuera de su
seccion) el literal que la sostiene y mira si el test falla. Hacerlo a mano
repite el trabajo (#224 lo hizo tres veces en un ciclo) y deja pasar el caso
peor: reportar "verificado por mutacion" sobre un archivo que nunca cambio
(#124). Este script lo hace en una copia temporal del cwd, comprueba que la
mutacion entro y corre unittest en la copia. El arbol original no se toca.

Tres respuestas, nunca dos (`heuristics/general/sensor-declara-su-evidencia.md`):
hay conteo (`fallos: N de M`, exit 0) o hay "no se" (exit 2). Una mutacion que
no entra, un objetivo que no recolecta tests o una salida no parseable jamas se
reportan como `fallos: 0 de M`: ese 0 diria "invariante vacua" sin haberla
probado.

    python3 scripts/mutar_literal.py --ruta agents/x.md --literal "texto" \\
        --modo borrar [--test tests.modulo.Clase]
    python3 scripts/mutar_literal.py --ruta x.md --literal "texto" \\
        --modo mover --a "## Notas"
    python3 scripts/mutar_literal.py --ruta x.sh --literal "continue" \\
        --modo sustituir --por "break" [--linea 93]

Modos (la unidad es la linea; se mutan TODAS las que contienen el literal):
    borrar  quita el literal de cada linea que lo contiene
    mover   las lineas con el literal fuera de la seccion `--a` se quitan y se
            reinsertan al final de esa seccion. `--a` es la linea completa del
            encabezado (`## Notas`, no un prefijo ni un titulo sin `#`).
            Seccion = desde el encabezado
            hasta el siguiente de nivel <= al suyo, o fin de archivo.
    sustituir  reemplaza el literal por `--por B` (texto literal, sin regex) en
            cada linea que lo contiene. Es la mutacion para cambios de
            comportamiento (`*/.git)` -> `*)`, `continue` -> `break`) donde
            borrar dejaria un error de sintaxis.

`--linea N` (entero, 1-based como `grep -n`) acota `borrar` y `sustituir` a esa
linea cuando el literal se repite; una linea sin el literal es
`mutacion_no_aplicada`. Con `mover` no aplica. `--por` solo aplica a `sustituir`.

Borrar una llamada completa con sus paréntesis (`f(x)` entero) deja la copia
con un error de sintaxis. Si el test importa el archivo, el objetivo "no se
encuentra" y sale `no sé` (exit 2); si lo ejecuta por subprocess, el error de
sintaxis se contaria como fallo del test. Por eso, antes de correr nada, la
mutacion se verifica por sufijo (`VERIFICADORES`: `.py` compila, `.json`
parsea, `.sh` pasa `bash -n`) y una copia que ya no compila sale `no sé`
(`mutacion_no_compila`). Solo cuenta si el original si compilaba; otras
extensiones (`.md`) no se verifican. Hay que mutar el argumento o la
condicion, no la llamada entera.

Sin `--test` corre `unittest discover -s tests` en la copia.

Stdout: `lineas mutadas: K`, `fallos: N de M` y `base: B de M`, en ese orden y
cada una en su linea. `base` es la misma corrida sobre la copia SIN mutar,
medida antes de escribir la mutacion: si la suite ya falla en la copia, `N` solo
es evidencia cuando `N > B`. La linea `fallos:` no cambia de forma.

Codigos de salida:
    0   hubo conteo `fallos: N de M` (con la mutacion verificada) y `base: B de M`
    2   no se (stderr: `no sé: <motivo>`, uno de `MOTIVOS`): mutacion que no
        entro, `--a` que no es un encabezado `#+ `, seccion destino
        inexistente, copia o lectura imposible (OSError, shutil.Error, archivo
        no UTF-8), objetivo sin tests o inexistente, salida no parseable,
        timeout, una corrida base cuyo `Ran M tests` no coincide con el de la
        mutada (`base_inconsistente`), o argumentos invalidos (coincide con el exit de uso de
        argparse): `sustituir` sin `--por`, `--por` vacio, igual a `--literal` o
        con salto de linea, `--por` fuera de `sustituir`, `--linea` con `mover`
        o fuera de rango; `mutacion_no_compila` (la copia mutada no compila o
        no parsea y el original si). Todos salen antes de correr tests. No hay exit 1: ningun "no pude medir" termina en traceback.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_S = 600
IGNORADOS_EN_CUALQUIER_DIR = {".git", "__pycache__", ".timonel"}

# Motivos del "no se" (exit 2). Lookup map en vez de mensajes sueltos.
MOTIVOS = {
    "literal_invalido": "--literal debe ser no vacío y de una sola línea",
    "ruta_invalida": "--ruta debe ser un archivo existente, relativo al repo y sin `..`",
    "mover_sin_destino": "--modo mover exige --a",
    "sustituir_sin_por": "--modo sustituir exige --por",
    "por_invalido": "--por debe ser no vacío, distinto de --literal y de una sola línea",
    "por_no_aplica_al_modo": "--por solo aplica a --modo sustituir",
    "linea_no_aplica_al_modo": "--linea solo aplica a --modo borrar o sustituir",
    "linea_invalida": "--linea debe estar entre 1 y el número de líneas de la ruta",
    "mutacion_no_aplicada": "la mutación no se aplicó (el literal no está fuera del destino o la copia quedó idéntica)",
    "mutacion_no_compila": "la mutación deja la copia sin compilar o parsear (el original sí): sus fallos serían de sintaxis, no de la invariante",
    "destino_no_es_encabezado": "--a debe ser un encabezado markdown completo (`#+ ` seguido del título)",
    "seccion_destino_inexistente": "sección destino no existe en la ruta",
    "objetivo_no_encontrado": "objetivo de test no encontrado",
    "sin_tests": "el objetivo no recolectó ningún test",
    "salida_no_parseable": "la salida de unittest no trae `Ran M tests`",
    "base_inconsistente": "la corrida sin mutar y la mutada no ejecutaron el mismo número de tests",
    "copia_o_lectura_imposible": "no se pudo copiar el repo o leer/escribir la ruta (symlink roto, permisos o archivo no UTF-8)",
    "timeout": f"unittest superó el timeout de {TIMEOUT_S} s",
}


class NoSe(Exception):
    """El sensor no puede responder: lleva la clave de `MOTIVOS`."""

    def __init__(self, clave: str):
        super().__init__(MOTIVOS[clave])
        self.clave = clave


def _nivel(linea: str) -> int:
    m = re.match(r"(#+)\s", linea)
    return len(m.group(1)) if m else 0


def rango_de_seccion(lineas: list[str], encabezado: str) -> tuple[int, int] | None:
    """(inicio, fin) de la seccion: del encabezado al siguiente de nivel <= al
    suyo (exclusivo) o fin de archivo. Encabezado anclado por igualdad de linea
    completa (`## N` no ancla en `## Nueva`)."""
    nivel = _nivel(encabezado)
    for i, linea in enumerate(lineas):
        if linea.rstrip("\n") == encabezado:
            for j in range(i + 1, len(lineas)):
                if 0 < _nivel(lineas[j]) <= nivel:
                    return i, j
            return i, len(lineas)
    return None


def _fuera_del_destino(lineas: list[str], literal: str, destino: str) -> list[int]:
    rango = rango_de_seccion(lineas, destino)
    if rango is None:
        raise NoSe("seccion_destino_inexistente")
    return [i for i, l in enumerate(lineas) if literal in l and not rango[0] <= i < rango[1]]


def _con_literal(lineas: list[str], literal: str, linea: int | None) -> list[int]:
    """Indices de las lineas con el literal; `linea` (1-based) acota a una sola."""
    return [i for i, l in enumerate(lineas) if literal in l and linea in (None, i + 1)]


def _borrar(lineas: list[str], literal: str, destino: str | None, por: str | None, linea: int | None) -> list[str]:
    afectadas = set(_con_literal(lineas, literal, linea))
    return [l.replace(literal, "") if i in afectadas else l for i, l in enumerate(lineas)]


def _sustituir(lineas: list[str], literal: str, destino: str | None, por: str | None, linea: int | None) -> list[str]:
    afectadas = set(_con_literal(lineas, literal, linea))
    return [l.replace(literal, por or "") if i in afectadas else l for i, l in enumerate(lineas)]


def _mover(lineas: list[str], literal: str, destino: str | None, por: str | None, linea: int | None) -> list[str]:
    indices = set(_fuera_del_destino(lineas, literal, destino or ""))
    movidas = [lineas[i] if lineas[i].endswith("\n") else lineas[i] + "\n" for i in sorted(indices)]
    resto = [l for i, l in enumerate(lineas) if i not in indices]
    inicio, fin = rango_de_seccion(resto, destino or "") or (0, len(resto))
    corte = fin
    while corte > inicio + 1 and not resto[corte - 1].strip():
        corte -= 1
    if not resto[corte - 1].endswith("\n"):
        resto[corte - 1] += "\n"
    return resto[:corte] + movidas + resto[corte:]


MODOS = {"borrar": _borrar, "mover": _mover, "sustituir": _sustituir}

# (condicion sobre modo, literal, por, linea) -> clave de MOTIVOS. Gana la primera.
REGLAS_DE_OPCIONES = [
    (lambda m, lit, p, n: m == "sustituir" and p is None, "sustituir_sin_por"),
    (lambda m, lit, p, n: m != "sustituir" and p is not None, "por_no_aplica_al_modo"),
    (lambda m, lit, p, n: m == "sustituir" and (not p or p == lit or "\n" in p or "\r" in p), "por_invalido"),
    (lambda m, lit, p, n: m == "mover" and n is not None, "linea_no_aplica_al_modo"),
    (lambda m, lit, p, n: n is not None and n < 1, "linea_invalida"),
]


def validar_opciones(literal: str, modo: str, por: str | None, linea: int | None) -> None:
    for condicion, clave in REGLAS_DE_OPCIONES:
        if condicion(modo, literal, por, linea):
            raise NoSe(clave)


def mutar(
    texto: str, literal: str, modo: str, destino: str | None,
    por: str | None = None, linea: int | None = None,
) -> tuple[str, int]:
    """Aplica la mutacion y la verifica. Devuelve (texto_mutado, lineas_mutadas).
    Lanza NoSe si el literal no esta, la seccion no existe, las opciones no
    aplican al modo, `linea` cae fuera del archivo o la copia no cambio."""
    validar_opciones(literal, modo, por, linea)
    lineas = texto.splitlines(keepends=True)
    if linea is not None and linea > len(lineas):
        raise NoSe("linea_invalida")
    contadores = {
        "borrar": lambda: _con_literal(lineas, literal, linea),
        "sustituir": lambda: _con_literal(lineas, literal, linea),
        "mover": lambda: _fuera_del_destino(lineas, literal, destino or ""),
    }
    afectadas = len(contadores[modo]())
    if afectadas == 0:
        raise NoSe("mutacion_no_aplicada")
    nuevo = "".join(MODOS[modo](lineas, literal, destino, por, linea))
    # Alcanzable: si el literal es el encabezado que sigue al destino y esta al
    # final del archivo, se quita y se reinserta en el mismo sitio (texto igual).
    if nuevo == texto:
        raise NoSe("mutacion_no_aplicada")
    return nuevo, afectadas


def parsear_unittest(salida: str, con_objetivo: bool) -> tuple[int, int]:
    """(fallos N, tests M) desde la salida de unittest, o NoSe."""
    ran = re.search(r"^Ran (\d+) tests?", salida, re.MULTILINE)
    if ran is None:
        raise NoSe("salida_no_parseable")
    total = int(ran.group(1))
    if total == 0:
        raise NoSe("sin_tests")
    if con_objetivo and "unittest.loader._FailedTest" in salida:
        raise NoSe("objetivo_no_encontrado")
    fallos = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", salida))
    return fallos, total


def _compila_py(texto: str) -> bool:
    try:
        compile(texto, "<mutada>", "exec")
    except (SyntaxError, ValueError):
        return False
    return True


def _parsea_json(texto: str) -> bool:
    try:
        json.loads(texto)
    except ValueError:
        return False
    return True


def _pasa_bash_n(texto: str) -> bool:
    try:
        r = subprocess.run(["bash", "-n"], input=texto, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return True  # sin bash no se puede afirmar que no compila: no se rechaza
    return r.returncode == 0


# sufijo -> verificador (texto -> compila). Sin entrada: no se verifica.
VERIFICADORES = {".py": _compila_py, ".json": _parsea_json, ".sh": _pasa_bash_n}


def verificar_que_compila(ruta: str, original: str, nuevo: str) -> None:
    """NoSe si la mutacion rompe un archivo que antes compilaba."""
    verificador = VERIFICADORES.get(Path(ruta).suffix, lambda texto: True)
    if verificador(original) and not verificador(nuevo):
        raise NoSe("mutacion_no_compila")


def _ignorar(origen: Path):
    def ignorar(directorio: str, nombres: list[str]) -> set[str]:
        rel = Path(directorio).resolve().relative_to(origen)
        return {
            n for n in nombres
            if n in IGNORADOS_EN_CUALQUIER_DIR
            or n.endswith(".pyc")
            or (rel == Path(".claude") and n == "worktrees")
        }
    return ignorar


def correr_unittest(copia: Path, objetivo: str | None) -> str:
    cmd = [sys.executable, "-m", "unittest"] + (
        [objetivo] if objetivo else ["discover", "-s", "tests"]
    )
    # Los tests importan hermanos (`from test_x import ...`): `<copia>/tests`
    # va delante del PYTHONPATH del llamador, que se conserva (#286).
    pythonpath = os.pathsep.join(
        [str(copia / "tests"), *filter(None, [os.environ.get("PYTHONPATH")])]
    )
    try:
        r = subprocess.run(
            cmd, cwd=copia, capture_output=True, text=True, timeout=TIMEOUT_S,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": pythonpath},
        )
    except subprocess.TimeoutExpired:
        raise NoSe("timeout")
    return r.stdout + r.stderr


def _validar(args: argparse.Namespace) -> None:
    if not args.literal or "\n" in args.literal or "\r" in args.literal:
        raise NoSe("literal_invalido")
    ruta = Path(args.ruta)
    if ruta.is_absolute() or ".." in ruta.parts or not (Path.cwd() / ruta).is_file():
        raise NoSe("ruta_invalida")
    validar_opciones(args.literal, args.modo, args.por, args.linea)
    if args.modo == "mover" and not args.a:
        raise NoSe("mover_sin_destino")
    if args.modo == "mover" and not re.match(r"#+ \S", args.a):
        raise NoSe("destino_no_es_encabezado")


def medir(args: argparse.Namespace) -> tuple[int, int, int, int]:
    """(lineas_mutadas, fallos, tests, fallos_base). Lanza NoSe."""
    _validar(args)
    origen = Path.cwd().resolve()
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "copia"
        archivo = copia / args.ruta
        try:
            shutil.copytree(origen, copia, ignore=_ignorar(origen))
            original = archivo.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            raise NoSe("copia_o_lectura_imposible")
        nuevo, k = mutar(original, args.literal, args.modo, args.a, args.por, args.linea)
        verificar_que_compila(args.ruta, original, nuevo)
        base, total_base = parsear_unittest(correr_unittest(copia, args.test), args.test is not None)
        try:
            archivo.write_text(nuevo, encoding="utf-8")
        except OSError:
            raise NoSe("copia_o_lectura_imposible")
        salida = correr_unittest(copia, args.test)
        fallos, total = parsear_unittest(salida, args.test is not None)
    if total_base != total:
        raise NoSe("base_inconsistente")
    return k, fallos, total, base


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Muta un literal en una copia del repo y cuenta los tests que fallan.")
    parser.add_argument("--ruta", required=True)
    parser.add_argument("--literal", required=True)
    parser.add_argument("--modo", required=True, choices=sorted(MODOS))
    parser.add_argument("--a")
    parser.add_argument("--por")
    parser.add_argument("--linea", type=int)
    parser.add_argument("--test")
    args = parser.parse_args(argv)
    try:
        k, fallos, total, base = medir(args)
    except NoSe as e:
        print(f"no sé: {e}", file=sys.stderr)
        return 2
    print(f"lineas mutadas: {k}")
    print(f"fallos: {fallos} de {total}")
    print(f"base: {base} de {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
