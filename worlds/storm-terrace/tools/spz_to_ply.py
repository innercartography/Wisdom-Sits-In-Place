#!/usr/bin/env python3
"""Convert an SPZ Gaussian-splat file (v2/v3) to a standard 3DGS PLY.

The PLY uses the usual 3DGS property layout (x y z, f_dc_*, opacity, scale_*, rot_*),
which Blender splat add-ons, SuperSplat and most 3DGS tools read.

Positions stay in the Atlas world (x right, y up, z back = the camera "rub" frame).
Blender is Z-up: after import rotate the object +90 deg about X (or pass --zup here).

    python3 tools/spz_to_ply.py IN.spz OUT.ply [--zup] [--max-points N]
"""
import argparse, gzip, struct, sys
import numpy as np

SH_C0 = 0.28209479177387814


def read_spz(path):
    raw = gzip.decompress(open(path, "rb").read())
    magic, version, n, sh_deg, frac, flags, _ = struct.unpack_from("<IIIBBBB", raw, 0)
    if magic != 0x5053474E:
        sys.exit(f"{path}: not an SPZ file")
    if version not in (2, 3):
        sys.exit(f"{path}: SPZ version {version} not supported")
    o = 16
    p = np.frombuffer(raw, np.uint8, n * 9, o).reshape(n, 3, 3).astype(np.int32); o += n * 9
    pos = p[..., 0] | (p[..., 1] << 8) | (p[..., 2] << 16)
    pos = np.where(pos & 0x800000, pos - (1 << 24), pos).astype(np.float32) / (1 << frac)
    alpha = np.frombuffer(raw, np.uint8, n, o).astype(np.float32) / 255.0; o += n
    col = np.frombuffer(raw, np.uint8, n * 3, o).reshape(n, 3).astype(np.float32); o += n * 3
    f_dc = (col / 255.0 - 0.5) / 0.15
    scale = np.frombuffer(raw, np.uint8, n * 3, o).reshape(n, 3).astype(np.float32) / 16.0 - 10.0; o += n * 3
    if version == 2:
        r = np.frombuffer(raw, np.uint8, n * 3, o).reshape(n, 3).astype(np.float32) / 127.5 - 1.0; o += n * 3
        w = np.sqrt(np.clip(1.0 - (r * r).sum(1), 0, None))
        quat = np.column_stack([w, r])                      # w x y z
    else:  # v3: smallest-three, 4 bytes
        b = np.frombuffer(raw, np.uint8, n * 4, o).reshape(n, 4).astype(np.uint32); o += n * 4
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16) | (b[:, 3] << 24)
        largest = (v >> 30) & 3
        mask, sq = (1 << 9) - 1, np.float32(np.sqrt(0.5))
        sumsq = np.zeros(n, np.float32)
        bits = v.copy()   # components packed from index 3 down, skipping `largest`
        comps = np.zeros((n, 4), np.float32)
        for i in range(3, -1, -1):
            skip = largest == i
            mag = (bits & mask).astype(np.float32)
            neg = (bits >> 9) & 1
            val = sq * mag / mask
            val = np.where(neg == 1, -val, val)
            comps[:, i] = np.where(skip, 0, val)
            bits = np.where(skip, bits, bits >> 10)
            sumsq += np.where(skip, 0, val * val)
        comps[np.arange(n), largest] = np.sqrt(np.clip(1 - sumsq, 0, None))
        quat = comps[:, [3, 0, 1, 2]]                       # w x y z
    return dict(n=n, sh_deg=sh_deg, pos=pos, alpha=alpha, f_dc=f_dc, scale=scale, quat=quat)


def write_ply(path, s, zup=False, max_points=None):
    n = s["n"]
    idx = np.arange(n)
    if max_points and max_points < n:
        idx = np.random.default_rng(0).choice(n, max_points, replace=False)
    pos, quat = s["pos"][idx], s["quat"][idx]
    if zup:  # y-up -> z-up: rotate +90 deg about X  (x, y, z) -> (x, -z, y)
        pos = np.column_stack([pos[:, 0], -pos[:, 2], pos[:, 1]])
        h = np.float32(np.sqrt(0.5))
        rq = np.array([h, h, 0, 0], np.float32)               # w x y z
        w1, x1, y1, z1 = rq
        w2, x2, y2, z2 = quat.T
        quat = np.column_stack([w1*w2 - x1*x2 - y1*y2 - z1*z2,
                                w1*x2 + x1*w2 + y1*z2 - z1*y2,
                                w1*y2 - x1*z2 + y1*w2 + z1*x2,
                                w1*z2 + x1*y2 - y1*x2 + z1*w2])
    a = np.clip(s["alpha"][idx], 1e-6, 1 - 1e-6)
    opacity = np.log(a / (1 - a))
    cols = [pos, np.zeros_like(pos), s["f_dc"][idx], opacity[:, None], s["scale"][idx], quat]
    names = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2", "opacity",
             "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    data = np.hstack(cols).astype("<f4")
    header = "ply\nformat binary_little_endian 1.0\n" + f"element vertex {len(idx)}\n" + \
             "".join(f"property float {k}\n" for k in names) + "end_header\n"
    with open(path, "wb") as f:
        f.write(header.encode())
        f.write(data.tobytes())
    return len(idx)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spz"); ap.add_argument("ply")
    ap.add_argument("--zup", action="store_true", help="rotate to Blender's Z-up")
    ap.add_argument("--max-points", type=int, help="random subsample for a lighter file")
    a = ap.parse_args()
    s = read_spz(a.spz)
    if s["sh_deg"]:
        print(f"note: SH degree {s['sh_deg']} present; only the base colour is written")
    k = write_ply(a.ply, s, a.zup, a.max_points)
    print(f"wrote {k} splats -> {a.ply}")
