# Heurística: Todo sensor declara dónde deja su evidencia, con qué ancla se cuenta, y distingue "no" de "sin datos"

## Regla general

Un **sensor** es cualquier cosa que mide el propio proceso y devuelve un veredicto: un check del DoD, un smoke del harness, una métrica de flujo, un hook que loguea. Su salida se lee como verdad, así que la salida sola no alcanza: el sensor tiene que declarar **de dónde sacó el número**.

Tres exigencias, ninguna opcional:

1. **Dónde vive la evidencia.** Ruta concreta, y de qué árbol: el repo del issue, el `cwd` de la sesión, un artefacto de CI. Un sensor que lee un archivo que el lector no sabe ubicar no es auditable.
2. **Con qué ancla se cuenta.** El patrón literal que se busca en esa evidencia (un prefijo de línea, un marcador, un label). Sin ancla, dos ejecuciones cuentan cosas distintas y nadie lo nota.
3. **Tres estados, no dos.** `sí` / `no` / **`sin datos` o `N/A en perfil <p>`**. Un booleano colapsa "medí y no pasó" con "no pude medir", que es la diferencia entre un hallazgo y un hueco.

## Qué hacer

**Mal — el booleano:**

```python
def hook_disparo(eventos: dict | None) -> bool:
    return bool(eventos and eventos["gh"])   # False si no hubo, False si no hay log
```

**Bien — los tres estados, con la evidencia en la fila:**

```python
def fila_hook(nombre: str, n: int | None, texto_en_cero: str) -> FilaDisparo:
    """Una fila de hook a partir del conteo de eventos: None (sin events.log) y
    0 (perfil sin ese consumidor) son casos distintos de 'no disparo'."""
    if n is None:
        sin_datos = "sin datos (events.log ausente)"
        return (nombre, sin_datos, sin_datos)
    if n == 0:
        return (nombre, "0 eventos", texto_en_cero)
    return (nombre, f"{n} eventos", "sí")
```

La fila lleva **las dos columnas**: la evidencia (`"12 eventos"`, `"#84 sí, #83 no"`, `"sin datos"`) y el veredicto. Y el tercer estado se **parametriza por perfil** en el llamador, que es quien sabe si el cero significa "no disparó" o "acá no aplica":

```python
fila_hook("hook `raiz-editada`", n_raiz, "N/A en perfil plugin (sin consumidor)")
```

El mismo criterio, al no medir algo: decilo. `_filas_disparo` lo deja escrito — *"No inventa filas para `dor_check` ni `estado_historia`: no son observables de forma directa desde el issue"*. Una fila ausente y declarada informa; una fila inventada en verde miente.

## Señales de que lo estás haciendo mal

- El sensor devuelve `True`/`False` y el reporte no dice sobre qué corrió.
- Un `0` en la salida y no podés decir si significa "no ocurrió" o "no se midió".
- La evidencia vive en un archivo cuya ubicación el reporte no nombra, y el lector la busca en el repo equivocado.
- El conteo se hace con un `in` o un `contains` en vez de un ancla anclada al inicio de línea: cualquier mención en prosa infla el número.
- El sensor cubre un perfil y en el otro devuelve el mismo valor que un fallo real.

## Caso real

**Sin defecto registrado: esta heurística nace de una observación de proceso, no de un bug.** Es la excepción del conjunto y conviene decirlo, porque inventarle un commit la volvería tan poco confiable como los comentarios que `comentarios-verificables.md` prohíbe.

El origen es la retro del issue #29, punto 5 ("patrones descubiertos"), registrado al construir y medir el smoke del harness (`tests/test_smoke_harness.py` sobre `medir_issue`, `contar_eventos`, `tabla_disparos`). Dos patrones, textuales:

> un sensor con tres estados (sí/no/N/A en perfil <p>) informa más que un booleano

> la evidencia de los hooks vive en el cwd de la sesión de Claude, no en el repo del issue

Es evidencia de **patrón**, no de un archivo con el defecto puntual: no hubo un commit del bug ni un commit del fix. Lo que sí existe hoy, como forma ya aplicada, es `scripts/smoke_harness.py:76-84` (`fila_hook`, los tres estados) y `:87-89` (`_filas_disparo`, la declaración de lo que no se mide) — el código citado arriba en "Qué hacer" sale de ahí. La heurística se registró como #45 para que la forma sobreviva a la memoria de quien la descubrió.

## Cuándo NO aplica

- **Cuando el sensor es un test unitario**: un `assert` es binario a propósito y su evidencia es el propio caso. Esta heurística es para sensores que miden **el proceso** y reportan a personas.
- **Cuando "sin datos" es imposible por construcción**: si la fuente se genera en la misma corrida, el tercer estado es ruido; basta el par.
- **Cuando declarar la evidencia filtra algo sensible** (rutas de una máquina, contenido de un log privado): declaralo por nombre lógico y dejá la ruta fuera del reporte.
- **En sensores de un solo perfil**: el `N/A en perfil <p>` sólo agrega valor cuando hay más de un perfil; forzarlo en uno solo es la variante inútil de la regla.

## Relación con otras heurísticas

- **`sensor-importa-no-reimplementa.md`** es su par y cubre la mitad opuesta del mismo sensor: ésta gobierna la **salida** (dónde está la evidencia, con qué ancla, con cuántos estados); aquélla gobierna la **entrada y el cálculo** (de dónde sale el número). Invocá ésta al diseñar la fila del reporte; invocá aquélla al escribir la función que la llena. Se refuerzan: importar el cálculo de otro sensor hereda gratis su ancla y su estado "sin datos", que es justo lo que ésta exige.
- **`comentarios-verificables.md`** explica por qué "declarar la evidencia" no puede ser un comentario en prosa: si la declaración no es consultable, es una afirmación sin verificar. La evidencia va en la salida del sensor, no en un comentario sobre él.
- **`propiedad-antes-que-tabla-en-fronteras.md`** comparte el principio del tercer estado: una entrada degenerada (o una medición ausente) nunca cae en el resultado favorable por default.
