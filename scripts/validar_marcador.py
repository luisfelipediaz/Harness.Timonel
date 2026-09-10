#!/usr/bin/env python3
"""Valida un comentario con marcador antes de publicarlo (gap 5 de la auditoria #11, issue #17).

Uso:
    python3 validar_marcador.py <archivo.md>            # detecta el tipo por el marcador
    python3 validar_marcador.py <archivo.md> --tipo review

Sale con 0 si es valido; con 1 e imprime los problemas si no. Los skills lo corren
antes de `publicar_marcador` para que retro-tools nunca reciba datos rotos.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from timonel_gh import _split_row, parse_secciones, parse_tabla, parse_yaml_plano

# Contrato por tipo: claves YAML obligatorias, valores permitidos, secciones `### ` obligatorias.
CONTRATOS: dict[str, dict] = {
    "review": {
        "yaml": ["fecha", "veredicto", "criticos", "warnings", "alcance", "modulo", "bloquea_dod"],
        "valores": {
            "veredicto": {"APROBADO", "APROBADO CON OBSERVACIONES", "REQUIERE CAMBIOS"},
            "bloquea_dod": {"si", "no"},
            "alcance": {"Backend", "Frontend", "Full-stack"},
        },
        "secciones": ["Resumen", "Hallazgos", "Veredicto"],
        "tabla": "Hallazgos",
    },
    "retro": {
        "yaml": ["fecha", "estimado_sp", "real_sp", "precision_estimacion", "alcance", "modulo"],
        "valores": {
            "precision_estimacion": {"sobreestimado", "preciso", "subestimado"},
            "alcance": {"Backend", "Frontend", "Full-stack"},
        },
        "secciones": ["Desviaciones", "Errores recurrentes", "Patrones descubiertos", "Mejoras sugeridas", "Harness engineering"],
    },
    "dod": {
        "yaml": ["fecha", "decision"],
        "valores": {
            "decision": {"DONE", "FALLAS_CRITICAS", "PENDIENTES"},
            "perfil": {"consumidor", "plugin"},
        },
        "secciones": ["Decisión final"],
        "tabla": "dod",
    },
    "consolidacion": {
        "yaml": ["fecha", "lint", "tests", "providers_registrados", "rutas_registradas"],
        "valores": {
            "lint": {"PASSED", "FAILED"},
            "tests": {"PASSED", "FAILED", "NO_SPECS"},
            "providers_registrados": {"si", "no", "n-a"},
            "rutas_registradas": {"si", "no", "n-a"},
        },
        "secciones": ["Archivos"],
    },
    "contrato-api": {
        "yaml": ["fecha", "backend_desplegado"],
        "valores": {"backend_desplegado": {"si", "no"}},
        "secciones": ["Endpoints"],
    },
    "investigacion": {
        "yaml": ["fecha", "modulo", "alcance", "reutiliza_investigacion_de"],
        "valores": {"alcance": {"Backend", "Frontend", "Full-stack"}},
        "secciones": ["Archivos de referencia", "Patrón a replicar", "Riesgos y consideraciones"],
    },
    "refinamiento": {
        "yaml": ["fecha", "modo", "problemas_detectados", "cambios_aplicados"],
        "valores": {"modo": {"solo-reporte", "aplicar"}},
        "secciones": ["Resumen"],
    },
    "harness-audit": {
        "yaml": ["fecha", "alcance", "harness", "semi", "adhoc", "score", "auditoria_anterior"],
        "valores": {"alcance": {"consumidor", "plugin"}},
        "secciones": [],
    },
}
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ENTEROS = {"criticos", "warnings", "estimado_sp", "real_sp", "problemas_detectados", "cambios_aplicados", "harness", "semi", "adhoc", "score"}

# Filas CRITICAS del DoD (gap 3 de la auditoria #24, issue #28): en perfil plugin
# la retro (fila 9) tambien bloquea; el item 11 (code review) es critico en ambos.
FILAS_CRITICAS_POR_PERFIL: dict[str, tuple[int, ...]] = {
    "consumidor": (1, 2, 4, 8, 11),
    "plugin": (1, 2, 4, 8, 9, 11),
}
# Veredictos del item 11 que significan "nadie reviso el codigo": nunca validos con decision DONE.
VEREDICTOS_SIN_REVIEW = {"NO_GENERADO", "SKIPPED"}
# Motivo que acompana al rechazo de cada fila critica (mensaje util para quien publica el DoD).
MOTIVO_FILA_CRITICA: dict[int, str] = {
    9: "la retrospectiva es obligatoria en perfil plugin",
    11: "el code review nunca es SKIPPED en tipo:hu/hotfix",
}


def detectar_tipo(texto: str) -> str | None:
    m = re.match(r"\s*<!-- timonel:([a-z-]+)(?::[^>]*)? -->", texto)
    return m.group(1) if m else None


def _secciones_presentes(texto: str) -> set[str]:
    return {m.group(1).strip() for m in re.finditer(r"^#{2,3}\s+(.+)$", texto, re.MULTILINE)}


def validar(texto: str, tipo: str | None = None) -> list[str]:
    """Devuelve la lista de problemas (vacia si el comentario es valido)."""
    problemas: list[str] = []
    detectado = detectar_tipo(texto)
    tipo = tipo or detectado
    if not detectado:
        problemas.append("la primera linea debe ser el marcador `<!-- timonel:<tipo> -->`")
    elif tipo and detectado != tipo:
        problemas.append(f"marcador `{detectado}` no coincide con el tipo esperado `{tipo}`")
    if tipo not in CONTRATOS:
        problemas.append(f"tipo desconocido: {tipo!r}; validos: {sorted(CONTRATOS)}")
        return problemas
    contrato = CONTRATOS[tipo]

    meta = parse_yaml_plano(texto)
    if not meta:
        problemas.append("falta el bloque ```yaml con pares clave: valor")
    for clave in contrato["yaml"]:
        if clave not in meta:
            problemas.append(f"yaml: falta la clave `{clave}`")
    for clave, permitidos in contrato.get("valores", {}).items():
        valor = meta.get(clave)
        if valor is not None and valor not in permitidos:
            problemas.append(f"yaml: `{clave}: {valor}` no esta en {sorted(permitidos)}")
    if "fecha" in meta and not FECHA.match(meta["fecha"]):
        problemas.append(f"yaml: `fecha: {meta['fecha']}` debe ser YYYY-MM-DD")
    for clave in ENTEROS & set(meta):
        if not meta[clave].isdigit():
            problemas.append(f"yaml: `{clave}: {meta[clave]}` debe ser entero")

    presentes = _secciones_presentes(texto)
    for seccion in contrato["secciones"]:
        if seccion not in presentes:
            problemas.append(f"falta la seccion `### {seccion}`")

    if contrato.get("tabla") == "Hallazgos" and "Hallazgos" in presentes:
        filas = parse_tabla(texto, "Hallazgos")
        sin_hallazgos = re.search(r"^### Hallazgos\s*\n+\s*Sin hallazgos\.", texto, re.MULTILINE)
        if not filas and not sin_hallazgos:
            problemas.append("Hallazgos: tabla vacia o no parseable y sin la linea `Sin hallazgos.`")
        for fila in filas:
            if len(fila) < 6:
                problemas.append(f"Hallazgos: fila con {len(fila)} columnas (se esperan 6): {fila[:2]}")
            elif fila[2].upper() not in {"CRITICO", "WARNING"}:
                problemas.append(f"Hallazgos: severidad invalida `{fila[2]}` en fila {fila[0]}")
        declarados = (int(meta.get("criticos", "0") or 0), int(meta.get("warnings", "0") or 0)) if meta.get("criticos", "0").isdigit() and meta.get("warnings", "0").isdigit() else None
        if declarados and filas:
            criticos = sum(1 for f in filas if len(f) >= 6 and f[2].upper() == "CRITICO")
            warnings = sum(1 for f in filas if len(f) >= 6 and f[2].upper() == "WARNING")
            if (criticos, warnings) != declarados:
                problemas.append(f"yaml criticos/warnings ({declarados}) no coincide con la tabla ({criticos}, {warnings})")
        if meta.get("veredicto") == "REQUIERE CAMBIOS" and meta.get("bloquea_dod") != "si":
            problemas.append("REQUIERE CAMBIOS exige `bloquea_dod: si`")
        if meta.get("veredicto") in {"APROBADO", "APROBADO CON OBSERVACIONES"} and meta.get("bloquea_dod") == "si":
            problemas.append("solo REQUIERE CAMBIOS puede llevar `bloquea_dod: si`")

    if contrato.get("tabla") == "dod":
        filas = [_split_row(l) for l in texto.splitlines() if re.match(r"^\|\s*\d+\s*\|", l)]
        numeros = sorted({int(f[0]) for f in filas if f and f[0].isdigit()})
        if numeros != list(range(1, 12)):
            problemas.append(f"DoD: la tabla debe tener las 11 filas (1..11); tiene {numeros or 'ninguna'}")
        estados = {int(f[0]): f[2].upper() for f in filas if len(f) >= 3 and f[0].isdigit()}
        for n, est in estados.items():
            if not est.startswith(("PASSED", "FAILED", "SKIPPED")):
                problemas.append(f"DoD: fila {n} con estado invalido `{est}` (PASSED|FAILED|SKIPPED)")
        m11 = re.search(r"^Item 11 · veredicto:\s*(.+)$", texto, re.MULTILINE)
        if not m11:
            problemas.append("DoD: falta la linea `Item 11 · veredicto: <valor>`")
        veredicto_11 = m11.group(1).strip() if m11 else None
        if meta.get("decision") == "DONE":
            perfil = meta.get("perfil", "consumidor")
            filas_criticas = FILAS_CRITICAS_POR_PERFIL.get(perfil, FILAS_CRITICAS_POR_PERFIL["consumidor"])
            for n in filas_criticas:
                if not estados.get(n, "").startswith("PASSED"):
                    problemas.append(f"DoD: decision DONE exige la fila {n} en PASSED (tiene `{estados.get(n, 'ausente')}`); {MOTIVO_FILA_CRITICA.get(n, 'es una fila critica')}")
            if veredicto_11 in VEREDICTOS_SIN_REVIEW:
                problemas.append(f"DoD: decision DONE con Item 11 · veredicto: {veredicto_11}; el code review es obligatorio en tipo:hu/hotfix")

    if tipo == "retro":
        secciones = parse_secciones(texto)
        for nombre in ("Desviaciones", "Errores recurrentes", "Patrones descubiertos", "Mejoras sugeridas"):
            if nombre in presentes and len(secciones.get(nombre, [])) > 5:
                problemas.append(f"`### {nombre}` tiene {len(secciones[nombre])} bullets; maximo 5")
        est, real, prec = meta.get("estimado_sp", ""), meta.get("real_sp", ""), meta.get("precision_estimacion", "")
        if est.isdigit() and real.isdigit():
            esperada = "preciso" if int(real) == int(est) else ("subestimado" if int(real) > int(est) else "sobreestimado")
            if prec and prec != esperada:
                problemas.append(f"precision_estimacion deberia ser `{esperada}` (estimado {est}, real {real})")
    return problemas


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida un comentario con marcador de Timonel.")
    parser.add_argument("archivo")
    parser.add_argument("--tipo", choices=sorted(CONTRATOS))
    args = parser.parse_args()
    texto = Path(args.archivo).read_text(encoding="utf-8")
    problemas = validar(texto, args.tipo)
    if problemas:
        print(f"INVALIDO ({len(problemas)} problemas):")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    print(f"OK: comentario `{detectar_tipo(texto)}` valido")


if __name__ == "__main__":
    main()
