---
name: generate-retro
description: Genera la retrospectiva de una historia completada y la publica como comentario timonel:retro en el issue de GitHub (YAML plano + cuatro secciones fijas: desviaciones, errores recurrentes, patrones descubiertos, mejoras sugeridas) con su label retro:*. Usa tras consolidacion y code review. Fase NO bloqueante: si falla, reporta el motivo sin abortar la entrega.
---

Analiza la implementacion completada y publica la retro en el issue. Siempre en espanol.

Las retros se consumen con `scripts/retro_query.py` y `scripts/retro_distill.py` para calibrar estimaciones y detectar patrones; el formato es obligatorio.

## Parametros de entrada

| Parametro | Descripcion |
| --- | --- |
| `issue`, `repo` | Numero y `owner/repo` |
| `archivos_modificados` | Lista de archivos creados/modificados |
| `resultado_verificacion` | Resumen de consolidacion (lint, tests, correcciones) |
| `estimado_sp` | Valor del label `sp:*` |
| `modulo`, `alcance` | Del issue |
| `veredicto_review` | `VEREDICTO` de code-review, o `N/A` |

Si el issue no existe, detente y reporta.

## Pasos

1. `gh issue view <issue> -R <repo> --json title,body,labels,comments`: titulo, Gherkin, contexto, y el comentario `<!-- timonel:review -->` si existe.
2. Usa el review como insumo: WARNING recurrentes → "Errores recurrentes"/"Patrones descubiertos"; CRITICO → "Desviaciones" (hubo remediacion); sugerencias con alcance mas alla de la historia → "Mejoras sugeridas". Destila, no copies filas.
3. Escribe el comentario con el formato `timonel:retro` de `PLUGIN_ROOT/skills/github-issues/references/marcadores.md`:

````markdown
<!-- timonel:retro -->
## Retrospectiva

```yaml
fecha: YYYY-MM-DD
estimado_sp: <estimado_sp>
real_sp: <tu juicio independiente, Fibonacci>
precision_estimacion: sobreestimado | preciso | subestimado
alcance: <alcance>
modulo: <modulo>
```

### Desviaciones
- ...
### Errores recurrentes
- ...
### Patrones descubiertos
- ...
### Mejoras sugeridas
- ...

### Harness engineering
- ¿Surgió un patrón repetitivo? → heurística propuesta o `Ninguno`
- ¿Un proceso manual se ejecutó 2+ veces? → skill/hook propuesto o `Ninguno`
- ¿Faltó contexto que ralentizó? → sección de CLAUDE.md / config propuesta o `Ninguno`
- ¿Un error pudo prevenirse automáticamente? → hook / CI step / test propuesto o `Ninguno`
````

4. Publica con `publicar_marcador <issue> retro <archivo>`; label exclusivo `cambiar_label_exclusivo <issue> retro <precision>`; marca `- [x] Retrospectiva` en `## Tareas`.

## Reglas de contenido

- Maximo 3-5 bullets por seccion; `- Ninguno` si no aplica.
- `real_sp` es tu juicio, no una copia del estimado. `precision_estimacion`: `sobreestimado` si real < estimado, `preciso` si igual, `subestimado` si real > estimado.
- Mejoras sugeridas deben ser accionables: a que skill, heuristica, `CLAUDE.md` o convencion apuntan.
- La seccion **Harness engineering** responde las 4 preguntas siempre (con `Ninguno` si no aplica): es la que convierte cada historia en una mejora del entorno de la siguiente. Si alguna respuesta apunta al plugin Timonel, sugiere `/timonel:draft` en el repo del plugin.

## Reporte de salida

```
RETRO_GENERADA: si | no
RETRO_PUBLICADA: si | no
REAL_SP: <n>
PRECISION: <valor>
MOTIVO: <solo si no>
```
