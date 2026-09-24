---
name: disenar
description: Diseña una interfaz completa y la entrega como canvas de Claude Design (artboards en páginas, con zoom y tema claro/oscuro), partiendo de investigación de tendencias, del sistema de diseño del proyecto y de un prototipo interactivo donde cada pantalla tiene su flujo completo. Úsalo cuando el usuario pida «diseñar», «proponer un diseño», «un canvas», «artboards», pantallas con todos sus estados o un reto de diseño de front.
---

# disenar

Entrega: un **canvas de Claude Design** publicado como artifact. Cada estado de cada pantalla es un
artboard, los artboards se agrupan en páginas por flujo, y una página de Documentación trae los
flujos, la matriz de combinaciones, el inventario de controles, las tendencias y las brechas.
El canvas nace de un prototipo interactivo que se congela estado por estado.

## Proceso

### 1. Contexto antes de dibujar

- Sistema de diseño: tokens, tipografías, chrome, componentes y capturas del proyecto (CLAUDE.md,
  archivos de tema, memoria). Si el proyecto no tiene uno, se decide y se declara.
- Dominio real: las operaciones que existen, sus reglas y sus mensajes exactos (código, contratos,
  ADR). Nada de pantallas para operaciones que no existen: lo que falta va a «Brechas».

### 2. Investigación de tendencias

Lanza un subagente `general-purpose` en segundo plano con WebSearch/WebFetch sobre los referentes del
tipo de producto y las guías de UX pertinentes (NN/g, WCAG 2.2, sistemas de diseño públicos). Pide
patrones con URL, tendencias, anti-patrones y recomendaciones para las operaciones concretas, y que
marque «sin verificar» lo que no abrió. En paralelo, otro subagente extrae los tokens del sistema de
diseño con valores exactos.

### 3. Prototipo interactivo

Carga `frontend-design` y `artifact-design` y escribe un HTML único que cumpla el contrato de
[references/prototipo.md](references/prototipo.md). Lo esencial:

- La app vive en `#frame > #app`, con un laboratorio de escenarios fuera del marco.
- Cada combinación relevante es un escenario reproducible (`button[data-p="clave"]` en la matriz).
- Ninguna pantalla sin salida: cada estado de error, vacío, carga y resultado tiene su acción.
- Documentación en secciones con id: portada, flujos (`pre.mermaid`), matriz, controles,
  tendencias, brechas.

Valida la sintaxis del script con `node` y míralo una vez con Playwright antes de seguir.

### 4. Runtime del editor

El canvas se empaqueta en el HTML de un canvas ya publicado: su editor y un bloque
`<script type="application/json" id="appifact-doc">` con los archivos `.dc.html` y `canvas.json`.

1. `Artifact` con `action: "list"` y busca un artifact del usuario que sea canvas (su HTML trae el
   comentario README «Design canvas … published from Claude Code»).
2. `Artifact` con `action: "read"` sobre él. El resultado da la ruta del HTML completo guardado y
   el contrato del runtime (por ejemplo `contract 0.1.31`). Esa ruta es el `runtime` de la
   configuración.

### 5. Captura, armado y verificación

Resuelve `PLUGIN_ROOT` y trabaja en una carpeta del scratchpad:

```bash
PLUGIN_ROOT=$(cat .timonel/.plugin-root 2>/dev/null); [ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/*/timonel/*/ | sort -V | tail -1); PLUGIN_ROOT="${PLUGIN_ROOT%/}"
npm init -y >/dev/null && npm i playwright-core@1 >/dev/null
cp <prototipo>.html prototipo.html
# escribir canvas.config.json según references/config.md
node "$PLUGIN_ROOT/skills/disenar/scripts/capture.js" canvas.config.json
node "$PLUGIN_ROOT/skills/disenar/scripts/build.js"   canvas.config.json
node "$PLUGIN_ROOT/skills/disenar/scripts/verify.js"  canvas.config.json
```

- `capture.js` recorre cada escenario en Chrome headless y guarda el DOM de `#frame` y una captura.
  Con `mermaid: true` dibuja los diagramas antes de congelar la documentación.
- `build.js` convierte cada captura en un artboard `.dc.html` con **un solo `<helmet>`** (el editor
  ignora los siguientes), el tema como prop `theme`, y arma `canvas.json` con páginas, notas y
  posiciones. En la documentación, cada botón de escenario pasa a nombrar su artboard.
- `verify.js` abre el canvas empaquetado en el editor y fotografía la vista inicial y cada página.

Revisa las capturas `out/_canvas.png` y `out/_pagina-*.png`: los artboards deben verse con sus
estilos, no como texto plano. Revisa también que no haya capturas idénticas entre estados que
deberían diferir (`md5 -q out/*.html`).

### 6. Publicación

Carga `artifact-capabilities` y publica el `dest` con:

- `capabilities: {"self": {}, "downloads": {}}`: el Save y la descarga del editor.
- `contract`: el mismo del runtime leído en el paso 4.
- `icon` genérico y `description` de una frase.

Si el usuario tiene un canvas existente donde deba ir el diseño, publica sobre esa URL sumando
páginas en lugar de crear uno nuevo: lee su `appifact-doc`, agrega los archivos con un prefijo propio
y conserva sus artboards, notas y comentarios.

### 7. Entrega

Da el enlace del canvas y resume: páginas y número de artboards, qué cubre la documentación, las
brechas del backend que cambian lo que ve el usuario y lo que no se verificó. El prototipo
interactivo puede publicarse aparte como compañero navegable del canvas.

## Reglas

- Un artboard no lleva `<script>` en el cuerpo ni `{{` fuera de las props; `build.js` lo rechaza.
- El canvas completo pesa 16 MB o menos.
- Textos del usuario en su idioma y con los mensajes reales del sistema, nunca inventados.
- Estados derivados de datos se diseñan con sus tres respuestas: hay, no hay y no se sabe (error).
