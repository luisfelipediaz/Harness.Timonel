# Contrato del prototipo

`barrido.js` y quien revisa el diseño dependen de estas piezas. El resto del diseño es libre.

## Estructura

```html
<title>Nombre del producto</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/…">
<style>/* tokens, tema y estilos */</style>

<div class="wrap">
  <header class="doc-head">…</header>          <!-- portada y datos clave -->
  <section class="sec" id="prototipo">
    <div class="lab">                          <!-- laboratorio de escenarios, fuera del marco -->
      <select id="sc-device"><option value="desktop">…</option><option value="mobile">…</option></select>
      <button id="lab-reset">Reiniciar</button>
      …otros selectores de escenario…
    </div>
    <div class="frame" id="frame"><div id="app"></div></div>
  </section>
  <section class="sec" id="flujos">…<pre class="mermaid">flowchart TD …</pre>…</section>
  <section class="sec" id="combinaciones">…tabla con <button data-p="clave">Reproducir</button>…</section>
  <section class="sec" id="controles">…</section>
  <section class="sec" id="tendencias">…</section>
  <section class="sec" id="brechas">…</section>
</div>
<script>/* la app */</script>
```

Los diagramas `pre.mermaid` se dibujan en la página con mermaid desde un CDN permitido por
`artifact-design`, con versión exacta.

## CSS

- Tokens de color en `:root` y tema oscuro según el contrato de `artifact-design`.
- `.frame` tiene `container-type: inline-size` y la versión móvil se resuelve con
  `@container (max-width: …)`, porque el móvil mide 390 px dentro del marco y no cambia el viewport.
- `.frame.mobile` es la variante de 390 px que activa `#sc-device`.

## Escenarios

- `#lab-reset` deja la app en su estado inicial poblado.
- Cada `button[data-p="clave"]` de la matriz reinicia y lleva la app a un estado exacto, esperando
  sus propias transiciones. Debe quedar quieto antes de 2,5 s.
- Clic en un escenario lleva al marco: quien revisa ve el estado sin buscarlo.
- Los pasos posteriores (confirmar, abrir un menú) se hacen con clics sobre selectores estables:
  `id` en los botones de confirmación (`#fl-confirm`), `data-a`/`data-id` en las acciones.
- La página no produce errores de JavaScript en ningún escenario: `barrido.js` falla si los hay.

## Cobertura

- Cada pantalla tiene su flujo completo: entrada, formulario, vista previa, resultado y todas las
  respuestas de error, cada una con una salida.
- Estados de lectura: cargando, error (nunca presentado como vacío), vacío, vacío por filtro, parcial.
- Permisos: la vista de quien no puede actuar, con la razón visible.
- Móvil: al menos la lista principal, un detalle, un formulario y una confirmación.
