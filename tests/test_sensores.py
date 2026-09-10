import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import contrato_check as cc  # noqa: E402
import cosechar_retro as cr  # noqa: E402
import dor_check as dc  # noqa: E402
import estado_historia as eh  # noqa: E402
import metricas_flujo as mf  # noqa: E402
import validar_marcador as vm  # noqa: E402
from test_markers import RETRO_COMMENT, REVIEW_COMMENT  # noqa: E402

HU_OK = {
    "number": 42, "title": "Registrar gasto con categoría", "parent": {"number": 3},
    "label_names": ["tipo:hu", "estado:listo", "alcance:full-stack", "sp:5", "mod:mis-finanzas", "moscow:must", "prioridad:alta"],
    "body": """## Historia

**Como** empleado, **quiero** registrar un gasto, **para** controlar mis finanzas.

## Criterios de aceptación

```gherkin
DADO QUE estoy en el dashboard
CUANDO registro un gasto
ENTONCES aparece en la lista
```

## Ficha técnica

| Campo | Valor |
| --- | --- |
| Alcance | Full-stack |
| Módulo destino | mis-finanzas |

## Endpoints

- `POST /api/mis-finanzas/gastos`

## Modelos compartidos

- `Gasto { monto: number }`

## Dependencias

Ninguna

## Tareas

- [x] Contrato API aprobado
- [x] Modelos compartidos
- [x] Backend
- [ ] Frontend
- [ ] Consolidación (lint + tests)
- [ ] Code review
- [ ] Retrospectiva
- [ ] Definition of Done
""",
}


class ValidarMarcadorTests(unittest.TestCase):
    def test_review_valido(self):
        self.assertEqual(vm.validar(REVIEW_COMMENT), [])

    def test_retro_sin_harness_engineering_falla(self):
        problemas = vm.validar(RETRO_COMMENT)
        self.assertTrue(any("Harness engineering" in p for p in problemas))

    def test_retro_completa_valida(self):
        retro = RETRO_COMMENT.replace("precision_estimacion: subestimado", "precision_estimacion: subestimado") + "\n### Harness engineering\n\n- ¿Surgió un patrón repetitivo? → Ninguno\n"
        self.assertEqual(vm.validar(retro), [])

    def test_review_inconsistente(self):
        malo = REVIEW_COMMENT.replace("warnings: 2", "warnings: 1").replace("bloquea_dod: no", "bloquea_dod: si")
        problemas = vm.validar(malo)
        self.assertTrue(any("no coincide con la tabla" in p for p in problemas))
        self.assertTrue(any("bloquea_dod" in p for p in problemas))

    def test_precision_incoherente(self):
        malo = RETRO_COMMENT.replace("precision_estimacion: subestimado", "precision_estimacion: preciso") + "\n### Harness engineering\n- Ninguno\n"
        self.assertTrue(any("deberia ser `subestimado`" in p for p in vm.validar(malo)))

    def test_sin_marcador(self):
        self.assertIn("la primera linea debe ser el marcador `<!-- timonel:<tipo> -->`", vm.validar("hola"))


DOD_OK = """<!-- timonel:dod -->
## Definition of Done

```yaml
fecha: 2026-09-10
decision: DONE
```

| # | Item | Estado |
| --- | --- | --- |
""" + "\n".join(f"| {i} | Item {i} | {'SKIPPED' if i in (5, 7) else 'PASSED'} |" for i in range(1, 12)) + """

Item 11 · veredicto: APROBADO

### Decisión final

**DONE**
"""


class ValidarDodTests(unittest.TestCase):
    def test_dod_completo_valido(self):
        self.assertEqual(vm.validar(DOD_OK), [])

    def test_dod_con_6_filas_y_review_skipped_es_invalido(self):
        malo = "<!-- timonel:dod -->\n## DoD\n\n```yaml\nfecha: 2026-09-10\ndecision: DONE\n```\n\n| # | Item | Estado |\n| --- | --- | --- |\n| 1 | a | PASSED |\n| 2 | b | PASSED |\n| 4 | c | PASSED |\n| 8 | d | PASSED |\n| 10 | e | PASSED |\n| 11 | Code review | SKIPPED |\n\n### Decisión final\n**DONE**\n"
        problemas = vm.validar(malo)
        self.assertTrue(any("11 filas" in p for p in problemas))
        self.assertTrue(any("Item 11 · veredicto" in p for p in problemas))
        self.assertTrue(any("fila 11 en PASSED" in p for p in problemas))


class DorCheckTests(unittest.TestCase):
    def test_hu_completa(self):
        self.assertEqual(dc.check(HU_OK), [])
        self.assertEqual(dc.check(HU_OK, "implementar"), [])

    def test_faltan_labels_y_secciones(self):
        hu = dict(HU_OK, label_names=["tipo:hu", "estado:borrador"], body=HU_OK["body"].replace("## Tareas", "## Otras"))
        faltantes = dc.check(hu, "implementar")
        self.assertTrue(any("`alcance:*`" in f for f in faltantes))
        self.assertTrue(any("Tareas" in f for f in faltantes))
        self.assertTrue(any("estado:listo" in f for f in faltantes))

    def test_por_definir_y_sp_grande(self):
        hu = dict(HU_OK, label_names=[l if not l.startswith("sp:") else "sp:21" for l in HU_OK["label_names"]], body=HU_OK["body"] + "\nPOR DEFINIR")
        faltantes = dc.check(hu)
        self.assertTrue(any("POR DEFINIR" in f for f in faltantes))
        self.assertTrue(any("supera el maximo" in f for f in faltantes))

    def test_hotfix_con_endpoints_no_es_hotfix(self):
        hf = dict(HU_OK, label_names=["tipo:hotfix", "estado:listo", "alcance:backend", "sp:2", "mod:x"])
        self.assertTrue(any("Ninguno" in f for f in dc.check(hf)))

    def test_hu_sin_padre(self):
        hu = dict(HU_OK, parent=None)
        self.assertTrue(any("sub-issue" in f for f in dc.check(hu)))

    def test_bloqueado_impide_implementar(self):
        hu = dict(HU_OK, label_names=HU_OK["label_names"] + ["bloqueado"])
        self.assertEqual(dc.check(hu), [])
        self.assertTrue(any("bloqueado" in f for f in dc.check(hu, "implementar")))


class EstadoHistoriaTests(unittest.TestCase):
    def test_reanuda_en_frontend(self):
        issue = dict(HU_OK, state="OPEN", comments=[{"body": "<!-- timonel:investigacion -->\nx"}, {"body": "<!-- timonel:contrato-api -->\nx"}])
        e = eh.estado(issue, rama="hu/42-registrar-gasto")
        self.assertEqual(e["reanudar_en"], "3 Frontend")
        self.assertIn("2 Contrato API", e["fases_hechas"])
        self.assertFalse(e["nueva"])

    def test_historia_nueva(self):
        body = HU_OK["body"].replace("- [x]", "- [ ]")
        issue = dict(HU_OK, body=body, state="OPEN", comments=[], label_names=[l for l in HU_OK["label_names"]])
        e = eh.estado(issue, rama=None)
        self.assertTrue(e["nueva"])
        self.assertEqual(e["reanudar_en"], "1.5 Investigacion")

    def test_alcance_backend_salta_frontend(self):
        issue = dict(HU_OK, state="OPEN", comments=[{"body": "<!-- timonel:investigacion -->"}], label_names=[l.replace("full-stack", "backend") for l in HU_OK["label_names"]])
        e = eh.estado(issue, rama="hu/42-x")
        self.assertNotIn("3 Frontend", e["fases_pendientes"])
        self.assertEqual(e["reanudar_en"], "4-5 Consolidacion")


    def test_cerrada_no_reanuda(self):
        issue = dict(HU_OK, state="CLOSED", comments=[{"body": "<!-- timonel:dod -->\nx"}])
        e = eh.estado(issue, rama=None)
        self.assertEqual(e["reanudar_en"], "cerrar")
        self.assertFalse(e["nueva"])

    def test_nueva_backend_sin_tareas(self):
        body = HU_OK["body"].replace("- [x]", "- [ ]")
        issue = dict(HU_OK, body=body, state="OPEN", comments=[], label_names=[l.replace("full-stack", "backend").replace("estado:listo", "estado:listo") for l in HU_OK["label_names"]])
        e = eh.estado(issue, rama=None)
        self.assertTrue(e["nueva"], "una HU backend sin trabajo debe ser nueva aunque Frontend cuente como N/A")


class CosecharRetroTests(unittest.TestCase):
    def test_extrae_mejoras_y_omite_ninguno(self):
        retro = RETRO_COMMENT + "\n### Harness engineering\n\n- ¿Surgió un patrón repetitivo? → Ninguno\n- ¿Un proceso manual se ejecutó 2+ veces? → Agregar hook que corra prettier tras Edit\n"
        items = cr.extraer_mejoras(retro)
        self.assertEqual(items, [("mejora", "Documentar Date.setMonth en heuristicas."), ("harness", "Agregar hook que corra prettier tras Edit")])

    def test_destino(self):
        self.assertEqual(cr.destino("Agregar en el skill ngrx-signal-store una nota sobre rxMethod"), "plugin")
        self.assertEqual(cr.destino("Agregar en CLAUDE.md la recomendación de state machine con flag"), "consumidor")

    def test_titulo_recortado(self):
        self.assertLessEqual(len(cr._titulo("x" * 100)), 70)


class ContratoCheckTests(unittest.TestCase):
    def test_extrae_y_verifica(self):
        contrato = "Metodo: POST\nRuta:   /api/mis-finanzas/ingreso-nomina/upsert\nMetodo: GET\nRuta: /api/mis-finanzas/movimientos/:id"
        endpoints = cc.extraer_endpoints(contrato)
        self.assertEqual(len(endpoints), 2)
        indice = [("apps/api/x.controller.ts", "mis-finanzas", [("POST", "ingreso-nomina/upsert"), ("GET", "movimientos/:movimientoId")])]
        res = cc.verificar(endpoints, indice)
        self.assertEqual([r[2] for r in res], ["PASSED", "PASSED"])
        res2 = cc.verificar([("DELETE", "/api/mis-finanzas/movimientos/:id")], indice)
        self.assertEqual(res2[0][2], "FAILED")

    def test_query_string_no_rompe(self):
        indice = [("c.ts", "organigrama", [("GET", "empleados")])]
        res = cc.verificar([("GET", "/api/organigrama/empleados?area=1&sede=2")], indice)
        self.assertEqual(res[0][2], "PASSED")


class MetricasTests(unittest.TestCase):
    def test_calcula_cobertura_y_lead_time(self):
        cerradas = [
            {"number": 1, "label_names": ["tipo:hu", "review:aprobado", "retro:preciso"], "comments": [{"body": REVIEW_COMMENT}, {"body": RETRO_COMMENT}], "createdAt": "2026-09-01T00:00:00Z", "closedAt": "2026-09-03T00:00:00Z"},
            {"number": 2, "label_names": ["tipo:hu"], "comments": [], "createdAt": "2026-09-01T00:00:00Z", "closedAt": "2026-09-02T00:00:00Z"},
        ]
        abiertas = [{"number": 3, "label_names": ["tipo:hu", "estado:listo", "bloqueado"], "comments": []}]
        m = mf.calcular(cerradas, abiertas)
        self.assertEqual(m["cobertura"]["review"], 1)
        self.assertEqual(m["review"]["aprobado"], 1)
        self.assertAlmostEqual(m["lead_time_prom"], 1.5)
        self.assertEqual(m["bloqueadas"], 1)
        self.assertIn("50%", mf.reporte(m))


if __name__ == "__main__":
    unittest.main()
