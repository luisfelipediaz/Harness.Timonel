import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import metricas_flujo  # noqa: E402
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


def _issue(number, retro=False, body=None, label_names=None, state="CLOSED",
           created="2026-01-01T00:00:00Z", closed="2026-01-05T00:00:00Z"):
    comments = [{"body": "<!-- timonel:retro -->\n## Retrospectiva"}] if retro else []
    return {
        "number": number,
        "state": state,
        "body": body or f"## Historia {number}",
        "label_names": label_names or ["tipo:hu"],
        "comments": comments,
        "createdAt": created,
        "closedAt": closed,
    }


class MetricasFlujoTests(unittest.TestCase):
    def setUp(self):
        # #26 cerrada sin retro; #27 y #28 cerradas con retro (#27 con 2 derivados, #28 con 0).
        # #33 derivado CLOSED de la retro #29 (HU origen no listada: no hace falta que exista).
        self.cerradas = [
            _issue(26),
            _issue(27, retro=True),
            _issue(28, retro=True),
            _issue(33, body="Origen: retro #29 (1) — luisfelipediaz/Harness.Timonel",
                   label_names=["tipo:hu", "estado:borrador"]),
        ]
        # Dos derivados abiertos de la retro #27: uno en borrador, otro ya refinado (estado:listo).
        self.abiertas = [
            _issue(31, body="Origen: retro #27 (1) — luisfelipediaz/Harness.Timonel",
                   label_names=["tipo:hu", "estado:borrador"], state="OPEN"),
            _issue(32, body="Origen: retro #27 (2) — luisfelipediaz/Harness.Timonel",
                   label_names=["tipo:hu", "estado:listo"], state="OPEN"),
        ]

    def test_calcular_ratchet_agrupa_por_hu_origen_y_bucketiza(self):
        r = metricas_flujo.calcular_ratchet(self.cerradas, self.abiertas)
        self.assertEqual(r["total"], 3)
        self.assertEqual(r["por_origen"], {27: 2, 29: 1})
        self.assertEqual(r["hus_con_retro"], 2)
        self.assertEqual(r["hus_con_derivados"], 1)
        self.assertEqual(r["buckets"], {"borrador": 1, "refinado": 1, "cerrado": 1})

    def test_reporte_ratchet_incluye_tabla_y_porcentaje(self):
        r = metricas_flujo.calcular_ratchet(self.cerradas, self.abiertas)
        rep = metricas_flujo.reporte_ratchet(r)
        self.assertIn("## Ratchet", rep)
        self.assertIn("| #27 | 2 |", rep)
        self.assertIn("1 (50%)", rep)

    def test_reporte_disparos_sin_events_log_dice_sin_datos(self):
        self.assertIn("sin datos", metricas_flujo.reporte_disparos(None))

    def test_reporte_disparos_con_eventos(self):
        rep = metricas_flujo.reporte_disparos({"gh": 3, "raiz-editada": 0})
        self.assertIn("3 eventos", rep)
        self.assertIn("| no |", rep)

    def test_reporte_completo_incluye_secciones_nuevas(self):
        m = metricas_flujo.calcular(self.cerradas, [])
        ratchet = metricas_flujo.calcular_ratchet(self.cerradas, self.abiertas)
        rep = metricas_flujo.reporte(m, ratchet, {"gh": 2, "raiz-editada": 0})
        self.assertTrue(rep.startswith("<!-- timonel:metricas -->"))
        self.assertIn("## Ratchet", rep)
        self.assertIn("## Disparos de hooks", rep)


if __name__ == "__main__":
    unittest.main()
