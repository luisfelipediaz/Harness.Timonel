# Heurística: Un tipo por concepto — no crear abstracciones que duplican otros tipos

## Regla general
Cada tipo debe representar una idea nueva. Si un tipo solo existe para renombrar, reordenar o recortar campos de otro, no es una abstracción — es ruido. Antes de crear `XResponse`, `XRequest`, `XDto`, `XPersistencia`, `XViewModel`, pregúntate: **¿este tipo dice algo que el original no dice?**

## Señales de que un tipo sobra

- Comparte **>70% de campos** con otro tipo del mismo dominio
- Su único aporte es **agregar o quitar 1-2 campos** no sensibles
- Requiere un **mapper manual campo-a-campo** para convertir entre ambos
- Si eliminás el tipo, podrías usar `Omit<>`, `Pick<>` o `Partial<>` sin perder claridad

## Composición en vez de duplicación

Cuando sí hay variación legítima entre capas, derivar en vez de redefinir:

**Mal — dos interfaces que repiten campos:**
```ts
interface ProductoPersistencia {
  _id?: string;
  nombre: string;
  precio: number;
  activo: boolean;
  tenantId: string;
}

interface ProductoResponse {
  _id: string;
  nombre: string;
  precio: number;
  activo: boolean;
}
```

**Bien — un tipo base y derivaciones con `&`, `Omit`, `Pick`:**
```ts
interface Producto {
  _id?: string;
  nombre: string;
  precio: number;
  activo: boolean;
}

type ProductoPersistencia = Producto & {
  tenantId: string;
};

// Si realmente necesitas un subtipo estricto:
type ProductoResumen = Pick<Producto, '_id' | 'nombre'>;
```

## No crear mappers triviales

Si un mapper solo copia campos y aplica fallbacks (`?? ''`, `String()`), eliminarlo. TypeScript no filtra propiedades en runtime y no necesita hacerlo — el tipo como contrato es suficiente.

**Mal:**
```ts
mapear(doc: Persistencia): Response {
  return {
    _id: String(doc._id),
    nombre: doc.nombre,
    icono: doc.icono ?? '',
    precio: doc.precio,
  };
}
```

**Bien:**
```ts
return doc; // el tipo del return ya restringe la forma
```

## Cuándo SÍ crear un tipo separado

- La transformación es **no trivial** (cálculos, agregaciones, aplanamiento de relaciones)
- Los campos omitidos son **datos sensibles** (tokens, passwords, secrets internos)
- El tipo combina datos de **múltiples fuentes** que no comparten un modelo natural
- El tipo representa un **contrato público** (API pública, SDK) que debe ser estable aunque el modelo interno cambie

## Caso real

**Procedencia: importada, sin caso registrado en este repo.** Llegó con el harness original del Portal en `c8bcc42` (v0.1.0), antes de TIM-ADR-0005: ese commit no referencia issue y no hay retro ni code review que la origine. No se le inventa uno; su procedencia quedó documentada en #134.

Lo verificable hoy es su uso como criterio de review: `evals/code-review/tres-violaciones-warning/` la usa como uno de los tres hallazgos esperados, con el grader `detecta-tipo-espejo.md` (*"`GastoResponse` copia campo a campo `Gasto` (tipo espejo…) y debe salir como hallazgo WARNING"*).

## Relación con otras heurísticas

- **`evitar-ifs.md`** es su par sobre el flujo de control: las dos terminan en el mismo `Record<Tipo, …>` exhaustivo, pero aquélla pregunta *"¿este condicional es una tabla?"* y ésta *"¿este tipo dice algo nuevo?"*.
- **`sensor-importa-no-reimplementa.md`** es el mismo principio sobre cálculos en vez de tipos: un segundo contador que duplica a otro diverge en silencio igual que un segundo tipo que duplica a otro. Invocá aquélla cuando estés por copiar una función; ésta cuando estés por copiar una forma de datos.
- **`enumerar-la-clase-no-el-representante.md`** aparece al derivar con `Omit`/`Pick`: si la derivación enumera campos a mano en vez de expresarse por la regla que los selecciona, el tipo espejo vuelve por la ventana.
