"""Test de consistencia entre artefactos del plugin (gap 2/13 de la auditoria #11, issue #14).

Detecta drift: agentes referenciados por commands que no existen, skills declarados en
agentes que no existen, marcadores usados por skills/agentes que no estan documentados en
marcadores.md ni en timonel_gh.py, version de plugin.json distinta de la del CHANGELOG,
y comandos sin frontmatter completo.
"""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import timonel_gh as tg  # noqa: E402

AGENTES = {p.stem for p in (ROOT / "agents").glob("*.md")}
SKILLS = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
COMMANDS = list((ROOT / "commands").glob("*.md"))


def _frontmatter(path: Path) -> dict:
    texto = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", texto, re.DOTALL)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            k, sep, v = line.partition(":")
            if sep and not line.startswith(" "):
                fm[k.strip()] = v.strip()
    return fm


class AgentesYCommandsTests(unittest.TestCase):
    def test_commands_referencian_agentes_existentes(self):
        for cmd in COMMANDS:
            for ref in re.findall(r'subagent_type:\s*"timonel:([a-z0-9-]+)"', cmd.read_text(encoding="utf-8")):
                self.assertIn(ref, AGENTES, f"{cmd.name} referencia agente inexistente `{ref}`")

    def test_agentes_referenciados_en_texto_existen(self):
        marcadores = set(re.findall(r"## `timonel:([a-z-]+)`", (ROOT / "skills/github-issues/references/marcadores.md").read_text(encoding="utf-8")))
        conocidos = AGENTES | marcadores | {"sdd"}
        for f in list((ROOT / "agents").glob("*.md")) + COMMANDS + list((ROOT / "skills").glob("*/SKILL.md")):
            for ref in re.findall(r"`timonel:([a-z0-9-]+)`", f.read_text(encoding="utf-8")):
                self.assertIn(ref, conocidos, f"{f} referencia `timonel:{ref}` inexistente")

    def test_agentes_declaran_skills_existentes(self):
        for a in (ROOT / "agents").glob("*.md"):
            texto = a.read_text(encoding="utf-8")
            m = re.search(r"^skills:\n((?:\s+-\s+.+\n)+)", texto, re.MULTILINE)
            if m:
                for s in re.findall(r"-\s+([a-z0-9-]+)", m.group(1)):
                    self.assertIn(s, SKILLS, f"{a.name} declara skill inexistente `{s}`")

    def test_frontmatter_de_agentes(self):
        for a in (ROOT / "agents").glob("*.md"):
            fm = _frontmatter(a)
            self.assertEqual(fm.get("name"), a.stem, f"{a.name}: name debe coincidir con el archivo")
            for k in ("description", "model"):
                self.assertIn(k, fm, f"{a.name}: falta `{k}`")

    def test_frontmatter_de_commands(self):
        for c in COMMANDS:
            fm = _frontmatter(c)
            for k in ("description", "model"):
                self.assertIn(k, fm, f"{c.name}: falta `{k}` en frontmatter")

    def test_frontmatter_de_skills(self):
        for s in (ROOT / "skills").glob("*/SKILL.md"):
            fm = _frontmatter(s)
            self.assertEqual(fm.get("name"), s.parent.name, f"{s}: name debe coincidir con la carpeta")
            self.assertIn("description", fm)


class MarcadoresTests(unittest.TestCase):
    def test_marcadores_usados_estan_documentados(self):
        documentados = set(re.findall(r"## `timonel:([a-z-]+)`", (ROOT / "skills/github-issues/references/marcadores.md").read_text(encoding="utf-8")))
        documentados |= {"sdd", "insights-retro", "insights-review", "metricas"}  # marcadores de issues especiales
        usados = set()
        for f in list((ROOT / "agents").glob("*.md")) + list((ROOT / "skills").rglob("*.md")) + list((ROOT / "scripts").glob("*.py")) + COMMANDS:
            usados |= set(re.findall(r"<!-- timonel:([a-z-]+)", f.read_text(encoding="utf-8")))
            usados |= set(re.findall(r"publicar_marcador\s+\S+\s+([a-z-]+)", f.read_text(encoding="utf-8")))
        usados -= {"<tipo>", "tipo"}
        faltan = {u for u in usados if not u.startswith("sdd") and u not in documentados}
        self.assertFalse(faltan, f"marcadores usados sin documentar en marcadores.md: {sorted(faltan)}")

    def test_validador_cubre_marcadores_documentados(self):
        import validar_marcador as vm
        documentados = set(re.findall(r"## `timonel:([a-z-]+)`", (ROOT / "skills/github-issues/references/marcadores.md").read_text(encoding="utf-8")))
        faltan = documentados - set(vm.CONTRATOS)
        self.assertFalse(faltan, f"marcadores sin contrato en validar_marcador.py: {sorted(faltan)}")


class PerfilPluginTests(unittest.TestCase):
    def test_flechodiezx_tiene_perfil_plugin(self):
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        for frase in ("Perfil plugin", "implement-plugin-change", "git merge --no-ff", "contrato de cambio"):
            self.assertIn(frase, texto, f"flechodiezx.md debe describir el perfil plugin: falta `{frase}`")
        self.assertIn("implement-plugin-change", SKILLS)

    def test_guard_del_plugin_protege_main(self):
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
        guard = hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn('"$branch" = main', guard)
        self.assertIn("exit 2", guard)


class InvocadoresTests(unittest.TestCase):
    def test_cada_contrato_del_validador_tiene_invocador(self):
        import validar_marcador as vm
        textos = "\n".join(f.read_text(encoding="utf-8") for f in list((ROOT / "agents").glob("*.md")) + list((ROOT / "skills").glob("*/SKILL.md")) + COMMANDS)
        sin = [t for t in vm.CONTRATOS if f"--tipo {t}" not in textos]
        self.assertFalse(sin, f"contratos de validar_marcador sin ningun agente/skill que los invoque: {sin}")

    def test_scripts_documentados_en_claude_md(self):
        claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8") + (ROOT / "README.md").read_text(encoding="utf-8")
        sin = [p.name for p in (ROOT / "scripts").glob("*.py") if p.name not in claude and p.stem not in claude]
        self.assertFalse(sin, f"scripts sin mencion en CLAUDE.md/README.md: {sin}")


class VersionTests(unittest.TestCase):
    def test_version_plugin_coincide_con_changelog(self):
        version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["version"]
        primera = re.search(r"^## (\d+\.\d+\.\d+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(primera)
        self.assertEqual(primera.group(1), version, "CHANGELOG.md debe empezar por la version de plugin.json")

    def test_labels_script_incluye_labels_documentados(self):
        doc = (ROOT / "skills/github-issues/references/labels.md").read_text(encoding="utf-8")
        script = (ROOT / "scripts/setup-github-labels.sh").read_text(encoding="utf-8")
        for label in re.findall(r"^\| `([a-z-]+:[a-z-]+|bloqueado|bug|duplicada|obsoleta|insights|harness-audit)` \|", doc, re.MULTILINE):
            if label.startswith("mod:") or label.startswith("sp:"):
                continue
            self.assertIn(f"\n{label}|", script, f"labels.md documenta `{label}` pero setup-github-labels.sh no lo crea")


if __name__ == "__main__":
    unittest.main()
