import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import timonel_gh as tg  # noqa: E402

RETRO_COMMENT = """<!-- timonel:retro -->
## Retrospectiva

```yaml
fecha: 2026-09-09
estimado_sp: 8
real_sp: 13
precision_estimacion: subestimado
alcance: Frontend
modulo: mis-finanzas
```

### Desviaciones

- La spec sugeria setMonth; se uso aritmetica modular.

### Errores recurrentes

- Bug de overflow de Date con dia 31.
- flushMicrotasks(6) para estabilizar asserts.

### Patrones descubiertos

- Ninguno

### Mejoras sugeridas

- Documentar Date.setMonth en heuristicas.
"""

REVIEW_COMMENT = """<!-- timonel:review -->
## Code review

```yaml
fecha: 2026-09-09
veredicto: APROBADO CON OBSERVACIONES
criticos: 0
warnings: 2
alcance: Full-stack
modulo: prestamos
bloquea_dod: no
```

### Resumen

La historia implementa correctamente el alta. Dos observaciones.

### Hallazgos

| #   | Tipo       | Severidad | Archivo:Línea                    | Descripción                       | Sugerencia              |
| --- | ---------- | --------- | -------------------------------- | --------------------------------- | ----------------------- |
| 1   | Convención | WARNING   | apps/client/x.component.html:22  | Uso de *ngIf                      | Reemplazar por @if      |
| 2   | Heurística | WARNING   | libs/modelos/prestamo-response.ts | Tipo espejo                      | Eliminar                |

### Veredicto

**APROBADO CON OBSERVACIONES** — 0 CRITICO, 2 WARNING.
"""

ISSUE = {"number": 42, "title": "Registrar prestamo", "label_names": ["tipo:hu", "mod:prestamos", "alcance:full-stack", "sp:5"]}


class YamlPlanoTests(unittest.TestCase):
    def test_extrae_pares(self):
        meta = tg.parse_yaml_plano(RETRO_COMMENT)
        self.assertEqual(meta["estimado_sp"], "8")
        self.assertEqual(meta["precision_estimacion"], "subestimado")

    def test_sin_bloque_devuelve_vacio(self):
        self.assertEqual(tg.parse_yaml_plano("sin yaml"), {})


class MarkerTests(unittest.TestCase):
    def test_encuentra_ultimo_comentario_con_marcador(self):
        comments = [{"body": "hola"}, {"body": RETRO_COMMENT}, {"body": "<!-- timonel:review -->\nx"}]
        self.assertEqual(tg.find_marker_comment(comments, "retro"), RETRO_COMMENT)
        self.assertIsNone(tg.find_marker_comment(comments, "dod"))


class RetroTests(unittest.TestCase):
    def test_retro_desde_comentario(self):
        retro = tg.retro_from_comment(ISSUE, RETRO_COMMENT)
        self.assertEqual(retro.issue, 42)
        self.assertEqual(retro.estimado_sp, 8)
        self.assertEqual(retro.real_sp, 13)
        self.assertEqual(retro.precision, "subestimado")
        self.assertEqual(retro.modulo, "mis-finanzas")
        self.assertEqual(len(retro.sections["Errores recurrentes"]), 2)
        self.assertEqual(retro.sections["Patrones descubiertos"], [])

    def test_modulo_cae_a_label_si_yaml_no_lo_trae(self):
        cuerpo = RETRO_COMMENT.replace("modulo: mis-finanzas\n", "")
        retro = tg.retro_from_comment(ISSUE, cuerpo)
        self.assertEqual(retro.modulo, "prestamos")


class ReviewTests(unittest.TestCase):
    def test_review_desde_comentario(self):
        review = tg.review_from_comment(ISSUE, REVIEW_COMMENT)
        self.assertEqual(review.veredicto, "APROBADO CON OBSERVACIONES")
        self.assertEqual(review.warnings, 2)
        self.assertFalse(review.bloquea_dod)
        self.assertEqual(len(review.hallazgos), 2)
        self.assertEqual(review.hallazgos[0].tipo_normalizado, "Convencion")
        self.assertEqual(review.hallazgos[1].archivo, "libs/modelos/prestamo-response.ts")
        self.assertTrue(review.resumen.startswith("La historia implementa"))

    def test_sin_hallazgos(self):
        cuerpo = REVIEW_COMMENT.split("### Hallazgos")[0] + "### Hallazgos\n\nSin hallazgos.\n\n### Veredicto\n\n**APROBADO**\n"
        review = tg.review_from_comment(ISSUE, cuerpo)
        self.assertEqual(review.hallazgos, [])


if __name__ == "__main__":
    unittest.main()
