#!/usr/bin/env python3
"""Metricas de flujo del backlog (gap 15 de la auditoria #11, issue #23; ratchet
y disparos de hooks, gap 4 de la auditoria #24, issue #30).

Uso:
    python3 metricas_flujo.py [--repo owner/repo] [--publish] [--events-log RUTA]

Mide, sobre las HUs cerradas: cobertura de artefactos (review, retro, dod), % de
review aprobado a la primera, distribucion de precision de estimacion, lead time
(creacion → cierre) y HUs abiertas por estado. Ademas mide el ratchet de issues
derivados por retro (cuantos genero cada HU origen, cuantas HUs con retro tuvieron
al menos un derivado, y en que estado quedaron: borrador/refinado/cerrado) y los
disparos de hooks registrados en `.timonel/events.log` de una sesion de consumidor
(`--events-log`; ese log no vive en este repo, sino en el cwd de la sesion de
Claude). --publish hace upsert del issue "Métricas de flujo" (label insights).
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from smoke_harness import contar_eventos, fila_hook
from timonel_gh import fetch_issues, find_marker_comment, label_value, origen_retro, repo_from_config, upsert_issue_by_title

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


BUCKET_POR_ESTADO = {"borrador": "borrador"}


def _bucket_derivado(issue: dict) -> str:
    """`cerrado` si el derivado ya cerro; si no, su bucket sale del label
    `estado:*` (default `refinado`: paso de `borrador` sin cerrar)."""
    if issue.get("state") == "CLOSED":
        return "cerrado"
    return BUCKET_POR_ESTADO.get(label_value(issue["label_names"], "estado"), "refinado")


def calcular_ratchet(cerradas: list[dict], abiertas: list[dict]) -> dict:
    """Issues derivados de retro (`Origen: retro #N`) agrupados por HU origen,
    cuantas HUs cerradas con retro generaron >=1 derivado, y en que estado
    quedaron los derivados (borrador/refinado/cerrado)."""
    por_origen: Counter = Counter()
    buckets: Counter = Counter()
    for i in cerradas + abiertas:
        origen = origen_retro(i.get("body") or "")
        if origen is None:
            continue
        por_origen[origen] += 1
        buckets[_bucket_derivado(i)] += 1
    con_retro = [i for i in cerradas if find_marker_comment(i.get("comments", []), "retro")]
    return {
        "total": sum(por_origen.values()),
        "por_origen": dict(por_origen),
        "hus_con_retro": len(con_retro),
        "hus_con_derivados": sum(1 for i in con_retro if por_origen.get(i["number"], 0) >= 1),
        "buckets": {b: buckets.get(b, 0) for b in ("borrador", "refinado", "cerrado")},
    }


def reporte_ratchet(r: dict) -> str:
    origenes = "\n".join(f"| #{origen} | {n} |" for origen, n in sorted(r["por_origen"].items()))
    estados = "\n".join(f"| {estado} | {n} |" for estado, n in r["buckets"].items())
    return f"""## Ratchet (issues derivados por retro)

Issues derivados de retro detectados: **{r['total']}**.

| HU origen | derivados |
| --- | --- |
{origenes}

HUs cerradas con retro que generaron ≥1 issue: **{_pct(r['hus_con_derivados'], r['hus_con_retro'])}**.

| Estado | derivados |
| --- | --- |
{estados}
"""


def reporte_disparos(eventos: dict | None) -> str:
    n_gh = eventos.get("gh") if eventos is not None else None
    n_raiz = eventos.get("raiz-editada") if eventos is not None else None
    filas = [
        fila_hook("hook PostToolUse `[gh]`", n_gh, "no"),
        fila_hook("hook `raiz-editada`", n_raiz, "no"),
    ]
    cuerpo = "\n".join(f"| {nombre} | {evidencia} | {disparo} |" for nombre, evidencia, disparo in filas)
    return f"""## Disparos de hooks

| Hook | Evidencia | Disparó |
| --- | --- | --- |
{cuerpo}

El `events.log` vive en el cwd de la sesion de Claude (no en este repo): pasalo con `--events-log`.
"""


def reporte(m: dict, ratchet: dict, eventos: dict | None) -> str:
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

{reporte_ratchet(ratchet)}
{reporte_disparos(eventos)}"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Metricas de flujo del backlog.")
    parser.add_argument("--repo")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--events-log", default=".timonel/events.log")
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
    events_path = Path(args.events_log)
    eventos = contar_eventos(events_path.read_text(encoding="utf-8").splitlines()) if events_path.exists() else None
    rep = reporte(calcular(cerradas, abiertas), calcular_ratchet(cerradas, abiertas), eventos)
    if args.publish:
        num = upsert_issue_by_title(repo, TITULO_ISSUE, rep, ["insights"])
        print(f"Métricas publicadas en #{num}")
    else:
        print(rep)


if __name__ == "__main__":
    main()
