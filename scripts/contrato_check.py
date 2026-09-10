#!/usr/bin/env python3
"""Contrasta el contrato API del issue con el codigo (gap 7 de la auditoria #11, issue #20).

Uso:
    python3 contrato_check.py <issue> [--repo owner/repo] [--api-path apps/api]

Extrae `Metodo:`/`Ruta:` del comentario `<!-- timonel:contrato-api -->` y busca en los
controllers NestJS del consumidor un decorador HTTP compatible. Imprime una tabla
PASSED/FAILED por endpoint que code-review pega en la fila Ficha/Contrato.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from timonel_gh import find_marker_comment, gh_json, load_config, repo_from_config

ENDPOINT = re.compile(r"Metodo:\s*(?P<metodo>GET|POST|PUT|PATCH|DELETE)\s*\n\s*Ruta:\s*(?P<ruta>\S+)", re.IGNORECASE)
DECORADOR = {"GET": "Get", "POST": "Post", "PUT": "Put", "PATCH": "Patch", "DELETE": "Delete"}


def extraer_endpoints(contrato: str) -> list[tuple[str, str]]:
    return [(m.group("metodo").upper(), m.group("ruta")) for m in ENDPOINT.finditer(contrato)]


def _segmentos(ruta: str) -> list[str]:
    ruta = re.sub(r"^/?api/", "", ruta.strip("/"))
    return [s for s in ruta.split("/") if s]


def _indexar_controllers(api_path: Path) -> list[tuple[str, str, list[tuple[str, str]]]]:
    """[(archivo, prefijo @Controller, [(metodoHttp, subruta)])]."""
    indice = []
    for f in api_path.rglob("*.controller.ts"):
        texto = f.read_text(encoding="utf-8", errors="ignore")
        ctrl = re.search(r"@Controller\(\s*['\"]([^'\"]*)['\"]?\s*\)", texto)
        prefijo = ctrl.group(1) if ctrl else ""
        handlers = [(m.group(1).upper(), m.group(2) or "") for m in re.finditer(r"@(Get|Post|Put|Patch|Delete)\(\s*(?:['\"]([^'\"]*)['\"])?\s*\)", texto)]
        indice.append((str(f), prefijo, handlers))
    return indice


def _coincide(esperado: list[str], real: list[str]) -> bool:
    if len(esperado) != len(real):
        return False
    return all(r.startswith(":") or r.startswith("*") or e.startswith(":") or e.lower() == r.lower() for e, r in zip(esperado, real))


def verificar(endpoints: list[tuple[str, str]], indice) -> list[tuple[str, str, str, str]]:
    """[(metodo, ruta, estado, evidencia)]."""
    resultados = []
    for metodo, ruta in endpoints:
        esperado = _segmentos(ruta)
        evidencia = ""
        for archivo, prefijo, handlers in indice:
            for http, sub in handlers:
                if http != metodo:
                    continue
                real = [s for s in (prefijo.strip("/").split("/") + sub.strip("/").split("/")) if s]
                if _coincide(esperado, real):
                    evidencia = f"{archivo} @{DECORADOR[metodo]}('{sub}') en @Controller('{prefijo}')"
                    break
            if evidencia:
                break
        resultados.append((metodo, ruta, "PASSED" if evidencia else "FAILED", evidencia or "sin controller con esa ruta/metodo"))
    return resultados


def tabla(resultados) -> str:
    lines = ["| Método | Ruta | Estado | Evidencia |", "| --- | --- | --- | --- |"]
    lines += [f"| {m} | `{r}` | {e} | {ev} |" for m, r, e, ev in resultados]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Contrasta contrato API vs controllers.")
    parser.add_argument("issue", type=int)
    parser.add_argument("--repo")
    parser.add_argument("--api-path")
    args = parser.parse_args()
    config = load_config()
    repo = args.repo or repo_from_config(config)
    api_path = Path(args.api_path or (config.get("api") or {}).get("path") or "apps/api")
    issue = gh_json("issue", "view", str(args.issue), "-R", repo, "--json", "comments")
    contrato = find_marker_comment(issue.get("comments", []), "contrato-api")
    if not contrato:
        print(f"#{args.issue}: sin comentario timonel:contrato-api; nada que contrastar")
        return
    endpoints = extraer_endpoints(contrato)
    if not endpoints:
        print("El contrato no declara endpoints (Metodo:/Ruta:); OK si la HU es solo frontend.")
        return
    resultados = verificar(endpoints, _indexar_controllers(api_path))
    print(tabla(resultados))
    fallidos = [r for r in resultados if r[2] == "FAILED"]
    print(f"\nCONTRATO_CHECK: {'PASSED' if not fallidos else f'FAILED ({len(fallidos)} de {len(resultados)})'}")
    sys.exit(1 if fallidos else 0)


if __name__ == "__main__":
    main()
