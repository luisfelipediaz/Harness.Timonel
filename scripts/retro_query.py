#!/usr/bin/env python3
"""Consulta retrospectivas publicadas como comentario `<!-- timonel:retro -->` en los issues.

Uso:
    python3 retro_query.py --modulo mis-finanzas
    python3 retro_query.py --epica 12            # HUs hijas del issue #12
    python3 retro_query.py --issue 42
    python3 retro_query.py --seccion "Errores recurrentes"
    python3 retro_query.py --repo owner/repo ... # si no hay .claude/timonel.config.json
"""

from __future__ import annotations

import argparse
import sys

from timonel_gh import Retro, epic_children, load_retros, repo_from_config


def filter_retros(
    retros: list[Retro],
    modulo: str | None = None,
    issue: int | None = None,
    hijos_epica: set[int] | None = None,
) -> list[Retro]:
    result = retros
    if hijos_epica is not None:
        result = [r for r in result if r.issue in hijos_epica]
    if modulo:
        result = [r for r in result if r.modulo.lower() == modulo.lower()]
    if issue is not None:
        result = [r for r in result if r.issue == issue]
    return result


def format_retro(retro: Retro, seccion: str | None = None) -> str:
    lines = [
        f"### #{retro.issue}: {retro.titulo}",
        f"Estimado: {retro.estimado_sp} SP | Real: {retro.real_sp} SP | Precision: {retro.precision}",
        f"Modulo: {retro.modulo} | Alcance: {retro.alcance}",
        "",
    ]
    sections = retro.sections
    if seccion:
        sections = {k: v for k, v in sections.items() if k.lower() == seccion.lower()}
    for name, bullets in sections.items():
        if bullets:
            lines.append(f"**{name}:**")
            lines.extend(f"- {b}" for b in bullets)
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Consulta retrospectivas del backlog en GitHub.")
    parser.add_argument("--repo", help="owner/repo (default: github.repo del config)")
    parser.add_argument("--modulo", help="Filtrar por modulo (label mod:)")
    parser.add_argument("--epica", type=int, help="Filtrar por HUs hijas de esta epica")
    parser.add_argument("--issue", type=int, help="Filtrar por numero de issue")
    parser.add_argument("--seccion", help='Mostrar solo una seccion (ej: "Errores recurrentes")')
    args = parser.parse_args()

    repo = args.repo or repo_from_config()
    retros = load_retros(repo)
    if not retros:
        print("No hay retrospectivas aun.")
        sys.exit(0)

    hijos = epic_children(repo, args.epica) if args.epica else None
    filtered = filter_retros(retros, modulo=args.modulo, issue=args.issue, hijos_epica=hijos)
    if not filtered:
        print("Sin resultados para los filtros indicados.")
        sys.exit(0)

    print(f"# Retrospectivas ({len(filtered)} encontradas)\n")
    for retro in filtered:
        print(format_retro(retro, seccion=args.seccion))
        print("---\n")


if __name__ == "__main__":
    main()
