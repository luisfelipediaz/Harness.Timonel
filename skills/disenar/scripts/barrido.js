// Recorre cada escenario de la matriz (button[data-p]) en escritorio y móvil.
// Uso: node barrido.js <prototipo.html>   (CHROME=<ruta> cambia el navegador)
// Exit 0: sin errores. Exit 1: errores de JS, un #frame vacío, o ningún escenario que barrer.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const SRC = path.resolve(process.argv[2] || 'prototipo.html');
// playwright-core se instala en la carpeta de trabajo, no junto al skill.
const { chromium } = require(require.resolve('playwright-core', { paths: [process.cwd()] }));
const OUT = path.resolve('barrido');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
// Contrato de references/prototipo.md: un escenario queda quieto antes de 2,5 s.
const QUIETO_MS = 2600;

async function escenario(page, clave, dispositivo, errores) {
  await page.goto('file://' + SRC, { waitUntil: 'load' });
  await page.click(`button[data-p="${clave}"]`);
  await page.waitForTimeout(QUIETO_MS);
  if (dispositivo === 'mobile') {
    await page.selectOption('#sc-device', 'mobile');
    await page.waitForTimeout(300);
  }
  const marco = page.locator('#frame');
  const html = await marco.evaluate(el => el.outerHTML);
  // Un marco sin alto no se puede fotografiar: Playwright espera que sea visible hasta agotar el timeout.
  const caja = await marco.boundingBox();
  if (!caja || caja.height === 0) errores.push(`${dispositivo}/${clave}: #frame quedó vacío o invisible`);
  else await marco.screenshot({ path: path.join(OUT, `${dispositivo}-${clave}.png`) });
  return crypto.createHash('md5').update(html).digest('hex');
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROME });
  const page = await browser.newPage({ reducedMotion: 'reduce', viewport: { width: 1440, height: 1000 } });
  let actual = '';
  const errores = [];
  page.on('pageerror', e => errores.push(`${actual}: ${e.message}`));

  await page.goto('file://' + SRC, { waitUntil: 'load' });
  const claves = [...new Set(await page.$$eval('button[data-p]', bs => bs.map(b => b.dataset.p)))];
  if (!claves.length) {
    await browser.close();
    console.error('No hay button[data-p] en la página: no hay escenarios que barrer.');
    process.exit(1);
  }

  const duplicados = [];
  for (const dispositivo of ['desktop', 'mobile']) {
    const vistos = new Map();
    for (const clave of claves) {
      actual = `${dispositivo}/${clave}`;
      const hash = await escenario(page, clave, dispositivo, errores);
      if (vistos.has(hash)) duplicados.push(`${actual} = ${dispositivo}/${vistos.get(hash)}`);
      else vistos.set(hash, clave);
    }
  }
  await browser.close();

  console.log(`${claves.length} escenarios × 2 dispositivos; capturas en ${OUT}`);
  if (duplicados.length) console.log('Mismo #frame (el escenario no hace lo que dice, o sobra):\n  ' + duplicados.join('\n  '));
  if (errores.length) {
    console.error('Errores:\n  ' + errores.join('\n  '));
    process.exit(1);
  }
})().catch(e => { console.error(e); process.exit(1); });
