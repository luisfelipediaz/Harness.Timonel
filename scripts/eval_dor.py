#!/usr/bin/env python3
"""DoR sobre la HU devuelta por el eval del planner (issue #32, gap 12 de la auditoria #11).

`claude plugin eval` corre el prompt de `evals/user-story-planner/hu-cumple-dor/` y guarda la
respuesta del agente. Este sensor reutiliza `dor_check.check()` sobre esa respuesta en texto
libre (no un issue de GitHub): extrae la HU de su bloque ```markdown``` (hasta el ultimo ```
del texto, para tolerar los fences ```gherkin``` anidados dentro del body) y sus labels de la
linea `Labels: ...` que pide el prompt.

Uso:
    python3 eval_dor.py <archivo> [--title "..."] [--para listo|implementar]
    python3 eval_dor.py -           # lee la respuesta de stdin

Sale 0 e imprime `DoR cumplido` si no hay faltantes; 1 con la lista de faltantes si los hay.
Sin `gh`: no golpea la red, solo texto.
"""

from __future__ import annotations

import argparse
import re
import sys

import dor_check

BLOQUE_MARKDOWN = re.compile(r"```markdown\n(.*)```", re.DOTALL)
LABELS_LINEA = re.compile(r"^Labels:\s*(.+)$", re.MULTILINE)
TITULO_ENCABEZADO = re.compile(r"^#\s+(.+)$", re.MULTILINE)
TITULO_CAMPO = re.compile(r"^\*\*T[ií]tulo\*\*:?\s*(.+)$|^T[ií]tulo:\s*(.+)$", re.MULTILINE)


def _titulo(texto: str) -> str:
    m = TITULO_ENCABEZADO.search(texto)
    if m:
        return m.group(1).strip()
    m = TITULO_CAMPO.search(texto)
    if m:
        return (m.group(1) or m.group(2) or "").strip()
    return ""


def extraer_hu(texto: str, title: str = "") -> dict:
    """Extrae `{title, body, label_names}` de la respuesta en texto libre del agente."""
    m = BLOQUE_MARKDOWN.search(texto)
    body = m.group(1) if m else texto
    m = LABELS_LINEA.search(texto)
    label_names = [t.strip() for t in m.group(1).split(",")] if m else []
    return {"title": title or _titulo(texto), "body": body, "label_names": label_names}


def evaluar(texto: str, para: str = "listo") -> list[str]:
    """Faltantes del DoR (TIM-ADR-0003) para la HU contenida en `texto`."""
    return dor_check.check(extraer_hu(texto), para)


def main() -> None:
    parser = argparse.ArgumentParser(description="DoR sobre la respuesta de un eval de user-story-planner.")
    parser.add_argument("archivo", help="Ruta al archivo con la respuesta del agente, o '-' para stdin.")
    parser.add_argument("--title", default="", help="Titulo de la HU si no viene como `# ...` en el texto.")
    parser.add_argument("--para", choices=["listo", "implementar"], default="listo")
    args = parser.parse_args()

    texto = sys.stdin.read() if args.archivo == "-" else open(args.archivo, encoding="utf-8").read()
    faltantes = dor_check.check(extraer_hu(texto, args.title), args.para)
    if faltantes:
        print(f"DoR NO cumplido ({len(faltantes)} faltantes):")
        for f in faltantes:
            print(f"  - {f}")
        sys.exit(1)
    print("DoR cumplido")


if __name__ == "__main__":
    main()
