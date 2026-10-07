#!/usr/bin/env python3
"""Sensor del estado del PR para el item 1 del DoD (issue #81, epica #79).

Uso:
    python3 pr_check.py <issue> [--repo owner/repo] [--base main] [--espera 60]
    python3 pr_check.py <issue> --json '<array de `gh pr list` --json ...>'   # tests

El sensor descubre el PR solo: toma la rama actual (`git rev-parse --abbrev-ref
HEAD`) y verifica que referencie el issue (`hu/<N>-*` / `fix/<N>-*`, mismos
prefijos que `estado_historia.PREFIJOS_RAMA`). No recibe `pr_url` -- un dato que
el orquestador *afirma* es falsificable con un copy-paste de otro PR; `gh pr
list --head <rama>` es evidencia de GitHub ligada a la rama (decision D1 del
contrato de #81). `--pr`/`--rama` existen solo para depurar a mano; el skill
`verify-dod` nunca los usa.

Imprime `ESTADO: PASSED|FAILED`, `CRITICIDAD: critico|no-critico|n-a`,
`MOTIVO: <texto>`, `PR: <url o n-a>`. Sale 0 si `ESTADO` empieza por `PASSED`,
1 si no.

Dos decisiones que el codigo no puede explicar solo:

1. `BLOCKED` (en `mergeStateStatus`) es el estado **normal** de un PR sano bajo
   branch protection con review humano obligatorio: el PR es mergeable y sus
   checks estan verdes, pero GitHub igual lo marca `BLOCKED` porque falta la
   aprobacion de un humano. Tratarlo como falla haria que el DoD nunca diera
   `DONE` bajo esa politica -- exactamente el dia en que se active branch
   protection real (epica #79, #85). Por eso de `mergeStateStatus` solo se usan
   dos valores (`DIRTY` y `BEHIND`, decision D2); el resto (`CLEAN`, `BLOCKED`,
   `UNSTABLE`, `HAS_HOOKS`, `UNKNOWN`, `DRAFT`) no altera el veredicto: lo que
   importa ya esta cubierto por `mergeable`, `isDraft` y `statusCheckRollup`.

2. El detector de workflows (`hay_workflows`, la existencia de
   `.github/workflows/*.y*ml`) tiene un limite conocido: un repo cuyos
   workflows existen pero **ninguno** dispara en el evento `pull_request`
   (por ejemplo, solo corren en `push` a `main` o en `schedule`) siempre cae
   en el caso 18 (`statusCheckRollup` vacio + hay workflows -> `PENDIENTES`
   permanente), aunque nunca vaya a llegar un check. No se resuelve parseando
   el `on:` de cada workflow con regex -- la stdlib no trae YAML, y un parser
   de triggers es justo la clase de fragil que la epica #82 (guard de
   integracion) enseño a no escribir. El dano esta acotado: es **no critico**,
   el motivo lo nombra, y no bloquea el cierre. Criterio de parada: si aparece
   un consumidor real con esa forma, se resuelve consultando
   `gh api repos/{owner}/{repo}/actions/workflows` (lista los workflows y sus
   estados sin parsear su contenido), no agregando un parser de YAML.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from estado_historia import PREFIJOS_RAMA
from integracion import tipo_remote
from timonel_gh import numero_issue, repo_from_config

CAMPOS_PR = "number,url,state,isDraft,baseRefName,headRefName,body,mergeable,mergeStateStatus,statusCheckRollup"

_RAMA_RE = re.compile(rf"^(?:{'|'.join(re.escape(p) for p in PREFIJOS_RAMA)})/(\d+)-")
_CIERRA_ISSUE_RE = re.compile(r"\b(?:Closes|Fixes|Resolves)\s+#(\d+)\b", re.IGNORECASE)

# R5: dos `__typename` de `statusCheckRollup` se normalizan al mismo eje. Todo
# valor fuera del mapa cae en "desconocido", que nunca es verde y siempre se
# nombra en el motivo. Agregar un estado nuevo de GitHub es agregar una fila,
# no tocar el parser.
_CONCLUSION_A_EJE: dict[str, str] = {
    "SUCCESS": "verde", "NEUTRAL": "verde", "SKIPPED": "verde",
    "FAILURE": "rojo", "TIMED_OUT": "rojo", "CANCELLED": "rojo",
    "ACTION_REQUIRED": "rojo", "STARTUP_FAILURE": "rojo", "STALE": "rojo",
}
_STATUS_EN_CURSO = {"QUEUED", "IN_PROGRESS", "WAITING", "PENDING", "REQUESTED"}
_STATE_A_EJE: dict[str, str] = {
    "SUCCESS": "verde", "FAILURE": "rojo", "ERROR": "rojo",
    "PENDING": "en_curso", "EXPECTED": "en_curso",
}
# Precedencia del rollup: rojo > desconocido > en_curso > verde.
_PRECEDENCIA: dict[str, int] = {"rojo": 0, "desconocido": 1, "en_curso": 2, "verde": 3}


@dataclass
class Veredicto:
    estado: str        # PASSED | FAILED
    criticidad: str     # critico | no-critico | n-a (n-a solo si estado es PASSED)
    motivo: str
    pr: str              # url del PR, o "n-a" si no se identifico ninguno


def _rama_corresponde(rama: str, issue: int) -> bool:
    m = _RAMA_RE.match(rama or "")
    return bool(m) and int(m.group(1)) == issue


def _cierra_issue(body: str, issue: int) -> bool:
    return any(int(n) == issue for n in _CIERRA_ISSUE_RE.findall(body or ""))


def _unir(items: list[str]) -> str:
    """Une una lista para prosa en español: sin "y" con uno solo, "y" antes
    del ultimo con dos o mas, sin coma serial (`#1 y #2`, `#1, #2 y #3`)."""
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + f" y {items[-1]}"


def _frase_pr(items: list[str], forma_singular: str, forma_plural: str) -> str:
    """Concuerda "el/los PR" y una forma verbal con la cardinalidad de
    `items` (WARNING cosmetico del review de #81: con varios PRs el motivo
    quedaba en singular, ej. "el PR #1, #2 esta cerrado sin merge"). Un unico
    punto de formato en vez de repetir el condicional en cada motivo que
    nombra uno o mas PRs."""
    sujeto = "el PR " if len(items) == 1 else "los PR "
    forma = forma_singular if len(items) == 1 else forma_plural
    return f"{sujeto}{_unir(items)} {forma}"


def _analizar_check(check: dict) -> tuple[str, str, str, str]:
    """(eje, nombre, valor, typename) de un elemento de `statusCheckRollup`.

    Un check sin su campo identificador (`context` en StatusContext, `name`
    en CheckRun) no es confiable aunque su conclusion sea verde: no hay forma
    de nombrarlo por su identidad, asi que el eje cae en "desconocido" (nunca
    "verde") -- la misma logica que ya aplica a un valor de conclusion fuera
    del mapa (hallazgo #3 del review de #81: una entrada degenerada nunca es
    PASSED). El motivo si distingue ambos casos (`nombre == "?"` marca la
    falta de identificador): "sin identificador" no es lo mismo que "estado
    no reconocido" -- decirle a SUCCESS "estado desconocido" seria falso
    (WARNING cosmetico del mismo review). Ver `_MOTIVO_POR_EJE["desconocido"]`.
    """
    typename = check.get("__typename", "CheckRun")
    if typename == "StatusContext":
        contexto = check.get("context")
        valor = check.get("state", "")
        if not contexto:
            return "desconocido", "?", valor, typename
        return _STATE_A_EJE.get(valor, "desconocido"), contexto, valor, typename
    nombre = check.get("name")
    if not nombre:
        return "desconocido", "?", check.get("conclusion") or check.get("status") or "", typename
    if check.get("status") != "COMPLETED":
        estado = check.get("status", "")
        eje = "en_curso" if estado in _STATUS_EN_CURSO else "desconocido"
        return eje, nombre, estado, typename
    valor = check.get("conclusion", "")
    return _CONCLUSION_A_EJE.get(valor, "desconocido"), nombre, valor, typename


def _motivo_en_curso(nombre: str, typename: str) -> str:
    if typename == "StatusContext":
        return f"checks en curso ({nombre})"
    return f"checks en curso ({nombre}); reevaluá al terminar"


def _motivo_desconocido(nombre: str, valor: str, typename: str) -> str:
    """Bifurca el unico mensaje que compartian dos causas distintas (WARNING
    cosmetico del review de #81): sin identificador (`nombre == "?"`, el
    campo falta) vs. estado no reconocido (el campo esta, su valor no)."""
    if nombre == "?":
        campo = "context" if typename == "StatusContext" else "name"
        return f"check sin {campo} identificable (estado {valor}); no cuenta como verde"
    return f"check {nombre}: estado desconocido {valor}"


_MOTIVO_POR_EJE = {
    "rojo": lambda nombre, valor, typename: f"check {nombre} en rojo ({valor})",
    "desconocido": _motivo_desconocido,
    "en_curso": lambda nombre, valor, typename: _motivo_en_curso(nombre, typename),
}


def _estado_checks(checks: list[dict]) -> tuple[str, str]:
    """(eje predominante, motivo) del rollup ya sabido no vacio."""
    analizados = [_analizar_check(c) for c in checks]
    eje, nombre, valor, typename = min(analizados, key=lambda a: _PRECEDENCIA[a[0]])
    if eje == "verde":
        return eje, ""
    return eje, _MOTIVO_POR_EJE[eje](nombre, valor, typename)


def evaluar(
    prs: list[dict],
    issue: int,
    rama: str,
    base: str,
    tipo_remote: str,
    hay_workflows: bool,
    gh_error: str | None = None,
    espera: int = 60,
) -> Veredicto:
    """Traduce el estado de GitHub (PR + checks) a un veredicto del item 1 del DoD.

    Pura: no ejecuta `gh` ni `git`. Las reglas se evaluan en el orden del
    contrato de #81 (R0 remote/herramienta -> R1 rama/existencia -> R2 estado
    -> R3 forma -> R4 merge -> R5 checks); la primera que aplica decide.

    Guard clauses, no una lista de tuplas `(predicado, resultado)` recorrida
    con `next()` al estilo `_PATRONES` de `integracion.py` -- alternativa
    evaluada y descartada en el review de #81. En `_PATRONES` todos los
    predicados deciden sobre un unico string (la URL del remote), por eso una
    tabla de datos los captura sin perdida. Aca los predicados cierran sobre
    objetos heterogeneos -- el remote, la rama, la lista completa de PRs, un
    PR individual, la lista de checks --, asi que una tupla necesitaria un
    parametro comun artificial o closures sobre variables externas, y las dos
    opciones son mas indirectas que el guard clause que ya esta. Criterio de
    desempate: ¿se lee igual que la tabla de 27 casos que lo especifica? Los
    guard clauses, leidos en orden, si; una lista de tuplas con closures no
    mejora esa lectura y agrega una capa mas.
    """
    if tipo_remote == "azure-devops":
        return Veredicto("FAILED", "no-critico", "remote azure-devops: gh pr no aplica; verificá el PR a mano", "n-a")
    if tipo_remote == "desconocido":
        return Veredicto("FAILED", "no-critico", "remote no reconocido: verificá el PR a mano", "n-a")
    if gh_error:
        return Veredicto("FAILED", "critico", f"no se pudo verificar el PR: {gh_error}", "n-a")

    if not _rama_corresponde(rama, issue):
        return Veredicto("FAILED", "critico", f"la rama actual {rama} no corresponde al issue #{issue}", "n-a")

    if not prs:
        return Veredicto("FAILED", "critico", f"no hay PR abierto para la rama {rama}", "n-a")

    abiertos = [p for p in prs if p.get("state") == "OPEN"]
    if len(abiertos) > 1:
        return Veredicto("FAILED", "critico", f"hay {len(abiertos)} PRs abiertos para la rama; ambigüedad", "n-a")

    if not abiertos:
        # Se filtra por estado, nunca por la cardinalidad de `prs`: un MERGED
        # contra la base equivocada no debe pasar (aunque sea el unico
        # elemento) y un MERGED valido no debe fallar por coexistir con un
        # CLOSED (aunque la lista tenga mas de un elemento). Hallazgo #1 del
        # review de #81.
        mergeados = [p for p in prs if p.get("state") == "MERGED"]
        validos = [p for p in mergeados if p.get("baseRefName") == base]
        if validos:
            numeros = [f"#{p.get('number')}" for p in validos]
            motivo = _frase_pr(
                numeros,
                "ya fue mergeado (fuera del flujo: el merge va después del DoD)",
                "ya fueron mergeados (fuera del flujo: el merge va después del DoD)",
            )
            return Veredicto("PASSED", "n-a", motivo, validos[0].get("url", "n-a"))
        if mergeados:
            detalle = [f"#{p.get('number')} (base {p.get('baseRefName')})" for p in mergeados]
            motivo = _frase_pr(
                detalle,
                f"fue mergeado contra una base distinta de {base}",
                f"fueron mergeados contra una base distinta de {base}",
            )
            return Veredicto("FAILED", "critico", motivo, mergeados[0].get("url", "n-a"))
        cerrados = [p for p in prs if p.get("state") == "CLOSED"]
        if cerrados:
            numeros = [f"#{p.get('number')}" for p in cerrados]
            motivo = _frase_pr(numeros, "está cerrado sin merge", "están cerrados sin merge")
            return Veredicto("FAILED", "critico", motivo, cerrados[0].get("url", "n-a"))
        return Veredicto("FAILED", "critico", f"no hay PR abierto para la rama {rama}", "n-a")

    pr = abiertos[0]
    url = pr.get("url", "n-a")

    # `gh pr list` siempre devuelve estos campos para un PR real; si faltan,
    # el dato esta corrupto o incompleto y el motivo debe decirlo -- no debe
    # caer en la rama de "checks aun no registrados", que manda a esperar por
    # algo que no va a cambiar (hallazgo #4 del review de #81).
    campos_ausentes = [c for c in ("number", "isDraft", "mergeable") if pr.get(c) is None]
    if campos_ausentes:
        return Veredicto(
            "FAILED", "no-critico",
            f"gh pr list no devolvió {', '.join(campos_ausentes)}: no se pudo evaluar el PR con certeza",
            url,
        )

    if pr.get("isDraft"):
        return Veredicto("FAILED", "critico", f"el PR #{pr.get('number')} está en draft; un humano no puede mergearlo", url)
    if pr.get("baseRefName") != base:
        return Veredicto("FAILED", "critico", f"el PR apunta a {pr.get('baseRefName')}, no a {base}", url)
    if not _cierra_issue(pr.get("body", ""), issue):
        return Veredicto("FAILED", "no-critico", f"el PR no cierra #{issue}: el issue quedará abierto al mergear", url)

    mergeable = pr.get("mergeable")
    merge_state = pr.get("mergeStateStatus")
    if mergeable == "CONFLICTING":
        return Veredicto("FAILED", "critico", f"conflictos con {base}", url)
    if merge_state == "DIRTY":
        return Veredicto("FAILED", "critico", f"conflictos con {base} (mergeStateStatus DIRTY)", url)
    if mergeable == "UNKNOWN":
        return Veredicto("FAILED", "critico", f"GitHub no pudo calcular el estado de merge tras {espera}s", url)
    if merge_state == "BEHIND":
        return Veredicto("FAILED", "no-critico", f"la rama está detrás de {base}; actualizala antes del merge", url)
    # CLEAN, BLOCKED, UNSTABLE, HAS_HOOKS, UNKNOWN, DRAFT: no alteran el veredicto (D2).

    checks = pr.get("statusCheckRollup") or []
    if not checks:
        if hay_workflows:
            return Veredicto("FAILED", "no-critico", "checks aún no registrados; reevaluá en unos segundos", url)
        return Veredicto("PASSED", "n-a", "PR mergeable; el repo no tiene checks configurados", url)

    eje, motivo = _estado_checks(checks)
    if eje == "rojo":
        return Veredicto("FAILED", "critico", motivo, url)
    if eje in ("desconocido", "en_curso"):
        return Veredicto("FAILED", "no-critico", motivo, url)
    return Veredicto("PASSED", "n-a", f"PR #{pr.get('number')} abierto contra {base}, mergeable, checks en verde", url)


def _rama_actual() -> str:
    proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _remote_actual() -> str:
    proc = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _hay_workflows() -> bool:
    carpeta = Path(".github/workflows")
    return carpeta.is_dir() and any(carpeta.glob("*.y*ml"))


def _pr_list(rama: str, repo: str) -> list[dict]:
    proc = subprocess.run(
        ["gh", "pr", "list", "--head", rama, "--state", "all", "-R", repo, "--json", CAMPOS_PR],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 and proc.stderr.strip():
        raise RuntimeError(proc.stderr.strip())
    return json.loads(proc.stdout) if proc.stdout.strip() else []


def _esperar_mergeable(rama: str, repo: str, prs: list[dict], espera: int) -> list[dict]:
    """Reintenta `gh pr list` mientras el unico PR OPEN tenga `mergeable: UNKNOWN`
    (asincronia de GitHub que se resuelve en segundos). No espera por checks."""
    transcurrido = 0
    while transcurrido < espera:
        abiertos = [p for p in prs if p.get("state") == "OPEN"]
        if len(abiertos) != 1 or abiertos[0].get("mergeable") != "UNKNOWN":
            break
        time.sleep(5)
        transcurrido += 5
        prs = _pr_list(rama, repo)
    return prs


def main() -> None:
    parser = argparse.ArgumentParser(description="Sensor del estado del PR (item 1 del DoD, issue #81).")
    parser.add_argument("issue", type=numero_issue)
    parser.add_argument("--repo")
    parser.add_argument("--base", default="main")
    parser.add_argument("--espera", type=int, default=60, help="segundos maximos de espera mientras mergeable=UNKNOWN")
    parser.add_argument("--rama", help="override de depuracion; verify-dod no lo usa (D1)")
    parser.add_argument("--pr", type=int, help="override de depuracion; verify-dod no lo usa (D1)")
    parser.add_argument("--remote-url", help="override de depuracion")
    parser.add_argument("--json", help="array de `gh pr list --json %s` (tests)" % CAMPOS_PR)
    args = parser.parse_args()

    rama = args.rama or _rama_actual()

    if args.json:
        prs = json.loads(args.json)
        veredicto = evaluar(prs, args.issue, rama, args.base, "github", True, espera=args.espera)
    else:
        url_remote = args.remote_url or _remote_actual()
        remote = tipo_remote(url_remote)
        prs: list[dict] = []
        gh_error: str | None = None
        if remote == "github":
            repo = args.repo or repo_from_config()
            try:
                prs = _pr_list(rama, repo)
                prs = _esperar_mergeable(rama, repo, prs, args.espera)
            except RuntimeError as exc:
                gh_error = str(exc)
        veredicto = evaluar(prs, args.issue, rama, args.base, remote, _hay_workflows(), gh_error=gh_error, espera=args.espera)

    print(f"ESTADO: {veredicto.estado}")
    print(f"CRITICIDAD: {veredicto.criticidad}")
    print(f"MOTIVO: {veredicto.motivo}")
    print(f"PR: {veredicto.pr}")
    sys.exit(0 if veredicto.estado.startswith("PASSED") else 1)


if __name__ == "__main__":
    main()
