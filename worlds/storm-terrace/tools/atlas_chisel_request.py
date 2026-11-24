#!/usr/bin/env python3
"""Build an atlasChisel request from blockout depth layouts (render_views.py output).

World frame for Atlas: the glTF frame of the blockout (Y-up, x east, z = -north, metres), which
is right-handed as Atlas expects. Cameras are camera-to-world, "rub", XYZW quaternions.
Depth is encoded as 16-bit inverted log depth PNGs (0 = no surface).

Usage: python3 tools/atlas_chisel_request.py OUT_DIR VIEW [VIEW ...]
       python3 tools/atlas_chisel_request.py OUT_DIR --views=FILE.json   (all cameras in a views file)
  writes OUT_DIR/<view>_logdepth.png and OUT_DIR/frames.json (camera + zMin/zMax per view)
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STATIONS = {"A": (0, 1.6, 0), "B": (4, 3.1, 34), "C": (-0.5, -1.4, 22), "D": (9, 1.6, 22), "E": (0, 1.6, 108)}
YAW = {"front": 0, "right": 90, "back": 180, "left": 270}
FAR_CAP = 400.0  # metres; farther sea counts as no surface so it doesn't squeeze the depth range
W, H, F = 1280, 720, 640.0  # 90 deg horizontal FOV


def camera_from(pos, yaw):
    x, y, z = pos
    t = math.radians(yaw)
    # turning right is a negative rotation about +Y
    q = [0.0, math.sin(-t / 2), 0.0, math.cos(-t / 2)]
    return {"extrinsics": {"position": [x, y, -z], "quaternion": [round(v, 9) for v in q], "coordinateSystem": "rub"},
            "intrinsics": {"width": W, "height": H, "fx": F, "fy": F, "cx": W / 2, "cy": H / 2}}


def camera(view):
    return camera_from(STATIONS[view[0]], YAW[view.split("_")[1]])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--views=")]
    vf = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--views=")), None)
    custom = {v["name"]: v for v in json.loads(Path(vf).read_text())["views"]} if vf else {}
    layout = ROOT / "layout" / Path(vf).stem if vf else ROOT / "layout"
    out = Path(args[0]); out.mkdir(parents=True, exist_ok=True)
    frames = {}
    for view in (args[1:] or list(custom)):
        d = np.load(layout / f"{view}_depth.npy").astype(np.float64)
        assert d.shape == (H, W), d.shape
        valid = np.isfinite(d) & (d > 0) & (d <= FAR_CAP)
        zmin, zmax = float(d[valid].min()), float(d[valid].max())
        white = 65535
        p = np.zeros_like(d)
        p[valid] = np.round(white * (1 - np.log(d[valid] / zmin) / np.log(zmax / zmin)))
        p[valid] = np.clip(p[valid], 1, white)
        Image.fromarray(p.astype(np.uint16)).save(out / f"{view}_logdepth.png")
        cam = camera_from(custom[view]["pos"], custom[view]["yaw"]) if view in custom else camera(view)
        frames[view] = {"camera": cam, "zMin": round(zmin, 4), "zMax": round(zmax, 4),
                        "coverage": round(float(valid.mean()), 3)}
        print(view, frames[view]["zMin"], frames[view]["zMax"], "surface fraction", frames[view]["coverage"])
    (out / "frames.json").write_text(json.dumps(frames, indent=1))


if __name__ == "__main__":
    main()
