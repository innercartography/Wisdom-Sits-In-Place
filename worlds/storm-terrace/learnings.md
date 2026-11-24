# Storm Terrace: learnings

A running record of what worked, what failed and why, so the next world starts ahead of this one.
Newest entries go at the top of each section.

## Pipeline so far

| Stage | What | Result |
|---|---|---|
| Gemini views | 17 views from the painting plus a site plan (`generated/`) | Good mood, but geometry drifts between views |
| Blockout | `tools/blockout.py`, which builds a GLB with separately named meshes | Editable spatial source of truth |
| Chisel run 1 | A0–A3 from the origin, with context frames at the same cameras | Atlas copied the context frames almost exactly |
| Chisel run 2 | Context moved off the target cameras | Literal tree primitives reproduced literally; masked tree regions came back empty |
| Chisel run 3 | 12 cameras along the causeway, returnDepth | Coherent world; deck sometimes rendered as sea |
| Chisel run 4 | Denser bent tree, dry-paving prompt, sun stated per direction | Paving and tree fixed; A_yaw045/135 went back to sea; P6 got a south-facing bolt |
| Splats run 4 | posedImages2Splats from the 12 run-4 frames | 2M splats in about 20 min; structure correct from the start view |

## Image generation (Gemini)

- **Lock the style explicitly.** Without the STYLE LOCK block, views drift toward clean photoreal renders.
- **Fix geometry one sentence at a time.** Add a specific sentence to the shot that went wrong, rather than rewriting the shared style.
- Always attach the painting and the site plan, plus one or two neighbouring views, as references.
- Use the native `generateContent` endpoint. The OpenAI-compatible endpoint cannot return images.

## atlasChisel

- **A context frame at the same camera as a target gets copied.** Place context frames at different poses, or leave them out.
- **Blockout primitives are taken literally.** A lollipop tree comes back as a lollipop tree. Model the silhouette you actually want, such as a dense, leaning crown.
- **Masked regions are not reliably filled in.** The masked tree areas came back empty.
- **The prompt applies to every view.** "Sun on the left" puts a sun on the left in every direction, so describe lighting per direction (sun to the west, storm to the north) and check the views that face away from it.
- **Two flat surfaces at similar heights blur together.** The deck at y=0 and the sea at y=−2 both read as flat ground in depth, so Atlas sometimes turns the deck into water. The planned fix is geometry, not prompt: thicker deck edges and a visible step or kerb, the sea lower, or the sea left out of depth.
- A camera at exactly the origin, with a diagonal yaw, lost the deck. Nudge it off the origin.
- Budget: 128 rollout views (4 per depth target, 1 per context frame). `returnDepth` needs 2–256 targets that are not all at one centre.
- Depth is planar z, written as a 16-bit inverted log-depth PNG (0 = no surface). See `tools/atlas_chisel_request.py`.

## Splats

- 12 frames gave a coherent first world. The areas no frame sees, such as the south side, the far east and behind the monoliths, are invented or blurry.
- Expected artifacts: the sky becomes a shell of splats; foliage, glass and lightning are soft.
- Inspect on a GPU. Software rendering in the container loads 2M splats in under a second but cannot render a frame in a useful time. See `viewer/README.md`.

## Tooling gotchas

- Node's fetch behind the proxy needs `NODE_USE_ENV_PROXY=1`.
- Three.js headless pages need an importmap entry for `three/addons/` when Spark is used.
- Seed procedural geometry deterministically (`sum(map(ord, name))`, not Python's `hash()`).
