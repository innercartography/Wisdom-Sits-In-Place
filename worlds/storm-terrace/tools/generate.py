#!/usr/bin/env python3
"""Generate the Storm Terrace directional views with Gemini (native generateContent API).

Prompts (STYLE, RULES, SHOT blocks) are read from ../README.md so the README stays
the single source of truth. Each shot is sent with its reference images.

Auth: sends `x-goog-api-key: $GEMINI_API_KEY`. In the Claude cloud environment the
network proxy injects the saved key into that header, so the variable can be a placeholder.
(The OpenAI-compatible endpoint can't return images from these models, so we use the
native API.)

Usage:
  python3 tools/generate.py                 # all missing shots, in dependency order
  python3 tools/generate.py A1_right B2_back  # specific shots (regenerates them)
  MODEL=gemini-3.1-flash-image python3 tools/generate.py
"""
import base64, io, json, os, re, ssl, sys, time, urllib.request, urllib.error
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "A0_front_source_clean.png"
PLAN = ROOT / "source" / "site_plan.png"
OUT = ROOT / "generated"
MODEL = os.environ.get("MODEL", "gemini-3-pro-image")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "2K")
KEY = os.environ.get("GEMINI_API_KEY", "proxy-injected")

# shot -> generated neighbours to attach (source + plan are always attached first)
ORDER = [
    ("A0_front", []), ("A1_right", ["A0_front"]), ("A2_back", ["A1_right"]), ("A3_left", ["A0_front"]),
    ("B2_back", ["A0_front", "A1_right"]), ("B0_front", ["A0_front"]),
    ("B1_right", ["B0_front", "B2_back"]), ("B3_left", ["B0_front", "A3_left"]),
    ("E2_back", ["A0_front", "B0_front"]), ("E0_front", ["A0_front"]),
    ("E1_right", ["E0_front", "E2_back"]), ("E3_left", ["E0_front", "E2_back"]),
    ("D0_front", ["B2_back"]), ("D2_back", ["A2_back", "B2_back"]), ("D3_left", ["A3_left"]),
    ("C0_front", ["A0_front"]), ("C2_back", ["A2_back"]),
]


def load_prompts():
    md = (ROOT / "README.md").read_text()
    blocks = re.findall(r"```\n(.*?)\n```", md, re.S)
    style = next(b for b in blocks if b.startswith("STYLE:"))
    rules = next(b for b in blocks if b.startswith("RULES:"))
    shots = {}
    for b in blocks:
        m = re.match(r"SHOT (\w+):", b)
        if m:
            shots[m.group(1)] = b
    return style, rules, shots


def inline(path, max_side=1600):
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=92)
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}


def find_images(obj):
    """Collect base64 image payloads from any response shape."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                if v.startswith("data:image"):
                    found.append(v.split(",", 1)[1])
                elif k in ("b64_json", "data") and len(v) > 1000:
                    found.append(v)
                else:
                    found += [m for m in re.findall(r"data:image/\w+;base64,([A-Za-z0-9+/=]+)", v)]
            else:
                found += find_images(v)
    elif isinstance(obj, list):
        for v in obj:
            found += find_images(v)
    return found


def post(payload):
    ctx = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt") if Path("/root/.ccr/ca-bundle.crt").exists() else None
    req = urllib.request.Request(URL, json.dumps(payload).encode(), {
        "Content-Type": "application/json", "x-goog-api-key": KEY})
    with urllib.request.urlopen(req, timeout=300, context=ctx) as r:
        return json.load(r)


def to_16x9(im):
    w, h = im.size
    target = 16 / 9
    if abs(w / h - target) < 0.01:
        return im
    if w / h > target:
        nw = round(h * target); x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = round(w / target); y = (h - nh) // 2
    return im.crop((0, y, w, y + nh))


def generate(name, refs, style, rules, shots):
    if name not in shots:
        sys.exit(f"no SHOT block for {name} in README.md")
    text = f"{style}\n\n{rules}\n\n{shots[name]}\n\nOutput one 16:9 landscape image."
    content = [{"text": text}, inline(SRC), inline(PLAN)]
    for r in refs:
        p = OUT / f"{r}.png"
        if p.exists():
            content.append(inline(p))
        else:
            print(f"  (reference {r} missing, continuing without it)")
    for attempt in range(3):
        try:
            resp = post({"contents": [{"role": "user", "parts": content}],
                         "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                                              "imageConfig": {"aspectRatio": "16:9", "imageSize": IMAGE_SIZE}}})
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:400]
            if e.code in (429, 500, 503) and attempt < 2:
                print(f"  HTTP {e.code}, retrying in {20 * (attempt + 1)}s"); time.sleep(20 * (attempt + 1)); continue
            sys.exit(f"HTTP {e.code}: {body}")
    imgs = find_images(resp)
    if not imgs:
        (OUT / f"{name}.response.json").write_text(json.dumps(resp, indent=1)[:20000])
        sys.exit(f"no image in response for {name}; saved {name}.response.json")
    im = Image.open(io.BytesIO(base64.b64decode(imgs[-1]))).convert("RGB")
    raw = im.size
    im = to_16x9(im)
    im.save(OUT / f"{name}.png")
    print(f"  saved {name}.png  {raw} -> {im.size}")


def main():
    OUT.mkdir(exist_ok=True)
    style, rules, shots = load_prompts()
    wanted = sys.argv[1:]
    for name, refs in ORDER:
        if wanted and name not in wanted:
            continue
        if not wanted and (OUT / f"{name}.png").exists():
            continue
        print(f"{name}  (model {MODEL})")
        generate(name, refs, style, rules, shots)


if __name__ == "__main__":
    main()
