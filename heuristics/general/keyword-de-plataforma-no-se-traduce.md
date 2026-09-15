# Heurística: Una palabra que interpreta un sistema externo se escribe en su idioma original, nunca traducida

## Regla general

Hay strings que **se leen** y strings que **se ejecutan**. Un texto que una plataforma va a parsear —`Closes #N` de GitHub, `BREAKING CHANGE:` de Conventional Commits, `WIP:` de un CI, un nombre de label, un nombre de branch, una cabecera HTTP, el valor de un enum de un tercero— es una **keyword**, no prosa. Cambiarle el idioma, la capitalización o la puntuación no la hace "menos legible": la hace **no existir**.

El peligro específico: la plataforma **no protesta**. No hay error, no hay warning, no hay log. El texto aparece renderizado, en el lugar correcto, con buen aspecto, y simplemente no hace nada. En un repo en español la tentación es sistemática y el síntoma es invisible.

La regla: cuando escribas un string que un sistema externo interpreta, la keyword va literal, en su idioma; la explicación humana va **al lado**, en el idioma del equipo.

## Qué hacer

**Mal — la keyword traducida:**

```python
def cuerpo_pr(issue, repo, titulo):
    link = f"https://github.com/{repo}/issues/{issue}"
    return f"Cierra #{issue} ({link})\n\n"   # GitHub no reconoce "Cierra"
```

**Peor — la keyword correcta agregada *junto a* la traducida:**

```python
return f"Closes #{issue}\n\nCierra #{issue} ({link})\n\n"
```

Funciona, pero deja dos referencias al mismo issue y la falsa impresión de que la línea en español también hace algo.

**Bien — la keyword literal, y la prosa en español sin fingir que es keyword:**

```python
return (
    f"Closes #{issue}\n\n"
    f"Implementa la historia [#{issue}]({link}): {titulo}\n\n"
    …
)
```

Y la sujeción: **un test que afirme la primera línea literal**. No hay revisión de diff que lo detecte, porque el diff se ve bien.

```python
self.assertTrue(cuerpo.startswith(f"Closes #{issue}\n"))
```

## Señales de que lo estás haciendo mal

- Un string en español ocupa una posición sintáctica que una plataforma parsea (primera línea de un cuerpo de PR, prefijo de un commit, valor de un campo de configuración).
- El efecto que debía producir ese string **lo está produciendo otra cosa**: un paso manual, un `gh issue close` en alguna fase, un humano que lo hace "por las dudas". Ese paso manual es la máscara.
- Nadie puede citar la documentación del tercero donde aparece esa palabra.
- La única prueba de que funciona es que "se ve bien en la interfaz".
- Al quitar el paso manual, nada falla en verde — falla en silencio, semanas después.

## Caso real

**`Cierra #N` que nunca cerró un issue (#90, retro #80(5)).** `scripts/integracion.py`, función `cuerpo_pr`. El commit `6a57e24` (*"agrega scripts/integracion.py y la fase 8 PR/Integracion en estado_historia (#31)"*) escribió **únicamente**:

```python
f"Cierra #{issue} ({link})\n\n"
```

Nunca `Closes` / `Fixes` / `Resolves`, que es la única familia que GitHub reconoce. Durante toda esa etapa **el cierre real lo tapaba el `gh issue close` manual de la vieja Fase 8**: el efecto existía, la causa era otra.

Al quitarse ese paso manual, el commit `5aca74e` (#80) agregó `Closes #{issue}` **junto a** la línea vieja (redundante), y el fix `ac342d6` (#80, *"el cuerpo del PR usa la keyword de cierre y cita el titulo, sin duplicar la referencia"*) dejó la forma actual: `Closes #{issue}` primero y `Implementa la historia [#{issue}](link): {titulo}` como prosa.

La retro #80, textual:

> Sin la corrección, la HU habría dejado los issues abiertos para siempre… Solo un test que afirme la primera línea literal lo sujeta; ninguna lectura del diff lo detecta.

El síntoma en una frase: **una palabra en español, visualmente correcta, que la plataforma simplemente ignora.**

## Cuándo NO aplica

- **A la prosa dirigida a personas**: títulos de PR, descripciones, mensajes de error de cara al usuario, comentarios de issue. Ahí el español es la regla del repo y traducir es correcto.
- **Cuando la plataforma es explícitamente multilingüe** y la documentación del tercero lista tu idioma entre los aceptados: entonces la palabra traducida **también es keyword**. Hay que poder citar dónde lo dice.
- **A las keywords de tu propio sistema**: los marcadores `timonel:*`, los labels propios o los nombres de fase los definís vos; el idioma es una decisión de diseño, no una restricción externa. Lo que sigue aplicando es que el literal viva en un solo lugar.
- **Cuando el string es configurable por el consumidor**: ahí el valor no se hardcodea en ningún idioma; se lee del config y se valida.

## Relación con otras heurísticas

- **`propiedad-antes-que-tabla-en-fronteras.md`** cubre la misma frontera en el sentido contrario: aquélla, los datos que **entran** desde el sistema externo; ésta, el vocabulario que **sale** hacia él. Las dos comparten el modo de fallo característico de las fronteras: **el tercero no devuelve error**, así que la única señal posible es una que pongas vos.
- **`comentarios-verificables.md`** ataca la variante documental del mismo engaño: *"esto cierra el issue"* escrito en un comentario es tan falso como `Cierra #N` en el cuerpo del PR, y también sobrevive porque nadie lo ejecuta.
- **`enumerar-la-clase-no-el-representante.md`** interviene cuando la familia de keywords es un conjunto (`Closes`/`Fixes`/`Resolves`, con sus variantes): la aserción que sujeta el literal debe saber cuál de la clase acepta, no sólo la que elegiste.
