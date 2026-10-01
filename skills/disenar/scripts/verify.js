// Abre el canvas empaquetado en el editor y fotografía la vista inicial y cada página.
// Uso: node verify.js <canvas.config.json>
const fs = require('fs');
const path = require('path');

const CFG_PATH = path.resolve(process.argv[2] || 'canvas.config.json');
const cfg = JSON.parse(fs.readFileSync(CFG_PATH, 'utf8'));
const BASE = path.dirname(CFG_PATH);
// playwright-core se instala en la carpeta de trabajo, no junto al skill.
const { chromium } = require(require.resolve('playwright-core', { paths: [BASE, process.cwd()] }));
const OUT = path.join(BASE, 'out');
const CHROME = cfg.chrome || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + path.resolve(BASE, cfg.dest));
  await page.waitForTimeout(5000);
  await page.screenshot({ path: path.join(OUT, '_canvas.png') });

  const names = [cfg.doc_page || 'Documentación', ...cfg.pages.map(p => p.name), 'Móvil'];
  const shots = [];
  for (const [i, name] of names.entries()) {
    const menu = await page.$('text=/\\d+ pages/');
    if (!menu) break;
    await menu.click();
    await page.waitForTimeout(500);
    const item = await page.$(`text="${name}"`);
    if (!item) { await page.keyboard.press('Escape'); continue; }
    await item.click();
    await page.waitForTimeout(4000);
    const file = `_pagina-${i}.png`;
    await page.screenshot({ path: path.join(OUT, file) });
    shots.push(file);
  }
  await browser.close();
  if (errors.length) { console.error('Errores del editor:', errors.slice(0, 5)); process.exit(1); }
  console.log('ok', ['_canvas.png', ...shots].join(' '));
})().catch(e => { console.error(e); process.exit(1); });
