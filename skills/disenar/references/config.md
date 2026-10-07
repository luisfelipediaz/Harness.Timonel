# canvas.config.json

Las rutas se resuelven contra la carpeta del archivo de configuración.

```json
{
  "title": "Miembros y accesos",
  "src": "prototipo.html",
  "runtime": "/ruta/al/html/del/canvas/leido.html",
  "dest": "canvas.html",
  "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "mermaid": true,
  "fonts": "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=…&display=swap\">",
  "desktop": { "w": 1440, "h": 900 },
  "mobile": { "w": 390, "h": 844 },
  "doc_width": 1240,
  "doc_page": "Documentación",
  "pages": [
    { "id": "entrar", "name": "Entrar y miembros", "note": "Nota adhesiva opcional a la derecha de la página." }
  ],
  "states": [
    { "file": "Miembros", "title": "Miembros", "page": "entrar", "preset": null, "steps": [] },
    { "file": "Cargando", "title": "Cargando", "page": "entrar", "preset": "slow", "steps": [], "early": true },
    { "file": "AltaHecho", "title": "Agregar · hecho", "page": "agregar", "preset": "addok", "steps": ["#fl-confirm"], "wait": 900 }
  ],
  "mobile_states": [
    { "file": "MovilMiembros", "title": "Móvil · Miembros", "preset": null, "steps": [] }
  ],
  "preset_titles": { "mobile": "Móvil · Miembros" },
  "docs": [
    { "file": "Portada", "title": "Portada", "selectors": [".doc-head", ".facts"] },
    { "file": "Flujos", "title": "Flujos completos", "selectors": ["#flujos"] },
    { "file": "Matriz", "title": "Matriz de combinaciones", "selectors": ["#combinaciones"] }
  ],
  "doc_replacements": [["texto del prototipo", "texto en el canvas"]],
  "extra_css": ""
}
```

| Campo | Qué es |
|---|---|
| `runtime` | HTML completo de un canvas publicado, tal como lo guarda `Artifact` `read`. Aporta el editor. |
| `states[].preset` | `data-p` que lleva al estado; `null` usa `#lab-reset`. |
| `states[].steps` | Selectores que se clican en orden después del escenario. |
| `states[].wait` | Espera extra en ms tras los pasos (animaciones, respuestas simuladas). |
| `states[].early` | Captura a los 350 ms, para estados de carga. |
| `states[].page` | `id` de una entrada de `pages`; todas las páginas deben tener al menos un estado. |
| `preset_titles` | Título de artboard para escenarios de la matriz que no tienen estado propio. |
| `docs[].selectors` | Elementos que se concatenan en un artboard de documentación. |
| `doc_replacements` | Sustituciones de texto en la documentación, para frases que solo tienen sentido en el prototipo. |
| `extra_css` | CSS adicional que se agrega a cada artboard. |

Cada `data-p` que aparezca en la documentación necesita un artboard, ya sea porque un estado usa ese
`preset` o porque figura en `preset_titles`; si no, `build.js` se detiene y lo nombra.
