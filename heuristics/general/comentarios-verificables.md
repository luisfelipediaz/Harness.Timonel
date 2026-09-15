# Heurística: Un comentario que afirma un hecho verificable, o se verifica al escribirlo, o no se escribe

## Regla general

Los comentarios se dividen en dos especies y sólo una es peligrosa:

| Especie | Ejemplo | Riesgo |
| --- | --- | --- |
| **Intención / decisión** | *"cae en desconocido a propósito: sin identificador no hay confianza"* | envejece, pero no puede ser falsa hoy |
| **Hecho verificable** | *"otros módulos importan esta constante"*, *"el test X ya lo cubre"*, *"esto lo exige la API"* | **puede ser falsa en el momento de escribirla** |

Un comentario de la segunda especie es una aserción sin test. Nadie la ejecuta, nadie la revisa, y **le presta credibilidad al código que acompaña**: un lector que quiera borrar la constante lee "otros módulos la importan" y no la borra. Si la afirmación era falsa, el comentario acaba de proteger código muerto.

La regla: antes de escribir una afirmación verificable, **verificala** —`grep`, abrí el archivo, corré el test que nombrás— y si no la vas a verificar, no la escribas. "Comentario borrado" siempre es una opción válida.

## Qué hacer

**Mal — retrocompatibilidad afirmada, no comprobada:**

```python
# Retrocompat: otros modulos importan TAREAS directamente
# (test_consistencia.py::ChecklistsPorTipoTests ya cubre...)
TAREAS = CHECKLISTS["hu"]
```

Dos afirmaciones verificables en dos líneas: que existen módulos que importan la constante, y que un test concreto lo cubre. Un `grep` de treinta segundos habría mostrado que la primera es falsa.

**Bien — verificar y actuar sobre el resultado:**

```bash
grep -rn "import TAREAS\|from .* import .*TAREAS" scripts/ tests/
```

Sin consumidores: se borran **el comentario y la constante**. Con consumidores: el comentario sobra igual, porque el `grep` lo demuestra mejor que la prosa; lo que corresponde es el test que fija el contrato.

Formulaciones que convierten una afirmación falsable en una decisión honesta:

- *"otros módulos importan X"* → borrar X, o dejar el test que prueba que X sigue exportada.
- *"el test Y ya cubre esto"* → nombrar el test **y** que el test exista; si el motivo de la línea es sólo ese test, ponelo en el test.
- *"la API siempre manda este campo"* → un `.get()` con default explícito dice lo mismo y no puede mentir.

## Señales de que lo estás haciendo mal

- El comentario contiene *"otros"*, *"varios"*, *"ya está cubierto"*, *"por retrocompatibilidad"*, *"lo exige"*, sin nombrar nada comprobable.
- El comentario justifica **la existencia** de un símbolo (no su forma): es exactamente el que impide borrarlo.
- Cita un test por nombre y no verificaste que ese test exista y cubra eso.
- Describe el comportamiento de un tercero (una API, una plataforma, otro repo) que no consultaste hoy.
- La única razón por la que el código de abajo sigue vivo es lo que dice el comentario.

## Caso real

**El comentario de `TAREAS` con consumidores inexistentes (#108, retro #83(3)).** `scripts/estado_historia.py`. El commit `756f2ac` (*"aislar flechodiezx-hotfix en worktree con PR obligatorio (#83)"*) introdujo:

```python
# Retrocompat: otros modulos importan TAREAS directamente
# (test_consistencia.py::ChecklistsPorTipoTests ya cubre...)
TAREAS = CHECKLISTS["hu"]
```

Era **falso**: ningún consumidor real existía. El `TAREAS` de `scripts/migrate_backlog.py` es una constante propia, sin relación con ésta. El hallazgo salió del code review del mismo issue y el fix `f62ee1a` (#83) eliminó el comentario **y la constante muerta** que el comentario estaba sosteniendo.

La retro #83 lo cerró con la formulación que da nombre a esta heurística, textual:

> un comentario que afirma un hecho verificable, o se verifica al escribirlo, o no se escribe.

El contra-hecho: antes del fix, el código tenía una constante sin usar **protegida por una razón inventada**, y ninguna herramienta la marcaba — un linter de símbolos sin uso la habría visto, pero el comentario era la respuesta preparada para quien preguntara.

## Cuándo NO aplica

- **A los comentarios de intención y decisión**: *"esto cae en desconocido a propósito"*, *"no convertir este switch: pierde el narrowing"*. No afirman un hecho externo; son la razón, y son justamente los que hay que escribir más.
- **Cuando la afirmación se verifica sola**: un comentario que cita un identificador que el compilador o el import resolverían rompe la build si deja de ser cierto.
- **Cuando el hecho es la entrada y no el código**: documentar la forma de un payload ajeno que observaste es legítimo; lo que exige verificación es afirmar que **tu** repo depende de algo.
- **En documentación de proceso** (ADRs, CHANGELOG), donde la afirmación está fechada y se lee como histórica, no como estado actual.

## Relación con otras heurísticas

- **`fixture-cumple-su-propio-contrato.md`** es la misma regla en `evals/` y `tests/`: en las dos, una afirmación que nadie ejecuta se desalinea del mundo sin dejar rastro. Invocá ésta cuando escribas prosa **dentro** del código; aquélla cuando escribas la **entrada** de un evaluador.
- **`unidad-de-verificacion.md`** describe el caso extremo de esta heurística: cuando el comentario vive dentro del archivo que una aserción inspecciona, no sólo puede ser falso — puede **satisfacer el test por sí mismo** y vaciar la verificación.
- **`sensor-declara-su-evidencia.md`** es el remedio estructural para la familia *"esto ya está cubierto"*: si un sensor publica dónde deja su evidencia y con qué ancla, la afirmación deja de necesitar un comentario y se puede consultar.
