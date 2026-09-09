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
