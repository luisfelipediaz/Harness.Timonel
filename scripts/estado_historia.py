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

CHECKLISTS: dict[str, list[str]] = {
    "hu": ["Contrato API aprobado", "Modelos compartidos", "Backend", "Frontend",
           "Consolidación (lint + tests)", "Code review", "Retrospectiva", "PR abierto",
           "Definition of Done"],
    "hotfix": ["Implementación", "Lint + tests afectados", "Code review", "PR abierto",
               "Definition of Done"],
}
# Retrocompat: otros modulos importan TAREAS directamente (test_consistencia.py::ChecklistsPorTipoTests
# ya cubre la invariante contra plantilla-hu.md para todos los tipos, incluido este).
TAREAS = CHECKLISTS["hu"]

MARCADORES = ["investigacion", "contrato-api", "consolidacion", "review", "retro", "dod"]

# Prefijos de rama que reconoce rama_local(), en orden de preferencia cuando existe mas
# de una para el mismo issue (hu/ para historias, fix/ para hotfixes aislados en worktree).
PREFIJOS_RAMA = ("hu", "fix")

# Orden de fases por tipo y la condicion (tareas/marcadores) que indica que ya se hizo.
# Una tarea ausente del body cuenta como pendiente, nunca como hecha por defecto: si el
# checklist del tipo la declara (CHECKLISTS[tipo]) y no aparece en el body del issue
# (p. ej. issues anteriores a v0.6.0 sin "PR abierto"), esta pendiente, no SKIPPED.
FASES_POR_TIPO: dict[str, list[tuple]] = {
    "hu": [
        # Unica fase cuya evidencia puede vivir en OTRO issue: la Fase 1.5 de flechodiezx
        # autoriza reutilizar una investigacion vigente en vez de relanzar a Dora. El
        # contrato sirve de evidencia indirecta porque el dominio lo garantiza: "nunca
        # redactes el contrato sin la investigacion" (flechodiezx.md).
        ("1.5 Investigacion",      lambda e: "investigacion" in e["marcadores"]
                                         or e["tareas"].get("Contrato API aprobado")
                                         or "contrato-api" in e["marcadores"]),
        ("2 Contrato API",         lambda e: e["tareas"].get("Contrato API aprobado") or "contrato-api" in e["marcadores"]),
        ("3 Backend",              lambda e: e["tareas"].get("Backend") or e["alcance"] == "frontend"),
        ("3 Frontend",             lambda e: e["tareas"].get("Frontend") or e["alcance"] == "backend"),
        ("4-5 Consolidacion",      lambda e: e["tareas"].get("Consolidación (lint + tests)") or "consolidacion" in e["marcadores"]),
        ("5.5 Code review",        lambda e: e["tareas"].get("Code review") or "review" in e["marcadores"]),
        ("6 Retrospectiva",        lambda e: e["tareas"].get("Retrospectiva") or "retro" in e["marcadores"]),
        ("6.5 PR/Integración",     lambda e: e["tareas"].get("PR abierto")),
        ("7 Definition of Done",   lambda e: e["tareas"].get("Definition of Done") or "dod" in e["marcadores"]),
    ],
    "hotfix": [
        ("2 Implementacion",  lambda e: e["tareas"].get("Implementación") and e["tareas"].get("Lint + tests afectados")),
        ("3 Code review",     lambda e: e["tareas"].get("Code review") or "review" in e["marcadores"]),
        ("5 PR/Integración",  lambda e: e["tareas"].get("PR abierto")),
        ("6 DoD reducido",    lambda e: e["tareas"].get("Definition of Done") or "dod" in e["marcadores"]),
    ],
}


def _fases_del_tipo(tipo: str | None) -> list[tuple]:
    """Fases del checklist del tipo de issue; tipo ausente o desconocido cae a `hu`."""
    return FASES_POR_TIPO.get(tipo, FASES_POR_TIPO["hu"])


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
    for prefijo in PREFIJOS_RAMA:
        out = subprocess.run(["git", "branch", "--list", f"{prefijo}/{issue}-*"], capture_output=True, text=True)
        ramas = [l.strip().lstrip("* ").strip() for l in out.stdout.splitlines() if l.strip()]
        if ramas:
            return ramas[0]
    return None


def estado(issue: dict, rama: str | None = None) -> dict:
    labels = issue.get("label_names") or [l["name"] for l in issue.get("labels", [])]
    comentarios = issue.get("comments", [])
    tipo = label_value(labels, "tipo")
    fases = _fases_del_tipo(tipo if tipo in CHECKLISTS else "hu")
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
    hechas = [nombre for nombre, cond in fases if cond(e)]
    pendientes = [nombre for nombre, cond in fases if not cond(e)]
    e["fases_hechas"] = hechas
    e["fases_pendientes"] = pendientes
    # Cerrada = estado CLOSED, o todas las fases del tipo hechas (no solo la ultima):
    # con "PR abierto" ya sin default True, una historia con DoD marcado pero el PR
    # todavia pendiente NO esta cerrada (decision aprobada del humano en #83).
    cerrada = e["state"].upper() == "CLOSED" or not pendientes
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
