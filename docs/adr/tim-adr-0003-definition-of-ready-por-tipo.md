# TIM-ADR-0003: Definition of Ready por tipo de issue

**Fecha**: 2026-09-09
**Estado**: Aceptado

## Contexto

`story-executor` consume el body del issue como única especificación. Si llega sin Ficha Técnica o sin Gherkin, los sub-agentes inventan endpoints y el code review no puede evaluar criterios. El harness original ya exigía la ficha "obligatoria", pero nadie la validaba antes de implementar.

## Decisión

| Sección / label | `hu` | `hotfix` | `epica` | `sdd` |
| --- | --- | --- | --- | --- |
| Título `[verbo infinitivo] [qué]` | Obligatorio | Obligatorio | Obligatorio | Obligatorio |
| `tipo:*` | Obligatorio | Obligatorio | Obligatorio | Obligatorio |
| `estado:listo` para implementar | Obligatorio | Obligatorio | No aplica | No aplica |
| `alcance:*` | Obligatorio | Obligatorio | No aplica | No aplica |
| `sp:*` | Obligatorio (≤13) | Obligatorio (≤2; 3 con confirmación) | No aplica | No aplica |
| `mod:*` | Obligatorio | Obligatorio | Recomendado | No aplica |
| `moscow:*`, `prioridad:*` | Obligatorio | Recomendado | No aplica | No aplica |
| `## Historia` | **Crítico** | Recomendado | No aplica | No aplica |
| `## Criterios de aceptación` (gherkin) | **Crítico** | **Crítico** | No aplica | No aplica |
| `## Ficha técnica` (tabla) | **Crítico** | **Crítico** | No aplica | No aplica |
| `## Endpoints`, `## Modelos compartidos` | Obligatorio (o `Ninguno`) | Debe ser `Ninguno` | No aplica | No aplica |
| `## Dependencias` | Obligatorio (o `Ninguna`) | Obligatorio | Recomendado | No aplica |
| `## Tareas` | Obligatorio (checklist) | Obligatorio | No aplica | No aplica |
| Padre (sub-issue de) | Épica | Opcional | SDD u ninguno | Ninguno |
| `## Objetivo`, `## Alcance` | No aplica | No aplica | Obligatorio | Obligatorio |
| `## Requisitos funcionales`, `## Contrato de datos y API` | No aplica | No aplica | No aplica | **Crítico** |

**Crítico** = input directo de un agente; su ausencia degrada el resultado. **Obligatorio** = requerido para `estado:listo`.

Validación programática en `/timonel:implement` y `/timonel:hotfix`: labels `estado:listo`, `tipo:`, `alcance:`, `sp:`, `mod:`; body contiene `## Criterios de aceptaci`, `## Ficha t` y `## Tareas`. Si falla, lista todo lo que falta y sugiere `/timonel:refine N`.

## Consecuencias

- `estado:borrador` es el estado por defecto de creación; pasar a `listo` exige el checklist.
- El refiner tiene un criterio objetivo para "Ficha incompleta".
