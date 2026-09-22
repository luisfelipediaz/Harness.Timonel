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


class DefinicionDelRepoEnPerfilPluginTests(unittest.TestCase):
    """#147: en perfil plugin, flechodiezx y flechodiezx-hotfix corren con las
    instrucciones de la copia **instalada** del plugin (`$PLUGIN_ROOT`, cache), que puede
    ser una version vieja del repo que estan editando -- eso fue lo que paso en la epica
    #79 (el contrato de #85 salio con el orden de fases viejo). La Fase 0 tiene que
    comparar version del repo vs. instalada y, si difieren, releer `agents/<nombre>.md`
    del repo con Read.

    "Releer la definicion" NO es recargar el system prompt -- Claude Code no lo permite --
    asi que el texto tiene que decirlo de forma explicita, o un editor futuro lo
    "arregla" prometiendo una recarga que no existe."""

    AGENTES = ("flechodiezx", "flechodiezx-hotfix")

    @staticmethod
    def _seccion_fase_0(texto: str) -> str:
        """La unidad de verificacion es la seccion `## Fase 0`, no el archivo entero.

        Con el archivo entero, dos de las frases exigidas (`avisa`, `Read`) son palabras
        genericas que aparecen en otras fases de ambos agentes, asi que mover el paso
        fuera de la Fase 0 dejaba el test en verde con el AC ya incumplido. Corta en el
        siguiente `## ` -- que es `## Fase 0.5` en los dos agentes."""
        inicio = re.search(r"^## Fase 0:.*$", texto, re.MULTILINE)
        assert inicio, "el agente debe tener una seccion `## Fase 0:`"
        resto = texto[inicio.end():]
        fin = re.search(r"^## ", resto, re.MULTILINE)
        return resto[: fin.start()] if fin else resto

    def test_fase_0_describe_el_mecanismo_completo(self):
        for nombre in self.AGENTES:
            texto = (ROOT / f"agents/{nombre}.md").read_text(encoding="utf-8")
            fase_0 = self._seccion_fase_0(texto)
            for frase in (
                "jq -r .version .claude-plugin/plugin.json",
                ".plugin-root",
                "avisa",
                "Read",
                f"agents/{nombre}.md",
            ):
                self.assertIn(frase, fase_0, f"{nombre}.md: la Fase 0 debe describir el mecanismo completo (falta `{frase}`)")

    def test_no_promete_recarga_de_system_prompt(self):
        for nombre in self.AGENTES:
            texto = (ROOT / f"agents/{nombre}.md").read_text(encoding="utf-8")
            self.assertIn(
                "no recarga tu system prompt",
                texto,
                f"{nombre}.md debe aclarar que releer la definicion no recarga el system prompt",
            )

    def test_hook_de_version_no_lleva_gate_de_config_consumidor(self):
        """Invariante 2 (#147): `.claude/timonel.config.json` no existe en el repo del
        plugin (perfil plugin, verificado); con ese gate el aviso del AC4 nunca correria
        en el unico perfil donde se necesita."""
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
        comandos = [h["command"] for bloque in hooks["hooks"]["SessionStart"] for h in bloque["hooks"]]
        candidatos = [c for c in comandos if "version_instalada" in c]
        self.assertTrue(candidatos, "hooks.json debe tener el hook nuevo de version repo vs instalada")
        for c in candidatos:
            self.assertNotIn("[ -f .claude/timonel.config.json ]", c)


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


class PoliticaDeIntegracionDocumentadaTests(unittest.TestCase):
    """La politica "todo cambio entra por PR, la base no recibe commits directos" no
    puede contradecirse en la doctrina que la explica (#85, epica #79).

    **Ambito: el PARRAFO, no el archivo** (leccion de #84, `WorktreeDeImplementacionTests`,
    y de la propia HU #85: con ambito de archivo, la invariante mataria a la entrada de
    `tim-adr-0005` que deroga una via vieja, porque para derogarla tiene que citarla).

    **Correccion (hallazgo CRITICO del code review de #85 sobre esta misma clase): el
    parrafo no es "lo que separan las lineas en blanco".** La primera version de
    `_parrafos` cortaba solo ahi (`re.split(r"\n[ \t]*\n", texto)`). Una lista Markdown no
    lleva linea en blanco entre items, asi que la seccion "Control de cambios" de
    `tim-adr-0005-gobernanza-del-plugin.md` colapsaba entera en un unico "parrafo".
    Evidencia reproducida sobre el archivo real (comentario `timonel:review` del issue):

    ```
    --- parrafo 7: lineas=2  mecanica=['--ff-only', 'git push origin']  derogacion=['derogad']
    - 2026-09-10 (#27): ...
    - 2026-09-15 (v0.6.0, #85): ... deroga expresamente ...
    ```

    Las entradas de **#27 y #85 son el mismo parrafo fusionado**: la marca de derogacion
    vive en la de #85 y le da cobertura, sin querer, a la de #27. El reviewer lo probo
    metiendo `git push origin main` sin derogar en la entrada de #27 y
    `test_ningun_parrafo_vivo_propone_mecanica_de_integracion_a_la_base` siguio en
    **verde** -- los casos 3 y 10 del contrato pasaban por fusion de parrafo, no por
    cumplir la propiedad.

    El fix: `_parrafos` corta ademas en **frontera de item de lista y de fila de tabla**.
    Una linea que empieza (tras espacios opcionales) con `- `, `* `, `+ `, `| ` o un
    ordinal `N. ` abre una unidad nueva; una linea de continuacion (indentada, que no abre
    unidad) se acumula con la unidad anterior, para no partir un item que envuelve a la
    siguiente linea. La unidad correcta no es "el parrafo" en abstracto sino **el bloque
    mas chico que contiene una instruccion completa**: en Markdown eso lo define la
    estructura (item, fila, bloque), no las lineas en blanco (ver
    `heuristics/general/unidad-de-verificacion.md`).

    **La leccion es simetrica (la misma de #84, repetida un nivel mas abajo): un defecto
    de ambito nunca es puntual.** No alcanza con mutar la entrada que el review encontro
    (#27): hay que mutar tambien la de #85 -- quitarle la marca de derogacion a #85 debe
    romper el test por si sola, sin que la entrada de #27 la tape ni la descubra.

    **La propiedad, no el literal ni el verbo.** Un parrafo viola la politica cuando, a la
    vez: (a) contiene **mecanica de integracion** (`--no-ff`, `--ff-only`,
    `git push origin`, `git checkout main`, `git.integracion: "merge"`, normalizando
    backticks); (b) menciona la base (`main`, `rama base`); y (c) no esta marcado como
    derogado (`derogad`/`deprecad` en el mismo parrafo). Dos candidatas mas simples se
    midieron y se descartaron (contrato de #85, comentario `timonel:contrato-api`):

    1. *Verbo (`merge`/`push`) + base*: 5 falsos positivos sobre los parrafos reales del
       repo, entre ellos la propia entrada de Control de cambios que enuncia la politica
       correcta.
    2. *Forma-comando* (`git merge`/`gh pr merge`/...): invierte el resultado. Marca
       parrafos legitimos (la fila de `hooks/` en CLAUDE.md usa literalmente
       `gh pr merge`) y no atrapa la violacion real de `README.md` (`merge` + backtick +
       `--no-ff`, sin `git` inmediatamente antes).

    Medicion de la propiedad elegida (contrato de #85): 1/1 violacion viva detectada, 3/3
    mutaciones detectadas, 5/5 parrafos legitimos pasan.

    **Hueco conocido, declarado a proposito**: la prosa instructiva sin mecanica no se
    detecta -- "el orquestador mergea la rama a main" o "integra la rama a la rama base sin
    pasar por un PR" pasan las dos. Perseguirlo pediria una gramatica de prosa: superficie
    nueva de bug sin defecto que la motive, el mismo criterio con que `guard_integracion.py`
    declara que no persigue `eval`/`bash -c`.

    **Limite de alcance declarado**: `CHANGELOG.md` queda fuera (es historico por
    definicion: narra transiciones ya cerradas, no prescribe el mecanismo vigente) y
    `skills/` tambien (sus `--no-ff` documentan mergear un *worktree* a la rama de la
    *historia*, nunca a la base, y cubrirlos exigiria que la propiedad distinga destinos
    dentro de un skill -- sin ese defecto no se justifica la superficie nueva)."""

    ARCHIVOS = (ROOT / "CLAUDE.md", ROOT / "README.md") + tuple(sorted((ROOT / "docs/adr").glob("*.md")))

    MECANICAS_DE_INTEGRACION = (
        "--no-ff",
        "--ff-only",
        "git push origin",
        "git checkout main",
        'git.integracion: "merge"',
    )
    MENCIONES_DE_BASE = ("main", "rama base")
    MARCAS_DE_DEROGACION = ("derogad", "deprecad")

    _INICIO_DE_ITEM = re.compile(r"^[ \t]*(?:[-*+][ \t]|\d+\.[ \t]|\|)")

    @classmethod
    def _parrafos(cls, texto: str) -> list[str]:
        """El bloque mas chico que contiene una instruccion completa: primero se corta por
        linea en blanco, y DENTRO de cada bloque, otra vez en cada frontera de item de
        lista o fila de tabla -- una lista o una tabla Markdown no llevan linea en blanco
        entre sus entradas, asi que sin este segundo corte todas colapsan en un unico
        "parrafo" (ver docstring de la clase, evidencia de #27/#85).

        Abre unidad nueva una linea que empieza (tras espacios opcionales) con `- `, `* `,
        `+ `, `| ` o un ordinal `N. `. Una linea de continuacion -- indentada, que no abre
        unidad -- se acumula con la unidad anterior en vez de separarse: un item que
        envuelve a la siguiente linea fisica sigue siendo una sola instruccion.
        """
        unidades: list[str] = []
        for bloque in re.split(r"\n[ \t]*\n", texto):
            actual: list[str] = []
            for linea in bloque.split("\n"):
                if cls._INICIO_DE_ITEM.match(linea) and actual:
                    unidades.append("\n".join(actual))
                    actual = [linea]
                else:
                    actual.append(linea)
            if actual:
                unidades.append("\n".join(actual))
        return unidades

    @classmethod
    def _viola(cls, parrafo: str) -> bool:
        normalizado = parrafo.replace("`", "")
        tiene_mecanica = any(m in normalizado for m in cls.MECANICAS_DE_INTEGRACION)
        menciona_base = any(b in normalizado for b in cls.MENCIONES_DE_BASE)
        derogado = any(marca in normalizado.lower() for marca in cls.MARCAS_DE_DEROGACION)
        return tiene_mecanica and menciona_base and not derogado

    def test_ningun_parrafo_vivo_propone_mecanica_de_integracion_a_la_base(self):
        for archivo in self.ARCHIVOS:
            texto = archivo.read_text(encoding="utf-8")
            for parrafo in self._parrafos(texto):
                self.assertFalse(
                    self._viola(parrafo),
                    f"{archivo.relative_to(ROOT)}: parrafo con mecanica de integracion a la "
                    f"base sin marca de derogacion:\n{parrafo}",
                )

    def test_la_propiedad_exige_mecanica_y_base_a_la_vez(self):
        """Casos 3 y 5 del contrato, verificados como logica pura (no dependen de que el
        repo tenga hoy un parrafo con esta forma exacta)."""
        solo_mecanica = "El script interno usa --no-ff para un merge de prueba en un repo aislado."
        self.assertFalse(self._viola(solo_mecanica), "sin mencion de la base, no deberia violar")

        solo_base = "La rama base recibe cambios solo mediante revision humana en GitHub."
        self.assertFalse(self._viola(solo_base), "sin mecanica de integracion, no deberia violar")

        ambas_sin_derogar = "Se sigue haciendo git push origin main para llevar cambios a la base."
        self.assertTrue(self._viola(ambas_sin_derogar), "mecanica + base sin marca de derogacion deberia violar")

        ambas_derogadas = "Se dejo de hacer git push origin main a la base: esa practica quedo derogada en #27."
        self.assertFalse(self._viola(ambas_derogadas), "la misma combinacion, marcada como derogada, no deberia violar (caso 3: derogar exige citar)")

    def test_el_opt_out_de_derogacion_no_es_vacuo(self):
        """Caso 5: quitar la marca de derogacion debe volver a encender la violacion."""
        derogado = "Se integraba con git merge --ff-only parado en main; via derogada desde #82."
        self.assertFalse(self._viola(derogado))
        vigente = derogado.replace("derogada", "vigente")
        self.assertTrue(self._viola(vigente), "sin la marca de derogacion, el mismo parrafo debe violar la politica")

    def test_items_de_lista_consecutivos_no_se_fusionan_en_un_solo_parrafo(self):
        """Logica pura (no depende de que el repo tenga hoy este texto exacto): fija la
        unidad nueva con la MISMA forma real de #27/#85 en `tim-adr-0005` -- dos items de
        lista consecutivos, sin linea en blanco entre ellos, uno con mecanica de
        integracion vigente y el vecino con la marca de derogacion.

        Con el ambito viejo (una linea en blanco) los dos items eran un solo "parrafo": la
        marca de derogacion del segundo item cubria al primero y la violacion daba
        **verde**. Con el ambito nuevo (item de lista) tienen que ser dos unidades, y la
        del item vigente tiene que violar por si sola."""
        texto = (
            "- (#27): se sigue haciendo git push origin main en la rama base.\n"
            "- (#85): esa via quedo derogada desde #82.\n"
        )
        parrafos = self._parrafos(texto)
        self.assertEqual(
            len(parrafos), 2,
            "cada item de lista debe quedar en su propia unidad, no fusionado en un solo parrafo",
        )
        item_27, item_85 = parrafos
        self.assertIn("#27", item_27)
        self.assertIn("#85", item_85)
        self.assertTrue(
            self._viola(item_27),
            "el item de #27, aislado en su propia unidad, tiene mecanica + base sin su "
            "propia marca de derogacion: debe violar (antes daba verde, tapado por la "
            "marca de derogacion del item vecino)",
        )
        self.assertFalse(
            self._viola(item_85),
            "el item de #85 tiene su propia marca de derogacion y no debe violar",
        )

    def test_el_pipeline_de_implement_en_readme_nombra_pr_antes_que_dod(self):
        """Caso 12, asercion POSITIVA (prohibir no detecta omisiones): el parrafo de
        `/timonel:implement` en README.md debe nombrar `PR` antes que `DoD`, porque la
        Fase 6.5 (abrir el PR) ocurre antes de la Fase 7 (DoD) -- ver `agents/flechodiezx.md`.
        No alcanza con que el parrafo mencione `PR` en cualquier posicion: una version
        anterior de este caso solo exigia presencia, y esa version dejaba pasar
        `-> DoD -> PR` (el orden invertido, previo a #80)."""
        texto = (ROOT / "README.md").read_text(encoding="utf-8")
        parrafo = next((p for p in self._parrafos(texto) if "/timonel:implement #hu" in p), None)
        self.assertIsNotNone(parrafo, "README.md no tiene el parrafo del pipeline de /timonel:implement")
        idx_pr = parrafo.find("PR")
        idx_dod = parrafo.find("DoD")
        self.assertNotEqual(idx_pr, -1, "el parrafo del pipeline no nombra PR")
        self.assertNotEqual(idx_dod, -1, "el parrafo del pipeline no nombra DoD")
        self.assertLess(idx_pr, idx_dod, "PR debe aparecer antes que DoD en el pipeline: la Fase 6.5 abre el PR antes del DoD (Fase 7)")


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


class SincronizacionDelWorktreeTests(unittest.TestCase):
    """Push + sincronizacion al arrancar (#122): el worktree de un sub-agente nace de
    `origin/main`, nunca de la rama de la historia (#84, reconfirmado con sonda en vivo
    por #122). La Fase 2 pushea la rama de la historia y cada sub-agente de un skill
    `implement-*` sincroniza su worktree contra el remoto de esa rama (fetch + merge sin
    editor) antes de empezar a trabajar. Molde de `WorktreeDeImplementacionTests`: ambito
    parrafo, propiedad existencial, skills por glob (nunca lista de nombres).

    Igual que la invariante de `isolation: worktree`, la unidad de verificacion es el
    PARRAFO, no la seccion `## Fase 3`: esa seccion agrupa los lanzamientos de los tres
    skills `implement-*`, y una asercion sobre toda la seccion (o sobre el archivo
    entero) daria falso verde si el literal solo sobrevive en el parrafo del perfil
    plugin (que ya lo tenia para la divergencia desde #84) mientras el parrafo del
    perfil consumidor -- el que agrega esta HU -- se queda sin el. Es la reincidencia de
    `heuristics/general/unidad-de-verificacion.md` que el contrato de #122 nombro por
    adelantado.

    Ronda de correccion del code review: dos casos mas. El primero (`RAMA_LITERAL`)
    corrige el CRITICO 1 -- el Paso 0 original hardcodeaba `hu/<issue>-*` y por lo tanto
    asumia que el orquestador SIEMPRE indica una rama, lo que rompe a
    `flechodiezx-hotfix` en su camino normal (rama `fix/N-<slug>` no pusheada: no hay
    nada que sincronizar, y no es lo mismo que "la rama no existe"). La correccion
    parametriza el paso con `RAMA_HISTORIA`; este test verifica que cada `SKILL.md`
    `implement-*` menciona esa variable en el mismo parrafo que declara la
    sincronizacion -- no que el comportamiento condicional funcione en runtime (eso no
    es verificable por texto), sino que el paso dejo de estar hardcodeado a una rama fija.
    El segundo (`MERGE_BASE_LITERAL`) corrige el CRITICO 2 -- la verificacion objetiva
    `git merge-base --is-ancestor` solo vivia en el perfil plugin; el perfil consumidor,
    que es el que describe el Gherkin 1 de la HU, seguia confiando en el auto-reporte del
    sub-agente."""

    SYNC_LITERAL = "git merge --no-edit origin/hu"
    DIVERGENCIA_LITERAL = "rev-list --left-right --count"
    RAMA_LITERAL = "RAMA_HISTORIA"
    MERGE_BASE_LITERAL = "merge-base --is-ancestor"
    PUSH_LITERAL = "git push -u origin"
    CONCLUSION_DIVERGENCIA_LITERAL = "no sigas al paso 1"
    CONDICION_PUSH_LITERAL = "`0 0`"

    @staticmethod
    def _skills_implement() -> list[str]:
        return sorted(p.parent.name for p in (ROOT / "skills").glob("implement-*/SKILL.md"))

    @staticmethod
    def _parrafos(texto: str) -> list[str]:
        """Bloques separados por linea en blanco: la unidad mas chica que todavia
        contiene una instruccion de lanzamiento completa."""
        return re.split(r"\n[ \t]*\n", texto)

    @staticmethod
    def _casos(parrafo: str) -> list[str]:
        """Recorta un parrafo en sus items de lista (bullets `- **...**: ...`):
        los cuatro casos del Paso 0 ("Cuatro casos, nunca dos") viven en el
        MISMO parrafo -- sin linea en blanco entre bullets -- asi que una
        asercion a nivel parrafo no distingue el caso que mide divergencia del
        caso vecino que tambien dice "no sigas al paso 1" por otro motivo
        (WARNING 1 del review de #194: una mutacion que vacia la conclusion de
        un solo caso no hace fallar nada si el chequeo mira el parrafo entero)."""
        return re.split(r"\n(?=[ \t]*-\s)", parrafo)

    @staticmethod
    def _oraciones(texto: str) -> list[str]:
        """Divide en oraciones por punto seguido de espacio: la unidad mas chica
        donde push, la condicion `0 0` y RAMA_HISTORIA conviven en la prosa de
        la Fase 5.5/0.5/3. El mismo parrafo repite `0 0` en la oracion vecina
        que describe el camino negativo ("Si el conteo no es `0 0`, no pasas la
        variable..."), asi que una asercion a nivel parrafo no distingue la
        condicion vinculante de esa repeticion (WARNING 2 del review de #194)."""
        return re.split(r"(?<=\.)\s+", texto)

    @staticmethod
    def _seccion(texto: str, titulo: str) -> str:
        """Recorta desde `## <titulo>` hasta el siguiente encabezado de nivel 2
        (`\\n## `), o el fin del archivo. Ancla real de #194: un parrafo que
        menciona el literal correcto pero vive en otra seccion (o en `## Notas`)
        no debe satisfacer un caso acotado a una fase concreta -- de lo
        contrario el ancla no hace ningun trabajo (M8 del contrato)."""
        inicio = texto.find(titulo)
        if inicio == -1:
            return ""
        resto = texto[inicio + len(titulo):]
        fin = resto.find("\n## ")
        return resto if fin == -1 else resto[:fin]

    def _parrafos_que_mencionan(self, skill: str) -> list[tuple]:
        encontrados = []
        for agente in sorted((ROOT / "agents").glob("*.md")):
            for parrafo in self._parrafos(agente.read_text(encoding="utf-8")):
                if skill in parrafo:
                    encontrados.append((agente, parrafo))
        return encontrados

    def test_1_cada_skill_implement_tiene_un_parrafo_que_declara_sincronizacion(self):
        for skill in self._skills_implement():
            parrafos = self._parrafos_que_mencionan(skill)
            self.assertTrue(parrafos, f"ningun agente menciona el skill `{skill}` en ningun parrafo")
            sincronizados = [(a, p) for a, p in parrafos if self.SYNC_LITERAL in p]
            self.assertTrue(
                sincronizados,
                f"ningun parrafo que menciona `{skill}` declara la sincronizacion con la "
                f"rama de la historia: lo mencionan {[a.name for a, _ in parrafos]}, pero "
                "ninguno en el mismo parrafo trae el fetch+merge contra el remoto de esa "
                "rama. Un fetch+merge que vive en otro parrafo no cubre a este skill",
            )

    def test_2_cada_skill_md_implement_contiene_su_paso_de_sincronizacion(self):
        for skill in self._skills_implement():
            archivo = ROOT / "skills" / skill / "SKILL.md"
            texto = archivo.read_text(encoding="utf-8")
            self.assertIn(
                self.SYNC_LITERAL, texto,
                f"{archivo.relative_to(ROOT)} no declara el paso de sincronizacion con "
                "la rama de la historia (fetch+merge contra el remoto de esa rama)",
            )

    def test_3_fase_3_mide_divergencia_en_los_dos_perfiles(self):
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        parrafos_con_divergencia = [p for p in self._parrafos(texto) if self.DIVERGENCIA_LITERAL in p]
        self.assertTrue(
            parrafos_con_divergencia,
            f"agents/flechodiezx.md no mide divergencia ({self.DIVERGENCIA_LITERAL}) en ningun parrafo",
        )
        parrafo_consumidor = next(
            (p for p in parrafos_con_divergencia if "**Perfil consumidor**" in p), None
        )
        self.assertIsNotNone(
            parrafo_consumidor,
            "ningun parrafo que arranca declarando el perfil consumidor mide la "
            f"divergencia ({self.DIVERGENCIA_LITERAL}): esa medicion solo sobrevive en el "
            "parrafo del perfil plugin (#84); el parrafo del perfil consumidor -- el que "
            "agrega #122 -- se quedo sin ella",
        )

    def test_4_hotfix_no_afirma_que_el_worktree_nazca_sobre_su_rama_fix(self):
        texto = (ROOT / "agents/flechodiezx-hotfix.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "worktree` sobre esa rama",
            texto,
            "flechodiezx-hotfix.md no debe afirmar que el worktree nace sobre "
            "`fix/N-<slug>`: como en flechodiezx, nace de `origin/main` (#122)",
        )

    def test_5_skill_implement_no_hardcodea_la_rama_de_sincronizacion(self):
        """CRITICO 1 del review de correccion: el Paso 0 no puede asumir que el
        orquestador siempre indica una rama -- `flechodiezx-hotfix` en su camino normal
        no tiene ninguna que pasar. Cada `SKILL.md` `implement-*` debe declarar, en el
        mismo parrafo que sincroniza, la variable `RAMA_HISTORIA` que distingue
        "no me la indicaron" de "la rama no existe"."""
        for skill in self._skills_implement():
            archivo = ROOT / "skills" / skill / "SKILL.md"
            texto = archivo.read_text(encoding="utf-8")
            parrafos_con_sync = [p for p in self._parrafos(texto) if self.SYNC_LITERAL in p]
            self.assertTrue(
                parrafos_con_sync,
                f"{archivo.relative_to(ROOT)} no declara el paso de sincronizacion",
            )
            parametrizados = [p for p in parrafos_con_sync if self.RAMA_LITERAL in p]
            self.assertTrue(
                parametrizados,
                f"{archivo.relative_to(ROOT)} hardcodea la rama de sincronizacion: su "
                f"parrafo de Paso 0 no menciona `{self.RAMA_LITERAL}`, la variable que "
                "el orquestador usa para indicar (o no) la rama. Sin ella el paso no "
                "distingue 'no me indicaron rama' de 'la rama no existe', y todo hotfix "
                "nuevo que reuse este skill sobre `fix/N-<slug>` (nunca pusheada en el "
                "camino normal) aborta buscando una rama que no aplica",
            )

    def test_6_fase_3_contrasta_merge_base_en_perfil_consumidor(self):
        """CRITICO 2 del review de correccion: el contrato promete que el orquestador
        'no le cree al sub-agente' y lo contraste con `git merge-base --is-ancestor`.
        Esa verificacion objetiva solo vivia en el perfil plugin; el perfil consumidor
        -- el que describe el Gherkin 1 de la HU -- no tenia ningun paso posterior al
        lanzamiento que confirmara desde el arbol principal que la sincronizacion
        ocurrio de verdad."""
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        parrafos_con_merge_base = [p for p in self._parrafos(texto) if self.MERGE_BASE_LITERAL in p]
        self.assertTrue(
            parrafos_con_merge_base,
            f"agents/flechodiezx.md no contrasta la sincronizacion con "
            f"`{self.MERGE_BASE_LITERAL}` en ningun parrafo",
        )
        parrafo_consumidor = next(
            (p for p in parrafos_con_merge_base if "**Perfil consumidor**" in p), None
        )
        self.assertIsNotNone(
            parrafo_consumidor,
            "ningun parrafo que arranca declarando el perfil consumidor contrasta la "
            f"sincronizacion con `{self.MERGE_BASE_LITERAL}`: esa verificacion objetiva "
            "solo sobrevive en el parrafo del perfil plugin; el perfil consumidor -- el "
            "que describe el Gherkin 1 de #122 -- seguia apoyado enteramente en el "
            "auto-reporte del sub-agente",
        )

    def test_7_cada_skill_implement_mide_divergencia_contra_la_rama_local(self):
        """Gherkin 3 y 7 de #194: la cuarta respuesta del Paso 0 -- `origin/<RAMA>`
        atrasada respecto de la rama local -- vive en el MISMO parrafo que la
        sincronizacion, no en un parrafo aparte (p. ej. el reporte de salida) donde
        un `Already up to date` legitimo quedaria indistinguible del que miente."""
        for skill in self._skills_implement():
            with self.subTest(skill=skill):
                archivo = ROOT / "skills" / skill / "SKILL.md"
                texto = archivo.read_text(encoding="utf-8")
                parrafos_con_sync = [p for p in self._parrafos(texto) if self.SYNC_LITERAL in p]
                self.assertTrue(
                    parrafos_con_sync,
                    f"{archivo.relative_to(ROOT)} no declara el paso de sincronizacion",
                )
                con_divergencia = [p for p in parrafos_con_sync if self.DIVERGENCIA_LITERAL in p]
                self.assertTrue(
                    con_divergencia,
                    f"{archivo.relative_to(ROOT)}: el parrafo del Paso 0 no mide "
                    f"divergencia contra la rama local ({self.DIVERGENCIA_LITERAL}) -- sin "
                    "eso, un `Already up to date` con el remoto atrasado se confunde con "
                    "el no-op legitimo (heuristics/general/sensor-declara-su-evidencia.md)",
                )
                casos_con_divergencia = [
                    caso
                    for p in con_divergencia
                    for caso in self._casos(p)
                    if self.DIVERGENCIA_LITERAL in caso
                ]
                self.assertTrue(
                    casos_con_divergencia,
                    f"{archivo.relative_to(ROOT)}: ningun caso (bullet) del Paso 0 mide "
                    f"divergencia ({self.DIVERGENCIA_LITERAL})",
                )
                casos_con_conclusion = [
                    caso for caso in casos_con_divergencia
                    if self.CONCLUSION_DIVERGENCIA_LITERAL in caso
                ]
                self.assertTrue(
                    casos_con_conclusion,
                    f"{archivo.relative_to(ROOT)}: el caso (bullet) que mide divergencia "
                    f"({self.DIVERGENCIA_LITERAL}) no concluye deteniendose "
                    f"({self.CONCLUSION_DIVERGENCIA_LITERAL}) en ese MISMO bullet -- una "
                    "medicion sin la conclusion condicional que el Gherkin exige es el "
                    "\"no se\" colapsado en \"no\" otra vez, una capa mas arriba",
                )

    def test_8_consolidate_story_pushea_la_rama_de_la_historia(self):
        """Gherkin 1 y 6 de #194: `consolidate-story` es el archivo que hoy no
        aparece en ningun grep del mecanismo (`RAMA_HISTORIA` ni el literal de
        sync) -- es justo donde nacen los commits que el remoto no ve tras la
        consolidacion (merge de worktrees, providers/rutas, linea del CHANGELOG)."""
        archivo = ROOT / "skills/consolidate-story/SKILL.md"
        texto = archivo.read_text(encoding="utf-8")
        con_push = [p for p in self._parrafos(texto) if self.PUSH_LITERAL in p]
        self.assertTrue(
            con_push,
            f"{archivo.relative_to(ROOT)} no pushea la rama de la historia al cerrar "
            f"la consolidacion (falta un parrafo con `{self.PUSH_LITERAL}`)",
        )

    def test_9_flechodiezx_pushea_antes_de_relanzar(self):
        """Gherkin 2 de #194: antes de relanzar un sub-agente posterior a la
        consolidacion (ronda de correccion del review en `## Fase 5.5`, o una
        reanudacion en `## Fase 0.5`), el orden es push -> verificar -> pasar
        `RAMA_HISTORIA`. El ancla es la SECCION, no el archivo entero:
        `flechodiezx.md` ya trae cuatro `git push -u origin` desde antes de esta
        HU (Fase 2, Fase 3 x2, Fase 6.5) -- una asercion de archivo entero pasa
        hoy, con el arreglo revertido."""
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        for titulo in ("## Fase 0.5", "## Fase 5.5"):
            with self.subTest(seccion=titulo):
                seccion = self._seccion(texto, titulo)
                self.assertTrue(seccion, f"agents/flechodiezx.md no tiene la seccion `{titulo}`")
                parrafos = [
                    p for p in self._parrafos(seccion)
                    if self.PUSH_LITERAL in p and self.RAMA_LITERAL in p
                ]
                self.assertTrue(
                    parrafos,
                    f"la seccion `{titulo}` de agents/flechodiezx.md no tiene un parrafo "
                    f"que pushee ({self.PUSH_LITERAL}) y recien despues pase "
                    f"`{self.RAMA_LITERAL}` antes de relanzar un sub-agente",
                )
                oraciones_con_condicion = [
                    o
                    for p in parrafos
                    for o in self._oraciones(p)
                    if self.PUSH_LITERAL in o and self.RAMA_LITERAL in o
                    and self.CONDICION_PUSH_LITERAL in o
                ]
                self.assertTrue(
                    oraciones_con_condicion,
                    f"la seccion `{titulo}` de agents/flechodiezx.md pushea y pasa "
                    f"`{self.RAMA_LITERAL}` pero ninguna ORACION ata esa secuencia a la "
                    f"condicion vinculante ({self.CONDICION_PUSH_LITERAL}) -- pasar la "
                    "variable sin la condicion reproduce el defecto que #194 cierra",
                )

    def test_10_flechodiezx_pushea_al_cerrar_la_consolidacion(self):
        """Gherkin 1 de #194: red de seguridad del orquestador sobre el push que
        ya intento `consolidate-story` en su Fase C -- no un reemplazo."""
        texto = (ROOT / "agents/flechodiezx.md").read_text(encoding="utf-8")
        seccion = self._seccion(texto, "## Fases 4 y 5")
        self.assertTrue(seccion, "agents/flechodiezx.md no tiene la seccion `## Fases 4 y 5`")
        parrafos = [p for p in self._parrafos(seccion) if self.PUSH_LITERAL in p]
        self.assertTrue(
            parrafos,
            "la seccion `## Fases 4 y 5` de agents/flechodiezx.md no pushea la rama de "
            f"la historia al cerrar la consolidacion (falta un parrafo con "
            f"`{self.PUSH_LITERAL}`)",
        )

    def test_11_hotfix_pushea_antes_de_relanzar_tras_el_review(self):
        """Gherkin 2 (hotfix) de #194: misma precondicion push -> verificar ->
        pasar `RAMA_HISTORIA`, ahora para `fix/N-<slug>`, acotada a la seccion
        `## Fase 3`. `flechodiezx-hotfix.md` ya trae un parrafo con PUSH_LITERAL
        y RAMA_LITERAL juntos en la Fase 2 (reanudacion) desde #122 -- ese
        parrafo no debe satisfacer este caso, que es sobre la ronda de
        correccion del review."""
        texto = (ROOT / "agents/flechodiezx-hotfix.md").read_text(encoding="utf-8")
        seccion = self._seccion(texto, "## Fase 3")
        self.assertTrue(seccion, "agents/flechodiezx-hotfix.md no tiene la seccion `## Fase 3`")
        parrafos = [
            p for p in self._parrafos(seccion)
            if self.PUSH_LITERAL in p and self.RAMA_LITERAL in p
        ]
        self.assertTrue(
            parrafos,
            "la seccion `## Fase 3` de agents/flechodiezx-hotfix.md no tiene un parrafo "
            f"que pushee ({self.PUSH_LITERAL}) y recien despues pase "
            f"`{self.RAMA_LITERAL}` antes de relanzar el sub-agente de correccion",
        )
        oraciones_con_condicion = [
            o
            for p in parrafos
            for o in self._oraciones(p)
            if self.PUSH_LITERAL in o and self.RAMA_LITERAL in o
            and self.CONDICION_PUSH_LITERAL in o
        ]
        self.assertTrue(
            oraciones_con_condicion,
            "la seccion `## Fase 3` de agents/flechodiezx-hotfix.md pushea y pasa "
            f"`{self.RAMA_LITERAL}` pero ninguna ORACION ata esa secuencia a la condicion "
            f"vinculante ({self.CONDICION_PUSH_LITERAL}) -- pasar la variable sin la "
            "condicion reproduce el defecto que #194 cierra",
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
        """Antes solo exigia la presencia de la palabra `integracion` en onboard.md: un
        bug -- pasaba con cualquier mencion, incluso una que dijera "no preguntes por
        integracion" sin fijar ningun valor. Ahora afirma la semantica (#85): el valor se
        escribe fijo (`"pr"`) y onboard.md ya no pregunta por `protectBase` como via para
        seguir comiteando en la base (ese flag quedo deprecado e ignorado, TIM-ADR-0002)."""
        adr = (ROOT / "docs/adr/tim-adr-0002-configuracion-del-consumidor.md").read_text(encoding="utf-8")
        onboard = (ROOT / "commands/onboard.md").read_text(encoding="utf-8")
        self.assertIn("git.integracion", adr, "tim-adr-0002 debe documentar `git.integracion`")
        self.assertIn('"integracion": "pr"', onboard, "onboard.md debe fijar `integracion` en \"pr\"")
        self.assertIn("unico valor valido", onboard, "onboard.md debe declarar que \"pr\" es el unico valor valido")
        self.assertNotIn(
            "Pregunta si el equipo commitea directo a la rama base", onboard,
            "onboard.md ya no debe preguntar por protectBase: el flag quedo deprecado e ignorado",
        )

    def test_receta_de_proteccion_de_rama_esta_completa(self):
        """Caso 9 del contrato de #85 (comentario `timonel:contrato-api`), nunca
        implementado -- el review de #85 lo marco WARNING: no habia ningun test que
        verificara la receta de proteccion de rama del Paso 2.5 de `onboard.md`. Los
        CUATRO campos top-level son *required* en la API de GitHub aunque acepten `null`
        (omitir uno da 422); una receta que se recorte a dos campos lo daria y ningun
        test lo detectaria."""
        onboard = (ROOT / "commands/onboard.md").read_text(encoding="utf-8")
        campos = (
            "required_status_checks",
            "enforce_admins",
            "required_pull_request_reviews",
            "restrictions",
        )
        for campo in campos:
            self.assertIn(
                campo, onboard,
                f"onboard.md debe nombrar el campo `{campo}` en la receta de proteccion de rama (los 4 son required en la API)",
            )
        self.assertIn(
            "403", onboard,
            "onboard.md debe documentar el manejo del 403 (falta de permiso de admin) de la receta de proteccion de rama",
        )


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
