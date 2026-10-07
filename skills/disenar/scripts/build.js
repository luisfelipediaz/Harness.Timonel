// Convierte las capturas en artboards .dc.html y los empaqueta en el editor del canvas.
// Uso: node build.js <canvas.config.json>
const fs = require('fs');
const path = require('path');

const CFG_PATH = path.resolve(process.argv[2] || 'canvas.config.json');
const cfg = JSON.parse(fs.readFileSync(CFG_PATH, 'utf8'));
const BASE = path.dirname(CFG_PATH);
const OUT = path.join(BASE, 'out');
const SRC = fs.readFileSync(path.resolve(BASE, cfg.src), 'utf8');
const meta = JSON.parse(fs.readFileSync(path.join(OUT, 'meta.json'), 'utf8'));
const docs = JSON.parse(fs.readFileSync(path.join(OUT, 'docs.json'), 'utf8'));
const DW = cfg.desktop?.w ?? 1440, DH = cfg.desktop?.h ?? 900;
const MW = cfg.mobile?.w ?? 390, MH = cfg.mobile?.h ?? 844;
const DOC_W = cfg.doc_width ?? 1240;
const COLS = 4, GAP_X = 120, GAP_Y = 260;

// --- CSS: el tema deja de seguir al sistema y pasa a ser la prop del artboard ---
function dropBlock(css, opener) {
  const i = css.indexOf(opener);
  if (i < 0) return css;
  let depth = 0, j = i + opener.length - 1;
  for (; j < css.length; j++) {
    if (css[j] === '{') depth++;
    else if (css[j] === '}' && --depth === 0) break;
  }
  return css.slice(0, i) + css.slice(j + 1);
}
let css = SRC.match(/<style>([\s\S]*?)<\/style>/)[1];
css = dropBlock(css, '@media (prefers-color-scheme: dark){');
css = css.replace(':root[data-theme="dark"]{', '.root.theme-dark{');
css = css.replace(/(^|\n)body\{/, '$1.root{');
if (/prefers-color-scheme: dark|\[data-theme="dark"\]/.test(css)) throw new Error('quedó un selector de tema del sistema en el CSS');

const artboardCss = `
html,body{margin:0}
.root{min-height:100%;box-sizing:border-box;padding:0;background:var(--bg);color:var(--ink)}
.root > .frame{width:100%!important;max-width:none!important;height:100%!important;border-radius:0!important;box-shadow:none!important}
.root.doc{padding:40px 48px 48px}
.root.doc .sec{margin-top:0}
.root.doc .doc-head{padding-block:0 24px}
.runref{display:inline-flex;align-items:center;min-height:24px;padding:2px 8px;border-radius:4px;background:var(--pri-50);color:var(--pri-t);font:500 12px/1.4 var(--f-body);white-space:nowrap}
${cfg.extra_css || ''}
`;
const props = (w, h) => JSON.stringify({
  theme: { editor: 'enum', options: ['light', 'dark'], default: 'light', section: 'Tema' },
  $preview: { width: w, height: h },
}).replace(/'/g, '&#39;');

// Un solo <helmet> por artboard: el editor ignora los que vienen después del primero.
function artboard(body, w, h, extra = '') {
  if (/\{\{|<script/i.test(body)) throw new Error('el cuerpo trae {{ o <script>');
  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  ${cfg.fonts || ''}
  <style>
${css}
${artboardCss}
  </style>
</helmet>
<div class="root ${extra} theme-{{theme}}" style="width: ${w}px; height: ${h}px;">
${body}
</div>
</x-dc>
<script data-dc-script data-props='${props(w, h)}'>
class Component extends DCLogic {
  renderVals() {
    return { theme: this.props.theme ?? 'light' };
  }
}
</script>
</body>
</html>
`;
}

// --- Documentación: cada botón de escenario nombra el artboard que lo muestra ---
const byPreset = Object.assign({}, cfg.preset_titles || {});
[...meta.desktop, ...meta.mobile].forEach(a => { if (a.preset && !byPreset[a.preset]) byPreset[a.preset] = a.title; });
function docBody(html) {
  const out = html.replace(/<button[^>]*\sdata-p="([^"]+)"[^>]*>[\s\S]*?<\/button>/g, (_, k) => {
    if (!byPreset[k]) throw new Error('escenario sin artboard: ' + k);
    return `<span class="runref">→ ${byPreset[k]}</span>`;
  });
  if (/data-p=/.test(out)) throw new Error('quedó un data-p en la documentación');
  return (cfg.doc_replacements || []).reduce((s, [a, b]) => s.split(a).join(b), out).replace(/\{\{/g, '{ {');
}

// --- Artboards, notas y páginas ---
const files = {}, artboards = [], annotations = [];
for (const p of cfg.pages) {
  const list = meta.desktop.filter(a => a.page === p.id);
  if (!list.length) throw new Error('página sin artboards: ' + p.id);
  list.forEach((a, i) => {
    files[a.file + '.dc.html'] = artboard(fs.readFileSync(path.join(OUT, a.file + '.html'), 'utf8'), DW, DH);
    artboards.push({ file: a.file + '.dc.html', title: a.title, x: (i % COLS) * (DW + GAP_X), y: Math.floor(i / COLS) * (DH + GAP_Y), w: DW, h: DH, page: 'page-' + p.id });
  });
  if (p.note) annotations.push({ id: 'nota-' + p.id, x: COLS * (DW + GAP_X), y: 0, w: 460, page: 'page-' + p.id, text: p.note });
}
const orphan = meta.desktop.find(a => !cfg.pages.some(p => p.id === a.page));
if (orphan) throw new Error('estado con página desconocida: ' + orphan.file);
meta.mobile.forEach((a, i) => {
  files[a.file + '.dc.html'] = artboard(fs.readFileSync(path.join(OUT, a.file + '.html'), 'utf8'), MW, MH);
  artboards.push({ file: a.file + '.dc.html', title: a.title, x: i * (MW + GAP_X), y: 0, w: MW, h: MH, page: 'page-movil' });
});
let y = 0;
for (const d of cfg.docs || []) {
  const H = docs[d.file].h + 96;
  files[d.file + '.dc.html'] = artboard(docBody(docs[d.file].html), DOC_W, H, 'doc');
  artboards.push({ file: d.file + '.dc.html', title: d.title, x: 0, y, w: DOC_W, h: H, page: 'page-documentacion' });
  y += H + 140;
}
const pages = [
  ...(cfg.docs?.length ? [{ id: 'page-documentacion', name: cfg.doc_page || 'Documentación' }] : []),
  ...cfg.pages.map(p => ({ id: 'page-' + p.id, name: p.name })),
  ...(meta.mobile.length ? [{ id: 'page-movil', name: 'Móvil' }] : []),
];
files['canvas.json'] = JSON.stringify({ artboards, annotations, launch: { view: 'canvas', page: pages[0].id }, pages }, null, 2) + '\n';
fs.mkdirSync(path.join(BASE, 'dc'), { recursive: true });
for (const [n, s] of Object.entries(files)) fs.writeFileSync(path.join(BASE, 'dc', n), s);

// --- Empaquetado en el runtime del editor ---
const tpl = fs.readFileSync(path.resolve(BASE, cfg.runtime), 'utf8');
const re = /(<script type="application\/json" id="appifact-doc">\n?)([\s\S]*?)(\n?<\/script>)/;
const m = tpl.match(re);
if (!m) throw new Error('el runtime no trae el bloque appifact-doc: no es un canvas');
const oldTitle = JSON.parse(m[2]).title;
const json = JSON.stringify({ title: cfg.title, content: { files }, comments: [] }).replace(/</g, '\\u003c').replace(/>/g, '\\u003e');
let html = tpl.slice(0, m.index) + m[1] + json + m[3] + tpl.slice(m.index + m[0].length);
html = html.split(`<title>${oldTitle}</title>`).join(`<title>${cfg.title}</title>`).split(`Design canvas (${oldTitle})`).join(`Design canvas (${cfg.title})`);
const DEST = path.resolve(BASE, cfg.dest);
fs.writeFileSync(DEST, html);

const back = JSON.parse(html.match(re)[2]);
if (Object.keys(back.content.files).length !== Object.keys(files).length || back.title !== cfg.title) throw new Error('el bloque del documento no se lee completo');
const mb = html.length / 1e6;
if (mb > 16) throw new Error(`el canvas pesa ${mb.toFixed(2)} MB; el límite es 16`);
console.log('ok', artboards.length, 'artboards,', pages.length, 'páginas,', mb.toFixed(2), 'MB →', DEST);
