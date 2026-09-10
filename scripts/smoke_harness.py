#!/usr/bin/env python3
"""Smoke E2E del harness: mide cuantos sensores/hooks dispararon en la practica
sobre HUs reales ya implementadas (gap 4 de la auditoria #11, issue #29).

Uso:
    python3 smoke_harness.py [--repo owner/repo] [--issues 27,28] [--events-log .timonel/events.log]

Por cada issue mide cobertura de los 6 marcadores, labels review:*/retro:*,
issues derivados por cosechar_retro.py y commits que lo referencian; ademas
cuenta eventos `[gh]` y `raiz-editada` en el events.log de una sesion de
consumidor (no vive en este repo). Imprime una tabla de disparos por
sensor/hook, una tabla de cobertura por HU y la linea final
`SMOKE: <k> de <m> sensores dispararon`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from timonel_gh import find_marker_comment, gh_json, label_value, parse_secciones, repo_from_config

MARCADORES = ["investigacion", "contrato-api", "consolidacion", "review", "retro", "dod"]

SI_NO = {True: "sí", False: "no"}

FilaDisparo = tuple[str, str, str]


# ---------------------------------------------------------------------------
# Funciones puras (testeables sin gh)
# ---------------------------------------------------------------------------


def medir_issue(issue: dict, derivados: list[dict], commits: list[str]) -> dict:
    """Cobertura de artefactos de una HU: marcadores, labels, derivados y commits."""
    numero = issue.get("number")
    comments = issue.get("comments", [])
    label_names = issue.get("label_names") or [l["name"] for l in issue.get("labels") or []]
    marcadores = {m: bool(find_marker_comment(comments, m)) for m in MARCADORES}

    origen = re.compile(rf"Origen: retro #{numero}\b")
    derivados_por_origen = sorted(d["number"] for d in derivados if origen.search(d.get("body") or ""))

    retro_body = find_marker_comment(comments, "retro") or ""
    secciones = parse_secciones(retro_body)
    derivados_en_retro = sorted(
        int(n)
        for bullet in secciones.get("Issues derivados", [])
        for n in re.findall(r"#(\d+)$", bullet)
    )

    return {
        "issue": numero,
        "marcadores": marcadores,
        "review": label_value(label_names, "review"),
        "retro": label_value(label_names, "retro"),
        "derivados_por_origen": derivados_por_origen,
        "derivados_en_retro": derivados_en_retro,
        "commits": len(commits),
    }


def contar_eventos(lineas: list[str]) -> dict:
    """Cuenta entradas `[gh]` (por ancla de inicio, no por numero de lineas de
    archivo: un comando multilinea es UNA entrada) y avisos `raiz-editada`."""
    gh_anchor = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]\[gh\]")
    raiz_anchor = re.compile(r"^\d{2}:\d{2}:\d{2} raiz-editada ")
    return {
        "gh": sum(1 for linea in lineas if gh_anchor.match(linea)),
        "raiz-editada": sum(1 for linea in lineas if raiz_anchor.match(linea)),
    }


def _fila_hook(nombre: str, n: int | None, texto_en_cero: str) -> FilaDisparo:
    """Una fila de hook a partir del conteo de eventos: None (sin events.log) y
    0 (perfil sin ese consumidor) son casos distintos de 'no disparo'."""
    if n is None:
        sin_datos = "sin datos (events.log ausente)"
        return (nombre, sin_datos, sin_datos)
    if n == 0:
        return (nombre, "0 eventos", texto_en_cero)
    return (nombre, f"{n} eventos", "sí")


def _filas_disparo(mediciones: list[dict], eventos: dict | None) -> list[FilaDisparo]:
    """Una fila por sensor/hook medible. No inventa filas para dor_check ni
    estado_historia: no son observables de forma directa desde el issue."""
    validas = [m for m in mediciones if "error" not in m]
    filas: list[FilaDisparo] = []

    for marcador in MARCADORES:
        evidencia = ", ".join(f"#{m['issue']} {SI_NO[bool(m['marcadores'].get(marcador))]}" for m in validas)
        dispara = any(m["marcadores"].get(marcador) for m in validas)
        filas.append((f"marcador `{marcador}`", evidencia or "sin datos", SI_NO[dispara]))

    evidencia_review = ", ".join(f"#{m['issue']} {m['review'] or '-'}" for m in validas)
    filas.append(("label `review:*`", evidencia_review or "sin datos", SI_NO[any(m["review"] for m in validas)]))

    evidencia_retro = ", ".join(f"#{m['issue']} {m['retro'] or '-'}" for m in validas)
    filas.append(("label `retro:*`", evidencia_retro or "sin datos", SI_NO[any(m["retro"] for m in validas)]))

    def n_derivados(m: dict) -> int:
        return len(set(m["derivados_por_origen"]) | set(m["derivados_en_retro"]))

    evidencia_derivados = ", ".join(f"#{m['issue']} {n_derivados(m)} derivados" for m in validas)
    filas.append((
        "`cosechar_retro.py` (issues derivados)",
        evidencia_derivados or "sin datos",
        SI_NO[any(n_derivados(m) >= 1 for m in validas)],
    ))

    evidencia_commits = ", ".join(f"#{m['issue']} {m['commits']} commits" for m in validas)
    filas.append(("commits `#N` en git log", evidencia_commits or "sin datos", SI_NO[any(m["commits"] for m in validas)]))

    n_gh = eventos.get("gh") if eventos is not None else None
    filas.append(_fila_hook("hook PostToolUse `[gh]`", n_gh, "no"))

    n_raiz = eventos.get("raiz-editada") if eventos is not None else None
    filas.append(_fila_hook("hook `raiz-editada`", n_raiz, "N/A en perfil plugin (sin consumidor)"))

    return filas


def _tabla_por_hu(mediciones: list[dict]) -> str:
    encabezado = "## Cobertura por HU\n\n| Issue | marcadores | review | retro | derivados | commits |\n| --- | --- | --- | --- | --- | --- |\n"
    filas = []
    for m in mediciones:
        if "error" in m:
            filas.append(f"| #{m.get('issue', '?')} | error: {m['error']} |  |  |  |  |")
            continue
        n_marcadores = sum(1 for v in m["marcadores"].values() if v)
        derivados = len(set(m["derivados_por_origen"]) | set(m["derivados_en_retro"]))
        filas.append(
            f"| #{m['issue']} | {n_marcadores}/6 | {m['review'] or '-'} | {m['retro'] or '-'} | {derivados} | {m['commits']} |"
        )
    return encabezado + "\n".join(filas)


def tabla_disparos(mediciones: list[dict], eventos: dict | None) -> str:
    """Tabla Markdown 'Disparos por sensor/hook' + tabla de cobertura por HU."""
    filas = _filas_disparo(mediciones, eventos)
    encabezado = "## Disparos por sensor/hook\n\n| Sensor/Hook | Evidencia | Disparó |\n| --- | --- | --- |\n"
    cuerpo = "\n".join(f"| {sensor} | {evidencia} | {disparo} |" for sensor, evidencia, disparo in filas)
    return f"{encabezado}{cuerpo}\n\n{_tabla_por_hu(mediciones)}"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def _medir_con_gh(repo: str, numero: int) -> dict:
    issue = gh_json("issue", "view", str(numero), "-R", repo, "--json", "number,title,body,labels,comments")
    issue["label_names"] = [l["name"] for l in issue["labels"]]
    candidatos = gh_json(
        "issue", "list", "-R", repo, "--search", f"Origen: retro #{numero}",
        "--state", "all", "--json", "number,body", "--limit", "50",
    )
    ancla = re.compile(rf"Origen: retro #{numero}\b")
    derivados = [d for d in candidatos if ancla.search(d.get("body") or "")]
    proc = subprocess.run(
        ["git", "log", "--oneline", "--all", "--grep", f"#{numero}"], capture_output=True, text=True,
    )
    commits = [linea for linea in proc.stdout.splitlines() if linea.strip()]
    return medir_issue(issue, derivados, commits)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke E2E: mide disparos de sensores/hooks sobre HUs reales.")
    parser.add_argument("--repo")
    parser.add_argument("--issues", default="27,28")
    parser.add_argument("--events-log", default=".timonel/events.log")
    args = parser.parse_args()

    repo = args.repo or repo_from_config()
    numeros = [int(n) for n in args.issues.split(",") if n.strip()]

    mediciones: list[dict] = []
    for numero in numeros:
        try:
            mediciones.append(_medir_con_gh(repo, numero))
        except (SystemExit, Exception) as exc:
            mediciones.append({"issue": numero, "error": str(exc)})

    events_path = Path(args.events_log)
    eventos = contar_eventos(events_path.read_text(encoding="utf-8").splitlines()) if events_path.exists() else None

    print(tabla_disparos(mediciones, eventos))
    filas = _filas_disparo(mediciones, eventos)
    disparados = sum(1 for _, _, disparo in filas if disparo == "sí")
    print(f"\nSMOKE: {disparados} de {len(filas)} sensores dispararon")


if __name__ == "__main__":
    main()
