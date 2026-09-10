---
name: interrogame
description: Entrevista al usuario exhaustivamente sobre un plan o diseño hasta alcanzar un entendimiento comun, resolviendo cada rama del arbol de decisiones una pregunta a la vez y con respuesta recomendada. Usalo cuando el usuario quiera poner a prueba un plan, cuestionar su diseño, mencione "interrogame", o cuando un agente (sdd-planner, user-story-planner) necesite descubrir requisitos antes de escribir.
---

# Interrógame

Entrevista al usuario exhaustivamente sobre cada aspecto del plan o diseño hasta alcanzar un entendimiento común. Recorre cada rama del árbol de diseño, resolviendo las dependencias entre decisiones una por una.

## Reglas

- Formula las preguntas **una a la vez** — nunca en lista.
- Para cada pregunta, proporciona tu **respuesta recomendada** basada en lo que sabes del contexto y del código, y dilo así: "Recomiendo X porque Y. ¿Confirmas o prefieres otra cosa?".
- Si una pregunta se puede responder explorando el código fuente, **explóralo primero** y respóndela tú mismo sin preguntarle al usuario; solo informa lo que encontraste.
- Recorre cada rama del árbol de decisiones hasta alcanzar un entendimiento completo; una respuesta suele abrir la siguiente pregunta.
- Si el usuario dice "no aplica" o "no sé", registra la incertidumbre (candidata a *duda abierta*) y avanza.
- Si detectas inconsistencias entre respuestas previas, señálalas y pide aclaración antes de seguir.
- Cierra cuando puedas enunciar el diseño completo sin huecos; resume las decisiones tomadas y las dudas que quedaron abiertas.

## Bloques sugeridos para diseño de software

Salta los que claramente no apliquen; adapta el vocabulario al stack declarado en `.claude/timonel.config.json` y al `CLAUDE.md` del consumidor.

| Bloque | Qué resolver |
| --- | --- |
| A. Contexto y alcance | Motivación, apps/libs/módulos afectados, alcance Backend/Frontend/Full-stack, referencia a issue, prioridad y plazo |
| B. Requisitos funcionales | Casos de uso (actor + acción + resultado), reglas de negocio, flujos alternativos y de error, casos límite, estados y transiciones si es workflow |
| C. Requisitos no funcionales | Volumen, rendimiento, disponibilidad, seguridad/compliance, soporte móvil |
| D. Modelo de datos | Interfaces compartidas nuevas o modificadas, esquemas/discriminadores, migraciones, índices |
| E. API | Endpoints (método + ruta), request/response, validaciones, permiso y datos de sesión que consume |
| F. Arquitectura backend | Responsabilidad por capa, base a extender o caso de uso independiente, módulos nuevos, servicios externos con variante de desarrollo, caché/auditoría/push |
| G. Frontend | Estado (store raíz vs store del módulo), containers/componentes, facade, HTTP e interceptores, rutas/guards/permisos, componentes reutilizados, estados de UI (loading, empty, error) |
| H. Seguridad | Permisos y guard, aislamiento multi-tenant, datos sensibles, auditoría |
| I. Pruebas | Unitarias por capa, integración, cobertura objetivo, escenarios críticos |
| J. Despliegue | Retrocompatibilidad y orden de deploy, migraciones, feature flags, impacto en build móvil |
