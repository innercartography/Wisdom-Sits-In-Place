// Headless three.js renderer for the Storm Terrace blockout.
// Called by render_views.py:  node render_views.cjs <serve_dir> <port> <views.json> <out_dir>
// Writes <name>_layout.png (colour) and <name>_depth.rgb24 (raw RGB, z-depth in mm as 24-bit int).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const [serveDir, port, viewsPath, outDir] = process.argv.slice(2);
const job = JSON.parse(fs.readFileSync(viewsPath, 'utf8'));

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 64, height: 64 } });
  page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  page.on('pageerror', e => console.error('pageerror:', e.message));
  await page.goto(`http://127.0.0.1:${port}/render.html`);
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
  for (const v of job.views) {
    const res = await page.evaluate(([v, W, H, vfov]) => window.renderView(v, W, H, vfov), [v, job.width, job.height, job.vfov]);
    fs.writeFileSync(path.join(outDir, `${v.name}_layout.png`), Buffer.from(res.color.split(',')[1], 'base64'));
    fs.writeFileSync(path.join(outDir, `${v.name}_depth.rgb24`), Buffer.from(res.depth, 'base64'));
    fs.writeFileSync(path.join(outDir, `${v.name}_trees.u8`), Buffer.from(res.trees, 'base64'));
    console.log('rendered', v.name);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
