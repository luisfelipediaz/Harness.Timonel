# Esquema de labels

Provisionados por `scripts/setup-github-labels.sh` (idempotente). Los ejes `tipo:`, `estado:`, `alcance:`, `moscow:`, `sp:`, `prioridad:`, `review:` y `retro:` son **exclusivos**: un issue lleva a lo sumo un valor de cada eje.

| Label | Color | Descripción |
| --- | --- | --- |
| `tipo:sdd` | `5319E7` | Software Design Document; padre de épicas |
| `tipo:epica` | `3E4B9E` | Épica; padre de historias |
| `tipo:hu` | `0052CC` | Historia de usuario implementable por flechodiezx |
| `tipo:hotfix` | `1D76DB` | Cambio ≤2 SP sin ceremonia completa |
| `estado:borrador` | `EDEDED` | Capturado, no cumple DoR |
| `estado:listo` | `0E8A16` | Cumple DoR; puede implementarse |
| `estado:en-progreso` | `FBCA04` | En implementación |
| `estado:en-revision` | `1D76DB` | PR abierto, pendiente de merge humano |
| `alcance:backend` | `C2E0C6` | Solo API |
| `alcance:frontend` | `BFD4F2` | Solo cliente |
| `alcance:full-stack` | `D4C5F9` | API + cliente |
| `moscow:must` | `B60205` | Must Have |
| `moscow:should` | `D93F0B` | Should Have |
| `moscow:could` | `FBCA04` | Could Have |
| `moscow:wont` | `CCCCCC` | Won't Have (por ahora) |
| `sp:1` … `sp:21` | `F9D0C4` | Story points Fibonacci (1, 2, 3, 5, 8, 13, 21) |
| `prioridad:alta` | `E11D21` | Prioridad de negocio alta |
| `prioridad:media` | `EB6420` | Media |
| `prioridad:baja` | `FEF2C0` | Baja |
| `mod:<modulo>` | `006B75` | Módulo destino (uno por `modulos[]` del config) |
| `review:aprobado` | `0E8A16` | Code review sin hallazgos |
| `review:observaciones` | `FBCA04` | Aprobado con warnings |
| `review:requiere-cambios` | `B60205` | Hallazgos críticos; bloquea DoD |
| `retro:preciso` | `C5DEF5` | SP real = estimado |
| `retro:subestimado` | `F9D0C4` | SP real > estimado |
| `retro:sobreestimado` | `D4E7D4` | SP real < estimado |
| `bloqueado` | `000000` | Alguna dependencia abierta |
| `bug` | `D73A4A` | Corrige un defecto (ortogonal a `tipo:`) |
| `duplicada` | `CFD3D7` | Duplicada de otra HU (cerrada not_planned) |
| `obsoleta` | `CFD3D7` | Reemplazada o ya no aplica (cerrada not_planned) |
| `insights` | `5319E7` | Issue de insights destilados (retro/review) |
| `harness-audit` | `0E8A16` | Auditoría de madurez del harness (una por corrida) |
| `draft-intencional` | `CFD3D7` | PR en draft a propósito: PoC o rama que no se mergea |

Los 9 labels default de GitHub (`enhancement`, `documentation`, `good first issue`, …) se eliminan en repos nuevos dedicados a backlog; en repos con historia se conservan.
