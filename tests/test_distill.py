import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import retro_distill  # noqa: E402
import review_distill  # noqa: E402
import timonel_gh as tg  # noqa: E402


def _retro(issue, modulo, est, real, errores):
    return tg.Retro(
        issue=issue, titulo=f"HU {issue}",
        meta={"estimado_sp": str(est), "real_sp": str(real), "precision_estimacion": "subestimado" if real > est else "preciso", "modulo": modulo, "alcance": "Frontend"},
        sections={"Errores recurrentes": errores, "Patrones descubiertos": [], "Mejoras sugeridas": ["x"]},
        labels=[],
    )


def _review(issue, hallazgos):
    return tg.Review(issue=issue, titulo=f"HU {issue}", meta={"veredicto": "APROBADO CON OBSERVACIONES", "criticos": "0", "warnings": str(len(hallazgos)), "modulo": "m", "alcance": "Backend", "bloquea_dod": "no"}, resumen="", hallazgos=hallazgos)


class RetroDistillTests(unittest.TestCase):
    def test_reporte_agrupa_errores_recurrentes(self):
        retros = [_retro(1, "mf", 5, 8, ["Bug de Date"]), _retro(2, "mf", 3, 3, ["bug de date", "otro"])]
        report = retro_distill.generate_report(retros)
        self.assertIn("(2x, ej. #1) bug de date", report)
        self.assertNotIn("(1x", report.split("## Mejoras sugeridas")[0])
        self.assertIn("| mf | Frontend | 2 | 4.0 | 5.5 |", report)
        self.assertTrue(report.startswith("<!-- timonel:insights-retro -->"))


class ReviewDistillTests(unittest.TestCase):
    def test_reporte_archivos_y_convenciones(self):
        h1 = tg.Hallazgo(1, "Convención", "WARNING", "apps/a.ts:1", "Uso de any", "tipar")
        h2 = tg.Hallazgo(1, "Convención", "WARNING", "apps/a.ts:9", "uso de any", "tipar")
        h3 = tg.Hallazgo(2, "Gherkin", "CRITICO", "apps/b.ts:3", "No cumple criterio X", "impl")
        report = review_distill.generate_report([_review(10, [h1]), _review(11, [h2, h3])])
        self.assertIn("(2x en #10, #11) Uso de any", report)
        self.assertIn("(2 historias: #10, #11) apps/a.ts", report)
        self.assertIn("[#11] apps/b.ts:3 — No cumple criterio X", report)


if __name__ == "__main__":
    unittest.main()
