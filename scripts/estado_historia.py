#!/usr/bin/env python3
"""Estado de una historia para reanudar /implement (gap 4 de la auditoria #11, issue #16).

Uso:
    python3 estado_historia.py <issue> [--repo owner/repo] [--json]

Lee el issue (labels, `## Tareas`, comentarios con marcador) y la rama local
`hu/<issue>-*`, y deduce la fase desde la que flechodiezx debe continuar.
Esta es la memoria entre sesiones: el agente no adivina, lee.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess

from timonel_gh import find_marker_comment, gh_json, label_value, repo_from_config

TAREAS = ["Contrato API aprobado", "Modelos compartidos", "Backend", "Frontend",
          "Consolidación (lint + tests)", "Code review", "Retrospectiva", "Definition of Done"]
MARCADORES = ["investigacion", "contrato-api", "consolidacion", "review", "retro", "dod"]

# Orden de fases y la condicion (tareas/marcadores) que indica que ya se hizo.
FASES = [
    ("1.5 Investigacion",      lambda e: "investigacion" in e["marcadores"]),
    ("2 Contrato API",         lambda e: e["tareas"].get("Contrato API aprobado") or "contrato-api" in e["marcadores"]),
    ("3 Backend",              lambda e: e["tareas"].get("Backend") or e["alcance"] == "frontend"),
    ("3 Frontend",             lambda e: e["tareas"].get("Frontend") or e["alcance"] == "backend"),
    ("4-5 Consolidacion",      lambda e: e["tareas"].get("Consolidación (lint + tests)") or "consolidacion" in e["marcadores"]),
    ("5.5 Code review",        lambda e: e["tareas"].get("Code review") or "review" in e["marcadores"]),
    ("6 Retrospectiva",        lambda e: e["tareas"].get("Retrospectiva") or "retro" in e["marcadores"]),
    ("7 Definition of Done",   lambda e: e["tareas"].get("Definition of Done") or "dod" in e["marcadores"]),
]


def parse_tareas(body: str) -> dict[str, bool]:
    m = re.search(r"^## Tareas\s*\n(.*?)(?=^##\s|\Z)", body or "", re.MULTILINE | re.DOTALL)
    tareas: dict[str, bool] = {}
    if not m:
        return tareas
    for line in m.group(1).splitlines():
        mm = re.match(r"- \[( |x|X)\] (.+)", line.strip())
        if mm:
            tareas[mm.group(2).strip()] = mm.group(1).lower() == "x"
    return tareas


def rama_local(issue: int) -> str | None:
    out = subprocess.run(["git", "branch", "--list", f"hu/{issue}-*"], capture_output=True, text=True)
    ramas = [l.strip().lstrip("* ").strip() for l in out.stdout.splitlines() if l.strip()]
    return ramas[0] if ramas else None


def estado(issue: dict, rama: str | None = None) -> dict:
    labels = issue.get("label_names") or [l["name"] for l in issue.get("labels", [])]
    comentarios = issue.get("comments", [])
    e = {
        "issue": issue["number"],
        "titulo": issue.get("title", ""),
        "state": issue.get("state", "OPEN"),
        "estado_label": label_value(labels, "estado"),
        "alcance": label_value(labels, "alcance"),
        "tareas": parse_tareas(issue.get("body", "")),
        "marcadores": [m for m in MARCADORES if find_marker_comment(comentarios, m)],
        "rama": rama,
    }
    hechas = [nombre for nombre, cond in FASES if cond(e)]
    pendientes = [nombre for nombre, cond in FASES if not cond(e)]
    e["fases_hechas"] = hechas
    e["fases_pendientes"] = pendientes
    cerrada = e["state"].upper() == "CLOSED" or "dod" in e["marcadores"]
    e["reanudar_en"] = "cerrar" if cerrada else (pendientes[0] if pendientes else "cerrar")
    hay_trabajo = bool(e["marcadores"]) or any(e["tareas"].values()) or rama is not None or e["estado_label"] == "en-progreso"
    e["nueva"] = not cerrada and not hay_trabajo
    return e


def formato(e: dict) -> str:
    lines = [f"#{e['issue']} {e['titulo']} [{e['state']}] estado:{e['estado_label'] or '-'} alcance:{e['alcance'] or '-'}"]
    lines.append(f"Rama local: {e['rama'] or 'ninguna'}")
    lines.append("Marcadores publicados: " + (", ".join(e["marcadores"]) or "ninguno"))
    lines.append("Tareas: " + ", ".join(f"[{'x' if v else ' '}] {k}" for k, v in e["tareas"].items()))
    lines.append("Fases hechas: " + (", ".join(e["fases_hechas"]) or "ninguna"))
    if e["nueva"]:
        lines.append("REANUDAR_EN: inicio (historia sin empezar)")
    elif e["reanudar_en"] == "cerrar":
        lines.append("REANUDAR_EN: cerrar (historia terminada o issue cerrado; no relanzar fases)")
    else:
        lines.append(f"REANUDAR_EN: {e['reanudar_en']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Estado de una historia para reanudar /implement.")
    parser.add_argument("issue", type=int)
    parser.add_argument("--repo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = args.repo or repo_from_config()
    issue = gh_json("issue", "view", str(args.issue), "-R", repo, "--json", "number,title,state,body,labels,comments")
    issue["label_names"] = [l["name"] for l in issue["labels"]]
    e = estado(issue, rama_local(args.issue))
    print(json.dumps(e, ensure_ascii=False, indent=2) if args.json else formato(e))


if __name__ == "__main__":
    main()
