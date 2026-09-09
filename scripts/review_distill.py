#!/usr/bin/env python3
"""Destila los code reviews del backlog en insights accionables.

Uso:
    python3 review_distill.py            # imprime el reporte
    python3 review_distill.py --publish  # upsert del issue "Insights destilados de code reviews"
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date

from timonel_gh import Review, load_reviews, normalizar_descripcion, repo_from_config, upsert_issue_by_title

TITULO_ISSUE = "Insights destilados de code reviews"


def _veredicto_table(reviews: list[Review]) -> str:
    groups: dict[tuple[str, str], list[Review]] = defaultdict(list)
    for r in reviews:
        groups[(r.modulo or "sin-modulo", r.alcance or "sin-alcance")].append(r)
    rows = []
    for (modulo, alcance), items in sorted(groups.items()):
        c = Counter(r.veredicto for r in items)
        rows.append(
            f"| {modulo} | {alcance} | {len(items)} | {c.get('APROBADO', 0)} | "
            f"{c.get('APROBADO CON OBSERVACIONES', 0)} | {c.get('REQUIERE CAMBIOS', 0)} |"
        )
    if not rows:
        return "_Sin reviews._\n"
    header = (
        "| Modulo | Alcance | Historias | Aprobadas | Con observaciones | Requiere cambios |\n"
        "|--------|---------|-----------|-----------|-------------------|------------------|\n"
    )
    return header + "\n".join(rows) + "\n"


def _por_tipo(reviews: list[Review], tipo: str, min_count: int) -> str:
    agrupado: dict[str, tuple[str, set[int]]] = {}
    for r in reviews:
        for h in r.hallazgos:
            if h.tipo_normalizado.lower() != tipo.lower():
                continue
            key = normalizar_descripcion(h.descripcion)
            agrupado.setdefault(key, (h.descripcion.strip(), set()))[1].add(r.issue)
    filas = sorted(
        ((d, sorted(i)) for d, i in agrupado.values() if len(i) >= min_count),
        key=lambda t: (-len(t[1]), t[0].lower()),
    )
    if not filas:
        return f"_Ningun hallazgo aparece {min_count}+ veces aun._\n"
    return "\n".join(f"- ({len(i)}x en {', '.join(f'#{n}' for n in i)}) {d}" for d, i in filas) + "\n"


def _gherkin_criticos(reviews: list[Review]) -> str:
    lines = []
    for r in reviews:
        for h in r.hallazgos:
            if h.tipo_normalizado == "Gherkin" and h.severidad == "CRITICO":
                lines.append(f"- [#{r.issue}] {h.archivo_linea} — {h.descripcion.strip()}")
    return ("\n".join(lines) + "\n") if lines else "_Sin criterios Gherkin fallidos registrados._\n"


def _archivos_problematicos(reviews: list[Review], min_issues: int = 2) -> str:
    por_archivo: dict[str, set[int]] = defaultdict(set)
    severidades: dict[str, Counter[str]] = defaultdict(Counter)
    for r in reviews:
        for h in r.hallazgos:
            if h.archivo and h.archivo != "-":
                por_archivo[h.archivo].add(r.issue)
                severidades[h.archivo][h.severidad] += 1
    frecuentes = sorted(
        ((a, sorted(i)) for a, i in por_archivo.items() if len(i) >= min_issues),
        key=lambda t: (-len(t[1]), t[0]),
    )
    if not frecuentes:
        return f"_Ningun archivo aparece en {min_issues}+ historias distintas._\n"
    return "\n".join(
        f"- ({len(i)} historias: {', '.join(f'#{n}' for n in i)}) {a} — "
        + ", ".join(f"{s}={c}" for s, c in severidades[a].most_common())
        for a, i in frecuentes
    ) + "\n"


def generate_report(reviews: list[Review]) -> str:
    return f"""<!-- timonel:insights-review -->
> Generado: {date.today().isoformat()} | Reviews: {len(reviews)} | Criticos: {sum(r.criticos for r in reviews)} | Warnings: {sum(r.warnings for r in reviews)} | Bloqueantes: {sum(1 for r in reviews if r.bloquea_dod)}

## Resumen de veredictos

{_veredicto_table(reviews)}
## Convenciones mas violadas (2+ historias)

{_por_tipo(reviews, "Convencion", 2)}
## Heuristicas mas violadas (2+ historias)

{_por_tipo(reviews, "Heuristica", 2)}
## Criterios Gherkin fallidos (CRITICO)

{_gherkin_criticos(reviews)}
## Archivos problematicos frecuentes (2+ historias)

{_archivos_problematicos(reviews)}"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Destila code reviews en insights.")
    parser.add_argument("--repo")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    repo = args.repo or repo_from_config()
    reviews = load_reviews(repo)
    if not reviews:
        print("No hay reviews aun. Implementa historias para generar reviews.")
        return
    report = generate_report(reviews)
    if args.publish:
        num = upsert_issue_by_title(repo, TITULO_ISSUE, report, ["insights"])
        print(f"Insights publicados en #{num} ({len(reviews)} reviews)")
    else:
        print(report)


if __name__ == "__main__":
    main()
