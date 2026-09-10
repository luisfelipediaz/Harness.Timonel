#!/usr/bin/env python3
"""Ratchet: convierte las mejoras de una retro en issues (gap 1 de la auditoria #11, issue #13).

Uso:
    python3 cosechar_retro.py <issue> [--repo owner/repo] [--plugin-repo luisfelipediaz/Harness.Timonel] [--apply]

Lee el comentario `<!-- timonel:retro -->` del issue, toma los bullets de
`### Mejoras sugeridas` y las respuestas no vacias de `### Harness engineering`,
decide el destino (plugin Timonel vs consumidor) y crea un issue `estado:borrador`
por cada uno con `Origen: retro #N`. Idempotente: busca `Origen: retro #N (k)`.
Al final agrega/edita en la retro la seccion `### Issues derivados`.
Sin --apply solo imprime el plan.
"""

from __future__ import annotations

import argparse
import re
import tempfile

from timonel_gh import (
    MARCADOR_RETRO,
    find_marker_comment,
    gh,
    gh_json,
    label_value,
    load_config,
    parse_secciones,
    repo_from_config,
)

PLUGIN_REPO_DEFAULT = "luisfelipediaz/Harness.Timonel"
PALABRAS_PLUGIN = ("timonel", "plugin", "skill", "agente", "sub-agente", "orquestador", "plantilla", "marcador",
                   "flechodiezx", "dora", "code-review", "generate-retro", "verify-dod", "consolidate-story", "retro-tools")
PALABRAS_CONSUMIDOR = ("claude.md", "heur", "convenci", "lint", "eslint", "ci", "pipeline", "test", "modulo", "módulo", "componente", "servicio")
NINGUNO = re.compile(r"^(ninguno|ninguna|n/a|no aplica)\.?$", re.IGNORECASE)
RESPUESTA_HE = re.compile(r"^¿[^?]+\?\s*→\s*(.+)$")  # "¿Surgió...? → propuesta"


def extraer_mejoras(retro_body: str) -> list[tuple[str, str]]:
    """[(fuente, texto)] con fuente = 'mejora' | 'harness'. Omite 'Ninguno'."""
    secciones = parse_secciones(retro_body)
    items: list[tuple[str, str]] = []
    for b in secciones.get("Mejoras sugeridas", []):
        if not NINGUNO.match(b.strip()):
            items.append(("mejora", b.strip()))
    for b in secciones.get("Harness engineering", []):
        m = RESPUESTA_HE.match(b.strip())
        texto = (m.group(1) if m else b).strip()
        if texto and not NINGUNO.match(texto) and not NINGUNO.match(texto.split(" o ")[0].strip()):
            items.append(("harness", texto))
    return items


def destino(texto: str) -> str:
    """'plugin' si la mejora apunta a Timonel (skills, agentes, plantillas); si no, 'consumidor'."""
    t = texto.lower()
    if any(p in t for p in PALABRAS_PLUGIN):
        return "plugin"
    return "consumidor"


def _titulo(texto: str) -> str:
    limpio = re.sub(r"[`*_]", "", texto).strip().rstrip(".")
    limpio = re.sub(r"^(documentar|agregar|añadir|re-evaluar|reevaluar|explicitar|mover|crear)\b", lambda m: m.group(1).capitalize(), limpio, flags=re.IGNORECASE)
    return limpio[:70].rstrip(" ,;:")


def _body(origen_repo: str, issue: int, k: int, fuente: str, texto: str, modulo: str) -> str:
    return f"""Origen: retro #{issue} ({k}) — {origen_repo}
Fuente: {'Mejoras sugeridas' if fuente == 'mejora' else 'Harness engineering'}

## Historia

**Como** equipo, **quiero** {texto[0].lower() + texto[1:] if texto else texto}, **para** que la siguiente historia del módulo `{modulo or 'n/a'}` arranque con ese aprendizaje incorporado.

## Criterios de aceptación

Por definir en refinamiento (`/timonel:refine`).

## Notas técnicas

- Capturado automáticamente por `cosechar_retro.py` (ratchet, TIM-ADR-0001 / auditoría #11 gap 1).
- Contexto completo en la retro del issue origen.

## Dependencias

Ninguna
"""


def cosechar(repo: str, issue_num: int, plugin_repo: str, apply: bool) -> list[str]:
    issue = gh_json("issue", "view", str(issue_num), "-R", repo, "--json", "number,title,body,labels,comments")
    labels = [l["name"] for l in issue["labels"]]
    modulo = label_value(labels, "mod")
    retro = find_marker_comment(issue.get("comments", []), MARCADOR_RETRO)
    if not retro:
        return [f"#{issue_num} no tiene comentario timonel:retro; nada que cosechar"]
    mejoras = extraer_mejoras(retro)
    if not mejoras:
        return [f"#{issue_num}: la retro no tiene mejoras accionables"]

    salida: list[str] = []
    creados: list[str] = []
    for k, (fuente, texto) in enumerate(mejoras, 1):
        dest_repo = plugin_repo if destino(texto) == "plugin" else repo
        marca = f"Origen: retro #{issue_num} ({k})"
        existente = gh_json("issue", "list", "-R", dest_repo, "--state", "all", "--limit", "20",
                            "--search", f'"{marca}" in:body', "--json", "number,body")
        previo = next((i for i in existente if marca in (i.get("body") or "")), None)
        if previo:
            salida.append(f"  [{k}] ya existe {dest_repo}#{previo['number']}: {texto[:60]}")
            creados.append(f"{dest_repo}#{previo['number']}")
            continue
        labels_nuevo = ["tipo:hu", "estado:borrador"] + (["mod:plugin"] if dest_repo == plugin_repo else ([f"mod:{modulo}"] if modulo else []))
        if not apply:
            salida.append(f"  [{k}] crear en {dest_repo} [{', '.join(labels_nuevo)}]: {_titulo(texto)}")
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(_body(repo, issue_num, k, fuente, texto, modulo))
            path = f.name
        args = ["issue", "create", "-R", dest_repo, "--title", _titulo(texto), "--body-file", path]
        for l in labels_nuevo:
            args += ["--label", l]
        try:
            num = int(gh(*args).strip().rsplit("/", 1)[-1])
        except SystemExit:
            # label mod:<x> puede no existir en el repo destino: reintenta sin el
            args = [a for a in args if not a.startswith("mod:")]
            args = [a for i, a in enumerate(args) if not (a == "--label" and i + 1 < len(args) and args[i + 1].startswith("mod:"))]
            num = int(gh(*args).strip().rsplit("/", 1)[-1])
        creados.append(f"{dest_repo}#{num}")
        salida.append(f"  [{k}] creado {dest_repo}#{num}: {_titulo(texto)}")

    if apply and creados:
        refs = "\n".join(f"- {c}" for c in creados)
        nuevo = re.sub(r"\n### Issues derivados\n.*\Z", "", retro, flags=re.DOTALL).rstrip() + f"\n\n### Issues derivados\n{refs}\n"
        cid = gh("api", f"repos/{repo}/issues/{issue_num}/comments", "--paginate",
                 "-q", '[.[] | select(.body | startswith("<!-- timonel:retro -->"))] | last | .id').strip()
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(nuevo)
            path = f.name
        gh("api", "-X", "PATCH", f"repos/{repo}/issues/comments/{cid}", "-F", f"body=@{path}")
        salida.append(f"retro de #{issue_num} actualizada con {len(creados)} issues derivados")
    return salida


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte las mejoras de una retro en issues.")
    parser.add_argument("issue", type=int)
    parser.add_argument("--repo")
    parser.add_argument("--plugin-repo", default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    config = load_config()
    repo = args.repo or repo_from_config(config)
    plugin_repo = args.plugin_repo or (config.get("timonel") or {}).get("repo") or PLUGIN_REPO_DEFAULT
    print(f"Cosecha de la retro #{args.issue} ({'APPLY' if args.apply else 'DRY-RUN'}) → consumidor {repo}, plugin {plugin_repo}")
    for line in cosechar(repo, args.issue, plugin_repo, args.apply):
        print(line)


if __name__ == "__main__":
    main()
