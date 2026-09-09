# Plantilla — issue `tipo:epica`

**Titulo**: nombre de la epica en infinitivo o sustantivo claro. Ej: `Gestionar presupuesto mensual y alertas`.

**Labels**: `tipo:epica`, `mod:<modulo>` (recomendado).

**Padre**: sub-issue del SDD si existe; si no, raiz.

**Hijos**: cada HU es sub-issue de la epica. No mantener listas manuales de HUs en el body: GitHub muestra los sub-issues y su progreso.

## Body

````markdown
## Objetivo

[Que problema de negocio resuelve la epica y para quien. 2-4 lineas.]

## Alcance

- Incluye: ...
- No incluye: ...

## Usuarios

- [rol]: [necesidad]

## Notas técnicas

- Modulo destino, permisos, integraciones, decisiones que aplican a todas las HU.

## Dependencias

Depende de #N
(o `Ninguna`)
````

## Reglas

- Una epica cabe en 2-4 sprints. Si tiene mas de ~10 HU, dividirla.
- El refiner publica sus reportes de refinamiento como comentario `<!-- timonel:refinamiento -->` en la epica.
