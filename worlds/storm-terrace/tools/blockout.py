#!/usr/bin/env python3
"""Build a coarse 3D blockout of Storm Terrace from the site plan, for Marble Chisel / Atlas.

Coordinates follow the site plan: x = east (m), z = north (m), y = up, with camera A at the
origin, eye height 1.6 m. In the exported GLB (glTF is Y-up, -Z forward) north is -Z, so
a default camera at the origin looking down -Z sees the A0_front view.

Usage: python3 tools/blockout.py source/storm_terrace_blockout.glb
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon

PALETTE = {
    "tile":     [190, 220, 214, 255],
    "water":    [10, 15, 42, 255],
    "glass":    [77, 124, 255, 255],
    "tower":    [44, 71, 201, 255],
    "lintel":   [138, 74, 58, 255],
    "starfield":[21, 26, 58, 255],
    "trunk":    [60, 50, 30, 255],
    "foliage":  [31, 61, 26, 255],
    "sea":      [122, 29, 18, 255],
}
scene = trimesh.Scene()


def add(name, mesh, mat):
    mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=mat, baseColorFactor=PALETTE[mat], metallicFactor=0.0, roughnessFactor=0.6))
    # plan (x, y_up, z_north) -> glTF (x, y, -z)
    mesh.apply_transform(np.diag([1, 1, -1, 1]))
    mesh.invert()  # mirroring flips winding; restore outward normals
    scene.add_geometry(mesh, node_name=name, geom_name=name)


def box(name, x0, x1, y0, y1, z0, z1, mat):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    add(name, m, mat)


def prism(name, pts_xz, y0, y1, mat):
    # extrude_polygon builds along +Z from a polygon in XY; rotate so it extrudes along +Y
    m = trimesh.creation.extrude_polygon(Polygon([(x, -z) for x, z in pts_xz]), y1 - y0)
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    add(name, m, mat)


def limb(name, p0, p1, r, mat):
    m = trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=10)
    add(name, m, mat)


def tree(name, x, z, base, size=1.0, lean=(1.0, 0.3), h=1.0, crown=1.0):
    """Gnarled tree: S-curved trunk in three segments, a few branches, and a flat, clumpy crown.
    h scales height, crown scales the crown blobs."""
    lx, lz = lean
    s = size
    pts = [np.array([x, base, z]),
           np.array([x - 0.6 * lx * s, base + 2.5 * s * h, z - 0.6 * lz * s]),
           np.array([x + 0.4 * lx * s, base + 5.0 * s * h, z + 0.4 * lz * s]),
           np.array([x + 1.4 * lx * s, base + 7.0 * s * h, z + 1.4 * lz * s])]
    for i in range(3):
        limb(f"{name}_trunk_{i}", pts[i], pts[i + 1], (0.75 - 0.15 * i) * s, "trunk")
    top = pts[3]
    rng = np.random.default_rng(sum(map(ord, name)))
    for i, ang in enumerate(np.linspace(0, 2 * np.pi, 5, endpoint=False) + 0.4):
        tip = top + np.array([np.cos(ang) * 3.2 * s * crown, (1.2 * s + rng.uniform(0, 1.0) * s) * h, np.sin(ang) * 3.2 * s * crown])
        limb(f"{name}_branch_{i}", top, tip, 0.25 * s, "trunk")
        blob = trimesh.creation.icosphere(subdivisions=2, radius=2.4 * s * crown)
        blob.apply_scale([1.0, 0.55, 1.0])
        blob.apply_translation(tip + np.array([0, 0.6 * s, 0]))
        add(f"{name}_crown_{i}", blob, "foliage")
    core = trimesh.creation.icosphere(subdivisions=2, radius=3.0 * s * crown)
    core.apply_scale([1.3, 0.5, 1.3])
    core.apply_translation(top + np.array([0, 2.2 * s, 0]))
    add(f"{name}_crown_core", core, "foliage")


# --- deck (top surface at y = 0), split around the channel x -2..1 from z 6 northward
box("deck_south", -14, 36, -1, 0, -190, 6, "tile")
box("deck_west", -14, -2, -1, 0, 6, 72, "tile")
box("deck_east", 1, 36, -1, 0, 6, 72, "tile")
box("walkway_west", -6, -2, -1, 0, 72, 98, "tile")
box("walkway_east", 1, 6, -1, 0, 72, 98, "tile")
box("lightning_platform", -12, 12, -1, 0, 98, 122, "tile")
box("lightning_platform_rim", -2, 1, -1, 0, 98, 122, "tile")  # platform closes over the channel end
# channel: walls are the deck sides; dark water 3 m down; simple stair landings
box("channel_water", -2, 1, -4, -3, 6, 98, "water")
for i, z in enumerate(np.arange(8, 30, 2.2)):
    y = -0.4 - i * 0.28
    box(f"ribbon_stair_{i:02d}", -1.7 + 0.5 * np.sin(i * 0.9) - 0.4, -1.7 + 0.5 * np.sin(i * 0.9) + 1.6,
        y - 0.15, y, z, z + 1.6, "tile")
# plinth, pool, tower, plinth tree
box("plinth", 2, 14, 0, 1.5, 30, 60, "tile")
box("plinth_pool", 2.2, 10, 1.5, 1.55, 31, 47, "water")
box("tower", 6, 12, 1.5, 46.5, 48, 56, "tower")
tree("plinth_tree", 7, 38, 1.5, size=0.9, lean=(-0.8, 0.3))
# monoliths and lintel
box("glass_monolith", 12, 16, 0, 70, 17, 40, "glass")
prism("lintel", [(16, 40), (16, 17), (4, 10), (2, 26)], 55, 58, "lintel")
box("starfield_monolith", 26, 30, 0, 60, -5, 30, "starfield")
# bent tree, south gate
tree("bent_tree", -8, 10, 0, size=1.0, lean=(2.6, 0.8), h=0.75, crown=1.35)
box("south_gate_west", -12, -8, 0, 12, -182, -178, "glass")
box("south_gate_east", 8, 12, 0, 12, -182, -178, "glass")
# optional sea plane (delete in Chisel if the prompt should own the sea)
box("sea_optional", -600, 600, -2.05, -2, -600, 600, "sea")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "storm_terrace_blockout.glb"
    scene.export(out)
    print("wrote", out, "with", len(scene.geometry), "meshes")
