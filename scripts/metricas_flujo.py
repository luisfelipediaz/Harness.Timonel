#!/usr/bin/env python3
"""Metricas de flujo del backlog (gap 15 de la auditoria #11, issue #23).

Uso:
    python3 metricas_flujo.py [--repo owner/repo] [--publish]

Mide, sobre las HUs cerradas: cobertura de artefactos (review, retro, dod), % de
review aprobado a la primera, distribucion de precision de estimacion, lead time
(creacion → cierre) y HUs abiertas por estado. --publish hace upsert del issue
"Métricas de flujo" (label insights).
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime

from timonel_gh import fetch_issues, find_marker_comment, label_value, repo_from_config, upsert_issue_by_title

TITULO_ISSUE = "Métricas de flujo"


def _dias(a: str | None, b: str | None) -> float | None:
    if not a or not b:
        return None
    fa = datetime.fromisoformat(a.replace("Z", "+00:00"))
    fb = datetime.fromisoformat(b.replace("Z", "+00:00"))
    return (fb - fa).total_seconds() / 86400


def calcular(cerradas: list[dict], abiertas: list[dict]) -> dict:
    n = len(cerradas)
    con = Counter()
    review_labels = Counter()
    retro_labels = Counter()
    lead = []
    for i in cerradas:
        c = i.get("comments", [])
        for m in ("review", "retro", "dod", "investigacion", "contrato-api"):
            if find_marker_comment(c, m):
                con[m] += 1
        review_labels[label_value(i["label_names"], "review") or "sin-label"] += 1
        retro_labels[label_value(i["label_names"], "retro") or "sin-label"] += 1
        d = _dias(i.get("createdAt"), i.get("closedAt"))
        if d is not None:
            lead.append(d)
    estados = Counter(label_value(i["label_names"], "estado") or "sin-estado" for i in abiertas)
    return {
        "cerradas": n,
        "cobertura": {m: con[m] for m in ("investigacion", "contrato-api", "review", "retro", "dod")},
        "review": dict(review_labels),
        "retro": dict(retro_labels),
        "lead_time_prom": (sum(lead) / len(lead)) if lead else None,
        "lead_time_max": max(lead) if lead else None,
        "abiertas_por_estado": dict(estados),
        "bloqueadas": sum(1 for i in abiertas if "bloqueado" in i["label_names"]),
    }


def _pct(x: int, n: int) -> str:
    return f"{x} ({100 * x // n}%)" if n else "0"


def reporte(m: dict) -> str:
    n = m["cerradas"]
    cob = "\n".join(f"| {k} | {_pct(v, n)} |" for k, v in m["cobertura"].items())
    rev = "\n".join(f"| {k} | {_pct(v, n)} |" for k, v in sorted(m["review"].items()))
    ret = "\n".join(f"| {k} | {_pct(v, n)} |" for k, v in sorted(m["retro"].items()))
    est = "\n".join(f"| {k} | {v} |" for k, v in sorted(m["abiertas_por_estado"].items()))
    lt = f"{m['lead_time_prom']:.1f} días (máx {m['lead_time_max']:.1f})" if m["lead_time_prom"] is not None else "sin datos"
    aprobado_primera = m["review"].get("aprobado", 0) + m["review"].get("observaciones", 0)
    return f"""<!-- timonel:metricas -->
> Generado: {date.today().isoformat()} | HUs cerradas: {n} | Abiertas: {sum(m['abiertas_por_estado'].values())} | Bloqueadas: {m['bloqueadas']}

## Cobertura de artefactos en HUs cerradas

| Artefacto | HUs con el comentario |
| --- | --- |
{cob}

Una HU cerrada sin `review`/`retro`/`dod` es un salto del harness: revisar por qué.

## Code review a la primera

| Label review | HUs |
| --- | --- |
{rev}

Aprobadas sin cambios críticos a la primera: **{_pct(aprobado_primera, n)}**.

## Precisión de estimación

| Label retro | HUs |
| --- | --- |
{ret}

## Lead time (creación → cierre)

{lt}

## Backlog abierto por estado

| Estado | HUs |
| --- | --- |
{est}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Metricas de flujo del backlog.")
    parser.add_argument("--repo")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    repo = args.repo or repo_from_config()
    cerradas = fetch_issues(repo, ["tipo:hu"], state="closed")
    abiertas = fetch_issues(repo, ["tipo:hu"], state="open")
    # createdAt no viene en fetch_issues: lo pedimos aparte solo para cerradas
    if cerradas:
        from timonel_gh import gh_json
        extra = {i["number"]: i for i in gh_json("issue", "list", "-R", repo, "--label", "tipo:hu", "--state", "closed", "--limit", "500", "--json", "number,createdAt,closedAt")}
        for i in cerradas:
            i.update(extra.get(i["number"], {}))
    rep = reporte(calcular(cerradas, abiertas))
    if args.publish:
        num = upsert_issue_by_title(repo, TITULO_ISSUE, rep, ["insights"])
        print(f"Métricas publicadas en #{num}")
    else:
        print(rep)


if __name__ == "__main__":
    main()
