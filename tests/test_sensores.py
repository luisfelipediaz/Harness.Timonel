import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import contrato_check as cc  # noqa: E402
import cosechar_retro as cr  # noqa: E402
import dor_check as dc  # noqa: E402
import estado_historia as eh  # noqa: E402
import eval_dor as ed  # noqa: E402
import integracion as ig  # noqa: E402
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

    def test_dod_done_con_veredicto_11_no_generado_es_invalido(self):
        # Fila 11 dice PASSED pero la linea de veredicto dice NO_GENERADO: el
        # sensor no debe confiar solo en el estado de la fila (gap de #28).
        malo = DOD_OK.replace("Item 11 · veredicto: APROBADO", "Item 11 · veredicto: NO_GENERADO")
        problemas = vm.validar(malo)
        self.assertTrue(any("NO_GENERADO" in p for p in problemas))

    def test_dod_done_con_veredicto_11_skipped_es_invalido(self):
        malo = DOD_OK.replace("Item 11 · veredicto: APROBADO", "Item 11 · veredicto: SKIPPED")
        problemas = vm.validar(malo)
        self.assertTrue(any("SKIPPED" in p for p in problemas))

    def test_dod_perfil_plugin_con_fila_9_failed_es_invalido(self):
        malo = (
            DOD_OK.replace("decision: DONE\n```", "decision: DONE\nperfil: plugin\n```")
            .replace("| 9 | Item 9 | PASSED |", "| 9 | Item 9 | FAILED |")
        )
        problemas = vm.validar(malo)
        self.assertTrue(any("fila 9" in p for p in problemas))

    def test_dod_perfil_consumidor_con_fila_9_failed_y_pendientes_es_valido(self):
        bueno = (
            DOD_OK.replace("decision: DONE\n```", "decision: PENDIENTES\nperfil: consumidor\n```")
            .replace("| 9 | Item 9 | PASSED |", "| 9 | Item 9 | FAILED |")
        )
        self.assertEqual(vm.validar(bueno), [])

    def test_dod_perfil_desconocido_es_invalido(self):
        malo = DOD_OK.replace("decision: DONE\n```", "decision: DONE\nperfil: otro\n```")
        problemas = vm.validar(malo)
        self.assertTrue(any("perfil" in p for p in problemas))

    def test_dod_ok_con_perfil_consumidor_explicito_sigue_valido(self):
        bueno = DOD_OK.replace("decision: DONE\n```", "decision: DONE\nperfil: consumidor\n```")
        self.assertEqual(vm.validar(bueno), [])

    def test_dod_ok_sin_perfil_sigue_valido_por_retrocompatibilidad(self):
        # DOD_OK ya no declara `perfil`: los DoD historicos deben seguir siendo validos.
        self.assertNotIn("perfil", vm.parse_yaml_plano(DOD_OK))
        self.assertEqual(vm.validar(DOD_OK), [])


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


class EvalDorTests(unittest.TestCase):
    """Sensor del eval del planner (#32): DoR sobre la HU devuelta en la respuesta del agente."""

    def _respuesta(self, body: str, labels: str | None = "tipo:hu, alcance:full-stack, sp:5, mod:mis-finanzas, moscow:must, prioridad:alta") -> str:
        texto = f"Aca va la HU propuesta:\n\n```markdown\n{body}```\n"
        if labels is not None:
            texto += f"\nLabels: {labels}\n"
        return texto

    def test_extraer_hu_de_bloque_markdown_y_labels(self):
        hu = ed.extraer_hu(self._respuesta(HU_OK["body"]))
        self.assertEqual(hu["body"], HU_OK["body"])
        self.assertEqual(
            hu["label_names"],
            ["tipo:hu", "alcance:full-stack", "sp:5", "mod:mis-finanzas", "moscow:must", "prioridad:alta"],
        )
        self.assertEqual(len(hu["label_names"]), 6)
        self.assertEqual(hu["title"], "")

    def test_extraer_hu_sin_bloque_usa_todo_el_texto(self):
        hu = ed.extraer_hu("texto plano sin fences", title="Registrar gasto")
        self.assertEqual(hu["body"], "texto plano sin fences")
        self.assertEqual(hu["title"], "Registrar gasto")
        self.assertEqual(hu["label_names"], [])

    def test_evaluar_hu_completa_cumple_dor(self):
        self.assertEqual(ed.evaluar(self._respuesta(HU_OK["body"])), [])

    def test_evaluar_reporta_faltantes_si_falta_seccion_o_label(self):
        cuerpo_sin_tareas = HU_OK["body"].split("## Tareas")[0]
        faltantes = ed.evaluar(self._respuesta(
            cuerpo_sin_tareas,
            labels="tipo:hu, alcance:full-stack, mod:mis-finanzas, moscow:must, prioridad:alta",
        ))
        self.assertTrue(faltantes)
        self.assertTrue(any("Tareas" in f for f in faltantes))
        self.assertTrue(any("sp:" in f for f in faltantes))

    def test_evaluar_sin_labels_reporta_falta_label(self):
        faltantes = ed.evaluar(self._respuesta(HU_OK["body"], labels=None))
        self.assertTrue(any("label" in f for f in faltantes))


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

    COMENTARIOS_HASTA_DOD = [{"body": "<!-- timonel:investigacion -->\nx"}, {"body": "<!-- timonel:dod -->\nx"}]
    COMENTARIOS_SIN_DOD = [{"body": "<!-- timonel:investigacion -->\nx"}]

    def test_pr_pendiente_antes_de_dod(self):
        """Con el DoD y el PR ambos pendientes, la fase activa es 6.5 PR/Integración: el PR se abre antes del DoD."""
        body = HU_OK["body"].replace(
            "- [ ] Frontend\n- [ ] Consolidación (lint + tests)\n- [ ] Code review\n- [ ] Retrospectiva\n- [ ] Definition of Done",
            "- [x] Frontend\n- [x] Consolidación (lint + tests)\n- [x] Code review\n- [x] Retrospectiva\n- [ ] Definition of Done\n- [ ] PR abierto",
        )
        issue = dict(HU_OK, body=body, state="OPEN", comments=self.COMENTARIOS_SIN_DOD)
        e = eh.estado(issue, rama="hu/42-registrar-gasto")
        self.assertEqual(e["reanudar_en"], "6.5 PR/Integración")
        self.assertFalse(e["nueva"])

    def test_pr_marcado_dod_pendiente(self):
        """Con el PR ya marcado pero el DoD pendiente, la fase activa es 7 Definition of Done."""
        body = HU_OK["body"].replace(
            "- [ ] Frontend\n- [ ] Consolidación (lint + tests)\n- [ ] Code review\n- [ ] Retrospectiva\n- [ ] Definition of Done",
            "- [x] Frontend\n- [x] Consolidación (lint + tests)\n- [x] Code review\n- [x] Retrospectiva\n- [ ] Definition of Done\n- [x] PR abierto",
        )
        issue = dict(HU_OK, body=body, state="OPEN", comments=self.COMENTARIOS_SIN_DOD)
        e = eh.estado(issue, rama="hu/42-registrar-gasto")
        self.assertEqual(e["reanudar_en"], "7 Definition of Done")

    def test_sin_linea_pr_es_skipped(self):
        body = HU_OK["body"].replace("- [ ]", "- [x]")
        issue = dict(HU_OK, body=body, state="OPEN", comments=self.COMENTARIOS_HASTA_DOD)
        e = eh.estado(issue, rama="hu/42-registrar-gasto")
        self.assertEqual(e["reanudar_en"], "cerrar")
        self.assertIn("6.5 PR/Integración", e["fases_hechas"])


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


class IntegracionTests(unittest.TestCase):
    def test_tipo_remote_github(self):
        for url in ("https://github.com/o/r.git", "git@github.com:o/r.git"):
            self.assertEqual(ig.tipo_remote(url), "github")

    def test_tipo_remote_azure_devops(self):
        urls = (
            "https://dev.azure.com/org/proj/_git/repo",
            "https://org.visualstudio.com/proj/_git/repo",
            "git@ssh.dev.azure.com:v3/org/proj/repo",
        )
        for url in urls:
            self.assertEqual(ig.tipo_remote(url), "azure-devops")

    def test_tipo_remote_desconocido(self):
        self.assertEqual(ig.tipo_remote("https://gitlab.com/o/r"), "desconocido")

    def test_comando_pr_github(self):
        cmd = ig.comando_pr("https://github.com/o/r.git", "hu/31-x", "main", "Titulo (#31)", "/tmp/pr-31.md")
        for esperado in ("gh pr create", "--head hu/31-x", "--base main", "(#31)"):
            self.assertIn(esperado, cmd)

    def test_comando_pr_azure_devops(self):
        cmd = ig.comando_pr("https://dev.azure.com/org/proj/_git/repo", "hu/31-x", "main", "Titulo (#31)", "/tmp/pr-31.md")
        for esperado in ("az repos pr create", "--source-branch hu/31-x", "--organization https://dev.azure.com/org", "--project proj", "--repository repo"):
            self.assertIn(esperado, cmd)

    def test_comando_pr_visualstudio(self):
        cmd = ig.comando_pr("https://org.visualstudio.com/proj/_git/repo", "hu/31-x", "main", "Titulo (#31)", "/tmp/pr-31.md")
        self.assertIn("--organization https://org.visualstudio.com", cmd)

    def test_comando_pr_azure_ssh(self):
        cmd = ig.comando_pr("git@ssh.dev.azure.com:v3/org/proj/repo", "hu/31-x", "main", "Titulo (#31)", "/tmp/pr-31.md")
        for esperado in ("az repos pr create", "--organization https://dev.azure.com/org", "--project proj", "--repository repo"):
            self.assertIn(esperado, cmd)

    def test_comando_pr_escapa_titulo_con_apostrofo(self):
        import shlex
        titulo = "Fase 8: abrir el PR de 'hu/N-slug' y registrarlo (#31)"
        for url in ("https://github.com/o/r.git", "https://dev.azure.com/org/proj/_git/repo"):
            cmd = ig.comando_pr(url, "hu/31-x", "main", titulo, "/tmp/pr-31.md")
            partes = shlex.split(cmd)
            self.assertIn(titulo, partes, "el titulo debe sobrevivir intacto a shlex.split (eval en la Fase 8)")

    def test_comando_pr_azure_no_usa_command_substitution(self):
        cmd = ig.comando_pr("https://dev.azure.com/org/proj/_git/repo", "hu/31-x", "main", "Titulo (#31)", "/tmp/pr-31.md")
        self.assertNotIn("$(", cmd)
        self.assertIn("--description @/tmp/pr-31.md", cmd)

    def test_comando_pr_desconocido_lanza(self):
        with self.assertRaises(ValueError):
            ig.comando_pr("https://gitlab.com/o/r", "hu/31-x", "main", "Titulo (#31)", "/tmp/pr-31.md")

    def test_cuerpo_pr_sin_contrato(self):
        cuerpo = ig.cuerpo_pr(31, "luisfelipediaz/Harness.Timonel", "Titulo", None, DOD_OK)
        self.assertIn("Cierra #31", cuerpo)
        self.assertIn("Sin contrato publicado", cuerpo)
        self.assertIn("| 1 |", cuerpo)

    def test_cuerpo_pr_corta_en_seccion_hermana_y_prefiere_contrato_de_cambio(self):
        contrato = ("<!-- timonel:contrato-api -->\n## Contrato API aprobado\n\n### Modelos compartidos\n\nNinguno.\n\n"
                    "### Endpoints\n\nNinguno — explícito.\n\n### Contrato de cambio\n\n| Archivo | Cambio |\n| --- | --- |\n| a.py | x |\n\n"
                    "### Invariantes nuevas\n\n- una invariante\n")
        cuerpo = ig.cuerpo_pr(31, "o/r", "Titulo", contrato, None)
        self.assertIn("| a.py | x |", cuerpo)
        self.assertNotIn("una invariante", cuerpo)
        self.assertNotIn("Ninguno — explícito", cuerpo)

    def test_cuerpo_pr_sin_dod(self):
        cuerpo = ig.cuerpo_pr(31, "luisfelipediaz/Harness.Timonel", "Titulo", "### Contrato de cambio\n\nTabla.", None)
        self.assertIn("DoD pendiente", cuerpo)
        self.assertNotIn("Sin DoD publicado", cuerpo)
        self.assertIn("Tabla.", cuerpo)

    def test_cuerpo_pr_emite_keyword_de_cierre_real(self):
        cuerpo = ig.cuerpo_pr(31, "o/r", "Titulo", None, None)
        self.assertIn("Closes #31", cuerpo, "la keyword real de GitHub debe estar presente, no solo 'Cierra #N' en prosa")

    def test_cuerpo_pr_dod_none_contiene_keyword_contrato_y_dod_pendiente(self):
        contrato = "### Contrato de cambio\n\n| Archivo | Cambio |\n| --- | --- |\n| agents/flechodiezx.md | Fase 6.5 nueva |\n"
        cuerpo = ig.cuerpo_pr(80, "o/r", "Titulo", contrato, None)
        self.assertIn("Closes #80", cuerpo)
        self.assertIn("agents/flechodiezx.md", cuerpo)
        self.assertIn("DoD pendiente", cuerpo)

    def test_cuerpo_pr_con_dod_con_filas_sigue_rindiendo_tabla(self):
        cuerpo = ig.cuerpo_pr(31, "luisfelipediaz/Harness.Timonel", "Titulo", None, DOD_OK)
        self.assertIn("| 1 |", cuerpo)
        self.assertNotIn("DoD pendiente", cuerpo)


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
        self.assertIn("50%", mf.reporte(m, mf.calcular_ratchet(cerradas, abiertas), None))


if __name__ == "__main__":
    unittest.main()
