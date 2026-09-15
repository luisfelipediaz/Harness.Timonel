# Heurística: Enumerar la clase de entradas o la regla que la genera, nunca un representante por concepto

## Regla general

Cuando cubrís un concepto con casos (tests, tablas de entrada, listas de flags, validaciones de un parser), la pregunta no es *"¿tengo un caso para este concepto?"* sino **"¿tengo la clase entera, o la regla que la genera?"**. Un concepto —"separador de shell", "flag global de git", "estado de un PR"— no es un caso: es un conjunto. Cubrirlo con un representante deja el resto del conjunto sin cubrir **y el test en verde**, que es lo que lo vuelve caro: la cobertura se siente completa.

Hay dos ejes independientes y los dos se olvidan por separado:

| Eje | Pregunta | Se olvida así |
| --- | --- | --- |
| **Valores** | ¿están todas las formas sintácticas / todos los literales de la clase? | se cubre `&&` y no `;`, `-C path` y no `-Cpath` |
| **Cardinalidad** | ¿están 0, 1, N y las mezclas del conjunto? | se cubren todos los valores, pero siempre con un solo elemento |

## Qué hacer

Antes de escribir la lista, escribí la **regla que la genera** y derivá la lista de ella. Si no podés escribir la regla, ese es el hallazgo.

**Mal — la lista de las formas que se nos ocurrieron:**

```python
SEPARADORES = {"&&", "||"}          # ronda 0
SEPARADORES = {"&&", "||", ";"}     # ronda 1, después del review
SEPARADORES = {"&&", "||", ";", "\n"}  # ronda 2...
```

**Bien — la clase completa, nombrada como clase:**

```python
SEPARADORES_DE_SEGMENTO = {"&&", "||", ";", "&", "|", "(", ")"}
# y un normalizador previo que reduce a esta clase todo lo que Bash
# también separa (saltos de línea, agrupaciones), en vez de sumarlo
# a mano cuando alguien lo encuentra.
```

Para los flags, la regla que los genera (*"flag global de git que consume el token siguiente"*) es un conjunto explícito con nombre, más el manejo de la forma pegada derivado de él — no dos listas escritas a mano.

### El eje de cardinalidad (0 / 1 / N / mezclas)

Una tabla puede enumerar perfectamente los **valores** de cada campo y seguir estando incompleta, porque nunca varía **cuántos elementos** tiene el conjunto de entrada. Las cuatro filas que casi siempre faltan:

- **0 elementos**: la lista vacía. ¿Es "todo bien" o "no hay evidencia"? Una entrada degenerada nunca debería caer en el caso verde por default.
- **1 elemento**: el caso feliz, el único que suele estar.
- **N elementos homogéneos**: ¿el predicado es "existe uno que..." o "todos..."? Con un solo elemento las dos formulaciones son indistinguibles.
- **Mezclas**: N elementos con valores distintos, en particular uno válido conviviendo con uno inválido.

**Mal:**

```python
if len(prs) == 1 and prs[0]["state"] == "MERGED":
    return ok()          # un MERGED contra la base equivocada también pasa
```

**Bien:**

```python
mergeados = [p for p in prs if p.get("state") == "MERGED"]
validos = [p for p in mergeados if p.get("baseRefName") == base]
if validos: ...          # se filtra por estado, nunca por cardinalidad
```

## Señales de que lo estás haciendo mal

- El mismo archivo acumula **una ronda de fix por cada forma sintáctica** del mismo concepto, y cada ronda dice "ahora sí".
- Una constante se llama por el ejemplo (`SEPARADORES_AND_OR`) en vez de por la clase (`SEPARADORES_DE_SEGMENTO`).
- La tabla de casos tiene columnas para todos los campos y **ninguna columna para el tamaño** del conjunto de entrada.
- Un `if len(x) == 1` decide la semántica de la respuesta.
- La justificación de que la cobertura está completa es *"cubrimos los casos que se nos ocurrieron"*.

## Caso real

**Los separadores del guard (#102, retro #82).** `scripts/guard_integracion.py` nació en `e5dce30` (#82) y necesitó **cinco fixes sobre el mismo archivo**, uno por ronda de review adversarial: `12014b6` *"no evade separadores pegados, -C, VAR= ni refs/heads"* → `08fc814` *"trata \n, & , | y (...) como separadores"* → `5f546c9` *"ronda 3 del review adversarial"* → `8678d80` *"ronda final"* → `830f111` *"dos falsos positivos de git reset"*. La retro #82 lo dejó escrito así, textual:

> Ronda 0: && sí, ; pegado no. Ronda 1: ; sí, \n no. Ronda 2: -C separado sí, -Cpath pegado no. Ronda 3: la lista de flags globales que se nos ocurrieron, en vez de la regla que los genera.

El contra-hecho: **al terminar cada ronda la tabla de casos de esa ronda estaba completa y verde**. Lo que faltaba nunca era un caso, era el resto de la clase.

**La cardinalidad de los PRs (#112, retro #81).** `scripts/pr_check.py:227-234` lleva el hallazgo escrito en el código:

> Se filtra por estado, nunca por la cardinalidad de `prs`: un MERGED contra la base equivocada no debe pasar (aunque sea el unico elemento) y un MERGED valido no debe fallar por coexistir con un CLOSED (aunque la lista tenga mas de un elemento). Hallazgo #1 del review de #81.

La tabla de 27 casos de #81 enumeró bien los **valores** (`state`, `mergeable`, `conclusion`) y nunca la **cardinalidad** (0/1/N, mezclas `MERGED` + `CLOSED`). Fix: `f61ff26` *"pr_check filtra MERGED por estado y baseRefName, no por cardinalidad"*.

## Cuándo NO aplica

- **Cuando la clase es realmente infinita o desconocida** (todo el espacio de JSON que puede devolver una API externa): ahí enumerar es el error opuesto. Usá `propiedad-antes-que-tabla-en-fronteras.md`: una propiedad generada sobre entradas degeneradas cubre lo que ninguna lista puede.
- **Cuando el conjunto lo fija un tercero y es cerrado por contrato** (los 12 meses, los métodos HTTP): enumerar es correcto y el compilador o un `Record` exhaustivo ya lo sujeta.
- **Cuando el costo de la clase completa es desproporcionado frente al riesgo**: un helper interno con un único llamador no necesita la clase de todas las formas de invocarlo. La heurística pesa donde la entrada viene de afuera o donde el verde es el criterio de aceptación.
- **Cuando el elemento único es una restricción estructural, no un supuesto**: si el dominio garantiza exactamente un elemento, decilo en una aserción explícita en vez de fingir que cubrís N.

## Relación con otras heurísticas

- **`unidad-de-verificacion.md`** responde una pregunta distinta sobre la misma aserción: ésta dice **qué entradas** cubrís (la extensión del conjunto), aquélla dice **sobre qué bloque** afirmás (la granularidad del ámbito). Una aserción puede tener la clase completa de entradas y seguir siendo vacua porque el ámbito sobre el que corre es demasiado grande, y al revés. Invocá ésta cuando te preguntes *"¿falta un caso?"*; invocá aquélla cuando te preguntes *"¿este test se rompería si borro la línea que importa?"*.
- **`propiedad-antes-que-tabla-en-fronteras.md`** es el remedio cuando esta heurística no se puede aplicar: si la clase no es enumerable, la cubre una propiedad generada. Son secuenciales, no alternativas: primero preguntás si podés listar la clase; sólo si no podés, generás la propiedad.
- **`no-tipos-espejo.md`** comparte el mecanismo del `Record<Tipo, …>` exhaustivo: cuando la clase sí es una unión de literales, el compilador puede enumerarla por vos.
- **`perfiles-como-tabla.md`** es esta misma regla aplicada a prosa de agentes: diez menciones sueltas de un perfil son diez representantes; la tabla es la clase.
