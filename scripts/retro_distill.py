#!/usr/bin/env python3
"""Destila las retrospectivas del backlog en insights accionables.

Uso:
    python3 retro_distill.py            # imprime el reporte
    python3 retro_distill.py --publish  # upsert del issue "Insights destilados de retrospectivas" (label insights)
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date

from timonel_gh import Retro, load_retros, repo_from_config, upsert_issue_by_title

TITULO_ISSUE = "Insights destilados de retrospectivas"


def _estimation_table(retros: list[Retro]) -> str:
    groups: dict[tuple[str, str], list[Retro]] = {}
    for r in retros:
        groups.setdefault((r.modulo or "sin-modulo", r.alcance or "sin-alcance"), []).append(r)
    rows = []
    for (modulo, alcance), items in sorted(groups.items()):
        n = len(items)
        est = sum(r.estimado_sp for r in items) / n
        real = sum(r.real_sp for r in items) / n
        tendencia = Counter(r.precision for r in items).most_common(1)[0][0] or "—"
        rows.append(f"| {modulo} | {alcance} | {n} | {est:.1f} | {real:.1f} | {tendencia} |")
    if not rows:
        return "_Sin datos de estimacion._\n"
    header = (
        "| Modulo | Alcance | Historias | SP Estimado Prom. | SP Real Prom. | Tendencia |\n"
        "|--------|---------|-----------|-------------------|---------------|-----------|\n"
    )
    return header + "\n".join(rows) + "\n"


def _bullets(retros: list[Retro], section: str, min_count: int) -> str:
    counter: Counter[str] = Counter()
    ejemplo: dict[str, str] = {}
    for r in retros:
        for bullet in r.sections.get(section, []):
            key = bullet.strip().lower()
            counter[key] += 1
            ejemplo.setdefault(key, f"#{r.issue}")
    items = [(t, c) for t, c in counter.most_common() if c >= min_count]
    if not items:
        return f"_Ningun item aparece {min_count}+ veces aun._\n" if min_count > 1 else "_Sin entradas._\n"
    return "\n".join(f"- ({c}x, ej. {ejemplo[t]}) {t}" for t, c in items) + "\n"


def generate_report(retros: list[Retro]) -> str:
    return f"""<!-- timonel:insights-retro -->
> Generado: {date.today().isoformat()} | Retrospectivas analizadas: {len(retros)}

## Calibracion de estimaciones

{_estimation_table(retros)}
## Errores recurrentes (2+ ocurrencias)

{_bullets(retros, "Errores recurrentes", 2)}
## Patrones candidatos a convencion (2+ ocurrencias)

{_bullets(retros, "Patrones descubiertos", 2)}
## Mejoras sugeridas (todas)

{_bullets(retros, "Mejoras sugeridas", 1)}"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Destila retrospectivas en insights.")
    parser.add_argument("--repo", help="owner/repo (default: github.repo del config)")
    parser.add_argument("--publish", action="store_true", help="Publica/actualiza el issue de insights")
    args = parser.parse_args()

    repo = args.repo or repo_from_config()
    retros = load_retros(repo)
    if not retros:
        print("No hay retrospectivas aun. Implementa historias para generar retros.")
        return
    report = generate_report(retros)
    if args.publish:
        num = upsert_issue_by_title(repo, TITULO_ISSUE, report, ["insights"])
        print(f"Insights publicados en #{num} ({len(retros)} retrospectivas)")
    else:
        print(report)


if __name__ == "__main__":
    main()
