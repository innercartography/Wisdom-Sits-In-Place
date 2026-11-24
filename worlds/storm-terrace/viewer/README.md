# Viewing the splats on your own machine (GPU)

The cloud container renders splats in software, so 2M splats are unusably slow there.
On a PC with an RTX card, all three routes below run in real time.

## 1. Browser viewer (no install)

1. Pull the branch (`claude/ecstatic-cerf-2h2juw`).
2. Open `worlds/storm-terrace/viewer/index.html` in Chrome or Edge (double-click works).
3. Drop `worlds/storm-terrace/atlas/splats_run4/results/refinedSplats_2000000.spz` onto the page.

Controls: click to look around, WASD to move, E/Space and Q/C for up and down, Shift to go faster.
Keys `1`–`9` and `0`, and `[` / `]`, step through the camera presets: the start view, the 12 run-4
frames the splats were built from, a mid-causeway view, and an overview from the south.
`P` copies the current camera pose as JSON, in the same `rub` world Atlas uses, so a pose
you like can go straight into a camera list. `K` saves a screenshot.

Three.js and Spark load from jsDelivr, so the page needs internet the first time.

## 2. SuperSplat (browser editor)

Open https://superspl.at/editor and drop in the PLY from step 3 below (newer builds also take the
SPZ directly). It is good for cropping the sky shell and deleting floaters.

## 3. Blender

Convert first (numpy is the only dependency):

```bash
python tools/spz_to_ply.py atlas/splats_run4/results/refinedSplats_2000000.spz storm_terrace_run4.ply --zup
```

Import the PLY with a 3D Gaussian Splatting add-on, for example KIRI Engine's free "3DGS Render"
add-on. `--zup` rotates the scene into Blender's Z-up frame. Leave the flag off for tools that
expect Y-up. Use `--max-points 300000` for a lighter file while you lay out cameras.

`source/storm_terrace_blockout.glb` imports into the same Blender scene, so you can compare
the splats against the blockout. The GLB is Y-up as well: Blender's glTF importer rotates it
automatically, which matches `--zup`.
