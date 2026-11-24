#!/usr/bin/env python3
"""Render the blockout from every station camera: colour preview, metric depth and camera JSON.

Uses headless Chromium + three.js (render.html / render_views.cjs). three.js is fetched from
the npm registry into ~/.cache/storm-terrace-three on first run.

Outputs in ../layout/:
  <view>_layout.png      flat-lit colour render of the blockout (check against generated/<view>.png)
  <view>_depth_cm.png    16-bit z-depth in centimetres (0..655 m, clipped), 0 = sky
  <view>_depth.npy       float32 z-depth in metres, NaN = sky (exact, unclipped)
  cameras.json           camera-to-world 4x4 (OpenCV axes: +X right, +Y down, +Z forward) and pinhole
                         intrinsics per view, world frame = site plan (x east, y up, z north, metres)

Usage: python3 tools/render_views.py [width]     (default 1280 -> 1280x720, Atlas's target size)
"""
import functools, http.server, json, os, shutil, subprocess, sys, tempfile, threading
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
W = int(sys.argv[1]) if len(sys.argv) > 1 else 1280
H = round(W * 9 / 16)
HFOV = 90.0
VFOV = float(np.degrees(2 * np.arctan(np.tan(np.radians(HFOV / 2)) * H / W)))
STATIONS = {"A": (0, 1.6, 0), "B": (4, 3.1, 34), "C": (-0.5, -1.4, 22), "D": (9, 1.6, 22), "E": (0, 1.6, 108)}
VIEWS = {"A": "0123", "B": "0123", "C": "02", "D": "023", "E": "0123"}
DIRS = {"0": ("front", 0), "1": ("right", 90), "2": ("back", 180), "3": ("left", 270)}


def three_dir():
    cache = Path.home() / ".cache" / "storm-terrace-three"
    pkg = cache / "package"
    if not (pkg / "build" / "three.module.js").exists():
        cache.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "pack", "three@0.160.0", "--silent"], cwd=cache, check=True)
        subprocess.run(["tar", "xzf", "three-0.160.0.tgz"], cwd=cache, check=True)
    return pkg


def camera(pos, yaw):
    t = np.radians(yaw)
    fwd = np.array([np.sin(t), 0, np.cos(t)])
    right = np.array([np.cos(t), 0, -np.sin(t)])
    c2w = np.eye(4)
    c2w[:3, 0], c2w[:3, 1], c2w[:3, 2], c2w[:3, 3] = right, [0, -1, 0], fwd, pos
    return c2w


def main():
    out = ROOT / "layout"; out.mkdir(exist_ok=True)
    views = [{"name": f"{s}{d}_{DIRS[d][0]}", "pos": list(STATIONS[s]), "yaw": DIRS[d][1]}
             for s in STATIONS for d in VIEWS[s]]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        os.symlink(three_dir(), tmp / "three")
        shutil.copy(ROOT / "source" / "storm_terrace_blockout.glb", tmp / "blockout.glb")
        shutil.copy(TOOLS / "render.html", tmp / "render.html")
        (tmp / "views.json").write_text(json.dumps({"width": W, "height": H, "vfov": VFOV, "views": views}))
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp))
        handler.log_message = lambda *a: None
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            subprocess.run(["node", str(TOOLS / "render_views.cjs"), str(tmp), str(srv.server_address[1]),
                            str(tmp / "views.json"), str(out)], check=True)
        finally:
            srv.shutdown()
    f = (W / 2) / np.tan(np.radians(HFOV / 2))
    cams = {"convention": "camera_to_world, OpenCV axes (+X right, +Y down, +Z forward); "
                          "world: x east, y up, z north, metres; depth = z-depth along +Z",
            "width": W, "height": H, "hfov_deg": HFOV, "intrinsics": [[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]],
            "views": {}}
    for v in views:
        raw = np.fromfile(out / f"{v['name']}_depth.rgb24", np.uint8).reshape(H, W, 3).astype(np.uint32)
        mm = (raw[..., 0] << 16) | (raw[..., 1] << 8) | raw[..., 2]
        (out / f"{v['name']}_depth.rgb24").unlink()
        m = np.where(mm > 0, mm / 1000.0, np.nan).astype(np.float32)
        np.save(out / f"{v['name']}_depth.npy", m)
        Image.fromarray(np.nan_to_num(m * 100, nan=0).clip(0, 65535).astype(np.uint16)).save(out / f"{v['name']}_depth_cm.png")
        cams["views"][v["name"]] = {"camera_to_world": camera(np.array(v["pos"], float), v["yaw"]).round(6).tolist(),
                                    "image": f"generated/{v['name']}.png", "layout": f"layout/{v['name']}_layout.png",
                                    "depth_cm_png": f"layout/{v['name']}_depth_cm.png", "depth_npy": f"layout/{v['name']}_depth.npy"}
    (out / "cameras.json").write_text(json.dumps(cams, indent=1))
    print(f"wrote {len(views)} views to {out}")


if __name__ == "__main__":
    main()
