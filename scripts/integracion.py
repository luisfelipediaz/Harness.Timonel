#!/usr/bin/env python3
"""Arma el comando de PR (gh o az) segun el remote del repo (gap de la HU #31).

Uso:
    python3 integracion.py <issue> --rama hu/N-slug [--base main] [--remote-url URL]
                            [--repo owner/repo] [--body-out archivo]
    python3 integracion.py --tipo-remote [--remote-url URL]

Detecta si el remote es GitHub o Azure DevOps y arma (imprime, no ejecuta) el
comando `gh pr create` o `az repos pr create` correspondiente. Con `--body-out`
ademas arma el cuerpo del PR (Cierra #N, contrato de cambio, tabla del DoD) leyendo
los comentarios `timonel:contrato-api`/`timonel:dod` del issue y lo escribe en ese
archivo. El agente (flechodiezx, Fase 8) es quien ejecuta el comando impreso: este
script, como `contrato_check.py`/`validar_marcador.py`, solo lee e imprime.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Callable

from timonel_gh import find_marker_comment, gh_json, repo_from_config

REMOTE_GITHUB = re.compile(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?/?$")
REMOTE_AZURE_DEV = re.compile(r"dev\.azure\.com/(?P<org>[^/]+)/(?P<project>[^/]+)/_git/(?P<repo>[^/]+)/?$")
REMOTE_AZURE_VS = re.compile(r"(?P<org>[^./]+)\.visualstudio\.com/(?P<project>[^/]+)/_git/(?P<repo>[^/]+)/?$")
REMOTE_AZURE_SSH = re.compile(r"ssh\.dev\.azure\.com:v3/(?P<org>[^/]+)/(?P<project>[^/]+)/(?P<repo>[^/]+)/?$")


def _datos_github(m: re.Match) -> dict[str, str]:
    return {"owner": m.group("owner"), "repo": m.group("repo")}


def _datos_azure_dev(m: re.Match) -> dict[str, str]:
    return {
        "org": m.group("org"), "project": m.group("project"), "repo": m.group("repo"),
        "organization_url": f"https://dev.azure.com/{m.group('org')}",
    }


def _datos_azure_vs(m: re.Match) -> dict[str, str]:
    return {
        "org": m.group("org"), "project": m.group("project"), "repo": m.group("repo"),
        "organization_url": f"https://{m.group('org')}.visualstudio.com",
    }


def _datos_azure_ssh(m: re.Match) -> dict[str, str]:
    return {
        "org": m.group("org"), "project": m.group("project"), "repo": m.group("repo"),
        "organization_url": f"https://dev.azure.com/{m.group('org')}",
    }


# Lookup ordenado (regex, tipo, extractor de datos) — sin if/elif por tipo de remote.
_PATRONES: list[tuple[re.Pattern, str, Callable[[re.Match], dict[str, str]]]] = [
    (REMOTE_GITHUB, "github", _datos_github),
    (REMOTE_AZURE_DEV, "azure-devops", _datos_azure_dev),
    (REMOTE_AZURE_VS, "azure-devops", _datos_azure_vs),
    (REMOTE_AZURE_SSH, "azure-devops", _datos_azure_ssh),
]


def tipo_remote(url: str) -> str:
    """"github" | "azure-devops" | "desconocido"."""
    return next((tipo for patron, tipo, _ in _PATRONES if patron.search(url)), "desconocido")


def datos_remote(url: str) -> dict[str, str]:
    for patron, _, extraer in _PATRONES:
        m = patron.search(url)
        if m:
            return extraer(m)
    raise ValueError(f"tipo de remote desconocido: {url!r}")


# Todo valor interpolado pasa por shlex.quote: el agente ejecuta el comando con `eval`,
# y un titulo con apostrofo (o un cuerpo con `$(...)`) no debe romperlo ni ejecutarse.
def _cmd_gh(datos: dict[str, str], rama: str, base: str, titulo: str, body_file: str) -> str:
    q = shlex.quote
    return f"gh pr create --base {q(base)} --head {q(rama)} --title {q(titulo)} --body-file {q(body_file)}"


def _cmd_az(datos: dict[str, str], rama: str, base: str, titulo: str, body_file: str) -> str:
    q = shlex.quote
    return (
        f"az repos pr create --source-branch {q(rama)} --target-branch {q(base)} "
        f"--title {q(titulo)} --description {q('@' + body_file)} "
        f"--repository {q(datos['repo'])} --organization {q(datos['organization_url'])} --project {q(datos['project'])}"
    )


COMANDOS: dict[str, Callable[[dict[str, str], str, str, str, str], str]] = {
    "github": _cmd_gh,
    "azure-devops": _cmd_az,
}


def comando_pr(url: str, rama: str, base: str, titulo: str, body_file: str) -> str:
    tipo = tipo_remote(url)
    if tipo not in COMANDOS:
        raise ValueError(f"tipo de remote desconocido: {url!r}")
    return COMANDOS[tipo](datos_remote(url), rama, base, titulo, body_file)


def titulo_pr(titulo_issue: str, issue: int) -> str:
    return f"{titulo_issue} (#{issue})"


_SECCION_CONTRATO = re.compile(r"^### (?:Contrato de cambio|Endpoints)\s*\n(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
_FILA_DOD = re.compile(r"^\|\s*\d+\s*\|.*\|\s*$", re.MULTILINE)


def _seccion_contrato(contrato: str | None) -> str:
    if not contrato:
        return "Sin contrato publicado"
    m = _SECCION_CONTRATO.search(contrato)
    return m.group(1).strip() if m else "Sin contrato publicado"


def _tabla_dod(dod: str | None) -> str:
    if not dod:
        return "Sin DoD publicado"
    filas = _FILA_DOD.findall(dod)
    if not filas:
        return "Sin DoD publicado"
    return "\n".join(["| # | Item | Estado |", "| --- | --- | --- |", *filas])


def cuerpo_pr(issue: int, repo: str, titulo: str, contrato: str | None, dod: str | None) -> str:
    link = f"https://github.com/{repo}/issues/{issue}"
    return (
        f"Cierra #{issue} ({link})\n\n"
        f"## Contrato de cambio\n\n{_seccion_contrato(contrato)}\n\n"
        f"## Definition of Done\n\n{_tabla_dod(dod)}\n"
    )


def _remote_actual() -> str:
    proc = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Arma (imprime) el comando de PR segun el remote del repo.")
    parser.add_argument("issue", type=int, nargs="?")
    parser.add_argument("--rama")
    parser.add_argument("--base", default="main")
    parser.add_argument("--remote-url")
    parser.add_argument("--repo")
    parser.add_argument("--body-out")
    parser.add_argument("--tipo-remote", action="store_true")
    args = parser.parse_args()

    url = args.remote_url or _remote_actual()

    if args.tipo_remote:
        print(tipo_remote(url))
        return

    if args.issue is None or not args.rama:
        parser.error("issue y --rama son obligatorios salvo con --tipo-remote")

    repo = args.repo or repo_from_config()
    issue_data = gh_json("issue", "view", str(args.issue), "-R", repo, "--json", "title,comments")
    titulo = titulo_pr(issue_data["title"], args.issue)

    if args.body_out:
        comentarios = issue_data.get("comments", [])
        contrato = find_marker_comment(comentarios, "contrato-api")
        dod = find_marker_comment(comentarios, "dod")
        cuerpo = cuerpo_pr(args.issue, repo, issue_data["title"], contrato, dod)
        Path(args.body_out).write_text(cuerpo, encoding="utf-8")
        body_file = args.body_out
    else:
        body_file = "<archivo>"

    try:
        print(comando_pr(url, args.rama, args.base, titulo, body_file))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
