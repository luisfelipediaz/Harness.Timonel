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
        for frase in ("Perfil plugin", "implement-plugin-change", "contrato de cambio",
                      "verify-dod", "perfil", "integracion.py"):
            self.assertIn(frase, texto, f"flechodiezx.md debe describir el perfil plugin: falta `{frase}`")
        self.assertIn("implement-plugin-change", SKILLS)

    def test_guard_del_plugin_protege_main(self):
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
        guard = hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn('"$branch" = main', guard)
        self.assertIn("exit 2", guard)


class IntegracionPorPrTests(unittest.TestCase):
    """El PR es la unica via de integracion (#80): sin merge directo a la rama base."""

    def test_flechodiezx_no_menciona_merge_directo(self):
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        prohibidas = ('git.integracion: "merge"', "git merge --no-ff", "git push origin main",
                      "merge --ff-only", "git checkout main", "gh issue close")
        for cadena in prohibidas:
            self.assertNotIn(cadena, texto, f"flechodiezx.md no debe mencionar `{cadena}`: la unica via de integracion es el PR")

    def test_flechodiezx_declara_regla_dura_de_via_unica(self):
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        self.assertIn("Una sola vía de integración", texto)

    def test_ningun_hook_propone_merge_no_ff(self):
        """El mensaje viejo del guard de commits del plugin proponia `git merge --no-ff`
        (TIM-ADR-0005, #27); #80 lo derogo: ahora la integracion es por PR (#82)."""
        texto = (ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
        self.assertNotIn("git merge --no-ff", texto)

    def test_hooks_referencian_guard_integracion_existente(self):
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
        comandos = "\n".join(
            hook["command"]
            for bloque in hooks["hooks"]["PreToolUse"]
            for hook in bloque["hooks"]
        )
        self.assertIn("guard_integracion.py", comandos)
        self.assertTrue((ROOT / "scripts/guard_integracion.py").exists())

    def test_guard_integracion_documentado(self):
        claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("guard_integracion.py", claude, "CLAUDE.md debe documentar scripts/guard_integracion.py")
        self.assertTrue(
            "guard_integracion.py" in readme or "guard_integracion" in readme,
            "README.md debe documentar scripts/guard_integracion.py",
        )


class DodEstrictoTests(unittest.TestCase):
    """DoD estricto (gap 3 de la auditoria #24, issue #28): sin autoevaluacion sin evaluador."""

    def test_fila_11_de_verify_dod_no_degrada_a_no_critico(self):
        texto = (ROOT / "skills/verify-dod/SKILL.md").read_text(encoding="utf-8")
        fila_11 = next((l for l in texto.splitlines() if l.startswith("| 11 |")), None)
        self.assertIsNotNone(fila_11, "verify-dod/SKILL.md debe tener la fila 11 de la checklist")
        self.assertNotIn("FAILED NO critico", fila_11, "la fila 11 no debe degradar NO_GENERADO/SKIPPED a NO critico")

    def test_agentes_pasan_perfil_a_verify_dod(self):
        for nombre in ("flechodiezx", "flechodiezx-hotfix"):
            texto = (ROOT / f"agents/{nombre}.md").read_text(encoding="utf-8")
            self.assertIn("verify-dod", texto, f"{nombre}.md debe invocar verify-dod")
            self.assertIn("perfil", texto, f"{nombre}.md debe pasar `perfil` a verify-dod")


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


class TareasTests(unittest.TestCase):
    def test_tareas_de_estado_historia_estan_en_plantilla_hu(self):
        import estado_historia as eh
        plantilla = (ROOT / "skills/github-issues/references/plantilla-hu.md").read_text(encoding="utf-8")
        lineas_plantilla = re.findall(r"^- \[ \] (.+)$", plantilla, re.MULTILINE)
        self.assertEqual(eh.TAREAS, lineas_plantilla,
                          "TAREAS (estado_historia.py) y el checklist de plantilla-hu.md deben coincidir en contenido y orden")

    def test_git_integracion_documentado(self):
        adr = (ROOT / "docs/adr/tim-adr-0002-configuracion-del-consumidor.md").read_text(encoding="utf-8")
        onboard = (ROOT / "commands/onboard.md").read_text(encoding="utf-8")
        self.assertIn("git.integracion", adr, "tim-adr-0002 debe documentar `git.integracion`")
        self.assertIn("integracion", onboard, "onboard.md debe generar/detectar `git.integracion`")


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


class EvalsTests(unittest.TestCase):
    """Casos de `claude plugin eval` (issue #32, gap 12 de la auditoria #11)."""

    GRADER_TYPES = {"regex", "llm", "tool_used", "file_exists", "tool_order", "baseline"}

    def _prompts(self) -> list[Path]:
        return list((ROOT / "evals").glob("**/prompt.md"))

    def _casos(self) -> list[Path]:
        return self._prompts() + list((ROOT / "evals").glob("**/case.yaml"))

    def test_cada_case_referencia_agente_o_skill_existente(self):
        casos = self._casos()
        self.assertTrue(casos, "evals/ debe tener al menos un caso (prompt.md o case.yaml)")
        conocidos = AGENTES | SKILLS
        for caso in casos:
            primero = caso.relative_to(ROOT / "evals").parts[0]
            self.assertIn(primero, conocidos, f"{caso} cuelga de `{primero}`, que no es un agente ni un skill existente")

    def test_cada_case_tiene_graders(self):
        for prompt in self._prompts():
            graders = list((prompt.parent / "graders").glob("*.md"))
            self.assertTrue(graders, f"{prompt} no tiene graders/*.md")
            for grader in graders:
                fm = _frontmatter(grader)
                self.assertIn(fm.get("type"), self.GRADER_TYPES, f"{grader}: `type` invalido o ausente")

    def test_prompt_tiene_name(self):
        for prompt in self._prompts():
            fm = _frontmatter(prompt)
            self.assertIn("name", fm, f"{prompt} no declara `name` en el frontmatter")

    def test_fixture_code_review_siembra_tres_violaciones(self):
        prompt = ROOT / "evals/code-review/tres-violaciones-warning/prompt.md"
        texto = prompt.read_text(encoding="utf-8")
        for violacion in (": any", "*ngIf", "GastoResponse"):
            self.assertIn(violacion, texto, f"el fixture de code-review debe sembrar `{violacion}`")

    def test_evals_results_ignorado(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("evals/results/", gitignore, ".gitignore debe ignorar evals/results/")


if __name__ == "__main__":
    unittest.main()
