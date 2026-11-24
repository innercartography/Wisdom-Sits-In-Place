# Next sprint: from one splat to a revisable world kit

**Goal:** finish one beautiful, navigable, revisable world, then make a second by transforming it.
This is a proposal; nothing here has been built yet.

## We are closer than it looks

Most of the separation already exists. It is spread across folders rather than named as a kit:

| World-kit layer | What already exists |
|---|---|
| Identity and invariants | The painting, `source/site_plan.png`, the pose table in `README.md` |
| Editable geometry | `tools/blockout.py`, which builds `source/storm_terrace_blockout.glb` with 55 named meshes (`deck_*`, `sea_optional`, `bent_tree_*`, `glass_monolith`, `lintel`, `tower`, `starfield_monolith`, and so on) |
| Style bible (draft) | The STYLE, RULES and STYLE LOCK blocks in `README.md`, plus the painting as Atlas style reference |
| Cameras | `atlas/views_run3.json`, `atlas/splats_run4/check_cameras.json`, presets in `viewer/index.html` |
| Generations | `generated/` (Gemini) and `atlas/chisel_*` (requests, results, contact sheets) |
| Exports | `atlas/splats_run4/results/*.spz` |
| Learnings | `learnings.md` |

So the splat is already one manifestation, not the source of truth. Changing the world means
editing the blockout and cameras and regenerating, not patching splats.

## Proposed kit layout (move, don't rewrite)

```
storm-terrace/
  world.json        identity, scale, invariants, parameters, pointers to everything below
  style/            approved/ and provisional/ references, palette, rules (from README STYLE/RULES)
  geometry/         blockout.py, blockout.glb, and later a .blend if you start hand-editing
  cameras/          canonical views, diagnostic views, exploration paths (JSON, rub world)
  variants/         morphology presets: time of day, weather, season, material, medium
  generations/      gemini/, chisel_run1..4/, splats_run4/ (each with request + summary)
  exports/          spz, ply, glb, video
  tools/            unchanged
  learnings.md
```

## One decision to make: where the geometry is edited

Keep exactly one editable source. Today that is `blockout.py`. Code is diffable and easy for an
agent to change exactly ("move the tree 2 m west"). Once you start shaping things by hand in
Blender, the `.blend` becomes the source, and the scripts only export cameras, depth and masks
from it. Don't maintain both.

## Sprint backlog, smallest first

1. **Look at run 4 on your GPU** (see `viewer/README.md`). Press `P` on views you love or hate and
   paste the poses back. They become `cameras/` entries and review notes.
2. **Curate the style bible.** I build a review sheet of all four Chisel runs plus the Gemini views,
   organised by camera. You promote picks into `style/approved/`; the rest stay provisional.
3. **Write `world.json`.** Split invariants from parameters:
   - *Invariant:* the causeway axis, the plinth with its tree, the tower, the glass monolith with its terracotta lintel, the starfield slab, the bent tree at the west edge, the low red horizon.
   - *Parameters:* sky, weather, time of day, season, materials, rendering medium, crown density.
4. **Fix the deck/sea confusion in geometry**, then add a free validation gate:
   - Render blockout depth plus an object-ID mask for each camera.
   - Automatically flag frames where deck and sea meet at nearly the same depth.
   - You review a 4-view diagnostic contact sheet.
   - Only then pay for a 3–4-view Chisel check before the full set.
5. **Fill the coverage gaps.** Add south-facing views and stations past the monoliths, then do one new
   splat reconstruction.
6. **First morphology experiment: one dimension only.** Same geometry and cameras, change only time
   of day through the Chisel prompt and style reference. This is the cheapest test of how much
   identity survives a change.

Not this sprint: ComfyUI, Supabase, a morphology UI or a kit library. Revisit them after world two.
