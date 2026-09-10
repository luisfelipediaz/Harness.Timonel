#!/usr/bin/env python3
"""Migra un backlog en markdown (formato del harness original) a GitHub Issues.

Lee `docs/user-stories/BACKLOG.md` + archivos de HU (individuales o dentro de
`completadas.md`) y crea epicas (`tipo:epica`) con sus HUs como sub-issues.
Completadas -> cerradas `completed`; tachadas -> `obsoleta` + `not planned`.
Retros/reviews `.retro.md` / `.review.md` -> comentario con marcador.

Uso:
    python3 migrate_backlog.py --docs docs/user-stories            # dry-run: imprime el plan
    python3 migrate_backlog.py --docs docs/user-stories --apply    # crea en github.repo del config
    python3 migrate_backlog.py --docs ... --repo owner/repo --apply

Idempotente: busca `Id histórico: HU-XXX` en issues existentes antes de crear.
"""

from __future__ import annotations

import argparse
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from timonel_gh import gh, gh_json, load_config, repo_from_config

LINEA_HU = re.compile(
    r"^- \[(?P<done>[x ])\] (?P<tacha>~~)?\[(?P<id>HU-\d+)\]\((?P<ruta>[^)]+)\)"
    r"(?:~~)?:\s*(?P<titulo>.*?)(?:~~)?(?:\s*—\s*(?P<resto>.*))?$"
)
MOSCOW_SP = re.compile(r"(?P<moscow>Must|Should|Could|Won't) Have \((?P<sp>\d+) SP\)")
EPICA = re.compile(r"^### Epica (?P<num>\d+):\s*(?P<titulo>.+)$")
TITULO_HU = re.compile(r"^## (?P<id>HU-\d+):\s*(?P<titulo>.+)$", re.MULTILINE)

MOSCOW_LABEL = {"Must": "must", "Should": "should", "Could": "could", "Won't": "wont"}
ALCANCE_LABEL = {"backend": "backend", "frontend": "frontend", "full-stack": "full-stack"}
TAREAS = [
    "Contrato API aprobado", "Modelos compartidos", "Backend", "Frontend",
    "Consolidación (lint + tests)", "Code review", "Retrospectiva", "Definition of Done",
]
# Encabezados del formato viejo -> canon de la plantilla (TIM-ADR-0001 §6.4)
RENOMBRES = {
    "### Criterios de Aceptacion": "## Criterios de aceptación",
    "### Criterios de Aceptación": "## Criterios de aceptación",
    "### INVEST": "## INVEST",
    "### Ficha Tecnica": "## Ficha técnica",
    "### Ficha Técnica": "## Ficha técnica",
    "### Endpoints sugeridos": "## Endpoints",
    "### Modelos compartidos": "## Modelos compartidos",
    "### Notas Tecnicas (opcional)": "## Notas técnicas",
    "### Notas Tecnicas": "## Notas técnicas",
    "### Notas Técnicas": "## Notas técnicas",
    "### Alcance Tecnico": "## Notas técnicas",
    "### Alcance Técnico": "## Notas técnicas",
}
TRAILERS = ("**MoSCoW:**", "**Story Points:**", "**Prioridad:**", "**Dependencias:**")


@dataclass
class Epica:
    numero: int
    titulo: str


@dataclass
class Historia:
    id: str
    titulo: str
    ruta: str
    epica: int
    completada: bool
    obsoleta: bool
    moscow: str | None
    sp: int | None
    nota: str


@dataclass
class Backlog:
    epicas: list[Epica]
    historias: list[Historia]

    @property
    def por_id(self) -> dict[str, Historia]:
        return {h.id: h for h in self.historias}


@dataclass
class Spec:
    titulo: str
    cuerpo: str
    ficha: dict[str, str]
    prioridad: str
    dependencias: list[str]


# ---------------------------------------------------------------------------
# Parseo
# ---------------------------------------------------------------------------


def parse_backlog(path: Path) -> Backlog:
    epicas: list[Epica] = []
    historias: list[Historia] = []
    epica_actual = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        m = EPICA.match(line.strip())
        if m:
            epica_actual = int(m.group("num"))
            epicas.append(Epica(epica_actual, m.group("titulo").strip()))
            continue
        m = LINEA_HU.match(line.strip())
        if not m:
            continue
        resto = m.group("resto") or ""
        ms = MOSCOW_SP.search(resto)
        tachada = bool(m.group("tacha")) or line.strip().startswith("- [x] ~~")
        historias.append(
            Historia(
                id=m.group("id"),
                titulo=m.group("titulo").strip().rstrip("~"),
                ruta=m.group("ruta"),
                epica=epica_actual,
                completada=m.group("done") == "x",
                obsoleta=tachada,
                moscow=MOSCOW_LABEL[ms.group("moscow")] if ms else None,
                sp=int(ms.group("sp")) if ms else None,
                nota="" if ms else resto.strip(),
            )
        )
    return Backlog(epicas, historias)


def _extraer_de_completadas(texto: str, hu_id: str) -> str:
    matches = list(TITULO_HU.finditer(texto))
    for i, m in enumerate(matches):
        if m.group("id") == hu_id:
            fin = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
            return texto[m.start():fin].rstrip().rstrip("-").rstrip()
    raise ValueError(f"{hu_id} no aparece en completadas.md")


def _ficha(texto: str) -> dict[str, str]:
    ficha: dict[str, str] = {}
    for line in texto.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0] not in ("Campo", "Criterio") and not re.match(r"^-+$", cells[0]):
            ficha.setdefault(cells[0], cells[1])
    return ficha


def load_spec(docs: Path, ruta: str, hu_id: str) -> Spec:
    texto = (docs / ruta).read_text(encoding="utf-8")
    if ruta.endswith("completadas.md"):
        texto = _extraer_de_completadas(texto, hu_id)
    m = TITULO_HU.search(texto)
    titulo = m.group("titulo").strip() if m else hu_id
    cuerpo = texto[m.end():].strip() if m else texto.strip()
    prio = re.search(r"\*\*Prioridad:\*\*\s*(\w+)", cuerpo)
    deps_line = re.search(r"\*\*Dependencias:\*\*\s*(.+)", cuerpo)
    deps_txt = deps_line.group(1).strip() if deps_line else ""
    deps = [] if deps_txt.lower().startswith("ningun") else re.findall(r"HU-\d+", deps_txt)
    return Spec(
        titulo=titulo,
        cuerpo=cuerpo,
        ficha=_ficha(cuerpo),
        prioridad=(prio.group(1).lower() if prio else ""),
        dependencias=deps,
    )


# ---------------------------------------------------------------------------
# Transformacion a issue
# ---------------------------------------------------------------------------


def _renombrar_secciones(cuerpo: str) -> str:
    out = []
    for line in cuerpo.splitlines():
        stripped = line.strip()
        if stripped in RENOMBRES:
            out.append(RENOMBRES[stripped])
        elif stripped.startswith(TRAILERS):
            continue
        else:
            out.append(line)
    return "\n".join(out).strip()


def _tareas(hu: Historia) -> str:
    marca = "x" if hu.completada else " "
    return "\n".join(f"- [{marca}] {t}" for t in TAREAS)


def build_body(hu: Historia, spec: Spec, mapa_ids: dict[str, int]) -> str:
    deps = [f"Depende de #{mapa_ids[d]}" if d in mapa_ids else f"Depende de {d} (sin migrar)" for d in spec.dependencias]
    partes = [
        f"Id histórico: {hu.id}" + (f" — {hu.nota}" if hu.nota else ""),
        "",
        "## Historia",
        "",
        _renombrar_secciones(spec.cuerpo),
        "",
        "## Dependencias",
        "",
        "\n".join(deps) if deps else "Ninguna",
        "",
        "## Tareas",
        "",
        _tareas(hu),
    ]
    return "\n".join(partes).strip() + "\n"


def build_labels(hu: Historia, spec: Spec, modulos: set[str]) -> list[str]:
    labels = ["tipo:hu"]
    alcance = ALCANCE_LABEL.get(spec.ficha.get("Alcance", "").lower())
    if alcance:
        labels.append(f"alcance:{alcance}")
    if hu.moscow:
        labels.append(f"moscow:{hu.moscow}")
    if hu.sp:
        labels.append(f"sp:{hu.sp}")
    if spec.prioridad in ("alta", "media", "baja"):
        labels.append(f"prioridad:{spec.prioridad}")
    modulo = spec.ficha.get("Modulo destino", spec.ficha.get("Módulo destino", "")).strip()
    if modulo in modulos:
        labels.append(f"mod:{modulo}")
    if hu.obsoleta:
        labels.append("obsoleta")
    if not hu.completada:
        completa = spec.ficha.get("Alcance") and "POR DEFINIR" not in spec.cuerpo
        labels.append("estado:listo" if completa else "estado:borrador")
    return labels


def _frontmatter(texto: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", texto, re.DOTALL)
    if not m:
        return {}, texto
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if _:
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def retro_file_to_comment(texto: str) -> str:
    meta, body = _frontmatter(texto)
    yaml = "\n".join(f"{k}: {meta[k]}" for k in ("fecha", "estimado_sp", "real_sp", "precision_estimacion", "alcance", "modulo") if k in meta)
    body = re.sub(r"^## ", "### ", body, flags=re.MULTILINE).strip()
    return f"<!-- timonel:retro -->\n## Retrospectiva\n\n```yaml\n{yaml}\n```\n\n{body}\n"


def review_file_to_comment(texto: str) -> str:
    meta, body = _frontmatter(texto)
    yaml = "\n".join(f"{k}: {meta[k]}" for k in ("fecha", "veredicto", "criticos", "warnings", "alcance", "modulo", "bloquea_dod") if k in meta)
    body = re.sub(r"^## ", "### ", body, flags=re.MULTILINE).strip()
    return f"<!-- timonel:review -->\n## Code review\n\n```yaml\n{yaml}\n```\n\n{body}\n"


# ---------------------------------------------------------------------------
# Ejecucion contra GitHub
# ---------------------------------------------------------------------------


def _existentes(repo: str) -> tuple[dict[str, int], dict[int, int]]:
    """(HU-XXX -> issue, epica_num -> issue) ya migrados."""
    issues = gh_json("issue", "list", "-R", repo, "--state", "all", "--limit", "1000", "--json", "number,body,labels,title")
    hus, epicas = {}, {}
    for i in issues:
        m = re.match(r"Id histórico: (HU-\d+)", i.get("body") or "")
        if m:
            hus[m.group(1)] = i["number"]
        m = re.match(r"Id histórico: Epica (\d+)", i.get("body") or "")
        if m:
            epicas[int(m.group(1))] = i["number"]
    return hus, epicas


def _crear(repo: str, titulo: str, body: str, labels: list[str]) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        path = f.name
    args = ["issue", "create", "-R", repo, "--title", titulo, "--body-file", path]
    for l in labels:
        args += ["--label", l]
    return int(gh(*args).strip().rsplit("/", 1)[-1])


def _node_id(repo: str, num: int) -> str:
    return gh("issue", "view", str(num), "-R", repo, "--json", "id", "-q", ".id").strip()


def _sub_issue(repo: str, padre: int, hijo: int) -> None:
    q = "mutation($p:ID!,$c:ID!){ addSubIssue(input:{issueId:$p, subIssueId:$c, replaceParent:true}){ subIssue{ number } } }"
    gh("api", "graphql", "-f", f"query={q}", "-f", f"p={_node_id(repo, padre)}", "-f", f"c={_node_id(repo, hijo)}")


def _comentar(repo: str, num: int, body: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        path = f.name
    gh("issue", "comment", str(num), "-R", repo, "--body-file", path)


def migrar(docs: Path, repo: str, modulos: set[str], apply: bool) -> None:
    backlog = parse_backlog(docs / "BACKLOG.md")
    hus_exist, epicas_exist = _existentes(repo) if apply else ({}, {})
    print(f"Backlog: {len(backlog.epicas)} epicas, {len(backlog.historias)} historias -> {repo} ({'APPLY' if apply else 'DRY-RUN'})")

    mapa_epicas: dict[int, int] = dict(epicas_exist)
    for e in backlog.epicas:
        if e.numero in mapa_epicas:
            print(f"  epica {e.numero} ya existe como #{mapa_epicas[e.numero]}")
            continue
        body = f"Id histórico: Epica {e.numero}\n\n## Objetivo\n\n{e.titulo}\n\n## Alcance\n\nMigrada desde docs/user-stories. Ver sub-issues.\n"
        if apply:
            mapa_epicas[e.numero] = _crear(repo, e.titulo, body, ["tipo:epica"])
            print(f"  epica {e.numero} -> #{mapa_epicas[e.numero]}")
        else:
            print(f"  [crear epica] {e.numero}: {e.titulo}")

    # Primera pasada: crear HUs (sin dependencias resueltas) para tener el mapa de ids.
    mapa_hus: dict[str, int] = dict(hus_exist)
    specs: dict[str, Spec] = {}
    for hu in backlog.historias:
        try:
            specs[hu.id] = load_spec(docs, hu.ruta, hu.id)
        except (FileNotFoundError, ValueError) as exc:
            print(f"  AVISO {hu.id}: {exc}; se crea con body minimo")
            specs[hu.id] = Spec(hu.titulo, f"## Criterios de aceptación\n\nNo migrados (spec no encontrada).\n", {}, "", [])
        if hu.id in mapa_hus:
            print(f"  {hu.id} ya existe como #{mapa_hus[hu.id]}")
            continue
        labels = build_labels(hu, specs[hu.id], modulos)
        if apply:
            mapa_hus[hu.id] = _crear(repo, specs[hu.id].titulo, build_body(hu, specs[hu.id], {}), labels)
            print(f"  {hu.id} -> #{mapa_hus[hu.id]} [{', '.join(labels)}]")
        else:
            estado = "obsoleta" if hu.obsoleta else ("cerrada" if hu.completada else "abierta")
            print(f"  [crear] {hu.id} ({estado}) {specs[hu.id].titulo} [{', '.join(labels)}]")

    if not apply:
        return

    # Segunda pasada: body definitivo con dependencias, sub-issue, cierre, comentarios.
    for hu in backlog.historias:
        num = mapa_hus[hu.id]
        spec = specs[hu.id]
        if hu.id not in hus_exist:
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write(build_body(hu, spec, mapa_hus))
                gh("issue", "edit", str(num), "-R", repo, "--body-file", f.name)
            if hu.epica in mapa_epicas:
                _sub_issue(repo, mapa_epicas[hu.epica], num)
            base = docs / hu.ruta
            if not hu.ruta.endswith("completadas.md"):
                retro = base.with_suffix("").with_suffix(".retro.md")
                review = base.with_suffix("").with_suffix(".review.md")
                if retro.exists():
                    _comentar(repo, num, retro_file_to_comment(retro.read_text(encoding="utf-8")))
                if review.exists():
                    _comentar(repo, num, review_file_to_comment(review.read_text(encoding="utf-8")))
            if hu.obsoleta:
                gh("issue", "close", str(num), "-R", repo, "--reason", "not planned", "--comment", hu.nota or "Obsoleta en la migracion.")
            elif hu.completada:
                gh("issue", "close", str(num), "-R", repo, "--reason", "completed", "--comment", "Completada antes de la migracion a GitHub Issues.")
            print(f"  {hu.id} #{num} listo")
    print("Migracion terminada.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra docs/user-stories a GitHub Issues.")
    parser.add_argument("--docs", default="docs/user-stories", help="Carpeta con BACKLOG.md")
    parser.add_argument("--repo", help="owner/repo (default: github.repo del config)")
    parser.add_argument("--apply", action="store_true", help="Crea los issues (sin esto es dry-run)")
    args = parser.parse_args()

    config = {}
    try:
        config = load_config()
    except SystemExit:
        if not args.repo:
            raise
    repo = args.repo or repo_from_config(config)
    modulos = set(config.get("modulos", []))
    migrar(Path(args.docs), repo, modulos, args.apply)


if __name__ == "__main__":
    main()
