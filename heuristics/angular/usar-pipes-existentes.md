# Heurística: Usar los pipes e utilidades que ya vienen con el framework

## Regla general

Antes de escribir lógica de presentación (formatear fechas, números, monedas, capitalizar, truncar, transformar), **pregúntate si el framework ya trae un pipe o utilidad para eso**. Si existe, úsalo. No duplicar trabajo que el framework ya resolvió con soporte de internacionalización, accesibilidad y mantenimiento gratis.

Esto aplica a Angular (`DatePipe`, `CurrencyPipe`, `TitleCasePipe`, `LowerCasePipe`, `UpperCasePipe`, `DecimalPipe`, `PercentPipe`, `SlicePipe`, `JsonPipe`, `AsyncPipe`, `KeyValuePipe`, `I18nPluralPipe`, `I18nSelectPipe`), pero también a la plataforma (`Intl.DateTimeFormat`, `Intl.NumberFormat`, `Intl.ListFormat`, `Intl.RelativeTimeFormat`, `Intl.PluralRules`, `Array.prototype.toSorted`, etc.) y a las libs ya instaladas en el proyecto.

## Señales de que estás reinventando la rueda

- Declaras un **array hardcoded de meses, días de la semana, monedas, locales** para indexarlo por número
- Escribes un método `formatearFecha`, `formatearMoneda`, `capitalizar`, `truncar`
- Concatenas strings con `$`, `,`, `.` para formatear cantidades
- Conviertes `Date` a string con `padStart`, `split`, `toString`, manualmente
- Tu lógica tiene comentarios tipo `// hardcoded en español` o `// no sé hacerlo con el pipe`
- Tienes literales `'Enero', 'Febrero', ...` o `'Mon', 'Tue', ...` en código de producción

Todo esto son **olores** de que un pipe o API del framework ya resuelve el caso.

## Ejemplo: formatear periodo mes-año

**Mal — array hardcoded de meses:**

```ts
const MESES = ['Enero', 'Febrero', 'Marzo', /* ... */];

// En el selector:
const periodoFormateado = computed(() => `${MESES[mes() - 1]} ${anio()}`);
```

**Problemas:**

- Duplicado en cada módulo (selector + componente de preview tenían el mismo array).
- No responde a cambio de locale (`LOCALE_ID`) — siempre en español codificado a mano.
- No capitaliza consistente (`'Enero'` fijo pero `titlecase` del CLDR daría `'Enero'` con locale español igual).
- Crece con cada nueva necesidad: nombres cortos, día de la semana, estacionalidad.

**Bien — `DatePipe` con un `Date` que representa el periodo:**

```ts
// Selector: exponer mes + anio (signals primitivos) y construir Date en el consumer
readonly periodoFecha = computed(
  () => new Date(this.facade.anio(), this.facade.mes() - 1, 1)
);
```

```html
{{ periodoFecha() | date: 'LLLL y' | titlecase }}
```

**Beneficios:**

- Cero strings de meses en el proyecto.
- El locale manda: `LOCALE_ID = 'es-CO'` → `'Abril 2026'`, cambio a `'en-US'` → `'April 2026'`.
- Se encadena con otros pipes (`titlecase`, `lowercase`, etc.) sin código extra.
- Tests comparan `Date` (semántica pura) en vez de strings formateados (que rompen al cambiar idioma).

## Formato de `DatePipe`

Memorizar los más usados evita reinventar:

- `'shortDate'` / `'mediumDate'` / `'longDate'` / `'fullDate'` — presets locale-aware
- `'MMMM'` — nombre largo del mes (dependiente del contexto de formato)
- `'LLLL'` — nombre largo del mes en **forma standalone** (úsalo cuando el mes va solo, no dentro de una fecha completa — en español cambia las dos formas son iguales, en otros idiomas como ruso difieren)
- `'MMM'` / `'LLL'` — nombre corto
- `'y'` — año, `'yyyy'` — año 4 dígitos
- `'EEEE'` — día de la semana largo

**Regla mental**: si estás iterando un array de strings para mostrarlos por locale, ese array probablemente ya vive en el CLDR de Angular y se obtiene con un pipe.

## Cuándo sí hacer código propio

Solo cuando el pipe no cubre el caso:

- Formato **muy idiosincrático del dominio** que no es traducción de locale (ej: `'Quincena 1 de Abril'` — eso sí es lógica de negocio)
- **Combinar varios datos** que no son solo fecha/número (ej: `'Abril 2026 (en curso)'` con estado derivado)
- Para casos así, **envolver el pipe** en un pipe propio o en un `computed` que llame `formatDate`/`formatNumber` de `@angular/common` — no reescribir lo que el pipe hace.

## Checklist antes de escribir código de formato

1. ¿Existe un **pipe de Angular** que haga esto? → `CommonModule` tiene 13 pipes, revisa primero.
2. ¿Existe una **API `Intl.*`** que haga esto? → Está en todos los navegadores soportados.
3. ¿La lib del proyecto (`@sinco/angular`, Material, etc.) ya expone un pipe? → Grep por `Pipe` en las libs antes.
4. Si nada aplica, ¿puedo **encadenar pipes existentes** en vez de escribir uno nuevo? → `| date | titlecase`, `| currency | slice:0:-3`, etc.
5. Si debo escribir código, ¿lo encapsulo en un **pipe reutilizable** en vez de lógica inline en el componente?

## Caso real

**Procedencia: importada, sin caso registrado en este repo.** Llegó con el harness original del Portal en `c8bcc42` (v0.1.0), antes de TIM-ADR-0005; el ejemplo del array `MESES` viene del código del Portal, no de un issue de Timonel. No se le inventa un commit propio: la procedencia se documentó en #134.

Su uso verificable hoy es como fuente de hallazgos `Heurística` del skill `code-review`, junto con el resto de `heuristics/`.

## Relación con otras heurísticas

- **`sensor-importa-no-reimplementa.md`** es la misma regla mirando hacia adentro del harness: no reimplementar un cálculo que otro sensor ya resolvió. Invocá ésta cuando lo ya resuelto lo trae **el framework o la plataforma**; aquélla cuando lo trae **otro módulo del propio repo**.
- **`no-tipos-espejo.md`** ataca la variante estructural del mismo desperdicio: un `ViewModel` que sólo existe para guardar el string ya formateado suele ser el síntoma de no haber usado el pipe.
- **`convenciones-bitakora.md`** cataloga las reglas de estilo de Angular/NestJS del consumidor; ésta es una heurística de diseño, no una regla de estilo, y manda el `CLAUDE.md` del consumidor sobre aquél, no sobre ésta.
