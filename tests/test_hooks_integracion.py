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
