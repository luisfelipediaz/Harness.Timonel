// Congela cada estado del prototipo como DOM estático, más las secciones de documentación.
// Uso: node capture.js <canvas.config.json>
const fs = require('fs');
const path = require('path');

const CFG_PATH = path.resolve(process.argv[2] || 'canvas.config.json');
const cfg = JSON.parse(fs.readFileSync(CFG_PATH, 'utf8'));
const BASE = path.dirname(CFG_PATH);
// playwright-core se instala en la carpeta de trabajo, no junto al skill.
const { chromium } = require(require.resolve('playwright-core', { paths: [BASE, process.cwd()] }));
const OUT = path.join(BASE, 'out');
fs.mkdirSync(OUT, { recursive: true });
const SRC = 'file://' + path.resolve(BASE, cfg.src);
const CHROME = cfg.chrome || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

async function load(page) {
  await page.goto(SRC, { waitUntil: 'load' });
  await page.waitForTimeout(900);
}

async function reach(page, s, mobile) {
  if (s.preset) {
    await page.click(`button[data-p="${s.preset}"]`);
    await page.waitForTimeout(s.early ? 350 : 2600);
  } else {
    await page.click('#lab-reset');
    await page.waitForTimeout(1000);
  }
  if (mobile) {
    await page.selectOption('#sc-device', 'mobile');
    await page.waitForTimeout(300);
  }
  for (const sel of s.steps || []) {
    const el = await page.$(sel);
    if (!el) throw new Error(`${s.file}: no encontré ${sel}`);
    await el.click();
    await page.waitForTimeout(500);
  }
  if (s.wait) await page.waitForTimeout(s.wait);
}

async function grab(page, file) {
  const html = await page.$eval('#frame', el => el.outerHTML);
  fs.writeFileSync(path.join(OUT, file + '.html'), html);
  await page.locator('#frame').screenshot({ path: path.join(OUT, file + '.png') });
}

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  const ctx = await browser.newContext({ reducedMotion: 'reduce', colorScheme: 'light', viewport: { width: 1440, height: 1000 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));

  const meta = { desktop: [], mobile: [] };
  for (const s of cfg.states) {
    await load(page); await reach(page, s, false); await grab(page, s.file);
    meta.desktop.push({ file: s.file, title: s.title, page: s.page, preset: s.preset || null });
  }
  for (const s of cfg.mobile_states || []) {
    await load(page); await reach(page, s, true); await grab(page, s.file);
    meta.mobile.push({ file: s.file, title: s.title, preset: s.preset || null });
  }

  await load(page);
  if (cfg.mermaid) {
    await page.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js' });
    await page.evaluate(async () => {
      window.mermaid.initialize({ startOnLoad: false, theme: 'neutral', fontFamily: 'Inter, sans-serif' });
      await window.mermaid.run({ querySelector: 'pre.mermaid' });
    });
    await page.waitForTimeout(600);
  }
  const docs = {};
  for (const d of cfg.docs || []) {
    docs[d.file] = await page.evaluate(sels => {
      const els = sels.map(s => document.querySelector(s));
      if (els.some(e => !e)) return null;
      return { html: els.map(e => e.outerHTML).join(''), h: Math.ceil(els.reduce((h, e) => h + e.getBoundingClientRect().height, 0)) + 24 };
    }, d.selectors);
    if (!docs[d.file]) throw new Error(`${d.file}: falta alguno de ${d.selectors.join(', ')}`);
  }

  fs.writeFileSync(path.join(OUT, 'docs.json'), JSON.stringify(docs));
  fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));
  await browser.close();
  if (errors.length) { console.error('Errores de la página:', errors); process.exit(1); }
  console.log('ok', meta.desktop.length, 'escritorio,', meta.mobile.length, 'móvil,', Object.keys(docs).length, 'documentos');
})().catch(e => { console.error(e); process.exit(1); });
