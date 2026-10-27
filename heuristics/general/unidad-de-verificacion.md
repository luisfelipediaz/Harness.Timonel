# Heurística: Una aserción vale lo que vale su ámbito — el ámbito es el bloque más chico que todavía contiene la instrucción completa

## Regla general

Toda aserción sobre texto o estructura (un test de consistencia, un lint, un grader, una búsqueda de literal) corre sobre un **ámbito**: el archivo, la sección, el párrafo, la línea. El ámbito no es un detalle de implementación: **es la mitad de la aserción**. `assertIn(literal, ámbito)` afirma exactamente *"el literal sobrevive en algún punto del ámbito"*, y cuanto más grande el ámbito, menos dice.

La unidad correcta es **el bloque más chico que todavía contiene la instrucción completa** que querés proteger. Ni más grande (la aserción se vuelve vacua) ni más chico (se vuelve frágil y falla por formato).

## Qué hacer

Nombrá el ámbito explícitamente y justificalo, en vez de heredar el que venía por default (el archivo entero).

**Mal — la sección `##` como ámbito:**

```python
seccion = next(s for s in self._secciones(texto) if "Fase 3" in s)
self.assertIn("<literal de aislamiento>", seccion)
```

La sección agrupa tres lanzamientos distintos. Borrar el literal de **uno** de ellos deja el test en verde, porque sobrevive en los otros dos.

**Bien — el párrafo, con la propiedad formulada como existencial por párrafo:**

```python
parrafos = [p for p in self._parrafos(texto) if skill in p]
aislados = [p for p in parrafos if "<literal de aislamiento>" in p]
self.assertTrue(aislados, f"ningun parrafo que menciona `{skill}` lo declara")
```

Ahora la propiedad es *"existe un párrafo que nombra al skill **y** declara el aislamiento"*: una declaración que viva en otro párrafo ya no cubre a este skill.

### Orden y prohibición: el literal lleva a su elemento, y la negación

Dos propiedades de prosa se pierden con facilidad al verificarlas por literales, porque el ámbito por defecto (el párrafo, la sección) las deja pasar en vacío.

**El orden.** *"A va después de B"* se verifica con un literal que ordena (`después del commit`, `y no antes`). Ese literal tiene que vivir **en la misma frase que el elemento ordenado**, no en cualquier parte del ámbito. Si la aserción mide la posición de la primera aparición del elemento, o busca el literal de orden suelto en el párrafo, otra frase que los contenga a ambos (un "en el mismo commit", por ejemplo) satisface el test aunque la frase que ordena diga lo contrario. Ancla el literal al elemento: una sola regex que exija ambos en la misma frase, y muta el literal de orden por su opuesto para ver el test en rojo.

**La prohibición.** *"Nunca hagas X"* se verifica con un literal que **incluye la negación**, no solo el término. Exigir como presente `X` no distingue lo recomendado de lo prohibido: el párrafo puede pasar a recomendarlo y el término sigue ahí, en verde. El literal es la frase negada completa y la mutación es sustituir la negación por su afirmativa (`sustituir`, no `borrar`), porque borrar el término deja un test que falla por otra razón.

### El segundo filo: no repitas el literal dentro del ámbito verificado

Si el archivo que la aserción inspecciona también contiene su propia documentación (un docstring, un comentario, una nota de diseño), **escribir el literal ahí satisface la aserción sin que el código real lo cumpla**. Es la forma más silenciosa de vaciar un test: el fix y la regresión caben en el mismo commit.

Al escribir la explicación, referí al literal sin reproducirlo: *"el literal de aislamiento"*, `<modo>`, una referencia al issue. Y dejá dicho en el texto **que te abstenés a propósito**, o el siguiente editor lo "arregla" reponiéndolo.

### Corolario operativo: al corregir un defecto de ámbito, mutá toda la clase del ámbito

Un defecto de ámbito **nunca es puntual**: si una aserción estaba mirando el bloque equivocado, todas las que comparten ese ámbito lo están. Después de arreglar una, recorré las demás del mismo ámbito y **mutá cada miembro por separado** —borrá la cláusula de cada uno, una a la vez— confirmando que cada mutación pone el test en rojo por su propio motivo. Arreglar sólo el miembro que el review encontró deja intacto el resto de la clase.

## Señales de que lo estás haciendo mal

- La aserción es `assertIn(literal, archivo.read_text())` y el archivo tiene más de una responsabilidad.
- El ámbito se eligió por lo que era fácil de segmentar (`split("## ")`), no por lo que contiene la instrucción.
- El mensaje de fallo no puede nombrar **cuál** de los N elementos del ámbito falló, porque el ámbito los agrupa a todos.
- La explicación de la regla, dentro del archivo verificado, contiene el literal que la regla busca.
- Un test de orden mide la primera aparición del elemento, o busca el literal de orden suelto en el párrafo.
- Una prohibición se verifica exigiendo el término presente, sin su negación.
- No sabés responder *"¿qué línea puedo borrar sin que este test se ponga rojo?"*.

## Caso real

**La sección era un ámbito demasiado grueso (#129, retro #84(5)).** `tests/test_consistencia.py`, clase `WorktreeDeImplementacionTests`. La primera versión segmentaba por bloques `##` y exigía el literal de aislamiento *"en la sección"*. Pero `## Fase 3: Ejecucion paralela` de `agents/flechodiezx.md` es **una sola sección que agrupa los tres lanzamientos** (el del perfil plugin y los dos del consumidor). Quitar la declaración de aislamiento sólo de la cláusula que lanza el sub-agente del perfil plugin **dejaba el test en VERDE**, porque la frase seguía viva en el párrafo del perfil consumidor. Era exactamente la regresión que el Gherkin de la HU quería impedir, invisible para el único test que debía cubrirla. Lo destapó un hallazgo CRÍTICO del code review, no la suite.

El fix `4fdb04c` (*"la invariante de worktree se verifica por parrafo, no por seccion (#84)"*) cambió la unidad a **párrafo** (`_parrafos`, split por línea en blanco) y la propiedad a existencial-por-párrafo.

**La segunda vuelta, en el mismo commit (#126, retro #84(2)).** Al reescribir el docstring para explicar la regla nueva, **la propia explicación repitió el literal**, volviendo a vaciar la invariante que el fix acababa de arreglar. Quedó corregido reformulando el docstring sin reproducir el literal. Por eso este archivo, cuando habla de ese caso, escribe `<literal de aislamiento>` y no el literal: no porque `heuristics/` esté bajo esa aserción —no lo está—, sino porque la disciplina de no reproducir lo que se busca es más barata que recordar el ámbito exacto de cada test.

**El orden y la prohibición pasaron en vacío (#321, retro #321, commit `579ec4a`).** `ChangelogEnHotfixPluginTests` verificaba dos propiedades de redacción del hotfix y ninguna mordía. El code review de #321, hallazgo 1 (WARNING): "El orden se mide con la primera aparición de `chore: changelog #N`, que cae en la frase de \"mismo commit\", antes de `verificar_plugin.py` pase lo que pase con \"despues\". Verificado en copia: cambiar \"despues del commit ... y no antes\" por \"antes del commit ...\" deja los 2 tests en verde (fallos 0 de 2)." Hallazgo 2 (WARNING): "`sed -i` solo se exige como presente, no como prohibido: el párrafo podría pasar a recomendarlo y seguir verde."

El fix `579ec4a` ("test(plugin): #321 endurece orden y prohibicion en ChangelogEnHotfixPluginTests") anclo el literal de orden a la frase de `verificar_plugin.py` y exigió la prohibición con su negación. La retro de #321 lo resumió como patrón: "Para un test de invariante de redacción sobre un agente, anclar el literal a la misma frase que el elemento con el que se ordena (`despues del commit ... y no antes` junto a `verificar_plugin.py`) hace que la mutación de ese literal falle 1 de 2."

## Cuándo NO aplica

- **Cuando el literal es global por definición** (la versión en `plugin.json`, el nombre del repo): ahí el archivo entero **es** el ámbito correcto y partirlo no agrega nada.
- **Cuando bajar el ámbito lo vuelve frágil por formato**: si la instrucción se reparte legítimamente en dos párrafos (una tabla y su nota al pie), exigir que todo viva en uno fuerza a escribir peor la documentación. Subí un nivel y compensá con un mensaje de fallo que nombre el elemento.
- **Cuando la aserción es sobre ausencia y la ausencia es global** (`assertNotIn("TODO", texto)`): no hay ámbito más chico útil.
- **En código ejecutable con tests de comportamiento**: si podés invocar la función y afirmar sobre su salida, hacelo — esta heurística es para aserciones sobre *texto*, que son un sustituto de segunda.

## Relación con otras heurísticas

- **`enumerar-la-clase-no-el-representante.md`** cubre el otro eje de la misma aserción: aquélla pregunta **qué entradas** entran, ésta pregunta **sobre qué bloque** se afirma. Invocá aquélla cuando dudes de si falta un caso; invocá ésta cuando dudes de si el caso que tenés realmente se rompería al borrar la línea que importa. El corolario de arriba (mutar toda la clase del ámbito) es el punto donde las dos se tocan: la clase a enumerar son los miembros del ámbito.
- **`aserciones-no-vacuas.md`** da el método general (mutar el literal por su opuesto y ver el rojo); la subsección *Orden y prohibición* es su aplicación a dos propiedades de prosa donde el ámbito esconde el vacío.
- **`propiedad-antes-que-tabla-en-fronteras.md`** ataca el mismo síntoma —una verificación que pasa sin verificar— pero en datos que cruzan una frontera, no en texto del repo, y su remedio es generar entradas, no achicar el ámbito.
- **`comentarios-verificables.md`** es su pariente cercano en la segunda vuelta: un docstring que explica una regla es una afirmación verificable, y cuando además vive dentro del ámbito verificado, no sólo puede ser falsa: puede volver falso al test.
