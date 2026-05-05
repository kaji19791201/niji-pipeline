import io
import json
import os
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


def _fallback_placements(image: Image.Image, texts: list[dict]) -> list[dict]:
    height = image.size[1]
    font_size = int(height * 0.04)
    result = []
    dialogue_idx = 0
    sfx_idx = 0
    for t in texts:
        if t["role"] == "dialogue":
            result.append({
                "text": t["text"],
                "role": "dialogue",
                "top": "10%",
                "left": f"{5 + dialogue_idx * 20}%",
                "font_size": font_size,
                "rotation": 0,
            })
            dialogue_idx += 1
        else:
            result.append({
                "text": t["text"],
                "role": "sfx",
                "top": f"{65 + sfx_idx * 10}%",
                "left": f"{60 + sfx_idx * 5}%",
                "font_size": int(font_size * 1.3),
                "rotation": 15 * (1 if sfx_idx % 2 == 0 else -1),
            })
            sfx_idx += 1
    return result


def detect_placements(image: Image.Image, texts: list[dict]) -> list[dict]:
    import google.genai as genai
    from google.genai import types

    width, height = image.size

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    texts_json = json.dumps(texts, ensure_ascii=False)
    font_min = int(height * 0.02)
    font_max = int(height * 0.08)

    prompt = f"""You are a manga layout designer. Place text elements on this image so they avoid covering the main character(s).

Image size: {width}x{height}px
Text elements: {texts_json}

For each element assign:
- top: "N%" from top (0-95)
- left: "N%" from left (0-90)
- font_size: integer pixels ({font_min}-{font_max})
- rotation: integer degrees (dialogue=0, sfx=±10 to ±30)

Placement rules:
- dialogue: place in dark/empty background areas (left or right edges), avoid character face
- sfx: scatter near character with rotation, overlapping character is acceptable
- Elements should not heavily overlap each other

Return JSON only."""

    schema = {
        "type": "object",
        "properties": {
            "placements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text":      {"type": "string"},
                        "role":      {"type": "string"},
                        "top":       {"type": "string"},
                        "left":      {"type": "string"},
                        "font_size": {"type": "integer"},
                        "rotation":  {"type": "integer"},
                    },
                    "required": ["text", "role", "top", "left", "font_size", "rotation"],
                },
            }
        },
        "required": ["placements"],
    }

    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        raw = json.loads(response.text)
        placements = raw["placements"]

        result = []
        for p in placements:
            top_val = min(max(float(str(p["top"]).rstrip("%")), 0), 95)
            left_val = min(max(float(str(p["left"]).rstrip("%")), 0), 90)
            font_size = min(max(int(p["font_size"]), font_min), font_max)
            rotation = min(max(int(p["rotation"]), -30), 30)
            result.append({
                "text": p["text"],
                "role": p["role"],
                "top": f"{top_val:.0f}%",
                "left": f"{left_val:.0f}%",
                "font_size": font_size,
                "rotation": rotation,
            })
        return result

    except Exception as e:
        print(f"[renderer] Vision LLM failed: {e}, using fallback")
        return _fallback_placements(image, texts)


def render_dialogue(image: Image.Image, placements: list[dict], output_path: Path) -> None:
    width, height = image.size

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp:
        img_path = Path(img_tmp.name)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_tmp:
        html_path = Path(html_tmp.name)

    try:
        image.save(img_path)

        divs = []
        for p in placements:
            text = (p["text"]
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br>"))
            role = p["role"]
            top = p["top"]
            left = p["left"]
            font_size = p["font_size"]
            rotation = p.get("rotation", 0)
            divs.append(
                f'<div class="text {role}" '
                f'style="top:{top};left:{left};font-size:{font_size}px;--rot:{rotation}deg">'
                f'{text}</div>'
            )

        divs_html = "\n".join(divs)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ width: {width}px; height: {height}px; overflow: hidden; position: relative; }}
  img {{ position: absolute; top: 0; left: 0; width: {width}px; height: {height}px; }}
  .text {{
    position: absolute;
    font-family: 'Hiragino Mincho ProN', 'Yu Mincho', serif;
    color: white;
    line-height: 1.4;
    text-shadow:
      -2px -2px 0 black,  2px -2px 0 black,
      -2px  2px 0 black,  2px  2px 0 black,
      -3px  0   0 black,  3px  0   0 black,
       0   -3px 0 black,  0    3px 0 black,
       0    0   12px rgba(100, 160, 255, 0.9);
  }}
  .dialogue {{
    writing-mode: vertical-rl;
    text-orientation: upright;
  }}
  .sfx {{
    writing-mode: horizontal-tb;
    font-weight: bold;
    font-style: italic;
    font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
    transform: rotate(var(--rot, 0deg));
  }}
</style>
</head><body>
<img src="file://{img_path}">
{divs_html}
</body></html>"""

        html_path.write_text(html, encoding="utf-8")

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"file://{html_path}")
            page.screenshot(
                path=str(output_path),
                clip={"x": 0, "y": 0, "width": width, "height": height},
            )
            browser.close()
    finally:
        img_path.unlink(missing_ok=True)
        html_path.unlink(missing_ok=True)
