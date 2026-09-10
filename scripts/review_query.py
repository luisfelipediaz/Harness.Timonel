#!/usr/bin/env python3
"""Consulta code reviews publicados como comentario `<!-- timonel:review -->` en los issues.

Uso:
    python3 review_query.py --modulo mis-finanzas
    python3 review_query.py --epica 12
    python3 review_query.py --issue 42
    python3 review_query.py --severidad CRITICO
    python3 review_query.py --tipo Heuristica
    python3 review_query.py --veredicto "REQUIERE CAMBIOS"
    python3 review_query.py --solo-bloqueantes
"""

from __future__ import annotations

import argparse
import sys

from timonel_gh import (
    SEVERIDADES_VALIDAS,
    VEREDICTOS_VALIDOS,
    Hallazgo,
    Review,
    epic_children,
    load_reviews,
    repo_from_config,
)


def _normalizar_veredicto(value: str) -> str:
    return value.strip().replace("_", " ").upper()


def filter_reviews(
    reviews: list[Review],
    modulo: str | None = None,
    issue: int | None = None,
    veredicto: str | None = None,
    solo_bloqueantes: bool = False,
    hijos_epica: set[int] | None = None,
) -> list[Review]:
    result = reviews
    if hijos_epica is not None:
        result = [r for r in result if r.issue in hijos_epica]
    if modulo:
        result = [r for r in result if r.modulo.lower() == modulo.lower()]
    if issue is not None:
        result = [r for r in result if r.issue == issue]
    if veredicto:
        v = _normalizar_veredicto(veredicto)
        result = [r for r in result if r.veredicto == v]
    if solo_bloqueantes:
        result = [r for r in result if r.bloquea_dod]
    return result


def filter_hallazgos(hallazgos: list[Hallazgo], severidad: str | None, tipo: str | None) -> list[Hallazgo]:
    result = hallazgos
    if severidad:
        result = [h for h in result if h.severidad == severidad.strip().upper()]
    if tipo:
        t = tipo.strip().lower()
        result = [h for h in result if t in (h.tipo.lower(), h.tipo_normalizado.lower())]
    return result


def format_review(review: Review, severidad: str | None, tipo: str | None) -> str:
    lines = [
        f"### #{review.issue}: {review.titulo}",
        f"Veredicto: {review.veredicto} | Criticos: {review.criticos} | Warnings: {review.warnings} | Bloquea DoD: {'si' if review.bloquea_dod else 'no'}",
        f"Modulo: {review.modulo} | Alcance: {review.alcance} | Fecha: {review.meta.get('fecha', '')}",
        "",
    ]
    if review.resumen:
        lines += ["**Resumen:**", review.resumen, ""]
    hallazgos = filter_hallazgos(review.hallazgos, severidad, tipo)
    if not hallazgos:
        lines += ["**Hallazgos:** ninguno coincidente." if (severidad or tipo) else "**Hallazgos:** ninguno.", ""]
        return "\n".join(lines)
    lines.append(f"**Hallazgos ({len(hallazgos)}):**")
    lines += [f"- [{h.severidad}][{h.tipo}] {h.archivo_linea} — {h.descripcion}. Sugerencia: {h.sugerencia}" for h in hallazgos]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Consulta code reviews del backlog en GitHub.")
    parser.add_argument("--repo")
    parser.add_argument("--modulo")
    parser.add_argument("--epica", type=int)
    parser.add_argument("--issue", type=int)
    parser.add_argument("--severidad", help="CRITICO | WARNING")
    parser.add_argument("--tipo", help="Gherkin | Ficha | Convencion | Heuristica | Tests")
    parser.add_argument("--veredicto", help='"APROBADO" | "APROBADO CON OBSERVACIONES" | "REQUIERE CAMBIOS"')
    parser.add_argument("--solo-bloqueantes", action="store_true")
    args = parser.parse_args()

    if args.severidad and args.severidad.upper() not in SEVERIDADES_VALIDAS:
        parser.error(f"--severidad debe ser uno de {sorted(SEVERIDADES_VALIDAS)}")
    if args.veredicto and _normalizar_veredicto(args.veredicto) not in VEREDICTOS_VALIDOS:
        parser.error(f"--veredicto debe ser uno de {sorted(VEREDICTOS_VALIDOS)}")

    repo = args.repo or repo_from_config()
    reviews = load_reviews(repo)
    if not reviews:
        print("No hay reviews aun.")
        sys.exit(0)

    hijos = epic_children(repo, args.epica) if args.epica else None
    filtered = filter_reviews(reviews, args.modulo, args.issue, args.veredicto, args.solo_bloqueantes, hijos)
    if not filtered:
        print("Sin resultados para los filtros indicados.")
        sys.exit(0)

    print(f"# Reviews ({len(filtered)} encontrados)\n")
    for review in filtered:
        print(format_review(review, args.severidad, args.tipo))
        print("---\n")


if __name__ == "__main__":
    main()
