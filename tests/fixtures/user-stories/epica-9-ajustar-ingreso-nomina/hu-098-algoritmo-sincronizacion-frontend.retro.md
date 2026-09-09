---
historia: HU-098
titulo: Algoritmo de sincronizacion del ingreso de nomina desde liquidacion
estimado_sp: 8
real_sp: 13
precision_estimacion: subestimado
modulo: mis-finanzas
alcance: Frontend
fecha: 2026-04-20
---

## Desviaciones

- La spec sugeria `setMonth(d.getMonth()+1)` para la utilidad de mapping; en la practica tuvo que reemplazarse por aritmetica modular sobre getMonth/getFullYear por el bug de overflow de Date (ver Errores recurrentes).
- El re-dispatch del algoritmo tras la navegacion de liquidacion no se resolvio con una action explicita sino con una suscripcion directa a `rootStore.select(getLiquidacion)` filtrada por el flag `sincronizandoNomina()`; aparece en las notas tecnicas como opcion pero no como decision firme.
- Se agrego una suscripcion `takeUntilDestroyed()` en el bloque de `withMethods`, patron no contemplado en la spec que mezcla signals con un Observable "vivo" dentro del signalStore.

## Errores recurrentes

- Bug de overflow de `Date` al hacer `setMonth(getMonth()+1)` en fechas con dia 31 (p.ej. 2026-01-31 saltaba a marzo porque febrero no tiene dia 31). Se reemplazo por aritmetica directa sin mutar la Date, y se agrego test explicito para enero-31.
- El spec de `sincronizarIngresoNomina` fallaba porque `resolverSincronizacion` encadena multiples `await firstValueFrom`, y un solo `Promise.resolve()` no drenaba suficientes microtareas. Se introdujo helper `flushMicrotasks(6)` para estabilizar los asserts.

## Patrones descubiertos

- `rxMethod<void>(pipe(tap(() => asyncFn())))`: forma efectiva de disparar una funcion async dentro de un signalStore sin bloquear el pipe ni encadenar el Observable al ciclo de vida del await.
- State machine minima con un solo flag (`sincronizandoNomina`) + suscripcion filtrada a un selector externo: sustituye un effect dedicado y evita orquestar actions intermedias para re-ejecutar el algoritmo tras cada navegacion.
- Proteccion contra bucle imposible con `console.warn` unico + reset del flag: patron liviano para algoritmos iterativos que dependen de un store externo que podria no avanzar.
- Helper local `upsertEnArray` para reducir el patch del signalStore: encapsula "reemplazar por \_id o agregar al final" sin tocar el resto del estado.

## Mejoras sugeridas

- Documentar en heuristicas/skills que `Date.setMonth(m+1)` NO es seguro para cruce de fin-de-mes y debe evitarse; preferir aritmetica modular sobre getMonth/getFullYear. Es un bug recurrente en mapping de periodos.
- Agregar en el skill `ngrx-signal-store` una nota sobre combinar `rxMethod` con funciones async (patron `tap(() => asyncFn())`) y sobre como testear timing cuando hay cadena de `firstValueFrom` (helper `flushMicrotasks(n)`).
- En CLAUDE.md, cuando una historia involucre iteracion sobre un store externo con side-effects, explicitar la recomendacion de usar state machine con flag + suscripcion filtrada antes de plantear un effect dedicado, para reducir ambiguedad en diseño.
- Re-evaluar el estimado base para HU que orquestan dos stores (modulo + portal) con navegacion iterativa: 8 SP resulto insuficiente por los casos borde de Date y timing de tests.
