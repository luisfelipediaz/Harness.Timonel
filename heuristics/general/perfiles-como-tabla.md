# Heurística: Un perfil se expresa como tabla de detección más tabla de fases, no como condicionales repartidos en prosa

## Regla general

Cuando un agente, un skill o un script se comporta distinto según un **perfil** (plugin vs consumidor, dev vs prod, monorepo vs repo simple), la variación es **datos**: un conjunto cerrado de perfiles × un conjunto cerrado de fases. Expresarla como frases condicionales repartidas por el documento —*"**Perfil plugin**: acá hacés esto"*, diez veces, en diez lugares— es el `if` encadenado de `evitar-ifs.md`, pero en prosa, donde además **no hay compilador que exija exhaustividad**.

Dos tablas resuelven el caso:

1. **Tabla de detección**: qué señal concreta determina el perfil, en orden de precedencia, y qué pasa si ninguna aplica.
2. **Tabla de fases × perfil**: una fila por fase, una columna por perfil, y en cada celda `obligatorio` / `N/A` / la variante. **Las celdas `N/A` son el aporte principal**: una fase que no aplica a un perfil es información, y en prosa simplemente no se escribe — se lee como olvido o como "hacé lo mismo".

## Qué hacer

**Mal — el perfil disperso en prosa, una mención por fase:**

```markdown
## Fase 2
**Perfil plugin**: no hay API. El contrato es un contrato de cambio…

## Fase 3
**Perfil consumidor**: lanza los sub-agentes en el mismo mensaje…

## Fase 6
**Perfil consumidor**: si falla, sigue (no bloqueante). **Perfil plugin**: la retro sí bloquea…
```

Para saber qué hace el perfil plugin hay que leer el documento entero y acordarse de todas las menciones. Para saber si a una fase le falta su variante, no hay forma.

**Bien — detección primero, matriz después:**

```markdown
| Señal (en orden) | Perfil |
| --- | --- |
| `.claude-plugin/plugin.json` con `name == "timonel"` | `plugin` |
| issue con label `mod:plugin` | `plugin` |
| en otro caso | `consumidor` |

| Fase | `plugin` | `consumidor` |
| --- | --- | --- |
| 2 · Contrato | contrato de cambio (`Archivo \| Cambio`) | contrato API |
| 3 · Ejecución | un sub-agente, cualquiera sea el alcance | backend/frontend según alcance |
| 6 · Retro | **bloquea** el DoD (ítem 9) | no bloqueante |
```

La prosa que queda debajo explica **una** celda cuando la celda no se explica sola — no repite la condición.

## Señales de que lo estás haciendo mal

- `grep -c "Perfil <X>"` sobre el documento devuelve un número de dos cifras.
- Para responder *"¿qué hace el perfil X en la fase N?"* hay que leer el documento completo.
- Hay fases sin ninguna mención del perfil y no sabés si es porque no aplica o porque se olvidó.
- Agregar un perfil nuevo obliga a revisar cada sección buscando dónde insertar otra frase.
- La misma condición está escrita con palabras distintas en dos lugares (*"si el repo es el propio plugin"* / *"en perfil plugin"*), y no podés afirmar que signifiquen lo mismo.

## Caso real

**Los perfiles de `flechodiezx` en prosa (#34, retro #27(2)).** `agents/flechodiezx.md` menciona `Perfil plugin` / `Perfil consumidor` **diez veces**, repartidas en la Fase 0 (línea 16), Fase 1 (38), Fase 2 (50, 52), Fase 3 (67, 83), Fases 4-5 (130, 132), Fase 6 (140) y las notas (173) — **sin ninguna tabla de detección ni tabla de fases × perfil**. La Fase 0 lleva la regla de detección redactada dentro de un párrafo corrido, junto con lo que cada perfil lee del config.

La retro del issue #27, punto 2, textual:

> Los perfiles del orquestador (nx vs plugin) se expresan bien como una tabla de detección + tabla de fases con 'obligatorio/N/A' por perfil; evita ramificar cada fase con condicionales en prosa.

El contra-hecho es el estado presente, no un bug pasado: al escribirse esta heurística el archivo **sigue en el formato que la retro describe como problema**. Por eso el caso es verificable con un comando en vez de con un diff:

```bash
grep -o 'Perfil plugin\|Perfil consumidor' agents/flechodiezx.md | wc -l   # → 10
```

## Cuándo NO aplica

- **Con un solo perfil, o con dos que difieren en una única fase**: una tabla de una fila es peor que la frase. La heurística se activa cuando la variación cruza **varias** fases.
- **Cuando la diferencia es de grado y no de estructura** (el mismo paso con otro timeout, otro modelo): eso es un parámetro del config, no una columna de la matriz. Convertirlo en perfil multiplica las celdas sin agregar información.
- **Cuando la variante necesita media página de explicación**: la celda queda ilegible. Poné en la celda el nombre de la variante y debajo **un** párrafo que la desarrolle, referenciado desde la tabla — el error es repetir la condición, no explicar.
- **En código donde el lenguaje ya da exhaustividad**: en un `Record<Perfil, …>` de TypeScript o un `dict` con `KeyError`, la tabla ya existe y es el código.

## Relación con otras heurísticas

- **`evitar-ifs.md`** es la misma regla en código y ésta es su traducción a documentos de agentes y skills. La diferencia que decide cuál invocar: en código el `Record<Tipo, …>` te da exhaustividad gratis del compilador, y por eso allá la tabla es sobre todo legibilidad; en prosa **nadie verifica que estén todas las celdas**, y por eso acá la tabla es el único mecanismo que hace visible lo que falta. Si estás editando `.ts` o `.py`, es aquélla; si estás editando un `.md` de `agents/` o `skills/`, es ésta.
- **`enumerar-la-clase-no-el-representante.md`** explica por qué la dispersión es cara: diez menciones sueltas de un perfil son diez representantes de una clase que nunca se enumeró. La matriz **es** la clase.
- **`unidad-de-verificacion.md`** entra al escribir el test de consistencia que sujeta la tabla: sobre prosa dispersa no hay ámbito sensato que verificar; sobre una tabla, la fila es la unidad natural.
