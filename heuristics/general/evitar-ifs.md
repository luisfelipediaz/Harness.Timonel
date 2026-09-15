# Heurística: Evitar condicionales — preferir maps, polimorfismo y herencia

## Regla general
Antes de escribir un `if`, un ternario, o un `switch`, pregúntate: ¿puede esto expresarse como un mapa de datos, una clase polimórfica, o una jerarquía?

**Marco mental: el `if` como objeto de decisión.** Un condicional que elige un valor o un comportamiento según una clave es **datos disfrazados de control de flujo**. Modelalo como datos:
```ts
const TITULOS = { isNew: 'Nuevo producto', isEdit: 'Editar producto' } as const;
const titulo = TITULOS[tipo];
```
La tabla es declarativa (se lee de un vistazo), se extiende agregando una fila, y con `Record<Key, V>` el compilador te obliga a cubrir todas las claves.

## Lookup maps en vez de ternarios/switch por tipo

**Mal:**
```ts
const clase = tipo === 'a' ? 'clase1' : tipo === 'b' ? 'clase2' : 'clase3';
```

**Bien:**
```ts
const clasePorTipo: Record<Tipo, string> = {
  a: 'clase1',
  b: 'clase2',
  c: 'clase3',
};
const clase = clasePorTipo[tipo];
```

Aplica igual en templates Angular:
```html
<!-- Mal -->
[ngClass]="tipo === 'a' ? 'clase1' : 'clase2'"

<!-- Bien -->
[ngClass]="clasePorTipo[tipo]"
```

## Valores que dependen de algo en runtime (theme, config) → `Record` de funciones

Si el valor no es estático porque depende de algo en runtime (colores del theme, locale, config),
el mapa sigue aplicando: hacelo un `Record<Key, (deps) => Value>` definido **a nivel de módulo**
(una sola vez, no por render):

```ts
const PALETTES: Record<ButtonVariant, (c: SemanticColors) => Palette> = {
  primary: (c) => ({ bg: c.primary, fg: c.primaryOn }),
  ghost:   (c) => ({ bg: c.surfaceMuted, fg: c.text }),
};
const palette = PALETTES[variant](colors);
```

Reemplaza a la típica función `getX(variant)` con un `switch` interno. El mapa es el único lugar
donde vive la decisión.

## Polimorfismo en vez de ifs que varían por tipo

Si el `if` decide **qué comportamiento ejecutar** según el tipo de un objeto, ese comportamiento pertenece al objeto mismo.

**Mal:**
```ts
if (figura instanceof Circulo) {
  return Math.PI * figura.radio ** 2;
} else if (figura instanceof Rectangulo) {
  return figura.ancho * figura.alto;
}
```

**Bien:**
```ts
// Cada figura sabe calcular su área
figura.area();
```

## Herencia / interfaces en vez de ifs que varían por variante

Si el `if` construye o configura algo diferente según un tipo de entrada, considera si ese tipo de entrada debería ser una clase/interfaz propia.

## Cuándo SÍ está bien un if / switch (no fuerces el mapa)

Forzar un lookup donde no corresponde es el anti-patrón opuesto. Dejá el condicional cuando:

- **Guards** de nulidad/`undefined`/`typeof` al inicio de una función, y discriminadores de overload.
- **Validaciones en boundaries** del sistema (input del usuario, respuestas de API).
- **Condiciones de negocio únicas** que no representan variación estructural.
- **Discriminated unions en TypeScript**: un `switch` exhaustivo sobre el campo discriminante es la
  forma **idiomática y type-safe**. Da *narrowing* por caso (cada rama ve los campos correctos de esa
  variante) y, con un tipo de retorno declarado, error de compilación si falta un caso. Un
  `Record<type, handler>` recibiría la unión completa → perdés el narrowing y necesitás casts. **No
  lo conviertas.**
  ```ts
  switch (mut.type) {
    case 'add':       return applyAdd(s, mut.item);        // acá mut.item existe
    case 'updateQty': return applyQty(s, mut.itemId, mut.quantity);
    case 'remove':    return applyRemove(s, mut.itemId);
  }
  ```
- **Rangos / umbrales numéricos** (`x >= 3 ? 2 : x >= 1 ? 1 : 0`): no son claves discretas, son
  cortes en un continuo; un `Record` no aplica (a lo sumo una tabla de rangos si hay muchos). El
  ternario encadenado está bien.

## Caso real

**Procedencia: importada, sin caso registrado en este repo.** Llegó con el harness original del Portal en el commit `c8bcc42` (*"extraer harness SDD del Portal como plugin timonel con backlog en GitHub Issues"*, v0.1.0), anterior a la gobernanza de TIM-ADR-0005 — ese commit no referencia ningún issue y no hay retro ni review que la origine. No se le inventa un caso: su procedencia se documentó retroactivamente en #134, la historia que hizo descubribles las heurísticas.

El uso vivo que sí es verificable: `CLAUDE.md` la cita como regla de Python del propio plugin (*"lookup maps antes que cadenas de `if`"*), y `scripts/pr_check.py` y `scripts/guard_integracion.py` la aplican con sus mapas de traducción (`_STATE_A_EJE`, `_CONCLUSION_A_EJE`, `_MOTIVO_POR_EJE`).

## Relación con otras heurísticas

- **`perfiles-como-tabla.md`** es esta misma regla aplicada a la prosa de agentes y skills. Invocá ésta cuando edites código —donde `Record<Tipo, …>` te da exhaustividad del compilador— y aquélla cuando edites un `.md` de `agents/` o `skills/`, donde nadie verifica que estén todas las celdas y la tabla es el único mecanismo que hace visible lo que falta.
- **`no-tipos-espejo.md`** comparte el mecanismo del `Record` exhaustivo por unión de literales, pero mira los tipos en vez del flujo de control: allá el olor es un tipo que duplica a otro, acá un condicional que duplica una tabla.
- **`enumerar-la-clase-no-el-representante.md`** interviene cuando la clave del mapa no es una unión cerrada: un lookup sobre valores externos necesita además la clase completa de entradas y un default que no sea el resultado favorable.
