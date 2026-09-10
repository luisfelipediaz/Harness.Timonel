import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import smoke_harness as sh  # noqa: E402

ISSUE_COMPLETO = {
    "number": 27,
    "label_names": ["tipo:hu", "review:observaciones", "retro:preciso"],
    "comments": [
        {"body": "<!-- timonel:investigacion -->\nhallazgos"},
        {"body": "<!-- timonel:contrato-api -->\ncontrato"},
        {"body": "<!-- timonel:consolidacion -->\nverde"},
        {"body": "<!-- timonel:review -->\nok"},
        {
            "body": (
                "<!-- timonel:retro -->\n## Retrospectiva\n\n"
                "### Issues derivados\n"
                "- luisfelipediaz/Harness.Timonel#33\n"
                "- luisfelipediaz/Harness.Timonel#34\n"
            )
        },
        {"body": "<!-- timonel:dod -->\nDONE"},
    ],
}

DERIVADOS = [
    {"number": 33, "body": "Origen: retro #27 (1) — luisfelipediaz/Harness.Timonel\n\n## Historia"},
    {"number": 34, "body": "Origen: retro #27 (2) — luisfelipediaz/Harness.Timonel\n\n## Historia"},
    # Derivado de otra HU: medir_issue(27) debe descartarlo por el ancla \b.
    {"number": 99, "body": "Origen: retro #28 (1) — luisfelipediaz/Harness.Timonel\n\n## Historia"},
]

COMMITS = ["abc123 feat: x (#27)", "def456 fix: y (#27)", "ghi789 test: z (#27)"]


class MedirIssueTests(unittest.TestCase):
    def test_issue_completo(self):
        m = sh.medir_issue(ISSUE_COMPLETO, DERIVADOS, COMMITS)
        self.assertEqual(m["issue"], 27)
        self.assertEqual(
            m["marcadores"],
            {
                "investigacion": True,
                "contrato-api": True,
                "consolidacion": True,
                "review": True,
                "retro": True,
                "dod": True,
            },
        )
        self.assertEqual(m["review"], "observaciones")
        self.assertEqual(m["retro"], "preciso")
        self.assertEqual(sorted(m["derivados_por_origen"]), [33, 34])
        self.assertEqual(sorted(m["derivados_en_retro"]), [33, 34])
        self.assertEqual(m["commits"], 3)

    def test_issue_vacio(self):
        m = sh.medir_issue({}, [], [])
        self.assertIsNone(m.get("issue"))
        self.assertEqual(
            m["marcadores"],
            {
                "investigacion": False,
                "contrato-api": False,
                "consolidacion": False,
                "review": False,
                "retro": False,
                "dod": False,
            },
        )
        self.assertEqual(m["review"], "")
        self.assertEqual(m["retro"], "")
        self.assertEqual(m["derivados_por_origen"], [])
        self.assertEqual(m["derivados_en_retro"], [])
        self.assertEqual(m["commits"], 0)


class ContarEventosTests(unittest.TestCase):
    def test_entrada_gh_multilinea_cuenta_una_vez(self):
        lineas = [
            '[12:45:51][gh] gh issue edit',
            'REPO="owner/repo"',
            'NUM=19',
        ]
        eventos = sh.contar_eventos(lineas)
        self.assertEqual(eventos["gh"], 1)
        self.assertEqual(eventos["raiz-editada"], 0)

    def test_raiz_editada(self):
        lineas = [
            "10:00:00 raiz-editada apps/api/src/app.module.ts",
            "10:00:05 raiz-editada libs/models/src/index.ts",
        ]
        eventos = sh.contar_eventos(lineas)
        self.assertEqual(eventos["raiz-editada"], 2)
        self.assertEqual(eventos["gh"], 0)

    def test_lista_vacia(self):
        self.assertEqual(sh.contar_eventos([]), {"gh": 0, "raiz-editada": 0})


class TablaDisparosTests(unittest.TestCase):
    def test_eventos_none_dice_sin_datos(self):
        m = sh.medir_issue({}, [], [])
        tabla = sh.tabla_disparos([m], None)
        self.assertIn("sin datos", tabla)

    def test_raiz_editada_en_cero_es_na_perfil_plugin(self):
        m = sh.medir_issue(ISSUE_COMPLETO, DERIVADOS, COMMITS)
        tabla = sh.tabla_disparos([m], {"gh": 5, "raiz-editada": 0})
        self.assertIn("N/A en perfil plugin", tabla)
        self.assertNotIn("| no |", tabla.split("hook `raiz-editada`")[1].split("\n")[0])

    def test_gh_positivo_y_derivados_marcan_si(self):
        m = sh.medir_issue(ISSUE_COMPLETO, DERIVADOS, COMMITS)
        tabla = sh.tabla_disparos([m], {"gh": 5, "raiz-editada": 0})
        self.assertIn("sí", tabla)


if __name__ == "__main__":
    unittest.main()
