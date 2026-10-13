"""Tests de `scripts/detectar_push_forzado.py` y del seam `argumentos_de_segmento`
(#316). Unitarios puros, sin disco ni hooks: la caja negra del hook vive en
`tests/test_hooks_integracion.py::CompuertaPushForzadoPorSegmentoTests`."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import detectar_push_forzado as dpf  # noqa: E402
import guard_integracion as gi  # noqa: E402


class DetectarPushForzadoUnitarioTests(unittest.TestCase):
    SI, NO, NOSE = True, False, None

    CASOS = [
        ("-f", "git push -f origin x", SI),
        ("-uf agrupado", "git push -uf origin x", SI),
        ("-fu agrupado", "git push -fu origin x", SI),
        ("--force", "git push --force origin x", SI),
        ("--force-with-lease", "git push --force-with-lease origin x", SI),
        ("--force-with-lease=r:sha", "git push --force-with-lease=r:sha origin x", SI),
        ("-C <r> con -uf", "git -C . push -uf origin x", SI),
        ("asignacion de entorno y -c", "FOO=1 git -c a=b push -f", SI),
        ("push forzado en el segundo segmento", "git status && git push --force origin x", SI),
        ("force de otro subcomando tras push", "git push origin tag && git worktree remove --force x", NO),
        ("force de branch tras ;", "git push origin hu/1-x; git branch -D --force y", NO),
        ("--force-if-includes solo", "git push --force-if-includes origin x", NO),
        ("--no-force", "git push --no-force origin x", NO),
        ("--forced", "git push --forced origin x", NO),
        ("refspec +rama (fuera de alcance)", "git push origin +rama", NO),
        ("echo con la cadena", 'echo "git push -f"', NO),
        ("push sin banderas", "git push origin x", NO),
        ("comando vacio", "", NO),
        ("comilla sin cerrar: no se", 'git push -f "origin', NOSE),
    ]

    def test_tabla_de_casos(self):
        for descripcion, cmd, esperado in self.CASOS:
            with self.subTest(caso=descripcion, cmd=cmd):
                self.assertIs(dpf.invoca_push_forzado(cmd), esperado)

    def test_excepcion_inesperada_es_no_se_no_no(self):
        original = gi.clave_de_segmento

        def explota(segmento):
            raise RuntimeError("boom")

        gi.clave_de_segmento = explota
        try:
            self.assertIsNone(dpf.invoca_push_forzado("git push -f"))
        finally:
            gi.clave_de_segmento = original


class DetectarPushForzadoSoloUsaSeamsPublicosTests(unittest.TestCase):
    """El sensor solo puede depender de los seams publicos de `gi`: con un doble de
    `gi` SIN `_clave_y_resto` sigue funcionando y sigue los valores de los seams."""

    def test_funciona_con_un_doble_de_gi_sin_privadas(self):
        class DobleGi:
            @staticmethod
            def segmentar(cmd):
                return [["x"]]

            @staticmethod
            def clave_de_segmento(segmento):
                return ("git", "push")

            @staticmethod
            def argumentos_de_segmento(segmento):
                return ["-f"]

        original = dpf.gi
        dpf.gi = DobleGi
        try:
            self.assertIs(dpf.invoca_push_forzado("cualquier cosa"), True)
        finally:
            dpf.gi = original


class ArgumentosDeSegmentoTests(unittest.TestCase):
    def test_devuelve_lo_que_sigue_al_subcomando_sin_flags_globales(self):
        segmento = gi.segmentar("FOO=1 git -C . -c a=b push -uf origin x")[0]
        self.assertEqual(gi.argumentos_de_segmento(segmento), ["-uf", "origin", "x"])

    def test_segmento_sin_clave_conocida_devuelve_lista_vacia(self):
        self.assertEqual(gi.argumentos_de_segmento(["ls", "-la"]), [])


class DetectarPushForzadoCliTests(unittest.TestCase):
    def _main_con(self, entrada):
        original = sys.stdin
        sys.stdin = io.StringIO(entrada)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return dpf.main()
        finally:
            sys.stdin = original

    def test_codigos_de_salida_por_stdin(self):
        for entrada, esperado in (
            ("git push --force origin x", 0),
            ("git push origin x", 1),
            ('git push -f "sin cerrar', 3),
        ):
            with self.subTest(entrada=entrada):
                self.assertEqual(self._main_con(entrada), esperado)

    def test_excepcion_al_leer_stdin_es_no_se(self):
        class Roto:
            def read(self):
                raise OSError("stdin roto")

        original = sys.stdin
        sys.stdin = Roto()
        try:
            self.assertEqual(dpf.main(), 3)
        finally:
            sys.stdin = original


if __name__ == "__main__":
    unittest.main()
