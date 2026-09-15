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
    """El PR es la unica via de integracion (#80, extendido a flechodiezx-hotfix por
    #83): sin merge directo a la rama base, en ningun agente que integre por PR."""

    AGENTES_CON_PR = ("flechodiezx", "flechodiezx-hotfix")

    def test_flechodiezx_no_menciona_merge_directo(self):
        prohibidas = ('git.integracion: "merge"', "git merge --no-ff", "git push origin main",
                      "merge --ff-only", "git checkout main", "gh issue close")
        for nombre in self.AGENTES_CON_PR:
            texto = (ROOT / f"agents/{nombre}.md").read_text(encoding="utf-8")
            for cadena in prohibidas:
                self.assertNotIn(cadena, texto, f"{nombre}.md no debe mencionar `{cadena}`: la unica via de integracion es el PR")

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


class HotfixAisladoTests(unittest.TestCase):
    """flechodiezx-hotfix aisla en worktree y siempre abre PR (#83): espejo de
    IntegracionPorPrTests.test_flechodiezx_no_menciona_merge_directo pero con la
    familia de frases que la decision de #83 volvio obsoletas ('sin worktree(s)',
    'en la/rama actual', cierre directo del issue, o cualquier via de integracion
    distinta del PR)."""

    ARCHIVOS = (ROOT / "agents/flechodiezx-hotfix.md", ROOT / "commands/hotfix.md")

    PROHIBIDAS = (
        "sin worktree", "sin worktrees", "Nunca worktree", "en la rama actual",
        "rama actual", "gh issue close", "git push origin main", "merge --ff-only",
        "git checkout main", "git merge --no-ff",
    )

    def test_no_menciona_frases_obsoletas(self):
        for archivo in self.ARCHIVOS:
            texto = archivo.read_text(encoding="utf-8")
            for frase in self.PROHIBIDAS:
                self.assertNotIn(frase, texto, f"{archivo.name} no debe mencionar `{frase}`: el hotfix aisla en worktree y siempre abre PR")

    def test_menciona_worktree_fix_integracion_y_en_revision(self):
        texto = (ROOT / "agents/flechodiezx-hotfix.md").read_text(encoding="utf-8")
        for frase in ("isolation: worktree", "fix/", "integracion.py", "en-revision"):
            self.assertIn(frase, texto, f"flechodiezx-hotfix.md debe mencionar `{frase}`")


class WorktreeDeImplementacionTests(unittest.TestCase):
    """Todo skill `implement-*` se lanza con `isolation: worktree` (#84). Se genera del
    glob `skills/implement-*` en vez de listar frases prohibidas por agente, porque
    `agents/flechodiezx.md` dice "sin worktree" cuatro veces de forma legitima (code-review
    en 5.5, retro en 6, verify-dod en 7, y Dora en 1.5): son sub-agentes de solo lectura
    que no deben aislarse, y una lista de frases prohibidas convertiria esa documentacion
    correcta en un test rojo.

    **La unidad de verificacion es el PARRAFO, no la seccion `##`** — corregido tras el
    hallazgo critico del code review de #84. La primera version segmentaba por bloques
    `##`, y `## Fase 3: Ejecucion paralela` es una sola seccion que agrupa los TRES
    lanzamientos (`implement-plugin-change` del perfil plugin, `implement-backend-story` y
    `implement-frontend-story` del consumidor). Con esa granularidad bastaba que
    `isolation: worktree` apareciera en cualquier punto de la seccion: quitarlo solo de la
    clausula que lanza `implement-plugin-change` dejaba el test en VERDE, porque la frase
    seguia viva en el parrafo del perfil consumidor. Era exactamente la regresion que el
    Gherkin 1 de la HU quiere impedir, invisible para el unico test que debia cubrirla.

    La propiedad correcta es existencial y por parrafo: para cada skill debe existir **un
    parrafo que nombre el skill y declare `isolation: worktree` a la vez**. Un `isolation`
    que vive en otro parrafo ya no cubre a un skill que no esta ahi.

    Caso degenerado (eje 1, caso 3 del contrato de #84): "delta = 0 en las ramas
    `worktree-agent-*` pero con commits nuevos en la rama de la historia" significa que el
    sub-agente escribio en el arbol de trabajo de la sesion en vez de en su worktree — el
    aislamiento fallo. Es la razon por la que este test exige que CADA skill `implement-*`
    aparezca mencionado en algun parrafo (`test_todo_skill_implement_aparece_en_un_parrafo`):
    sin esa fila, "ningun agente menciona el skill" se leeria como que no hay nada que
    objetar, exactamente cuando el sub-agente nunca se lanza aislado. Es el mismo
    razonamiento de #81 con las entradas degeneradas del PR (sin `number`, sin `mergeable`):
    a una entrada degenerada le corresponde un motivo propio, no un pase por default."""

    FRASES_PROHIBIDAS = (
        "sin worktree",
        "sin worktrees",
        "Nunca worktree",
        "sin merge de worktrees",
        "trabaja en la rama",
    )

    @staticmethod
    def _skills_implement() -> list[str]:
        return sorted(p.parent.name for p in (ROOT / "skills").glob("implement-*/SKILL.md"))

    @staticmethod
    def _parrafos(texto: str) -> list[str]:
        """Bloques separados por linea en blanco. Es la unidad mas chica que todavia
        contiene una instruccion de lanzamiento completa (verbo + skill + isolation)."""
        return re.split(r"\n[ \t]*\n", texto)

    def _parrafos_que_mencionan(self, skill: str) -> list[tuple]:
        encontrados = []
        for agente in sorted((ROOT / "agents").glob("*.md")):
            for parrafo in self._parrafos(agente.read_text(encoding="utf-8")):
                if skill in parrafo:
                    encontrados.append((agente, parrafo))
        return encontrados

    def test_todo_skill_implement_aparece_en_un_parrafo(self):
        skills_implement = self._skills_implement()
        self.assertTrue(skills_implement, "no hay skills implement-* que verificar: glob vacio")
        for skill in skills_implement:
            self.assertTrue(
                self._parrafos_que_mencionan(skill),
                f"ningun agente menciona el skill `{skill}` en ningun parrafo: no hay "
                "evidencia de que se lance, y sin evidencia la invariante de aislamiento "
                "seria vacua (ver docstring, caso 3 del eje 1 de #84)",
            )

    def test_cada_skill_implement_se_lanza_en_un_parrafo_que_declara_worktree(self):
        """Existencial y por parrafo: el `isolation: worktree` tiene que estar en el MISMO
        parrafo que nombra al skill. Es la fila que el review de #84 encontro ausente."""
        for skill in self._skills_implement():
            parrafos = self._parrafos_que_mencionan(skill)
            aislados = [(a, p) for a, p in parrafos if "isolation: worktree" in p]
            self.assertTrue(
                aislados,
                f"ningun parrafo que menciona `{skill}` declara `isolation: worktree`: "
                f"lo mencionan {[a.name for a, _ in parrafos]}, pero ninguno en el mismo "
                "parrafo que el lanzamiento. Un `isolation` en otro parrafo no cubre a este skill",
            )

    def test_ningun_parrafo_que_menciona_implement_niega_el_worktree(self):
        for skill in self._skills_implement():
            for agente, parrafo in self._parrafos_que_mencionan(skill):
                for frase in self.FRASES_PROHIBIDAS:
                    self.assertNotIn(
                        frase, parrafo,
                        f"{agente.name}: el parrafo que menciona `{skill}` no debe decir `{frase}`",
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


class ChecklistsPorTipoTests(unittest.TestCase):
    """Genera la familia (#83): itera CHECKLISTS contra su plantilla-<tipo>.md, en vez de
    cablear un test hermano por tipo. Cubre `hu` (invariante que ya afirmaba TareasTests)
    y `hotfix`, y cualquier tipo que se agregue despues sin tener que recordar escribir
    un test nuevo."""

    def test_checklists_coinciden_con_su_plantilla(self):
        import estado_historia as eh
        for tipo, checklist in eh.CHECKLISTS.items():
            plantilla_path = ROOT / f"skills/github-issues/references/plantilla-{tipo}.md"
            self.assertTrue(plantilla_path.exists(), f"CHECKLISTS declara el tipo `{tipo}` pero falta {plantilla_path}")
            texto = plantilla_path.read_text(encoding="utf-8")
            lineas_plantilla = re.findall(r"^- \[ \] (.+)$", texto, re.MULTILINE)
            self.assertEqual(checklist, lineas_plantilla,
                              f"CHECKLISTS['{tipo}'] y el checklist de {plantilla_path.name} deben coincidir en contenido y orden")


class TareasTests(unittest.TestCase):
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


class HeuristicasDescubriblesTests(unittest.TestCase):
    """Una heuristica escrita que ningun skill puede descubrir no cambia ninguna decision (#134).

    El ratchet cosecho once heuristicas como issues desde #34 y ninguna llego al disco;
    peor, el mecanismo que las consume enumeraba por nombre los archivos que leia, asi que
    crear un archivo nuevo no lo activaba. Estas cinco invariantes cubren las dos mitades:
    que el descubrimiento sea por patron (A), que no queden referencias colgadas (B), que
    cada archivo tenga la forma que lo hace aplicable (C, D) y que su carpeta sea alcanzable
    por alguna regla documentada (E).

    **A verifica el nombre SIN extension (el *stem*), no el nombre con `.md`.** La lista
    cerrada que esta invariante existe para atrapar --la de la seccion 3.4 del skill de
    review, que es la que decide que hallazgos se reportan-- estaba escrita sin extension.
    Verificar con `.md` la habria dejado pasar limpia y la invariante habria nacido vacua:
    verde, y sin cubrir el unico lugar que importaba. El stem es ademas estrictamente mas
    fuerte, porque toda mencion con extension contiene al stem.

    Este docstring se abstiene **a proposito** de escribir un stem real de heuristica, y los
    tests derivan la lista de stems del contenido de `heuristics/` en vez de listarla. En #84
    (`4fdb04c`) el fix que corrigio el ambito de una invariante reescribio su docstring para
    explicar la regla, la explicacion repitio el literal buscado, y eso volvio a vaciar la
    invariante que el fix acababa de arreglar. El ambito de A son los skills, no este archivo,
    asi que aqui un literal no vaciaria nada hoy; la abstencion es disciplina barata frente a
    un ambito que puede ampliarse. Si alguien "completa" este texto con un ejemplo concreto,
    esta deshaciendo la leccion.

    El selector de C y D es **default-in con opt-out declarado**: todo archivo de `heuristics/`
    esta cubierto salvo que su H1 termine en el sufijo literal de catalogo. No se usa "el H1
    empieza con tal prefijo" porque seria default-out: un archivo nuevo con el encabezado mal
    escrito quedaria exento en silencio, que es el modo de fallo que esta clase persigue.
    """

    SKILLS_QUE_DESCUBREN = ("code-review", "implement-plugin-change")
    SUFIJO_OPT_OUT = " — catálogo"
    GLOB_OBLIGATORIO = "general/*.md"
    MARCA_DE_GLOB = "*.md"
    SECCION_CASO = "Caso real"
    SECCION_RELACION = "Relación con otras heurísticas"
    SECCION_REGLA = "Regla general"
    PREFIJO_CUANDO = "Cuándo"
    CARPETA_SIEMPRE_ALCANZABLE = "general"
    DIRS_CON_MARKDOWN = ("agents", "commands", "skills", "scripts", "hooks", "heuristics", "docs", "evals", "tests", ".github")
    _RE_RUTA_HEURISTICA = re.compile(r"heuristics/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+\.md)")

    @staticmethod
    def _heuristicas() -> list[Path]:
        return sorted((ROOT / "heuristics").rglob("*.md"))

    @classmethod
    def _stems(cls) -> list[str]:
        """Los nombres sin extension, derivados del disco. Nunca una lista literal: una
        lista aqui seria la misma enumeracion cerrada que la invariante A prohibe."""
        return sorted({p.stem for p in cls._heuristicas()})

    @staticmethod
    def _h1(path: Path) -> str:
        for linea in path.read_text(encoding="utf-8").splitlines():
            if linea.startswith("# "):
                return linea
        return ""

    @classmethod
    def _cubiertas_por_formato(cls) -> list[Path]:
        return [p for p in cls._heuristicas() if not cls._h1(p).rstrip().endswith(cls.SUFIJO_OPT_OUT)]

    @staticmethod
    def _sin_bloques_de_codigo(texto: str) -> str:
        """Un `## ...` dentro de un bloque cercado es parte de un ejemplo, no una seccion.
        Contarlo dejaria que un ejemplo satisfaga las invariantes de formato."""
        return re.sub(r"^```.*?^```", "", texto, flags=re.M | re.S)

    @classmethod
    def _titulos_de_seccion(cls, texto: str) -> list[str]:
        return [l[3:].strip() for l in cls._sin_bloques_de_codigo(texto).splitlines() if l.startswith("## ")]

    @classmethod
    def _cuerpo_de_seccion(cls, texto: str, titulo: str) -> str | None:
        for bloque in re.split(r"^## ", cls._sin_bloques_de_codigo(texto), flags=re.M)[1:]:
            if bloque.splitlines()[0].strip() == titulo:
                return bloque
        return None

    @staticmethod
    def _parrafos(texto: str) -> list[str]:
        return re.split(r"\n[ \t]*\n", texto)

    @classmethod
    def _markdown_del_repo(cls):
        """Solo los directorios versionados con documentacion. `rglob` desde la raiz
        entraria a `.claude/worktrees/`, donde viven copias completas del repo."""
        yield from sorted(ROOT.glob("*.md"))
        for carpeta in cls.DIRS_CON_MARKDOWN:
            yield from sorted((ROOT / carpeta).rglob("*.md"))

    # --- A: descubrimiento por glob -------------------------------------------------

    def test_a_los_skills_que_consumen_heuristicas_declaran_el_glob(self):
        for skill in self.SKILLS_QUE_DESCUBREN:
            archivo = ROOT / "skills" / skill / "SKILL.md"
            self.assertTrue(archivo.exists(), f"{skill}/SKILL.md no existe")
            self.assertTrue(
                self.GLOB_OBLIGATORIO in archivo.read_text(encoding="utf-8"),
                f"{skill}/SKILL.md debe descubrir las heuristicas por glob `{self.GLOB_OBLIGATORIO}`: "
                "sin el glob no hay mecanismo, y una heuristica nueva no llega a nadie",
            )

    def test_a_ningun_parrafo_nombra_una_heuristica_sin_declarar_el_glob(self):
        """Unidad: el PARRAFO (leccion de #84). Un glob que vive en otro parrafo no cubre a
        la cita de este. Se busca el stem y no el basename con extension: ver docstring."""
        stems = self._stems()
        self.assertTrue(stems, "no hay archivos en heuristics/: la invariante seria vacua")
        for skill in self.SKILLS_QUE_DESCUBREN:
            archivo = ROOT / "skills" / skill / "SKILL.md"
            for parrafo in self._parrafos(archivo.read_text(encoding="utf-8")):
                nombrados = [s for s in stems if s in parrafo]
                if not nombrados:
                    continue
                self.assertIn(
                    self.MARCA_DE_GLOB, parrafo,
                    f"{skill}/SKILL.md: el parrafo que nombra {nombrados} no declara el glob. "
                    "Una cita puntual solo sobrevive en el mismo parrafo que el patron de "
                    "descubrimiento; sola, es una lista cerrada disfrazada",
                )

    # --- B: sin referencias huerfanas -----------------------------------------------

    def test_b_toda_ruta_de_heuristica_citada_existe_en_disco(self):
        for doc in self._markdown_del_repo():
            for carpeta, archivo in self._RE_RUTA_HEURISTICA.findall(doc.read_text(encoding="utf-8")):
                ruta = ROOT / "heuristics" / carpeta / archivo
                self.assertTrue(
                    ruta.exists(),
                    f"{doc.relative_to(ROOT)} cita `heuristics/{carpeta}/{archivo}` y ese archivo no existe",
                )

    # --- C y D: formato y evidencia --------------------------------------------------

    def test_c_toda_heuristica_tiene_regla_cuando_y_relacion(self):
        cubiertas = self._cubiertas_por_formato()
        self.assertTrue(cubiertas, "ninguna heuristica quedo cubierta por el formato: revisa el opt-out")
        for archivo in cubiertas:
            titulos = self._titulos_de_seccion(archivo.read_text(encoding="utf-8"))
            nombre = archivo.relative_to(ROOT)
            self.assertIn(self.SECCION_REGLA, titulos, f"{nombre} no tiene `## {self.SECCION_REGLA}`")
            self.assertTrue(
                any(t.startswith(self.PREFIJO_CUANDO) for t in titulos),
                f"{nombre} no tiene una seccion `## {self.PREFIJO_CUANDO}...`: sin limites, una heuristica "
                "se aplica donde no corresponde y se vuelve ruido ignorable",
            )
            self.assertIn(
                self.SECCION_RELACION, titulos,
                f"{nombre} no tiene `## {self.SECCION_RELACION}`: sin decir en que se distingue de su "
                "vecina, dos heuristicas parientes se invocan indistintamente",
            )

    def test_d_toda_heuristica_cita_su_caso_con_un_issue(self):
        for archivo in self._cubiertas_por_formato():
            nombre = archivo.relative_to(ROOT)
            cuerpo = self._cuerpo_de_seccion(archivo.read_text(encoding="utf-8"), self.SECCION_CASO)
            self.assertIsNotNone(cuerpo, f"{nombre} no tiene `## {self.SECCION_CASO}`")
            self.assertRegex(
                cuerpo, r"#\d+",
                f"{nombre}: `## {self.SECCION_CASO}` no cita ningun issue `#N`. Una heuristica sin el caso "
                "que la origino es prosa generica, y una con evidencia inventada es peor que una sin evidencia",
            )

    # --- E: carpeta alcanzable --------------------------------------------------------

    def test_e_toda_carpeta_de_heuristicas_es_alcanzable(self):
        claude_md = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        carpetas = sorted({p.parent.name for p in self._heuristicas()})
        self.assertTrue(carpetas, "no hay carpetas en heuristics/")
        for carpeta in carpetas:
            if carpeta == self.CARPETA_SIEMPRE_ALCANZABLE:
                continue
            self.assertTrue(
                f"`{carpeta}/`" in claude_md,
                f"la carpeta `heuristics/{carpeta}/` no esta documentada en CLAUDE.md: ningun glob la "
                "alcanza y sus heuristicas son codigo muerto. Documenta la regla que la deriva o no la crees",
            )


if __name__ == "__main__":
    unittest.main()
