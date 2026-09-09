# Plantilla — issue `tipo:hotfix`

**Titulo**: `[verbo infinitivo] [que cosa]`. Ej: `Corregir corte del header del modal en iOS`.

**Labels obligatorios**: `tipo:hotfix`, `estado:borrador|listo`, `alcance:*`, `sp:1|2` (`sp:3` solo con confirmacion), `mod:<modulo>`. Agregar `bug` si corrige un defecto.

**Padre**: opcional (puede ser raiz o sub-issue de una epica).

## Body

````markdown
## Historia

[Descripcion breve del fix y del comportamiento esperado. Puede omitir Como/quiero/para.]

## Criterios de aceptación

```gherkin
DADO QUE [contexto]
CUANDO [accion]
ENTONCES [resultado]
```

## Ficha técnica

| Campo             | Valor                                  |
| ----------------- | -------------------------------------- |
| Alcance           | Backend / Frontend / Full-stack        |
| App destino       | (si aplica)                            |
| Entidad principal | ...                                    |
| Tipo de operación | Fix / Refactor / Ajuste de texto       |
| Permiso requerido | (existente; un hotfix no crea permisos)|
| Módulo destino    | (existente; un hotfix no crea modulos) |

## Endpoints

Ninguno

## Modelos compartidos

Ninguno

## Dependencias

Ninguna

## Tareas

- [ ] Implementación
- [ ] Lint + tests afectados
- [ ] Code review
- [ ] Definition of Done
````

## Reglas

- `Endpoints` y `Modelos compartidos` deben ser `Ninguno`; si no, es una HU y va por `story-executor`.
- `sp` ≥ 5 → no es hotfix.
