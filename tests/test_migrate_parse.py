import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import migrate_backlog as mb  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "user-stories"


class BacklogParseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backlog = mb.parse_backlog(FIX / "BACKLOG.md")

    def test_epicas_y_conteo(self):
        self.assertEqual(len(self.backlog.epicas), 10)
        self.assertEqual(self.backlog.epicas[0].numero, 1)
        self.assertEqual(self.backlog.epicas[0].titulo, "Infraestructura del Modulo Mis Finanzas")
        self.assertEqual(len(self.backlog.historias), 87)  # el resumen del BACKLOG dice 77 pero hay 87 lineas

    def test_linea_pendiente(self):
        hu = self.backlog.por_id["HU-011"]
        self.assertFalse(hu.completada)
        self.assertEqual(hu.moscow, "should")
        self.assertEqual(hu.sp, 8)
        self.assertEqual(hu.epica, 3)
        self.assertEqual(hu.ruta, "epica-3-gestion-gastos/hu-011-deuda-tarjeta-credito.md")

    def test_linea_tachada_reemplazada(self):
        hu = self.backlog.por_id["HU-004"]
        self.assertTrue(hu.completada)
        self.assertTrue(hu.obsoleta)
        self.assertEqual(hu.nota, "Reemplazada por HU-054")
        self.assertIsNone(hu.sp)

    def test_completada_en_consolidado(self):
        hu = self.backlog.por_id["HU-001"]
        self.assertTrue(hu.completada)
        self.assertTrue(hu.ruta.endswith("completadas.md"))


class SpecTests(unittest.TestCase):
    def test_spec_individual(self):
        spec = mb.load_spec(FIX, "epica-9-ajustar-ingreso-nomina/hu-097-esquema-endpoint-upsert-nomina.md", "HU-097")
        self.assertTrue(spec.titulo.startswith("Persistir el ingreso de nomina"))
        self.assertEqual(spec.ficha["Alcance"], "Backend")
        self.assertEqual(spec.ficha["Modulo destino"], "mis-finanzas")
        self.assertEqual(spec.prioridad, "alta")
        self.assertEqual(spec.dependencias, [])

    def test_spec_desde_completadas(self):
        spec = mb.load_spec(FIX, "epica-1-infraestructura/completadas.md", "HU-001")
        self.assertEqual(spec.titulo, "Estructura base del modulo Angular + API")
        self.assertIn("DADO QUE el empleado esta autenticado", spec.cuerpo)
        self.assertNotIn("## HU-002:", spec.cuerpo)

    def test_dependencias_parseadas(self):
        spec = mb.load_spec(FIX, "epica-9-ajustar-ingreso-nomina/hu-098-algoritmo-sincronizacion-frontend.md", "HU-098")
        self.assertIn("HU-097", spec.dependencias)


class BodyTests(unittest.TestCase):
    def test_body_canonico(self):
        backlog = mb.parse_backlog(FIX / "BACKLOG.md")
        hu = backlog.por_id["HU-097"]
        spec = mb.load_spec(FIX, hu.ruta, hu.id)
        body = mb.build_body(hu, spec, {"HU-097": 5, "HU-098": 6})
        self.assertTrue(body.startswith("Id histórico: HU-097"))
        for seccion in ("## Historia", "## Criterios de aceptación", "## Ficha técnica", "## Endpoints", "## Modelos compartidos", "## Dependencias", "## Tareas"):
            self.assertIn(seccion, body, seccion)
        self.assertNotIn("**MoSCoW:**", body)
        self.assertNotIn("**Story Points:**", body)
        self.assertIn("- [x] Backend", body)          # completada → tareas marcadas
        self.assertIn("- [x] Definition of Done", body)

    def test_dependencias_mapeadas_a_issues(self):
        backlog = mb.parse_backlog(FIX / "BACKLOG.md")
        hu = backlog.por_id["HU-098"]
        spec = mb.load_spec(FIX, hu.ruta, hu.id)
        body = mb.build_body(hu, spec, {"HU-097": 5})
        self.assertIn("Depende de #5", body)

    def test_labels(self):
        backlog = mb.parse_backlog(FIX / "BACKLOG.md")
        hu = backlog.por_id["HU-097"]
        spec = mb.load_spec(FIX, hu.ruta, hu.id)
        labels = mb.build_labels(hu, spec, modulos={"mis-finanzas"})
        self.assertEqual(set(labels), {"tipo:hu", "alcance:backend", "moscow:should", "sp:5", "prioridad:alta", "mod:mis-finanzas"})

    def test_labels_pendiente_lleva_estado(self):
        backlog = mb.parse_backlog(FIX / "BACKLOG.md")
        hu = backlog.por_id["HU-011"]
        labels = mb.build_labels(hu, mb.Spec(titulo="x", cuerpo="", ficha={"Alcance": "Full-stack"}, prioridad="", dependencias=[]), modulos=set())
        self.assertIn("estado:listo", labels)
        self.assertNotIn("mod:", " ".join(labels))


class RetroConversionTests(unittest.TestCase):
    def test_retro_md_a_comentario(self):
        texto = (FIX / "epica-9-ajustar-ingreso-nomina/hu-098-algoritmo-sincronizacion-frontend.retro.md").read_text()
        comentario = mb.retro_file_to_comment(texto)
        self.assertTrue(comentario.startswith("<!-- timonel:retro -->"))
        self.assertIn("estimado_sp: 8", comentario)
        self.assertIn("### Errores recurrentes", comentario)
        self.assertNotIn("historia: HU-098", comentario)


if __name__ == "__main__":
    unittest.main()
