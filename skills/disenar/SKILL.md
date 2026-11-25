---
name: disenar
description: Diseña una interfaz completa y la entrega como prototipo interactivo publicado como artifact, con cada pantalla en su flujo completo y cada estado reproducible desde una matriz de escenarios, partiendo de investigación de tendencias y del sistema de diseño del proyecto. Úsalo cuando el usuario pida «diseñar», «proponer un diseño», «un prototipo», pantallas con todos sus estados o un reto de diseño de front.
---

# disenar

Entrega: un **prototipo interactivo publicado como artifact**. La app vive en un marco, un
laboratorio fuera del marco lleva a cualquier estado, y la matriz de combinaciones reproduce cada
estado de cada pantalla con un clic. La misma página trae los flujos, los controles, las tendencias
y las brechas. Lo que se revisa es lo que se navega: no hay una copia congelada aparte.

## Proceso

### 1. Contexto antes de dibujar

- Sistema de diseño: tokens, tipografías, chrome, componentes y capturas del proyecto (CLAUDE.md,
  archivos de tema, memoria). Si el proyecto no tiene uno, se decide y se declara.
- Dominio real: las operaciones que existen, sus reglas y sus mensajes exactos (código, contratos,
  ADR). Nada de pantallas para operaciones que no existen: lo que falta va a «Brechas».
- Prototipo existente: pregunta si el diseño ya está publicado como artifact y pide la URL. Si la
  hay, `Artifact` con `action: "read"` sobre ella y se diseña sobre lo que ya existe.

### 2. Investigación de tendencias

Lanza un subagente `general-purpose` en segundo plano con WebSearch/WebFetch sobre los referentes del
tipo de producto y las guías de UX pertinentes (NN/g, WCAG 2.2, sistemas de diseño públicos). Pide
patrones con URL, tendencias, anti-patrones y recomendaciones para las operaciones concretas, y que
marque «sin verificar» lo que no abrió. En paralelo, otro subagente extrae los tokens del sistema de
diseño con valores exactos.

### 3. Prototipo interactivo

Carga `frontend-design` y `artifact-design` y escribe el prototipo según el contrato de
[references/prototipo.md](references/prototipo.md). Lo esencial:

- La app vive en `#frame > #app`, con un laboratorio de escenarios fuera del marco.
- Cada combinación relevante es un escenario reproducible (`button[data-p="clave"]` en la matriz).
- Ninguna pantalla sin salida: cada estado de error, vacío, carga y resultado tiene su acción.
- Documentación en secciones con id: portada, flujos (`pre.mermaid`), matriz, controles,
  tendencias, brechas.

### 4. Barrido

Valida la sintaxis del script con `node` y corre el barrido en una carpeta del scratchpad:

```bash
PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
npm init -y >/dev/null && npm i playwright-core@1 >/dev/null
node "$PLUGIN_ROOT/skills/disenar/scripts/barrido.js" <prototipo>.html
```

`barrido.js` abre el prototipo en Chrome headless, recorre cada `button[data-p]` en escritorio y en
móvil, y falla si alguno produce errores de JavaScript. Imprime los escenarios cuyo `#frame` quedó
idéntico a otro: o el escenario no hace lo que dice, o sobra. Las capturas quedan en `barrido/` y
no se cargan en la sesión salvo para mirar una pantalla concreta.

Mira con Playwright los estados que el barrido no prueba por sí solo: tema oscuro, foco de teclado
y los pasos posteriores a un escenario (confirmar, abrir un menú).

### 5. Publicación

Publica el prototipo con `Artifact`:

- Si el paso 1 dio una URL, publica sobre ella: nunca se crea otro artifact, ni copia ni versión
  de prueba.
- Si no, publica uno nuevo con `icon` genérico y `description` de una frase.

### 6. Entrega

Da el enlace y resume: pantallas y escenarios de la matriz, qué cubren los flujos, las brechas del
backend que cambian lo que ve el usuario y lo que no se verificó.

## Reglas

- Textos del usuario en su idioma y con los mensajes reales del sistema, nunca inventados.
- Estados derivados de datos se diseñan con sus tres respuestas: hay, no hay y no se sabe (error).
- La página publicada pesa 16 MB o menos.
