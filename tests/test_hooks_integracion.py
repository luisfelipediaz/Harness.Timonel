"""Tests del guard de integracion por PR (epica #79, #82): `scripts/guard_integracion.py`
y su cableado en `hooks/hooks.json`.

Dos capas:
  - `GuardIntegracionPuroTests`: la funcion pura `decidir(cmd, rama, bases)` sobre la
    TABLA_DE_CASOS, sin tocar disco ni procesos.
  - `HookEnCajaNegraTests`: extrae los comandos REALES de `hooks/hooks.json` (no una
    copia pegada) y los corre con `bash -c` sobre un repo git temporal, tal como los
    correria Claude Code. Es el patron que faltaba (Dora, #82): hasta ahora nada
    ejecutaba el shell de hooks.json, solo se hacia `assertIn` sobre el string.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import guard_integracion as gi  # noqa: E402

BLOQUEADO = "bloqueado"
PERMITIDO = "permitido"

# Cada fila = un caso del contrato del issue #82. `rama` es la rama actual antes de
# correr `cmd`; `esperado` es BLOQUEADO (exit 2, mensaje en stderr) o PERMITIDO
# (exit 0, sin salida). Agregar un caso nuevo es agregar una fila.
TABLA_DE_CASOS = [
    # numero, rama, cmd, esperado
    (1, "hu/82-x", "git push origin main", BLOQUEADO),
    (2, "main", "git push", BLOQUEADO),
    (3, "main", "git push origin HEAD", BLOQUEADO),
    (4, "hu/82-x", "git push origin hu/82-x:main", BLOQUEADO),
    (5, "main", "git push --all origin", BLOQUEADO),
    (6, "main", "git merge hu/82-x", BLOQUEADO),
    (7, "main", "git merge --ff-only hu/82-x", BLOQUEADO),  # el agujero de #30
    (8, "hu/82-x", "git checkout main && git merge --ff-only hu/82-x", BLOQUEADO),  # el compuesto no evade
    (9, "main", "git pull", BLOQUEADO),
    (10, "main", "git pull --ff-only origin hu/82-x", BLOQUEADO),
    (11, "main", "gh pr merge 94 --squash", BLOQUEADO),
    (12, "hu/82-x", "gh pr merge --auto 94", BLOQUEADO),
    (14, "main", "git checkout main && git merge --ff-only origin/main", PERMITIDO),
    (15, "hu/82-x", "git checkout main && git merge --ff-only origin/main", PERMITIDO),
    (16, "main", "git pull --ff-only", PERMITIDO),
    (17, "main", "git pull --ff-only origin main", PERMITIDO),
    (18, "main", "git merge --ff-only @{u}", PERMITIDO),
    (19, "hu/82-x", "git push -u origin hu/82-x", PERMITIDO),
    ("20a", "hu/82-x", "gh pr create --fill", PERMITIDO),
    ("20b", "hu/82-x", "gh pr view 94", PERMITIDO),
    ("20c", "hu/82-x", "gh pr checks", PERMITIDO),
    (21, "main-fix", "git push origin main-fix", PERMITIDO),  # frontera de substring
    (22, "hu/82-x", "git merge hu/82-backend", PERMITIDO),  # consolidacion de worktrees
    (26, "main", "git merge --abort", PERMITIDO),
    # --- review de #82: separador pegado a un token evade el guard (CRITICO) ---
    (27, "hu/82-x", "git checkout main; git merge hu/x", BLOQUEADO),  # ; pegado
    (28, "hu/82-x", "git checkout main ; git merge hu/x", BLOQUEADO),  # ; separado
    (29, "hu/82-x", "git checkout main; git merge --ff-only hu/x", BLOQUEADO),  # ; pegado + agujero #30
    (30, "hu/82-x", "git switch main; git merge hu/x", BLOQUEADO),  # ; pegado con switch
    (31, "hu/82-x", "git checkout main&&git merge hu/x", BLOQUEADO),  # && pegado
    (32, "hu/82-x", "git checkout main && git merge hu/x", BLOQUEADO),  # && separado
    (33, "hu/82-x", "git checkout main||git merge hu/x", BLOQUEADO),  # || pegado
    (34, "hu/82-x", "git checkout main || git merge hu/x", BLOQUEADO),  # || separado
    # --- warnings del review de #82 ---
    (35, "hu/82-x", "git -C /otro/repo push origin main", BLOQUEADO),  # -C salteado
    (36, "hu/82-x", "git push origin hu/x:refs/heads/main", BLOQUEADO),  # refs/heads/ normalizado
    (37, "hu/82-x", "GIT_DIR=.git git push origin main", BLOQUEADO),  # prefijo VAR=valor descartado
    # --- comillas: un separador dentro de comillas no es separador (trampa del arreglo) ---
    (38, "hu/82-x", 'git commit -m "fix del parser; ver #82"', PERMITIDO),  # ; interno no es separador
    (39, "hu/82-x", 'git checkout main && git merge hu/x -m "algo; con punto y coma"', BLOQUEADO),  # && externo si separa
    # --- regresion: esto ya funcionaba y no debe romperse ---
    (40, "main", "git pull origin main --ff-only", PERMITIDO),  # flags despues de la ref
    (41, "main", "git merge  --ff-only  origin/main", PERMITIDO),  # espacios multiples
    (42, "hu/82-x", "git push origin +hu/x:main", BLOQUEADO),
    (43, "main", "git push origin HEAD:main", BLOQUEADO),
    (44, "main", "git pull --rebase", BLOQUEADO),
    (45, "main", "git push --mirror origin", BLOQUEADO),
    (46, "hu/82-x", "git switch main && git merge hu/x", BLOQUEADO),
    # --- review ronda 2 de #82: CRITICO, separadores no tratados evaden el guard ---
    # salto de linea: como Bash entrega comandos multilinea todo el tiempo (no una
    # evasion deliberada) -- el mas grave de los cuatro.
    (47, "hu/82-x", "git checkout main\ngit merge hu/x", BLOQUEADO),  # \n pegado
    (48, "hu/82-x", "git checkout main \n git merge hu/x", BLOQUEADO),  # \n separado
    (49, "hu/82-x", "git checkout main\r\ngit merge hu/x", BLOQUEADO),  # \r\n pegado
    (50, "hu/82-x", "git checkout main \r\n git merge hu/x", BLOQUEADO),  # \r\n separado
    (51, "hu/82-x", "git status\ngit checkout main\ngit merge hu/82-x", BLOQUEADO),  # multilinea realista de 3 lineas
    # de fondo (&)
    (52, "hu/82-x", "git checkout main&git merge hu/x", BLOQUEADO),  # & pegado
    (53, "hu/82-x", "git checkout main & git merge hu/x", BLOQUEADO),  # & separado
    # pipe simple (|)
    (54, "hu/82-x", "git checkout main|git merge hu/x", BLOQUEADO),  # | pegado
    (55, "hu/82-x", "git checkout main | git merge hu/x", BLOQUEADO),  # | separado
    # agrupacion (...)
    (56, "hu/82-x", "(git checkout main && git merge hu/x)", BLOQUEADO),  # agrupado
    # \n dentro de comillas NO es separador
    (57, "hu/82-x", 'git commit -m "linea1\nlinea2"', PERMITIDO),
    # --- warnings ronda 2: flag-skip pegado ---
    (58, "hu/82-x", "git -Cpath push origin main", BLOQUEADO),  # -C pegado
    (59, "main", "git -c user.name=x merge hu/z", BLOQUEADO),  # -c global rompia la deteccion del subcomando
    (60, "main", "git -cuser.name=x merge hu/z", BLOQUEADO),  # -c pegado
    # --- warning ronda 2: casos limite de escapes (fijan el comportamiento actual) ---
    (61, "hu/82-x", 'git commit -m "cita \\"escapada\\" adentro"', PERMITIDO),  # backslash antes de comilla
    (63, "main", "git merge \\;hu/x", BLOQUEADO),  # backslash antes de separador: no evade, ref insegura en base
    (64, "hu/82-x", "git commit -m 'a;b'\\''c;d'", PERMITIDO),  # comillas anidadas simples (idioma it's)
    (65, "hu/82-x", 'git commit -m "mix \'single\' and \\"double\\""', PERMITIDO),  # comillas mixtas
    # el que SI resulto explotable (ver mutacion/reporte): comilla escapada + && sin espacio
    # -> en Bash real corre igual (`"a\"b"&&git merge x` ejecuta las dos), y el tracker
    # simple (sin reconocer el escape) lo dejaba pasar. Ya corregido arriba.
    (66, "main", 'git commit -m "a\\"b"&&git merge hu/x', BLOQUEADO),  # explotable, corregido
    (67, "main", 'git commit -m "a\\"b";git merge hu/x', BLOQUEADO),  # idem con ;
    # --- limitacion aceptada y documentada (NO perseguir): evasion deliberada ---
    # guard != sandbox; cada capa de parser nueva para cubrir esto es superficie de
    # bug nueva (ver docstring del modulo y CHANGELOG). Si este test empieza a fallar
    # porque alguien "lo arreglo", que sea una decision, no un descuido.
    (68, "main", 'eval "git merge hu/x"', PERMITIDO),  # limite conocido: eval
    (69, "main", 'bash -c "git merge hu/x"', PERMITIDO),  # limite conocido: bash -c
    # $(...) no se inspecciona por dentro, pero lo que queda AFUERA del `$()` se
    # juzga normalmente contra la rama REAL: parado en "main" (base), el
    # "&& git merge hu/x" es visible fuera del command substitution y bloquea.
    # Lo que NO se cubre es `$()` envolviendo el comando ENTERO (eso si seguiria
    # evadiendo, pero no es este caso).
    (70, "main", "$(git checkout main) && git merge hu/x", BLOQUEADO),  # $(...) no oculta lo de afuera

    # --- review #4 de #82: flags globales booleanos, la REGLA no una lista ---
    (71, "hu/82-x", "git --no-pager push origin main", BLOQUEADO),
    (72, "hu/82-x", "git --paginate push origin main", BLOQUEADO),
    (73, "hu/82-x", "git -P push origin main", BLOQUEADO),
    (74, "hu/82-x", "git --bare push origin main", BLOQUEADO),
    (75, "hu/82-x", "git --literal-pathspecs push origin main", BLOQUEADO),
    (76, "hu/82-x", "git --flag-que-no-existe push origin main", BLOQUEADO),  # inventado: prueba la regla, no la lista
    (77, "hu/82-x", "git --no-pager -C /otro push origin main", BLOQUEADO),  # booleano + con-valor combinados
    (78, "main", "git -c user.name=x --no-pager merge hu/z", BLOQUEADO),  # idem, con merge en base

    # --- review #2 de #82: rebase y cherry-pick sobre la rama base ---
    (79, "main", "git rebase hu/x", BLOQUEADO),
    (80, "main", "git cherry-pick abc1234", BLOQUEADO),
    (81, "hu/82-x", "git rebase hu/x", PERMITIDO),  # fuera de base, normal
    (82, "hu/82-x", "git cherry-pick abc1234", PERMITIDO),  # fuera de base, normal
    (83, "main", "git rebase origin/main", PERMITIDO),  # ref segura: sync
    (84, "main", "git rebase --continue", PERMITIDO),
    (85, "main", "git rebase --abort", PERMITIDO),
    (86, "main", "git rebase --skip", PERMITIDO),
    (87, "main", "git rebase --quit", PERMITIDO),
    (88, "main", "git cherry-pick --continue", PERMITIDO),
    (89, "main", "git cherry-pick --abort", PERMITIDO),

    # --- review #3 de #82: gh api como puerta trasera de gh pr merge ---
    (90, "hu/82-x", "gh api -X PUT repos/o/r/pulls/94/merge", BLOQUEADO),
    (91, "hu/82-x", "gh api --method PUT repos/o/r/pulls/94/merge", BLOQUEADO),
    (92, "hu/82-x", "gh api repos/o/r/pulls/94/merge", BLOQUEADO),  # sin metodo, igual bloqueado
    (93, "hu/82-x", "gh api repos/o/r/pulls/94", PERMITIDO),  # sin /merge: solo lectura
    (94, "hu/82-x", "gh api user", PERMITIDO),

    # --- ronda final de #82: gh api /merges (Merge a branch, sin PR) ---
    (95, "hu/82-x", "gh api -X POST repos/o/r/merges -f base=main -f head=hu/x", BLOQUEADO),
    (96, "hu/82-x", "gh api repos/o/r/merges", BLOQUEADO),
    (97, "hu/82-x", "gh api repos/o/merged-stuff/pulls/1", PERMITIDO),  # "merge" no es el segmento final

    # --- ronda final de #82: git revert / git am, misma familia que cherry-pick ---
    (98, "main", "git revert abc1234", BLOQUEADO),
    (99, "main", "git am /tmp/p.patch", BLOQUEADO),
    (100, "hu/82-x", "git revert abc1234", PERMITIDO),  # fuera de base, normal
    (101, "hu/82-x", "git am /tmp/p.patch", PERMITIDO),  # fuera de base, normal
    (102, "main", "git revert --abort", PERMITIDO),  # forma de control
    (103, "main", "git am --continue", PERMITIDO),  # forma de control

    # --- ronda final de #82: git reset --hard a una ref no segura ---
    (104, "main", "git reset --hard hu/x", BLOQUEADO),  # mueve main a codigo no revisado
    (105, "main", "git reset --hard origin/main", PERMITIDO),  # sync, ref segura
    (106, "hu/82-x", "git reset --hard hu/x", PERMITIDO),  # fuera de base, normal
    # decision documentada (ver _revisar_reset): el criterio de ref segura no
    # distingue modo, solo ref -- HEAD~1 no es vacia ni origin/main, bloquea
    # igual que --hard aunque --soft no toque el working tree.
    (107, "main", "git reset --soft HEAD~1", BLOQUEADO),
]

BASES = ["main", "master", "develop"]


class GuardIntegracionPuroTests(unittest.TestCase):
    """`decidir()` sobre la tabla, sin disco ni procesos."""

    def test_tabla_de_casos(self):
        for numero, rama, cmd, esperado in TABLA_DE_CASOS:
            with self.subTest(caso=numero, cmd=cmd, rama=rama):
                mensaje = gi.decidir(cmd, rama, BASES)
                if esperado == BLOQUEADO:
                    self.assertIsNotNone(mensaje, f"caso {numero}: deberia bloquear `{cmd}` en `{rama}`")
                    self.assertTrue(mensaje.startswith("[timonel] Bloqueado: "))
                else:
                    self.assertIsNone(mensaje, f"caso {numero}: deberia permitir `{cmd}` en `{rama}`, bloqueo con: {mensaje}")

    def test_mensaje_push_a_base_es_accionable(self):
        mensaje = gi.decidir("git push origin main", "hu/82-x", BASES)
        self.assertIn("git push -u origin hu/<issue>-<slug>", mensaje)
        self.assertIn("epica #79", mensaje)

    def test_mensaje_merge_en_base_incluye_alternativa_de_pull(self):
        mensaje = gi.decidir("git merge hu/82-x", "main", BASES)
        self.assertIn("git merge --ff-only origin/main", mensaje)
        self.assertIn("git pull --ff-only", mensaje)

    def test_mensaje_pull_sin_ff_only_incluye_literal(self):
        mensaje = gi.decidir("git pull", "main", BASES)
        self.assertIn("git pull --ff-only", mensaje)

    def test_mensaje_rebase_ofrece_rebase_no_generico_de_merge(self):
        mensaje = gi.decidir("git rebase hu/x", "main", BASES)
        self.assertIn("git rebase origin/main", mensaje)

    def test_mensaje_reset_ofrece_reset_hard_origin_base(self):
        mensaje = gi.decidir("git reset --hard hu/x", "main", BASES)
        self.assertIn("git reset --hard origin/main", mensaje)

    def test_mensaje_cherry_pick_revert_am_ofrece_pr_no_ff_only(self):
        """Aserciones no vacias (#82 ronda final): a quien quiere llevar un commit a
        la base, sincronizar no le sirve. Si el mensaje vuelve al generico de
        `merge` (`--ff-only`), este test debe fallar -- ver mutacion obligatoria."""
        for cmd in ("git cherry-pick abc1234", "git revert abc1234", "git am /tmp/p.patch"):
            with self.subTest(cmd=cmd):
                mensaje = gi.decidir(cmd, "main", BASES)
                self.assertIn("abri el PR", mensaje)
                self.assertIn("git checkout hu/<issue>-<slug>", mensaje)
                self.assertNotIn("--ff-only", mensaje)

    def test_mensaje_gh_pr_merge_explica_via_humana(self):
        mensaje = gi.decidir("gh pr merge 1", "main", BASES)
        self.assertIn("humano", mensaje)
        self.assertIn("epica #79", mensaje)

    def test_shlex_invalido_es_fail_open(self):
        self.assertIsNone(gi.decidir("git push origin main 'sin cerrar", "main", BASES))

    def test_shlex_invalido_deja_rastro_auditable_en_events_log(self):
        """Fail-open silencioso == agujero que se descubre por casualidad seis HUs
        despues. El fail-open sigue permitiendo el comando, pero ahora queda rastro."""
        import os

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cwd = Path.cwd()
            try:
                os.chdir(tmp_path)
                self.assertIsNone(gi.decidir("git push origin main 'sin cerrar", "main", BASES))
            finally:
                os.chdir(cwd)
            log = tmp_path / ".timonel/events.log"
            self.assertTrue(log.exists(), "el fail-open deberia crear .timonel/events.log")
            contenido = log.read_text(encoding="utf-8")
            self.assertIn("guard-integracion-fail-open shlex-invalido", contenido)

    def test_fail_open_nunca_rompe_el_guard_si_no_puede_escribir_el_log(self):
        """Si .timonel no se puede crear (p. ej. un archivo ocupa ese nombre), el
        fail-open sigue devolviendo None: escribir el log nunca hace fallar el guard."""
        import os

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".timonel").write_text("no es un directorio", encoding="utf-8")
            cwd = Path.cwd()
            try:
                os.chdir(tmp_path)
                self.assertIsNone(gi.decidir("git push origin main 'sin cerrar", "main", BASES))
            finally:
                os.chdir(cwd)

    def test_bases_configuradas_lee_config_del_consumidor(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".claude").mkdir()
            (tmp_path / ".claude/timonel.config.json").write_text(
                json.dumps({"git": {"baseBranches": ["trunk"]}}), encoding="utf-8"
            )
            cwd = Path.cwd()
            try:
                import os

                os.chdir(tmp_path)
                self.assertEqual(gi._bases_configuradas(), ["trunk"])
            finally:
                os.chdir(cwd)

    def test_bases_configuradas_por_defecto_sin_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path.cwd()
            try:
                import os

                os.chdir(tmp)
                self.assertEqual(gi._bases_configuradas(), ["main", "master", "develop"])
            finally:
                os.chdir(cwd)


def _comandos_pretooluse() -> list[str]:
    """Extrae, del hooks.json REAL, los comandos del bloque PreToolUse/Bash."""
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    comandos = []
    for bloque in hooks["hooks"]["PreToolUse"]:
        for hook in bloque["hooks"]:
            comandos.append(hook["command"])
    return comandos


def _comando_guard_integracion() -> str:
    for cmd in _comandos_pretooluse():
        if "guard_integracion.py" in cmd:
            return cmd
    raise AssertionError("hooks.json no tiene ningun guard que invoque guard_integracion.py")


def _comando_push_force() -> str:
    for cmd in _comandos_pretooluse():
        if "push" in cmd and "--force" in cmd:
            return cmd
    raise AssertionError("hooks.json no tiene el guard de push --force")


def _preparar_repo(tmp: Path, rama: str, perfil: str) -> None:
    subprocess.run(["git", "init", "-q", "-b", rama], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "a@a.com"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", "init"], cwd=tmp, check=True)
    if rama != "main":
        subprocess.run(["git", "branch", "main"], cwd=tmp, check=True)
    if perfil == "plugin":
        (tmp / ".claude-plugin").mkdir(exist_ok=True)
        (tmp / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "timonel"}), encoding="utf-8")
    elif perfil == "consumidor":
        (tmp / ".claude").mkdir(exist_ok=True)
        (tmp / ".claude/timonel.config.json").write_text(json.dumps({"github": {"repo": "o/r"}}), encoding="utf-8")


def _correr_hook(comando_hook: str, cmd_bash: str, tmp: Path, plugin_root: str) -> subprocess.CompletedProcess:
    import os

    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = plugin_root
    payload = json.dumps({"tool_input": {"command": cmd_bash}})
    return subprocess.run(
        ["bash", "-c", comando_hook],
        input=payload,
        capture_output=True,
        text=True,
        cwd=tmp,
        env=env,
    )


class HookEnCajaNegraTests(unittest.TestCase):
    """Corre el shell REAL de hooks.json sobre un repo git temporal (perfil plugin)."""

    def test_tabla_de_casos_contra_el_hook_real(self):
        comando = _comando_guard_integracion()
        for numero, rama, cmd, esperado in TABLA_DE_CASOS:
            with self.subTest(caso=numero, cmd=cmd, rama=rama):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = Path(tmp)
                    _preparar_repo(tmp_path, rama, perfil="plugin")
                    resultado = _correr_hook(comando, cmd, tmp_path, plugin_root=str(ROOT))
                    if esperado == BLOQUEADO:
                        self.assertEqual(resultado.returncode, 2, f"caso {numero}: stderr={resultado.stderr!r}")
                        self.assertIn("[timonel] Bloqueado: ", resultado.stderr)
                    else:
                        self.assertEqual(resultado.returncode, 0, f"caso {numero}: stderr={resultado.stderr!r}")
                        self.assertEqual(
                            resultado.stderr,
                            "",
                            f"caso {numero}: no deberia imprimir nada en stderr, obtuvo {resultado.stderr!r}",
                        )

    def test_repo_sin_harness_no_bloquea_nada(self):
        """Caso 23: sin .claude/timonel.config.json ni plugin.json de timonel, el guard no corre."""
        comando = _comando_guard_integracion()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _preparar_repo(tmp_path, "main", perfil="ninguno")
            for cmd in ("git push origin main", "git merge hu/82-x", "gh pr merge 1"):
                resultado = _correr_hook(comando, cmd, tmp_path, plugin_root=str(ROOT))
                self.assertEqual(resultado.returncode, 0, f"`{cmd}` sin harness no deberia bloquear: {resultado.stderr!r}")

    def test_script_ausente_es_fail_open_caso_25(self):
        """Caso 25: perfil plugin pero guard_integracion.py no se puede resolver -> pasa."""
        comando = _comando_guard_integracion()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _preparar_repo(tmp_path, "main", perfil="plugin")
            plugin_root_inexistente = str(tmp_path / "no-existe")
            resultado = _correr_hook(comando, "git merge hu/82-x", tmp_path, plugin_root=plugin_root_inexistente)
            self.assertEqual(resultado.returncode, 0, f"stderr={resultado.stderr!r}")

    def test_push_force_bloqueado_en_perfil_plugin_caso_13(self):
        comando = _comando_push_force()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _preparar_repo(tmp_path, "hu/82-x", perfil="plugin")
            resultado = _correr_hook(comando, "git push --force origin hu/82-x", tmp_path, plugin_root=str(ROOT))
            self.assertEqual(resultado.returncode, 2)
            self.assertIn("[timonel] Bloqueado", resultado.stderr)

    def test_push_force_bloqueado_incondicional_sin_script_caso_24(self):
        """Caso 24: aunque guard_integracion.py sea inexistente/no resoluble, --force sigue bloqueado
        (es la protección INCONDICIONAL, no fail-open) -- vive inline, no depende del script python."""
        comando = _comando_push_force()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _preparar_repo(tmp_path, "hu/82-x", perfil="plugin")
            plugin_root_inexistente = str(tmp_path / "no-existe")
            resultado = _correr_hook(comando, "git push --force origin hu/82-x", tmp_path, plugin_root=plugin_root_inexistente)
            self.assertEqual(resultado.returncode, 2, f"stderr={resultado.stderr!r}")
            self.assertIn("[timonel] Bloqueado", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
