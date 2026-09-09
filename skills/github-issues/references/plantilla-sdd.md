# Plantilla — issue `tipo:sdd` (Software Design Document)

**Titulo**: `SDD — [feature o modificacion]`. Ej: `SDD — Marcación de turnos con captura de ubicación`.

**Labels**: `tipo:sdd`, `mod:<modulo>` (recomendado), `estado:borrador|listo`.

**Padre**: ninguno. **Hijos**: epicas (`tipo:epica`) derivadas.

Secciones tomadas de los SDD reales del Portal y del POC. Las numeradas son fijas; el contenido escala con la complejidad.

## Body

````markdown
## 1. Resumen ejecutivo

[3-6 lineas: que se construye, por que ahora, resultado esperado.]

**Stack detectado:** [de `.claude/timonel.config.json` y del codigo real]
**Estado:** Borrador | Aprobado | Implementado

## 2. Contexto y motivación

[Evidencia del codigo actual, pain points, restricciones de plataforma. Citar archivos reales.]

## 3. Alcance

### 3.1 In scope
### 3.2 Fuera de alcance
### 3.3 Módulos / archivos afectados

## 4. Requisitos funcionales

### RF-01 — [titulo]
[Descripcion + criterio verificable]

## 5. Requisitos no funcionales

[Rendimiento, offline, accesibilidad, seguridad, observabilidad.]

## 6. Decisiones de diseño

| # | Decisión | Alternativas consideradas | Razón |
| - | -------- | ------------------------- | ----- |
| D-1 | ... | ... | ... |

## 7. Contrato de datos y API

### 7.1 Tipos / interfaces (en `modelos.path`, sin prefijo `I`)
### 7.2 Endpoints

## 8. Diseño de componentes y estado

[Estructura de carpetas, store, facade, servicios, flujos. Diagramas en ```mermaid.]

## 9. Estrategia de pruebas

## 10. Seguridad y permisos

## 11. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| ------ | ------- | ---------- |

## 12. Épicas propuestas

- [ ] [Nombre de epica 1] — [1 linea]
- [ ] [Nombre de epica 2] — [1 linea]

(Al crearlas como sub-issues, reemplazar cada linea por `#N`.)

## 13. Dudas abiertas

- DA-1: [pregunta] — **Resuelta 2026-MM-DD:** [respuesta] (o `Pendiente`)
````

## Tamano

El body de un issue admite 65.536 caracteres. Si el SDD lo supera, dejar en el body las secciones 1–6 y 12–13, y publicar 7–11 como comentarios que empiecen con `<!-- timonel:sdd:seccion=7 -->` (uno por seccion), agregando en el body un indice `## Secciones en comentarios` con links a cada comentario.

## Versionado

Cada cambio relevante agrega una linea al inicio del body bajo `**Historial:**` con fecha y resumen (`- 2026-07-21 v1.2: resuelta DA-1, agrega RF-09`). No se crean issues nuevos por version.
