#!/usr/bin/env python3
"""Render an Atlas SPZ from given cameras with Spark in headless Chromium.

Usage: python3 tools/view_splats.py SCENE.spz CAMERAS.json OUT_DIR
  CAMERAS.json: {"name": {"position": [x,y,z], "quaternion": [x,y,z,w]}, ...}  (rub world, as Atlas returns)
Needs three@0.180 and @sparkjsdev/spark@2.4.0 unpacked in ~/.cache/storm-terrace-spark (npm pack).
"""
import base64, functools, http.server, json, os, shutil, subprocess, sys, tempfile, threading
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CACHE = Path.home() / ".cache" / "storm-terrace-spark"


def ensure_libs():
    if not (CACHE / "package" / "dist" / "spark.module.js").exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "pack", "@sparkjsdev/spark@2.4.0", "--silent"], cwd=CACHE, check=True)
        subprocess.run("tar xzf sparkjsdev-spark-2.4.0.tgz", shell=True, cwd=CACHE, check=True)
    if not (CACHE / "three180" / "package" / "build" / "three.module.js").exists():
        subprocess.run(["npm", "pack", "three@0.180.0", "--silent"], cwd=CACHE, check=True)
        (CACHE / "three180").mkdir(exist_ok=True)
        subprocess.run(["tar", "xzf", "three-0.180.0.tgz", "-C", "three180"], cwd=CACHE, check=True)


JS = r"""
const { chromium } = require('playwright');
const fs = require('fs');
const [port, camsPath, outDir] = process.argv.slice(2);
const cams = JSON.parse(fs.readFileSync(camsPath, 'utf8'));
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => console.error('pageerror:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/view_splats.html`);
  await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
  for (const [name, cam] of Object.entries(cams)) {
    const url = await page.evaluate(c => window.shoot(c), cam);
    fs.writeFileSync(`${outDir}/${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
    console.log('shot', name);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def main():
    spz, cams, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    ensure_libs()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        os.symlink(CACHE / "three180" / "package", tmp / "three")
        os.symlink(CACHE / "package", tmp / "spark")
        os.symlink(spz, tmp / "scene.spz")
        shutil.copy(TOOLS / "view_splats.html", tmp / "view_splats.html")
        (tmp / "shoot.cjs").write_text(JS)
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp))
        h.log_message = lambda *a: None
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            subprocess.run(["node", str(tmp / "shoot.cjs"), str(srv.server_address[1]), str(cams), str(out)],
                           check=True, env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()})
        finally:
            srv.shutdown()


if __name__ == "__main__":
    main()
