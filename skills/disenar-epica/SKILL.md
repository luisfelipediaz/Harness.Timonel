---
name: disenar-epica
description: Diseña una épica completa de front en el prototipo del proyecto, con cada flujo y cada variante pensados desde el perfil que usa la pantalla, y cierra con barridos e2e por perfil repetidos hasta que no queden hallazgos de diseño ni de UI. Usa agentes en paralelo. Úsalo cuando el usuario pida «diseña la épica N en el prototipo», «agrega la épica N al prototipo», «diseña todos los flujos de…» o un barrido e2e de diseño de una épica. Para entregar un diseño suelto como canvas, usa `disenar`.
argument-hint: "<número de la épica>"
---

# disenar-epica

Diseña la épica **#$ARGUMENTS** en el prototipo del proyecto. Si no viene número, se pregunta.

## Rol

Experto en UX y UI: Material 3 en su versión vigente, tendencias de UI llamativas e intuitivas, y diseño orientado a la psicología del usuario. Cada pantalla se diseña desde la cara de quien la usa (su contexto, su dispositivo, lo que sabe y lo que teme) para que ese perfil la encuentre obvia. Detallado, cuidadoso y profesional: **ningún flujo sin diseñar y ninguna variante sin su estado**.

## Parámetros de entrada

| Parámetro | De dónde sale | Si falta |
| --- | --- | --- |
| Épica | `$ARGUMENTS` | Se pregunta |
| Prototipo publicado | URL de un artifact (`claude.ai/artifact/…`) que da el usuario | Se pregunta antes de diseñar (ver abajo) |
| Carpeta del prototipo | `CLAUDE.md` o docs de diseño del consumidor | Se pregunta |
| Sistema de diseño | Tokens, tipografías y componentes del consumidor | Se decide y se declara en la nota |
| Docs de diseño | Carpeta de notas, inventario de pantallas e investigación del consumidor | Se pregunta dónde van |

## 0. El artifact del prototipo

Antes de diseñar se pregunta al usuario: **«¿El prototipo ya está publicado como artifact? Pásame la URL.»**

- **Hay URL**: `Artifact` con `action: "read"` sobre ella y `action: "list"`, `scope: "files"` para ver sus archivos. Toda publicación pasa esa `url`: nunca se crea otro artifact, ni copia ni vista previa de una rama. Desde una rama el diseño se mira en local (servidor http + Playwright); se publica sobre la URL después de integrar el PR en la rama base, solo con los archivos que cambiaron.
- **No hay**: se pregunta si crear uno (uno solo, cuya URL se anota en las docs de diseño del consumidor) o trabajar solo en local. No se publica nada sin esa respuesta.

## 1. Entender la épica

- `gh issue view $ARGUMENTS` y cada HU hija (criterios, prioridad). La investigación previa del consumidor que la respalde.
- Lista de **perfiles** que tocan la épica, con su dispositivo principal y su objetivo.
- Matriz **perfil × flujo × estado**: vacío, cargando, con datos, error, sin permiso, límite, cada fase o momento del proceso, celular y computador, claro y oscuro. Esa matriz es el contrato de «nada sin diseñar».
- Lo que el diseño decide sin respaldo del negocio va como pregunta abierta para quien decide, no se presenta como hecho.

## 2. Investigación UX

Un subagente `general-purpose` en opus, con WebSearch y WebFetch: productos reales del dominio, patrones (NN/g, WCAG 2.2, Material, sistemas de diseño públicos) con URL, y «sin verificar» en lo que no abrió. El resultado queda en un archivo de las docs de diseño del consumidor.

## 3. Diseño en el prototipo

- Rama en un worktree aislado; nunca se cambia de rama en el checkout principal.
- Se respetan las convenciones del prototipo del consumidor (un archivo por pantalla, índice, notas por estado). Para tocar una pantalla se abre solo su archivo.
- Piezas compartidas primero (cabeceras, filas, avisos, componentes de la épica), solo con los tokens del sistema de diseño; después las áreas.
- **Agentes en paralelo por área**, en opus, cada uno dueño de sus archivos para no pisarse; el coordinador integra lo compartido. Brief de cada uno: perfil, flujos, estados de la matriz que le tocan, datos canónicos y archivos que puede tocar.
- **Datos canónicos** únicos para toda la épica (nombres, cifras, resultados): lo que ve un perfil coincide con lo que ve otro.
- Entradas desde lo que ya existe (menús, pantallas actuales) y el mapa de flujos actualizado.
- Responsive pensado por tamaño: celular, tablet y computador por separado, no el diseño de celular estirado.

## 4. Barrido e2e hasta cerrar todo

Se repite **sin límite de rondas** hasta una ronda sin hallazgos altos ni medios:

1. **Auditores en paralelo (opus), uno por perfil más uno de sistema visual.** Cada uno recorre el flujo completo de punta a punta como ese perfil, en celular y computador, claro y oscuro, y reporta cada hallazgo con pantalla, severidad, regla y propuesta. Revisa usabilidad (heurísticas de Nielsen), proporciones y espaciado de Material, jerarquía, consistencia de datos y textos entre perfiles, accesibilidad (contraste, foco, área táctil de WCAG 2.5.8), estados faltantes y enlaces rotos.
2. **Barrido automático** con Playwright: errores de consola, desbordes, enlaces rotos y área táctil efectiva (toque emulado y `elementFromPoint`), en los dos tamaños y los dos temas. Se mide con el DOM; las capturas se recortan al componente.
3. **Correctores en paralelo por área**, con los hallazgos de esa área. Después, la siguiente ronda.

Los hallazgos bajos que no cambian un flujo pueden ir a un issue de pulido con sub-issues por área; se dice explícitamente en el reporte.

## 5. Cierre

- Nota de diseño con fecha: cómo está armado, decisiones por perfil, datos canónicos, decisiones por confirmar, rondas del barrido y pendientes.
- Inventario de pantallas del consumidor actualizado.
- PR a la rama base. Tras integrarlo, se republica sobre la URL del paso 0 (si la hay) con solo los archivos que cambiaron.

## Reporte de salida

```
Épica: #<N> — <título>
Artifact: <URL> | solo local
Perfiles: <lista>
Pantallas y estados: <n> (por perfil: <perfil> <n>, …)
Rondas e2e: <n> de auditoría, <n> de corrección; última ronda sin altos ni medios: sí | no
Pendientes: <issues de pulido y preguntas abiertas>
PR: <URL>
```
