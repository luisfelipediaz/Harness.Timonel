import argparse
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mutar_literal as ml  # noqa: E402

SCRIPT = ROOT / "scripts" / "mutar_literal.py"

DOC = "# Doc\n## A\nalfa MARCA\n## Notas\nfin\n"

TEST_X = '''import re
import unittest
from pathlib import Path

DOC = (Path(__file__).resolve().parents[1] / "doc.md").read_text(encoding="utf-8")


class TestA(unittest.TestCase):
    def test_marca_en_la_seccion_a(self):
        seccion = re.search(r"## A\\n(.*?)(?=^## |\\Z)", DOC, re.S | re.M).group(1)
        self.assertIn("MARCA", seccion)


class TestB(unittest.TestCase):
    def test_fin_en_el_doc(self):
        self.assertIn("fin", DOC)


class Vacia(unittest.TestCase):
    pass
'''


def _repo_minimo(tmp: str) -> Path:
    repo = Path(tmp) / "repo"
    (repo / "tests").mkdir(parents=True)
    # Fuera del repo y con el literal: sin el control de ruta, la mutacion entraria.
    (Path(tmp) / "fuera.md").write_text(DOC, encoding="utf-8")
    (repo / "doc.md").write_text(DOC, encoding="utf-8")
    (repo / "tests" / "test_x.py").write_text(TEST_X, encoding="utf-8")
    return repo


def _correr(repo: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *flags], cwd=repo, capture_output=True, text=True, timeout=120,
    )


class SeccionYMutacionTests(unittest.TestCase):
    """Funciones puras: semantica de seccion y de las dos mutaciones."""

    def _lineas(self, texto: str) -> list[str]:
        return texto.splitlines(keepends=True)

    def test_h2_corta_en_el_siguiente_h2_y_los_h3_no_cortan(self):
        lineas = self._lineas("## X\na\n### Y\nb\n## Z\nc\n")
        self.assertEqual(ml.rango_de_seccion(lineas, "## X"), (0, 4))

    def test_h3_corta_en_el_siguiente_h3_o_h2(self):
        lineas = self._lineas("## X\n### Y\nb\n### W\nc\n## Z\n")
        self.assertEqual(ml.rango_de_seccion(lineas, "### Y"), (1, 3))
        self.assertEqual(ml.rango_de_seccion(lineas, "### W"), (3, 5))

    def test_seccion_final_llega_al_fin_del_archivo(self):
        self.assertEqual(ml.rango_de_seccion(self._lineas("## X\na\nb\n"), "## X"), (0, 3))

    def test_encabezado_anclado_a_inicio_de_linea(self):
        self.assertIsNone(ml.rango_de_seccion(self._lineas("texto ## X\n"), "## X"))

    def test_borrar_quita_el_literal_de_todas_las_lineas(self):
        nuevo, k = ml.mutar("a LIT\nb\nc LIT LIT\n", "LIT", "borrar", None)
        self.assertEqual((nuevo, k), ("a \nb\nc  \n", 2))

    def test_mover_reinserta_al_final_del_destino_antes_del_siguiente_encabezado(self):
        nuevo, k = ml.mutar("## A\nx LIT\n## N\nfin\n\n## Z\nz\n", "LIT", "mover", "## N")
        self.assertEqual((nuevo, k), ("## A\n## N\nfin\nx LIT\n\n## Z\nz\n", 1))

    def test_mover_no_toca_las_lineas_que_ya_estan_en_el_destino(self):
        nuevo, k = ml.mutar("## A\nx LIT\n## N\ny LIT\n", "LIT", "mover", "## N")
        self.assertEqual((nuevo, k), ("## A\n## N\ny LIT\nx LIT\n", 1))

    def test_mover_con_destino_en_ultima_linea_sin_salto_final(self):
        nuevo, _ = ml.mutar("## A\nx LIT\n## N\nfin", "LIT", "mover", "## N")
        self.assertEqual(nuevo, "## A\n## N\nfin\nx LIT\n")

    def test_literal_ausente_es_no_se(self):
        with self.assertRaises(ml.NoSe) as c:
            ml.mutar("a\n", "LIT", "borrar", None)
        self.assertEqual(c.exception.clave, "mutacion_no_aplicada")

    def test_mover_con_todo_ya_en_destino_es_no_se(self):
        with self.assertRaises(ml.NoSe) as c:
            ml.mutar("## N\nLIT\n", "LIT", "mover", "## N")
        self.assertEqual(c.exception.clave, "mutacion_no_aplicada")

    def test_mover_a_seccion_inexistente_es_no_se(self):
        with self.assertRaises(ml.NoSe) as c:
            ml.mutar("LIT\n", "LIT", "mover", "## N")
        self.assertEqual(c.exception.clave, "seccion_destino_inexistente")


class ParsearUnittestTests(unittest.TestCase):
    def test_cuenta_failures_mas_errors(self):
        salida = "Ran 7 tests in 0.1s\n\nFAILED (failures=2, errors=1)\n"
        self.assertEqual(ml.parsear_unittest(salida, True), (3, 7))

    def test_ok_es_cero_fallos(self):
        self.assertEqual(ml.parsear_unittest("Ran 4 tests in 0.1s\n\nOK\n", True), (0, 4))

    def test_ran_cero_y_no_tests_ran_son_no_se(self):
        for salida in ("Ran 0 tests in 0.0s\n\nNO TESTS RAN\n", "Ran 0 tests in 0.0s\n\nOK\n"):
            with self.subTest(salida=salida):
                with self.assertRaises(ml.NoSe) as c:
                    ml.parsear_unittest(salida, True)
                self.assertEqual(c.exception.clave, "sin_tests")

    def test_failedtest_con_objetivo_es_objetivo_no_encontrado(self):
        salida = "ERROR: Nada (unittest.loader._FailedTest.Nada)\nRan 1 test in 0.0s\n\nFAILED (errors=1)\n"
        with self.assertRaises(ml.NoSe) as c:
            ml.parsear_unittest(salida, True)
        self.assertEqual(c.exception.clave, "objetivo_no_encontrado")

    def test_failedtest_sin_objetivo_cuenta_como_fallo_de_la_suite(self):
        salida = "ERROR: modulo (unittest.loader._FailedTest.modulo)\nRan 1 test in 0.0s\n\nFAILED (errors=1)\n"
        self.assertEqual(ml.parsear_unittest(salida, False), (1, 1))

    def test_sin_linea_ran_es_no_parseable(self):
        with self.assertRaises(ml.NoSe) as c:
            ml.parsear_unittest("basura", False)
        self.assertEqual(c.exception.clave, "salida_no_parseable")


class MainSubprocessTests(unittest.TestCase):
    """Cableado de `main()`: una fila por decision, assertEqual sobre el returncode (#233).
    Cada caso corre el script real en un repo temporal con un test que asevera un literal."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = _repo_minimo(tmp.name)

    def test_borrar_con_test_sale_0_con_conteo_y_no_toca_el_original(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "borrar", "--test", "tests.test_x.TestA")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("lineas mutadas: 1", r.stdout)
        self.assertIn("fallos: 1 de 1", r.stdout)
        self.assertEqual((self.repo / "doc.md").read_text(encoding="utf-8"), DOC)

    def test_sin_test_mide_la_suite_completa(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "borrar")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fallos: 1 de 2", r.stdout)

    def test_mover_a_seccion_existente_sale_0_con_conteo(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "mover", "--a", "## Notas", "--test", "tests.test_x.TestA")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fallos: 1 de 1", r.stdout)

    def test_literal_ausente_sale_2_sin_fallos_0(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "NO ESTA", "--modo", "borrar")
        self.assertEqual(r.returncode, 2)
        self.assertIn("la mutación no se aplicó", r.stderr)
        self.assertNotIn("fallos:", r.stdout)

    def test_copia_identica_sale_2(self):
        # `fin` ya vive en `## Notas`: mover no cambia nada.
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "fin", "--modo", "mover", "--a", "## Notas")
        self.assertEqual(r.returncode, 2)
        self.assertIn("la mutación no se aplicó", r.stderr)
        self.assertNotIn("fallos:", r.stdout)

    def test_mover_sin_a_sale_2(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "mover")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--modo mover exige --a", r.stderr)

    def test_mover_a_seccion_inexistente_sale_2(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "mover", "--a", "## Nada")
        self.assertEqual(r.returncode, 2)
        self.assertIn("sección destino no existe", r.stderr)

    def test_objetivo_con_cero_tests_sale_2(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "borrar", "--test", "tests.test_x.Vacia")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("fallos:", r.stdout)

    def test_objetivo_inexistente_sale_2_y_no_es_fallos_1_de_1(self):
        r = _correr(self.repo, "--ruta", "doc.md", "--literal", "MARCA", "--modo", "borrar", "--test", "tests.test_x.NoExiste")
        self.assertEqual(r.returncode, 2)
        self.assertIn("objetivo de test no encontrado", r.stderr)
        self.assertNotIn("fallos:", r.stdout)

    def test_ruta_invalida_sale_2(self):
        fuera = self.repo.parent / "fuera.md"
        for ruta in (str(fuera), "../fuera.md", "no_existe.md"):
            with self.subTest(ruta=ruta):
                r = _correr(self.repo, "--ruta", ruta, "--literal", "MARCA", "--modo", "borrar")
                self.assertEqual(r.returncode, 2)
                self.assertIn("--ruta debe ser", r.stderr)
                self.assertEqual(fuera.read_text(encoding="utf-8"), DOC)

    def test_literal_vacio_o_multilinea_sale_2(self):
        for literal in ("", "a\nb", "a\rb"):
            with self.subTest(literal=literal):
                r = _correr(self.repo, "--ruta", "doc.md", "--literal", literal, "--modo", "borrar")
                self.assertEqual(r.returncode, 2)
                self.assertIn("--literal debe ser", r.stderr)


class MainEnProcesoTests(unittest.TestCase):
    """Las dos filas que no se pueden provocar de forma barata con un subproceso real."""

    def _args(self, repo: Path) -> list[str]:
        return ["--ruta", "doc.md", "--literal", "MARCA", "--modo", "borrar"]

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = _repo_minimo(tmp.name)
        cwd = mock.patch("pathlib.Path.cwd", return_value=self.repo)
        cwd.start()
        self.addCleanup(cwd.stop)

    def test_salida_no_parseable_sale_2(self):
        with mock.patch.object(ml, "correr_unittest", return_value="basura"):
            self.assertEqual(ml.main(self._args(self.repo)), 2)

    def test_timeout_sale_2(self):
        with mock.patch.object(ml.subprocess, "run", side_effect=subprocess.TimeoutExpired("x", 1)):
            self.assertEqual(ml.main(self._args(self.repo)), 2)


class EscenarioRealContraElRepoTests(unittest.TestCase):
    """Escenario 1 de #263 contra la copia del repo real (no un repo de juguete)."""

    def _status(self) -> str:
        return subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout

    def test_borrar_literal_de_flechodiezx_reporta_fallos_y_deja_el_arbol_intacto(self):
        antes = self._status()
        r = _correr(
            ROOT, "--ruta", "agents/flechodiezx.md", "--literal", "**Modo rama del usuario",
            "--modo", "borrar", "--test", "tests.test_consistencia.ModoRamaDelUsuarioTests",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        m = re.search(r"^fallos: (\d+) de (\d+)$", r.stdout, re.MULTILINE)
        self.assertIsNotNone(m, r.stdout)
        self.assertGreaterEqual(int(m.group(1)), 1)
        self.assertEqual(self._status(), antes)


if __name__ == "__main__":
    unittest.main()
