#!/usr/bin/env python3
"""Definition of Ready computacional (TIM-ADR-0003; gap 6 de la auditoria #11, issue #18).

Uso:
    python3 dor_check.py <issue> [--repo owner/repo] [--para listo|implementar]
    python3 dor_check.py --json '<issue json>'    # para tests / pipelines

--para listo (default): lo que exige el planner/refiner antes de poner `estado:listo`.
--para implementar: ademas exige `estado:listo` (lo usa /implement y flechodiezx).

Sale 0 si cumple; 1 con la lista de faltantes si no. Un solo sensor para planner,
refiner e implement.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from timonel_gh import gh_json, label_value, numero_issue, repo_from_config

SP_VALIDOS = {"1", "2", "3", "5", "8", "13", "21"}
SECCION = lambda body, prefijo: re.search(rf"^##\s+{prefijo}", body, re.MULTILINE | re.IGNORECASE) is not None  # noqa: E731

# Requisitos por tipo (TIM-ADR-0003). `labels`: prefijos exclusivos obligatorios.
REQUISITOS: dict[str, dict] = {
    "hu": {
        "labels": ["alcance", "sp", "mod", "moscow", "prioridad"],
        "secciones": ["Historia", "Criterios de aceptaci", "Ficha t", "Endpoints", "Modelos compartidos", "Dependencias", "Tareas"],
        "sp_max": 13,
        "padre": True,
    },
    "hotfix": {
        "labels": ["alcance", "sp", "mod"],
        "secciones": ["Criterios de aceptaci", "Ficha t", "Endpoints", "Modelos compartidos", "Dependencias", "Tareas"],
        "sp_max": 3,
        "padre": False,
        "ninguno": ["Endpoints", "Modelos compartidos"],
    },
    "epica": {"labels": [], "secciones": ["Objetivo", "Alcance"], "sp_max": None, "padre": False},
    "sdd": {"labels": [], "secciones": ["1. Resumen ejecutivo", "3. Alcance", "4. Requisitos funcionales", "7. Contrato de datos y API"], "sp_max": None, "padre": False},
}


def _seccion_texto(body: str, prefijo: str) -> str:
    m = re.search(rf"^##\s+{re.escape(prefijo)}[^\n]*\n(.*?)(?=^##\s|\Z)", body, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def check(issue: dict, para: str = "listo") -> list[str]:
    """Devuelve los faltantes del DoR. `issue` trae number, title, body, label_names, parent (opcional)."""
    faltantes: list[str] = []
    labels: list[str] = issue.get("label_names") or [l["name"] for l in issue.get("labels", [])]
    body: str = issue.get("body") or ""
    tipo = label_value(labels, "tipo")
    if tipo not in REQUISITOS:
        return [f"falta label `tipo:*` valido (hu|hotfix|epica|sdd); tiene: {tipo or 'ninguno'}"]
    req = REQUISITOS[tipo]

    titulo = issue.get("title", "")
    if re.match(r"^(HU-\d+|\[|feat|fix|chore)\b", titulo, re.IGNORECASE):
        faltantes.append("titulo con prefijo; usar `[verbo infinitivo] [que cosa]`")

    for prefijo in req["labels"]:
        if not label_value(labels, prefijo):
            faltantes.append(f"falta label `{prefijo}:*`")
    sp = label_value(labels, "sp")
    if sp and sp not in SP_VALIDOS:
        faltantes.append(f"`sp:{sp}` no es Fibonacci valido")
    if sp and req["sp_max"] and sp.isdigit() and int(sp) > req["sp_max"]:
        faltantes.append(f"`sp:{sp}` supera el maximo {req['sp_max']} para tipo:{tipo}; dividir")
    if para == "implementar" and tipo in ("hu", "hotfix") and label_value(labels, "estado") != "listo":
        faltantes.append(f"estado es `{label_value(labels, 'estado') or 'ninguno'}`; se requiere `estado:listo`")
    if tipo in ("hu", "hotfix") and "bloqueado" in labels and para == "implementar":
        faltantes.append("lleva label `bloqueado`; resolver dependencias primero")

    for prefijo in req["secciones"]:
        if not SECCION(body, re.escape(prefijo)):
            faltantes.append(f"falta la seccion `## {prefijo}…`")
    if "POR DEFINIR" in body.upper():
        faltantes.append("el body contiene `POR DEFINIR`")
    if tipo in ("hu", "hotfix"):
        gherkin = _seccion_texto(body, "Criterios de aceptaci")
        if gherkin and not re.search(r"DADO QUE.*CUANDO.*ENTONCES", gherkin, re.DOTALL | re.IGNORECASE):
            faltantes.append("Criterios de aceptación sin escenario DADO/CUANDO/ENTONCES")
        ficha = _seccion_texto(body, "Ficha t")
        if ficha and not re.search(r"\|\s*Alcance\s*\|\s*(Backend|Frontend|Full-stack)\s*\|", ficha):
            faltantes.append("Ficha técnica sin fila `Alcance` con Backend|Frontend|Full-stack")
        tareas = _seccion_texto(body, "Tareas")
        if tareas and "- [" not in tareas:
            faltantes.append("`## Tareas` sin checklist")
        for seccion in req.get("ninguno", []):
            texto = _seccion_texto(body, seccion)
            if texto and texto.strip().lower() != "ninguno":
                faltantes.append(f"un hotfix exige `{seccion}: Ninguno`; si no, es una HU")
        deps = _seccion_texto(body, "Dependencias")
        if deps and deps.strip().lower() != "ninguna" and not re.search(r"Depende de #\d+", deps):
            faltantes.append("`## Dependencias` debe ser `Ninguna` o lineas `Depende de #N`")
    if req["padre"] and issue.get("parent") is None and "parent" in issue:
        faltantes.append("la HU no es sub-issue de ninguna epica")
    return faltantes


def _fetch(repo: str, num: int) -> dict:
    issue = gh_json("issue", "view", str(num), "-R", repo, "--json", "number,title,body,labels")
    issue["label_names"] = [l["name"] for l in issue["labels"]]
    owner, name = repo.split("/", 1)
    q = "query($o:String!,$r:String!,$n:Int!){ repository(owner:$o,name:$r){ issue(number:$n){ parent{ number } } } }"
    data = gh_json("api", "graphql", "-f", f"query={q}", "-f", f"o={owner}", "-f", f"r={name}", "-F", f"n={num}")
    issue["parent"] = (((data.get("data") or {}).get("repository") or {}).get("issue") or {}).get("parent")
    return issue


def main() -> None:
    parser = argparse.ArgumentParser(description="Definition of Ready de un issue de Timonel.")
    parser.add_argument("issue", nargs="?", type=numero_issue)
    parser.add_argument("--repo")
    parser.add_argument("--para", choices=["listo", "implementar"], default="listo")
    parser.add_argument("--json", help="issue como JSON (tests)")
    args = parser.parse_args()
    if args.json:
        issue = json.loads(args.json)
    elif args.issue:
        issue = _fetch(args.repo or repo_from_config(), args.issue)
    else:
        parser.error("indica <issue> o --json")
    faltantes = check(issue, args.para)
    if faltantes:
        print(f"DoR NO cumplido para #{issue.get('number', '?')} ({len(faltantes)} faltantes):")
        for f in faltantes:
            print(f"  - {f}")
        print("Sugerencia: /timonel:refine #%s" % issue.get("number", ""))
        sys.exit(1)
    print(f"DoR cumplido para #{issue.get('number', '?')} ({args.para})")


if __name__ == "__main__":
    main()
