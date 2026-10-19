# Heurística: Un test no está terminado hasta que lo viste fallar por la razón correcta

## Regla general

Un test que pasa no demuestra nada por sí solo: demuestra que **alguna** condición se cumple, no que sea la que querías probar. Antes de dar por bueno un test nuevo, **muta el sistema bajo prueba (o el arrange) para romper exactamente lo que el test dice verificar, y confirma que falla.** Si sigue pasando, la aserción es vacua: está midiendo otra cosa.

La trampa más común es una **aserción sobre una propiedad con más de una causa posible**: un botón deshabilitado, una ausencia en el DOM, un `undefined`, una lista vacía, una subcadena que no está. Si la propiedad puede cumplirse por tres razones y tu arrange deja dos activas, el test pasa aunque la que pruebas no funcione.

## Qué hacer

1. **Enumera las causas.** Antes de escribir la aserción, pregúntate qué otras cosas hacen cierta la misma propiedad. Lee la función que la decide (el guard, el `@if`, el regex).
2. **Neutraliza en el arrange todas las causas salvo la que pruebas.** Solo entonces el resultado significa "esta causa".
3. **Muta y mira.** Cambia el sistema (o el arrange) para que la causa bajo prueba desaparezca y corre el test: **debe fallar**. Si no falló, vuelve al paso 1.
4. **Deja evidencia.** En el commit o el review, una línea: "verificado por mutación: con `<cambio>` el test falla (N fallos)".

### Cuando el texto es prosa de un agente

La prosa que escribe un agente no es un string estable: el agente envuelve los literales en markup. Dos reglas:

- **Compara con regex tolerante al markup, no con subcadenas literales.** Los literales aparecen entre backticks (``exit 2 `no sé` ``) o en negritas (`**PASSED**`), y una subcadena como `"exit 2 PASSED"` no está en ``exit 2 `PASSED` `` ni en el mismo texto con negritas. Una aserción de **ausencia** con subcadena es vacua por construcción: nunca encuentra lo que busca, así que nunca falla. Usa `assertNotRegex(frase, r"exit 2 `?PASSED")`, con el markup opcional en el patrón.
- **La mutación sustituye el literal protegido; no basta con borrar un encabezado.** Borrar el encabezado de la sección deja el párrafo vacío y rompe todos los tests de la clase por una causa que no es la probada. Cambia el literal por su contrario (``exit 2 `no sé` `` por ``exit 2 `PASSED` ``) y confirma que falla la aserción que lo protege, y solo esa.

**Mal — una subcadena sin markup en una aserción de ausencia:**

```python
self.assertNotIn("exit 2 PASSED", frase)   # el agente escribe exit 2 `PASSED`: no contiene la subcadena
```

**Bien — regex tolerante al markup, vista fallar con la sustitución:**

```python
self.assertNotRegex(frase, r"exit 2 `?PASSED")
# Verificado por mutación: ``exit 2 `no sé` `` -> ``exit 2 `PASSED` `` pone el test en rojo.
```

### Un snapshot solo cubre la etapa que ejercita

La misma trampa, en el eje del pipeline. Un test que congela una salida la toma donde el test la produce. Si después hay etapas que la transforman (middleware, serializadores del host, paquetes que se autorregistran), el snapshot sigue en verde aunque la salida real cambie. Enumera las etapas posteriores, cubre cada una con su propio test y muta cada una.

## Señales de que lo estás haciendo mal

- El test pasa **antes** de implementar la funcionalidad que dice probar.
- Aserciones de ausencia (`assertNotIn`, `toBeNull()`, `length === 0`) sin que el arrange haya construido primero el estado "positivo".
- Una aserción sobre texto de un agente con una subcadena que incluye literales que el agente suele escribir entre backticks o en negritas.
- La mutación que informas solo borra un encabezado o una línea entera, y rompe varios tests a la vez.
- Nadie puede decir en una frase *qué cambio en producción haría fallar este test*.

## Caso real

**#356, commit `4ba26da`** (*"fix(plugin): #356 asercion de exit 2 con regex, no vacua (review)"*). `tests/test_consistencia.py` protegía que el párrafo de `exit 2` del hotfix no mapeara ese código a `PASSED`. El diff cambió `self.assertNotIn("exit 2 PASSED", frase, ...)` por `self.assertNotRegex(frase, r"exit 2 `?PASSED", ...)`. El hallazgo del code review decía:

> `assertNotIn("exit 2 PASSED", frase)` es vacua: el agente escribe los literales entre backticks (``exit 2 `no sé` ``), asi que un mapeo erroneo ``exit 2 `PASSED` `` tampoco contiene esa subcadena y el test seguiria en verde. La mutacion informada solo borra el encabezado (rompe ambos tests por `_parrafo` vacio); ninguna mutacion ejercita la asercion de `exit 2`.

Es la tercera vez que una retro invoca esta heurística (#321, #356, #362): la suite estaba en verde las tres veces y fue el review, no los tests, quien destapó la aserción vacua.

## Cuándo NO aplica

- **Código ejecutable con tests de comportamiento**: si puedes invocar la función y afirmar sobre su salida, hazlo; la mutación a mano es para aserciones indirectas.
- **Literales que el código controla por completo** (una versión en `plugin.json`, una clave de un `dict`): no hay markup que los envuelva y una subcadena basta.
- **Cuando el costo de la mutación supera el riesgo**: un test trivial sobre una constante no necesita una mutación documentada; sí la necesita cualquier aserción de ausencia o sobre una propiedad con varias causas.

## Relación con otras heurísticas

- **`unidad-de-verificacion.md`** ataca la misma falla, una verificación que pasa sin verificar, pero en el eje del **ámbito**: sobre qué bloque (archivo, sección, párrafo) se afirma. Invócala cuando dudes de si la aserción mira el bloque correcto; invoca esta cuando dudes de la **forma del literal** (¿aparece así en la prosa real?) y de si tu mutación ejercita la aserción o solo rompe el ámbito.
- **`enumerar-la-clase-no-el-representante.md`** pregunta qué entradas entran; esta pregunta si la aserción de cada una puede fallar de verdad.
