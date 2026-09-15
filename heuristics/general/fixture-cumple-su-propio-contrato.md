# Heurística: El fixture de un test o de un eval debe cumplir lo que su propio evaluador exige

## Regla general

Un fixture no es decorado: es **la entrada bajo la cual el evaluador tiene sentido**. Si el grader de un eval exige *"detectá que falta el spec"* y el fixture no trae un servicio con spec, el eval no mide lo que dice medir — mide otra cosa, **y pasa igual**. Lo mismo vale para el `arrange` de un test: si el escenario montado no satisface las precondiciones que la aserción presupone, el verde es ruido.

La regla operativa: **corré el evaluado contra el fixture antes de dar el caso por escrito**, y leé la salida preguntándote si el evaluador tuvo materia sobre la cual decidir. Un fixture que hace pasar al grader *por ausencia de contenido* es el modo de fallo, no el éxito.

## Qué hacer

Escribí el fixture como si fuera producción, incluidos los artefactos que el criterio menciona.

**Mal — el fixture insinúa el escenario:**

```ts
// gastos-lista.component.ts (fixture del eval)
cargarGastos() {}      // vacío
// (no hay gastos.service.ts, no hay .spec.ts)
```

El grader pedía hallazgos sobre el servicio y sus tests. Con ese fixture no hay servicio ni tests: cualquier respuesta del evaluado —los encuentre o no— es compatible con el resultado.

**Bien — el fixture contiene los artefactos que el criterio nombra, y el estado declarado es verdadero:**

```ts
// gastos.service.ts
listarDelMes(): Observable<Gasto[]> { … }
// gastos-lista.component.spec.ts  → existe y pasa
```

```
TESTS_RESULTADO: PASSED (el spec de abajo corre y pasa)
```

Checklist antes de cerrar un fixture:

1. Listá los sustantivos del criterio/grader (servicio, spec, endpoint, permiso, tabla).
2. Verificá que **cada uno existe** en el fixture, con contenido no trivial.
3. Ejecutá el evaluado sobre el fixture y leé la salida: ¿cada hallazgo esperado tiene de dónde salir?
4. Mutá el fixture quitando el artefacto que el criterio busca: el evaluador tiene que cambiar de resultado. Si no cambia, el caso no mide.

## Señales de que lo estás haciendo mal

- El fixture tiene cuerpos de función vacíos, `TODO`, o archivos "que se sobreentienden".
- El grader menciona un archivo que el fixture no incluye.
- El caso declara un estado (`TESTS_RESULTADO: PASSED`) que nadie ejecutó.
- El eval pasa desde el primer intento y no sabés decir qué parte del fixture lo hizo pasar.
- Tu única evidencia de que el caso está bien es que la suite de `evals/` está verde: **ningún test unitario sobre `evals/` puede detectar esto**, porque el defecto está en la semántica del fixture, no en su forma.

## Caso real

**El fixture de `code-review` que no cumplía su propio Gherkin (#62, retro #32(5)).** `evals/code-review/tres-violaciones-warning/prompt.md`. La retro #32 lo registró así, textual:

> el fixture del caso code-review no cumplía su propio Gherkin (`cargarGastos()` vacío, sin spec)

y fue el **CRÍTICO de la primera ronda de review**. El fix `2936063` (*"el fixture de code-review cumple su Gherkin (servicio + spec), sin weight y en español neutro (#32)"*) agregó `gastos.service.ts` con `GastosService.listarDelMes()` y el spec, y dejó declarado en el prompt `TESTS_RESULTADO: PASSED (el spec de abajo corre y pasa)` — la línea 61 del fixture actual.

El contra-hecho, y la parte que convierte el caso en heurística, está en la misma retro:

> **Verificar el fixture ejecutando el evaluado**: un eval cuyo fixture no cumple lo que su grader exige mide otra cosa. El CRITICO lo encontró el reviewer lanzando el skill `code-review` real contra el fixture, no leyéndolo; ningún test unitario de `evals/` (convención de carpeta, `type` de graders, 3 violaciones sembradas) puede detectarlo.

Es decir: **no existe un guardrail automático posible** para este defecto. Sólo ejecutar el evaluado.

## Cuándo NO aplica

- **Cuando el fixture es deliberadamente degenerado porque *eso* es lo que se prueba**: un caso cuyo criterio es "detectá que falta el spec" debe tener el fixture sin spec. La regla es "cumplir el contrato del evaluador", no "estar completo".
- **En stubs de compilación de la fase roja de TDD**: ahí el cuerpo vacío es el punto, y el contrato todavía no existe.
- **Cuando montar el artefacto real cuesta más que el riesgo cubierto** (levantar una base de datos para verificar un parseo de strings): usá un doble, pero **declaralo** en el caso en vez de dejar que se lea como el artefacto real.
- **Cuando el estado declarado se genera automáticamente** (un `TESTS_RESULTADO` que sale de correr la suite): ahí la afirmación ya está verificada por construcción.

## Relación con otras heurísticas

- **`comentarios-verificables.md`** es la misma exigencia sobre otro artefacto: un comentario afirma algo sobre el código; un fixture afirma ser un caso del contrato. En los dos, la afirmación no se ejecuta y por eso puede ser falsa indefinidamente. Invocá aquélla cuando estés escribiendo *prosa dentro del código*; ésta cuando estés escribiendo *la entrada de un evaluador*.
- **`propiedad-antes-que-tabla-en-fronteras.md`** cubre el caso opuesto del mismo eje: allá el problema es que el fixture está **demasiado bien formado** (siempre completo, siempre feliz); acá que está **demasiado mal formado** para que el evaluador tenga trabajo. Las dos se responden con la misma pregunta: *"¿qué tendría que cambiar en la entrada para que el resultado cambie?"*.
- **`unidad-de-verificacion.md`** aporta la mutación de control que cierra el paso 4 de la checklist: un fixture, como una aserción, vale lo que vale la mutación que lo pondría en rojo.
