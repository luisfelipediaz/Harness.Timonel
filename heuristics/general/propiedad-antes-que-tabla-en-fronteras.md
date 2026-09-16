# Heurística: En toda frontera de traducción, escribí primero la propiedad sobre entradas degeneradas y después la tabla de casos

## Regla general

Una **frontera de traducción** es cualquier función que convierte datos de un sistema ajeno (JSON de una API, salida de un CLI, respuesta de `gh`, payload de un webhook) en una decisión interna: un veredicto, un enum, un booleano. En esas fronteras la tabla de casos es necesaria pero **estructuralmente insuficiente**: la tabla la escribe quien ya tiene un modelo mental del dato, y ese modelo es justo lo que la entrada real puede violar.

La regla: antes de la tabla, escribí **una propiedad generada programáticamente sobre entradas degeneradas** —campos ausentes, vacíos, `null`, del tipo equivocado, con el identificador faltante— y hacela valer para todas. La propiedad más útil casi siempre es la misma:

> **Una entrada degenerada nunca cae en el resultado favorable.**

## Qué hacer

**Mal — la tabla de casos, escrita desde el modelo mental:**

```python
def analizar(check: dict) -> str:
    if check["conclusion"] == "SUCCESS":
        return "verde"
    return _MAPA.get(check["conclusion"], "desconocido")
```

La tabla cubre `SUCCESS`, `FAILURE`, `NEUTRAL`, `SKIPPED`… todos los valores del campo que el modelo mental considera relevante. Un elemento **sin el campo que lo identifica** entra igual y sale verde.

**Bien — la propiedad primero, y la tabla después dentro de lo que la propiedad deja pasar:**

```python
def analizar(check: dict) -> tuple[str, str, str, str]:
    nombre = check.get("name")
    if not nombre:
        # sin identificador no hay confianza posible: nunca "verde"
        return "desconocido", "?", check.get("conclusion") or "", typename
    ...
```

Y en los tests, la propiedad se **genera**, no se lista:

```python
for campo in CAMPOS_DEL_PAYLOAD:
    degenerada = {**entrada_feliz}
    del degenerada[campo]
    self.assertNotEqual("PASSED", veredicto(degenerada), f"falta `{campo}` y aun asi paso")
```

Reglas de acompañamiento que salen del mismo caso:

- **El motivo sí distingue los casos degenerados entre sí.** "Sin identificador" no es lo mismo que "estado no reconocido"; decirle *"estado desconocido"* a un `SUCCESS` es falso aunque el veredicto sea correcto.
- **Un valor fuera del mapa es una entrada degenerada**, no un default silencioso. `.get(valor, "verde")` es el bug; `.get(valor, "desconocido")` es la propiedad.

## Señales de que lo estás haciendo mal

- El parser accede con `dato["campo"]` o asume que el campo existe porque *"la API siempre lo manda"*.
- Los tests de la frontera son todos diccionarios escritos a mano, completos y bien formados.
- El default de un lookup sobre un valor externo es el resultado favorable.
- La revisión del código la hicieron varias personas y ninguna lo vio: **leyeron la misma tabla y heredaron su marco**.
- El resultado de esa función alimenta un gate (un DoD, un merge, un deploy): un falso verde ahí no se nota nunca.

## Caso real

**`CheckRun` sin `name` devolviendo PASSED (#116, retro #81(6)).** `scripts/pr_check.py:121-149`, función `_analizar_check`. El docstring actual lo lleva escrito:

> Un check sin su campo identificador (`context` en StatusContext, `name` en CheckRun) no es confiable aunque su conclusion sea verde: no hay forma de nombrarlo por su identidad, asi que el eje cae en "desconocido" (nunca "verde") -- la misma logica que ya aplica a un valor de conclusion fuera del mapa (hallazgo #3 del review de #81: una entrada degenerada nunca es PASSED).

El contra-hecho: un `CheckRun` **sin `name`** con `conclusion: SUCCESS` devolvía `PASSED` — un **falso verde en el ítem crítico del DoD**. Fix: `ade4254` *"check sin identificador nunca es verde (#81)"*.

Lo que hace al caso instructivo no es el bug sino quién lo encontró. La retro #81, textual:

> El sensor pasó por tres pasadas adversariales independientes (code review, team lead, orquestador) sobre una tabla de 27 casos escrita justamente para "enumerar la clase y no el representante", y aun así el bug más grave —un `CheckRun` sin `name` con `conclusion: SUCCESS` devolviendo `PASSED`, un **falso verde en el ítem crítico del DoD**— lo destapó una invariante generada programáticamente sobre entradas degeneradas. […] Los tres lectores no eran tres muestreos independientes: leyeron la misma tabla y heredaron su marco.

Tres revisiones humanas independientes sobre una tabla de 27 casos no lo vieron; una propiedad generada sí. Esa es la razón de que la propiedad vaya **antes** y no después.

## Cuándo NO aplica

- **Dentro del sistema, entre funciones propias donde el tipo ya es la garantía**: si la entrada viene de un dataclass que construiste vos, degenerarla prueba el constructor, no la frontera. La heurística pesa donde el dato viene de afuera.
- **Cuando la degeneración ya es imposible por contrato verificado** (un esquema validado en el borde, con su propio test): entonces la frontera está un nivel más arriba y es ahí donde va la propiedad, no repetida en cada consumidor.
- **Cuando la propiedad no se puede formular sin reescribir la implementación**: si "entrada degenerada" sólo se define ejecutando la misma lógica que probás, la propiedad es una tautología. Volvé a la tabla y documentá el hueco.
- **Cuando el resultado no es un gate**: en un reporte informativo el costo de un falso verde es bajo y la tabla alcanza. En un DoD, un merge o un deploy, no.

## Relación con otras heurísticas

- **`enumerar-la-clase-no-el-representante.md`** es la heurística hermana y se invocan en orden: primero preguntás si la clase de entradas es enumerable; si lo es, la enumerás; **sólo cuando no lo es** —y el JSON de un tercero nunca lo es— generás la propiedad. Enumerar donde debías generar deja huecos; generar donde podías enumerar produce tests que no dicen qué caso falló.
- **`unidad-de-verificacion.md`** atiende el mismo síntoma ("pasa sin verificar") desde el ámbito de la aserción, no desde la forma del dato. Si tu test es sobre texto del repo, es aquélla; si es sobre datos que cruzan una frontera, es ésta.
- **`keyword-de-plataforma-no-se-traduce.md`** es la misma frontera recorrida al revés: aquélla habla del vocabulario que **sale** hacia el sistema externo, ésta de los datos que **entran** desde él. Las dos fallan igual de silenciosas porque en las dos el sistema externo no protesta.
